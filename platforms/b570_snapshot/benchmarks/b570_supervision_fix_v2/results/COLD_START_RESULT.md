# Cold-start Windows validation: BOOTSTRAP_BLOCKED

Final outcome: ENGINEERING_BLOCKED before the first new task process.
Locked reviewed source: af91aa6703b16ba3178eeec9895a4f4a13f712cc.
Author reported the PR119 repair/update and the existing dispatch was continued against its amended B570_NEXT_PROMPT.md.
This is an actual tool-interface admission failure, not a broker/Windows case failure.

## Repair and exact-byte admission

The new cold bootstrap source removes the prior ledger continuation dependency, retires the old entries, and adds an existing-service Win32 observer.
The previous results/RESULT.md remains unchanged (Git blob 58f699e810cea937f40c10571f142e5b89e3be9f).
The previous blocker is historical; it is not reused as evidence of this updated source failing.

Fetched all 64 PR files from the locked remote commit into existing-service memory:
64/64 computed Git blob SHA1 identities matched; exact bytes total 304275.
59/59 reviewed_inputs and 50/50 bound_files matched their SHA256 bindings.
Final independent report/status hashes matched and status is scoped-clean.
SOURCE_REVIEW_FREEZE.json SHA256:
871374cf39d0b0813bbffd14d1ae7c3dfc0eb77eb5946843e28f48111606c26a.
These are source/review identity checks, not Windows execution or a rerun of the 99 portable tests.

## Actual first failure: existing Node service does not expose process

The amendment's first required operation, before local preparation, is:
```javascript
globalThis.b570ToolBegin = process.hrtime.bigint();
```
Executing that operation in the actual existing mcp__node_repl service returned:
`process is not defined`.
No later statement in that tool invocation ran.

The tool's published interface explicitly states:
“Top-level static imports and node:process are unavailable.”
An explicit dynamic import compatibility check returned:
`Importing module "node:process" is not allowed in node_repl`.
No shell/helper process was used to obtain a replacement clock or observer.
No global process shim, indirect require, alternate VM, clock approximation or modified bootstrap was introduced.
The prescribed startCold call cannot be supplied its required prospectively captured toolBeginNs through the exposed interface.

A subsequent existing-service check at 2026-10-16T13:13:40.605Z
(2026-10-16 21:13:40.605 Asia/Shanghai) confirmed:
- global process type: undefined;
- b570ToolBegin absent; b570 session absent;
- C:/hs/b570-supervision-fix-v2-20261016 absent.
The same no-root/no-anchor/no-session state was rechecked at 13:14:27.455Z.

The updated prompt says to use the ALREADY RUNNING Node service, not launch a new observer,
and “If unavailable, stop admission; do not adapt tools on the machine.”
The retained prompt also says to stop if tool adaptation requires modification.
Accordingly this dispatch stops at BOOTSTRAP_BLOCKED. The observed limitation is specific
to this tool interface; it does not prove the new cold-start implementation fails in a
Windows Node environment that exposes the required APIs. The pinned native bridge was
not downloaded or loaded, so its Windows behavior and the broker remain untested.

## Exact execution matrix

|Item|Attempts|Outcome|
|---|---:|---|
|bootstrap-smoke|0|UNSTARTED|
|normal_single|0|UNSTARTED|
|normal_transition, 8 A→B pairs|0|UNSTARTED|
|terminal_pending_completion|0|UNSTARTED|
|frozen_input|0|UNSTARTED|
|late_closed_slot_write|0|UNSTARTED|
|resource_read_failure|0|UNSTARTED|
|directory_read_timeout|0|UNSTARTED|
|journal_write_failure|0|UNSTARTED|

0 completed, 0 runtime failures, 8 case coordinates UNSTARTED; one tool-interface admission block.
No intended control point, fault injection, detector, watcher I/O or A→B notification was reached.
Portable regressions, CPU DLL compilation, snapshots and raw-auditor processes were not launched.
No confirm.py, full 19-case suite or 57-item confirmation.

## Accounting, evidence and limits

New task-owned child processes: 0. New broker/outer processes: 0.
Task-owned OS lifetime sum: 0 seconds, because no process was created.
No subprocess, Git command, compiler, shell, observer, launcher, test, auditor or recovery helper was launched.
Existing GitHub/Node services performed remote reads, fs.lstat checks, in-memory hashes and remote-only result delivery.
Their whole-application process counts, CPU/RSS and historical lifetimes were not measured and are not reported as zero.

No approved monotonic task anchor was established; engineering-wall/supervision qualification is unavailable,
not a passing zero-duration run. No sample, OS identity, bootstrap registry, successful closure or ledger was fabricated.
No local derived task files, native package, archives or restored trees were created (new local task storage 0 bytes).
The remote result is independent delivery evidence. No runtime raw manifest, download/restore
or unchanged packaged-auditor recomputation was performed or claimed.

GPU query/init/plugin load, model file read/request, scientific native start and graph compute: all 0.
PR115 remains Draft at d04b41e03b1fcd747851edb6aed3b4c40c544a5d.
PR117 remains Draft at 08ec85f4a2c58e53a6dde4a230d686930dc7e600.
No historical evidence, paper, main, release, RTX task or automation was changed.
PR119 remains Draft and reviewed source bytes are unchanged by this evidence-only delivery.

A further attempt needs a supported already-running Windows Node executor exposing the prescribed process/hrtime
and native-bridge APIs, or a separately reviewed amendment compatible with the actual available service.
No SMALL_WINDOWS_VALIDATION_PASS, ENGINEERING_READY, scientific or paper claim is made.
