"""C1024 LLAMA_F integration using the qualified supervisor and exact native readers.

Admission, independent R, geometry/natural qualification and formal timing are
separate gates. No C4096 or M2 job is supported by this coordinator.
"""
from pathlib import Path
import argparse, copy, datetime, importlib.util, json, sys, time

FAMILY='Llama'
ARMS={'W_L4_M':('loop4','SIMPLE',False),'W_P_M':('packed','SIMPLE',False),
      'L_L4_M':('loop4','LOCAL',False),'L_P_M':('packed','LOCAL',False),
      'W_L4_D4':('loop4','SIMPLE',True),'L_P_D4':('packed','LOCAL',True)}

def load(runtime):
    sys.dont_write_bytecode=True;sys.path.insert(0,str(runtime))
    global need,read,save,sha,host,native,checks,freeze,shared
    from common import need,read,save,sha
    import host,qualify_native as native,native_checks as checks,freeze
    spec=importlib.util.spec_from_file_location('llama_f_shared',Path(__file__).parents[1]/'shared/experiment.py')
    shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)

def capability(models,structures,core,cut,draft=False):
    def model(role):
        s=structures[role];ub,out=(1,1) if core=='reference' else ((32,4) if role=='target' else (4,1))
        return dict(sha256=models[role+'_sha256'],structure={k:s[k] for k in ('architecture','layers','query_heads','kv_heads','head_k','head_v','K_elements','V_elements','vocab','tensor_count')},
            context=dict(n_ctx=1024,n_batch=1024,n_ubatch=ub,outputs_max=out,outputs_per_seq=out,flash_attention=False,
                type_k='f16',type_v='f16',cache_capacity=1024,all_KV_on_selected_GPU=True,active_prefix_tokens=0),all_model_tensors_on_selected_GPU=True)
    return dict(schema='heterospec.llama_f.native-capability.v1',core=core,family=FAMILY,residency='matched' if draft else 'target_only',
        cut='WHOLE_UB1' if core=='reference' else cut,k=3 if draft else 0,draft_width=4 if draft else 0,threads=2,greedy=True,
        target_output_policy='PREFILL:last;VERIFY:all_original_rows',placement_policy='all_model_tensors_and_KV_on_one_GPU_v1',
        target=model('target'),draft=model('draft') if draft else None)

