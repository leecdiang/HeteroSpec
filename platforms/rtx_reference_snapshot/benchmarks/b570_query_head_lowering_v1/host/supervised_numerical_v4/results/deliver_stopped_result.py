"""CPU-only authentication/delivery of the stopped v4 registration.

Never invokes a subprocess, native executable, device API, backend or graph.
No historical/frozen file or failed-slot file is changed. Missing stays missing.
"""
import hashlib
import json
import os
import pathlib
import sys
import time
import zipfile
sys.dont_write_bytecode=True
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from legacy import HERE,OUT,RUN,ROOT,load,save,sha,need,modules

DEST=pathlib.Path(__file__).resolve().parent

def main():
    begin=time.monotonic_ns();before=modules();f0=load(HERE/'F0.json');plan=load(HERE/'PLAN.json')
    need(sha(HERE/'F0.json')=='5fab2cf08daa2f2ac57537ade5a16648a324ec0c0fcfa9a77d97d9b18bd351f7','approved F0')
    checked=[]
    for r in f0['bound_files']+f0['old_raw_files']:
        need(sha(r['path'])==r['sha256'],'frozen/history drift '+r['path']);checked.append(r)
    oldraw=0
    for history in f0['historical_raw_manifests']:
        for r in load(history['manifest'])['files']:
            p=pathlib.Path(history['root'])/r['path'];need(p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'v3 raw drift');oldraw+=1
    close=load(RUN/'CLOSEOUT.json');committed=load(RUN/'CLOSEOUT_COMMITTED.json');reconstruction=load(RUN/'V4_RECONSTRUCTION.json')
    need(sha(RUN/'CLOSEOUT.json')==committed['closeout_sha256'],'closeout commit')
    need(len(close['records'])==1 and close['records'][0]['slot']['kind']=='census' and close['records'][0]['status']=='FAILED_OR_INVALID','actual stopped registration')
    slot=plan['slots'][0];folder=RUN/slot['id']
    missing=['STATE.jsonl','REQUEST.wire','JOB.json','raw.jsonl','LIFECYCLE.json','MONITOR.jsonl','AUDITOR.jsonl','CONTROL_PIDS.json','EXIT_OBSERVED.json','STORAGE_LEASE.json','POST_AUDIT.json','vectors','normalized']
    need(all(not (folder/n).exists() for n in missing),'failure before launch; missing artifacts must stay absent')
    need(all(x['status']=='MISSING' and x['relation'] is None for x in reconstruction['cross_representation']+reconstruction['independent_repeats']+reconstruction['separate_v3_anchors']),'no missing comparisons promoted')
    need(len(reconstruction['cross_representation'])==124 and len(reconstruction['independent_repeats'])==34 and len(reconstruction['separate_v3_anchors'])==10,'complete expected comparison inventories')
    source=(HERE/'supervisor.py').read_text(encoding='utf-8').splitlines()
    lease_line=next(i+1 for i,s in enumerate(source) if 'lease=Lease(job)' in s)
    state_line=next(i+1 for i,s in enumerate(source) if "record('SPAWN_BEGIN')" in s)
    spawn_line=next(i+1 for i,s in enumerate(source) if 'native=subprocess.Popen' in s)
    need(lease_line<state_line<spawn_line,'source ordering before any native Popen')
    pulses=[json.loads(s) for s in (folder/'WATCH_1.jsonl').read_text(encoding='utf-8').splitlines()]
    save(DEST/'SOURCE_BINDINGS_CHECK.json',dict(F0_sha256=sha(HERE/'F0.json'),frozen_bound_files_verified=len(f0['bound_files']),v2_raw_verified=len(f0['old_raw_files']),v3_raw_verified=oldraw,
        supervisor_sha256=sha(HERE/'supervisor.py'),lease_initialization_line=lease_line,first_state_write_line=state_line,native_Popen_line=spawn_line,
        inference='Lease initialization fails before first state/SPAWN/Popen. No native/worker raw or lifecycle files exist; do not manufacture a lifecycle for a process that never started.',old_evidence_modified=False))
    save(DEST/'LAUNCH_CONTEXT.json',dict(recorded_after_stop=True,source='Actual tool launch in this conversation; descriptive delivery record, not a frozen prelaunch receipt',
        controller_PID=load(DEST/'CONTROLLER_PROCESS.json')['pid'],executable=str(pathlib.Path(sys.executable)),
        arguments=[str(HERE/'execute.py'),'--author-approved-f0-sha',sha(HERE/'F0.json')],
        stdout=str(DEST/'CONTROLLER.stdout.log'),stderr=str(DEST/'CONTROLLER.stderr.log'),
        delivery_directory_inside_sealed_watched_source_root=True,
        finding='Launcher delivery/log files were placed beneath the watched source root outside the active slot. Frozen watcher reports the results directory as changed. This is an integration error; exact notification action/writer/timestamp were not captured, so unique attribution is not asserted.',
        no_retry=True,no_runtime_patch=True))
    # Preserve the independently produced CPU reconstruction byte-for-byte.
    with (DEST/'INDEPENDENT_RECONSTRUCTION.json').open('xb') as f:f.write((RUN/'V4_RECONSTRUCTION.json').read_bytes())
    raw=[]
    for p in sorted(x for x in RUN.rglob('*') if x.is_file()):
        raw.append(dict(path=p.relative_to(RUN).as_posix(),bytes=p.stat().st_size,sha256=sha(p),origin='POST_STOP_CPU_RECONSTRUCTION' if p.name=='V4_RECONSTRUCTION.json' else 'FROZEN_CONTROLLER_OR_PRESPAWN_WATCH'))
    with zipfile.ZipFile(DEST/'RAW_EVIDENCE.zip','x',zipfile.ZIP_DEFLATED) as z:
        for r in raw:z.write(RUN/r['path'],r['path'])
    with zipfile.ZipFile(DEST/'RAW_EVIDENCE.zip') as z:
        need(set(z.namelist())=={r['path'] for r in raw},'complete capsule')
        for r in raw:
            b=z.read(r['path']);need(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'raw capsule readback')
    save(DEST/'RAW_MANIFEST.json',dict(files=raw,total_files=len(raw),total_bytes=sum(r['bytes'] for r in raw),archive_sha256=sha(DEST/'RAW_EVIDENCE.zip'),archive_bytes=(DEST/'RAW_EVIDENCE.zip').stat().st_size))
    groups={g:dict(planned=sum(s.get('group')==g for s in plan['slots']),native_started=0,completed=0,failed=0,unattempted=sum(s.get('group')==g for s in plan['slots'])) for g in 'ABCD'}
    summary=dict(run_id=f0['run_id'],approved_commit='03176f0115b0c3387961a386356c455651f59ff6',approved_F0_sha256=sha(HERE/'F0.json'),status='STOPPED_PRESPAWN_SEALED_DIRECTORY_NOTIFICATION',
        census=dict(planned=1,registration_attempts=1,failed_before_native_spawn=1,native_started=0,admitted=0,support_graph_descriptions_observed=0,unattempted_registration=0),groups=groups,
        actual_experimental_hosts=0,actual_graph_calls=0,actual_registered_monitor_processes=0,actual_registered_auditor_processes=0,controller_processes=1,controller_PID=42436,
        prelaunch_storage_watch_threads_created=2,prelaunch_watch_threads_are_not_additional_processes=True,
        engineering_seconds_through_closeout=committed['whole_controller_engineering_seconds_through_closeout'],external_controller_seconds=load(DEST/'CONTROLLER_PROCESS.json')['external_controller_wall_seconds'],
        native_lifetime_seconds=None,post_exit_native_audit_seconds=None,runtime_resource_reads=0,runtime_directory_reads=0,runtime_monitoring_gap_ns=None,
        prelaunch_output_watcher_pulses=len(pulses),prelaunch_output_watcher_max_read_ns=max(p['end_ns']-p['begin_ns'] for p in pulses),prelaunch_output_watcher_max_effective_interval_ns=max(p['end_ns']-p['previous_begin_ns'] for p in pulses),
        source_watcher_error=close['error'],source_watcher_pulse_journal_present=(folder/'WATCH_0.jsonl').exists(),
        q1=dict(admitted=0,planned=8),independent_repeats=dict(available=0,missing=34,planned=34),cross_mode_pairs=dict(available=0,missing=124,planned=124),v3_anchors=dict(available=0,missing=10,planned=10),
        numerical_results=None,FP64_errors=None,q4_non_MQ_bitwise_relation='UNKNOWN_NOT_EXECUTED',MQ_AV_difference='UNKNOWN_NOT_EXECUTED',device_alignment_actual=None,
        failed_registration_slots=[slot],unattempted_slots=close['unstarted'],all_native_unstarted_slots=plan['slots'],missing_actual_artifacts=missing,
        raw_files=len(raw),raw_bytes=sum(r['bytes'] for r in raw),raw_archive_sha256=sha(DEST/'RAW_EVIDENCE.zip'),
        no_scientific_counterexamples_observed_in_v4=True,reason='No numerical execution; absence is not a numerical PASS',retries=0,model_requests=0,extra_probes=0,warmups=0,new_device_queries=0,
        prior_S1_diagnostics_v2_v3_unchanged=True,S2_S3='NOT_ADMITTED',AV_only='NOT_EXECUTED',next_GPU_execution='REQUIRES_NEW_REVIEW_AND_AUTHORIZATION; DO_NOT_RESTART_THIS_RUN')
    save(DEST/'SUMMARY.json',summary)
    save(DEST/'CPU_DELIVERY_PROCESS.json',dict(pid=os.getpid(),CPU_wall_seconds=(time.monotonic_ns()-begin)/1e9,subprocesses_started=0,device_queries=0,graph_computes=0,
        modules_before=before,modules_after=modules(),separate_CPU_delivery_invocations=dict(prelaunch_identity_resource_tool=1,frozen_reconstruct_v4=1,post_stop_authentication_delivery=1),
        frozen_reconstruction_reported_CPU_wall_seconds=reconstruction['CPU_wall_seconds'],prelaunch_reported_CPU_wall_seconds=load(DEST/'PRELAUNCH_CHECK.json')['CPU_wall_seconds'],
        external_PowerShell_launcher_is_not_frozen_controller=True,not_a_whole_machine_process_count=True))
    actual=sum(p.stat().st_size for root in (HERE,OUT) for p in root.rglob('*') if p.is_file());run_files=[p for p in RUN.rglob('*') if p.is_file()]
    reserve=sum(p.stat().st_size for p in run_files)+len(run_files)*1024+1024**2;receipt_reserve=65536
    need(actual+reserve+receipt_reserve<=f0['limits']['output_bytes'],'delivery artifact+export ceiling')
    save(DEST/'PUBLICATION_BUDGET.json',dict(actual_v4_prepared_built_tested_run_delivery_bytes_before_this_receipt=actual,additional_raw_export_reserve_bytes=reserve,
        receipt_remaining_delivery_reserve_bytes=receipt_reserve,conservative_combined_bytes=actual+reserve+receipt_reserve,ceiling_bytes=f0['limits']['output_bytes'],
        inherited_CPU_preparation_retained=True,files_deleted=0,lowered_evidence_scope=False))
    print(dict(status=summary['status'],experimental_hosts=0,graphs=0,raw_files=len(raw),archive_sha256=sha(DEST/'RAW_EVIDENCE.zip'),actual_plus_export_reserved=actual+reserve+receipt_reserve))

if __name__=='__main__':main()
