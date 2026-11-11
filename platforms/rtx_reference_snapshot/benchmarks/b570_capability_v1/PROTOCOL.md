# B570 CPU capability validation v1 — 2026-10-18

## Authority and scope

This is a newly authorized capability-development and measurement lane inside PR119.
It supersedes the old stop-on-any-adaptation rule ONLY for this new lane. It does
not amend or qualify b570_supervision_fix_v2, its source freeze, budgets, eight
cases or historical results. Do not invoke startCold or confirm.py. Do not load
Koffi, query/initialize GPU, read/request models, run scientific code or change the
paper. Keep PR115/117 and all historical PR119 evidence unchanged; keep PR119 Draft.

The delivered artifact is this protocol, acceptance specification and dispatch
prompt, NOT an already implemented or Windows-tested supervisor. B570 is explicitly
authorized to implement a small standalone Python standard-library/ctypes supervisor
and synthetic actors under this lane, using formal exec_command/write_stdin. Local
portable tests or review of this protocol do not qualify that future implementation.

## Fresh roots and real environment

Generate a fresh UUID and exclusively create C:/hs/b570-capability-v1/<UUID> using
existing file APIs. If that exact path exists, stop before writing; no cleanup,
resume, fallback reuse or modifications to old roots. Create stage-specific attempt
subdirectories. The code accepts an explicit root argument; never imports common.py
from the old fixed-root harness. Record protocol commit and initial acquisition hashes.
Preparation may use existing services. Actual commands may use formal exec_command;
record every invocation, shell, working directory, output, session ID and exit status.
Those tool fields are not OS process identities or hard runtime deadlines.

Use the known Python312 executable, after checking its current bytes and identity:
C:/Users/DIANG/AppData/Local/Programs/Python/Python312/python.exe.
Do not silently substitute bundled Python. Record any absent/incompatible binary as
ENVIRONMENT_BLOCKED. Run a bounded CPU preflight via the formal command tool that
queries its own sys.executable/version, os.name and selected environment presence,
and GetWindowsDirectoryW/GetSystemDirectoryW via ctypes. These are ordinary APIs
inside a newly launched Python process, not an indirect escape from node_repl.
Do not read process/node:process in shared Node, synthesize SYSTEMROOT, install
anything or dump environment secrets. Children inherit the standalone process's
actual environment, with explicit task TMP/TEMP overrides. If required paths cannot
be established from authoritative APIs, stop with exact evidence. No requirement
for nodeRepl.env, standalone Node or a C# compiler in this lane.

## Development and execution phases

Total task budget: 6 hours from the first preparation timestamp, including delivery.
D0: at most 90 minutes implementation/preflight, at most 3 source revisions, at most
20 recorded synthetic development case attempts. Fixes are allowed here; preserve
all attempts and diagnostics. They never count as qualification. A failed attempt
may be followed by a corrected attempt only after all its known children are proven
closed. Uncertain cleanup is a hard stop, not permission to try another root.
D0 includes source self-check, exact root confinement, timeouts, resource limits,
raw-log handling and cleanup. Use independent review if available, disclose its
result or unavailability; it is not falsely inherited from the old source freeze.
This bounded CPU capability lane does not require a prior independent clean verdict;
that explicit exception does NOT authorize the original Windows/scientific tests.

F: freeze final source bytes, Python identity, configuration, protocol and actor
identities in CAPABILITY_FREEZE.json. Hash on entry to each case. Any later source
change ends this measured run; no in-place repair/retry/resume. The freeze is a
provenance record, not a claim of independent source approval.
Q: exactly one qualification attempt for each case below, serially. All three must
pass before endurance. Any unexpected failure stops measured execution.
S: automatically continue without waiting for another human reply into a 3-hour
endurance window (10800 monotonic seconds). One serial cycle per 30-second cadence:
normal, timeout, abnormal-tree. No overlap, no catch-up bursts, no concurrent actors
from different cases. At most 360 cycles; do not start a cycle if fewer than 25
seconds remain. After completing cycles, remain under monitoring until 10800 seconds.
Require at least 350 complete cycles and all started cases PASS for endurance PASS.
No early success by shortening the window or filling it with unmonitored sleep.
R: reserve up to 30 minutes for closure, validation, evidence hashing and delivery.
If task budget leaves insufficient time for the full soak plus reserve, stop before
S as BUDGET_BLOCKED; do not silently shorten it. Never exceed the 6-hour hard limit.

