"""Windows successor experiment. Development may repair; held-out evaluation is sealed.
Examples and local paths are in benchmarks/rtx_reference_repair_v1/README.md.
"""
from __future__ import annotations
import argparse, ast, ctypes, json, os, queue, shutil, subprocess, sys, threading, time
from pathlib import Path
from common import *
import plan
from audit import record_check,matrix,performance,transaction_check,verify_greedy,verify_states
HERE=Path(__file__).resolve().parent
JOB_PIN='c4f1582ec655e16821f05d4f8b764bd67afa4d7d'

def windows_helpers(repo):
    b=git_read(repo,BASE,'scripts/experiments/rtx_dense14b_transfer_v1/run.py',JOB_PIN)
    t=ast.parse(b.decode());nodes=[n for n in t.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ('Job','available_ram')]
    need(len(nodes)==2,'missing tested Job/ram helpers')
    env={'ctypes':ctypes,'time':time,'need':need}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'pinned_windows_safety','exec'),env)
    return env['Job'],env['available_ram']

def local_code():return {p.name:file_hash(p) for p in HERE.iterdir() if p.is_file() and p.suffix in ('.py','.hpp','.inc')}

def check_epoch(bundle):
    seal=read(bundle/'EPOCH.json');need(seal['code']==local_code(),'code changed: create a successor epoch and preserve this one')
    for name,h in seal['inputs'].items():need(file_hash(bundle/name)==h,'epoch input changed: '+name)
    cfg=read(bundle/'CONFIG.json')
    for path,h in seal['assets'].items():need(file_hash(path)==h,'epoch executable/library/model changed')
    return cfg

