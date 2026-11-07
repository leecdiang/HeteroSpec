# PR118 CPU identity/monitor repair r2

Canonical `run_id=pr116-s1b-cost-v1`; independent
`execution_id=pr116-s1b-exact-r2`. The stopped r1 is never resumed. No GPU work
is authorized by this preparation. New GPU root remains absent until a separate
author-approved `clean0` launch creates it once.

Authorization binds exact bytes consumed by the execution entry. The unchanged
native CRLF Census is `d8c79ed1b4fc748ec8ce22a201137ef6fc201de79052fa7c6c4f7711806e8256`.
No parsing, reserialization or newline conversion participates in admission.
The native executable stays `073bdc32c6b54866b075d0dc47b5e9a343ec299fa1c87b5cd0937abe32db035b`.
Native arithmetic, graph/serializer, input, comparison rules and all 21 DLLs
are unchanged. Historical Census/module/IAT receipts are checked on CPU;
there is no new Census query or CUDA qualification.

## Actual monitoring contract

`MAX_MONITOR_INTERVAL_NS=1000000000`, inclusive. Both deterministic boundaries
999999999/1000000000 pass; 1000000001 fails. A requested 50ms sleep is not
evidence of compliance. Resource observations carry actual `monotonic_ns`
timestamps and a sequence/token/PID/identity-bound SHA256 chain, flushed to disk.
Each sample checks live target memory, Job memory, controller/disk guard,
stream overflow and process-event errors. FILETIME is only a process identity.

An independent Python OS process reads the journal and checks actual adjacent
intervals and startup/last-sample-to-independent-exit-observation coverage.
No qualified sample for more than one second writes FAIL and terminates the
named child Job, independently of the controller's GIL. Watchdog death is also
fatal to the controller. Host exit/EOF never creates a resource sample.
Native runtime ends at independently observed process exit; subsequent audit,
hashing, archive and cleanup are separate, still charged to the stage budget.
Raw sample/clock/config/PID/exit records are replayed independently.

The report distinguishes `observed_max_interval_ns` (adjacent actual samples)
and `observed_max_coverage_gap_ns` (also startup/tail/missing-sample windows).
Zero intervals means no adjacent pair; it does not assert zero elapsed runtime.
A wholly stalled Windows scheduler cannot be made hard realtime by Python;
an overdue observation is rejected on resumption, never certified as compliant.

## Explicit supervision overhead and unchanged scientific scope

Future Block0 only: 72 clean hosts, 72 readiness queries, 144 **CPU** watchdogs,
at most 288 console helpers, one controller: at most 577 controlled starts,
at most five concurrently (controller + one child Job of four).
The CPU watchdog performs no device query. Scientific counts stay 72 warmups,
576 measurements, 648 graph calls, PQ/QB/QH_C each24. No extra probe/retry.

Original stage ceilings remain wall600s/owned1800s. Charging five simultaneous
processes conservatively gives an effective wall cap360s, with the existing5s
durable stop reserve. This may stop before completing the panel; no completion
is promised. Native/query running limits remain60s/10s. Suspended monitor setup
and post-exit closure are separately bounded and charged, not native runtime.
Job memory allows original target cap plus128MiB for the watchdog; process and
Job limits remain enforced. Each journal <=2MiB; two per coordinate + old1MiB
metadata + <=256KiB stream logs fit the new prospective6MiB metadata ceiling,
inside the unchanged8MiB reservation and unchanged whole-study4GiB cap.

Only future entry: frozen Python `-B run_s1b.py --stage clean0 --approval PATH`.
Approval must explicitly bind canonical run_id, independent execution_id, new
exact F0, native CRLF Census and Decision hashes. No approval is created here.
Block1/2, Census rerun, trace/profile, actor/decoder, S2/S3 and hardware remain
NO-GO. Original 72 trace coordinates remain recorded, not executed.

CPU tests include deterministic boundary and identity cases; real Windows
normal/stall/crash/exit/EOF/slow-audit/watchdog-death processes; exact Census
byte negatives; unchanged72 CPU graph/serializer records; legacy regressions;
independent tamper replay; actual ignored archive staging and fresh restoration.
Intentional negative fixtures and the CPU command-path invocation failure are
retained. Historical stopped runs/raw archives are immutable.

After source/F0 commit, authenticated GitHub bytes must be fetched into a new
fresh root, every declared member enumerated/hashed, and CPU checks repeated
from the restored sources in a new interpreter before VERIFIED is written.
This constitutes CPU engineering evidence only, not new scientific GPU data.

Clock documentation: [Python monotonic clock](https://docs.python.org/3/library/time.html#time.monotonic_ns).
