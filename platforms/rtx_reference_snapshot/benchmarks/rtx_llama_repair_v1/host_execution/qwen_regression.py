"""New Qwen regressions on pinned old panels and the shared Llama-study ledger."""
import argparse
import copy
import importlib.util
import inspect
import json
from pathlib import Path
import sys


def initialize(repo):
    sys.path.insert(0,str(Path(repo)/'scripts/experiments/rtx_llama_repair_v1'))
    global host,parent,read,save,need,file_hash,utc,once,STUDY
    import host,parent
    from lr_common import read,save,need,file_hash,utc,once,STUDY


def check_epoch(bundle):
    seal=read(Path(bundle)/'EPOCH.json')
    for name,h in seal['inputs'].items():need(file_hash(Path(bundle)/name)==h,'regression input drift')
    for name,h in seal['assets'].items():need(file_hash(name)==h,'regression asset/source drift')
    c=read(Path(bundle)/'CONFIG.json');parent.verify(c['parent_snapshot'])
    budget=host.budget_current(c['research_root'])
    c['request_limit']=budget['request_credits'];c['development_limit']=budget['development_credits']
    c['resources'].update(total_native_seconds=budget['total_native_seconds'],worker_timeout_seconds=budget['worker_timeout_seconds'])
    return c


def driver(snapshot,binding):
    _,run,audit=parent.load(snapshot)
    spec=importlib.util.spec_from_file_location('pinned_qwen_regression',Path(snapshot)/'diagnostics/regression.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.model_geometry=lambda family: binding['repair_model']
    def check(r,slot,item,folder):
        module.profile_check(r,slot,item,folder,binding)
        if slot['observer']=='heavy':
            expected={'target/initial.f32'}
            if r['draft_enabled']:
                for cycle in r['cycles']:
                    expected.update(f'draft/proposal-{cycle["cycle"]}-{i}.f32' for i in range(r['k']))
                    expected.update(f'target/verify-{cycle["cycle"]}-{i}.f32' for i in range(r['k']+1))
            else:expected.update(f'target/ordinary-{i}.f32' for i in range(1,len(r['ids'])))
            actual={p.relative_to(folder).as_posix() for role in ('target','draft') for p in (Path(folder)/role).glob('*.f32')}
            need(actual==expected,'missing or extra regression decision vectors')
    original=inspect.getsource(run.run_unit);changed=original
    changed=once(changed,'used+(0 if admit else len(schedule))<=1200',"used+(0 if admit else len(schedule))<=c['request_limit']")
    changed=once(changed,'dev_used+(0 if admit else len(schedule))<=480',"dev_used+(0 if admit else len(schedule))<=c['development_limit']")
    env=dict(vars(run));env.update(check_epoch=check_epoch,record_check=check)
    exec(compile(changed,'source_bound_qwen_regression_driver','exec'),env)
    return env['run_unit'],original,changed,audit


def prepare(args):
    config=read(args.config);oldroot=Path(config['original_bundle']);build=read(config['build_receipt'])
    oldcfg=read(oldroot/'CONFIG.json');oldseal=read(oldroot/'EPOCH.json')
    for name in ('BINDING.json','ORIGINAL_BINDING.json','DEV.json','DEV_REFERENCES.json','PLAN.json'):
        need(file_hash(oldroot/name)==oldseal['inputs'][name],'prior bundle input changed '+name)
    original=read(oldroot/'ORIGINAL_BINDING.json');oldbinding=read(oldroot/'BINDING.json')
    identity=original['families']['Qwen']
    need(build['source_variant']=='original' and build['source_zip_sha256']==identity['source_zip_sha256'],'original Qwen source cohort')
    need(build['numerical_modules']==identity['numerical_modules'],'original Qwen numerical DLLs')
    need(build['repair_spec']['stable_norm_offload'] and build['repair_spec']['rowwise_roles']==0,'combined policy')
    binding=copy.deepcopy(oldbinding);binding['study_id']=STUDY;binding['candidate_policy']=read(config['policy'])
    binding['families']['Qwen'].update(executable_sha256=build['executable_sha256'],core_sha256=build['core_sha256'],worker_source_sha256=build['worker_source_sha256'])
    need(file_hash(config['worker'])==build['executable_sha256'],'new Qwen worker identity')
    need(file_hash(oldcfg['original_worker'])==identity['executable_sha256'],'old Qwen oracle identity')
    for role in ('target','draft'):need(file_hash(oldcfg[role])==identity['models'][role]['sha256'],'original Qwen model')
    qsource=read(config['source_binding']);lsource=read(config['llama_source_binding'])
    qstage=Path(qsource['stage']);lstage=Path(lsource['stage'])
    for name in ('prefix_extent.py','repair_offload.hpp'):
        need(file_hash(qstage/name)==file_hash(lstage/name),'cross-family source policy mismatch')
    panel=read(oldroot/'DEV.json');refs=read(oldroot/'DEV_REFERENCES.json')
    if config['profile']=='Qwen3-14B':
        need(file_hash(oldroot/'HELDOUT.json')==oldseal['inputs']['HELDOUT.json'],'prior panel changed')
        panel={'inputs':panel['inputs']+read(oldroot/'HELDOUT.json')['inputs']}
        refs={**refs,**read(oldroot/'QUALIFIED_REFERENCES.json')}
    else:need(config['profile']=='Qwen3-8B','registered Qwen profile')
    need(len({x['id'] for x in panel['inputs']})==len(panel['inputs']),'duplicate regression input')
    _,_,audit=parent.load(config['parent_snapshot'])
    import plan
    slots=[]
    for i in range(len(panel['inputs'])):
        for arm,producer in [('R','native'),('R','reference'),('M_PQ','native'),('M_QB','native'),('C_PQ','native'),('C_QB','native')]:
            for observer in ('off','heavy'):
                slot=plan.slot(panel,i,arm,producer,observer,f'regression/i{i:02d}/{arm}/{producer}/{observer}','development')
                slot.update(study_id=STUDY,family='Qwen',lifecycle='resident');slots.append(slot)
    cfg={**config,'target':oldcfg['target'],'draft':oldcfg['draft'],'original_worker':oldcfg['original_worker']}
    out=Path(args.out);need(not out.exists(),'fresh regression epoch');out.mkdir(parents=True)
    for name,value in [('CONFIG.json',cfg),('BINDING.json',binding),('ORIGINAL_BINDING.json',original),('DEV.json',panel),
                       ('DEV_REFERENCES.json',refs),('POLICY.json',binding['candidate_policy']),('SLOTS.json',slots),
                       ('PLAN.json',{'context':read(oldroot/'PLAN.json')['context'],'service_timer_definition':'New cross-model regression; no timing estimate'})]:save(out/name,value)
    _,before,after,_=driver(cfg['parent_snapshot'],binding)
    (out/'ORIGINAL_HOST_DRIVER.py').write_text(before);(out/'DERIVED_HOST_DRIVER.py').write_text(after)
    assets={str(Path(p).resolve()):file_hash(p) for p in [__file__,cfg['target'],cfg['draft'],cfg['worker'],cfg['original_worker'],cfg['build_receipt'],cfg['source_binding'],cfg['llama_source_binding']]}
    assets.update(qsource['files']);assets.update(lsource['files'])
    for name in ('host.py','parent.py','lr_common.py'):
        path=Path(cfg['repo'])/'scripts/experiments/rtx_llama_repair_v1'/name;assets[str(path)]=file_hash(path)
    for directory in {Path(cfg['worker']).parent,Path(cfg['original_worker']).parent}:
        for name,h in identity['numerical_modules'].items():need(file_hash(directory/name)==h,'Qwen DLL mismatch');assets[str(directory/name)]=h
    save(out/'EPOCH.json',{'created':utc(),'inputs':{p.name:file_hash(p) for p in out.iterdir() if p.is_file()},'assets':assets,
                          'original_epoch_sha256':file_hash(oldroot/'EPOCH.json'),'scope':'Previously exposed panels; new original-cohort executions under the combined policy.'},exclusive=True)
    print('REGRESSION_PREPARED',config['profile'],len(slots))


def execute(bundle,admit):
    b=Path(bundle);cfg=check_epoch(b);binding=read(b/'BINDING.json')
    fn,_,_,audit=driver(cfg['parent_snapshot'],binding);panel=read(b/'DEV.json');slots=read(b/'SLOTS.json')
    rows=fn(b,'admission' if admit else 'regression',panel,slots[:1] if admit else slots,admit=admit)
    if rows:
        result=audit.matrix(rows,panel,slots,read(b/'DEV_REFERENCES.json'))
        result['profile']=cfg['profile'];result['epoch_sha256']=file_hash(b/'EPOCH.json')
        result['raw_record_sha256']={s['slot_id']:file_hash(b/'units/regression/native'/(s['slot_id']+'.json')) for s in slots}
        save(b/'REGRESSION_AUDIT.json',result,exclusive=True)
        print(cfg['profile'],result['all_reference_equal'],result['observer_errors'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','admit','run']);p.add_argument('--repo',required=True)
    p.add_argument('--config');p.add_argument('--out');p.add_argument('--bundle');args=p.parse_args();initialize(args.repo)
    if args.command=='prepare':prepare(args)
    else:execute(args.bundle,args.command=='admit')
