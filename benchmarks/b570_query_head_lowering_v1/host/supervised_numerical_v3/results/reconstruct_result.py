"""Post-stop CPU reconstruction only. No subprocess, backend or device calls.

Frozen supervision/numerical code is read-only. Missing outputs stay absent;
observer-invalid hosts are never promoted by descriptive output inspection.
"""
import collections
import hashlib
import itertools
import json
import math
import os
import pathlib
import struct
import sys
import time
import zipfile

HERE=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from legacy import OLD,ROOT,OUT,RUN,RUN_ID,LIMITS,load,save,sha,modules,need,STAGES,MODES,audit_raw,analyze_files,compare
from lifecycle_audit import audit
from workers import rows,usage
from timing import Coverage
from reference import solve

DEST=HERE/'results'
APPROVED='56f5787e41dcf8dcc4ecad83eb26bf406a483664e67a939dc66edf0af5015fdc'

def main():
    begin=time.monotonic();before=modules();need(sha(HERE/'F0.json')==APPROVED,'unchanged approved F0')
    f0=load(HERE/'F0.json');plan=load(HERE/'PLAN.json');wires=load(HERE/'WIRES.json');closed=load(RUN/'CLOSEOUT.json')
    committed=load(RUN/'CLOSEOUT_COMMITTED.json');need(sha(RUN/'CLOSEOUT.json')==committed['closeout_sha256'],'closeout identity')
    need(closed['status']=='STOPPED_INCOMPLETE' and closed['error']=='supervision stopped: directory live observation gap >1s','actual terminal stop')
    for row in f0['bound_files']+f0['old_raw_files']:need(sha(row['path'])==row['sha256'],'frozen/history byte drift '+row['path'])
    save(DEST/'BINDINGS_CHECK.json',dict(approved_F0_sha256=APPROVED,all_match=True,frozen_files=len(f0['bound_files']),
        historical_raw_files=len(f0['old_raw_files']),original_F0_not_rewritten=True,old_ledgers_unchanged=True))
    inputs=load(OLD/'INPUTS.json');by_input={x['id']:x for x in inputs};refs={};ref_receipts=[]
    manifest=load(OLD/'REFERENCE_MANIFEST.json')
    for item in inputs:
        need(sha(item['path'])==item['sha256'],'original input bytes');ref=solve(pathlib.Path(item['path']).read_bytes());refs[item['id']]=ref;stages={}
        for stage in STAGES:
            b=b''.join(struct.pack('<d',x) for x in ref[stage]);r=manifest['inputs'][item['id']]['stages'][stage]
            need(b==(OLD/r['path']).read_bytes(),'fresh independent FP64 bytes')
            stages[stage]=dict(elements=len(ref[stage]),sha256=hashlib.sha256(b).hexdigest())
        ref_receipts.append(dict(input_id=item['id'],geometry=item['cell']['geometry'],stages=stages))
    save(DEST/'FRESH_FP64_CHECK.json',dict(origin='PURE_CPU_SCALAR_REFERENCE_NOT_GPU',actual_original_inputs=16,
        stage_vectors=64,all_bitwise_to_frozen_reference=True,inputs=ref_receipts))

    expected=load(OLD/'EXPECTED_GRAPHS.json');controller_records={x['slot']['id']:x for x in closed['records']}
    records=[];good={};lives={};native_events={};monitors={};auditors={};all_samples=[];all_checks=[];costs=[];failures=[];calls=0
    numerical_info=[];special_cost=collections.Counter();stream_stats={s:dict(valid_reads=0,discarded_reads=0,max_read_duration_ns=0,
        max_initial_completion_ns=0,max_inter_observation_ns=0,max_terminal_gap_ns=0) for s in ('resource','directory')}
    wire_by_slot={w['slot_id']:w for w in wires}
    for slot in plan['slots']:
        folder=RUN/slot['id'];record=dict(slot=slot,status='UNSTARTED')
        if slot['id'] not in controller_records:
            need(not folder.exists(),'unrecorded started folder');records.append(record);continue
        record['status']='FAILED_OR_INVALID';life=load(folder/'LIFECYCLE.json');lives[slot['id']]=life
        need(life['purpose']=='FROZEN_NATIVE_PANEL' and life['clock']=='SYSTEM_MONOTONIC_NS','actual production clock/purpose')
        job=load(folder/'JOB.json');need(not any(k in job for k in ('faults','virtual_clock','test_module','cpu_child')),'no CPU-test hooks in native execution')
        wire=wire_by_slot[slot['id']];need((folder/'REQUEST.wire').read_bytes()==(HERE/wire['path']).read_bytes() and sha(folder/'REQUEST.wire')==wire['sha256'],'exact actual wire')
        raw=rows(folder/'raw.jsonl');native_events[slot['id']]=raw;mon=rows(folder/'MONITOR.jsonl');monitors[slot['id']]=mon
        auditors[slot['id']]=rows(folder/'AUDITOR.jsonl');calls+=sum(e['event']=='GRAPH_START' for e in raw)
        need(raw[0]['origin']=='NATIVE_VULKAN' and raw[0]['pid']==life['pid'] and raw[0]['request']==job['request'],'actual native identity')
        all_checks += [e for e in raw if e['event']=='MEMORY_CHECKPOINT']
        exit_ns=life['exit_observed_ns']
        for e in mon:
            if e['event']=='READ_END' and e['stream']=='resource' and e['end_ns']<=exit_ns:all_samples.append(e['values'])
            if e['event']=='READ_DISCARDED':need('values' not in e,'no values on discarded samples')
        record['lifecycle']=dict(pid=life['pid'],creation_FILETIME=life['creation_FILETIME'],returncode=life['returncode'],stop=life['stop'],
            GO_sent=life['GO_sent'],gate_admitted=life['gate_admitted'],observed_native_seconds=life['observed_native_lifetime_seconds'],
            post_exit_audit_seconds=life['post_exit_audit_seconds'],control_processes=life['control_processes'])
        if controller_records[slot['id']]['status']=='ADMITTED':
            checked=audit(folder);record['independent_lifecycle_audit']=checked
            native=audit_raw(raw,job['request'],life['pid'],expected);record['graph_calls']=native['graph_calls']
            record['status']='COMPLETE_ADMITTED'
            cost=load(folder/'SLOT_COST.json');costs.append(dict(slot=slot['id'],kind=slot['kind'],**cost))
            need(cost['slot_engineering_seconds']<=180,'complete-slot engineering bound')
            for stream in stream_stats:
                valid=[e for e in mon if e['event']=='READ_END' and e['stream']==stream and e['end_ns']<=exit_ns]
                target=stream_stats[stream];target['valid_reads']+=len(valid)
                target['discarded_reads']+=sum(e['event']=='READ_DISCARDED' and e['stream']==stream for e in mon)
                target['max_initial_completion_ns']=max(target['max_initial_completion_ns'],valid[0]['end_ns']-life['launch_begin_ns'])
                target['max_terminal_gap_ns']=max(target['max_terminal_gap_ns'],exit_ns-valid[-1]['begin_ns'])
                target['max_read_duration_ns']=max(target['max_read_duration_ns'],max(e['end_ns']-e['begin_ns'] for e in valid))
                for previous,current in zip(valid,valid[1:]):target['max_inter_observation_ns']=max(target['max_inter_observation_ns'],current['end_ns']-previous['begin_ns'])
            if slot['kind']=='graph':
                item=by_input[slot['input_id']];analysis,vectors=analyze_files(job['request'],native['graph'],folder,
                    pathlib.Path(item['path']).read_bytes(),refs[item['id']])
                for stage in STAGES:need(vectors[stage]==(folder/'normalized'/(stage+'.f32')).read_bytes(),'independent raw-stage restoration versus worker bytes')
                record['analysis']=analysis;record['physical_costs']={k:v for k,v in native.items() if k.startswith('PQ_extra')}
                record['actual_graph_sha256']=hashlib.sha256(json.dumps(native['graph'],sort_keys=True).encode()).hexdigest()
                numerical_info.append(record);good[item['id'],slot['mode'],slot['repeat']]=vectors
                desc=native['graph'];ts={t['id']:t for t in desc['tensors']}
                if desc['packed_q']:
                    packs=[t for t in ts.values() if t['op']=='CONT' and t['src']==[desc['Q']]]
                    need(len(packs)==1,'actual packed-Q CONT retained');special_cost['packed_Q_CONT_graphs']+=1;special_cost['packed_Q_CONT_logical_bytes']+=packs[0]['bytes']
                if desc['copied_kv']:
                    copies=[t for t in ts.values() if t['op']=='REPEAT' and t['src'][0] in (desc['K'],desc['V'])]
                    need(len(copies)==2,'actual two KV repeat nodes');special_cost['REPEAT4_graphs']+=1;special_cost['REPEAT4_KV_root_logical_bytes']+=sum(t['bytes'] for t in copies)
                if desc['dense_mask']:
                    repeats=[t for t in ts.values() if t['op']=='REPEAT'];need(len(repeats)==1,'actual QH_D mask REPEAT')
                    special_cost['QH_D_mask_REPEAT_graphs']+=1;special_cost['QH_D_mask_REPEAT_logical_bytes']+=repeats[0]['bytes']
        else:
            need(life['stop']=='directory live observation gap >1s' and not life['GO_sent'],'actual failed waiting-GO directory condition')
            states=rows(folder/'STATE.jsonl');stop=next(e for e in states if e['state']=='STOP');coverage=Coverage(life['launch_begin_ns'])
            for e in mon:
                stamp=e.get('end_ns',e.get('begin_ns',e.get('ns')))
                if stamp is not None and stamp<=stop['ns']:coverage.event(e)
            try:coverage.live(stop['ns'])
            except ValueError as e:need(str(e)==life['stop'],'independently reproduce actual stop')
            else:raise ValueError('failure was not independently reproduced')
            need(not any(e['event'].startswith('GRAPH_') for e in raw),'failed host has no graph events')
            need(not (folder/'vectors').exists() and not (folder/'normalized').exists(),'no fabricated output for failed host')
            failed=dict(slot=slot,pid=life['pid'],stop_ns=stop['ns'],initial_directory_deadline_age_ns=stop['ns']-life['launch_begin_ns'],
                directory_events=[e for e in mon if e.get('stream')=='directory'],gate_admitted=life['gate_admitted'],GO_sent=False,
                graph_calls=0,output_present=False,post_audit_worker_events=[e for e in auditors[slot['id']] if e['event'] in ('POST_AUDIT_BEGIN','POST_AUDIT_OK','AUDIT_ERROR')],
                note='Initial directory completion was absent before the strict1s deadline; discarded read is not a sample. Auditor failure after target termination is retained, not a declared expected outcome.')
            failures.append(failed);record['failure']=failed
        records.append(record)
    need(len(records)==161 and len(lives)==117 and len(good)==115 and calls==115,'full independent actual counts')
    need([s['id'] for s in plan['slots'][:117]]==list(lives),'ordered attempt prefix, no retry')
    need(len({(l['pid'],l['creation_FILETIME']) for l in lives.values()})==117,'distinct experiment process identities')
    save(DEST/'INDEPENDENT_RECONSTRUCTION.json',dict(run_id=RUN_ID,records=records,failed=failures,
        complete_admitted_numerical=len(good),source='Actual native raw stage/input files plus frozen independent lifecycle/numerical analyzers and freshly recomputed scalar references'))

    summary_pairs={f'{a}/{b}':dict(available=0,missing=0,all_four_equal=0,first_divergence=collections.Counter(),
        stages={s:dict(bit_mismatches=0,max_abs=0.,max_relative_defined=0.,max_ULP=0,nonfinite=0) for s in STAGES},first_counterexample=None) for a,b in itertools.combinations(MODES,2)}
    cells=[];repeat_rows=[];q1=[]
    def counterexample(left,right,relation,geometry):
        stage=relation['first_bitwise_divergence_stage']
        if stage is None:return None
        i=relation['stages'][stage]['first_mismatch_index'];extent=geometry['n'] if stage in ('QK','softmax') else 128
        a,b=left[stage][i*4:i*4+4],right[stage][i*4:i*4+4]
        return dict(stage=stage,index=i,logical_query=i//(geometry['h']*extent),head=(i//extent)%geometry['h'],element=i%extent,
            left=struct.unpack('<f',a)[0],right=struct.unpack('<f',b)[0],left_bits=a.hex(),right_bits=b.hex())
    for item in inputs:
        ident=item['id'];geometry=item['cell']['geometry'];cell=dict(input_id=ident,geometry=geometry,pairs=[],repeats=[])
        cell['slots']=[dict(slot=r['slot']['id'],mode=r['slot']['mode'],repeat=r['slot']['repeat'],status=r['status']) for r in records if r['slot'].get('input_id')==ident]
        for mode in MODES:
            a,b=(ident,mode,0),(ident,mode,1);r=dict(input_id=ident,geometry=geometry,mode=mode,status='MISSING_OR_INVALID')
            if a in good and b in good:
                slots=[s for s in plan['slots'] if s.get('input_id')==ident and s.get('mode')==mode]
                la,lb=(lives[s['id']] for s in slots);independent=(la['pid'],la['creation_FILETIME'])!=(lb['pid'],lb['creation_FILETIME'])
                relation=compare(good[a],good[b]);need(independent and relation['all_stages_bitwise_equal'],'independent repeat control')
                r.update(status='COMPLETE_ADMITTED',independent=True,relation=relation)
            repeat_rows.append(r);cell['repeats'].append(r)
        for repeat in (0,1):
            for a,b in itertools.combinations(MODES,2):
                left,right=(ident,a,repeat),(ident,b,repeat);r=dict(left=a,right=b,repeat=repeat,status='MISSING_OR_INVALID',first_divergence_stage='UNKNOWN')
                aggregate=summary_pairs[f'{a}/{b}']
                if left in good and right in good:
                    relation=compare(good[left],good[right]);r.update(status='COMPLETE_ADMITTED',relation=relation,first_divergence_stage=relation['first_bitwise_divergence_stage'])
                    aggregate['available']+=1;aggregate['all_four_equal']+=relation['all_stages_bitwise_equal'];aggregate['first_divergence'][relation['first_bitwise_divergence_stage'] or 'NONE']+=1
                    for s in STAGES:
                        values=relation['stages'][s];target=aggregate['stages'][s];target['bit_mismatches']+=values['bit_mismatches']
                        for k in ('max_abs','max_relative_defined','max_ULP','nonfinite'):target[k]=max(target[k],values[k])
                    witness=counterexample(good[left],good[right],relation,geometry)
                    if witness and aggregate['first_counterexample'] is None:aggregate['first_counterexample']=dict(input_id=ident,geometry=geometry,repeat=repeat,**witness)
                else:aggregate['missing']+=1
                cell['pairs'].append(r)
        if geometry['q']==1:
            base=good[ident,'MQ',0]
            for mode in MODES:
                for repeat in (0,1):
                    key=ident,mode,repeat;need(key in good,'complete40 q1 controls')
                    relation=compare(good[key],base);need(relation['all_stages_bitwise_equal'],'q1 common control')
                    q1.append(dict(input_id=ident,mode=mode,repeat=repeat,relation=relation))
        cells.append(cell)
    save(DEST/'ALL_STAGE_RELATIONS.json',dict(expected_cross_pairs=320,expected_independent_repeat_pairs=80,pair_summary=summary_pairs,
        cells=cells,independent_repeats=repeat_rows,q1_controls=q1,missing_is_unknown=True,numerical_tolerance=None))

    fp64={}
    for stage in STAGES:
        values=[r['analysis']['FP64_error'][stage] for r in numerical_info]
        fp64[stage]={key:max(v[key] for v in values) for key in ('max_abs','max_relative_defined','max_ULP_against_F32_rounded_reference')}
        fp64[stage]['nonfinite_actual']=sum(v['nonfinite_actual'] for v in values)
    pq={key:sum(r['physical_costs'][key] for r in numerical_info) for key in ('PQ_extra_CPU_copy_bytes','PQ_extra_API_upload_bytes','PQ_extra_logical_storage_bytes','PQ_extra_allocator_rounded_bytes')}
    helper=[p for l in lives.values() for p in l['control_processes']]
    post=[l['post_exit_audit_seconds'] for l in lives.values() if l['post_exit_audit_seconds'] is not None]
    native=[l['observed_native_lifetime_seconds'] for l in lives.values()]
    record_by_id={r['slot']['id']:r for r in records};unstarted=[r['slot'] for r in records if r['status']=='UNSTARTED']
    save(DEST/'SUMMARY.json',dict(run_id=RUN_ID,approved_F0_sha256=APPROVED,reviewed_commit='8008be6ce831a86b3074e16f57a6746187775491',
        status='STOPPED_INCOMPLETE_INITIAL_DIRECTORY_OBSERVATION',
        census=dict(planned=1,started=1,admitted=1,failed=0,unstarted=0,support_graphs=80,graph_calls=0),
        numerical=dict(planned=160,started=116,admitted=115,failed_or_invalid=1,unstarted=44,graph_start=calls,
            graph_return=sum(e['event']=='GRAPH_RETURN' for raw in native_events.values() for e in raw),graph_output=sum(e['event']=='GRAPH_OUTPUT' for raw in native_events.values() for e in raw),
            no_graph_call_failed_host=1),
        control_workers=dict(total=len(helper),monitor=len([x for x in helper if x['role']=='monitor']),auditor=len([x for x in helper if x['role']=='audit']),
            abnormal=[dict(role=p['role'],pid=p['pid'],returncode=p['returncode']) for p in helper if p['returncode']!=0],
            aggregate_CPU_kernel_user_seconds=sum((p['process_times']['kernel_100ns']+p['process_times']['user_100ns'])/1e7 for p in helper)),
        timings=dict(controller_engineering_through_closeout_seconds=committed['whole_controller_engineering_seconds_through_closeout'],
            external_controller_wall_seconds=load(DEST/'CONTROLLER_PROCESS.json')['external_controller_wall_seconds'],
            observed_native_lifetimes_sum_seconds=sum(native),observed_native_lifetime_max_seconds=max(native),
            successful_post_exit_audits=len(post),post_exit_audits_sum_seconds=sum(post),post_exit_audit_max_seconds=max(post),
            admitted_slot_engineering_sum_seconds=sum(x['slot_engineering_seconds'] for x in costs),admitted_slot_engineering_max_seconds=max(x['slot_engineering_seconds'] for x in costs),
            failed_slot_receipt_engineering_seconds=load(RUN/failures[0]['slot']['id']/'RECEIPT_COMMITTED.json')['slot_engineering_seconds_before_commit'],
            monitor_intervals=stream_stats,stop_initial_directory_gap_ns=failures[0]['initial_directory_deadline_age_ns'],
            scope='Native observation, post-audit and controller wall are different scopes; none is operator latency. Controller wall includes controls, preflight and cleanup.'),
        resources=dict(peak_native_RSS_bytes=max(v['RSS'] for v in all_samples),peak_control_RSS_bytes=max(v['RSS'] for s in all_samples for v in s['control_RSS']),
            min_host_available_bytes=min(v['host_available'] for v in all_samples),min_disk_free_bytes=min(v['disk_free'] for v in all_samples),
            GPU_checkpoint_count=len(all_checks),GPU_checkpoint_min_free_bytes=min(e['free'] for e in all_checks),continuous_GPU_residency=False),
        actual_alignment_bytes=sorted({e['actual_alignment'] for raw in native_events.values() for e in raw if e['event']=='DEVICE'}),
        q1_controls=40,q1_all_four_stages_bitwise_equal=True,
        admitted_independent_repeat_pairs=sum(r['status']=='COMPLETE_ADMITTED' for r in repeat_rows),planned_independent_repeat_pairs=80,
        pair_summary=summary_pairs,FP64_errors=fp64,first_scalar_difference_stages=dict(collections.Counter(r['analysis']['first_nonzero_FP64_error_stage'] or 'NONE' for r in numerical_info)),
        PQ_costs=pq,special_operator_logical_costs=dict(special_cost),
        logical_cost_scope='Logical tensor allocation/operator-copy bytes and API upload amounts; not measured DRAM traffic or speed',
        failed_slots=failures,unstarted_slots=unstarted,
        old_v2='37 attempts/36 admitted/1invalid/124unstarted/36calls/41.327s unchanged',old_S1='2/5.109s/159unstarted unchanged',
        diagnostics='7/13.172s/5success/2declared negatives unchanged',old_samples_imported=0,
        models=0,extra_probes=0,warmups=0,retries=0,GPU_tasks_after_stop=0,S2_S3='NOT_ADMITTED',actor_execution=False,performance_claim=None))

    # No writes to RUN: archive the authentic stopped tree exactly as found.
    entries=[]
    with zipfile.ZipFile(DEST/'RAW_EVIDENCE.zip','x',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(p for p in RUN.rglob('*') if p.is_file()):
            name=str(path.relative_to(RUN)).replace('\\','/');entries.append(dict(path=name,bytes=path.stat().st_size,sha256=sha(path)));z.write(path,name)
    with zipfile.ZipFile(DEST/'RAW_EVIDENCE.zip') as z:
        need(set(z.namelist())=={r['path'] for r in entries},'complete archive inventory')
        for entry in entries:need(hashlib.sha256(z.read(entry['path'])).hexdigest()==entry['sha256'],'raw archive readback')
    save(DEST/'RAW_MANIFEST.json',dict(files=entries,raw_file_count=len(entries),raw_bytes=sum(e['bytes'] for e in entries),
        archive_bytes=(DEST/'RAW_EVIDENCE.zip').stat().st_size,archive_sha256=sha(DEST/'RAW_EVIDENCE.zip'),all_members_readback_verified=True,
        failed_host_missing_graph_output_preserved=True,no_raw_file_overwritten=True))
    storage=usage(dict(storage_roots=[str(HERE),str(OUT)],run_root=str(RUN)))
    need(storage['output_bytes']+storage['archive_reserve_bytes']<=LIMITS['output_bytes'],'whole v3 plus export reserve')
    save(DEST/'CPU_DELIVERY_PROCESS.json',dict(origin='PURE_CPU_INDEPENDENT_RECONSTRUCTION_AND_DELIVERY',pid=os.getpid(),
        actual_wall_seconds=time.monotonic()-begin,subprocesses_started=0,GPU_queries=0,graph_computes=0,models=0,
        modules_before=before,modules_after=modules(),storage=storage,combined_storage_bytes=storage['output_bytes']+storage['archive_reserve_bytes']))
    result=load(DEST/'SUMMARY.json')
    print(json.dumps({k:result[k] for k in ('status','census','numerical','control_workers','timings','resources','FP64_errors','PQ_costs','special_operator_logical_costs','admitted_independent_repeat_pairs')},indent=2))
    print(json.dumps(dict(raw_files=len(entries),raw_archive_sha256=sha(DEST/'RAW_EVIDENCE.zip'),combined_storage_bytes=storage['output_bytes']+storage['archive_reserve_bytes'])))

if __name__=='__main__':main()
