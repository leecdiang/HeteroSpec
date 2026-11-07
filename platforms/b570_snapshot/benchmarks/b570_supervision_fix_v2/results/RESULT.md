# PR119 small Windows validation — ENGINEERING_BLOCKED

Operational stop: **BOOTSTRAP_BLOCKED**, before the first new task process.
Locked source commit: `4d0c64def3389176f338e376d73637666cc9f66e`.
Dispatch: author's instruction “按照pr119继续推进”, interpreted through B570_NEXT_PROMPT.md.
This is a static admission result, not an observed Windows controller failure.

## Completed admission checks

The existing tool service fetched all 53 files from the locked remote commit into memory.
All 53 computed Git blob SHA1 identities matched the connector's returned blob IDs.
All 49 SOURCE_REVIEW_FREEZE.reviewed_inputs SHA256 values matched exact remote bytes.
Both final review/status file SHA256 values matched the source freeze; final status is scoped-clean.
SOURCE_REVIEW_FREEZE.json SHA256:
`71049fc8bac612d3e194136fa1c4891690b50e8ccc98d60f78f68638b6bebb3c`.
Total exact source bytes fetched: 264866. This authenticates source identity, not Windows behavior.

Existing-service fs.lstat found `C:/hs/b570-supervision-fix-v2-20261016` absent
at 2026-10-16T10:37:20.348Z and again at 10:38:51.711Z.
No local task root, checkout, process registry, fabricated ledger or runtime DLL was created.
No old task data was copied or modified.

## First blocker: fresh bootstrap and closure are not established

The supplied entrypoints do not provide a complete directly usable fresh-task
bootstrap/closure arrangement at the required isolated root:

- host/outer_task_ledger.py:12–14 derives BASE from its own source directory and uses
  BASE/queue and BASE/task. In the repo/benchmarks source layout used by the closing
  delivery code these are not the task-root directories used by common.py.
- host/outer_task_ledger_v2.py:12–14 uses the required new absolute task root and queue-v2,
  but :54–55 unconditionally reads a pre-existing nonempty task/PROCESS_LEDGER.jsonl
  and inherits its start, sequence, counts and lifetimes. This is a continuation entry,
  not an empty-root initialization. :167 also hardcodes an earlier malformed-request stop.
- host/queue_client.mjs:6–9 publishes only under the task-root queue-v2.
- host/closure_audit.mjs:28–29 requires both ledger parts; :49–74 requires actual OS
  closure for the prospectively registered outer identities and exact task boundaries.
  No missing observation can be supplied by a fixed allowance.
- host/live_budget.py requires the actual executing broker PID/OS creation identity
  in BOOTSTRAP_REGISTRY before broker admission.

These are source-level dependencies, not evidence that a broker was started and crashed.
A new externally observed bootstrap adapter and consistent fresh-run entry/closure
contract would have to be supplied or the reviewed implementation adapted. No such
adapter was created or executed during this dispatch. No claim is made that Windows
cannot support such an arrangement.

B570_NEXT_PROMPT.md explicitly requires:
“若无法做到，停止于 BOOTSTRAP_BLOCKED，列出缺失，而非继续再产生一份不完整总账。”
It also requires:
“若源码或工具适配需要修改，保留证据并停止，交回本 PR 修复。”

Accordingly, no source changes, import-time monkeypatches, copied historical ledger,
synthetic predecessor, empty ledger placeholder or invented bootstrap observations were used.
Missing prospective artifacts are NOT observations lost after a launch: no launch occurred.
They are an admitted bootstrap/outer-closure adapter, actual broker/outer identities,
a common monotonic start, and a complete OS-exit observation arrangement for those identities.

## Eight-case matrix

|Order|Case|Starts|Outcome|Control point / detector|
|---|---|---:|---|---|
|1|normal_single|0|UNSTARTED|Not reached|
|2|normal_transition (8 A→B pairs)|0|UNSTARTED|Not reached|
|3|terminal_pending_completion|0|UNSTARTED|Not reached|
|4|frozen_input|0|UNSTARTED|Not reached|
|5|late_closed_slot_write|0|UNSTARTED|Not reached|
|6|resource_read_failure|0|UNSTARTED|Not reached|
|7|directory_read_timeout|0|UNSTARTED|Not reached|
|8|journal_write_failure|0|UNSTARTED|Not reached|

0 complete, 0 runtime failures, 8 UNSTARTED. One static bootstrap admission block.
Portable Python/Node regressions and CPU DLL compilation were NOT run in this dispatch.
The PR preparation's reported 75 portable tests are historical source-preparation evidence,
not new tests or machine acceptance. No natural A→B notification was observed.
No implementation review was rerun; the authenticated existing source review remains scoped-clean.

## Actual costs, evidence and limits

New task child/outer process starts: 0; observed task-owned OS lifetime sum: 0 seconds.
No broker, compiler, Git command, shell, launcher, CPU test child, auditor child,
archive/recovery command or reviewer child was launched.
Pre-existing GitHub/Node tool services performed remote reads, in-memory hashing,
read-only root existence checks and this remote-only delivery; they are not new task children.
Full engine/application process counts and CPU/RSS consumption of those existing services
were not measured and are not asserted to be zero.

No prospective runtime monotonic task boundary exists, so runtime engineering-wall and
supervision metrics are NOT APPLICABLE, not a successful zero-duration monitored run.
The UTC root checks above are tool-service observations, not synthetic resource samples.
New local task-derived storage: 0 bytes; no local archive or restored tree exists.
Remote evidence is this result at its resulting commit, plus the immutable locked source
and source-review freeze. No raw runtime manifest, archive download, packaged-auditor
recompute or byte-identical restoration is claimed; these were not started.
No SMALL_WINDOWS_VALIDATION_PASS, ENGINEERING_READY or paper/scientific qualification.

All task execution counts remain zero:
GPU query/init/plugin load, model file read/request, scientific native start and graph compute.
confirm.py, the 19-case suite and the 57-case confirmation were not run.
No GPU, actor, S1–S3, profiling, RTX, paper, main, release or automation action was taken.

PR115 remains at d04b41e03b1fcd747851edb6aed3b4c40c544a5d (Draft).
PR117 remains at 08ec85f4a2c58e53a6dde4a230d686930dc7e600 (Draft).
Their historical ENGINEERING_BLOCKED evidence is unchanged.
PR119 remains Draft; only this independent result is added.
