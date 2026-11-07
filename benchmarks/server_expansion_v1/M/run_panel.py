"""Run exactly the prospectively balanced M1 panel after all native gates.

Reuses the successor's supervisor, freeze, transaction reader, physical checker
and cost coverage reader. No historical measurement is pooled into this panel.
"""
from pathlib import Path
import argparse, datetime, json, time
import run_m1 as m

def execute(w,baseline,repo,builds,runtime):
    m.load_runtime(runtime);need,read,save,sha=m.need,m.read,m.save,m.sha
    pin=read(Path(__file__).parent/'RUNTIME_PIN.json')
    need(pin['commit']=='592abdfe9267fd97ecbde18cd0ee9a1bfc319e20','Actual qualified successor pin')
    for name,h in pin['files'].items():
        path=runtime/Path(name).name if name.startswith('benchmarks/linux_transfer_v1/') else repo/name
        need(sha(path)==h,'Qualified supervisor/reader source differs from pinned successor: '+name)
    dest=w/'panel-01';plan=read(dest/'PLAN.json');qualification=w/'qualification-01'
    complete=read(qualification/'NATIVE_CHECKS_COMPLETE.json');need(complete['passed'] and complete['all_four_D4_paths'],'M1 finite native qualification required')
    need(read(w/'capability-negatives-01/CHECKED.json')['passed'],'Native unknown/ignored-field negative gates required')
    for r in complete['proofs']:need(sha(r['path'])==r['sha256'] and read(r['path'])['passed'],'Native proof changed')
    prospective=read(dest/'PROSPECTIVE_ORDER.json');need(prospective['plan_sha256']==sha(dest/'PLAN.json'),'Prospective M1 plan changed')
    need(sha(baseline/'ledger.jsonl')==prospective['prior_ledger_sha256'],'Historical ledger changed')
    old_text={x['path']:x['raw_sha256'] for x in read(baseline.parent/'public-export-final-01/TEXT_INDEX.json')['files']}
    def old_file(path):need(sha(path)==old_text[str(path.relative_to(baseline))],'Historical byte commitment changed')
    old_plan=read(baseline/'panel-01/PLAN.json');old_order=old_plan['workers'][0]['primers']+old_plan['workers'][0]['roots'];ref=baseline/'panel-01/reference-01'
    for p in (ref/'launch.json',ref/'HOST.json',baseline/'panel-01/REFERENCE-JOB.json'):old_file(p)
    launch=read(ref/'launch.json');need(read(ref/'HOST.json')['status']=='COMPLETE' and launch['job_sha256']==sha(baseline/'panel-01/REFERENCE-JOB.json') and launch['build_sha256']==sha(baseline/'build-R-01/BUILD.json'),'Historical independent reference binding')
    expected={}
    for i,key in enumerate(old_order):
        path=ref/'native'/f'reference-{i}'/'receipt.json';old_file(path);expected[key]=(read(path),path)
    reference_id='Linux-R-'+sha(baseline/'reference-01/REFERENCE_FREEZE.json')
    # This is an evidence binding, never a self-certificate of numerical PASS.
    save(w/'BINDING.json',{'runtime_commit':'592abdfe9267fd97ecbde18cd0ee9a1bfc319e20','not_pr196_worktree':True,
        'authorization_id':read(w/'config.json')['allocation_id'],'gpu_uuid':read(w/'config.json')['gpu_uuid'],
        'pr196_quiet_coordination':True,'reference_id':reference_id,'deployment_id':'A5000-Linux-C1024-Q8-M1',
        'runtime_evidence':{'path':str(qualification/'SOURCE_REVIEW.json'),'sha256':sha(qualification/'SOURCE_REVIEW.json')},
        'reference_evidence':{'path':str(baseline/'reference-01/REFERENCE_FREEZE.json'),'sha256':sha(baseline/'reference-01/REFERENCE_FREEZE.json')},
        'model_manifest':{'path':str(w/'inputs-01/MODELS.json'),'sha256':sha(w/'inputs-01/MODELS.json')},'numeric_qualification':'HOST_EVIDENCE_REQUIRED'})
    m.shared.binding_check(read(w/'BINDING.json'))
    save(dest/'SOURCE_FREEZE.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'adapter_files':{str(p):sha(p) for p in sorted(Path(__file__).parent.rglob('*')) if p.is_file() and '__pycache__' not in p.parts},
        'runtime_files':{str(p):sha(p) for p in sorted(runtime.glob('*.py'))},'M2':'NOT_RUN',
        'quiet_window':'Original panel complete; no other agent research downloads, builds, archiving or model processes during M1 formal workers. Company services remain running; nvidia-smi samples retained.',
        'reference_reused_before_all_new_candidate_outputs':True,'reference_panel_launch_sha256':sha(ref/'launch.json')})
    frozen=dest/'CONFIRMATION_FREEZE.json';m.freeze.confirmation(baseline/'reference-01/REFERENCE_FREEZE.json',qualification/'REGISTRY.json',dest/'PLAN.json',frozen)
    cfg=read(w/'config.json');cfg.update(freeze=str(frozen),freeze_sha256=sha(frozen));config=w/'config-confirmation.json';save(config,cfg)
    trace,_=m.checks.legacy_readers(repo);records=[];flat=[];slots={x['id']:'NOT_RUN' for x in plan['workers']}
    try:
        for worker in plan['workers']:
            name=worker['id'];out=dest/'runs'/name;job=dest/worker['job'];slots[name]='STARTED'
            invocation=time.monotonic()
            m.host.run(config,builds/worker['core']/'BUILD.json',job,out,'confirmation')
            invocation_wall=time.monotonic()-invocation
            payload=read(job);meta=read(out/'native/result.json');need(meta['native_capability']==payload['capability_request'],'Actual capability gate changed')
            need(meta['total_observed_API_calls']['context_creates']==2,'Actual D4 worker residency')
            calls=[]
            for key,entry in zip(worker['primers']+worker['roots'],payload['inputs']):
                path=out/'native'/entry['name']/'receipt.json';r=read(path);oracle,ref_path=expected[key]
                need(m.native.endpoint(r)==m.native.endpoint(oracle),'Independent frozen R endpoint mismatch')
                r['study_cap']=entry['input']['cap'];_,decoded=trace(r,entry['input']['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx')
                need(all(v==0 for v in r['observed_API_calls_within_service'].values()),'Heavy/state work in clean service')
                physical=m.native.Study.physical(r,entry['input'],True)
                need(r['graphs_reused']>0,'Clean D4 graph reuse not observed')
                need(r['target_final_kv']=={'min':0,'max':len(decoded['states'][-1]['prefix'])-1},'Actual terminal pending frontier')
                call={'root':key,'service_s':r['service_seconds'],'reference_id':reference_id,'reference_compatible':True,'trace_valid':True,
                    'native_receipt':str(path),'native_receipt_sha256':sha(path),'reference_receipt_sha256':sha(ref_path),'physical':physical,
                    'ids':r['ids'],'eog':r['eog'],'terminal_kind':r['stop_reason']};calls.append(call)
                if key in worker['roots']:
                    flat.append(dict(root=key,session=worker['session'],arm=worker['arm'],status='COMPLETE',qualified=True,
                        reference_id=reference_id,gpu_uuid=cfg['gpu_uuid'],service_s=r['service_seconds'],evidence_path=str(path),evidence_sha256=sha(path),
                        qualification_registry_sha256=sha(qualification/'REGISTRY.json'),native_capability_sha256=sha(out/'native/CAPABILITY.json')))
            clocks=read(out/'CLOCKS.json');h=read(out/'HOST.json');clocks.update(worker_wall_s=h['worker_wall_s'],wrapper_wall_s=h['wrapper_wall_s'],model_load_s=meta['model_load_s'],pool_setup_s=meta['pool_setup_s'])
            clocks['adapter_run_inclusive_s']=invocation_wall
            clocks['adapter_run_boundary']='Entire host.run invocation including dependency/model preflight, lock/admission, worker, telemetry and wrapper finalization; excludes later independent result verification'
            telemetry=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()];need(telemetry,'Actual memory sampling required')
            clocks.update(peak_observed_device_bytes=max((float(x['gpu']['memory.total'])-float(x['gpu']['memory.free']))*1024**2 for x in telemetry),
                memory_scope='Selected-device global used bytes, 2s sampled lower bound; not a per-process high-water mark')
            checked=dict(id=name,job_sha256=worker['job_sha256'],status='COMPLETE',native_checks_passed=True,requests=calls,actual_host_clocks=clocks,
                launch_sha256=sha(out/'launch.json'),loaded_modules_sha256=sha(out/'LOADED_MODULES.json'),native_capability_sha256=sha(out/'native/CAPABILITY.json'),actual_processes=1,model_loads=1)
            save(out/'CHECKED.json',checked);records.append(checked);slots[name]='COMPLETE';print('COMPLETE_M1_WORKER',len(records),16,name,flush=True)
        save(dest/'CHECKED.json',records);save(dest/'ANALYZER_RECORDS.private.json',{'records':flat});save(dest/'RESULTS.json',m.shared.analyze(plan,flat))
        from panel_native import costs
        costs(w,repo,plan,records)
        print('M1_BALANCED_PANEL_COMPLETE',flush=True)
    finally:
        for key in slots:
            if slots[key]=='STARTED':slots[key]='FAILED_RETAINED'
        save(dest/'ALL_SLOT_STATUS.json',dict(slots=slots,complete_workers=len(records),expected_workers=16,expected_measurements=256,expected_primers=32,
            no_selective_retries=True,all_controls_retained=True,inference_open=len(records)==16))

if __name__=='__main__':
    p=argparse.ArgumentParser();
    for key in ('work','baseline','repo','builds','runtime'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();execute(a.work.resolve(),a.baseline.resolve(),a.repo.resolve(),a.builds.resolve(),a.runtime.resolve())
