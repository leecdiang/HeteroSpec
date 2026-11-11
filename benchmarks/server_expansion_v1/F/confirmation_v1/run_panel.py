"""One prospective24-worker Llama panel after qualified finite native gates."""
from pathlib import Path
import argparse, datetime, inspect, json, sys, time

def execute(a):
    sys.path.insert(0,str(a.integration));import integrate as d
    d.load(a.runtime);need,read,save,sha=d.need,d.read,d.save,d.sha
    from quiet import check as check_quiet
    original_resources=d.host.check_resources
    def guarded_resources(config,group=None):
        check_quiet(a.baseline.parent)
        return original_resources(config,group)
    d.host.check_resources=guarded_resources
    w=a.work;dest=w/'panel-01';plan=read(dest/'PLAN.json');q=w/'qualification-registry-04'
    complete=read(q/'NATIVE_CHECKS_COMPLETE.json');need(complete['passed'] and complete['all_six_arms'],'All six actual native controls first')
    need(read(q/'PROJECTION_DISPATCH.json')['passed'],'Actual Llama backend marker/projection descriptors required')
    need(read(w/'capability-negatives-01/CHECKED.json')['passed'],'Native unknown/ignored-field gates required')
    for row in complete['proofs']:need(sha(row['path'])==row['sha256'] and read(row['path'])['passed'],'Native proof changed')
    need(len(plan['workers'])==24 and plan['measurements']==288 and plan['primers']==48 and set(plan['arms'])==set(d.ARMS),'Original six-arm measurement envelope')
    need(read(dest/'PROSPECTIVE_ORDER.json')['plan_sha256']==sha(dest/'PLAN.json'),'Prospective plan changed')
    cfg=read(w/'config-reference-frozen-01.json');rf=Path(cfg['reference_freeze']);need(sha(rf)==cfg['reference_freeze_sha256'],'Original independent Llama R changed')
    need(read(rf)['build']['sha256']==sha(a.builds/'reference/BUILD.json'),'Different independent reference build')
    # New cohort endpoints come from the original qualified Llama R executable.
    prepared=read(w/'inputs-formal-01/PROSPECTIVE_COHORT_CHECKED.json')
    need(prepared['passed'] and prepared['model_forwards']==0,'Prospective no-forward cohort preparation')
    need(prepared['plan_sha256']==sha(dest/'PLAN.json'),'Same pre-outcome plan')
    cohort=read(w/'inputs-formal-01/COHORT.json')['inputs'];primers=read(w/'inputs-formal-01/PRIMERS.json')['inputs']
    lookup={x['id']:x for x in cohort+primers};order=[x['id'] for x in primers+cohort]
    need(len(order)==len(set(order))==14,'Fixed14 endpoints')
    need(read(dest/'PROSPECTIVE_ORDER.json')['cohort_sha256']==sha(w/'inputs-formal-01/COHORT.json'),'Prospective cohort changed')
    job=dest/'REFERENCE-JOB.json';payload=read(job)
    need(prepared['reference_job_sha256']==sha(job),'Original prospective independent reference job')
    need([x['input']['id'] for x in payload['inputs']]==order and payload['capability_request']['core']=='reference','Exact R input order and scalar capability')
    pre_source={str(x):sha(x) for x in Path(__file__).parent.rglob('*') if x.is_file() and '__pycache__' not in x.parts}
    save(dest/'PRE_REFERENCE_SOURCE_FREEZE.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_commit=a.source_commit,files=pre_source,prepared_cohort_sha256=sha(w/'inputs-formal-01/PROSPECTIVE_COHORT_CHECKED.json'),
        reference_job_sha256=sha(job),new_cohort_model_outputs_seen=0,new_cohort_candidate_outputs_seen=0))
    ref=dest/'reference-01';d.host.run(w/'config-reference-frozen-01.json',a.builds/'reference/BUILD.json',job,ref,'reference')
    for path,h in pre_source.items():need(sha(path)==h,'Prospective source changed during independent R')
    expected={key:(read(ref/'native'/f'reference-{i}/receipt.json'),ref/'native'/f'reference-{i}/receipt.json') for i,key in enumerate(order)}
    # The coordinator must close all its downloads/builds before this stage.
    save(dest/'SOURCE_FREEZE.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        adapter_files={str(x):sha(x) for x in Path(__file__).parent.rglob('*') if x.is_file() and '__pycache__' not in x.parts},
        runtime_files={str(x):sha(x) for x in a.runtime.glob('*.py')},source_commit=a.source_commit,
        independent_R_freeze_sha256=sha(rf),reference_panel_launch_sha256=sha(ref/'launch.json'),
        pre_reference_source_freeze_sha256=sha(dest/'PRE_REFERENCE_SOURCE_FREEZE.json'),prepared_cohort_sha256=sha(w/'inputs-formal-01/PROSPECTIVE_COHORT_CHECKED.json'),
        quiet_window='This coordinator has finished all acquisition, builds and archiving before formal timing. Company services remain running; selected-device and host resource samples retained.',
        C4096='NOT_RUN',M2='NOT_RUN',formal_internal_state_recomparisons=False))
    source=dest/'SOURCE_FREEZE_CHECKED.json';save(source,dict(passed=True,source_freeze_sha256=sha(dest/'SOURCE_FREEZE.json'),
        qualification_source_review_sha256=sha(read(q/'REGISTRY.json')['checks']['source_freeze']['evidence']),projection_dispatch_sha256=sha(q/'PROJECTION_DISPATCH.json'),
        native_negative_gate_sha256=sha(w/'capability-negatives-01/CHECKED.json')))
    registry=read(q/'REGISTRY.json');registry['checks']['source_freeze']['evidence']=str(source);registry_path=dest/'REGISTRY-COMPLETE.json';save(registry_path,registry)
    frozen=dest/'CONFIRMATION_FREEZE.json';d.freeze.confirmation(rf,registry_path,dest/'PLAN.json',frozen)
    cfg.update(freeze=str(frozen),freeze_sha256=sha(frozen));config=w/'config-confirmation-formal-01.json';save(config,cfg)
    reference_id='Llama-F-C1024-R-'+sha(rf);trace,_=d.checks.legacy_readers(a.repo);records=[];flat=[];slots={x['id']:'NOT_RUN' for x in plan['workers']}
    try:
        for worker in plan['workers']:
            name=worker['id'];out=dest/'runs'/name;job=dest/worker['job'];payload=read(job);draft=payload['draft'];slots[name]='STARTED'
            start=time.monotonic();d.host.run(config,a.builds/worker['core']/'BUILD.json',job,out,'confirmation');invocation=time.monotonic()-start
            meta=read(out/'native/result.json');need(meta['native_capability']==payload['capability_request'],'Actual deployment differs from frozen request')
            need(meta['total_observed_API_calls']['context_creates']==(2 if draft else 1),'True target-only versus pair residency')
            calls=[]
            for key,entry in zip(worker['primers']+worker['roots'],payload['inputs']):
                path=out/'native'/entry['name']/'receipt.json';r=read(path);oracle,oracle_path=expected[key]
                need(d.native.endpoint(r)==d.native.endpoint(oracle),'Independent Llama R endpoint mismatch')
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
            save(out/'CHECKED.json',checked);records.append(checked);slots[name]='COMPLETE';print('COMPLETE_LLAMA_F_WORKER',len(records),24,name,flush=True)
        save(dest/'CHECKED.json',records);save(dest/'ANALYZER_RECORDS.private.json',dict(records=flat));save(dest/'RESULTS.json',d.shared.analyze(plan,flat))
        import panel_native
        namespace=dict(vars(panel_native));text=inspect.getsource(panel_native.costs).replace("'Qwen'","'Llama'")
        exec(compile(text,'Llama_family_label_cost_adapter','exec'),namespace);namespace['costs'](w,a.repo,plan,records)
        save(dest/'COST_READER_PORT.json',dict(base_sha256=sha(a.runtime/'panel_native.py'),changes=['Family label Qwen to Llama'],clock_or_coverage_rule_changes=False))
        print('LLAMA_F_C1024_PANEL_COMPLETE',flush=True)
    finally:
        for key in slots:
            if slots[key]=='STARTED':slots[key]='FAILED_RETAINED'
        save(dest/'ALL_SLOT_STATUS.json',dict(slots=slots,complete_workers=len(records),expected_workers=24,expected_measurements=288,expected_primers=48,
            no_selective_retries=True,all_controls_retained=True,inference_open=len(records)==24))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('work','baseline','runtime','builds','repo','integration'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--source-commit',required=True);a=p.parse_args()
    for key,value in vars(a).items():
        if isinstance(value,Path):setattr(a,key,value.resolve())
    execute(a)