def prepare(a):
    checked=read(a.assets/'CHECKED.json');need(checked['passed'] and checked['model_forwards']==0,'Exact assets/native tokenizer/templates first')
    rules=read(a.rule_freeze/'FREEZE.json');need(rules['status']=='FINAL_RULES_FROZEN_BEFORE_LLAMA_OUTPUTS','Original final rules frozen first')
    need(sha(a.builds/'BUILD_COMPLETE.json')==rules['build_complete_sha256'],'Different frozen initial transfer build')
    w=a.work;need(not w.exists(),'Fresh independent Llama work root');w.mkdir(parents=True);inputs=w/'inputs-01';inputs.mkdir()
    cfg=read(a.baseline/'config-reference-frozen-01.json');cfg.update(work_root=str(w),reference_freeze=None,reference_freeze_sha256=None,freeze=None,freeze_sha256=None);save(w/'config.json',cfg);host.inspect(w/'inventory.private.json')
    spec=read(Path(__file__).parent/'models.json');models=dict(family=FAMILY,target_model=str(a.target),target_sha256=spec['target']['sha256'],draft_model=str(a.draft),draft_sha256=spec['draft']['sha256'],n_ctx=1024,threads=2)
    structures={r:checks.gguf_structure(models[r+'_model']) for r in ('target','draft')};save(w/'MODEL_STRUCTURES.json',structures);save(inputs/'MODELS.json',{FAMILY:models})
    source=Path(__file__).parent/'HISTORICAL_DEVELOPMENT.json';roots=read(source)['inputs'];need(len(roots)==3 and roots[0]['id']=='CodeContests/valid/108','Retained exact witness and archived controls')
    save(inputs/(FAMILY+'-DEVELOPMENT.json'),dict(inputs=roots,source_sha256=sha(source),scope='Historical Llama diagnostic development, not new blind roots'))
    tape=roots[0]['prompt_ids'];need(len(tape)==737,'Original retained witness geometry')
    # Finite forced-prefix queries at the512 extent boundary. No text is padded;
    # these are structural prompt-prefix probes, not a natural confirmation panel.
    cases=[]
    layout=[('q4-inside',508,4,False),('q4-crossing',511,4,False),('q8-inside',504,8,False),('q8-crossing',511,8,False),('q32-inside',480,32,False),('q32-crossing',511,32,False),('q1-inside',510,1,False),('q1-boundary',511,1,False),('q4-tail',540,3,False),('q8-tail',536,7,False),('q32-tail',524,19,False),('q4-all-requested',511,4,True)]
    for name,head,width,all_rows in layout:
        last=head+width;cases.append(dict(name=name,forced=[dict(ids=tape[:head],phase='PREFILL',all=False),dict(ids=tape[head:last],phase='VERIFY',all=all_rows)],observe_positions=[head]+(list(range(head+1,last+1)) if all_rows else [last]),state_positions=[last]))
    save(inputs/(FAMILY+'-GEOMETRY.json'),dict(cases=cases,source_sha256=sha(source),scope='Finite known-query prefixes from retained737-token prompt; q1/4/8/32 inside/crossing512/tails/all-original-requested q4'))
    base={k:v for k,v in models.items() if not k.startswith('draft')};base.update(residency='target_only',draft=False,capability_request=capability(models,structures,'reference','WHOLE_UB1'))
    for repeat in (1,2):
        save(inputs/f'{FAMILY}-R-repeat-{repeat}.json',dict(base,cases=[cases[3],cases[-1]]))
        save(inputs/f'{FAMILY}-R-free-repeat-{repeat}.json',dict(base,inputs=[dict(name=f'dev-{i}',input=x,capture=True) for i,x in enumerate(roots)]))
    save(inputs/'CONTRACT_BEFORE_OUTPUTS.json',dict(schema='server-F.C1024-contract.v1',asset_check_sha256=sha(a.assets/'CHECKED.json'),rule_freeze_sha256=sha(a.rule_freeze/'FREEZE.json'),models=models,reference='New independent pristine-upstream Linux Llama UB1/reserve1 whole-prompt producer',n_ctx=1024,F16_KV=True,flash_attention=False,target_ubatch=32,target_outputs=4,draft_ubatch=4,k=3,Llama_candidate_forwards_before_prepare=0,natural_confirmation_roots='NOT_SELECTED',formal_performance='NOT_RUN',M2='NOT_RUN'))
    save(w/'PRIOR_ACCOUNTING.private.json',dict(old_ledger_sha256=sha(a.baseline/'ledger.jsonl'),M1_ledger_sha256=sha(a.baseline.parent/'m1-run-01/ledger.jsonl'),independent_ledger=True,request_ceiling=1536,row_ceiling=8000000))
    save(w/'PREPARED.json',dict(passed=True,rule_freeze_sha256=sha(a.rule_freeze/'FREEZE.json'),asset_check_sha256=sha(a.assets/'CHECKED.json'),build_complete_sha256=sha(a.builds/'BUILD_COMPLETE.json'),Llama_candidate_outputs_seen=0,formal_performance='NOT_RUN'))
    print('LLAMA_PREPARED_NO_FORWARD',flush=True)

def reference(a):
    # Same repeated-R implementation, with exactly one new deployment family.
    text=(a.runtime/'run_reference.py').read_text();need(text.count("('Qwen','Smol')")==2,'Pinned R family anchors')
    text=text.replace("('Qwen','Smol')","('Llama',)")
    text=text.replace('Both pinned model families;','Pinnellama_fB deployment;')
    save(a.work/'REFERENCE_ADAPTER.json',dict(base_source_sha256=sha(a.runtime/'run_reference.py'),
        changes=['One exact Llama deployment family','Scope label'],numerical_or_comparison_rule_changes=False))
    namespace={'__name__':'llama_f_independent_reference','__file__':str(a.runtime/'run_reference.py')};exec(compile(text,namespace['__file__'],'exec'),namespace)
    old=sys.argv;sys.argv=['LLAMA_F-independent-R','--work',str(a.work),'--config',str(a.work/'config.json'),'--build',str(a.builds/'reference/BUILD.json')]
    try:namespace['main']()
    finally:sys.argv=old

