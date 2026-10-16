# PR118 CPU repair/audit complete — GPU not authorized

A. Previous admission stop remains 0 GPU execution,0 graph calls,72 unstarted.
No previous execution_id is resumed. All4941 historical files compare exactly.

B. Canonical run_id `pr116-s1b-cost-v1`; independent execution_id `pr116-s1b-exact-r2`.
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

F0 SHA256: `f2d6965646e1f53c5d8a8b974f0277efc2903ed022689374af3f178fbad8e587`

Execution-bound native CRLF Census SHA256:
`d8c79ed1b4fc748ec8ce22a201137ef6fc201de79052fa7c6c4f7711806e8256`

Decision SHA256: `b5ed03a307182a87db18ed588bc852239e52860799034da897b48ce0f391373a`

CPU archive manifest SHA256: `3b84a2d8f000e2a8be7aceb46695d562696cb6912c8b875b90913e4b1db11c56`

CPU archive SHA256: `3c7fc674b5644a98f99d7cd18cbe6d774d82cc057d97fcf6b24bbcb031f7909c`

Actual authenticated remote data commit: `6d4a3232dccc0f6e8e6b355675a8a090031f684a`.
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
`D:\hs116-s1b\benchmarks\rtx_lowering_envelope_v1\s1b_monitor_repair_v2\run_s1b.py --stage clean0 --approval <new author approval>`

Approval must bind run_id,execution_id,F0,exact CRLF Census and Decision hashes.
No Census rerun;no Block1/2,trace/profile,actor,decoder,model,S2/S3 or hardware.
No new GPU query,CUDA load,graph call,warmup or scientific numerical data occurred.

CPU repair/audit complete; waiting for independent Block 0 GPU authorization.
