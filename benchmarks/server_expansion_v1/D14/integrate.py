"""C1024 D14 integration using the qualified supervisor and exact native readers.

Admission, independent R, geometry/natural qualification and formal timing are
separate gates. No C4096 or M2 job is supported by this coordinator.
"""
from pathlib import Path
import argparse, copy, datetime, importlib.util, json, sys, time

FAMILY='Qwen14B'
ARMS={'W_L4_M':('loop4','SIMPLE',False),'W_P_M':('packed','SIMPLE',False),
      'L_L4_M':('loop4','LOCAL',False),'L_P_M':('packed','LOCAL',False),
      'W_L4_D4':('loop4','SIMPLE',True),'L_P_D4':('packed','LOCAL',True)}

def load(runtime):
    sys.dont_write_bytecode=True;sys.path.insert(0,str(runtime))
    global need,read,save,sha,host,native,checks,freeze,shared
    from common import need,read,save,sha
    import host,qualify_native as native,native_checks as checks,freeze
    spec=importlib.util.spec_from_file_location('d14_shared',Path(__file__).parents[1]/'shared/experiment.py')
    shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)

def capability(models,structures,core,cut,draft=False):
    def model(role):
        s=structures[role];ub,out=(1,1) if core=='reference' else ((32,4) if role=='target' else (4,1))
        return dict(sha256=models[role+'_sha256'],structure={k:s[k] for k in ('architecture','layers','query_heads','kv_heads','head_k','head_v','K_elements','V_elements','vocab','tensor_count')},
            context=dict(n_ctx=1024,n_batch=1024,n_ubatch=ub,outputs_max=out,outputs_per_seq=out,flash_attention=False,
                type_k='f16',type_v='f16',cache_capacity=1024,all_KV_on_selected_GPU=True,active_prefix_tokens=0),all_model_tensors_on_selected_GPU=True)
    return dict(schema='heterospec.d14.native-capability.v1',core=core,family=FAMILY,residency='matched' if draft else 'target_only',
        cut='WHOLE_UB1' if core=='reference' else cut,k=3 if draft else 0,draft_width=4 if draft else 0,threads=2,greedy=True,
        target_output_policy='PREFILL:last;VERIFY:all_original_rows',placement_policy='all_model_tensors_and_KV_on_one_GPU_v1',
        target=model('target'),draft=model('draft') if draft else None)

