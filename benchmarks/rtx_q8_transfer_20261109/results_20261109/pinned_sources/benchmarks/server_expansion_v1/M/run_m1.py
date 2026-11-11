"""M1 native integration using the immutable qualified PR203 supervisor/readers.

This module adds lane-specific slot admission and reuses existing native finite
checks. The original worktree, ledger, reference and executable are read-only.
"""
from pathlib import Path
import argparse, copy, datetime, importlib.util, json, os, sys

ARMS={'W_L4_D4':('loop4','SIMPLE',True),'W_P_D4':('packed','SIMPLE',True),
      'L_L4_D4':('loop4','LOCAL',True),'L_P_D4':('packed','LOCAL',True)}

def load_runtime(path):
    sys.dont_write_bytecode=True;sys.path.insert(0,str(path))
    global need,read,save,sha,host,native,checks,freeze,shared
    from common import need,read,save,sha
    import host,qualify_native as native,native_checks as checks,freeze
    spec=importlib.util.spec_from_file_location('m1_shared',Path(__file__).parents[1]/'shared/experiment.py');shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
    host.confirmation_identity=confirmation_identity

def confirmation_identity(frozen,build_path,build,job_path,out,reserved):
    path=Path(frozen['plan']['path']).resolve();need(sha(path)==frozen['plan']['sha256'],'Frozen M1 plan changed')
    p=read(path);workers={x['id']:x for x in p['workers']}
    need(p['study']=='server_m_v1' and p['panel']=='attribution' and len(workers)==len(p['workers'])==16,'Exactly16 M1 workers')
    need(p['measurements']==256 and p['primers']==32 and set(p['arms'])==set(ARMS),'Frozen M1 budget/arms')
    out=Path(out).resolve();slot=workers.get(out.name)
    need(slot is not None and out==path.parent/'runs'/slot['id'],'Unregistered M1 output slot')
    need(Path(job_path).resolve()==path.parent/slot['job'] and sha(job_path)==slot['job_sha256'],'Different frozen slot job')
    need(build['role']==slot['core'],'Different numerical core for frozen slot')
    known=frozen['executables'].get(build['executable_sha256']);need(known is not None and sha(build_path)==known['build']['sha256'],'Different frozen build')
    for row in reserved:
        if row['phase']!='confirmation':continue
        prior=workers.get(Path(row['out']).name)
        need(prior is not None and Path(row['out']).resolve()==path.parent/'runs'/prior['id'],'Unresolved prior confirmation identity')
        need(row['job_sha256']==prior['job_sha256'] and row['plan_sha256']==frozen['plan']['sha256'],'Prior slot/plan binding changed')
        need(prior['id']!=slot['id'],'Frozen confirmation slot already reserved; no selective retry')
    return {'confirmation_slot_id':slot['id'],'plan_sha256':frozen['plan']['sha256'],'build_sha256':sha(build_path)}

def capability(models,structures,core,cut):
    topology=lambda s:{k:s[k] for k in ('layers','query_heads','kv_heads','head_k','head_v','K_elements','V_elements')}
    def ctx(ub,out):return dict(n_ctx=1024,n_batch=1024,n_ubatch=ub,outputs_max=out,outputs_per_seq=out,flash_attention=False,type_k='f16',type_v='f16')
    place=lambda s:dict(layers=['NVIDIA RTX A5000']*s['layers'],output='NVIDIA RTX A5000')
    return dict(schema='heterospec.m1.native-capability.v1',target_sha256=models['target_sha256'],draft_sha256=models['draft_sha256'],
        target_structure=topology(structures['target']),draft_structure=topology(structures['draft']),target_context=ctx(32,4),draft_context=ctx(4,1),
        target_placement=place(structures['target']),draft_placement=place(structures['draft']),k=3,draft_width=4,cut=cut,projection=core,
        threads=2,greedy=True,target_output_policy='PREFILL:last;VERIFY:all_original_rows',draft_output_policy='last',
        physical_rows_evidence='per-request executions and native physical width histograms')

