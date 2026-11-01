"""Pinned old-model regressions sharing the development ledger and Windows driver.
The 14B runner and candidate binary are not modified by this integration.
"""
import argparse,copy,inspect,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from common import *
import run,plan,audit

def git_json(repo,path):return json.loads(git_read(repo,BASE,path))

def profile_check(r,s,item,folder,binding):
    family=s['family'];need(family in ('Qwen','Llama') and r['family']==family,'regression family')
    need(r['identity']==binding['families'][family],'regression executable/model identity')
    need(r['slot']==s and r['input_id']==item['id'] and r['prompt_ids']==item['prompt_ids'] and r['prompt_ids_sha256']==item['prompt_ids_sha256'],'regression input identity')
    need(not r['teacher_forced'] and r['qualification_eligible'] and r['observer_mode']=='off','natural regression only')
    need(r['repair_prefill']==s['repair']['prefill'],'producer identity');audit.transaction_check(r)
    if r['repair_prefill']!='native':
        b=r['boundary'];need(b['positions_equal'] and not b['pending_token_consumed'] and b['pending_token']==r['ids'][0],'sham semantics')
        if s['observer']=='heavy':need(b['receiver_readback_checked'] and b['serialized_bytes_equal'],'sham byte roundtrip')
    if s['observer']=='heavy':
        audit.geometry_check(r['geometry'] or r['boundary'].get('producer_geometry',[]),32);audit.verify_states(r,folder)
        best={};n=151936 if family=='Qwen' else 128256
        for role in ('target','draft'):
            for p in sorted((Path(folder)/role).glob('*.f32')):best[p.relative_to(folder).as_posix()]=audit.full_vector(p,n)[0]
        need(best['target/initial.f32']==r['ids'][0],'initial argmax')
        if not r['draft_enabled']:
            for i,t in enumerate(r['ids'][1:],1):need(best[f'target/ordinary-{i}.f32']==t,'ordinary argmax')
        else:
            for cycle in r['cycles']:
                for i,t in enumerate(cycle['proposals']):need(best[f'draft/proposal-{cycle["cycle"]}-{i}.f32']==t,'draft argmax')
                for i,t in enumerate(cycle['decisions']):need(best[f'target/verify-{cycle["cycle"]}-{i}.f32']==t,'verify argmax')
    return endpoint(r)

def derived_driver(binding):
    # Preserve the complete Job/lock/timeout/resource/ledger implementation.
    # The sole textual adaptation is the already-bound family argument.
    source=inspect.getsource(run.run_unit);anchor="'Qwen',str(bundle/"
    need(source.count(anchor)==1,'driver family anchor drift')
    changed=source.replace(anchor,"c['regression_family'],str(bundle/")
    env=dict(vars(run));env['record_check']=lambda r,s,x,p:profile_check(r,s,x,p,binding)
    exec(compile(changed,'source_bound_regression_driver','exec'),env)
    return env['run_unit'],source,changed

