"""Owned Windows execution and promotion gates. Development failures are evidence,
not an instruction to abandon mechanism repair. Historical runs remain immutable.
"""
from __future__ import annotations
import argparse, datetime as dt, os, queue, shutil, subprocess, threading, time
from pathlib import Path
from common import *
import plans
from analyze import audit, analyze, transactions, vector_audit


def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def rows(path):return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s]

def host_identity(gpu_uuid):
    need(os.name=='nt','actual Windows host preparation required')
    q=['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total','--format=csv,noheader,nounits']
    r=subprocess.run(q,capture_output=True,text=True,check=True,timeout=30)
    matches=[x for x in r.stdout.splitlines() if x.split(',')[0].strip()==gpu_uuid]
    need(len(matches)==1 and '5070' in matches[0],'missing/ambiguous registered RTX device')
    return {'utc':utc(),'query':q,'device':matches[0],'scope':'inventory, not per-operator placement'}


def budget_totals(ledger):
    xs=rows(ledger) if Path(ledger).exists() else [];starts={};ends={}
    for x in xs:
        if x['event']=='START':need(x['attempt'] not in starts,'duplicate attempt');starts[x['attempt']]=x
        elif x['event']=='END':need(x['attempt'] in starts and x['attempt'] not in ends,'unbound/duplicate end');ends[x['attempt']]=x
    return {'reserved':sum(x['requests'] for x in starts.values()),
            'by_phase':{k:sum(x['requests'] for x in starts.values() if x['budget_phase']==k) for k in plans.BUDGET if k!='total'},
            'seconds':sum(pos(x['seconds'],'charged lifetime') for x in ends.values()),
            'unclosed':sorted(set(starts)-set(ends))}


def reference_records(raw_root,panel,target_pin=TARGET):
    """Recover original R endpoints, tokens and exact source-record hashes only.
    Full original archive verification remains a separate host receipt.
    """
    wanted={x['id']:x for x in panel['inputs']};found={}
    for p in Path(raw_root).rglob('*.json'):
        if p.stat().st_size>8*1024*1024:continue
        try:r=read(p)
        except (ValueError,UnicodeError,OSError):continue
        if not isinstance(r,dict) or r.get('arm')!='R' or r.get('input_id') not in wanted:continue
        x=wanted[r['input_id']]
        if r.get('prompt_ids_sha256')!=x['prompt_ids_sha256'] or r.get('prompt_ids')!=x['prompt_ids']:continue
        identity=r.get('identity',{});model=identity.get('models',{}).get('target',{})
        if model.get('sha256')!=target_pin:continue
        e=endpoint(r);entry=found.setdefault(x['id'],{'endpoint':e,'records':[],'captures':set()})
        need(entry['endpoint']==e,'historical R disagreement')
        entry['records'].append({'path':str(p.resolve()),'sha256':sha(p)})
        entry['captures'].add(bool(r.get('capture')))
    need(set(found)==set(wanted),'missing exact historical reference records')
    for v in found.values():need(v['captures']=={False,True},'original observer controls missing');v['captures']=sorted(v['captures'])
    return found