def prepare(a):
    w=a.work;need(not w.exists(),'Fresh independent D14 work root');w.mkdir(parents=True)
    admission=read(a.admission/'ADMISSION.json');need(admission['status']=='ZERO_FORWARD_C1024_ADMISSION_PASS','Actual zero-forward admission first')
    actual=read(a.admission/'native-01/native/result.json');need(actual['full_native_pair_vocab_and_EOG_equal'],'Actual native vocabulary/EOG compatibility')
    spec=read(Path(__file__).parent/'models.json')
    need(actual['target_sha256']==spec['target']['sha256'] and actual['draft_sha256']==spec['draft']['sha256'],'Same admitted model bytes')
    inputs=w/'inputs-01';inputs.mkdir();cfg=read(a.baseline/'config-reference-frozen-01.json')
    cfg.update(work_root=str(w),reference_freeze=None,reference_freeze_sha256=None,freeze=None,freeze_sha256=None);save(w/'config.json',cfg)
    host.inspect(w/'inventory.private.json')
    models=dict(family=FAMILY,target_model=str(a.target),target_sha256=spec['target']['sha256'],draft_model=str(a.draft),draft_sha256=spec['draft']['sha256'],n_ctx=1024,threads=2)
    structures={r:checks.gguf_structure(models[r+'_model']) for r in ('target','draft')}
    # Verify the independently parsed header and actual native tensor inventory.
    for role in ('target','draft'):
        need(structures[role]['tensor_count']==len(actual[role+'_model']['model_tensors']),'GGUF/native full tensor inventory count differs; inspect aliases before proceeding')
    save(w/'MODEL_STRUCTURES.json',structures);save(inputs/'MODELS.json',{FAMILY:models})
    for kind,key in (('DEVELOPMENT','inputs'),('GEOMETRY','cases')):
        path=a.baseline/'inputs-01'/('Qwen-'+kind+'.json');save(inputs/(FAMILY+'-'+kind+'.json'),dict(**{key:read(path)[key]},
            source_raw_sha256=sha(path),scope='Existing exposed Qwen native-token deployment cases; new independent14B oracle'))
    roots=read(inputs/(FAMILY+'-DEVELOPMENT.json'))['inputs'];cases=read(inputs/(FAMILY+'-GEOMETRY.json'))['cases']
    need(len(cases)==12 and len(roots)==4,'Preserve fixed development geometry/cohort')
    base={k:v for k,v in models.items() if not k.startswith('draft')};base.update(residency='target_only',draft=False,
        capability_request=capability(models,structures,'reference','WHOLE_UB1'))
    for repeat in (1,2):
        save(inputs/f'{FAMILY}-R-repeat-{repeat}.json',dict(base,cases=[cases[3],cases[-1]]))
        save(inputs/f'{FAMILY}-R-free-repeat-{repeat}.json',dict(base,inputs=[dict(name=f'dev-{i}',input=x,capture=True) for i,x in enumerate(roots)]))
    save(inputs/'PRIMERS.json',read(a.baseline/'inputs-01/PRIMERS.json'))
    save(inputs/'CONTRACT_BEFORE_OUTPUTS.json',dict(schema='server-d14.C1024-contract.v1',admission_sha256=sha(a.admission/'ADMISSION.json'),
        admitted_native_sha256=sha(a.admission/'native-01/native/result.json'),qualified_linux_successor='592abdfe9267fd97ecbde18cd0ee9a1bfc319e20',
        models=models,reference='Independent pristine-upstream archives, UB1/reserve1, whole-prompt caller; no8B R reuse',
        target_ubatch=32,target_output_reserve=4,draft_ubatch=4,k=3,n_ctx=1024,F16_KV=True,flash_attention=False,
        model_forwards_before_prepare=0,C4096='NOT_RUN',M2='NOT_RUN',actual_chat_template_sha256={r:actual[r+'_model']['chat_template_sha256'] for r in ('target','draft')}))
    save(w/'PRIOR_ACCOUNTING.private.json',dict(old_ledger_sha256=sha(a.baseline/'ledger.jsonl'),M1_ledger_sha256=sha(a.baseline.parent/'m1-run-01/ledger.jsonl'),
        admission_ledger_sha256=sha(a.admission/'ledger.jsonl'),independent_ledger=True,request_ceiling=2560,row_ceiling=12000000,no_old_records_modified=True))
    raw=a.baseline/'stage-04/authenticated-kit/samples/R2-INPUTS.json';cohort=read(raw)['inputs'];primers=read(inputs/'PRIMERS.json')['inputs']
    need(not {x['id'] for x in cohort}&{x['id'] for x in roots},'Development/formal disjointness')
    study=read(Path(__file__).parent/'study.json');plan=shared.schedule(study,'c1024',[{'root':x['id']} for x in cohort])
    arms=list(ARMS);rows=[[arms[(i+s)%6] for i in (0,1,5,2,4,3)] for s in range(4)];old={x['worker_id']:x for x in plan['workers']}
    plan['workers']=[old[f'{study["id"]}-c1024-s{s}-{arm}'] for s,row in enumerate(rows) for arm in row]
    plan.update(order_design='Four distinct Williams6 rows; each arm uses4 distinct positions and20 within-session directed edges are unique; not complete6-row balance',worker_order_rows=rows)
    dest=w/'panel-01';lookup={x['id']:x for x in cohort+primers}
    for worker in plan['workers']:
        core,cut,draft=ARMS[worker['arm']];keys=[x['id'] for x in primers]+worker['roots'];worker.update(id=worker['worker_id'],core=core,primers=keys[:2],job=worker['worker_id']+'.json')
        job=dict(models,residency='matched' if draft else 'target_only',draft=draft,draft_width=4 if draft else 1,lowering=cut,profile=False,
            capability_request=capability(models,structures,core,cut,draft),inputs=[dict(name=f'request-{i:02d}',input=lookup[key],capture=False) for i,key in enumerate(keys)])
        if not draft:job.pop('draft_model');job.pop('draft_sha256')
        save(dest/worker['job'],job);worker['job_sha256']=sha(dest/worker['job'])
    save(dest/'PLAN.json',plan);save(dest/'PROSPECTIVE_ORDER.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        plan_sha256=sha(dest/'PLAN.json'),D14_formal_outputs_seen=0,D14_candidate_outputs_seen=0,old8B_outputs_previously_exposed=True,
        reason='Prospective engineering amendment retains24 workers/384 tests/48 primers and seed; avoids always placing SIMPLE before LOCAL D4',
        order_rows=rows,D4_relative_order_counts={'SIMPLE_before_LOCAL':2,'LOCAL_before_SIMPLE':2},between_session_edges_not_balanced=True,
        cohort_source_sha256=sha(raw),C4096='NOT_RUN',M2='NOT_RUN'))
    save(w/'PREPARED.json',dict(passed=True,source_files={str(x):sha(x) for x in Path(__file__).parent.rglob('*') if x.is_file() and x.suffix in ('.py','.cpp','.hpp','.json')},
        builds_sha256=sha(a.builds/'BUILD_COMPLETE.json'),plan_sha256=sha(dest/'PLAN.json'),candidate_outputs_seen=0))
    print('D14_PREPARED',flush=True)

