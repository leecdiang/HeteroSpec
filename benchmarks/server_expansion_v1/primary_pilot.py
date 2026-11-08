"""Bounded clean-service pilot on exposed development roots after both gates.

One six-arm order, one observation/root/arm: no formal performance inference.
This entrypoint must run under the parent primary queue's GPU scheduling lock.
"""
from pathlib import Path
import argparse, copy, datetime, importlib.util, json, time

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','runtime','work','builds','repo','qualification','out'):
        parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args()
    spec=importlib.util.spec_from_file_location('primary_pilot_lane',a.source/'integrate.py')
    d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d);d.load(a.runtime)
    need,read,save,sha=d.need,d.read,d.save,d.sha
    summary=read(a.qualification/'NATIVE_CHECKS_COMPLETE.json')
    need(summary['passed'] and summary['all_six_arms'],'All actual native qualification first')
    for row in summary['proofs']:
        need(sha(row['path'])==row['sha256'] and read(row['path'])['passed'],'Qualified proof changed')
    need(read(a.qualification/'PROJECTION_DISPATCH.json')['passed'],'Actual dispatch gate')
    need(read(a.work/'capability-negatives-01/CHECKED.json')['passed'],'Native negative gate')
    need(not a.out.exists(),'Fresh pilot epoch; preserve failures and complete native jobs')
    a.out.mkdir(parents=True)
    roots=read(a.work/'inputs-01'/(d.FAMILY+'-DEVELOPMENT.json'))['inputs']
    need(len(roots) in (3,4),'Only the original exposed development population')
    models=read(a.work/'inputs-01/MODELS.json')[d.FAMILY]
    structures=read(a.work/'MODEL_STRUCTURES.json')
    cfg=read(a.work/'config-reference-frozen-01.json');rf=Path(cfg['reference_freeze'])
    need(sha(rf)==cfg['reference_freeze_sha256'],'Independent model-specific R changed')
    oracle=a.work/'reference-01'/(d.FAMILY+'-R-free-repeat-1')
    need(read(oracle/'HOST.json')['status']=='COMPLETE','Exact original independent free R')
    expected={x['id']:(oracle/'native'/f'dev-{i}'/'receipt.json') for i,x in enumerate(roots)}
    registry=read(a.qualification/'REGISTRY.json')
    module_maps={read(x['build'])['executable_sha256']:read(x['loaded_modules']) for x in registry['executables']}
    # Fixed before these pilot outcomes; first row of the registered six-arm
    # Williams layout. A single row has no position/adjacency balance claim.
    arms=['W_L4_M','W_P_M','L_P_D4','L_L4_M','W_L4_D4','L_P_M']
    primers=[roots[-1],roots[0]];jobs={}
    for arm in arms:
        core,cut,draft=d.ARMS[arm]
        job=copy.deepcopy(models)
        job.update(residency='matched' if draft else 'target_only',draft=draft,
            draft_width=4 if draft else 1,lowering=cut,profile=False,
            capability_request=d.capability(models,structures,core,cut,draft),
            inputs=[dict(name=f'request-{i:02d}',input=x,capture=False) for i,x in enumerate(primers+roots)])
        if not draft:job.pop('draft_model');job.pop('draft_sha256')
        path=a.out/'jobs'/(arm+'.json');save(path,job);jobs[arm]=path
    save(a.out/'PROSPECTIVE_FREEZE.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_sha256=sha(Path(__file__)),integration_source_sha256=sha(a.source/'integrate.py'),
        qualification_sha256=sha(a.qualification/'NATIVE_CHECKS_COMPLETE.json'),
        reference_freeze_sha256=sha(rf),jobs={k:sha(p) for k,p in jobs.items()},arm_order=arms,
        scope='Exposed development roots; bounded clean-service readiness pilot, no formal inference',
        primers_per_worker=2,observations_per_root_arm=1,model_or_numerical_changes=False))
    trace,_=d.checks.legacy_readers(a.repo);records=[];phase='START'
    try:
        for arm in arms:
            phase=arm;core,cut,draft=d.ARMS[arm];payload=read(jobs[arm]);out=a.out/'runs'/arm
            start=time.monotonic()
            d.host.run(a.work/'config-reference-frozen-01.json',a.builds/core/'BUILD.json',jobs[arm],out,'development')
            invocation=time.monotonic()-start;meta=read(out/'native/result.json')
            need(meta['native_capability']==payload['capability_request'],'Actual complete native deployment')
            need(meta['total_observed_API_calls']['context_creates']==(2 if draft else 1),'Real M/D residency')
            need(read(out/'LOADED_MODULES.json')==module_maps[read(a.builds/core/'BUILD.json')['executable_sha256']],
                 'Pilot actual modules differ from qualified native set')
            calls=[]
            for i,entry in enumerate(payload['inputs']):
                p=out/'native'/entry['name']/'receipt.json';row=read(p);x=entry['input'];ref=expected[x['id']]
                need(d.native.endpoint(row)==d.native.endpoint(read(ref)),'Independent free R endpoint')
                row['study_cap']=x['cap'];trace(row,x['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx')
                physical=d.native.Study.physical(row,x,draft)
                need(all(v==0 for v in row['observed_API_calls_within_service'].values()),'Heavy/state calls in clean pilot')
                calls.append(dict(root=x['id'],kind='primer' if i<2 else 'measurement',service_s=row['service_seconds'],
                    native_receipt=str(p),native_receipt_sha256=sha(p),reference_receipt_sha256=sha(ref),physical=physical))
            telemetry=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
            record=dict(arm=arm,passed=True,calls=calls,measurement_service_s=sum(x['service_s'] for x in calls[2:]),
                adapter_invocation_inclusive_s=invocation,HOST=read(out/'HOST.json'),CLOCKS=read(out/'CLOCKS.json'),
                module_map_sha256=sha(out/'LOADED_MODULES.json'),
                minimum_sampled_free_bytes=min(float(x['gpu']['memory.free'])*1024**2 for x in telemetry),
                memory_scope='Selected-device free bytes,2s samples; no per-process high-water claim')
            save(out/'CHECKED.json',record);records.append(record)
            print('COMPLETE_PRIMARY_PILOT',d.FAMILY,arm,flush=True)
        totals={x['arm']:x['measurement_service_s'] for x in records}
        save(a.out/'STATUS.json',dict(status='COMPLETE',passed=True,family=d.FAMILY,
            roots=len(roots),measurements=len(roots)*6,primers=12,all_six_arms=True,
            service_totals_s=totals,LP_over_each_control={k:totals['L_P_D4']/v for k,v in totals.items() if k!='L_P_D4'},
            scope='Known/exposed-root single-session pilot; no population effect or confidence interval',
            internal_state_recomparison='NOT_RUN_DURING_CLEAN_PILOT; earlier finite qualification bound',
            records=[dict(path=str(a.out/'runs'/x['arm']/'CHECKED.json'),sha256=sha(a.out/'runs'/x['arm']/'CHECKED.json')) for x in records]))
    except BaseException as error:
        save(a.out/'STATUS.json',dict(status='FAILED_RETAINED',phase=phase,error=str(error),complete_arms=len(records),
             no_native_slot_retry=True,formal_performance='NOT_RUN'));raise

if __name__=='__main__':main()
