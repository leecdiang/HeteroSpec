# PR119: three P2 repairs, separate from the historical run

This is a NEW implementation candidate. Nothing under the original UUID
`c475bcaf-b7ca-4830-82f1-9b52154891b1` is replaced. Its 10,800-second run,
1,083 cases, 1,805 actor identities and archives remain historical evidence under
the original protocol, with the three subsequently discovered P2 limitations.
This repair does not certify that run under the new guards or authorize GPU,
model, scientific or paper work. The old eight CPU cases have not run.

## Runtime contract

Deploy the runtime files into `src/rev2/` in a NEW UUID root directly beneath
`C:/hs/b570-capability-v1`. This staging path is a schema name, not a reference
to the historical directory. Never reuse an old root. Freeze all runtime files,
including `guards.py`, the config and protocol/review inputs before measurement.
The existing approved Python path and all existing actor/resource/cleanup
criteria remain. Use formal exec_command + write_stdin, not the restricted
shared Node service. Capture the exact tool requests and complete responses.

1. Watchdog writes identity-bound progress to its journal, then atomically to
   WATCHDOG_PROGRESS.json before resuming its child and after each successful
   monitor. Supervisor checks retained watchdog identity/liveness and progress
   age on every tick and BEFORE case directory creation or actor launch. More
   than 5 seconds, future timestamps, regressing sequence/time, wrong PID or OS
   creation identity fail closed. Offline audit binds each sampled observation
   to the watchdog's raw progress journal. RSS readability is not liveness.
2. Register the exact SHA256 of CAPABILITY_FREEZE.json in the prospective tool
   intent and pass `--freeze-sha256 DIGEST` to the watchdog. It passes the same
   digest to the supervisor. Both pin the initial inventory in memory and
   reject manifest replacement, even if new source hashes match a replacement
   manifest. The verifier reconciles the file with both runtime pins, the
   original intent and actual OS command. Do not regenerate a measured freeze.
3. Development registrations are unique by run, revisions 0..2, at most 20
   reserved case attempts. D0 must fit 5,400 seconds from first preparation to
   freeze; the watchdog also caps development deadlines at that boundary.
   The watchdog reserves 1,800 seconds for delivery inside the 21,600-second
   whole-task limit. Audit reconstructs elapsed time from original acquisition,
   UTC launch observation, monotonic watchdog interval and registrations.
   Negative/non-finite/missing/inconsistent values reject; they are not zero.

## Delivery frontier, not a self-attestation of unlimited future work

The worker archive audit with manifest and formal tool binding returns
`CAPABILITY_ENDURANCE_PENDING_DELIVERY`. It MUST NOT be reported as PASS.
After remote download, member/hash verification, unmodified restored verifier
recalculation and tool binding verification, create an immutable EXTERNAL tail
receipt (outside the worker root). It contains:

- `observed_utc`: actual UTC observation after those operations;
- `task_elapsed_seconds`: elapsed from ACQUISITION.first_preparation_utc;
- `restoration_verified: true`, `tool_exit_verified: true` only after those checks;
- `manifest_sha256`, `tool_binding_sha256`, `freeze_sha256` matching the worker.

Record its SHA256 separately in the delivery record, publish both and invoke
verify.py with `--completion-receipt ABSOLUTE_PATH --completion-sha256 DIGEST`
in addition to root/run/manifest/tool-receipt. It rejects a whole-task frontier
beyond six hours, delivery beyond 30 minutes, and inconsistent origin or early
completion. PASS is explicitly through the returned `budget.frontier_utc`.
The final audit/publication after that frontier is reported as tail overhead;
if completion of required task delivery exceeds six hours, final task status is
BUDGET_EXCEEDED even if the earlier finite-frontier audit passed. Never claim a
whole-process total ledger or the watchdog's own OS exit from these receipts.

## Validation

`python -B -m unittest discover -s runtime -p test_repairs.py -v` runs portable
counterexamples and actual supervisor tick/case admission code with fake OS
observations. It does not exercise Windows Jobs or certify native behavior.
An independent scoped code review must pass before publishing an eight-case
integration plan. Native acceptance must then prove stale watchdog cleanup,
freeze replacement rejection, budget refusal and healthy progress on B570.
No second three-hour run is required just to demonstrate these repairs.