def make_study(w,baseline,repo,builds):
    class M1Study(native.Study):
        def __init__(self):
            self.w=w;self.baseline=baseline;self.repo=repo;self.builds=builds;self.out=w/'qualification-01';need(not self.out.exists(),'Preserve all epochs');self.out.mkdir()
            self.cfg=w/'config.json';self.models=read(baseline/'inputs-01/MODELS.json');self.trace,self.parse=checks.legacy_readers(repo)
            self.modules={};self.reports=[];self.ref_build=baseline/'build-R-01/BUILD.json'
            self.profiles=read(baseline/'qualification-02/STATE_PROFILES.json');self.structures=read(baseline/'qualification-02/MODEL_STRUCTURES.json')
            self.fullstructures={family:{role:checks.gguf_structure(m[role+'_model']) for role in ('target','draft')} for family,m in self.models.items()}
            self.reuse=[];self.text_index={r['path']:r['raw_sha256'] for r in read(baseline.parent/'public-export-final-01/TEXT_INDEX.json')['files']}
            self.binary_index={r['path']:r['sha256'] for r in read(baseline.parent/'public-export-final-01/BINARY_CAPTURE_INDEX.json')['files']};self.verified=set()
            old=baseline/'qualification-02/NATIVE_CHECKS_COMPLETE.json';need(read(old)['passed'],'Actual qualified successor required')
            for r in read(old)['proofs']:need(sha(r['path'])==r['sha256'],'Historical proof changed')
            self.verify_text(baseline/'qualification-02/MODEL_STRUCTURES.json');self.verify_text(baseline/'qualification-02/STATE_PROFILES.json')
            save(self.out/'SOURCE_REVIEW.json',dict(passed=True,qualified_successor='592abdfe9267fd97ecbde18cd0ee9a1bfc319e20',
                independent_R_freeze_sha256=sha(baseline/'reference-01/REFERENCE_FREEZE.json'),original_qualification_sha256=sha(old),
                observer_build_complete_sha256=sha(builds/'BUILD_COMPLETE.json'),native_capability_source_sha256=sha(Path(__file__).parent/'native/capability.hpp'),
                numerical_archives_unchanged=True,old_geometry_evidence='All12 cases/family and four cut/projection controls qualified in immutable predecessor; M1 adds four real D4 native transactions'))
        def verify_text(self,p):
            key=str(p.relative_to(baseline));need(key in self.text_index and sha(p)==self.text_index[key],'Historical public text commitment changed: '+key)
        def verify_binary(self,p):
            p=Path(p)
            if not p.is_relative_to(baseline) or str(p) in self.verified:return
            key=str(p.relative_to(baseline));need(key in self.binary_index and sha(p)==self.binary_index[key],'Historical binary commitment changed: '+key);self.verified.add(str(p))
        def retained_reference(self,label,expected=None):
            out=baseline/'qualification-02/runs'/label;job=baseline/'qualification-02/jobs'/(label+'.json')
            if not out.exists() or expected is not None and read(job)!=expected:return None
            for p in (job,out/'launch.json',out/'HOST.json',out/'native/result.json',out/'LOADED_MODULES.json'):self.verify_text(p)
            launch=read(out/'launch.json');need(read(out/'HOST.json')['status']=='COMPLETE' and launch['job_sha256']==sha(job) and launch['build_sha256']==sha(self.ref_build),'Historical R launch binding')
            for p,r in read(out/'LOADED_MODULES.json').items():
                if r['kind']=='ELF_file':need(sha(p)==r['sha256'],'Historical R module changed')
            self.reuse.append(dict(label=label,job_sha256=sha(job),launch_sha256=sha(out/'launch.json'),new_requests=0))
            return out
        def execute(self,label,family,job,core='reference'):
            base=copy.deepcopy(self.models[family]);base.update(job)
            if core=='reference':
                base.pop('draft_model',None);base.pop('draft_sha256',None);base.update(residency='target_only',draft=False)
                old=self.retained_reference(label,base)
                if old:
                    self.modules.setdefault((core,family),old/'LOADED_MODULES.json');return old
            else:base['capability_request']=capability(self.models[family],self.fullstructures[family],core,base['lowering'])
            path=self.out/'jobs'/(label+'.json');save(path,base);dest=self.out/'runs'/label
            build=self.ref_build if core=='reference' else builds/core/'BUILD.json'
            host.run(self.cfg,build,path,dest,'reference' if core=='reference' else 'development')
            self.modules.setdefault((core,family),dest/'LOADED_MODULES.json')
            need(read(self.modules[(core,family)])==read(dest/'LOADED_MODULES.json'),'Actual modules changed')
            if core!='reference':need(read(dest/'native/CAPABILITY.json')==base['capability_request'],'Native complete capability gate')
            return dest
    original_bank=native.Bank
    class ReusedBank(original_bank):
        def __init__(self,s,family,index,input,free):
            self.s=s;self.family=family;self.index=index;self.input=input;self.free=free;self.entries={};self.teacher_count=100;self.ep=read(free/'receipt.json')
            s.verify_text(free/'receipt.json')
            paths=sorted((baseline/'qualification-02/jobs').glob(family+f'-root{index}-R-*.json'));need(paths,'Independent R prefix bank required')
            for job in paths:
                out=s.retained_reference(job.stem);need(out is not None,'Complete independent R bank required');self.add(out,read(job)['cases'])
        def add(self,out,cases):
            for case in cases:
                for n in case['observe_positions']:
                    p=out/'native'/case['name']/'captures'/str(n);self.s.verify_binary(p/'frontier.f32')
                    if n in case['state_positions']:self.s.verify_binary(p/'sequence.bin')
            super().add(out,cases)
    s=M1Study()
    # All actually consumed historical comparison operands are checked against
    # the published predecessor's raw binary commitments, including cap1.
    for function in ('vector_pair','state_pair'):
        original=getattr(checks,function)
        def verified_pair(a,b,*args,_original=original,**kwargs):
            s.verify_binary(Path(a));s.verify_binary(Path(b));return _original(a,b,*args,**kwargs)
        setattr(native,function,verified_pair)
    native.Bank=ReusedBank;native.ARMS=ARMS
    # Existing natural() consumes self.w/inputs-01. Copy immutable inputs into
    # this lane; no historical inputs are written or relabelled.
    return s

