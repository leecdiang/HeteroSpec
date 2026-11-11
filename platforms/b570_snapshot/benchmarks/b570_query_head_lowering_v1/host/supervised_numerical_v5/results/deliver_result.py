"""Post-stop CPU evidence certification only; never launches an experiment."""
import datetime
import hashlib
import json
import pathlib
import sys
import time
import zipfile

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from legacy import RUN, OUT, EXTERNAL_LOG_ROOT, load, save, sha, need, modules
from workers import full_usage

begin = time.monotonic_ns()
before = modules()
DEST = HERE / 'results'
f0 = load(HERE / 'F0.json')
need(sha(HERE / 'F0.json') == 'ff596ea94e80a80d004bdb6c9236d0494687a597149baa0c03a77f75e507db44', 'approved F0 changed')
for row in f0['bound_files']:
    need(sha(row['path']) == row['sha256'], 'bound file changed: ' + row['path'])
for row in f0['old_raw_files']:
    need(sha(row['path']) == row['sha256'], 'old v2 evidence changed')
historical = []
for history in f0['historical_raw_manifests']:
    entries = load(history['manifest'])['files']
    for row in entries:
        p = pathlib.Path(history['root']) / row['path']
        need(p.stat().st_size == row['bytes'] and sha(p) == row['sha256'], 'historical raw changed')
    historical.append(dict(root=history['root'], files=len(entries)))
close = load(RUN / 'CLOSEOUT.json')
committed = load(RUN / 'CLOSEOUT_COMMITTED.json')
need(committed['closeout_sha256'] == sha(RUN / 'CLOSEOUT.json'), 'closeout hash')
plan = load(HERE / 'PLAN.json')
reconstruction = load(RUN / 'V4_RECONSTRUCTION.json')
closed = load(EXTERNAL_LOG_ROOT / 'CLOSED.json')
initial = load(EXTERNAL_LOG_ROOT / 'INITIAL.json')
finished = load(DEST / 'launcher/LAUNCHER_FINISHED.json')
external_manifest = load(DEST / 'launcher/EXTERNAL_MANIFEST.json')
for row in external_manifest['files']:
    p = EXTERNAL_LOG_ROOT / row['name']
    need(p.stat().st_size == row['bytes'] and sha(p) == row['sha256'], 'external original changed')
    need(sha(DEST / 'launcher' / row['name']) == row['sha256'], 'external sealed copy changed')
need(closed['readers_completed'] == 2 and closed['error'] is None, 'log capture not certified')
slot = plan['slots'][0]
folder = RUN / slot['id']
present = sorted(p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file())
need(present == ['WATCH_1.jsonl'], 'unexpected census attempt evidence')
need(len(close['records']) == 1 and close['records'][0]['status'] == 'FAILED_OR_INVALID', 'one failed registration')
need(len(close['unstarted']) == 68 and close['extra_control_worker_processes'] == 0, 'unstarted/control accounting')
need(all(x['status'] == 'MISSING' and x['relation'] is None for x in reconstruction['cross_representation']), 'no invented comparisons')
need(all(x['status'] == 'MISSING' and x['relation'] is None for x in reconstruction['independent_repeats']), 'no invented repeats')
watch = [json.loads(s) for s in (folder/'WATCH_1.jsonl').read_text().splitlines() if s]
groups = [dict(group='census',planned=1,admitted=0,failed_registration=1,unattempted_registration=0,native_started=0,graph_calls=0)]
for name, count in [('A',8),('B',10),('C',10),('D',40)]:
    need(len([s for s in plan['slots'] if s.get('group') == name]) == count, 'group plan')
    groups.append(dict(group=name,planned=count,admitted=0,failed_registration=0,unattempted_registration=count,native_started=0,graph_calls=0))
