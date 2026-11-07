# Supervision repaired and new numerical registration frozen; GPU unstarted

Review base: `58511a4dfa39776503a14ed3176931c26cf657c4`. All new work is confined
to this directory and its separate ignored output root. No GPU/device query,
Vulkan/CUDA plugin load, native graph compute or model request was made.

The confirmed old boundary error is that `controller.py` measured its elapsed
after proc.wait, raw parsing and closing runtime_gate hashing; `native_audit.py`
then subtracted the last sample from that value. Post-exit audit could therefore
inflate the terminal gap. Old1.032s has no phase decomposition: its post-exit
fraction and actual live monitoring eligibility remain unknown. Old receipts
still fail their old auditor and cannot be accepted by the new schema.

New times are monotonic integer nanoseconds: launch/Popen return; both resource
and directory read begin/end; immediate first coordinator poll confirming exit;
post-exit audit begin/end; lifecycle write begin and an after-close commit marker.
GetProcessTimes creation/exit FILETIME and CPU times are retained separately.
No audit-end timestamp or FILETIME difference is used as an exit observation.

The coordinator performs no full module hash, raw parse or directory scan while
the target lives. One CPU monitor process runs independent resource/directory
reading threads; another CPU process audits identity/output. Waiting for GO is
fully supervised; GO requires successful module hashes and valid fresh readings.
The gap remains exactly1s, with conservative interval brackets including reading
duration. Stalls, failed reads, races, helper crashes, timeouts and kill/wait
cleanup are explicit. Exit races discard readings without invented RSS values.
Sampling eligibility ends at exit; subsequent CPU-control RSS and audit costs
are distinct. Complete gate/closing module checks and all numerical audits remain.
The exact policy and unchanged numerical contract are bound in `POLICY.md`.

Latest fresh CPU suite: **17/17 methods**,9.093s,16 actual CPU-only child processes
and32 CPU control workers. It tests actual new supervisor/worker paths: normal
real-clock exit;2s virtual post-exit hash-audit delay; real live resource stall
over1s;2s slow identity gate with ongoing reads and no early GO; pre/closing hash
mismatch; missing/truncated output; poll/read exit race; fast/abnormal exit;
engineering timeout; monitor-process crash; slow directory scan; API read failure;
exact1s±1ns boundaries; old-auditor rejection; all161 serializer fields; native
identity-only source change. Virtual tests use a named shared clock and controlled
event barriers, not sleep timing to choose either side of the1s boundary.

Across all prospective attempts,62 CPU children and124 CPU control workers ran;
CPU suite wall totaled43.562s and offline build-command wall24.314s, separately
from any experiment budget. Two failed preparation receipts are retained: a
Windows clock-file sharing race and unavailable Interlocked intrinsic exports
in the CPU harness. The final shared virtual clock uses a named mutex/mapping.
All1,383 CPU evidence files are retained in one authenticated archive with
member-by-member readback. `PREPARATION_CHECK.json` verifies586 frozen bindings,
694 old raw files, all161 wires and both evidence/binary archives. No CPU fixture
or virtual timestamp is presented as native GPU evidence.

The validated old executable hard-binds its run_id, so it cannot serve a new
identity unchanged. The new offline-built executable changes only that literal
in fixture.hpp. host.cpp is byte-identical; fixture.hpp is otherwise exact;
query_head.h, graph/arithmetic code, shapes/strides, inputs, precision, numerical
rules/analyzer/FP64 reference files and both numerical DLL bytes are unchanged.
No native executable was launched during this repair. The old executable itself
was rehashed unchanged. QH_C remains fixed; old results are never new repeats.

New run_id: `b570-supervised-numerical-v3-20261015-01`.
New plan:1 complete80-graph support-only census +160 numerical hosts
(16 original exposed inputs ×5 modes ×2 independent processes), all40 q1 first,
then120 q>1. Maximum161 experiment hosts/160 calls, plus at most322 CPU control
worker processes and one controller. The monitor has two reading threads plus
its main thread; the auditor has one main thread. These are not total OS counts.

Budget remains2GiB including all new preparation/build/test/output artifacts and
one full raw-export reserve. The entire future controller engineering wall is
<=3600s, and each complete slot<=180s, including CPU control workers, supervision,
all identity/output/numerical audits, cleanup, comparisons and lifecycle writes.
Observed native lifetime and post-exit auditor wall are separate fields. The
whole-controller closeout includes control overhead and closeout writing; it
must not be mixed with old41.327s accounting or called graph latency. Later CPU
delivery is separately timed. Existing RAM/disk/RSS/GPU-checkpoint limits remain;
additional CPU-control RSS is also checked.0 probes/warmups/retries/models.

New `F0.json` SHA256 (to be approved separately):

`56f5787e41dcf8dcc4ecad83eb26bf406a483664e67a939dc66edf0af5015fdc`

Only future entry, **not invoked**:

```powershell
& 'C:/Users/DIANG/AppData/Local/Programs/Python/Python312/python.exe' 'C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/host/supervised_numerical_v3/execute.py' --author-approved-f0-sha 56f5787e41dcf8dcc4ecad83eb26bf406a483664e67a939dc66edf0af5015fdc
```

New run root and all161 slots are unstarted. Old v2 remains37 attempts,
36 admitted(1census+35numerical),1 invalid,124 unstarted,36 calls,41.327s.
Original S1 remains2/5.109s/159 unstarted; diagnostics remain7/13.172s/5 success/
2 declared negatives. All old source/F0/receipts/samples/results/raw output stay
unchanged. S2/S3, actor, timing/profile, RTX, paper, main, release and automation
remain closed. Stop here pending explicit confirmation of this new F0.