## Supervisor boundary and required implementation

Use a small outer watchdog and inner supervisor, both launched through the formal
command route. The watchdog creates the supervisor suspended, assigns an outer
Windows Job with KILL_ON_JOB_CLOSE, retains its process handle and resumes it only
after registration. The watchdog independently enforces whole-run deadline and
supervisor heartbeat timeout (10 seconds), and records supervisor actual OS creation,
exit, exit code and empty outer Job before releasing handles. The supervisor owns
per-case Jobs and watches all actor descendants with Windows debug process events
(or another implementation with equivalent demonstrated descendant observation).
Register actual PID, creation FILETIME, parent, command identity before permitting
actor execution; retain handles until actual exit is observed and read via
GetProcessTimes. Whole Job termination must not rely on PID name matching or Ctrl-C.
Use DEBUG_PROCESS, not DEBUG_ONLY_THIS_PROCESS, when using debug events. Continuously
drain debug events; do not assume a Popen exit alone means all descendants exited.

Watchdog stdout/stderr, tool session and final exit code are retained, but watchdog,
command-shell and tool-host OS lifetimes are OUTSIDE the independently observed
closure boundary. Report these known starts separately with missing OS fields;
do not assign zero lifetimes, invent external receipts, or claim complete task
accounting. Earlier preflight/development/delivery processes are also listed, with
actual observation coverage marked. This explicit boundary permits capability
measurement; it DOES NOT satisfy the old PR119 complete-total-ledger acceptance.
The watchdog cannot certify its own OS exit from inside itself. Tool exit is a
separate supporting observation only. A future external observer remains required
if the old complete accounting criterion is retained.

Each observed identity is PID plus creation FILETIME; serialize FILETIME as decimal
strings. Flush append-only logs and preserve distinct START/CONTROL/TERMINATE/EXIT/
HANDLE_CLOSED records with monotonic times. Keep authoritative state in the watchdog/
supervisor, not a child-written PASS. Closing a handle is not observing process exit.
The watchdog owns an outer kill boundary; supervisor crash leads to termination of
remaining actors. If cleanup cannot be confirmed, end as CLEANUP_UNCONFIRMED and
list exact retained identities/handles. Do not blindly kill unrelated processes.

## Three frozen checks and acceptance

|Case|Actual behavior and control point|PASS requirements|Hard deadline|
|---|---|---|---|
|C1 normal|One CPU actor sends READY, waits about 1 second, writes a nonce-bound completion message and exits 0.|One observed actor identity; correct nonce; actual exit 0; exit FILETIME >= creation; zero active case-Job processes; all owned case handles closed.|5 seconds from launch; cleanup allowance 5 seconds.|
|C2 timeout|One actor sends READY then remains alive, sleeping, for at least 30 seconds unless killed. Supervisor triggers timeout at 2 seconds after READY.|READY reached; retained handle proves actor alive at trigger; timeout request at 2.0–3.0 seconds after READY; actual Job termination and nonzero exit; actual exit and empty Job within 5 seconds of trigger; no subsequent actor work; all handles closed.|READY within 3 seconds; whole case at most 10 seconds.|
|C3 abnormal tree|Root actor creates child; child creates grandchild. Both descendants send nonce-bound READY then wait up to 60 seconds. Only after all three identities and both READY messages are observed does supervisor send CRASH_GO; root exits 7 without cleaning descendants.|All 3 identities observed with correct parent links; both descendants alive when CRASH_GO is sent; actual root exit 7; terminate the whole case Job; actual exits for both descendants and empty Job within 5 seconds of root exit; all handles closed.|Tree READY within 5 seconds; whole case at most 10 seconds.|