def prepare(config,out):
    c=read(config);out=Path(out).resolve();need(not out.exists(),'fresh epoch root required')
    need(c.get('user_authorized') is True,'existing user authorization not recorded')
    pilot=plans.panel_check(read(c['development_panel']),'development')
    regression=c.get('regression_only',False)
    panel=pilot if regression else plans.panel_check(read(c['confirmation_panel']),'confirmation')
    if not regression:
        for k in ('id','text_sha256','prompt_ids_sha256'):
            need(not {x[k] for x in pilot['inputs']}&{x[k] for x in panel['inputs']},'development/confirmation overlap')
    b=read(c['reference_binding']);identity=b['families']['Qwen'];build=read(c['repair_build_receipt'])
    need(build['status']=='BUILT_NOT_QUALIFIED' and build['source_zip_sha256']==SOURCE,'wrong core source')
    need(len(build['numerical_modules'])==21 and build['numerical_modules']==identity['numerical_modules'],'numerical DLL cohort changed')
    need(build.get('repair_graph_patch',{}).get('native_validated') is False,'unexpected build receipt; preserve actual source provenance')
    assets={k:str(Path(c[k]).resolve()) for k in ('target','draft','reference_worker','repair_worker','reference_binding','repair_build_receipt','development_panel')+(() if regression else ('confirmation_panel',))}
    target_pin='408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6' if regression else TARGET
    need(identity['models']['target']['sha256']==target_pin and sha(assets['target'])==target_pin and sha(assets['draft'])==DRAFT,'frozen models changed')
    need(sha(assets['reference_worker'])==identity['executable_sha256'],'original R executable differs')
    need(sha(assets['repair_worker'])==build['executable_sha256'],'repair executable/build mismatch')
    for cohort in ('reference','repair'):
        for n,h in build['numerical_modules'].items():
            need(Path(n).name==n,'invalid DLL filename');p=Path(assets[cohort+'_worker']).parent/n
            need(sha(p)==h,'wrong DLL: '+str(p));assets[cohort+':'+n]=str(p)
    for k in ('worker_timeout_seconds','total_native_seconds','max_payload_bytes','min_ram_free_bytes','min_disk_free_bytes','min_vram_free_bytes'):
        pos(c['resources'][k],k)
    need(c['resources']['min_ram_free_bytes']>=8*1024**3 and c['resources']['min_vram_free_bytes']>=1024**3,'resource headroom weakened')
    need(c['resources']['worker_timeout_seconds']<=c['resources']['total_native_seconds'],'timeout ceiling')
    need(c.get('gpu_uuid') and c.get('gpu_lock_file') and c.get('shared_ledger'),'shared host ownership missing')
    host_probe=host_identity(c['gpu_uuid'])
    refs=reference_records(c['original_raw_root'],pilot,target_pin)
    candidate=json.loads(json.dumps(b));ci=candidate['families']['Qwen']
    for k in ('executable_sha256','core_sha256','worker_source_sha256'):ci[k]=build[k]
    candidate['study_id']=STUDY;candidate['repair']={'rows':'off','source_stage':c['repair_build_receipt']}
    candidate['status']='FROZEN_BEFORE_FIRST_NATIVE_REQUEST';candidate['is_synthetic']=False
    if regression:
        candidate['dense14b']={'target_gpu_layers':999,'threads':24,'expected_layers':36,'expected_embd':4096,'min_vram_free_bytes':c['resources']['min_vram_free_bytes'],'min_ram_free_bytes':c['resources']['min_ram_free_bytes']}
    else:
        need(candidate['dense14b']['target_gpu_layers']==24 and candidate['dense14b']['threads']==24,'14B placement policy changed')
    out.mkdir(parents=True)
    save(out/'HOST_PROBE.json',host_probe,True)
    for name,value in [('CONFIG',c),('DEVELOPMENT',pilot),('CONFIRMATION',panel),('HISTORICAL_REFERENCES',refs),('REFERENCE_BINDING',b),('REPAIR_BINDING',candidate)]:save(out/(name+'.json'),value,True)
    save(out/'ASSETS.json',{'paths':assets,'sha256':{k:sha(v) for k,v in assets.items()}},True)
    save(out/'EPOCH.json',{'study':STUDY,'created_utc':utc(),'historical_study_requests':40,'shared_ledger':c['shared_ledger'],
                         'code':code_pins(),'confirmation_panel_sha256':digest(panel),'status':'DEVELOPMENT'},True)
    ledger=Path(c['shared_ledger']);ledger.parent.mkdir(parents=True,exist_ok=True);ledger.touch(exist_ok=True)
    return out


def check_assets(bundle):
    a=read(bundle/'ASSETS.json')
    for k,p in a['paths'].items():need(sha(p)==a['sha256'][k],'changed asset: '+k)
    need(read(bundle/'EPOCH.json')['code']==code_pins(),'code changed: create a documented successor epoch, sharing the ledger')
    return a['paths']