def prepare(w,baseline,builds):
    import shutil
    need(not w.exists(),'New independent M1 work root');w.mkdir(parents=True)
    shutil.copytree(baseline/'inputs-01',w/'inputs-01')
    cfg=read(baseline/'config-reference-frozen-01.json');cfg.update(work_root=str(w),freeze=None,freeze_sha256=None);save(w/'config.json',cfg)
    host.inspect(w/'inventory.private.json')
    shared.save(w/'PRIOR_ACCOUNTING.json',{'original_ledger_sha256':sha(baseline/'ledger.jsonl'),
        'original_reservations':[r for r in map(json.loads,(baseline/'ledger.jsonl').read_text().splitlines()) if r.get('event')=='RESERVE'],
        'M1_independent_ledger':str(w/'ledger.jsonl'),'M1_ceiling_requests':2048,'M1_inherited_conservative_row_ceiling':4000000,
        'PR197_max_row_ceiling':8000000,'original_counters_not_reset':True,'M2':'NOT_AUTHORIZED_THIS_RUN'})
    roots=read(baseline/'stage-04/authenticated-kit/samples/R2-INPUTS.json')['inputs'];primers=read(baseline/'inputs-01/PRIMERS.json')['inputs'];lookup={x['id']:x for x in roots+primers}
    spec=read(Path(__file__).parent/'study.json');plan=shared.schedule(spec,'attribution',[{'root':x['id']} for x in roots]);out=w/'panel-01'
    models=read(w/'inputs-01/MODELS.json')['Qwen'];structures={r:checks.gguf_structure(models[r+'_model']) for r in ('target','draft')}
    for worker in plan['workers']:
        arm=worker['arm'];core,cut,_=ARMS[arm];keys=[x['id'] for x in primers]+worker['roots'];worker.update(id=worker['worker_id'],core=core,primers=keys[:2],job=worker['worker_id']+'.json')
        job={**models,'residency':'matched','draft':True,'draft_width':4,'lowering':cut,'profile':False,
            'capability_request':capability(models,structures,core,cut),'inputs':[{'name':f'request-{i:02d}','input':lookup[key],'capture':False} for i,key in enumerate(keys)]}
        save(out/worker['job'],job);worker['job_sha256']=sha(out/worker['job'])
    save(out/'PLAN.json',plan)
    save(out/'PROSPECTIVE_ORDER.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'plan_sha256':sha(out/'PLAN.json'),
        'new_M1_formal_outputs_seen':0,'old_panel_outputs_previously_exposed':True,'order_change_authority':'User explicitly requested position and directed adjacency balance before M1 timing',
        'arms':list(ARMS),'order_rows':spec['panels']['attribution']['worker_order_rows'],'M2':'NOT_RUN',
        'prior_ledger_sha256':sha(baseline/'ledger.jsonl'),'original_completed_panel_unchanged':True})
    print('M1_PLAN_FROZEN',flush=True)