def prepare(repo,family,build_path,worker,out):
    repo=Path(repo).resolve();out=Path(out).resolve();need(not out.exists(),'fresh regression epoch');need(family in ('Qwen','Llama'),'registered regression family only')
    base='benchmarks/rtx_scope_transfer_v1/';old_root=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/repo/work/scope-transfer-bundle-v1') if family=='Qwen' else Path('D:/rtx151-llama-diagnostic-v2')
    if family=='Qwen':
        identity=git_json(repo,base+'host_execution/EXECUTION_IDENTITY.json');panel={'inputs':git_json(repo,base+'PANEL.json')['families']['Qwen']}
        frozen_refs=git_json(repo,base+'host_execution/REFERENCES.json');refs={x['id']:frozen_refs['endpoints'][x['reference_id']]['endpoint'] for x in panel['inputs']}
        local=read(old_root/'LOCAL_PATHS.json')['Qwen'];recipes=[('R','native'),('R','reference'),('M_PQ','native'),('M_QB','native'),('C_PQ','native'),('C_QB','native')]
        source_paths=[base+'PANEL.json',base+'host_execution/REFERENCES.json',base+'host_execution/EXECUTION_IDENTITY.json']
    else:
        prefix=base+'sidecar_execution/diagnostic/';identity=git_json(repo,prefix+'EXECUTION_IDENTITY.json');oldpanel=git_json(repo,prefix+'PANEL.json');indices=[8,6,3]
        panel={'inputs':[oldpanel['inputs'][i] for i in indices]};frozen_refs=git_json(repo,prefix+'REFERENCES.json');refs={oldpanel['inputs'][i]['id']:frozen_refs[str(i)]['R'] for i in indices}
        local=read(old_root/'LOCAL_PATHS.json');recipes=[('R','native'),('R','reference'),('C_PQ','native'),('C_QB','native')]
        source_paths=[prefix+'PANEL.json',prefix+'REFERENCES.json',prefix+'EXECUTION_IDENTITY.json']
    original=identity['families'][family];build=read(build_path)
    need(build['status']=='BUILT_NOT_QUALIFIED' and build['source_zip_sha256']==original['source_zip_sha256'],'family source binding')
    need(build['numerical_modules']==original['numerical_modules'],'family numerical DLL cohort')
    need(build['repair_spec']['rowwise_roles']==0 and build['repair_spec']['stable_norm_offload'] is True,'same candidate intervention required')
    need(file_hash(worker)==build['executable_sha256'] and file_hash(local['executable'])==original['executable_sha256'],'old/new executable identity')
    for role in ('target','draft'):need(file_hash(local[role])==original['models'][role]['sha256'],'original model identity')
    for item in panel['inputs']:
        valid_input(item);need(max(item['prompt_ids'])<(151936 if family=='Qwen' else 128256),'family vocabulary')
    binding=copy.deepcopy(identity);binding['study_id']=STUDY;binding['repair_model']={'layers':32,'embd':4096};binding['dense14b']={'target_gpu_layers':999,'threads':24,'min_ram_free_bytes':8*1024**3,'min_vram_free_bytes':1024**3}
    bound=binding['families'][family];bound.update(executable_sha256=build['executable_sha256'],core_sha256=build['core_sha256'],worker_source_sha256=build['worker_source_sha256'])
    policy={'prefill':'native','rowwise_roles':0,'stable_norm_offload':True,'revision':'dev03-regression','mechanism':'Same head-normalization offload preference; original family source, models and reference'};binding['candidate_policy']=policy
    candidate=read('D:/rtx158/config03/HOST_CONFIG.json');cfg=dict(candidate,regression_family=family,parent_root=str(old_root),target=local['target'],draft=local['draft'],original_worker=local['executable'],worker=str(Path(worker).resolve()),build_receipt=str(Path(build_path).resolve()),policy=str(out/'POLICY.json'))
    slots=[]
    for i in range(len(panel['inputs'])):
        for arm,prefill in recipes:
            for observer in ['off','heavy']:
                s=plan.slot(panel,i,arm,prefill,observer,f'regression/{family}/i{i:02d}/{arm}/{prefill}/{observer}','development');s['family']=family;s['lifecycle']='resident' if family=='Qwen' else 'fresh';slots.append(s)
    need(len(slots)==(144 if family=='Qwen' else 24),'fixed complete regression matrix')
    out.mkdir(parents=True)
    for n,x in [('CONFIG.json',cfg),('BINDING.json',binding),('DEV.json',panel),('POLICY.json',policy),('DEV_REFERENCES.json',refs),('ORIGINAL_BINDING.json',identity),('PLAN.json',{'context':original['context'],'service_timer_definition':'Regression only; no performance estimate'}),('SLOTS.json',slots)]:save(out/n,x)
    assets={str(Path(p).resolve()):file_hash(p) for p in [local['target'],local['draft'],local['executable'],worker,build_path,__file__]}
    for directory in {Path(worker).parent,Path(local['executable']).parent}:
        for name,h in original['numerical_modules'].items():need(file_hash(directory/name)==h,'DLL path changed');assets[str((directory/name).resolve())]=h
    files=['CONFIG.json','BINDING.json','DEV.json','POLICY.json','DEV_REFERENCES.json','PLAN.json','ORIGINAL_BINDING.json','SLOTS.json'];save(out/'EPOCH.json',{'base':BASE,'created':utc(),'code':run.local_code(),'inputs':{n:file_hash(out/n) for n in files},'assets':assets},exclusive=True)
    fn,source,changed=derived_driver(binding);(out/'ORIGINAL_HOST_DRIVER.py').write_text(source,encoding='utf-8',newline='\n');(out/'DERIVED_HOST_DRIVER.py').write_text(changed,encoding='utf-8',newline='\n')
    save(out/'REGRESSION_SOURCE.json',{'family':family,'source_commit':BASE,'source_files':{p:hashlib.sha256(git_read(repo,BASE,p)).hexdigest() for p in source_paths},'original_worker':local['executable'],'original_worker_sha256':original['executable_sha256'],'candidate_worker_sha256':build['executable_sha256'],'requests':len(slots),'original_source_indices':[x['source_index'] for x in panel['inputs']],'shared_ledger':str(Path(cfg['research_root'])/'LEDGER.jsonl'),'scope':'Previously exposed old-model regression, not blind transfer. Llama retains original known failure and two controls; report original-R preservation separately from reproduction of the old failure.','driver_adaptation':'Same source-bound run_unit except family argument and model-bound vector/geometry checker; no change to budget, Job, lock or timeouts.'},exclusive=True)
    print(out,len(slots))

def execute(bundle,admit=False):
    bundle=Path(bundle);binding=read(bundle/'BINDING.json');fn,_,_=derived_driver(binding);panel=read(bundle/'DEV.json');slots=read(bundle/'SLOTS.json');name='admission01' if admit else 'regression01'
    rows=fn(bundle,name,panel,slots[:1] if admit else slots,admit=admit)
    if not admit:
        result=audit.matrix(rows,panel,slots,read(bundle/'DEV_REFERENCES.json'));result['epoch_sha256']=file_hash(bundle/'EPOCH.json');result['raw_hashes']={s['slot_id']:file_hash(bundle/'units'/name/'native'/(s['slot_id']+'.json')) for s in slots};save(bundle/'REGRESSION_AUDIT.json',result,exclusive=True);print(result['status'],result['all_reference_equal'],result['observer_errors'])

if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True);a=sub.add_parser('prepare')
    for n in ['repo','family','build','worker','out']:a.add_argument('--'+n,required=True)
    for name in ['admit','run']:a=sub.add_parser(name);a.add_argument('--bundle',required=True)
    a=p.parse_args()
    if a.cmd=='prepare':prepare(a.repo,a.family,a.build,a.worker,a.out)
    else:execute(a.bundle,a.cmd=='admit')