def run_worker(bundle,panel,planned,unit,budget_phase):
    from windows_job import Job,available_ram
    c=read(bundle/'CONFIG.json');assets=read(bundle/'ASSETS.json')['paths'];res=c['resources']
    need(os.name=='nt','native execution requires Windows RTX host')
    need(planned,'empty worker plan');cohort=planned[0]['cohort'];policy=planned[0]['rows']
    need(all(s['cohort']==cohort and s['rows']==policy for s in planned),'one cohort/policy per process')
    unitdir=bundle/'units'/unit;need(not unitdir.exists(),'attempt already exists; inspect retained receipt, do not overwrite')
    ledger=Path(c['shared_ledger']);b=budget_totals(ledger);need(not b['unclosed'],'unclosed owned attempt requires cleanup receipt')
    need(b['reserved']+len(planned)<=plans.BUDGET['total'],'total request budget exhausted')
    need(b['by_phase'][budget_phase]+len(planned)<=plans.BUDGET[budget_phase],'phase budget exhausted')
    need(b['seconds']<res['total_native_seconds'],'lifetime reservation exhausted')
    need(available_ram()>=res['min_ram_free_bytes'] and shutil.disk_usage(bundle).free>=res['min_disk_free_bytes'],'resource reserve')
    unitdir.mkdir(parents=True);native=unitdir/'native'
    binding=read(bundle/('REFERENCE_BINDING.json' if cohort=='reference' else 'REPAIR_BINDING.json'))
    if cohort=='repair':binding['repair']['rows']=policy
    compat=c.get('reference_compatibility_study','rtx_dense14b_transfer_v1')
    slots=[plans.native_slot(s,compat) for s in planned]
    save(unitdir/'BINDING.json',binding,True);save(unitdir/'PANEL.json',panel,True);save(unitdir/'SLOTS.json',slots,True);save(unitdir/'OUTER_SLOTS.json',planned,True)
    plan={'context':{'n_ctx':1024,'n_batch':1024,'threads':24,'kv':'F16','flash':False,'expected_layers':36 if c.get('regression_only') else 40},
          'service_timer_definition':'resident request including reset, actual producer, copies/restore/readback, drafting, verification and state; no historical reference-answer lookup'}
    save(unitdir/'PLAN.json',plan,True)
    argv=[assets[cohort+'_worker'],str(native),assets['target'],assets['draft'],str(unitdir/'PANEL.json'),str(unitdir/'SLOTS.json'),'Qwen',str(unitdir/'BINDING.json'),str(unitdir/'PLAN.json')]
    env=dict(os.environ)
    for k in list(env):
        if k.startswith(('HS_','HSC_','JSA_','GGML_')):del env[k]
    env['CUDA_VISIBLE_DEVICES']=c['gpu_uuid'];attempt=str(unitdir)
    append(ledger,{'event':'START','attempt':attempt,'budget_phase':budget_phase,'requests':len(planned),'utc':utc(),
                   'code':code_pins(),'binding_sha256':sha(unitdir/'BINDING.json'),'argv':argv,
                   'prompt_hashes':sorted({s['prompt_ids_sha256'] for s in planned}),'input_ids':sorted({s['input_id'] for s in planned})})
    start=time.monotonic();process=job=None;success=False;active=None;error=None;count=0
    try:
        with (unitdir/'stderr.log').open('xb') as stderr:
            process=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,text=True,encoding='utf-8',env=env,
                                     creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW)
            job=Job(process);q=queue.Queue()
            def consume():
                try:
                    for line in process.stdout:q.put(line)
                finally:q.put(None)
            threading.Thread(target=consume,daemon=True).start();ready=False
            timeout=min(res['worker_timeout_seconds'],res['total_native_seconds']-b['seconds'])
            while True:
                need(time.monotonic()-start<timeout,'owned process timeout')
                need(available_ram()>=res['min_ram_free_bytes'],'RAM reserve exhausted')
                try:line=q.get(timeout=.5)
                except queue.Empty:continue
                if line is None:break
                event=json.loads(line);append(unitdir/'events.jsonl',event)
                if event['event']=='POOLS_READY':
                    need(not ready,'duplicate readiness');ready=True
                    m=read(native/'PROVISIONED.json')['memory_after_provisioning']
                    need(m['free_bytes']>=res['min_vram_free_bytes'],'VRAM headroom')
                    process.stdin.write('RUN\n');process.stdin.flush()
                elif event['event']=='REQUEST_COMPLETED':
                    need(ready and count<len(slots) and event['slot_id']==slots[count]['slot_id'],'request order')
                    r=read(safe(native,slots[count]['slot_id']+'.json'));s=slots[count];x=panel['inputs'][s['source_index']]
                    need(r['slot']==s and r['identity']==binding['families']['Qwen'],'native identity/slot')
                    need(r['prompt_ids']==x['prompt_ids'],'native input changed');endpoint(r)
                    if not r.get('diagnostic_teacher_forced',False):transactions(r)
                    need(shutil.disk_usage(bundle).free>=res['min_disk_free_bytes'],'disk reserve exhausted')
                    need(sum(p.stat().st_size for p in bundle.rglob('*') if p.is_file())<=res['max_payload_bytes'],'payload budget')
                    process.stdin.write('CONTINUE\n');process.stdin.flush();count+=1
                else:raise ValueError('unexpected native handshake')
            need(process.wait(timeout=30)==0,'native nonzero exit');terminal=read(native/'result.json')
            need(count==len(planned) and terminal['status']=='COMPLETE' and terminal['normal_cleanup_returned'],'incomplete worker')
            active=job.wait_empty();need(active==0,'owned processes remain');success=True
    except BaseException as e:
        error=repr(e);raise
    finally:
        # Cleanup is performed even when logging or parsing fails; do not put a
        # fallible audit write before killing/waiting for owned processes.
        if not success:
            try:
                if job:job.terminate()
                elif process and process.poll() is None:process.kill()
            finally:
                if process:
                    try:process.wait(timeout=30)
                    except subprocess.TimeoutExpired:pass
                if job:
                    try:active=job.wait_empty()
                    except Exception:active=None
        if job:job.close()
        if process:
            for f in (process.stdin,process.stdout):
                if f:
                    try:f.close()
                    except Exception:pass
        receipt={'event':'END','attempt':attempt,'utc':utc(),'seconds':max(time.monotonic()-start,.000001),
                 'success':success,'active_processes':active,'completed':count,'error':error}
        save(unitdir/'RECEIPT.json',receipt);append(ledger,receipt)
    return unitdir


