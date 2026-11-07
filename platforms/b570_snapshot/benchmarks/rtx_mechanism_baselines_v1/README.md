# RTX mechanism and strong software baselines v1

**EXECUTED / FRESH_CPU_RECOMPUTATION_PASS / SOFTWARE_FIRST_HOLD.**
Actual results: [RESULT.md](RESULT.md), [SCIENTIFIC_FINDINGS.json](SCIENTIFIC_FINDINGS.json),
[results/](results/). All historical UUIDs remain sealed.

Actual1137 GPU-native hosts /40124 explicit GGML graph calls: core956 hosts/34124
calls, five capability attempts/32calls(including one preserved pre-graph CUPTI
startup failure), and a separately frozen OFF producer cohort176hosts/5968calls.
Core includes44 fresh serial references,144 numerical qualifications and768
timing hosts/two independent cycle starts. Optional OFF includes16 new q4 serial
captures,32 qualifications and128 timing hosts. No scientific reruns.

Actual CUPTI capture/end/instantiate/replay verifies16 distinct ON signatures
across18 layout coordinates(q1 shares a path). Clean hosts do not load CUPTI.
24 profile attempts include the failure;23 actual timelines complete. All formal
ordinary outputs and complete input bytes qualify against new references.

QB_A ON/OFF completed-cost ratios range0.615–0.849 on these selected geometries.
The OFF QB/QH cost gap narrows greatly with replay; fine mapping differences need
same-unit A/A caution. Actual QB kernel counts change8→3→8 at1023/1024/1025 keys;
compact Q removes one repeated copy kernel from QH_C at256. No physical traffic,
occupancy,TensorCore utilization or hardware benefit is established.

The continuous Q copy/transpose→upload→compute/sync→readback experiment charges
conversion in one actual interval. QH compact/permuted ratios0.965833(q2) and
0.947658(q4) are **OFF-only**, without an identical-arm A/A certificate. Natural Q
production, ON integrated transactions, actor/decoder/system benefit remain UNKNOWN.

All26545 archive members restore byte-exact; all scientific tables and raw audits
recompute in new interpreters on this host. This is not external review or remote
raw authentication. [RAW_LOCATION.json](RAW_LOCATION.json) supplies hashes/location.
[execution/](execution/) contains byte-copied consumed JSON with text conversion
disabled, bound by [EXACT_ARTIFACTS.json](EXACT_ARTIFACTS.json). Actual consumed
code/binaries are retained in raw SOURCE/SOURCE_REPAIR1; ordinary Git text can useLF.
[COMMANDS.md](COMMANDS.md) records actual commands and CPU-only reconstruction.

**Permanently closed UUID. Do not resume any GPU stage. No actor/decoder/W1,
weights,B570,paper/main,RTL/FPGA,merge or release was performed.**

## Initial design text (historical; actual status is above)

**CPU_DESIGN_READY / NATIVE_IMPLEMENTATION_PENDING / GPU_NOT_RUN.**
Parent: PR121, `d82ec4097adfa032886040e075e71e41cfeb5855`.

PR121 supports QB as the stronger observed baseline, with no established QH_C
winning region. Its q2 completed costs drop sharply at 1024 keys in all three
mappings; compact Q largely removes QH_C's deficit. Its collector explicitly sets
`GGML_CUDA_DISABLE_GRAPHS=1`. These motivate a focused mechanism experiment, not
another selector fit or an assumption of accelerator benefit.

This PR supplies a deterministic CPU task planner and descriptive paired analyzer.
The RTX executor must implement the native adapter, mode evidence and integrated
transaction. No callable GPU dispatcher is included in this initial delivery.

- [PROTOCOL.md](PROTOCOL.md): hypotheses, capability branches, numerical contract,
  clean and profiled measurements, cost boundaries, budget and stop conditions.
- [RECEIPTS.md](RECEIPTS.md): analysis interface and evidence responsibilities.
- [RTX_PROMPT.md](RTX_PROMPT.md): complete Chinese task to forward to RTX.
- [PLAN_OVERVIEW.json](PLAN_OVERVIEW.json): generated initial task counts.
- [VALIDATION.md](VALIDATION.md): actual CPU checks and untested scope.

Run from this directory:

```sh
python -B -m unittest -v test_cpu
python -B plan.py --graph dual --out runs/plan.json
python -B analyze.py --plan runs/plan.json --receipts runs/receipts.jsonl --out runs/analysis.json
```

The last command needs independently verified actual timing receipts. It cannot
verify CUDA Graph activation or device bytes. Tests use fabricated fixtures only.
`--graph off-only` is a prospectively frozen fallback with a different plan hash;
it does not relabel old attempts or turn unsupported ON into a valid comparison.
Plan order is not an execution instruction: inspect stage/optional/requires gates.

Core: six geometries × two existing PR121 input realizations. PQ/QB_A/QH_C/QB_B
are compared with graphs OFF and verified ON in eight blocks, two balanced cycles.
Default core: **956 planned hosts / 34124 calls**, including new serial references
and qualification. Optional integrated Q-update: **176 hosts / 5968 calls**.
The off-only core is 500 hosts / 17084 calls. Capability/trace probes are separately
capped and accounted; none of these planned counts is an observed execution result.

Six-hour first dispatch, final45minutes reserved for closure, one GPU worker.
Routine platform repairs are allowed. Missing profiler, unreliable SM telemetry
or unavailable graph capture narrow conclusions without blocking unrelated work.
No natural decoder/actor/W1, new weights, B570 work, RTL/FPGA, manuscript changes,
merge or release. Old UUIDs remain closed. Hardware stays HOLD unless a later
study establishes both a physical bottleneck and system relevance.
