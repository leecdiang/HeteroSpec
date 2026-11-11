"""CPU-only evidence summary and independently derived v5 ceilings."""
import pathlib
from legacy import HERE,ROOT,OUT,load,save,sha,need,modules,EXTERNAL_LOG_ROOT,EXTERNAL_RESERVED_BYTES
from workers import rows
from registration import plan,serialize

def main():
    need(not (HERE/'BUDGET.json').exists(),'exclusive new budget')
    receipts=sorted((HERE/'preparation').glob('CPU_TESTS_*.json'));tests=load(receipts[-1]);need(tests['success'],'latest actual suite must pass')
    evidence=pathlib.Path(tests['evidence_root']);normal=evidence/'LAUNCHER/normal'
    normal_closed=load(normal/'external_logs/CLOSED.json');normal_initial=load(normal/'external_logs/INITIAL.json')
    need(normal_closed['status']=='CLOSED_SUCCESS','end-to-end normal case')
    p=plan();old=load(ROOT/'host/supervised_numerical_v4/PLAN.json')
    need(len(p['slots'])==69,'69 slots')
    for a,b in zip(p['slots'],old['slots']):
        for k in ('kind','input_id','mode','repeat','q','group'):need(a.get(k)==b.get(k),'v4 scientific coordinate changed')
    output=[]
    for row in rows(evidence/'SERIALIZER/DESCRIPTORS.jsonl')[1:-1]:
        if row['request']['kind']!='graph':continue
        g=row['cell']['geometry'];stages=4*g['q']*g['h']*(2*g['n']+256);payload=sum(x['bytes'] for x in row['payload_sizes'])
        output.append(dict(slot=row['slot_id'],input_pre_post_bytes=2*payload,raw_stage_bytes=stages,normalized_stage_bytes=stages,exact_bytes=2*payload+2*stages))
    exact=sum(x['exact_bytes'] for x in output);need(exact==60149008,'unchanged full numerical payload')
    actual=sum(x.stat().st_size for root in (HERE,OUT) for x in root.rglob('*') if x.is_file())
    evidence_allowance=192*1024**2;packaging=64*1024**2;active=2*32*1024**2;export=exact+evidence_allowance+69*256*1024+1024**2
    total=actual+exact+evidence_allowance+packaging+active+export+EXTERNAL_RESERVED_BYTES
    need(total<=1024**3,'HOLD: independently derived1GiB insufficient')
    tree=ROOT/'host_outputs/supervised_numerical_v4/SCALING_TREE';tree_files=list(p for p in tree.rglob('*') if p.is_file())
    need(len(tree_files)==8000 and sum(p.stat().st_size for p in tree_files)==262144000,'old stress fixture reference')
    late=load(evidence/'LAUNCHER/late_tree/LATE_SCALE.json');limit=load(evidence/'LAUNCHER/log_limit/external_logs/CLOSED.json')
    lifecycles=[load(p) for p in (OUT/'CPU_TESTS').rglob('LIFECYCLE.json')];ps=[load(p) for p in (OUT/'CPU_TESTS').glob('attempt_*/LAUNCHER/*/POWERSHELL_PROCESS.json')]
    controls=[load(p) for p in (OUT/'CPU_TESTS').glob('attempt_*/LAUNCHER/*/external_logs/CLOSED.json')]
    audits=[load(p) for p in (OUT/'CPU_TESTS').glob('attempt_*/LAUNCHER/*/protected_source/results/POST_CLOSE_CAPTURE/LAUNCHER_FINISHED.json')]
    save(HERE/'CPU_INTEGRATION_EVIDENCE.json',dict(latest_test_receipt=str(receipts[-1]),methods=tests['methods'],pass_status=tests['success'],normal_closed=normal_closed,
        log_limit_closed=limit,late_tree=late,watcher_sha256=sha(HERE/'storage.py'),unchanged_v4_watcher_sha256=sha(ROOT/'host/supervised_numerical_v4/storage.py'),
        stdout_real_bytes=(normal/'external_logs/CONTROLLER.stdout.log').stat().st_size,stderr_real_bytes=(normal/'external_logs/CONTROLLER.stderr.log').stat().st_size,
        external_log_root_production=str(EXTERNAL_LOG_ROOT),owner_sid=normal_initial['owner_sid'],threshold_ns=1000000000,whole_launcher_normal=load(normal/'protected_source/results/POST_CLOSE_CAPTURE/LAUNCHER_FINISHED.json'),
        all_test_attempts=[dict(path=str(r),success=load(r)['success'],methods=load(r)['methods'],wall_seconds=load(r)['wall_seconds']) for r in receipts],
        fault_scope='Loss is injected at actual production notification parser using an empty completion, not claimed as a real OS queue overflow; other paths use actual CPU processes and actual PowerShell redirection'))
    save(HERE/'BUDGET.json',dict(run_id=p['run_id'],experimental_hosts_max=69,numerical_graph_calls_max=68,census_hosts=1,census_graph_descriptions=80,
        groups=dict(A=8,B=10,C=10,D=40),scientific_panel_identical_to_v4=True,experimental_monitor_auditor_processes_max=138,controller_processes=1,
        separate_PowerShell_launcher_processes=1,separate_post_controller_CPU_log_audit_processes=1,launcher_pipe_reader_threads=2,storage_watch_threads_per_active_slot=2,
        OS_job_membership_includes_observed_system_cleanup_processes='Recorded by PID/name when still visible; not described as extra experimental hosts or a whole-machine count',
        engineering_seconds=900,complete_slot_seconds=180,engineering_scope='PowerShell script entry through controller, owned-job cleanup, pipe drain and post-controller CPU log-audit receipt; controller also enforces its own900s; no graph latency claim',
        engineering_derivation='69*10s complete-slot planning +210s launcher/preflight/closeout contingency =900s; no unused v4 balance reused',
        artifact_limit_bytes=1024**3,prepared_actual_before_capsules=actual,exact_input_and_four_stage_output_bytes=exact,planned_JSON_monitor_audit_metadata_allowance=evidence_allowance,
        preparation_packaging_reserve_bytes=packaging,active_and_active_export_reservation_bytes=active,raw_export_reserve_bytes=export,
        external_actual_max_bytes=16*1024**2,external_plus_export_reserved_bytes=EXTERNAL_RESERVED_BYTES,external_source_post_close_copy='Charged again in source actual/evidence allowance; no free logs',
        conservative_total_planning_allowance_bytes=total,exact_per_slot_payloads=output,
        historical_stress_fixture=dict(path=str(tree),files=8000,bytes=262144000,read_only_reference=True,new_copy_bytes=0),
        historical_evidence='v2/v3/v4 immutable file/hash references; no old result is a v5 repeat or missing numerical sample',
        CPU_preparation_attempts=len(receipts),CPU_suite_seconds=sum(load(r)['wall_seconds'] for r in receipts),actual_CPU_test_hosts=sum(l['pid'] is not None for l in lifecycles),
        actual_CPU_test_monitor_auditor_processes=sum(len(l['control_processes']) for l in lifecycles),actual_PowerShell_test_invocations=len(ps),actual_gated_CPU_controller_PIDs=sum(c['controller_pid'] is not None for c in controls),
        actual_post_controller_CPU_log_audit_receipts=len(audits),actual_CPU_metadata_invocations=len(list((OUT/'CPU_TESTS').glob('attempt_*/SERIALIZER/PROCESS.json'))),
        builds=[load(r) for r in sorted((HERE/'preparation').glob('BUILD_*.json'))],launcher_builds=[load(r) for r in sorted((HERE/'preparation').glob('LAUNCHER_BUILD_*.json'))],
        modules=modules(),GPU_hosts_started=0,device_queries=0,graph_computes=0,model_requests=0,extra_probes=0,warmups=0,retries=0,
        note='Plan allowance is not guaranteed completeness under every failure/slow audit; actual reservations and limits still stop later slots. Temp compilation/build outputs are confined to prepared build paths; runtime loads prebuilt DLL, no compiler.'))
    print(dict(prepared_bytes=actual,planning_total_bytes=total,limit_bytes=1024**3,CPU_methods=tests['methods'],external_reserved=EXTERNAL_RESERVED_BYTES,late_max_directory_read_ns=late['max_read_ns'],GPU_started=0))

if __name__=='__main__':main()
