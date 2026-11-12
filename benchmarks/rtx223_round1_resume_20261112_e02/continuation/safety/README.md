# Windows runner: tested OS containment, native admission still blocked

The adapter imports no CUDA library and loads no model. It has not run an
actual GPU worker. `CURRENT_NATIVE_GATE` is fixed to
`BLOCKED_ORIGINAL_THREADS_UNVERIFIED`; neither a JSON boolean nor five
self-created receipts can release it. Any future native release needs a new
reviewed source identity plus independently verified thread/device/source,
protocol and **prelaunch counted** resource evidence. The artifact-inspection
template below the gate is not currently a trusted release authority.

The following mechanisms ran on Windows using only unique `CPU-TEST-...`
identities and own dummy Python processes. They did not acquire the actual
RTX UUID's mutex or canonical GPU lock.

- Global named mutex plus exclusive `CreateFileW(CREATE_NEW, share=0,
  DELETE_ON_CLOSE)` lock. A process crash closes handles and releases its own
  marker. An unknown pre-existing marker or any legacy lock is refused and
  never deleted or overwritten. Legacy paths are checked again while the own
  worker runs; appearance stops only the own worker.
- An own child starts suspended, is assigned to a non-inherited Windows Job
  object with `KILL_ON_JOB_CLOSE`, and only then resumes. Cleanup contains its
  descendants. A failure before Job assignment explicitly kills the own new
  suspended child. No API accepts a foreign PID to terminate.
- One persistent family window uses UTC and Windows uptime deadlines. Reopen
  does not reset the deadline. Clock/boot discontinuity refuses continuation.
  Worker exit is checked against a fresh deadline before declaring success.
- Durable SQLite reservations precede execution. Failures and reservations
  remain charged, all further work stops after failure, and there are no
  automatic retries or refunds. Observed overrun counts survive refusal;
  incomplete counters remain `null` with reservation charged, rather than
  becoming fabricated zeroes. A COMPLETE record cannot hide unknown counts.
- Bound heartbeat/final snapshots require epoch, attempt, PID and process
  creation FILETIME, nondecreasing sequence/counts and finite size. Counter
  reads use READ/WRITE/DELETE sharing so the own worker can atomically replace
  snapshots. Timeout, missing heartbeat and controller death contain only the
  own Job. Logs, receipts and counter lower bounds remain.

`os-checks-v2/RECEIPT.json` records **18 targeted tests passing in ordinary
Python and `-O`**. Tests cover contention, unknown/legacy markers, success,
crash, late marker, timeout, child descendants, controller death,
pre-assignment failure, deadline-observation race, parent budget binding and
counter/refusal behavior. `raw/` preserves own fixture ledgers, heartbeats,
logs and OS observations. A null OpenProcess result proves disappearance only
with WinError87; access denial is not accepted as termination evidence.

The overrun fixture writes a synthetic `kernel_launches=1` to its CPU counter
file. It executes **zero GPU kernels**. Fixture ledgers are not the real
resource ledger and must never be summed into native request/launch totals.

`BUDGET_BINDING.json` names the one canonical real family ledger and binds the
unchanged original plan and zero-usage parent snapshot. Future epochs must
reuse this canonical family state; they do not obtain a fresh budget. Its
window has not started and it has no native attempts. The original limits
remain 256 requests, 1,000,000 target/draft rows, 10,800 seconds, 4,096 total
kernel launches and 2 GiB capture, including warmup and failure margins.

Limits: a new named mutex does not make old/uncooperative clients participate
in it. The current host's original thread/process clearance is unresolved.
Source-level launch counting is not implemented by this host adapter; a
worker must enforce counted limits before each model/kernel launch and emit
bound receipts before a native release can be reviewed. The global cutoff is
observed at finite polling/OS scheduling resolution; any measured overshoot
is retained and charged as an overrun, not forgiven. These CPU OS results are
not GPU qualification, full-host exclusivity or service-performance evidence.

Reproduce in a **new** output directory (no model or GPU calls):

```powershell
& 'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe' -B continuation/safety/run_os_checks.py os-checks-new
```

Earlier host-test debugging failures are summarized honestly in
`DEBUG_FAILURE_HISTORY.json`. They are not native failures. Old e01 source,
build failures and ledgers were not edited.
