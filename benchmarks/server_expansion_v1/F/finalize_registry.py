"""Finish only the registry after all native marker bridges/negatives passed.

No model process is launched. Revalidate actual completed jobs and proof bytes;
keep the failed Path-indexing coordinator receipt and every native output.
"""
from pathlib import Path
import argparse, datetime, json, shutil, sys

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('work','runtime','builds','marker-builds','audit'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--source-commit',required=True);a=p.parse_args()
    sys.path.insert(0,str(a.runtime));from common import need,read,save,sha
    w=a.work.resolve();old=w/'qualification-complete-03';out=w/'qualification-registry-04'
    need(not out.exists() and not a.audit.exists(),'Fresh metadata-only completion epoch')
    a.audit.mkdir();failed=read(w.parent/'f-marker-completion-03/STATUS.json')
    need(failed['status']=='FAILED_RETAINED' and failed['error']=="'PosixPath' object is not subscriptable",'Retain exact registry-adapter failure')
    cfg=read(w/'config-reference-frozen-01.json');rf=Path(cfg['reference_freeze'])
    need(sha(rf)==cfg['reference_freeze_sha256'] and read(rf)['status']=='REFERENCE_FROZEN','Same independent Llama R')
    source_freeze=dict(source_commit=a.source_commit,self_sha256=sha(Path(__file__)),
        predecessor_failed_status_sha256=sha(w.parent/'f-marker-completion-03/STATUS.json'),
        predecessor_source_freeze_sha256=sha(w.parent/'f-marker-completion-03/SOURCE_FREEZE.private.json'),
        reference_freeze_sha256=sha(rf),new_model_forwards=0,new_native_jobs=0,formal_performance='NOT_RUN')
    save(a.audit/'SOURCE_FREEZE.private.json',source_freeze)
    try:
        summary=read(old/'NATIVE_CHECKS_COMPLETE.json')
        need(summary['passed'] and summary['all_six_arms'] and len(summary['proofs'])==22,'All original/EOG/actual-marker proof sets')
        for row in summary['proofs']:
            need(sha(row['path'])==row['sha256'] and read(row['path'])['passed'],'Completed native proof changed')
        need(read(old/'PROJECTION_DISPATCH.json')['passed'],'Actual backend-marker graph gate')
        neg=w/'capability-negatives-01/CHECKED.json';negative=read(neg)
        need(negative['passed'] and len(negative['tests'])==2 and negative['model_forwards']==0,'Both actual native bad-option gates completed')
        for row in negative['tests']:
            run=w/'capability-negatives-01/runs'/row['name'];job=w/'capability-negatives-01/jobs'/(row['name']+'.json')
            need(read(run/'HOST.json')['status']=='FAILED' and not (run/'native/result.json').exists(),'Expected pre-input native rejection retained')
            need(sha(job)==row['job_sha256'] and sha(run/'launch.json')==row['launch_sha256'] and sha(run/'native/failure.json')==row['failure_sha256'],'Actual negative job/failure binding')
        models=read(w/'inputs-01/MODELS.json')['Llama'];bindings=[];maps={};checked={}
        def hash_once(path):
            path=Path(path)
            if path not in checked:checked[path]=sha(path)
            return checked[path]
        for job_path in sorted((old/'jobs').glob('*.json')):
            job=read(job_path);run=old/'runs'/job_path.stem;core=job['capability_request']['core']
            observer=core!='reference' and job_path.stem.startswith('Llama-marker-')
            build=(a.marker_builds if observer else a.builds)/core/'BUILD.json'
            launch=read(run/'launch.json');b=read(build)
            need(read(run/'HOST.json')['status']=='COMPLETE' and launch['job_sha256']==hash_once(job_path) and launch['build_sha256']==hash_once(build),'Actual completed bridge/R worker')
            need(hash_once(b['executable'])==b['executable_sha256'] and job['target_sha256']==models['target_sha256'],'Same actual executable/model')
            if job.get('draft_model'):need(job['draft_sha256']==models['draft_sha256'],'Same exact draft bytes')
            need(read(run/'native/CAPABILITY.json')==job['capability_request'],'Actual full native capability')
            modules=read(run/'LOADED_MODULES.json')
            for path,row in modules.items():
                if row['kind']=='ELF_file':need(hash_once(path)==row['sha256'],'Actual loaded module changed')
            if not observer and core!='reference':
                maps.setdefault(core,run/'LOADED_MODULES.json');need(read(maps[core])==modules,'Original formal role modules differ')
            bindings.append(dict(job_sha256=hash_once(job_path),build_sha256=hash_once(build),run=str(run),observer=observer,native_replayed=False))
        need(set(maps)=={'loop4','packed'},'Both original formal binaries bridged')
        out.mkdir()
        for name in ('NATIVE_CHECKS_COMPLETE.json','PROJECTION_DISPATCH.json','RETAINED_PROOFS_REVALIDATED.json'):
            shutil.copy2(old/name,out/name)
        kinds={'source_freeze','whole_prompt_producer','full_requested_logits','active_KV','frontier','pending','rollback','cap','native_EOG','clean_no_state_transfer','physical_work','actual_module_map','all_fixed_controls'}
        evidence=out/'NATIVE_CHECKS_COMPLETE.json'
        registry=dict(contract_checks={'linux_reference_precedes_candidate_outputs':True},
            checks={k:dict(passed=True,evidence=str(evidence)) for k in kinds},
            executables=[dict(build=str(a.builds/c/'BUILD.json'),loaded_modules=str(maps[c])) for c in ('loop4','packed')])
        registry['checks']['source_freeze']['evidence']=str(a.audit/'SOURCE_FREEZE.private.json')
        registry['checks']['native_negatives']=dict(passed=True,evidence=str(neg))
        save(out/'REGISTRY.json',registry);save(out/'ACTUAL_NATIVE_BINDINGS.json',dict(bindings=bindings))
        save(a.audit/'STATUS.json',dict(status='QUALIFIED_FORMAL_NOT_RUN',qualification_sha256=sha(evidence),registry_sha256=sha(out/'REGISTRY.json'),
            preserved_failed_registry_adapter=True,new_model_forwards=0,new_native_jobs=0,
            formal_executables_or_reference_replaced=False,finite_only=True,formal_performance='NOT_RUN'))
        print('LLAMA_ALL_NATIVE_GATES_AND_REGISTRY_COMPLETE_ZERO_REPLAY',flush=True)
    except BaseException as error:
        save(a.audit/'STATUS.json',dict(status='FAILED_RETAINED',error=str(error),new_model_forwards=0));raise

if __name__=='__main__':main()
