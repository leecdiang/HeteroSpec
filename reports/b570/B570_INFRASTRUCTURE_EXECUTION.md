# B570 Infrastructure Execution Record

## Preserved attempts

- `work/b570/formal-v2-20260912-024351`: **INVALID / INFRASTRUCTURE-INTERRUPTED**; no admissible scientific payload.
- `work/b570/diagnostic-v1-20260912-141235`: **CONFIGURATION_ERROR / NO SCIENTIFIC RESULT**; llama-bench rejected `-ngl all` before model load. Its watchdog failure label is secondary, not the root cause.

The valid original correctness result is instead `work/b570/formal-v2-20260912-122930`: **CORRECTNESS = FAIL**, 36/36 workloads, 9/18 exact pairs.

## Detached execution controls

Windows Task Scheduler owns formal tasks. The infrastructure-only scheduler test completed twelve heartbeats over approximately two minutes with task result 0. The detached PresentMon test produced 301 samples and complete metadata. The watchdog observes the run-local heartbeat and preserves a failure snapshot without restarting scientific stages.

Before every new formal run, CBS RebootPending, Windows Update RebootRequired, model hashes, active workload processes, Task Scheduler evidence, and PresentMon evidence are checked. The persistent ZulerCoreTools pending-rename marker is attributed read-only to the ToDesk-installed watchdog self-maintenance component; no registry entry, service, or software is removed or modified.
