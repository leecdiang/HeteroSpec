"""Only new GPU entry. Preparation/tests never invoke main or the native host."""
import argparse
import datetime
import json
import os
import subprocess
import time
from legacy import HERE,OLD,ROOT,OUT,RUN,RUN_ID,LIMITS,PYTHON,load,save,sha,need,compare,modules,STAGES,MODES
from registration import serialize
from supervisor import supervise
from lifecycle_audit import audit

def admission(approved):
    need(approved==sha(HERE/'F0.json'),'exact author-approved new F0 required')
    f0=load(HERE/'F0.json');need(f0['run_id']==RUN_ID and f0['limits']==LIMITS,'registered identity/ceilings')
    for row in f0['bound_files']:need(sha(row['path'])==row['sha256'],'frozen file drift '+row['path'])
    for row in f0['old_raw_files']:need(sha(row['path'])==row['sha256'],'old raw history drift')
    env={k:v for k,v in sorted(os.environ.items()) if k.startswith(('GGML_','VK_','LLAMA_'))}
    need(env==f0['environment'],'environment drift')
    plan=load(HERE/'PLAN.json');wires=load(HERE/'WIRES.json')
    for s,w in zip(plan['slots'],wires):need((HERE/w['path']).read_bytes()==serialize(s,f0['execution_binding_sha256']) and sha(HERE/w['path'])==w['sha256'],'actual serialized wire drift')
    need(not RUN.exists(),'run exists; no restart, resume or retry')
    return f0,plan,wires

def main():
    panel_begin=time.monotonic_ns();parser=argparse.ArgumentParser();parser.add_argument('--author-approved-f0-sha',required=True);args=parser.parse_args()
    before=modules();f0,plan,wires=admission(args.author_approved_f0_sha)
    # Reuse only OS inventory; this function never queries a device.
    from run_panel import preflight_processes
    inventory=preflight_processes();RUN.mkdir(parents=True,exist_ok=False)
    save(RUN/'AUTHORIZATION.json',dict(approved_F0_sha256=args.author_approved_f0_sha,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Actual later human confirmation must precede this entry'))
    save(RUN/'PREFLIGHT.json',inventory);records=[];error=None;vectors={};identities={};common={}
    try:
        for slot,w in zip(plan['slots'],wires):
            need(time.monotonic_ns()-panel_begin<=3600*10**9,'whole-controller engineering budget')
            need(slot['index']==0 or records[0]['status']=='ADMITTED','census first')
            if slot.get('q',1)>1:need(len([r for r in records if r['slot']['index'] in range(1,41) and r['status']=='ADMITTED'])==40,'all40 q1 before q>1')
            folder=RUN/slot['id'];wire=(HERE/w['path']).read_bytes();need(wire==serialize(slot,f0['execution_binding_sha256']),'wire at attempt')
            need(sha(f0['executable']['path'])==f0['executable']['sha256'],'host changed before attempt')
            if slot['kind']=='graph':
                item=next(x for x in load(OLD/'INPUTS.json') if x['id']==slot['input_id']);need(sha(item['path'])==item['sha256'],'input changed before attempt')
            row=dict(slot=slot,status='STARTED');records.append(row);save(RUN/(str(slot['index']).zfill(3)+'-ATTEMPT.json'),row)
            request=json.loads(wire);start=time.monotonic_ns()
            job=dict(purpose='FROZEN_NATIVE_PANEL',folder=str(folder),disk_root=str(ROOT),run_root=str(RUN),storage_roots=[str(HERE),str(OUT)],
                limits=LIMITS,per_slot_seconds=180,panel_seconds=3600,panel_begin_ns=panel_begin,F0_path=str(HERE/'F0.json'),
                input_id=slot.get('input_id'),request=request,wire_bytes=wire.decode('utf-8'))
            life=supervise(job,[f0['executable']['path'],str(folder/'REQUEST.wire'),str(folder/'raw.jsonl')])
            need(life['stop'] is None,'supervision stopped: '+str(life['stop']));audit(folder)
            if slot['kind']=='graph':
                data={s:(folder/'normalized'/(s+'.f32')).read_bytes() for s in STAGES};key=(slot['input_id'],slot['mode'])
                identity=(life['pid'],life['creation_FILETIME'])
                if slot['repeat']==1:
                    need(key in vectors and identities[key]!=identity,'independent process repeat identity')
                    relation=compare(data,vectors[key]);save(folder/'REPEAT_RELATION.json',relation);need(relation['all_stages_bitwise_equal'],'same-implementation repeat mismatch')
                else:vectors[key]=data;identities[key]=identity
                if slot['q']==1:
                    if slot['input_id'] not in common:common[slot['input_id']]=data
                    relation=compare(data,common[slot['input_id']]);save(folder/'Q1_RELATION.json',relation);need(relation['all_stages_bitwise_equal'],'q1 common path mismatch')
                pairs=[]
                for other in MODES:
                    k=(slot['input_id'],other,slot['repeat'])
                    if k in vectors:pairs.append(dict(other_mode=other,relation=compare(data,vectors[k])))
                save(folder/'CROSS_RELATIONS.json',pairs);vectors[slot['input_id'],slot['mode'],slot['repeat']]=data
            row['observed_native_seconds']=life['observed_native_lifetime_seconds'];row['post_exit_audit_seconds']=life['post_exit_audit_seconds']
            save(folder/'SLOT_COST.json',dict(slot_engineering_seconds=(time.monotonic_ns()-start)/1e9,
                definition='Whole slot including spawning,2 CPU workers, monitoring, identity/numerical audits, cleanup, comparisons and lifecycle writes',
                native_seconds=life['observed_native_lifetime_seconds'],post_exit_audit_seconds=life['post_exit_audit_seconds']))
            need(time.monotonic_ns()-start<=180*10**9,'complete-slot engineering ceiling')
            row['status']='ADMITTED'
    except Exception as e:
        error=str(e)
        if records and records[-1]['status']=='STARTED':records[-1]['status']='FAILED_OR_INVALID'
    finally:
        completed={r['slot']['id'] for r in records};after=modules();elapsed=(time.monotonic_ns()-panel_begin)/1e9
        save(RUN/'CLOSEOUT.json',dict(status='STOPPED_INCOMPLETE' if error or len(records)!=161 else 'COMPLETE_PENDING_INDEPENDENT_RECONSTRUCTION',
            error=error,records=records,unstarted=[s for s in plan['slots'] if s['id'] not in completed],
            whole_controller_engineering_seconds=elapsed,definition='Includes preflight and controller/control-worker/audit/cleanup costs; not old v2 owned definition or graph latency',
            extra_control_worker_processes=sum(len(load(p).get('control_processes',[])) for p in RUN.glob('*/LIFECYCLE.json')),
            modules_before=before,modules_after=after,S2_S3='NOT_ADMITTED',retries=0,model_requests=0))
        ended=time.monotonic_ns()
        save(RUN/'CLOSEOUT_COMMITTED.json',dict(whole_controller_engineering_seconds_through_closeout=(ended-panel_begin)/1e9,
            within_3600_seconds=(ended-panel_begin)<=3600*10**9,closeout_sha256=sha(RUN/'CLOSEOUT.json')))
        if ended-panel_begin>3600*10**9:error=error or 'whole-controller engineering ceiling at close'
    if error:raise SystemExit(error)

if __name__=='__main__':main()