def execute(bundle,phase,producer='RSEED',row_policy='off',session=0,tag='v00',trace=None):
    bundle=Path(bundle).resolve();need(os.name=='nt','execution is Windows-only')
    c=read(bundle/'CONFIG.json');check_assets(bundle)
    need(not c.get('regression_only') or phase=='regression','regression epoch only runs its declared matrix')
    if phase=='confirmation':
        need(not (bundle/'CONFIRMATION_FAILED.json').exists() and not (bundle/'CONFIRMATION_PASS.json').exists(),'confirmation already exposed; no result-driven repeats')
    if phase in ('confirmation','timing','regression'):
        primary=Path(c['primary_bundle']) if phase=='regression' else bundle
        sealed=read(primary/'CANDIDATE.json');need(sealed['code']==code_pins(),'sealed source changed')
        if phase=='regression':
            need(c.get('regression_only') is True,'regression requires original Qwen8B configuration')
            need(read(primary/'ASSETS.json')['sha256']['repair_worker']==read(bundle/'ASSETS.json')['sha256']['repair_worker'],'regression candidate binary differs')
        need((producer,plans.policy(row_policy))==(sealed['producer'],sealed['rows']),'candidate changed after freeze')
    panel=read(bundle/('CONFIRMATION.json' if phase in ('confirmation','timing') else 'DEVELOPMENT.json'))
    if phase=='timing':
        proof=read(bundle/'CONFIRMATION_PASS.json');need(proof['candidate_sha256']==sha(bundle/'CANDIDATE.json'),'qualification identity changed')
        regression=read(bundle/'REGRESSION_PASS.json');need(regression['candidate_sha256']==proof['candidate_sha256'] and regression['status']=='PASS','old-model regression missing')
        planned=plans.timing(panel,producer,row_policy,session);bp='timing'
    elif phase in ('confirmation','regression'):
        planned=plans.confirmation(panel,producer,row_policy,tag,regression=phase=='regression');bp=phase
    else:
        planned=plans.development(panel,phase,tag,row_policy,trace,producer);bp='development'
    result_path=bundle/('RUN_'+phase+'_'+tag+(f'_s{session}' if phase=='timing' else '')+'.json')
    need(not result_path.exists(),'run already retained')
    plan_path=result_path.with_suffix('.plan.json')
    save(plan_path,{'phase':phase,'planned':planned,'panel_sha256':digest(panel),'candidate_sha256':sha((Path(c['primary_bundle']) if phase=='regression' else bundle)/'CANDIDATE.json') if phase in ('confirmation','timing','regression') else None},True)
    lock=Path(c['gpu_lock_file']);lock.parent.mkdir(parents=True,exist_ok=True)
    with lock.open('x') as f:f.write(json.dumps({'pid':os.getpid(),'bundle':str(bundle),'utc':utc()}))
    all_records={};roots={};units=[]
    try:
        # Timing always runs one arm/input worker with paired warmup+measurement;
        # qualification/development coalesce only adjacent identical cohorts/policies.
        groups=[]
        for s in planned:
            key=(s['cohort'],s['rows'],s['source_index'],s['experiment_arm']) if phase=='timing' else (s['cohort'],s['rows'])
            if not groups or groups[-1][0]!=key:groups.append((key,[]))
            groups[-1][1].append(s)
        for i,(_,group) in enumerate(groups):
            u=run_worker(bundle,panel,group,f'{phase}_{tag}_s{session}_{i:03d}',bp);units.append(str(u))
            for s in group:
                native=u/'native';r=read(safe(native,s['slot_id']+'.json'))
                all_records[s['slot_id']]=r;roots[s['slot_id']]=native
        save(result_path,{'phase':phase,'plan':planned,'panel':panel,'units':units,'record_roots':{k:str(v) for k,v in roots.items()}},True)
        if phase=='timing':
            refs=read(bundle/'CONFIRMATION_PASS.json')['references'];timed=[]
            for s in planned:
                r=all_records[s['slot_id']];need(endpoint(r)==refs[s['input_id']],'formal reference mismatch; retain all records, stop formal continuation')
                timed.append(dict(r,outer_slot=s,endpoint_qualified=True))
            save(bundle/f'TIMING_s{session}.json',{'records':timed,'candidate_sha256':sha(bundle/'CANDIDATE.json')},True)
        elif phase=='trace':
            save(result_path.with_suffix('.audit.json'),{'status':'DIAGNOSTIC_ONLY','not_performance':True,'records':len(all_records)},True)
        else:
            hist=None if phase in ('confirmation','regression') else {k:v['endpoint'] for k,v in read(bundle/'HISTORICAL_REFERENCES.json').items()}
            result=audit(all_records,planned,panel,hist,require_placement=True,vector_roots=roots)
            save(result_path.with_suffix('.audit.json'),result,True)
            if phase=='confirmation':
                if result['status']=='PASS':
                    save(bundle/'CONFIRMATION_PASS.json',dict(result,candidate_sha256=sha(bundle/'CANDIDATE.json'),run_sha256=sha(result_path)),True)
                else:
                    save(bundle/'CONFIRMATION_FAILED.json',{'status':'FAILED_PANEL_NOW_EXPOSED','candidate_sha256':sha(bundle/'CANDIDATE.json'),'panel_sha256':digest(panel),'audit':result},True)
        return result_path
    finally:
        # An unresolved process-ownership receipt keeps the lock for host recovery.
        b=budget_totals(c['shared_ledger'])
        ends=[x for x in rows(c['shared_ledger']) if x['event']=='END']
        if not b['unclosed'] and (not ends or ends[-1]['active_processes']==0):lock.unlink()