def qualify(w,baseline,repo,builds):
    s=make_study(w,baseline,repo,builds)
    for family in ('Qwen','Smol'):s.natural(family)
    reports=[read(p) for p in s.reports];need(len(reports)==8 and all(x['passed'] for x in reports),'All four D4 paths and both finite families required')
    eog=[dict(family=x['family'],arm=x['arm'],root=r['root']) for x in reports for r in x['roots'] if r['terminal_kind']=='EOG'];need(len(eog)>=4,'Actual native EOG for all D4 combinations')
    need(all(any(len(r['rejection_cycles'])>=2 for r in x['roots']) for x in reports if x['family']=='Qwen'),'First/later rejection on each D4 path')
    save(s.out/'REFERENCE_REUSE.json',{'references':s.reuse,'historical_binary_hashes_reverified':len(s.verified),'new_reference_when_missing':True})
    summary=s.out/'NATIVE_CHECKS_COMPLETE.json';save(summary,dict(passed=True,finite_only=True,all_four_D4_paths=True,native_EOG_observed=eog,proofs=[dict(path=str(p),sha256=sha(p)) for p in s.reports]))
    kinds={'source_freeze','whole_prompt_producer','full_requested_logits','active_KV','frontier','pending','rollback','cap','native_EOG','clean_no_state_transfer','physical_work','actual_module_map','all_fixed_controls'}
    registry={'contract_checks':{'linux_reference_precedes_candidate_outputs':True},'checks':{k:{'passed':True,'evidence':str(summary)} for k in kinds},
        'executables':[{'build':str(builds/core/'BUILD.json'),'loaded_modules':str(s.modules[(core,'Qwen')])} for core in ('loop4','packed')]}
    registry['checks']['source_freeze']['evidence']=str(s.out/'SOURCE_REVIEW.json');save(s.out/'REGISTRY.json',registry)
    print('M1_NATIVE_QUALIFICATION_COMPLETE',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','qualify']);p.add_argument('--work',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--repo',type=Path,required=True);p.add_argument('--builds',type=Path,required=True)
    a=p.parse_args();load_runtime(a.runtime.resolve());w=a.work.resolve();baseline=a.baseline.resolve();builds=a.builds.resolve()
    prepare(w,baseline,builds) if a.action=='prepare' else qualify(w,baseline,a.repo.resolve(),builds)
