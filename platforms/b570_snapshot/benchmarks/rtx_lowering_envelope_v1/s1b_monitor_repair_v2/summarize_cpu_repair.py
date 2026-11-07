"""CPU delivery summary from actual receipts; does not alter frozen inputs or tests."""
import datetime,json,subprocess
from pathlib import Path
from common import V,load,save,sha,pin

def main():
    f=load(V/'F0.json');remote=load(V/'REMOTE_ARCHIVE_VERIFIED.json');fresh=load(V/'FRESH_CPU_AUDIT.json');m=load(V/'delivery/cpu-qpc/ARCHIVE_MANIFEST.json')
    assert remote['status']=='VERIFIED' and fresh['status']=='PASS'
    assert fresh['F0_sha256']==sha(V/'F0.json') and fresh['test_count']==16 and fresh['prior_CPU_test_count']==186
    assert not Path(f['execution_root']).exists() and not (V/'execution_ledger').exists()
    rows=[]
    for s in load(V/'PLAN.json')['clean_slots']:
        if s['block']==0:rows.append({k:s[k] for k in ['id','descriptor','family','phase','q','layer','layout']}|dict(status='NOT_STARTED_NOT_AUTHORIZED',GPU_graph_calls=0))
    assert len(rows)==72
    ledger=[load(p)|dict(path=str(p)) for p in (V/'ledger').glob('*-EXIT.json')]
    publication=[];raw=[]
    for d in ['publication','publication_final','publication_qpc']:
        for p in (V/'cpu_raw'/d).rglob('*'):
            if not p.is_file():continue
            if p.name.endswith('ENDED.json'):publication.append(load(p)|dict(path=str(p)))
            # Lossless small transport receipts/streams; large raw downloads are
            # separately authenticated Git objects, recorded by exact hash here.
            if p.suffix=='.json' or p.suffix in ['.stdout','.stderr']:
                b=p.read_bytes();raw.append(dict(path=str(p.relative_to(V)),bytes=len(b),sha256=sha(p),UTF8=b.decode('utf-8',errors='replace') if len(b)<65536 else None,large_stream_already_authenticated=len(b)>=65536))
    save(V/'CPU_DELIVERY_ACCOUNTING.json',dict(run_id=f['run_id'],execution_id=f['execution_id'],CPU_jobs=ledger,publication_actions=publication,small_transport_receipts_and_streams=raw,supervised_CPU_command_seconds=sum(r['seconds'] for r in ledger)+sum(r['seconds'] for r in publication),supervised_conservative_owned_seconds=sum(r['charged_child_seconds_upper_bound'] for r in ledger)+sum(r['conservative_owned_seconds'] for r in publication),scope='Recorded supervised CPU jobs/publication actions only;tool file editing and agent reasoning not fabricated as measured process time. Final closure push has its own subsequent immutable receipt.',GPU_queries=0,CUDA_loads=0,graph_calls=0))
    result=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),run_id=f['run_id'],execution_id=f['execution_id'],previous_admission_stop=dict(GPU_execution=0,graph_calls=0,unstarted=72),current_CPU_repair=dict(GPU_queries=0,CUDA_loads=0,graph_calls=0,warmups=0,profiling=0,model_requests=0),Block0_coordinates=rows,scientific_GPU_results_created=False,CPU_regressions=186,fresh_independent_checks=16,total_CPU_checks_passed=202,failed_final_CPU_checks=0,actual_clock=f['monitor_contract']['actual_clock'],max_allowed_monitor_interval_ns=1000000000,deterministic_boundaries={'999999999':'PASS','1000000000':'PASS','1000000001':'FAIL'},positive_real_process_summary={k:fresh[k] for k in ['actual_sample_max_interval_ns','actual_positive_interval_count','missing_sample_count','watchdog_decision','identity_decision','exact_Census_byte_decision']},native_EXE_unchanged=pin(V/'s1b_clean.exe'),numerical_DLLs_unchanged=21,all4941_historical_files_unchanged=True,actual72_CPU_graphs_and_serializer_unchanged=True,execution_bound_Census=f['execution_bound_census'],F0_sha256=sha(V/'F0.json'),archive_manifest=pin(V/'delivery/cpu-qpc/ARCHIVE_MANIFEST.json'),archive_sha256=m['archive_sha256'],remote_data_commit=remote['commit'],remote_authenticated=True,fresh_root=remote['fresh_root'],archive_members=m['member_count'],archive_member_bytes=m['member_bytes'],archive_bytes=m['archive_bytes'],prepared_GPU_scope=dict(clean_hosts=72,readiness_queries=72,CPU_watchdogs=144,maximum_conhost_helpers=288,controllers=1,total_controlled_starts=577,warmups=72,measurements=576,graph_calls=648,effective_wall_seconds=360,conservative_owned_seconds=1800),next_admission_eight_CPU_conditions='ALL_PASS',GPU_execution_authorization='NOT_GRANTED',Block1_2_trace_actor_decoder='NO_GO',preserved_failures=['r1 canonical identity/monitor admission stop;0GPU','old LF/native CRLF hash difference and 404/ignore records','CPU relative command path invocation failure','CPU Job active1/Git child quota failure','GitHub443 connection failure;bounded CPU transport recovery only','superseded coarse GetTickCount64 CPU candidates and inaccurate QPC labels;raw proofs retained','all intentional monitor/crash/missing/sample/identity/archive negative fixtures'],unique_future_entry=str(V/'run_s1b.py')+' --stage clean0 --approval AUTHOR_EXACT_APPROVAL',status='CPU_REPAIR_AUDIT_COMPLETE_WAITING_INDEPENDENT_BLOCK0_AUTHORIZATION')
    save(V/'RESULT_CPU_REPAIR.json',result)
    text=f'''# PR118 CPU repair/audit complete — GPU not authorized

A. Previous admission stop remains 0 GPU execution,0 graph calls,72 unstarted.
No previous execution_id is resumed. All4941 historical files compare exactly.

B. Canonical run_id `{f['run_id']}`; independent execution_id `{f['execution_id']}`.
F0/entry/authorization/STOP/slot/manifest/results separate the two identities.
Authorization binds exact bytes consumed by the execution entry. Native EXE,
all21 numerical DLLs,input,graph,serializer,Census and comparisons are unchanged.
Actual72 CPU graph records are identical; no new GPU qualification is inferred.

Frozen Python's time.monotonic_ns actually uses GetTickCount64. Earlier CPU
candidates incorrectly labelled it QPC; these candidates,archives and receipts
are preserved under preparation_candidates and prior commits. The CURRENT
implementation uses verified time.perf_counter_ns / QueryPerformanceCounter,
monotonic,not adjustable,100ns resolution. This is not a claim of1ns resolution.

Actual adjacent intervals and startup/tail coverage are checked independently.
The sampler directly completes memory/Job/controller/disk/log/process checks
before timestamping and fsyncing its chained sample. An independent process
detects stalls/crashes/missing samples and terminates the owned Job. Watchdog
death fails closed. EOF/exit never supplies a fabricated sample. Native running,
independent exit observation and post-exit audit remain separately accounted.

186 final CPU regressions plus16 fresh independent checks passed:202/202.
999999999ns PASS;1000000000ns PASS;1000000001ns FAIL.
Qualified real CPU processes: actual max adjacent interval83347600ns,
15 adjacent intervals,0 missing samples. Intentional failures are retained and
rejected. The1second contract is a measured acceptance condition; Python/Windows
is not hard realtime, and an overdue scheduled observation is rejected.

F0 SHA256: `{result['F0_sha256']}`

Execution-bound native CRLF Census SHA256:
`{f['execution_bound_census']['sha256']}`

Decision SHA256: `{f['execution_bound_decision']['sha256']}`

CPU archive manifest SHA256: `{result['archive_manifest']['sha256']}`

CPU archive SHA256: `{m['archive_sha256']}`

Actual authenticated remote data commit: `{remote['commit']}`.
2210 members /20815264 uncompressed bytes /4533206 archive bytes were downloaded
from GitHub,restored into a fresh root,enumerated/hashed and replayed in a new
interpreter. Exact source,F0,Census,module-byte and test receipts passed.
See REMOTE_ARCHIVE_VERIFIED.json,FRESH_CPU_AUDIT.json,CPU_DELIVERY_ACCOUNTING.json.
CPU command/transport failures are retained; no scientific retry occurred.

C. All eight CPU prerequisites for requesting a NEW Block0 authorization pass.
No Block0 approval is created. The new GPU root and execution ledger are absent.
Future scope stays72 hosts,PQ/QB/QH_C each24,72 warmups,576 measurements,
648 graph calls. Added CPU supervision is explicit:1 controller,72 queries,
72 natives,144 CPU watchdogs,up to288 helpers,total577 starts,max5 concurrent.
Original owned1800s ceiling gives a conservative effective360s wall ceiling;
the original600s wall maximum and storage cap4GiB are not enlarged.

Only future entry,frozen Python -B:
`{V/'run_s1b.py'} --stage clean0 --approval <new author approval>`

Approval must bind run_id,execution_id,F0,exact CRLF Census and Decision hashes.
No Census rerun;no Block1/2,trace/profile,actor,decoder,model,S2/S3 or hardware.
No new GPU query,CUDA load,graph call,warmup or scientific numerical data occurred.

CPU repair/audit complete; waiting for independent Block 0 GPU authorization.
'''
    (V/'RESULT_CPU_REPAIR.md').write_text(text,encoding='utf-8')
    print('202/202 CPU checks;exact remote2210members;all GPU scope remains unstarted')
if __name__=='__main__':main()