def seal(bundle,producer,row_policy,mechanism,development_audit):
    bundle=Path(bundle);check_assets(bundle);m=read(mechanism)
    need(str(development_audit).endswith('.audit.json'),'expected a run-bound audit')
    candidate_run=Path(str(development_audit).replace('.audit.json','.json'))
    a=reaudit(candidate_run)
    need(a['status']=='PASS','candidate does not pass full development reference/observer matrix')
    need(producer in ('NATIVE','P1','RSEED'),'candidate producer')
    for k in ('observed_divergence','controlled_intervention','general_rule','remaining_uncertainty','performance_not_used_for_selection'):
        need(m.get(k),'mechanism selection report missing '+k)
    need(m['performance_not_used_for_selection'] is True,'development speed selection is disallowed')
    need(not (bundle/'CONFIRMATION_FAILED.json').exists(),'this confirmation panel is exposed; freeze a genuinely new panel in a successor epoch')
    panel=read(bundle/'CONFIRMATION.json');hashes={x['prompt_ids_sha256'] for x in panel['inputs']}
    ledger=Path(read(bundle/'CONFIG.json')['shared_ledger'])
    for event in rows(ledger):
        if event['event']=='START' and event['budget_phase']=='confirmation':
            need(not hashes.intersection(event.get('prompt_hashes',[])),'confirmation exposure retained across epochs')
    baseline=reaudit(bundle/'RUN_baseline_v00.json');sham=reaudit(bundle/'RUN_sham_v00.json')
    r_cells=[x for x in baseline['cells'] if x['arm']=='R_NEW']
    need(len(r_cells)==4 and all(x['reference_equal'] and x['observer_equal'] for x in r_cells),'new R does not preserve historical reference')
    need(sham['status']=='PASS','own-path state restore sham must pass')
    source=Path(development_audit).with_suffix('')
    # Bind the evidence to its completed plan, not an unbound caller PASS flag.
    need(str(development_audit).endswith('.audit.json'),'expected a run-bound audit')
    run_path=Path(str(development_audit).replace('.audit.json','.json'));run=read(run_path)
    need(run['phase'] in ('p1','rseed','candidate'),'not a candidate development matrix')
    candidate_producers={s['producer'] for s in run['plan'] if s['experiment_arm']!='R_NEW'}
    need(candidate_producers=={producer} and all(s['rows']==plans.policy(row_policy) for s in run['plan']),'audit/candidate mismatch')
    save(bundle/'CANDIDATE.json',{'producer':producer,'rows':plans.policy(row_policy),'code':code_pins(),
        'asset_hashes':read(bundle/'ASSETS.json')['sha256'],'development_audit_sha256':sha(development_audit),'raw_reaudit':a,
        'mechanism_report_sha256':sha(mechanism),'panel_sha256':digest(read(bundle/'CONFIRMATION.json')),
        'policy':'no prompt/model-ID/output-index special cases; source/precision/reference frozen','utc':utc()},True)