summary = dict(run_id=f0['run_id'], reviewed_commit='4ea4d0a6777f330ca4be5eb74875dc1ba23f3af1', F0_sha256=sha(HERE/'F0.json'),
    status='HOLD_STOPPED_INCOMPLETE_NO_RETRY', error=close['error'],groups=groups,
    registration_attempts=1,experimental_hosts_started=0,experimental_hosts_unstarted=69,graph_calls=0,
    experimental_monitor_processes=0,experimental_audit_processes=0,numerical_controller_PID=closed['controller_pid'],
    PowerShell_launcher_PID=initial['launcher_pid'],post_controller_CPU_log_audit_PID=finished['CPU_audit_pid'],
    controller_exit_code=closed['controller_exit_code'],launcher_exit_code=1,
    controller_engineering_seconds=close['whole_controller_engineering_seconds'],
    controller_through_closeout_seconds=committed['whole_controller_engineering_seconds_through_closeout'],
    whole_launcher_through_log_audit_ns=finished['engineering_through_log_audit_ns'],
    capture_through_close_ns=closed['engineering_ns'],post_controller_CPU_log_audit_seconds=finished['post_close_CPU_audit_seconds'],
    external_tool_command_wall_seconds=6.3500285,external_tool_scope='Command runner wall, separate from frozen script-entry-to-audit scope',
    native_lifetime_seconds=None,native_post_exit_audit_seconds=None,
    runtime_resource_samples=0,runtime_directory_samples=0,runtime_monitoring_qualification='ABSENT_NO_NATIVE_PROCESS',
    OUT_prelaunch_watcher_pulses=len(watch),OUT_prelaunch_watcher_max_read_ns=max(x['end_ns']-x['begin_ns'] for x in watch),
    OUT_prelaunch_watcher_max_effective_interval_ns=max(x['end_ns']-x['previous_begin_ns'] for x in watch),
    HERE_prelaunch_watcher_completed_pulses=0,strict_max_gap_ns=1000000000,
    terminal_notification_action=None,terminal_notification_writer=None,terminal_notification_event_timestamp=None,
    q1_available=0,q1_missing=8,independent_repeats_available=0,independent_repeats_missing=34,
    mode_comparisons_available=0,mode_comparisons_missing=124,v3_descriptive_anchors_available=0,v3_descriptive_anchors_missing=10,
    q4_bitwise_relationship='UNKNOWN_ALL40_UNSTARTED',MQ_first_divergence='UNKNOWN_NO_NEW_OUTPUT',FP64_errors=None,
    PQ_actual_additional_copy_upload_storage=None,device_alignment=None,actual_support=None,actual_bindings=None,
    nonfinite_output_count=None,scope='Missing is not zero/PASS. No v3 result fills a v5 sample. No new numerical counterexample or accuracy conclusion.',
    external_logs=dict(stdout_bytes=closed['stdout_bytes'],stderr_bytes=closed['stderr_bytes'],stdout_pipe_capacity=closed['stdout_pipe_capacity'],stderr_pipe_capacity=closed['stderr_pipe_capacity'],readers_completed=closed['readers_completed'],error=closed['error'],external_actual_bytes=sum(p.stat().st_size for p in EXTERNAL_LOG_ROOT.iterdir()),reserved_with_export_bytes=33554432),
    failed_coordinates=close['records'],unattempted_coordinates=close['unstarted'],all_native_unstarted_coordinates=plan['slots'],
    retries=0,warmups=0,extra_GPU_probes=0,model_requests=0,S2_S3='NOT_ADMITTED')
save(DEST/'SUMMARY.json', summary)
save(DEST/'INDEPENDENT_RECONSTRUCTION.json',reconstruction)
save(DEST/'SOURCE_BINDINGS_CHECK.json',dict(F0_sha256=sha(HERE/'F0.json'),bound_files=len(f0['bound_files']),old_v2_raw_files=len(f0['old_raw_files']),historical_raw=historical,
    immutable_history_verified=True,only_new_results_added=True,native_host_not_spawned=True,slot_file_set=present,
    proof='Lease(job) precedes STATE/SPAWN and native Popen in frozen supervisor; Lease failed; no STATE, REQUEST, JOB, lifecycle, worker or vector file exists',
    graph_calls=0,new_GPU_queries=0,modules_before=before,modules_after=modules()))