def reference(a):
    # Same repeated-R implementation, with exactly one new deployment family.
    text=(a.runtime/'run_reference.py').read_text();need(text.count("('Qwen','Smol')")==2,'Pinned R family anchors')
    text=text.replace("('Qwen','Smol')","('Qwen14B',)")
    text=text.replace('Both pinned model families;','Pinned14B deployment;')
    save(a.work/'REFERENCE_ADAPTER.json',dict(base_source_sha256=sha(a.runtime/'run_reference.py'),
        changes=['One exact Qwen14B deployment family','Scope label'],numerical_or_comparison_rule_changes=False))
    namespace={'__name__':'d14_independent_reference','__file__':str(a.runtime/'run_reference.py')};exec(compile(text,namespace['__file__'],'exec'),namespace)
    old=sys.argv;sys.argv=['D14-independent-R','--work',str(a.work),'--config',str(a.work/'config.json'),'--build',str(a.builds/'reference/BUILD.json')]
    try:namespace['main']()
    finally:sys.argv=old

def study(a):
    from qualify_partitioned import PartitionedStudy
    class D14Study(PartitionedStudy):
        def __init__(self):
            self.w=a.work;self.repo=a.repo;self.out=a.work/'qualification-01';need(not self.out.exists(),'Retain all qualification epochs');self.out.mkdir()
            self.cfg=self.w/'config-reference-frozen-01.json';rf=read(self.cfg)['reference_freeze'];need(read(rf)['status']=='REFERENCE_FROZEN','New14B R frozen first')
            self.models=read(self.w/'inputs-01/MODELS.json');self.trace,self.parse=checks.legacy_readers(self.repo);self.modules={};self.reports=[]
            self.structures={FAMILY:read(self.w/'MODEL_STRUCTURES.json')['target']};self.ref_build=a.builds/'reference/BUILD.json'
            self.profiles={FAMILY:checks.profile(self.models[FAMILY]['target_model'],self.models[FAMILY]['target_sha256'],a.baseline/'stage-04/sources/reference/src/llama-kv-cache.cpp',self.structures[FAMILY])}
            save(self.out/'MODEL_STRUCTURES.json',self.structures);save(self.out/'STATE_PROFILES.json',self.profiles)
            save(self.out/'WRITER_REVIEW.json',checks.review_writers(a.baseline/'stage-04'))
            save(self.out/'SOURCE_REVIEW.json',dict(passed=True,qualified_linux_successor='592abdfe9267fd97ecbde18cd0ee9a1bfc319e20',
                build_complete_sha256=sha(a.builds/'BUILD_COMPLETE.json'),independent14B_R_freeze_sha256=sha(rf),numerical_archives_read_only=True,
                all_model_and_KV_buffers_GPU_checked_natively=True,geometry_all12_cases_partitioned3_per_worker=True,
                natural_transaction_and_state_rules_unchanged=True,admission_sha256=sha(a.admission/'ADMISSION.json')))
        def execute(self,label,family,job,core='reference'):
            base=copy.deepcopy(self.models[family]);base.update(job);draft=bool(base.get('draft',False)) and core!='reference'
            if core=='reference' or base.get('residency')=='target_only':
                base.pop('draft_model',None);base.pop('draft_sha256',None);base.update(residency='target_only',draft=False);draft=False
            else:base['residency']='matched'
            base['capability_request']=capability(self.models[family],read(self.w/'MODEL_STRUCTURES.json'),core,base.get('lowering','WHOLE_UB1'),draft)
            # Free R was already independently repeated/frozen before candidates.
            if label==FAMILY+'-free-independent-R':
                old=self.w/'reference-01'/f'{FAMILY}-R-free-repeat-1';job_path=self.w/'inputs-01'/f'{FAMILY}-R-free-repeat-1.json'
                need(base==read(job_path) and read(old/'HOST.json')['status']=='COMPLETE','Exact retained independent free R job')
                launch=read(old/'launch.json');need(launch['job_sha256']==sha(job_path) and launch['build_sha256']==sha(self.ref_build),'Retained free R launch')
                self.modules.setdefault((core,family),old/'LOADED_MODULES.json');return old
            job_path=self.out/'jobs'/(label+'.json');save(job_path,base);dest=self.out/'runs'/label
            build=a.builds/core/'BUILD.json';host.run(self.cfg,build,job_path,dest,'reference' if core=='reference' else 'development')
            modules=dest/'LOADED_MODULES.json';self.modules.setdefault((core,family),modules);need(read(self.modules[(core,family)])==read(modules),'Actual loaded modules changed')
            need(read(dest/'native/CAPABILITY.json')==base['capability_request'],'Native complete deployment capability')
            return dest
    return D14Study()

