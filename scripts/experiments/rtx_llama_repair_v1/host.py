"""Parameterized Windows handoff. Reuses the executed PR159 Job/lock/handshake runner."""
from __future__ import annotations
import argparse, copy, inspect, os, sys
from pathlib import Path
from lr_common import *
import parent, schedule, lr_audit
HERE=Path(__file__).resolve().parent

def code_manifest():
    return {str(p.relative_to(HERE)):file_hash(p) for p in HERE.rglob('*') if p.is_file() and p.suffix in ('.py','.hpp') and '__pycache__' not in p.parts}

def budget_current(root):
    rows=[json.loads(l) for l in (Path(root)/'RESOURCE_POLICY.jsonl').read_text().splitlines() if l.strip()]
    need(rows,'resource policy missing');previous=None
    for row in rows:
        need(row['previous']==(digest(previous) if previous else None),'broken resource-policy chain')
        need(row.get('reason') and row.get('utc'),'unexplained resource amendment')
        for k,v in row['limits'].items():need(type(v) in (int,float) and math.isfinite(v) and v>0,'invalid resource limit '+k)
        previous=row
    return previous['limits']

def amend_budget(root,limits,reason):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);p=root/'RESOURCE_POLICY.jsonl'
    old=[json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
    if old:budget_current(root)
    need(reason.strip(),'describe what the next tranche will test')
    for k,v in limits.items():need(type(v) in (int,float) and math.isfinite(v) and v>0,'finite positive limit '+k)
    required={'request_credits','development_credits','total_native_seconds','worker_timeout_seconds'}
    need(set(limits)==required,'explicit resource policy fields required')
    need(limits['worker_timeout_seconds']<=limits['total_native_seconds'],'worker timeout beyond total reservation')
    need(limits['development_credits']<=limits['request_credits'],'development reservation exceeds total')
    row={'utc':utc(),'reason':reason,'previous':digest(old[-1]) if old else None,'limits':limits}
    with p.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(row,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
    return row

def check_epoch(bundle):
    bundle=Path(bundle);seal=read(bundle/'EPOCH.json')
    need(seal['code']==code_manifest(),'code changed: prepare a successor epoch, do not overwrite this epoch')
    for rel,h in seal['inputs'].items():need(file_hash(bundle/rel)==h,'frozen input changed '+rel)
    for path,h in seal['assets'].items():need(file_hash(path)==h,'frozen asset/source changed '+path)
    c=read(bundle/'CONFIG.json');parent.verify(c['parent_snapshot'])
    b=budget_current(c['research_root']);c['request_limit']=b['request_credits'];c['development_limit']=b['development_credits']
    c['resources']['total_native_seconds']=b['total_native_seconds'];c['resources']['worker_timeout_seconds']=b['worker_timeout_seconds']
    return c

def reserve_cost(slots,admit=False):
    # A model request plus every extra diagnostic decode is charged. Actual model
    # request and graph counts remain separate in records; these are work credits.
    return 0 if admit else sum(1+(s['k']+2 if s.get('llama_diag',{}).get('mode')=='pair' else 0) for s in slots)

def derive_driver(runmod,auditmod,binding,original=False):
    source=inspect.getsource(runmod.run_unit);s=source
    s=once(s,"'Qwen',str(bundle/","'Llama',str(bundle/")
    s=once(s,'used+(0 if admit else len(schedule))<=1200',"used+reserve_cost(schedule,admit)<=c['request_limit']")
    s=once(s,'dev_used+(0 if admit else len(schedule))<=480',"dev_used+reserve_cost(schedule,admit)<=c['development_limit']")
    s=once(s,"'reserved_requests':0 if admit else len(schedule)","'reserved_requests':reserve_cost(schedule,admit)")
    # Completion still counts actual model requests, NOT shadow-decode work credits.
    need('native_count==(0 if admit else len(schedule))' in s,'native completion-count guard drift')
    s=s.replace('new-study 1200-request budget exhausted; old 40 remain separately accounted','current work-credit tranche exhausted; append a reasoned resource amendment, never reset the ledger')
    s=s.replace('development budget exhausted','development tranche exhausted; extend transparently if mechanism work is justified')
    env=dict(vars(runmod));env.update(check_epoch=check_epoch,reserve_cost=reserve_cost)
    env['transaction_check']=lr_audit.transaction;env['verify_greedy']=lr_audit.verify_vectors
    # The original PR151 oracle does not export the later final.state format.
    # Compare its available logits/endpoint/transaction metadata, never invent
    # historical serialized-state equality. Candidate checks remain mandatory.
    env['verify_states']=lambda r,p: None
    env['record_check']=lambda r,slot,item,folder:lr_audit.check_record(r,slot,item,folder,binding['families']['Llama'],auditmod)
    exec(compile(s,'pinned_pr159_llama_host_adapter','exec'),env)
    return env['run_unit'],source,s

def prepare(config,out):
    c=read(config);out=Path(out).resolve();need(not out.exists(),'fresh epoch directory')
    need(c.get('user_authorized') is True,'execution authorization required')
    history=Path(c['history']);h=read(history/'HISTORY.json');need(h['status']=='HISTORICAL_RAW_RECONSTRUCTED','reconstruct historical raw first')
    dev=read(history/'DEV.json');refs=read(history/'REFERENCES.json');old=read(history/'ORIGINAL_BINDING.json')
    ident=old['families']['Llama'];build=read(c['build_receipt'])
    need(build['status']=='BUILT_NOT_QUALIFIED' and build['source_variant']=='metadata4','real metadata4 native build required')
    need(build['source_zip_sha256']==ident['source_zip_sha256'],'original source cohort')
    need(build['numerical_modules']==ident['numerical_modules'],'numeric DLL change requires documented source-successor integration')
    need(file_hash(c['original_worker'])==ident['executable_sha256'],'original oracle replaced')
    need(file_hash(c['worker'])==build['executable_sha256'],'candidate build identity')
    for role in ('target','draft'):need(file_hash(c[role])==ident['models'][role]['sha256'],'model bytes changed')
    for x in dev['inputs']:input_check(x)
    research=Path(c['research_root']).resolve();raw=Path(c['raw_history_root']).resolve()
    need(research!=raw and not research.is_relative_to(raw) and not raw.is_relative_to(research),'old raw and new research roots must be disjoint')
    need(c['gpu_uuid']==ident['device_id'],'unexpected GPU; register a separate platform experiment')
    need(c.get('gpu_lock_file') and c.get('gpu_driver'),'record GPU coordination and driver')
    for key in ('min_ram_free_bytes','min_vram_free_bytes','min_disk_free_bytes','max_payload_bytes'):
        need(type(c['resources'][key]) in (int,float) and c['resources'][key]>0,'resource reservation '+key)
    need(c['resources']['min_ram_free_bytes']>=8*1024**3 and c['resources']['min_vram_free_bytes']>=512*1024**2,'do not waive original headroom')
    need(c['resources']['min_disk_free_bytes']>=20*1024**3,'disk reserve')
    parent.verify(c['parent_snapshot']);source_binding=read(c['source_binding'])
    for p,hsh in source_binding['files'].items():need(file_hash(p)==hsh,'staged source changed after build')
    binding=copy.deepcopy(old);binding.update(study_id=STUDY,status='FROZEN_BEFORE_FIRST_NATIVE_REQUEST',is_synthetic=False)
    binding['repair_model']={'layers':32,'embd':4096};binding['dense14b']={'target_gpu_layers':999,'threads':24,
      'min_ram_free_bytes':c['resources']['min_ram_free_bytes'],'min_vram_free_bytes':c['resources']['min_vram_free_bytes']}
    ni=binding['families']['Llama'];ni.update(executable_sha256=build['executable_sha256'],core_sha256=build['core_sha256'],worker_source_sha256=build['worker_source_sha256'])
    policy=read(c['policy']);need(policy.get('prefill') in ('native','reference'),'global prefill policy')
    need(policy.get('mechanism') and policy.get('revision'),'record candidate hypothesis/revision')
    need(policy.get('rowwise_roles',0)==build['repair_spec']['rowwise_roles'],'candidate roles/build mismatch')
    binding['candidate_policy']=policy;out.mkdir(parents=True)
    for name,obj in [('CONFIG.json',c),('BINDING.json',binding),('ORIGINAL_BINDING.json',old),('DEV.json',dev),
      ('DEV_REFERENCES.json',refs),('POLICY.json',policy),('PLAN.json',{'study_id':STUDY,'context':ident['context'],
      'service_timer_definition':'fresh contexts: creation, native/paid producer prefill, speculation, reconciliation, synchronization, teardown; weights loaded separately; all diagnostics excluded from timing'})]:save(out/name,obj)
    assets={str(Path(c[k]).resolve()):file_hash(c[k]) for k in ('target','draft','worker','original_worker','build_receipt','source_binding')}
    assets.update(source_binding['files'])
    for directory in {Path(c['worker']).parent,Path(c['original_worker']).parent}:
        for name,hsh in ident['numerical_modules'].items():need(file_hash(directory/name)==hsh,'DLL cohort drift '+name);assets[str((directory/name).resolve())]=hsh
    inputs={p.name:file_hash(p) for p in out.iterdir() if p.is_file()}
    save(out/'EPOCH.json',{'base':BASE,'created':utc(),'code':code_manifest(),'inputs':inputs,'assets':assets},exclusive=True)
    research.mkdir(parents=True,exist_ok=True);(research/'LEDGER.jsonl').touch(exist_ok=True)
    if not (research/'RESOURCE_POLICY.jsonl').exists():amend_budget(research,c['resource_policy'],'Initial author-authorized Llama mechanism development and independent validation')
    return out

def execute(bundle,name,panel,slots,original=False,admit=False):
    bundle=Path(bundle);c=check_epoch(bundle);_,runmod,auditmod=parent.load(c['parent_snapshot'])
    # Additional gates cover diagnostic modes not known to the inherited runner.
    for s in slots:
        input_check(panel['inputs'][s['source_index']])
        need(s['family']=='Llama' and s['lifecycle']=='fresh','do not change family/lifecycle')
        if s['category'] in ('qualification','measured','warmup'):
            need(s.get('llama_diag',{}).get('mode','off')=='off' and s['repair']['trace']['mode']=='off','diagnostic leakage')
            seal=read(bundle/'CANDIDATE_FREEZE.json');need(seal['heldout_sha256']==file_hash(bundle/'HELDOUT.json'),'confirmation panel changed')
            need(digest(panel)==digest(read(bundle/'HELDOUT.json')),'unfrozen confirmation input')
        if s['category'] in ('measured','warmup'):need((bundle/'QUALIFICATION_PASS.json').exists(),'qualification gate absent')
    # Register output exposure before launching; a failed process is still exposure.
    if not admit:
        exposure=Path(c['research_root'])/'EXPOSURES.jsonl'
        freeze=file_hash(bundle/'CANDIDATE_FREEZE.json') if (bundle/'CANDIDATE_FREEZE.json').exists() else None
        with exposure.open('a',encoding='utf-8',newline='\n') as f:
            for i in sorted({s['source_index'] for s in slots}):
                x=panel['inputs'][i]
                f.write(json.dumps({'utc':utc(),'epoch':str(bundle),'unit':name,'freeze':freeze,
                  **{k:x.get(k) for k in ('id','text_sha256','prompt_ids_sha256')}})+'\n')
            f.flush();os.fsync(f.fileno())
    binding=read(bundle/('ORIGINAL_BINDING.json' if original else 'BINDING.json'))
    fn,before,after=derive_driver(runmod,auditmod,binding,original)
    auditdir=bundle/'HOST_ADAPTER';auditdir.mkdir(exist_ok=True)
    (auditdir/'original.py').write_text(before,encoding='utf-8');(auditdir/'adapted.py').write_text(after,encoding='utf-8')
    rows=fn(bundle,name,panel,slots,original=original,admit=admit)
    if not admit:
        for r,s in zip(rows,slots):lr_audit.check_record(r,s,panel['inputs'][s['source_index']],bundle/'units'/name/'native'/s['slot_id'],binding['families']['Llama'],auditmod,original)
    return rows

def seal(bundle,panel,mechanism,development,regression):
    bundle=Path(bundle);c=check_epoch(bundle);need(not (bundle/'CANDIDATE_FREEZE.json').exists(),'candidate already frozen')
    m=read(mechanism);d=read(development);r=read(regression);pan=read(panel)
    need(m.get('status')=='MECHANISM_REVIEWED' and m.get('reference_unchanged') is True and m.get('no_task_specific_rule') is True and m.get('ablation_passed') is True,'mechanism/ablation review missing')
    need(d['all_reference_equal'] and d['all_observer_equal'],'development not reference-preserving')
    need(r.get('status')=='CROSS_MODEL_REGRESSION_PASS' and set(r.get('families',[]))>={'Qwen3-8B','Qwen3-14B'},'both Qwen regressions required')
    for report in (m,r):
        need(report.get('evidence'),'evidence-backed review, not a bare PASS flag')
        for p,h in report['evidence'].items():need(file_hash(p)==h,'review evidence changed')
    need(len(pan['inputs'])>=12 and len(pan['inputs'])%12==0,'crossed held-out panel count')
    for x in pan['inputs']:input_check(x)
    dev=read(bundle/'DEV.json')
    for k in ('id','text_sha256','prompt_ids_sha256'):
        need(all(x.get(k) for x in pan['inputs']),'missing held-out exposure field')
        need(not {x[k] for x in pan['inputs']}&{x[k] for x in dev['inputs']},'development/held-out overlap')
        need(len({x[k] for x in pan['inputs']})==len(pan['inputs']),'duplicate held-out input')
    need(pan.get('source_pool_sha256') and pan.get('exposure_sha256'),'selection/exposure manifests required')
    exposure=Path(c['research_root'])/'EXPOSURES.jsonl'
    seen=[json.loads(l) for l in exposure.read_text().splitlines() if l] if exposure.exists() else []
    for key in ('id','text_sha256','prompt_ids_sha256'):
        need(not {x[key] for x in pan['inputs']}&{x[key] for x in seen if x.get(key)},'confirmation input was already exposed in this research ledger')
    save(bundle/'HELDOUT.json',pan,exclusive=True)
    save(bundle/'CANDIDATE_FREEZE.json',{'utc':utc(),'epoch_sha256':file_hash(bundle/'EPOCH.json'),
      'heldout_sha256':file_hash(bundle/'HELDOUT.json'),'mechanism_sha256':file_hash(mechanism),
      'development_sha256':file_hash(development),'regression_sha256':file_hash(regression),
      'selection':'frozen before original or candidate output exposure; no reused failed panel'},exclusive=True)

def unit_records(bundle,name,expected,panel,original=False):
    root=Path(bundle)/'units'/name;r=read(root/'RECEIPT.json');need(r['success'] and r['active_processes_after_wait']==0,'failed/incomplete unit retained; no automatic retry')
    need(read(root/'SLOTS.json')==expected and read(root/'PANEL.json')==panel,'resumed schedule/panel differs')
    c=check_epoch(bundle);_,_,pa=parent.load(c['parent_snapshot'])
    binding=read(Path(bundle)/('ORIGINAL_BINDING.json' if original else 'BINDING.json'))
    rows=[]
    for s in expected:
        v=read(root/'native'/(s['slot_id']+'.json'))
        lr_audit.check_record(v,s,panel['inputs'][s['source_index']],root/'native'/s['slot_id'],binding['families']['Llama'],pa,original)
        rows.append(v)
    return rows

def confirm(bundle):
    bundle=Path(bundle);check_epoch(bundle);pan=read(bundle/'HELDOUT.json');policy=read(bundle/'POLICY.json')
    oslots=schedule.original_references(pan)
    old=unit_records(bundle,'original_references',oslots,pan,True) if (bundle/'units/original_references').exists() else execute(bundle,'original_references',pan,oslots,True)
    refs={};oldheavy={}
    for i,x in enumerate(pan['inputs']):
        rs=[r for r in old if r['input_id']==x['id']];need(len(rs)==2 and endpoint(rs[0])==endpoint(rs[1]),'unstable original oracle')
        refs[x['id']]=endpoint(rs[0]);oldheavy[x['id']]=next(r for r in rs if r['slot']['observer']=='heavy')
    slots=schedule.qualification(pan,policy)
    rows=unit_records(bundle,'qualification',slots,pan) if (bundle/'units/qualification').exists() else execute(bundle,'qualification',pan,slots)
    result=lr_audit.matrix(rows,slots,refs);save(bundle/'QUALIFICATION_AUDIT.json',result)
    need(result['all_reference_equal'] and result['all_observer_equal'],'held-out failure: this panel is now exposed; return to development, do not time a success subset')
    # Ensure candidate R has not silently become a different oracle.
    for r in rows:
        if r['slot']['arm']=='R' and r['slot']['observer']=='heavy':
            oldr=oldheavy[r['input_id']]
            a=bundle/'units/original_references/native'/oldr['slot']['slot_id'];b=bundle/'units/qualification/native'/r['slot']['slot_id']
            need(lr_audit.verify_vectors(oldr,a)==lr_audit.verify_vectors(r,b),'candidate R decision vectors differ from original R')
    save(bundle/'QUALIFIED_REFERENCES.json',refs);save(bundle/'QUALIFICATION_PASS.json',{'utc':utc(),'audit_sha256':file_hash(bundle/'QUALIFICATION_AUDIT.json'),'candidate_R_vectors_equal_original':True})
    measured=[]
    for s in range(6):
        name=f'formal{s}';slots=schedule.timing(pan,policy,s)
        measured+=unit_records(bundle,name,slots,pan) if (bundle/'units'/name).exists() else execute(bundle,name,pan,slots)
    result=lr_audit.performance(measured,refs,len(pan['inputs']));save(bundle/'FINAL_COST.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('prepare');a.add_argument('--config',required=True);a.add_argument('--out',required=True)
    for cmd in ('admit','development','confirm'):
        a=sub.add_parser(cmd);a.add_argument('--bundle',required=True)
    a=sub.add_parser('run');a.add_argument('--bundle',required=True);a.add_argument('--name',required=True);a.add_argument('--panel',required=True);a.add_argument('--slots',required=True)
    a=sub.add_parser('seal')
    for n in ('bundle','panel','mechanism','development','regression'):a.add_argument('--'+n,required=True)
    a=sub.add_parser('budget')
    for n in ('research-root','limits','reason'):a.add_argument('--'+n,required=True)
    a=p.parse_args()
    if a.cmd=='prepare':print(prepare(a.config,a.out))
    elif a.cmd=='budget':print(amend_budget(a.research_root,read(a.limits),a.reason))
    elif a.cmd=='seal':seal(a.bundle,a.panel,a.mechanism,a.development,a.regression)
    elif a.cmd=='confirm':print(confirm(a.bundle)['status'])
    elif a.cmd=='run':execute(a.bundle,a.name,read(a.panel),read(a.slots))
    else:
        b=Path(a.bundle);pan=read(b/'DEV.json');slots=schedule.development(pan)
        rows=execute(b,'admission' if a.cmd=='admit' else 'development',pan,slots[:1] if a.cmd=='admit' else slots,admit=a.cmd=='admit')
        if rows:save(b/'DEVELOPMENT_AUDIT.json',lr_audit.matrix(rows,slots,read(b/'DEV_REFERENCES.json')))
