"""Noninteractive finite S3:24 R, frozen oracle, all bridges, final gates, panel.

Requires a complete prospective public F2 readback. No output-dependent input,
arm, order or budget selection, no native retry, and no dependence on SSH/AI.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback
sys.path.append(str(Path(__file__).resolve().parent.parent/'execution_v1'))
from host import Host,epoch,resource,verify_files
from support import need,read,sha,fresh,write
from verify import repeated_R,complete_bridge,clean,row,clock
from analyze import analyze


def utc():return dt.datetime.now(dt.timezone.utc).isoformat()


def execute(configuration):
    c=read(configuration);root=Path(c['execution_root']);need(not(root/'STATE.json').exists(),'Existing S3 stage: audit, never restart')
    need(c['execution_phase']=='S3_QUAL','First phase is complete new-root qualification')
    need(read(c['B2_public_delivery_proof'])['statistical_replay']=='PASSED_COMPLETE_128_OPERATIONS'and
         sha(c['B2_public_delivery_proof'])==c['B2_public_delivery_proof_sha256'],'B2 public delivery must close before S3')
    plan=read(c['manifest']);profile=read(c['state_profile']);roots=read(c['roots'])['inputs']
    need(len(roots)==12 and plan['planned_requests']==423,'Fixed complete439-slot envelope')
    began=time.monotonic();guard=None;completed=[];reference={};heavy={};tapes={};calibrations={};pair_costs=[]
    state=dict(status='S3_QUAL_RUNNING',utc=utc(),GPU_requests_complete=0,completed_workers=0)
    write(root/'STATE.json',state)
    def check_guard():
        need(guard is not None and guard.poll()is None,'Resource supervisor not alive')
        need(not(root/'PAUSE.json').exists()and not(root/'STOP_REQUESTED').exists(),'Resource/user safe-boundary stop')
        observed=read(root/'RESOURCE_GUARD_LATEST.private.json')
        need(time.time()-observed['epoch']<20 and not observed['events'],'Stale/conflicting current resource observation')
    try:
        with (root/'guard.stdout.log').open('xb')as so,(root/'guard.stderr.log').open('xb')as se:
            guard=subprocess.Popen([c['executables']['guard']['path'],'--parent',str(os.getpid()),'--',
                'taskset','-c','36',sys.executable,'-B',c['guard_script'],'--work',str(root)],
                stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
        for _ in range(40):
            if (root/'RESOURCE_GUARD_LATEST.private.json').exists():break
            need(guard.poll()is None,'Resource supervisor initialization failed');time.sleep(.5)
        with Host(configuration)as h:
            for worker in plan['workers']:
                if worker['stage']=='formal':continue
                check_guard();write(root/'STATE.json',dict(status='S3_QUAL_RUNNING',worker=worker['worker_id'],completed_workers=len(completed),utc=utc()))
                job=read(Path(c['manifest']).parent/worker['job']);kind=worker['kind'];slot=worker.get('slot');arm=worker.get('arm')
                output=h.run(worker,job,'R'if kind=='pristine-model-services'else'model',phase='S3_QUAL')
                check_guard();native=output/'native';proof={};validation_began=time.monotonic()
                if kind=='pristine-model-services':
                    reference[slot,worker['block']]=native
                    if worker['block']==1:
                        service=dict(id=f'new-root{slot:02d}',input=job['inputs'][0]['input'])
                        proof=repeated_R(reference[slot,0],native,service,profile)
                        fresh(root/'reference-checks'/(str(slot)+'.json'),proof)
                    if len(reference)==24:
                        # Content is frozen only after every independent repeat
                        # passes; no candidate has run at this point.
                        inventories=[]
                        for (s,repeat),directory in sorted(reference.items()):
                            records=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(directory.rglob('*'))if p.is_file()]
                            inventories.append(dict(slot=s,repeat=repeat,native=str(directory),files=records))
                        oracle=dict(status='ALL24_REPEATED_PRISTINE_R_REQUESTS_PASSED_AND_ORACLES_FROZEN',
                            roots_sha256=sha(c['roots']),manifest_sha256=c['manifest_sha256'],
                            reference_build=c['executables']['R'],inventories=inventories,
                            repeated_checks=[dict(path=str(root/'reference-checks'/(str(i)+'.json')),sha256=sha(root/'reference-checks'/(str(i)+'.json')))for i in range(12)],
                            roots={str(i):str(reference[i,0])for i in range(12)},utc=utc())
                        fresh(root/'NEW_ROOT_ORACLES_FROZEN.private.json',oracle)
                        h.c['new_root_oracles']=str(root/'NEW_ROOT_ORACLES_FROZEN.private.json')
                        h.c['new_root_oracles_sha256']=sha(h.c['new_root_oracles'])
                elif kind=='frontend-boundary-bridge':
                    proof=[]
                    for service in read(c['predecessor_manifest'])['services']:
                        name=service['id'];proof.append(complete_bridge(native,name+'-heavy',native,name+'-clean',
                            Path(c['old_R_native0']),service,profile,arm,root/'views'/worker['worker_id']/name))
                else:
                    service=dict(id=f'new-root{slot:02d}',input=job['inputs'][0]['input']);name=service['id']
                    if kind=='new-root-heavy-only':
                        heavy[slot,arm]=(native,name+'-heavy');clock(read(native/(name+'-heavy')/'receipt.json'))
                    elif kind in ('new-root-clean-pair-calibration','new-root-heavy-clean'):
                        if kind=='new-root-heavy-clean':heavy[slot,arm]=(native,name+'-heavy')
                        hn,hname=heavy[slot,arm];tape=read(hn/hname/'receipt.json')['semantic_tape_sha256'];proof=[]
                        clean_names=[x['name']for x in job['inputs']if not x['capture']]
                        for i,cn in enumerate(clean_names):
                            proof.append(complete_bridge(hn,hname,native,cn,reference[slot,0],service,profile,arm,
                                 root/'views'/worker['worker_id']/str(i)))
                            proof.append(clean(native/cn,reference[slot,0],service,profile,arm,tape))
                            pair_costs.append(dict(arm=arm,slot=slot,service_s=clock(read(native/cn/'receipt.json'))['elapsed_s']))
                        tapes[str(slot)+'/'+arm]=tape
                        if kind=='new-root-clean-pair-calibration':
                            calibrations[arm]=dict(worker_id=worker['worker_id'],HOST=read(output/'HOST.json'),
                                two_clean_request_service_s=[clock(read(native/x/'receipt.json'))['elapsed_s']for x in clean_names],
                                class_name='Fresh full model load/hash + full clean warm + full clean measured + receipt/exit',root_slot=0)
                    else:raise ValueError('Unregistered qualification kind')
                fresh(root/'comparisons'/(worker['worker_id']+'.json'),dict(proof=proof,validation_s=time.monotonic()-validation_began))
                completed.append(worker['worker_id'])
            need(len(completed)==66 and len(tapes)==36 and set(calibrations)==set('GBC'),'All fixed frontend/new-root/caller gates')
            cert=dict(status='ALL_NEW_ROOT_AND_FRONTEND_GATES_PASSED',workers=66,logical_operations=135,
                repeated_pristine_R_requests=24,old_boundary_heavy_clean_requests=36,new_root_bridge_calibration_requests=75,
                qualified_tapes=tapes,calibrations=calibrations,clean_service_costs=pair_costs,
                manifest_sha256=c['manifest_sha256'],roots_sha256=sha(c['roots']),
                new_root_oracles=h.c['new_root_oracles'],new_root_oracles_sha256=h.c['new_root_oracles_sha256'],
                comparison_files=[dict(path=str(root/'comparisons'/(w+'.json')),sha256=sha(root/'comparisons'/(w+'.json')))for w in completed],
                caller_s=time.monotonic()-began,UTC=utc())
            fresh(root/'S3_QUALIFICATION_CERTIFICATE.private.json',cert)
            budget=h.ledger.snapshot();need(c['budget_approval']['request_ceiling']-budget['requests']>=288+16,'Reserve all formal288 and16 failure slots after actual qualification')
        check_guard()
        # The same configuration is derived only in the explicitly frozen
        # oracle/certificate/cost/output-phase fields. Inputs/jobs/order do not change.
        formal=dict(c,execution_phase='S3',output_root=c['phase_output_roots']['S3'],
             S3_certificate=str(root/'S3_QUALIFICATION_CERTIFICATE.private.json'),S3_certificate_sha256=sha(root/'S3_QUALIFICATION_CERTIFICATE.private.json'),
             new_root_oracles=cert['new_root_oracles'],new_root_oracles_sha256=cert['new_root_oracles_sha256'])
        classes=[]
        for arm in 'GBC':
            calibration=calibrations[arm];maximum=max(x['service_s']for x in pair_costs if x['arm']==arm)
            adjustment=max(0,2*maximum-sum(calibration['two_clean_request_service_s']))
            classes.append(dict(arm=arm,workers=48,observed_same_configuration_complete_caller_max_s=calibration['HOST']['caller_s'],
                 conservative_all_root_service_adjustment_s=adjustment,
                 bound_s=48*(calibration['HOST']['caller_s']+adjustment)*1.25))
        observed=sum(x['bound_s']for x in classes)+144*c['fixed_worker_gap_s']+c['archive_bound_s']+900
        hard=144*(c['worker_timeout_s']+60)+144*c['fixed_worker_gap_s']+c['archive_bound_s']+900
        required=max(observed,hard)
        formal['S3_admission_cost_proof']=dict(whole_phase_fits=time.time()+required<=epoch(c['allocation_end_utc']),
             caller_cost_classes=classes,required_s=required,observed_class_estimate_s=observed,
             additional_hard_native_timeout_bound_s=hard,closeout_reserve_s=900,
             warmups_already_inside_full_caller=True,no_duplicate_warmup_cost=True,
             scope='Three exact two-clean-request configuration classes; input service variation conservatively added; hard timeout bound also fits')
        need(formal['S3_admission_cost_proof']['whole_phase_fits'],'Complete formal panel/archive/closeout window does not fit')
        fresh(root/'ADMISSION_FORMAL_DERIVED.private.json',formal)
        rows=[]
        with Host(root/'ADMISSION_FORMAL_DERIVED.private.json')as h:
            resource(formal);write(root/'STATE.json',dict(status='S3_FORMAL_RUNNING',completed_workers=0,utc=utc()))
            for worker in plan['workers']:
                if worker['stage']!='formal':continue
                check_guard();write(root/'STATE.json',dict(status='S3_FORMAL_RUNNING',worker=worker['worker_id'],completed_workers=len(rows)//2,utc=utc()))
                job=read(Path(c['manifest']).parent/worker['job']);output=h.run(worker,job,'model',phase='S3');check_guard()
                slot=worker['slot'];arm=worker['arm'];service=dict(id=f'new-root{slot:02d}',input=job['inputs'][0]['input']);proof=[]
                for ordinal,entry in enumerate(job['inputs']):
                    directory=output/'native'/entry['name']
                    proof.append(clean(directory,reference[slot,0],service,profile,arm,tapes[str(slot)+'/'+arm]))
                    rows.append(row(worker,ordinal,directory,job,read(output/'HOST.json')))
                fresh(root/'formal-checks'/(worker['worker_id']+'.json'),proof)
            check_guard();need(len(rows)==288,'Full fixed S3 panel')
            fresh(root/'S3_ROWS.json',rows);fresh(root/'S3_ANALYSIS.json',analyze(rows,'S3'))
            snapshot=h.ledger.snapshot();fresh(root/'FINAL_ACCOUNTING.json',{k:v for k,v in snapshot.items()if k not in ('events','operations')})
            with (root/'FINAL_GLOBAL_LEDGER.jsonl').open('xb')as f:f.write(Path(c['ledger']).read_bytes())
        write(root/'STATE.json',dict(status='S3_COMPLETE_REQUIRES_PUBLIC_ARCHIVE_REPLAY',workers=144,warmups=144,measurements=144,
             total_stage_logical_requests=423,caller_s=time.monotonic()-began,utc=utc()))
    except BaseException as error:
        write(root/'STATE.json',dict(status='S3_PARTIAL_STOPPED',reason=str(error),completed_qualification_workers=len(completed),
             caller_s=time.monotonic()-began,utc=utc(),no_native_retry=True))
        fresh(root/'FAILURE.json',dict(reason=str(error),traceback=traceback.format_exc()));raise
    finally:
        (root/'GUARD_DONE').touch(exist_ok=False)
        if guard:
            try:guard.wait(timeout=20)
            except subprocess.TimeoutExpired:guard.terminate();guard.wait(timeout=10)
        fresh(root/'CONTROLLER_CLOSED.private.json',dict(pid=os.getpid(),utc=utc(),caller_s=time.monotonic()-began))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--configuration',type=Path,required=True);execute(p.parse_args().configuration)