def advance(bundle):
    bundle=Path(bundle)
    if not (bundle/'CANDIDATE.json').exists():
        for p in ('baseline','sham','p1','rseed','cross'):
            if not (bundle/('RUN_'+p+'_v00.json')).exists():execute(bundle,p)
        return {'status':'MECHANISM_REVIEW_REQUIRED','next':'inspect audits/traces, repair family rule if needed; then seal candidate. No new user approval required for ordinary engineering.'}
    c=read(bundle/'CANDIDATE.json')
    if not (bundle/'CONFIRMATION_PASS.json').exists():
        if (bundle/'CONFIRMATION_FAILED.json').exists():return {'status':'CONFIRMATION_FAILED_RETURN_TO_DEVELOPMENT','timing_started':False}
        execute(bundle,'confirmation',c['producer'],c['rows'],tag='h0')
    if not (bundle/'CONFIRMATION_PASS.json').exists():return {'status':'CONFIRMATION_FAILED','timing_started':False}
    if not (bundle/'REGRESSION_PASS.json').exists():return {'status':'REGRESSION_REQUIRED','next':'run original-Qwen8B regression with the same structural rule; bind complete independent report before timing'}
    for s in range(4):
        if not (bundle/f'TIMING_s{s}.json').exists():execute(bundle,'timing',c['producer'],c['rows'],s)
    rec=[r for s in range(4) for r in read(bundle/f'TIMING_s{s}.json')['records']]
    result=analyze(rec);save(bundle/'RESULT.json',result,True);return result


