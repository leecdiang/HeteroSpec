"""Fresh16-worker factorial or8-worker packed-pair panel against original frozen14B R."""
from pathlib import Path
import argparse, datetime, inspect, json, time
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import integration_attribution as d

def execute(a):
    d.load(a.runtime);need,read,save,sha=d.need,d.read,d.save,d.sha
    from slot_identity import identity
    d.host.confirmation_identity=identity
    from quiet import check as check_quiet
    original_resources=d.host.check_resources
    def guarded_resources(config,group=None):
        check_quiet(a.baseline.parent)
        return original_resources(config,group)
    d.host.check_resources=guarded_resources
    w=a.work;dest=w/'panel-01';plan=read(dest/'PLAN.json');q=w/'qualification-03'
    complete=read(q/'NATIVE_CHECKS_COMPLETE.json');need(complete['passed'] and complete['all_eight_controls'],'All eight controls including four actual D4 paths first')
    need(read(q/'PROJECTION_DISPATCH.json')['passed'],'Actual14B projection descriptors required')
    need(read(w/'capability-negatives-01/CHECKED.json')['passed'],'Native unknown/ignored-field gates required')
    for row in complete['proofs']:need(sha(row['path'])==row['sha256'] and read(row['path'])['passed'],'Native proof changed')
    count=len(plan['workers']);need(count in (8,16) and plan['measurements']==16*count and plan['primers']==2*count and set(plan['arms'])==({'W_P_D4','L_P_D4'} if count==8 else {'W_L4_D4','W_P_D4','L_L4_D4','L_P_D4'}),'Fresh complete attribution envelope')
    need(read(dest/'PROSPECTIVE_ORDER.json')['plan_sha256']==sha(dest/'PLAN.json'),'Prospective plan changed')
    cfg=read(w/'config-reference-frozen-01.json');rf=Path(cfg['reference_freeze']);need(sha(rf)==cfg['reference_freeze_sha256'],'New14B R changed')
    need(read(rf)['build']['sha256']==sha(a.builds/'reference/BUILD.json'),'Different independent reference build')
    # Reference endpoints are new14B executions, never the old8B panel.
    cohort=read(a.baseline/'stage-04/authenticated-kit/samples/R2-INPUTS.json')['inputs'];primers=read(w/'inputs-01/PRIMERS.json')['inputs']
    lookup={x['id']:x for x in cohort+primers};order=[x['id'] for x in primers+cohort];need(len(order)==len(set(order))==18,'Fixed18 endpoints')
    models=read(w/'inputs-01/MODELS.json')[d.FAMILY];payload={k:v for k,v in models.items() if not k.startswith('draft')}
    payload.update(residency='target_only',draft=False,capability_request=d.capability(models,read(w/'MODEL_STRUCTURES.json'),'reference','WHOLE_UB1'),
        inputs=[dict(name=f'reference-{i}',input=lookup[key],capture=False) for i,key in enumerate(order)])
    job=dest/'REFERENCE-JOB.json';save(job,payload);old_job=a.predecessor/'panel-01/REFERENCE-JOB.json';ref=a.predecessor/'panel-01/reference-01'
    need(read(old_job)==payload,'Reuse only exact original14B R requests')
    index={x['path']:x['raw_sha256'] for x in read(a.predecessor.parent/'d14-public-export-02/TEXT_INDEX.json')['files']}
    for p in [old_job,ref/'launch.json',ref/'HOST.json',ref/'LOADED_MODULES.json']+[ref/'native'/f'reference-{i}/receipt.json' for i in range(18)]:
        need(sha(p)==index[str(p.relative_to(a.predecessor))],'Original14B R evidence changed')
    need(read(ref/'HOST.json')['status']=='COMPLETE' and read(ref/'launch.json')['job_sha256']==sha(old_job) and read(ref/'launch.json')['build_sha256']==sha(a.builds/'reference/BUILD.json'),'Original14B R launch binding')
    for p,row in read(ref/'LOADED_MODULES.json').items():
        if row['kind']=='ELF_file':need(sha(p)==row['sha256'],'Original14B R module changed')
    save(dest/'REFERENCE_REUSE.json',dict(passed=True,original_job_sha256=sha(old_job),original_launch_sha256=sha(ref/'launch.json'),original_R_freeze_sha256=sha(rf),new_R_requests=0,source_index_sha256=sha(a.predecessor.parent/'d14-public-export-02/TEXT_INDEX.json')))
    expected={key:(read(ref/'native'/f'reference-{i}/receipt.json'),ref/'native'/f'reference-{i}/receipt.json') for i,key in enumerate(order)}
    # The coordinator must close all its downloads/builds before this stage.
    save(dest/'SOURCE_FREEZE.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        adapter_files={str(x):sha(x) for x in Path(__file__).parent.rglob('*') if x.is_file() and '__pycache__' not in x.parts},
        runtime_files={str(x):sha(x) for x in a.runtime.glob('*.py')},source_commit=a.source_commit,
        independent_R_freeze_sha256=sha(rf),reference_panel_launch_sha256=sha(ref/'launch.json'),
        quiet_window='This coordinator has finished all acquisition, builds and archiving before formal timing. Company services remain running; selected-device and host resource samples retained.',
        C4096='NOT_RUN',M2='NOT_RUN',formal_internal_state_recomparisons=False))
    source=dest/'SOURCE_FREEZE_CHECKED.json';save(source,dict(passed=True,source_freeze_sha256=sha(dest/'SOURCE_FREEZE.json'),
        qualification_source_review_sha256=sha(q/'SOURCE_REVIEW.json'),projection_dispatch_sha256=sha(q/'PROJECTION_DISPATCH.json'),
        native_negative_gate_sha256=sha(w/'capability-negatives-01/CHECKED.json')))
    registry=read(q/'REGISTRY.json');registry['checks']['source_freeze']['evidence']=str(source);registry_path=dest/'REGISTRY-COMPLETE.json';save(registry_path,registry)
    frozen=dest/'CONFIRMATION_FREEZE.json';d.freeze.confirmation(rf,registry_path,dest/'PLAN.json',frozen)
    cfg.update(freeze=str(frozen),freeze_sha256=sha(frozen));config=w/'config-confirmation.json';save(config,cfg)
    reference_id='D14-C1024-R-'+sha(rf);trace,_=d.checks.legacy_readers(a.repo);records=[];flat=[];slots={x['id']:'NOT_RUN' for x in plan['workers']}
    try:
        for worker in plan['workers']:
            need(datetime.datetime.now(datetime.timezone.utc).timestamp()+960<=datetime.datetime.fromisoformat('2026-11-08T21:00:00+00:00').timestamp(),'Deadline admission closed: preserve all unstarted slots')
            name=worker['id'];out=dest/'runs'/name;job=dest/worker['job'];payload=read(job);draft=payload['draft'];slots[name]='STARTED'
            start=time.monotonic();d.host.run(config,a.builds/worker['core']/'BUILD.json',job,out,'confirmation');invocation=time.monotonic()-start
            meta=read(out/'native/result.json');need(meta['native_capability']==payload['capability_request'],'Actual deployment differs from frozen request')
            need(meta['total_observed_API_calls']['context_creates']==(2 if draft else 1),'True target-only versus pair residency')
            calls=[]
            for key,entry in zip(worker['primers']+worker['roots'],payload['inputs']):
                path=out/'native'/entry['name']/'receipt.json';r=read(path);oracle,oracle_path=expected[key]
                need(d.native.endpoint(r)==d.native.endpoint(oracle),'Independent14B R endpoint mismatch')
                r['study_cap']=entry['input']['cap'];_,decoded=trace(r,entry['input']['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx')
                need(all(x==0 for x in r['observed_API_calls_within_service'].values()),'Heavy/state work inside clean service')
                physical=d.native.Study.physical(r,entry['input'],draft)
                need(r['graphs_reused']>0 or len(r['ids'])==1,'Clean repeated graph reuse not observed')
                need(r['target_final_kv']==dict(min=0,max=len(decoded['states'][-1]['prefix'])-1),'Native pending terminal frontier')
                calls.append(dict(root=key,service_s=r['service_seconds'],reference_id=reference_id,reference_compatible=True,trace_valid=True,
                    native_receipt=str(path),native_receipt_sha256=sha(path),reference_receipt_sha256=sha(oracle_path),physical=physical,
                    ids=r['ids'],eog=r['eog'],terminal_kind=r['stop_reason']))
                if key in worker['roots']:flat.append(dict(root=key,session=worker['session'],arm=worker['arm'],status='COMPLETE',qualified=True,
                    reference_id=reference_id,gpu_uuid=cfg['gpu_uuid'],service_s=r['service_seconds'],evidence_path=str(path),evidence_sha256=sha(path),
                    qualification_registry_sha256=sha(registry_path),native_capability_sha256=sha(out/'native/CAPABILITY.json')))
            h=read(out/'HOST.json');clocks=read(out/'CLOCKS.json');clocks.update(worker_wall_s=h['worker_wall_s'],wrapper_wall_s=h['wrapper_wall_s'],
                model_load_s=meta['model_load_s'],pool_setup_s=meta['pool_setup_s'],adapter_run_inclusive_s=invocation,
                adapter_run_boundary='Entire host.run, including preflight/dependency/model hashing; excludes later result verification')
            telemetry=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()];need(telemetry,'Actual memory samples')
            clocks.update(maximum_sampled_total_minus_free_bytes=max((float(x['gpu']['memory.total'])-float(x['gpu']['memory.free']))*1024**2 for x in telemetry),
                minimum_sampled_free_bytes=min(float(x['gpu']['memory.free'])*1024**2 for x in telemetry),
                memory_scope='Selected-device total-minus-free includes reserved/unavailable memory;2s samples, not NVML memory.used or per-process high water')
            checked=dict(id=name,job_sha256=worker['job_sha256'],status='COMPLETE',native_checks_passed=True,requests=calls,actual_host_clocks=clocks,
                launch_sha256=sha(out/'launch.json'),loaded_modules_sha256=sha(out/'LOADED_MODULES.json'),native_capability_sha256=sha(out/'native/CAPABILITY.json'),
                placement_receipt_sha256=sha(out/'native/PLACEMENT.json'),actual_processes=1,model_files_loaded=2 if draft else 1)
            save(out/'CHECKED.json',checked);records.append(checked);slots[name]='COMPLETE';print('COMPLETE_D14_WORKER',len(records),count,name,flush=True)
        save(dest/'CHECKED.json',records);save(dest/'ANALYZER_RECORDS.private.json',dict(records=flat));save(dest/'RESULTS.json',d.shared.analyze(plan,flat))
        import panel_native
        namespace=dict(vars(panel_native));text=inspect.getsource(panel_native.costs).replace("'Qwen'","'Qwen14B'")
        exec(compile(text,'D14_family_label_cost_adapter','exec'),namespace);namespace['costs'](w,a.repo,plan,records)
        save(dest/'COST_READER_PORT.json',dict(base_sha256=sha(a.runtime/'panel_native.py'),changes=['Family label Qwen to Qwen14B'],clock_or_coverage_rule_changes=False))
        print('D14_C1024_PANEL_COMPLETE',flush=True)
    finally:
        for key in slots:
            if slots[key]=='STARTED':slots[key]='FAILED_RETAINED'
        save(dest/'ALL_SLOT_STATUS.json',dict(slots=slots,complete_workers=len(records),expected_workers=count,expected_measurements=16*count,expected_primers=2*count,
            no_selective_retries=True,all_controls_retained=True,inference_open=len(records)==count))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('work','baseline','runtime','builds','repo','predecessor'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--source-commit',required=True);a=p.parse_args()
    for key,value in vars(a).items():
        if isinstance(value,Path):setattr(a,key,value.resolve())
    execute(a)
