"""Derive CPU scaling evidence and the NEW v4 storage/engineering budget."""
import hashlib
import math
import pathlib
import statistics
import time
from legacy import HERE,OLD,ROOT,OUT,load,save,sha,need,modules
from storage import inventory,ACTIVE_BYTES,ACTIVE_FILES
from workers import rows
from registration import plan

def main():
    need(not (HERE/'BUDGET.json').exists(),'exclusive budget freeze')
    latest=sorted((HERE/'preparation').glob('CPU_TESTS_*.json'))[-1];tests=load(latest);need(tests['success'],'fresh CPU suite')
    evidence=pathlib.Path(tests['evidence_root']);scaling=load(evidence/'test_late_panel_real_process_concurrent_growth_0/SCALING.json')
    tree=OUT/'SCALING_TREE';growth=[]
    for count in (20,40,80,160):
        dirs=[tree/str(i).zfill(3) for i in range(count)];samples=[]
        for _ in range(3):
            begin=time.monotonic_ns()
            actual=sum(p.stat().st_size for root in dirs for p in root.rglob('*') if p.is_file())
            files=[p for root in dirs for p in root.rglob('*') if p.is_file()];reserve=sum(p.stat().st_size for p in files)+len(files)*1024+1024**2
            samples.append(dict(begin_ns=begin,end_ns=time.monotonic_ns(),output_bytes=actual,archive_reserve_bytes=reserve))
        growth.append(dict(files=count*50,depth=3,bytes=count*50*32768,samples=samples))
    meta=rows(evidence/'SERIALIZER/DESCRIPTORS.jsonl')[1:-1];output=[]
    for row in meta:
        if row['request']['kind']!='graph':continue
        g=row['cell']['geometry'];q,n,h=g['q'],g['n'],g['h']
        stages=4*q*h*(2*n+256);payload=sum(x['bytes'] for x in row['payload_sizes'])
        output.append(dict(slot=row['slot_id'],raw_input_before_after_bytes=2*payload,raw_four_stages_bytes=stages,normalized_four_stages_bytes=stages,exact_vector_and_input_bytes=2*payload+2*stages))
    prepared=sum(p.stat().st_size for root in (HERE,OUT) for p in root.rglob('*') if p.is_file())
    # New allocations, independently selected; no reuse of a v3 remainder.
    raw_known=sum(x['exact_vector_and_input_bytes'] for x in output)
    evidence_allowance=128*1024**2 # raw JSON, interval journals, audits, per-slot receipts, export metadata
    packaging_preparation_reserve=64*1024**2
    export_reserve=raw_known+evidence_allowance+69*ACTIVE_FILES*1024+1024**2
    total=prepared+raw_known+evidence_allowance+packaging_preparation_reserve+export_reserve+2*ACTIVE_BYTES
    need(total<=1024**3,'derived 1GiB ceiling not credible: HOLD')
    times=[load(p) for p in sorted((HERE/'preparation').glob('CPU_TESTS_*.json'))]
    life=[load(p) for p in evidence.rglob('LIFECYCLE.json')];positive=[r for r in life if r['stop'] is None]
    leases=[load(p) for p in evidence.rglob('STORAGE_LEASE.json')]
    cpu_scaling=dict(old_style_two_pass_growth=growth,late_tree=scaling['tree'],late_real_monitor_reads=scaling['bounded_reads'],
        late_lease=scaling['lease'],late_lifecycle_sha256=scaling['process_lifecycle_sha256'],
        exact_threshold_ns=1_000_000_000,interpretation='CPU metadata timings on this filesystem, including cache/OS variance; no worst-case scheduling guarantee; future overruns must STOP')
    save(HERE/'CPU_SCALING.json',cpu_scaling)
    save(HERE/'BUDGET.json',dict(run_id=plan()['run_id'],experimental_hosts_max=69,census_hosts=1,census_graph_descriptions=80,census_graph_computes=0,numerical_hosts=68,graph_calls_max=68,
        panel_groups=dict(A=8,B=10,C=10,D=40),new_CPU_control_workers_max=138,controller_processes=1,storage_watch_threads_per_slot=2,
        controller_engineering_seconds=900,per_complete_slot_seconds=180,
        engineering_derivation='69 * 10s prospective complete-slot allowance +210s admission/full-preflight/closeout contingency =900s. Not an estimate of GPU graph latency. Strict stop at ceiling; unused historical budgets excluded.',
        positive_CPU_complete_slot_seconds_max=max(r['whole_slot_engineering_seconds_before_lifecycle'] for r in positive),
        pre_spawn_snapshot_seconds_max=max((r['preflight_ready_ns']-r['preflight_begin_ns'])/1e9 for r in leases),
        artifact_limit_bytes=1024**3,prepared_bytes_before_capsules=prepared,exact_planned_vector_and_input_bytes=raw_known,
        raw_json_audit_journal_allowance=evidence_allowance,packaging_preparation_reserve=packaging_preparation_reserve,export_reserve_bytes=export_reserve,
        conservative_active_and_export_reservation=2*ACTIVE_BYTES,derived_total_upper_planning_allowance_bytes=total,
        active_slot_bytes_cap=ACTIVE_BYTES,active_slot_file_cap=ACTIVE_FILES,exact_outputs=output,
        CPU_test_methods=tests['methods'],CPU_test_attempts=len(times),CPU_test_seconds=sum(t['wall_seconds'] for t in times),
        supervised_CPU_children=sum(load(p)['pid'] is not None for p in (OUT/'CPU_TESTS').rglob('LIFECYCLE.json')),CPU_control_workers=sum(t['actual_CPU_control_workers'] for t in times),
        process_count_rule='Count actual non-null lifecycle PIDs; pre-spawn storage rejection is not a child process. Earlier attempt02 receipt counted lifecycle rows; preserved and corrected by this explicit recount.',
        CPU_metadata_processes_observed=sum(1 for p in (OUT/'CPU_TESTS').glob('attempt_*/SERIALIZER/PROCESS.json')),
        offline_failed_invocations=[dict(tool_exit_code=1,reported_wall_seconds=1.1698946,reason='CPU analyzer caller supplied vectors directory twice; corrected before successful immutable OFFLINE_REVIEW.json')],
        numerical_DLLs_unchanged=True,new_GPU_hosts=0,new_device_queries=0,new_graph_computes=0,model_requests=0,extra_probes=0,warmups=0,retries=0,
        CPU_modules=modules(),notes='Preparation includes the retained real 262144000-byte scalability tree, build and all CPU evidence. Actual capacity is monitored; reservations are conservative allowances, not promises that every pathological 180s slot fits. A reservation or monitoring miss stops before any next slot.'))
    print(dict(prepared_bytes=prepared,raw_vector_bytes=raw_known,planning_total=total,CPU_methods=tests['methods'],growth=[dict(files=x['files'],ms=[(s['end_ns']-s['begin_ns'])/1e6 for s in x['samples']]) for x in growth]))

if __name__=='__main__':main()
