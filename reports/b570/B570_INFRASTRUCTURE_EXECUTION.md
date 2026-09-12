# B570 Infrastructure Execution Record

## Preserved attempts

- `work/b570/formal-v2-20260912-024351`: **INVALID / INFRASTRUCTURE-INTERRUPTED**; no admissible scientific payload.
- `work/b570/diagnostic-v1-20260912-141235`: **CONFIGURATION_ERROR / NO SCIENTIFIC RESULT**; llama-bench rejected `-ngl all` before model load. Its watchdog failure label is secondary, not the root cause.

The valid original correctness result is instead `work/b570/formal-v2-20260912-122930`: **CORRECTNESS = FAIL**, 36/36 workloads, 9/18 exact pairs.

## Detached execution controls

Windows Task Scheduler owns formal tasks. The infrastructure-only scheduler test completed twelve heartbeats over approximately two minutes with task result 0. The detached PresentMon test produced 301 samples and complete metadata. The watchdog observes the run-local heartbeat and preserves a failure snapshot without restarting scientific stages.

Before every new formal run, CBS RebootPending, Windows Update RebootRequired, model hashes, active workload processes, Task Scheduler evidence, and PresentMon evidence are checked. The persistent ZulerCoreTools pending-rename marker is attributed read-only to the ToDesk-installed watchdog self-maintenance component; no registry entry, service, or software is removed or modified.

## Diagnostic closeout deviations

`diagnostic-v1-20260912-170834` completed all authorized scientific workloads. Its Task Scheduler finalizer then failed because the restricted task environment did not contain `git.exe` on `PATH`; reports and the 448-entry archive had already been generated. This is an implementation-only closeout failure. Git commits, push, PR creation, and final status were completed after reconnection without rerunning any workload.

The user reconnected while the fallback V2 512 cell was running. That cell is invalid for timing/power inference. Because a clean disconnected boundary was not re-established before the following 2048 cell, it is conservatively excluded too. The prior V2_raw cells, all 180 HumanEval30 workloads, and all 36 fallback-correctness workloads completed before reconnection and remain valid. No result-driven rerun was performed.