save(DEST/'LAUNCH_CONTEXT.json',dict(reviewed_commit=summary['reviewed_commit'],run_id=f0['run_id'],
    entry="& 'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe' -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File 'C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/host/supervised_numerical_v5/launch.ps1' -AuthorApprovedF0Sha ff596ea94e80a80d004bdb6c9236d0494687a597149baa0c03a77f75e507db44",
    invocations=1,stdout_stderr_redirection='No outer file redirection; frozen owned external capture only',exit_code=1,command_runner_wall_seconds=6.3500285,
    prelaunch_source_writes=['results/AUTHOR_CONFIRMATION.json','results/PRELAUNCH_IDENTITY.json'],
    prelaunch_writes_completed_before_frozen_launcher=True,controller_running_delivery_writes=[],
    receipt_time_policy='Recorded actual UTC when this authorization was handled, not an invented earlier transport timestamp',
    conclusion='External log path contract was respected and capture certified. Sealed source/results notification still rejected Lease. Exact triggering action, writer, operation time and cause remain unrecorded/unknown. No unique attribution or repair performed.'))

entries=[]
roots=[('run',RUN),('external',EXTERNAL_LOG_ROOT)]
for namespace, root in roots:
    for p in sorted(root.rglob('*')):
        if p.is_file():entries.append((namespace+'/'+p.relative_to(root).as_posix(),p,'POST_STOP_CPU_RECONSTRUCTION' if p.name=='V4_RECONSTRUCTION.json' else 'ACTUAL_EXECUTION_EVIDENCE'))
for name in ['AUTHOR_CONFIRMATION.json','PRELAUNCH_IDENTITY.json']:
    entries.append(('authorization/'+name,DEST/name,'PRELAUNCH_CPU_AUTHORIZATION_AND_IDENTITY'))
for name in ['EXTERNAL_MANIFEST.json','EXTERNAL_LOGS.zip','LAUNCHER_FINISHED.json']:
    entries.append(('post_controller/'+name,DEST/'launcher'/name,'POST_CONTROLLER_CPU_LOG_CERTIFICATION'))
manifest=[]
archive=DEST/'RAW_EVIDENCE.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for name,p,role in entries:
        manifest.append(dict(path=name,bytes=p.stat().st_size,sha256=sha(p),original_path=str(p),role=role))
        z.write(p,name)
with zipfile.ZipFile(archive) as z:
    need(set(z.namelist())=={x['path'] for x in manifest},'complete archive member set')
    for row in manifest:
        data=z.read(row['path']);need(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'archive restoration hash')
save(DEST/'RAW_MANIFEST.json',dict(files=manifest,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,uncompressed_bytes=sum(x['bytes'] for x in manifest),all_members_readback_verified=True))
elapsed=(time.monotonic_ns()-begin)/1e9
save(DEST/'CPU_DELIVERY.json',dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),CPU_wall_seconds=elapsed,
    frozen_independent_reconstruction_seconds=reconstruction['CPU_wall_seconds'],post_stop_only=True,experimental_hosts_started=0,graphs=0,device_queries=0,
    evidence_members=len(manifest),modules_before=before,modules_after=modules()))
usage=full_usage(dict(storage_roots=[str(HERE),str(OUT)],run_root=str(RUN),external_log_reserved_bytes=33554432))
delivery_reserve=1024**2
need(usage['output_bytes']+usage['archive_reserve_bytes']+delivery_reserve<=1024**3,'publication budget')
save(DEST/'PUBLICATION_BUDGET.json',dict(**usage,external_actual_bytes=summary['external_logs']['external_actual_bytes'],
    external_and_export_reserved_bytes=33554432,remaining_small_delivery_reserve_bytes=delivery_reserve,
    total_with_reserves=usage['output_bytes']+usage['archive_reserve_bytes']+delivery_reserve,limit_bytes=1024**3,
    accounting='Full new HERE+OUT actual, fixed32MiB external/export reserve, full raw-run export reserve,1MiB remaining delivery reserve; all preparation/test/build failures retained; no v4 balance reused'))
print(json.dumps(dict(status=summary['status'],groups=groups,experimental_hosts=0,graphs=0,workers=0,archive_members=len(manifest),archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),CPU_delivery_seconds=elapsed,publication_usage=load(DEST/'PUBLICATION_BUDGET.json')),ensure_ascii=False))