def qualify(a):
    s=study(a);s.matrix(FAMILY);s.natural(FAMILY)
    reports=[read(x) for x in s.reports];natural=[x for x in reports if 'roots' in x]
    need(len(reports)==10 and len(natural)==6 and all(x['passed'] for x in reports),'All four M geometry and all six natural controls')
    eog=[dict(arm=x['arm'],root=r['root']) for x in natural for r in x['roots'] if r['terminal_kind']=='EOG']
    need({x['arm'] for x in eog}==set(ARMS),'Actual14B native EOG on every control required')
    need(all(any(len(r['rejection_cycles'])>=2 for r in x['roots']) for x in natural if x['arm'].endswith('D4')),'First/later rejection on both D4 paths')
    complete=s.out/'NATIVE_CHECKS_COMPLETE.json';save(complete,dict(passed=True,finite_only=True,all_six_arms=True,all12_geometry_cases=True,
        native_EOG_observed=eog,first_later_rejection=True,proofs=[dict(path=str(x),sha256=sha(x)) for x in s.reports]))
    kinds={'source_freeze','whole_prompt_producer','full_requested_logits','active_KV','frontier','pending','rollback','cap','native_EOG','clean_no_state_transfer','physical_work','actual_module_map','all_fixed_controls'}
    registry=dict(contract_checks={'linux_reference_precedes_candidate_outputs':True},checks={k:dict(passed=True,evidence=str(complete)) for k in kinds},
        executables=[dict(build=str(a.builds/core/'BUILD.json'),loaded_modules=str(s.modules[(core,FAMILY)])) for core in ('loop4','packed')])
    registry['checks']['source_freeze']['evidence']=str(s.out/'SOURCE_REVIEW.json');save(s.out/'REGISTRY.json',registry);print('D14_FINITE_NATIVE_QUALIFICATION_COMPLETE',flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','reference','qualify'])
    for key in ('work','baseline','runtime','builds','repo','admission','target','draft'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    for key,value in vars(a).items():
        if isinstance(value,Path):setattr(a,key,value.resolve())
    load(a.runtime);globals()[a.action](a)

if __name__=='__main__':main()