def prepare(config,out):
    c=read(config);out=Path(out).resolve();need(not out.exists(),'fresh epoch directory required')
    need(c.get('user_authorized') is True,'user execution authorization missing')
    research_path=Path(c['research_root']).resolve(); parent_path=Path(c['parent_root']).resolve()
    need(research_path!=parent_path and not research_path.is_relative_to(parent_path) and not parent_path.is_relative_to(research_path),'new research root must be disjoint from PR156 root')
    parent=Path(c['parent_root']);binding=read(parent/'BINDING.json');build=read(c['build_receipt'])
    old_binding=read(parent/'BINDING.json')
    if not c.get('original_worker'):
        c['original_worker']=read(parent/'LOCAL_PATHS.json')['assets']['worker']
    need(file_hash(c['original_worker'])==old_binding['families']['Qwen']['executable_sha256'],'frozen original worker missing/different')
    need(build['status']=='BUILT_NOT_QUALIFIED','native build must finish first')
    need(build['source_zip_sha256']==old_binding['families']['Qwen']['source_zip_sha256'],'source capsule differs')
    need(build['numerical_modules']==old_binding['families']['Qwen']['numerical_modules'],'numerical DLL cohort changed: declare a source-repair successor, not silently replace it')
    need(file_hash(c['worker'])==build['executable_sha256'],'worker build identity')
    need(file_hash(c['target'])==TARGET and file_hash(c['draft'])==DRAFT,'frozen model bytes differ')
    dev=read(c['development_panel']);held=read(c['heldout_panel']);need(len(dev['inputs'])==4 and len(held['inputs'])==12,'panel sizes')
    for x in dev['inputs']+held['inputs']:valid_input(x)
    plan.assert_distinct_panels(dev,held)
    # Reuse exact predeclared prompts; do not silently retokenize or replace hard cases.
    for current,name in ((dev,'calibration.json'),(held,'selected_panel.json')):
        frozen=json.loads(git_read(c['repo'],BASE,'benchmarks/rtx_dense14b_transfer_v1/host_execution/'+name))
        projection=lambda x:[(r['id'],r['prompt_ids'],r['cap']) for r in x['inputs']]
        need(projection(current)==projection(frozen),'panel identity differs from PR156: '+name)
    policy=read(c['policy']);plan.policy_check(policy)
    need(policy['rowwise_roles']==build['repair_spec']['rowwise_roles'],'candidate build/policy differs')
    need(policy.get('stable_norm_offload',False)==build['repair_spec'].get('stable_norm_offload',False),'scheduler repair build/policy differs')
    for n in ('worker_timeout_seconds','total_native_seconds','min_ram_free_bytes','min_vram_free_bytes','min_disk_free_bytes','max_payload_bytes'):
        positive(c['resources'][n])
    need(c['resources']['min_ram_free_bytes']>=8*1024**3 and c['resources']['min_vram_free_bytes']>=1024**3,'retain headroom')
    need(c['resources']['worker_timeout_seconds']<=c['resources']['total_native_seconds'],'worker/global time budget')
    need(c.get('gpu_lock_file') and c.get('gpu_uuid'),'GPU identity/coordination lock')
    historical=git_read(c['repo'],BASE,'benchmarks/rtx_dense14b_transfer_v1/host_execution/PILOT_AUDIT.json')
    refs=json.loads(historical)['references']
    need(set(refs)=={x['id'] for x in dev['inputs']},'development IDs differ from retained counterexamples/controls')
    binding['study_id']=STUDY;binding['status']='FROZEN_BEFORE_FIRST_NATIVE_REQUEST'
    binding['repair_model']={'layers':40,'embd':5120}
    ident=binding['families']['Qwen'];ident['executable_sha256']=build['executable_sha256'];ident['core_sha256']=build['core_sha256'];ident['worker_source_sha256']=build['worker_source_sha256']
    binding['candidate_policy']=policy
    out.mkdir(parents=True)
    for name,x in [('CONFIG.json',c),('BINDING.json',binding),('DEV.json',dev),('HELDOUT.json',held),('POLICY.json',policy),('DEV_REFERENCES.json',refs),('ORIGINAL_BINDING.json',old_binding)]:save(out/name,x)
    (out/'PARENT_FAILED_AUDIT.json').write_bytes(historical)
    save(out/'PLAN.json',{'study_id':STUDY,'context':{'n_ctx':1024,'kv':'F16','flash':False,'threads':24},
        'service_timer_definition':'resident-model complete request; includes canonical producer context creation/destruction, prefill, state export/import, draft, verification, synchronization and assembly; diagnostic tensors are never timed'})
    assets={str(Path(c[n]).resolve()):file_hash(c[n]) for n in ('target','draft','worker','original_worker','build_receipt')}
    for n,h in build['numerical_modules'].items():
        p=Path(c['worker']).parent/n;need(file_hash(p)==h,'DLL identity differs');assets[str(p.resolve())]=h
    for n,h in old_binding['families']['Qwen']['numerical_modules'].items():
        p=Path(c['original_worker']).parent/n;need(file_hash(p)==h,'historical R DLL changed: '+n);assets[str(p.resolve())]=h
    files=('CONFIG.json','BINDING.json','DEV.json','HELDOUT.json','POLICY.json','DEV_REFERENCES.json','PLAN.json','ORIGINAL_BINDING.json')
    save(out/'EPOCH.json',{'base':BASE,'created':utc(),'code':local_code(),'inputs':{n:file_hash(out/n) for n in files},'assets':assets},exclusive=True)
    research=Path(c['research_root']);research.mkdir(parents=True,exist_ok=True)
    (research/'LEDGER.jsonl').touch(exist_ok=True)
    save(out/'STATE.json',{'status':'DEVELOPMENT_READY','native_runs':0,'heldout_exposed':False},exclusive=True)
    return out

def resource_totals(ledger):
    rows=[json.loads(l) for l in Path(ledger).read_text().splitlines() if l]
    outstanding={};reserved=0;seconds=0.
    for row in rows:
        key=(row.get('epoch'),row.get('unit'))
        if row.get('event')=='START':
            need(key not in outstanding,'duplicate unsettled attempt')
            outstanding[key]=row;reserved+=row.get('reserved_requests',0)
        elif row.get('event')=='END':
            need(key in outstanding,'receipt has no matching start')
            del outstanding[key];seconds+=row.get('seconds',0)
    need(not outstanding,'unsettled native attempt: audit/close its real costs and processes before proceeding')
    return reserved,seconds