No control point means FAIL, even if an earlier rejection prevented danger. A C2
forced nonzero exit and C3 root exit 7 are EXPECTED outcomes, not reasons to stop
if and only if every corresponding raw-evidence criterion passes. A spontaneous
C2 exit or tree that never formed cannot count as PASS. C2/C3 deadlines are enforced
inside the supervisor/watchdog, not by yield_time_ms. Capability thresholds here
are not the old one-second sampling qualification. Three cases total <=25 seconds
per cycle by admitting the next case only after prior closure; exceeding the cycle
budget is an endurance failure, not an excuse to overlap or catch up.

## Sustained monitoring and stopping rules

Sample at least once per second: live identity count, Job active count, per-process
RSS, total observed RSS, watchdog/supervisor heartbeat age, root storage allocation
and free disk. Record sample gaps; a gap >5 seconds fails endurance. Use bounded
known-file byte counters during cases and full root inventory between cycles;
never traverse old roots. Report actual measured gaps, not nominal timer intervals.
Limits: <=6000 actor starts (development included), <=8 live actors, <=256 MiB RSS
per actor, <=512 MiB each supervisor/watchdog, <=1.5 GiB aggregate for this new lane,
<=1 GiB task-root allocation including delivery with 256 MiB reserved before S,
>=10 GiB disk free, <=6 hours task wall, <=21600 seconds observed actor lifetime sum.
On a real resource limit, unexpected exit, missing control point, ledger corruption,
source drift, unclosed process, monitor failure or disk/log write error: stop admission,
terminate only owned Jobs, collect closure evidence, mark subsequent cases UNSTARTED.

Tool yielding, a session ID, sparse console output, successful expected fault
injection, and empty shared nodeRepl.env are NOT failures in this new lane. Keep
supervision in the standalone processes; poll write_stdin for progress without
spawning extra helpers or sending Ctrl-C as routine polling. A lost tool connection
is not a successful run: reacquire the same session if available, otherwise use
existing file APIs for evidence; do not start another supervisor or resume work.
The watchdog still enforces its local deadline. If no exit evidence is available,
report INCOMPLETE. Do not claim guaranteed survival of OS sleep, app termination,
machine restart or loss of the external executor.

## Evidence and statuses

Deliver immutable acquisition, command invocation records, environment provenance
(no secrets), all development attempts, frozen sources/config, all raw case events,
monitor samples, per-identity lifetimes, per-case conclusions, watchdog closure and
tool exit record. Hash an evidence manifest after workers close; reread and verify
all retained files and derived counts using a read-only verifier. Record verifier
and delivery processes in the outer/unobserved list; do not conceal tail costs.
Upload within this PR's capability lane only; read back small report/manifest/source
bytes and their hashes. If large raw evidence cannot be remotely delivered within
limits, retain it locally and mark remote evidence incomplete, never invent recovery.
No requirement to run the old archive/auditor against this incompatible new schema.

Statuses: ENVIRONMENT_BLOCKED, DEVELOPMENT_BLOCKED, CAPABILITY_FAIL,
CLEANUP_UNCONFIRMED, BUDGET_BLOCKED, INCOMPLETE; CAPABILITY_3CHECK_PASS only for Q;
CAPABILITY_ENDURANCE_PASS only for Q + full S + closed observed identities + verified
evidence + tool exit 0. Endurance PASS is explicitly scoped and retains the outer
accounting gap. Remote delivery status is separate. None means ENGINEERING_READY,
SMALL_WINDOWS_VALIDATION_PASS, original eight-case success, GPU suitability or a
paper result. No automatic progression into the original eight cases after endurance.