def study(a):
    from qualify_partitioned import PartitionedStudy
    class LLAMA_FStudy(PartitionedStudy):
        def __init__(self):
            self.w=a.work;self.repo=a.repo;self.out=a.work/'qualification-01';need(not self.out.exists(),'Retain all qualification epochs');self.out.mkdir()
            self.cfg=self.w/'config-reference-frozen-01.json';rf=read(self.cfg)['reference_freeze'];need(read(rf)['status']=='REFERENCE_FROZEN','NewLlama R frozen first')
            self.models=read(self.w/'inputs-01/MODELS.json');self.trace,self.parse=checks.legacy_readers(self.repo);self.modules={};self.reports=[]
            self.structures={FAMILY:read(self.w/'MODEL_STRUCTURES.json')['target']};self.ref_build=a.builds/'reference/BUILD.json'
            self.profiles={FAMILY:checks.profile(self.models[FAMILY]['target_model'],self.models[FAMILY]['target_sha256'],a.baseline/'stage-04/sources/reference/src/llama-kv-cache.cpp',self.structures[FAMILY])}
            save(self.out/'MODEL_STRUCTURES.json',self.structures);save(self.out/'STATE_PROFILES.json',self.profiles)
            save(self.out/'WRITER_REVIEW.json',checks.review_writers(a.baseline/'stage-04'))
            save(self.out/'SOURCE_REVIEW.json',dict(passed=True,qualified_linux_successor='592abdfe9267fd97ecbde18cd0ee9a1bfc319e20',
                build_complete_sha256=sha(a.builds/'BUILD_COMPLETE.json'),independentLlama_R_freeze_sha256=sha(rf),numerical_archives_read_only=True,
                all_model_and_KV_buffers_GPU_checked_natively=True,geometry_all12_cases_partitioned3_per_worker=True,
                natural_transaction_and_state_rules_unchanged=True,rule_freeze_sha256=sha(a.rule_freeze/'FREEZE.json'),asset_check_sha256=sha(a.assets/'CHECKED.json')))
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
    return LLAMA_FStudy()

