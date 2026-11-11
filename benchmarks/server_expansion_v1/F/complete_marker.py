"""Complete actual Llama dispatch observation without changing formal numerics.

The name-based failure remains. New heavy-only backend-marker probes are bridged
to the original formal binaries and the same frozen independent R.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse, copy, fcntl, inspect, json, shutil, time
import integrate as d

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('work','baseline','runtime','builds','marker-builds','repo','audit','retained-audit'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--source-commit',required=True);a=p.parse_args()
    for key,value in vars(a).items():
        if isinstance(value,Path):setattr(a,key,value.resolve())
    d.load(a.runtime);need,read,save,sha=d.need,d.read,d.save,d.sha
    w=a.work;old=w/'qualification-01';eog=w/'qualification-complete-02';out=w/'qualification-complete-03'
    need(not out.exists() and not a.audit.exists(),'Fresh explicit marker-completion epoch')
    a.audit.mkdir(parents=True)
    need(read(w.parent/'f-eog-completion-02/STATUS.json')['error']=='RealLlama marked loop4 path','Preserve actual name-based gate failure')
    frozen={str(x):sha(x) for x in Path(__file__).parent.rglob('*') if x.is_file() and x.suffix in ('.py','.cpp','.hpp','.json')}
    prior_eog={p.name:sha(p) for p in eog.glob('Llama-EOG-*-CHECKED.json')}
    need(len(prior_eog)==6,'All six completed genuine EOG proofs required')
    save(a.audit/'SOURCE_FREEZE.private.json',dict(source_commit=a.source_commit,files=frozen,
        original_R_sha256=sha(w/'reference-01/REFERENCE_FREEZE.json'),old_EOG_proofs=prior_eog,
        old_gate_failure_sha256=sha(w.parent/'f-eog-completion-02/STATUS.json'),
        marker_build_sha256=sha(a.marker_builds/'BUILD_COMPLETE.json'),formal_executables_replaced=False,
        arithmetic_changed=False,new_probe_generation_cap=8,verification_width=4,k=3,formal_performance='NOT_RUN'))
    phase='WAIT_RETAINED_OPERAND_REVALIDATION';start=time.monotonic()
    try:
        while not (a.retained_audit/'STATUS.json').exists():
            need(time.monotonic()-start<3600,'Retained operand audit wait limit');time.sleep(2)
        need(read(a.retained_audit/'STATUS.json')['status']=='RETAINED_PROOFS_REVALIDATED_ZERO_NEW_NATIVE_WORK','Every original consumed operand must be revalidated first')
        lock=(w.parent/'STUDY_SCHEDULING.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
        for path,h in frozen.items():need(sha(path)==h,'Marker completion source changed')
        need(read(a.marker_builds/'BUILD_COMPLETE.json')['numerical_archives_unchanged'],'Observer uses exact existing numerical archives')
        out.mkdir();models=read(w/'inputs-01/MODELS.json')[d.FAMILY];structures=read(w/'MODEL_STRUCTURES.json')
        cfg=read(w/'config-reference-frozen-01.json');rf=Path(cfg['reference_freeze'])
        need(sha(rf)==cfg['reference_freeze_sha256'],'Frozen independent R changed')
        trace,parse=d.checks.legacy_readers(a.repo);profiles=read(old/'STATE_PROFILES.json');modules={};bindings=[];hashes={}
        def hashed(path):
            path=Path(path)
            if path not in hashes:hashes[path]=sha(path)
            return hashes[path]
        def verify(dest,job_path,build,core,kind):
            job=read(job_path);b=read(build);launch=read(dest/'launch.json')
            need(read(dest/'HOST.json')['status']=='COMPLETE' and launch['job_sha256']==hashed(job_path) and launch['build_sha256']==hashed(build),'Actual complete native binding')
            need(hashed(b['executable'])==b['executable_sha256'] and job['target_sha256']==models['target_sha256'],'Actual executable/model unchanged')
            need(read(dest/'native/CAPABILITY.json')==job['capability_request'],'Complete native capability')
            actual=read(dest/'LOADED_MODULES.json')
            for name,row in actual.items():
                if row['kind']=='ELF_file':need(hashed(name)==row['sha256'],'Actual loaded module changed')
            key=(kind,core);modules.setdefault(key,dest/'LOADED_MODULES.json')
            need(read(modules[key])==actual,'Modules changed within the same compiled role')
            bindings.append(dict(run=str(dest),job_sha256=hashed(job_path),build_sha256=hashed(build),module_map_sha256=hashed(dest/'LOADED_MODULES.json')))
        class Study:
            def __init__(self):
                self.trace=trace;self.parse=parse;self.profiles=profiles;self.physical=d.native.Study.physical
            def execute(self,label,family,job,core='reference',kind='formal'):
                base=copy.deepcopy(models);base.update(job);draft=bool(base.get('draft',False)) and core!='reference'
                if not draft:
                    base.pop('draft_model',None);base.pop('draft_sha256',None);base.update(draft=False,residency='target_only')
                else:base['residency']='matched'
                base['capability_request']=d.capability(models,structures,core,base.get('lowering','WHOLE_UB1'),draft)
                path=out/'jobs'/(label+'.json');save(path,base);dest=out/'runs'/label
                build=(a.marker_builds if kind=='marker' else a.builds)/core/'BUILD.json'
                d.host.run(w/'config-reference-frozen-01.json',build,path,dest,'reference' if core=='reference' else 'development')
                verify(dest,path,build,core,kind);return dest
        s=Study();phase='RECHECK_COMPLETE_EOG_WITHOUT_NATIVE_REPLAY'
        fixture=read(Path(__file__).parent/'EOG_FIXTURE_V1.json')['inputs'][0]
        free=eog/'runs/Llama-EOG-free-R';verify(free,eog/'jobs/Llama-EOG-free-R.json',a.builds/'reference/BUILD.json','reference','formal')
        bank=d.native.Bank.__new__(d.native.Bank);bank.s=s;bank.family=d.FAMILY;bank.index=90;bank.input=fixture
        bank.free=free/'native/eog';bank.ep=read(bank.free/'receipt.json');bank.entries={};bank.teacher_count=0
        need(bank.ep['terminal_kind']=='EOG','Actual old independent-R EOG')
        for path in sorted((eog/'jobs').glob('Llama-root90-R-*.json')):
            dest=eog/'runs'/path.stem;verify(dest,path,a.builds/'reference/BUILD.json','reference','formal');bank.add(dest,read(path)['cases'])
        def forbid(*args,**kwargs):raise RuntimeError('Revalidating complete EOG proof must not replay native R')
        bank.s=SimpleNamespace(trace=trace,parse=parse,profiles=profiles,physical=d.native.Study.physical,execute=forbid)
        proofs=[]
        for name,h in read(Path(__file__).parent/'ORIGINAL_PROOF_BINDINGS.json')['proofs'].items():
            need(sha(old/name)==h,'Original positive proof changed');shutil.copy2(old/name,out/name);proofs.append(out/name)
        for arm,(core,cut,draft) in d.ARMS.items():
            path=eog/('Llama-EOG-'+arm+'-CHECKED.json');need(sha(path)==prior_eog[path.name],'Completed EOG proof changed')
            dest=eog/'runs'/('Llama-EOG-'+arm);verify(dest,eog/'jobs'/(dest.name+'.json'),a.builds/core/'BUILD.json',core,'formal')
            proof=bank.check(dest/'native/heavy',dest/'native/clean',read(dest/'native/result.json'),draft)
            need(proof==read(path)['proof'] and proof['passed'] and proof['terminal_kind']=='EOG','Exact complete old EOG proof recheck')
            shutil.copy2(path,out/path.name);proofs.append(out/path.name)
        save(out/'RETAINED_PROOFS_REVALIDATED.json',dict(passed=True,
            original_operand_audit_sha256=sha(a.retained_audit/'STATUS.json'),complete_old_EOG_proofs=prior_eog,old_native_requests_replayed=0))
        phase='NATIVE_BACKEND_MARKER_AND_FORMAL_BINARY_BRIDGES'
        root=dict(read(w/'inputs-01/Llama-DEVELOPMENT.json')['inputs'][0],cap=8)
        old_endpoint=read(w/'reference-01/Llama-R-free-repeat-1/native/dev-0/receipt.json')
        need(not any(old_endpoint['eog'][:8]),'Fixed exposed greedy prefix supports cap8')
        save(out/'PROBE_BEFORE_OUTCOMES.json',dict(input=root,formal_samples_added=0,k=3,draft_width=4,target_outputs=4,
            source='Original exposed737-token witness; short generation cap8, no prompt truncation',arithmetic_rules_changed=False))
        ref=s.execute('Llama-marker-free-R',d.FAMILY,dict(inputs=[dict(name='probe',input=root,capture=True)]))
        need(read(ref/'native/probe/receipt.json')['ids']==old_endpoint['ids'][:8],'Same frozen-R greedy prefix')
        bank=d.native.Bank(s,d.FAMILY,91,root,ref/'native/probe');dispatch=[]
        for arm,(core,cut,draft) in d.ARMS.items():
            base=dict(lowering=cut,draft=draft,draft_width=4 if draft else 1,residency='matched' if draft else 'target_only',profile=False)
            observer=s.execute('Llama-marker-'+arm,d.FAMILY,dict(base,inputs=[dict(name='heavy',input=root,capture=True),dict(name='clean',input=root,capture=False)]),core,'marker')
            bridge=s.execute('Llama-formal-bridge-'+arm,d.FAMILY,dict(base,inputs=[dict(name='clean',input=root,capture=False)]),core,'formal')
            meta=read(observer/'native/result.json');proof=bank.check(observer/'native/heavy',bridge/'native/clean',meta,draft)
            need(proof['passed'],'Full-vector/state bridge to original formal binary/R')
            clean=read(observer/'native/clean/receipt.json');formal=read(bridge/'native/clean/receipt.json')
            clean['study_cap']=formal['study_cap']=8
            need(d.native.endpoint(clean)==d.native.endpoint(formal),'Observer clean/original formal endpoint')
            need(trace(clean,root['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx')[1]==trace(formal,root['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx')[1],'Observer clean/original formal transaction')
            need(all(v==0 for v in clean['observed_API_calls_within_service'].values()),'Heavy transfer in clean observer service')
            heavy=read(observer/'native/heavy/receipt.json');graph=[x for x in heavy['geometry'] if x['op']=='MUL_MAT']
            marked=[x for x in graph if x.get('loop4_marked')];packed=[x for x in graph if x['name'].startswith('frontier_packed_')]
            need(all(x['loop4_marker_raw']==x['loop4_marker_expected'] and x['sources'][0]['type']=='q8_0' and x['sources'][1]['type']=='f32'
                and 5<=x['ne'][1]<=32 and x['ne'][2:]==[1,1] and x['phase']=='PREFILL' for x in marked),'Actual backend marker and supported Q8/F32 wide shape')
            if core=='loop4':need(marked and not packed,'Actual backend loop4 marker required despite renamed tensors')
            else:need(packed and not marked and all(x['ne'][1]==4 and x['ne'][2]>=2 and x['sources'][0]['type']=='q8_0' and x['sources'][1]['type']=='f32' and x['phase']=='PREFILL' for x in packed),'Actual independent packed groups and marker negative control')
            verify_nodes=[x for x in graph if x['phase']=='VERIFY' and x['sources'] and x['sources'][0]['type']=='q8_0']
            if draft:need(verify_nodes and all(x['ne'][1]<=4 and x['ne'][2]==1 and not x['loop4_marked'] for x in verify_nodes),'Actual q4 narrow projection negative control')
            ops={op:sum(x['op']==op for x in heavy['geometry']) for op in ('ROPE','RMS_NORM')}
            need(all(ops.values()),'Actual normalization and RoPE descriptors')
            natural=read(old/('Llama-natural-'+arm+'-CHECKED.json'))
            if draft:need(any(len(x['rejection_cycles'])>=2 for x in natural['roots']),'Retained first/later rejection coverage')
            checked=dict(passed=True,arm=arm,numerical_bridge=proof,backend_marked_nodes=len(marked),packed_nodes=len(packed),
                renamed_marked_nodes=sum(not x['name'].startswith('hs_backend_loop4_') for x in marked),q4_verify_nodes=len(verify_nodes),normalization_and_RoPE=ops,
                observer_receipt_sha256=sha(observer/'native/heavy/receipt.json'),formal_bridge_receipt_sha256=sha(bridge/'native/clean/receipt.json'),
                observer_build_sha256=sha(a.marker_builds/core/'BUILD.json'),formal_build_sha256=sha(a.builds/core/'BUILD.json'),
                scope='Actual scheduled GPU op_params dispatch markers/descriptors; not CUDA kernel-symbol profiling',verification_width=4,generation_cap=8)
            path=out/('Llama-marker-'+arm+'-CHECKED.json');save(path,checked);proofs.append(path);dispatch.append(checked)
            print('ACTUAL_BACKEND_MARKER_AND_FORMAL_BRIDGE_PASS',arm,len(marked),len(packed),flush=True)
        save(out/'PROJECTION_DISPATCH.json',dict(passed=True,arms=dispatch,formal_binaries_replaced=False,
            original_name_gate_failure_preserved=True,actual_backend_marker_observed=True,finite_only=True))
        summary=out/'NATIVE_CHECKS_COMPLETE.json';save(summary,dict(passed=True,all_six_arms=True,all12_geometry_cases=True,finite_only=True,
            proofs=[dict(path=str(p),sha256=sha(p)) for p in proofs],reference_freeze_sha256=sha(rf),formal_binaries_replaced=False,
            native_EOG_scope='Six already completed fixed-fixture controls, exact vectors/states rechecked; original natural roots CAP128',
            projection_scope='Six new actual-backend-marker observer/original-formal-binary bridges',original_native_requests_replayed=0))
        phase='NATIVE_NEGATIVE_GATES'
        code=inspect.getsource(d.negatives).replace("w/'qualification-01/NATIVE_CHECKS_COMPLETE.json'","w/'qualification-complete-03/NATIVE_CHECKS_COMPLETE.json'")
        ns=dict(vars(d));exec(compile(code,'marker_completion_negative_gate_adapter','exec'),ns);ns['negatives'](a)
        kinds={'source_freeze','whole_prompt_producer','full_requested_logits','active_KV','frontier','pending','rollback','cap','native_EOG','clean_no_state_transfer','physical_work','actual_module_map','all_fixed_controls'}
        registry=dict(contract_checks={'linux_reference_precedes_candidate_outputs':True},checks={k:dict(passed=True,evidence=str(summary)) for k in kinds},
            executables=[dict(build=str(a.builds[c]/'BUILD.json'),loaded_modules=str(modules[('formal',c)])) for c in ('loop4','packed')])
        registry['checks']['source_freeze']['evidence']=str(a.audit/'SOURCE_FREEZE.private.json')
        registry['checks']['native_negatives']=dict(passed=True,evidence=str(w/'capability-negatives-01/CHECKED.json'))
        save(out/'REGISTRY.json',registry);save(out/'ACTUAL_NATIVE_BINDINGS.json',dict(bindings=bindings))
        save(a.audit/'STATUS.json',dict(status='QUALIFIED_FORMAL_NOT_RUN',qualification_sha256=sha(summary),original_R_replaced=False,
            original_formal_executables_replaced=False,old_native_requests_replayed=0,old_name_gate_failure_preserved=True,M2='NOT_RUN',formal_performance='NOT_RUN'))
        print('LLAMA_ACTUAL_MARKER_FINITE_QUALIFICATION_COMPLETE',flush=True)
    except BaseException as error:
        save(a.audit/'STATUS.json',dict(status='FAILED_RETAINED',phase=phase,error=str(error),formal_performance='NOT_RUN'));raise

if __name__=='__main__':main()