def run_unit(bundle,name,panel,schedule,original=False,admit=False):
    import json
    need(os.name=='nt','native execution requires Windows RTX host')
    bundle=Path(bundle).resolve();c=check_epoch(bundle)
    need(bool(schedule),'empty schedule')
    for slot in schedule:
        need(slot['category'] in ('development','diagnostic','qualification','warmup','measured'),'unknown request category')
        need(0<=slot['source_index']<len(panel['inputs']),'input index outside panel')
        confined(bundle/'safe_slot_root',slot['slot_id'])
        if slot['category'] in ('warmup','measured','qualification'):
            need(not slot.get('repair',{}).get('probe',False),'teacher-forced probe cannot enter confirmation')
    if any(s['category'] in ('qualification','measured','warmup') for s in schedule):
        seal=read(bundle/'CANDIDATE_FREEZE.json');need(seal['epoch_sha256']==file_hash(bundle/'EPOCH.json'),'candidate freeze/epoch mismatch')
    unit=confined(bundle/'units',name);need(not unit.exists(),'attempt already exists; use a new attempt ID, never overwrite/rerun silently')
    research=Path(c['research_root']);ledger=research/'LEDGER.jsonl';used,spent=resource_totals(ledger)
    need(used+(0 if admit else len(schedule))<=1200,'new-study 1200-request budget exhausted; old 40 remain separately accounted')
    dev_used=sum(x.get('reserved_requests',0) for x in [json.loads(l) for l in ledger.read_text().splitlines() if l] if x.get('event')=='START' and x.get('stage')=='development')
    is_dev=all(s['category'] in ('development','diagnostic') for s in schedule)
    need(not is_dev or dev_used+(0 if admit else len(schedule))<=480,'development budget exhausted')
    need(spent<c['resources']['total_native_seconds'],'cumulative native time exhausted')
    Job,ram=windows_helpers(c['repo'])
    need(ram()>=c['resources']['min_ram_free_bytes'],'RAM reserve')
    gpu=subprocess.run(['nvidia-smi','--query-gpu=uuid,name,driver_version','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=30)
    lines=[l.strip() for l in gpu.stdout.splitlines() if c['gpu_uuid'] in l]
    need(len(lines)==1 and '5070' in lines[0],'GPU identity unavailable/ambiguous')
    if c.get('gpu_driver'):need(lines[0].split(',')[-1].strip()==c['gpu_driver'],'GPU driver changed after preparation')
    need(shutil.disk_usage(bundle).free>=c['resources']['min_disk_free_bytes'],'disk reserve')
    lock=Path(c['gpu_lock_file']);lock.parent.mkdir(parents=True,exist_ok=True)
    p=job=None;active=None;success=False;error=None;native_count=0;start=time.monotonic();launched=False
    unit.mkdir(parents=True);save(unit/'PANEL.json',panel);save(unit/'SLOTS.json',schedule)
    out=unit/'native';argv=[c['original_worker'] if original else c['worker'],str(out),c['target'],c['draft'],str(unit/'PANEL.json'),str(unit/'SLOTS.json'),'Qwen',str(bundle/('ORIGINAL_BINDING.json' if original else 'BINDING.json')),str(bundle/'PLAN.json')]+(['--admit-pools'] if admit else [])
    save(lock,{'pid':os.getpid(),'epoch':str(bundle),'unit':name,'utc':utc()},exclusive=True)
    try:
        append(ledger,{'event':'START','utc':utc(),'epoch':str(bundle),'unit':name,'reserved_requests':0 if admit else len(schedule),'stage':'development' if is_dev else 'confirmation','argv':argv})
        env=dict(os.environ)
        for k in list(env):
            if k.startswith(('HS_','HSC_','JSA_','GGML_')):del env[k]
        env['CUDA_VISIBLE_DEVICES']=c['gpu_uuid']
        with (unit/'stderr.log').open('xb') as err:
            p=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,encoding='utf-8',env=env,
              creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW)
            launched=True;job=Job(p);q=queue.Queue()
            def reader():
                try:
                    for line in p.stdout:q.put(line)
                finally:q.put(None)
            threading.Thread(target=reader,daemon=True).start();ready=False
            timeout=min(c['resources']['worker_timeout_seconds'],c['resources']['total_native_seconds']-spent)
            while True:
                need(time.monotonic()-start<timeout,'worker safety timeout')
                need(ram()>=c['resources']['min_ram_free_bytes'],'runtime RAM reserve')
                try:line=q.get(timeout=.5)
                except queue.Empty:continue
                if line is None:break
                e=json.loads(line);append(unit/'EVENTS.jsonl',e)
                if e['event']=='POOLS_READY':
                    need(not ready,'duplicate native handshake');ready=True
                    m=read(out/'PROVISIONED.json')['memory_after_provisioning']
                    need(m['free_bytes']>=c['resources']['min_vram_free_bytes'],'native VRAM reserve')
                    p.stdin.write('RUN\n');p.stdin.flush()
                elif e['event']=='REQUEST_COMPLETED':
                    need(ready and native_count<len(schedule),'extra native event')
                    s=schedule[native_count];need(e['slot_id']==s['slot_id'],'native request order')
                    r=read(confined(out,s['slot_id']+'.json'))
                    if original:
                        need(r['slot']==s and r['prompt_ids']==panel['inputs'][s['source_index']]['prompt_ids'],'original reference identity')
                        transaction_check(r)
                        if s['observer']=='heavy':
                            verify_greedy(r,confined(out,s['slot_id']));verify_states(r,confined(out,s['slot_id']))
                    else:record_check(r,s,panel['inputs'][s['source_index']],confined(out,s['slot_id']))
                    # Development reference mismatches are observations, not runner failures.
                    if s['category'] in ('measured','warmup'):
                        refs=read(bundle/'QUALIFIED_REFERENCES.json');need(endpoint(r)==refs[r['input_id']],'timing reference failure')
                    native_count+=1
                    need(shutil.disk_usage(bundle).free>=c['resources']['min_disk_free_bytes'],'disk reserve exhausted')
                    need(sum(f.stat().st_size for f in out.rglob('*') if f.is_file())<=c['resources']['max_payload_bytes'],'per-unit evidence budget exceeded')
                    p.stdin.write('CONTINUE\n');p.stdin.flush()
                else:raise ValueError('unexpected native event')
            need(p.wait(timeout=30)==0,'native worker failed')
            result=read(out/'result.json');need(result['status']==('RESOURCE_ADMITTED' if admit else 'COMPLETE') and result['normal_cleanup_returned'] and native_count==(0 if admit else len(schedule)),'incomplete native result')
            active=job.wait_empty(timeout=10);need(active==0,'Job cleanup not yet empty');success=True
    except BaseException as e:
        error=repr(e)
        try:
            if job:job.terminate()
            elif p and p.poll() is None:p.kill()
        finally:
            if p:p.wait(timeout=30)
            if job:active=job.wait_empty(timeout=10)
        raise
    finally:
        if job:job.close()
        if p:
            if p.stdin:p.stdin.close()
            if p.stdout:p.stdout.close()
        # Preserve ownership marker when cleanup cannot be established.
        if not launched or active==0:lock.unlink(missing_ok=True)
        receipt={'event':'END','utc':utc(),'epoch':str(bundle),'unit':name,'success':success,'error':error,'seconds':time.monotonic()-start,
                 'completed_requests':native_count,'active_processes_after_wait':active,'lock_retained':lock.exists()}
        save(unit/'RECEIPT.json',receipt);append(ledger,receipt)
    return [] if admit else [read(confined(out,s['slot_id']+'.json')) for s in schedule]

def load_records(bundle,name):
    unit=Path(bundle)/'units'/name;receipt=read(unit/'RECEIPT.json')
    need(receipt['success'] and receipt['active_processes_after_wait']==0,'incomplete attempt')
    return [read(confined(unit/'native',s['slot_id']+'.json')) for s in read(unit/'SLOTS.json')]

def develop(bundle,name):
    panel=read(bundle/'DEV.json');ss=plan.development(panel);rows=run_unit(bundle,name,panel,ss)
    report=matrix(rows,panel,ss,read(bundle/'DEV_REFERENCES.json'));report['native_files']='units/'+name
    report['epoch_sha256']=file_hash(bundle/'EPOCH.json')
    report['source_record_sha256']={s['slot_id']:file_hash(confined(bundle/'units'/name/'native',s['slot_id']+'.json')) for s in ss}
    save(bundle/(name+'_AUDIT.json'),report,exclusive=True)
    return report

def freeze(bundle,audit_path,mechanism_path):
    check_epoch(bundle);p=read(bundle/'POLICY.json');plan.policy_check(p)
    report=read(audit_path);need(not report['observer_errors'],'observer contamination blocks candidate freeze')
    need(report['epoch_sha256']==file_hash(bundle/'EPOCH.json'),'development audit belongs to another epoch')
    unit=confined(bundle,report['native_files']);slots=read(unit/'SLOTS.json')
    for slot in slots:
        record=confined(unit/'native',slot['slot_id']+'.json')
        need(file_hash(record)==report['source_record_sha256'][slot['slot_id']],'development source record changed')
        record_check(read(record),slot,read(bundle/'DEV.json')['inputs'][slot['source_index']],confined(unit/'native',slot['slot_id']))
    cells=report['cells'];expected={x['id'] for x in read(bundle/'DEV.json')['inputs']}
    shams=[r for r in cells if r['arm']=='R' and r['producer']=='reference']
    need({r['input'] for r in shams}==expected and all(r['reference_equal'] and r['observer_equal'] for r in shams),'canonical handoff own-path sham failed')
    for arm in plan.ARMS:
        producer='native' if arm=='R' else p['prefill']
        selected=[r for r in cells if r['arm']==arm and r['producer']==producer]
        need({x['input'] for x in selected}==expected and all(x['reference_equal'] and x['observer_equal'] for x in selected),'candidate has not repaired all development/control inputs: '+arm)
    mechanism=read(mechanism_path)
    for k in ('root_cause_evidence','intervention','ablation_result','regression_result','remaining_limits'):need(bool(mechanism.get(k)),'mechanism record missing '+k)
    need(mechanism.get('reviewed_by_agent') is True,'6astra must review mechanism evidence before exposure')
    save(bundle/'CANDIDATE_FREEZE.json',{'epoch_sha256':file_hash(bundle/'EPOCH.json'),'policy':p,
        'audit_sha256':file_hash(audit_path),'mechanism_sha256':file_hash(mechanism_path),'utc':utc(),
        'note':'Development repaired; not a universal guarantee or held-out PASS.'},exclusive=True)

def confirm(bundle):
    check_epoch(bundle)
    seal=read(bundle/'CANDIDATE_FREEZE.json')
    need(seal['epoch_sha256']==file_hash(bundle/'EPOCH.json'),'freeze identity')
    panel=read(bundle/'HELDOUT.json')
    exposures=Path(read(bundle/'CONFIG.json')['research_root'])/'HELDOUT_EXPOSURES.jsonl'
    previous=[json.loads(l) for l in exposures.read_text().splitlines() if l] if exposures.exists() else []
    current_ids={x['id'] for x in panel['inputs']}
    current_hashes={x['prompt_ids_sha256'] for x in panel['inputs']}
    for old in previous:
        need(not current_ids.intersection(old['ids']) and not current_hashes.intersection(old['prompt_hashes']),'held-out panel already exposed in this research chain; do not reuse as blind validation')
    append(exposures,{'utc':utc(),'epoch':str(bundle),'ids':sorted(current_ids),'prompt_hashes':sorted(current_hashes),'seal':file_hash(bundle/'CANDIDATE_FREEZE.json')})
    # Mark exposure before the first original-reference execution. Do not reuse
    # this panel as blind data after a candidate change or an incomplete first pass.
    save(bundle/'HELDOUT_EXPOSURE.json',{'utc':utc(),'policy_seal_sha256':file_hash(bundle/'CANDIDATE_FREEZE.json')},exclusive=True)
    old=[]
    for i in range(12):
        for observer in ('off','heavy'):
            s=plan.slot(panel,i,'R','native',observer,f'original/i{i:02d}/{observer}','qualification')
            s['study_id']='rtx_dense14b_transfer_v1';old.append(s)
    baseline=run_unit(bundle,'original_reference',panel,old,original=True)
    refs={}
    for i,item in enumerate(panel['inputs']):
        pair=[r for r in baseline if r['slot']['source_index']==i]
        need(len(pair)==2 and endpoint(pair[0])==endpoint(pair[1]),'original R unstable/observer contaminated')
        refs[item['id']]=endpoint(pair[0])
    save(bundle/'ORIGINAL_HELDOUT_REFERENCES.json',{'baseline_commit':BASE,'old_worker_sha256':read(bundle/'ORIGINAL_BINDING.json')['families']['Qwen']['executable_sha256'],
        'references':refs,'records':24,'raw_record_sha256':{s['slot_id']:file_hash(confined(bundle/'units/original_reference/native',s['slot_id']+'.json')) for s in old}},exclusive=True)
    ss=plan.qualification(panel,read(bundle/'POLICY.json'));rows=run_unit(bundle,'heldout',panel,ss)
    result=matrix(rows,panel,ss,refs);save(bundle/'HELDOUT_AUDIT.json',result,exclusive=True)
    if result['observer_errors'] or not result['all_reference_equal']:
        save(bundle/'STATE.json',{'status':'HELDOUT_FAILED_NO_TIMING','inputs_now_exposed':True});return result
    save(bundle/'QUALIFIED_REFERENCES.json',refs,exclusive=True)
    allrows=[]
    for s in range(4):allrows+=run_unit(bundle,f'formal_s{s}',panel,plan.timing(panel,read(bundle/'POLICY.json'),s))
    final=performance(allrows,refs);save(bundle/'FINAL_COST.json',final,exclusive=True)
    save(bundle/'STATE.json',{'status':'CONFIRMATION_AND_TIMING_COMPLETE','no_new_experiments_queued':True})
    return final

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('prepare');a.add_argument('--config',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('admit');a.add_argument('--bundle',type=Path,required=True);a.add_argument('--attempt',default='admission01')
    a=sub.add_parser('develop');a.add_argument('--bundle',type=Path,required=True);a.add_argument('--attempt',default='development01')
    a=sub.add_parser('probe');a.add_argument('--bundle',type=Path,required=True);a.add_argument('--slots',type=Path,required=True);a.add_argument('--attempt',required=True)
    a=sub.add_parser('freeze');a.add_argument('--bundle',type=Path,required=True);a.add_argument('--audit',type=Path,required=True);a.add_argument('--mechanism',type=Path,required=True)
    a=sub.add_parser('confirm');a.add_argument('--bundle',type=Path,required=True)
    a=p.parse_args()
    if a.cmd=='prepare':print(prepare(a.config,a.out))
    elif a.cmd=='admit':run_unit(a.bundle,a.attempt,read(a.bundle/'DEV.json'),plan.development(read(a.bundle/'DEV.json'))[:1],admit=True)
    elif a.cmd=='develop':print(json.dumps(develop(a.bundle,a.attempt),indent=2))
    elif a.cmd=='probe':run_unit(a.bundle,a.attempt,read(a.bundle/'DEV.json'),read(a.slots))
    elif a.cmd=='freeze':freeze(a.bundle,a.audit,a.mechanism)
    else:print(json.dumps(confirm(a.bundle),indent=2))
if __name__=='__main__':main()