def qualify(a):
    s=study(a);s.natural(FAMILY);s.matrix(FAMILY)
    reports=[read(x) for x in s.reports];natural=[x for x in reports if 'roots' in x]
    need(len(reports)==10 and len(natural)==6 and all(x['passed'] for x in reports),'All four M geometry and all six natural controls')
    eog=[dict(arm=x['arm'],root=r['root']) for x in natural for r in x['roots'] if r['terminal_kind']=='EOG']
    need({x['arm'] for x in eog}==set(ARMS),'ActualLlama native EOG on every control required')
    need(all(any(len(r['rejection_cycles'])>=2 for r in x['roots']) for x in natural if x['arm'].endswith('D4')),'First/later rejection on both D4 paths')
    dispatch=[]
    for arm,(core,cut,draft) in ARMS.items():
        run=s.out/'runs'/(FAMILY+'-natural-'+arm);packed=[];loop4=[];q4=[];hist={};op_counts={}
        for i in range(len(read(a.work/'inputs-01'/(FAMILY+'-DEVELOPMENT.json'))['inputs'])):
            row=read(run/'native'/f'dev-{i}-heavy/receipt.json');graph=[x for x in row['geometry'] if x['op']=='MUL_MAT']
            for node in row['geometry']:op_counts[node['op']]=op_counts.get(node['op'],0)+1
            packed += [x for x in graph if x['name'].startswith('frontier_packed_')]
            loop4 += [x for x in graph if x['name'].startswith('hs_backend_loop4_')]
            q4 += [x for x in graph if x['phase']=='VERIFY' and x['sources'] and x['sources'][0]['type']=='q8_0']
            for x in row['executions']:
                if x['phase']=='VERIFY':hist[str(x['width'])]=hist.get(str(x['width']),0)+1
        if core=='packed':need(packed and all(x['ne'][1]==4 and x['ne'][2]>=2 and x['sources'][0]['type']=='q8_0' and x['sources'][1]['type']=='f32' for x in packed),'RealLlama independent four-column packed groups')
        else:need(loop4 and not packed,'RealLlama marked loop4 path')
        need(all(x['phase']=='PREFILL' for x in packed),'Wide packing absent from q4/ordinary negative controls')
        if draft:
            need(q4 and all(x['ne'][1]<=4 and x['ne'][2]==1 for x in q4),'RealLlama q4 verification projection')
            if cut=='LOCAL':need(set(hist)=={'4'},'LOCAL retains physical q4')
        need(op_counts.get('ROPE',0)>0 and op_counts.get('RMS_NORM',0)>0,'Actual Llama normalization and RoPE graph descriptors required')
        dispatch.append(dict(arm=arm,actual_graph_op_counts=op_counts,packed_graph_nodes=len(packed),marked_loop4_graph_nodes=len(loop4),q4_graph_nodes=len(q4),
            verify_physical_width_hist=hist,observation='Actual scheduled GPU graph descriptors and device buffers, not kernel-symbol profiling'))
    save(s.out/'PROJECTION_DISPATCH.json',dict(passed=True,arms=dispatch,heavy_only=True,formal_binary_bridge='Same executable heavy/clean checks; zero heavy observer calls in clean service'))
    complete=s.out/'NATIVE_CHECKS_COMPLETE.json';save(complete,dict(passed=True,finite_only=True,all_six_arms=True,all12_geometry_cases=True,
        native_EOG_observed=eog,first_later_rejection=True,proofs=[dict(path=str(x),sha256=sha(x)) for x in s.reports]))
    kinds={'source_freeze','whole_prompt_producer','full_requested_logits','active_KV','frontier','pending','rollback','cap','native_EOG','clean_no_state_transfer','physical_work','actual_module_map','all_fixed_controls'}
    registry=dict(contract_checks={'linux_reference_precedes_candidate_outputs':True},checks={k:dict(passed=True,evidence=str(complete)) for k in kinds},
        executables=[dict(build=str(a.builds/core/'BUILD.json'),loaded_modules=str(s.modules[(core,FAMILY)])) for core in ('loop4','packed')])
    registry['checks']['source_freeze']['evidence']=str(s.out/'SOURCE_REVIEW.json');save(s.out/'REGISTRY.json',registry);print('LLAMA_F_FINITE_NATIVE_QUALIFICATION_COMPLETE',flush=True)

def negatives(a):
    w=a.work;need(read(w/'qualification-01/NATIVE_CHECKS_COMPLETE.json')['passed'],'All finite gates before native negatives')
    base=read(w/'qualification-01/jobs'/(FAMILY+'-natural-W_L4_D4.json'));base['inputs']=[x for x in base['inputs'] if x['name']=='cap1-clean']
    need(len(base['inputs'])==1,'One bounded negative request');rows=[]
    for name,error in [('unknown-field','Unknown LLAMA_F native job field'),('ignored-output-capacity','Native LLAMA_F capability differs from complete requested contract')]:
        job=copy.deepcopy(base)
        if name=='unknown-field':job['unimplemented_context_option']=True
        else:job['capability_request']['target']['context']['outputs_max']=8
        path=w/'capability-negatives-01/jobs'/(name+'.json');out=w/'capability-negatives-01/runs'/name;save(path,job)
        try:host.run(w/'config-reference-frozen-01.json',a.builds/'loop4/BUILD.json',path,out,'development')
        except RuntimeError:
            need(read(out/'HOST.json')['status']=='FAILED','Retain actual native negative')
            need(read(out/'native/failure.json')['error']==error and not (out/'native/result.json').exists(),'Expected pre-input capability rejection')
        else:raise RuntimeError('Bad capability reached native inputs')
        rows.append(dict(name=name,job_sha256=sha(path),launch_sha256=sha(out/'launch.json'),failure_sha256=sha(out/'native/failure.json'),charged=True))
    save(w/'capability-negatives-01/CHECKED.json',dict(passed=True,tests=rows,model_forwards=0,no_native_replays=True))

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','reference','qualify','negatives'])
    for key in ('work','baseline','runtime','builds','repo','assets','rule-freeze','target','draft'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    for key,value in vars(a).items():
        if isinstance(value,Path):setattr(a,key,value.resolve())
    load(a.runtime);globals()[a.action](a)

if __name__=='__main__':main()
