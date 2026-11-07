# Independent S1A Bridge v2 — CPU prepared, GPU NOT AUTHORIZED

Depends on PR113 and the terminal PR114 result at
`449ead854424a1ac88d538332994bcf9f8813e1e`. No old run is resumed. The scientific
24-context amendment is unchanged; no previous execution approval transfers.
Read READINESS_REVIEW.md for the A/B decision and its limits.

Run ID: `pr114-s1a-bridge-v2`.
New execution root: `D:/hs114-s1a-bridge-v2`.
Fresh restore root: `D:/hs114-s1a-bridge-v2-fresh`.
Both must remain absent before separate GPU authorization; no execution ledger
or real author stage approval has been created during this CPU preparation.

## Implemented registration

`readiness_policy.py` separates CPU-verifiable admission semantics from the
one explicitly charged readiness query per host. It permits only policy A:
exact device/driver/capacity and power scheme, AC, utilization<=5%,temperature<=55C,
free VRAM>=512MiB, one attempt, no cooldown or retry. Invalid/missing/nonfinite
telemetry stops. This is conservative environmental isolation, not a CUDA
correctness theorem or proof of continuous idle. Production Win32 executable
conflicts are checked at stage start and before each host; unknown GPU-client
attribution remains unknown. Windows child JobObject limits remain active.

The native gate changes only run/stage strings to admit this independent F0 and
wire. The graph constructor, shared-core initialization and imports, arithmetic
header, numerical analyzer, numerical DLLs and effective CUDA configuration are
unchanged. New EXE hash is honestly registered. Old census is not transferable:
**one new full census is required** before separately approved numerical work.

The fixed original profile_coordinates() selector regenerates exactly24 complete
snapshots: three families, both phases, q1..4. All Q/K/V/mask bytes, head/channel/key
dimensions, op parameters, precision, mask visibility and references remain
identical. Padded extent is distinguished from actual visible keys. Five layouts
MQ/PQ/QB/QH_C/QH_D, two independent fresh processes each. QH_C is primary and QH_D
fixed contrast. The first60 slots are all six q1 contexts; the remaining180 are
q>1. Old PR113474 observations and the zero-start Bridge are never repeats here.

## Exact future counters and independent budgets

| Stage | Controller | Native | Readiness | conhost cap | Graph calls | supports_op |
|---|---:|---:|---:|---:|---:|---:|
| Census | 1 | 1 | 1 | 2 | 0 | 1806 across120 graphs |
| Numerical | 1 | 240 | 240 | 480 | 240 | 3612 |
| Total | 2 | 241 | 241 | 482 | 240 | 5418 |

Total directly launched processes484; including registered helpers966. No free
probe, warmup, request, scientific retry or profiler. Census has600s wall/1800s
conservative owned, native240s, query10s. Numerical has1800s wall/5400s conservative
owned, native60s/query10s. Separate CPU delivery900s/2700s. Total9900s conservative
registered-job owned, independently budgeted, never old unused capacity.

Numerical wall includes source/input/runtime hashing, OS conflict inventories,
readiness, full actual readbacks, online controls and resource audits. Previously
observed active cost3.6535s/qualified slot extrapolates to876.84s for240; the1800s
cap is descriptive headroom, not a completion guarantee. One child+one conhost+
controller is conservatively wall x3. Native/job commit2GiB, ready256MiB,
controller512MiB; active child-job count2. Output pipes32KiB each. Existing
25ms-requested deadline/resource monitor and50ms-requested child polling are not
maximum-gap guarantees or continuous GPU monitoring. Free disk4GiB before,
512MiB during. Full byte reconciliation every30 completions and at stage edges;
append-only fsynced accounting and5s durable finalization reserve remain intact.

Worst raw255,969,782B; archive277,403,847B; two raw copies+two archive copies plus
384MiB preparation/Git allowance total1,486,177,658B<4GiB. No assumption of equal
outputs: all240 four-stage outputs reserve55,705,600B. Actual full input reads
before/after total1,694,597,120B but equal immutable bytes may be hash-deduplicated
only after full reads/verification; retain every occurrence and first mutation.
Full immutable reference CAS93,238,774B. Never discard failure data for capacity.
See BUDGET_FINAL.json for every device-identity and synchronization API count.
Internal CUDA/driver queries/allocations are UNKNOWN. CPU registered jobs are
accounted; ordinary Git/interactive tooling is not globally process-accounted,
and its elapsed delivery time must be reported separately.

## Stop and qualification

Any control/identity/readiness/interface/support/placement/input/nonfinite/q1/
MQ-own-path/history-PQ-QB/repeat/resource failure stops; no restart. A reservation
with no native start is distinguished from started failure. Completed slots are
not failed when the next slot cannot fit. Remaining coordinates stay explicit.
Only q>1 QH_D unsupported follows original explicit NOT_SUPPORTED rules.
Finite valid q>1 differences are retained with complete bitwise/error/ULP/first
divergence evidence; they are not a universal-MQ-equality gate. No tolerance,
candidate, input, kernel or observer changes to chase a result.

CPU delivery is separate: offline.py analyze/package/authenticated readback/
restore/analyze-fresh uses original independent analyzer semantics and retains
all input/stage/failure bytes. No archive output may fill historical slots.

## Unique future GPU entry — currently unauthorized

F0_IDENTITY.json gives the exact F0 SHA. First obtain **BRIDGE_V2_CENSUS_ONLY**
approval for that exact F0, run ID and accepted24-context scope. Then the only
entry, with the actual independent approval path, is:

```powershell
& 'C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'D:/hs114-bridge-v2/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v2/run_bridge.py' --stage census --approval '<actual independent census approval absolute path>'
```

Do not invoke the EXE directly. After a complete census, use the registered
offline.py seal-census/census-readback workflow and obtain a separate
**BRIDGE_V2_NUMERICAL_EXACT** approval binding F0 and actual census/decision SHA.
The same entry then uses `--stage numerical`. Neither stage auto-enters another.
No S1B clean timing, trace, actor, natural request, S2/S3 or hardware authorization.