def reaudit(run_path):
    """Reconstruct an existing completed matrix without requesting any new forward."""
    run_path=Path(run_path);v=read(run_path);bundle=run_path.parent
    records={};roots={}
    for sid,root in v['record_roots'].items():
        p=Path(root);record=read(safe(p,sid+'.json'))
        native_plan=read(p.parent/'SLOTS.json');binding=read(p.parent/'BINDING.json')
        slot=next(s for s in native_plan if s['slot_id']==sid)
        need(record['slot']==slot and record['identity']==binding['families']['Qwen'],'record/bound identity drift')
        need(read(p.parent/'RECEIPT.json')['success'] is True,'worker did not complete')
        records[sid]=record;roots[sid]=p
    hist=None if v['phase'] in ('confirmation','regression') else {k:x['endpoint'] for k,x in read(bundle/'HISTORICAL_REFERENCES.json').items()}
    return audit(records,v['plan'],v['panel'],hist,True,roots)


def attach_regression(bundle,run_path):
    bundle=Path(bundle);run_path=Path(run_path);v=read(run_path)
    need(v['phase']=='regression','not a regression matrix')
    reg_config=read(run_path.parent/'CONFIG.json');need(reg_config.get('regression_only') is True,'wrong regression deployment')
    c=read(bundle/'CANDIDATE.json');need(c['code']==code_pins(),'candidate source changed')
    pin=read(run_path.with_suffix('.plan.json'))['candidate_sha256'];need(pin==sha(bundle/'CANDIDATE.json'),'regression freeze changed')
    result=reaudit(run_path);need(result['status']=='PASS','regression does not pass')
    save(bundle/'REGRESSION_PASS.json',{'status':'PASS','candidate_sha256':pin,'run_sha256':sha(run_path),
        'run_path':str(run_path.resolve()),'audit':result,'scope':'four original Qwen3-8B inputs, same candidate rule; not a generalization theorem'},True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='cmd',required=True)
    q=sp.add_parser('prepare');q.add_argument('--config',type=Path,required=True);q.add_argument('--out',type=Path,required=True)
    q=sp.add_parser('run');q.add_argument('--bundle',type=Path,required=True);q.add_argument('--phase',choices=('baseline','sham','p1','rseed','cross','candidate','trace','confirmation','regression','timing'),required=True)
    q.add_argument('--producer',default='RSEED');q.add_argument('--rows',default='off');q.add_argument('--session',type=int,default=0);q.add_argument('--tag',default='v00');q.add_argument('--trace',type=Path)
    q=sp.add_parser('seal');q.add_argument('--bundle',type=Path,required=True);q.add_argument('--producer',required=True);q.add_argument('--rows',default='off');q.add_argument('--mechanism',type=Path,required=True);q.add_argument('--audit',type=Path,required=True)
    q=sp.add_parser('advance');q.add_argument('--bundle',type=Path,required=True)
    q=sp.add_parser('audit-existing');q.add_argument('--run',type=Path,required=True)
    q=sp.add_parser('attach-regression');q.add_argument('--bundle',type=Path,required=True);q.add_argument('--run',type=Path,required=True)
    a=p.parse_args()
    if a.cmd=='prepare':print(prepare(a.config,a.out))
    elif a.cmd=='run':print(execute(a.bundle,a.phase,a.producer,a.rows,a.session,a.tag,read(a.trace) if a.trace else None))
    elif a.cmd=='seal':seal(a.bundle,a.producer,a.rows,a.mechanism,a.audit)
    elif a.cmd=='audit-existing':print(json.dumps(reaudit(a.run),indent=2))
    elif a.cmd=='attach-regression':attach_regression(a.bundle,a.run)
    else:print(json.dumps(advance(a.bundle),indent=2))
