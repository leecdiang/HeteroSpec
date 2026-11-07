# RTX logical-extent / physical-extent intervention v1

Status: DESIGN_ONLY. No new GPU measurements. Parent: PR122,
a1f15bfc8222054aa7b94b40f41af0dd0492ddab. SOFTWARE_FIRST/HOLD.

## Question and scope
PR122 verified replay reduced the QB/QH difference but retained a large
1023/1024/1025 completed-cost cliff and actual 8/3/8 QB kernels. This study
intervenes on physical extent while holding logical input and visibility fixed.
Padding changes physical work AND may change dispatch: even a positive result
identifies a representation intervention, not the isolated effect of kernel count.
Do not fit selectors, scan for winners, or begin RTL from these results.

## S0: source and adapter preparation (CPU first)
Use the parent runtime manifest and full graph headers as the baseline. Read
CONTRIBUTING.md. Record exact DLL/header/source hashes, compiler, CUDA runtime,
driver, device, observer and plan hash. Locate the matching ggml CUDA source from
local build provenance, inspect matmul/softmax dispatch predicates, and record
file/line/commit plus actual launch signatures. If binary/source correspondence
cannot be established, mark SOURCE_LINK_UNKNOWN; do not block the empirical
intervention or guess source causality from current upstream code.
Implement a NEW entry point/run UUID in this directory, adapting the parent's
runner, collector, full-output checks and persistent input allocation. Old
collectors hard-code run identity and expect source span = physical span: do not
reuse them unmodified for padding. No old run resumes. CPU address tests must
check actual tensor strides for K, V, mask, Q and ordinary restoration, including
all logical words and padding. A source-only dispatch explanation is not a trace.
No forced-dispatch/rebuilt numerical DLL arm in this study; propose separately
only if the representation study leaves a concrete unresolved mechanism.

## B0: fixed logical input, changed physical representation
q=2,d=128,Hq=32,Hkv=8,permuted Q, two original PR121 value patterns/seeds
20261018 and 20261019. Preserve exact logical Q/K/V/mask bytes from the parent
input index; collect fresh references, not old outputs. Four cells:
logical L=1023 or 1024, each with both values. Arms per cell:
- native_A: QB, physical S=L
- native_B: identical QB implementation and input, physical S=L
- pad_1: QB, physical S=L+1
- pad_2: QB, physical S=L+2
Thus L=1023 tests S=1023/1024/1025; L=1024 tests S=1024/1025/1026.
All timed arms use verified ON; no OFF fallback within the primary cohort.

Append zero, finite K/V elements; preserve each original logical element by
coordinate, not a flat memcpy that changes strided head offsets. Preserve mask
bytes for all original columns. Extra columns are negative infinity in the
mask's actual format. The logical causal frontier stays L-q+j+1, NOT S-q+j+1.
Never truncate a logical token or regenerate the old mask from physical S.
Keep scaling, head grouping and all operator parameters unchanged. Inspect
implicit causal/position/ALiBi behavior: if physical extent alters semantics that
cannot be represented by this explicit mask, record UNSUPPORTED before timing.
The plan.py mask helper specifies visibility, not a replacement tensor generator.
Finite zero padding does not guarantee identical floating-point output.

Fresh reference: two independent serial-q1 captures for EACH logical query and
value, original unpadded arithmetic, complete ordinary bytes. Both references
must agree. Qualification: each unique arm (native,pad_1,pad_2), two fresh hosts,
2 warmup +32 calls. Every output finite and bit-exact to the SAME unpadded
reference; all inputs checked before/after; genuine CUDA placement, supported
nodes, compute/sync status and immutable storage required. Never accept an arm
only because it equals its own padded serial reference. A padded serial diagnostic
may help explain failure but cannot replace the contract. Qualification failures
are scientific outcomes; no relaxed tolerance, alternate seeds or retry search.
Freeze arm admission before clean latency inspection. Failed/unavailable arms
remain in coverage; execute eligible arms in their original schedule slots.

## T0: smallest ON integrated-Q transaction
q=2 and 4,k=256,d=128,Hq=32,Hkv=8, two parent values. Four arms:
QB_A permuted, QB_B identical permuted, QH_permuted, QH_compact.
Same preexisting immutable permuted host Q; KV/mask resident; targets preallocated.
One actual timer covers copy/transpose -> Q upload/completion -> graph replay /
device completion -> complete ordinary readback. No summing independent means.
Fresh serial references and two-host qualification per unique arm as above.
Verify ON for q4 and BOTH Q representations; a mode flag is not proof. Include
alternating-input replay checks to rule out stale capture. This is repeated
synthetic Q materialization, not original model Q production or decoder latency.
Record resident graph interval as secondary; conversion transaction is primary.

## Order, budgets, freeze
Each panel has four cells x eight blocks x four arms =128 timed hosts.
Two separately started sessions of four blocks, fixed four-arm Williams orders
(0,1,3,2),(1,2,0,3),(2,3,1,0), rotated per cell. Both panels occur in each session;
reverse panel order in session 2, deterministic shuffled cells. Do not treat two
sessions as independent devices/dates. Each host:8 warmups+30 measurements.
Plan generates order, not a GPU launcher. It must be bound into the native
adapter's pre-execution manifest along with all source/input/reference identities.

Maximum default core:40 reference hosts/calls +48 qualification hosts/1632 calls
+256 timed hosts/9728 calls =344 hosts /11400 explicit graph calls.
B0 references16;T0 references24. Qualification hosts24 per panel.
Trace qualification hosts when possible: six B0 unique value0 signatures,
each in both fresh qualification hosts (12 attempts), plus six T0 unique value0
signatures in one host each =18 attempts. Budget at most24 profiled attempts INCLUDING failures,
not an obligation to spend them. Up to8 extra capability hosts, each <=16 calls;
up to6 extra diagnostic hosts, each <=34 calls (including any padded serial
investigation). Total ceiling358 native hosts /11732 explicit graph calls.
Profiled qualification remains qualification and is never clean timing.

One GPU worker, six hours total, reserve last45min for closure; native timeout120s,
owned memory <=8GiB, raw/output <=8GiB, require >=10GiB disk headroom. Reuse
parent safe supervisor/resource checks, adapting paths and identities. Tool/source
preparation <=60min; trace onboarding <=45min within this total. Reaching a cap
means partial closure, not extra repetitions. No repeated telemetry-repair loop:
invalid clock channels remain UNKNOWN; do not normalize frequency from them.

Before first GPU call commit implementation and freeze UUID/source/runtime/input
plan. Reference collection precedes qualification. Commit/freeze admission and
clean schedule before timed collection. A tool failure before any graph may be
repaired under remaining capability budget with a new freeze and retained failure;
no scientific repeat after observed timing. Any formal failure is retained, excludes
its relevant comparison block, and is not replaced. No speed-based outlier removal.

## Evidence and analysis
Actual capture/end/instantiate/launch and formal replay must be verified per
unique shape/stride/operator/runtime signature, including padded paths and q4.
Clean processes do not load the tracer; bind them to matching qualified signatures
and immutable runtime, explicitly distinguishing inferred mode from directly
traced hosts. Record actual kernels, copies, stream/correlation IDs and source
link evidence. Do not pool instrumented timing with clean timing. Report capture,
allocation, packing, full KV upload and memory separately; resident K/V padding
is not free in an application and no reuse break-even is claimed without a measured
common transaction. Kernel count is not traffic, occupancy, busy time or throughput.

Use host means, paired log ratios and absolute differences by cell/block. Report
native_A/native_B (or QB_A/QB_B), candidates versus BOTH controls; no choosing the
faster baseline. Average values equally for geometry-level summaries. Resample
whole blocks stratified within actual session, keeping arms and values together;
report intervals, per-value/per-session signs, leave-one-block-out, coverage and
all exclusions. 30 inner calls are technical repeats. No grand speedup pooling
B0 and T0. Upstream PR122 analyzer can be adapted but panel/arm semantics must
change; old four-arm names must not silently mislabel these experiments.

Declare a PRACTICAL_CANDIDATE only if both values and sessions support the
same direction against BOTH controls, paired block interval is below1, and
saving exceeds max(2% baseline,1us, corresponding absolute A/A scale).
This is a prospective screening rule, not a universal precision certificate;
report unresolved and discordant outcomes. At least all8 complete blocks needed
for this label. With incomplete blocks provide descriptive results only. Native
A/A scale = median absolute paired host-mean difference for the same geometry,
with block values averaged equally; keep per-value A/A visible too.

## Decision and required delivery
- Exact padding failure: representation infeasible under this reference contract;
  report mismatch extent/max error diagnostically, do not label incorrect speedup.
- Padding qualifies and changes path/cost: software representation opportunity;
  charge setup/repacking before any deployment claim; still SOFTWARE_FIRST/HOLD.
- Padding qualifies but path unchanged: limits the shape-dispatch hypothesis.
- Trace/source unavailable: lower claim level, preserve numerical/cost findings.
- T0 tiny/no advantage: close QH optimization branch for these inputs, no more
  precision hunting. Unverified ON: mark T0 incomplete, no OFF substitution.
- Hardware design requires later physical bottleneck AND system critical-path
  evidence relative to best qualified software; this study alone cannot grant GO.

Commit RESULT.md, generated coverage/host/pair tables, source-predicate notes,
mode-evidence and admission manifests, all failure receipts and cost boundaries.
Keep raw locally, hash inventory and fresh restore/reanalysis; distinguish local
verification from remote artifact verification and external review. Permanently
close UUID; retain Draft; no main/merge, paper edits, B570 changes, actor/decoder,
new models, selector training, RTL or FPGA. Report blockers and negative results
as completed research outcomes rather than trying indefinitely to obtain a win.

## Primary methodological references
NVIDIA CUDA Programming Guide, CUDA Graphs:
https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/cuda-graphs.html
Definition/instantiation/replay are distinct; changing graph topology can require
re-instantiation. This motivates actual replay evidence and separate setup costs.
PR122 RESULT.md and results/TRACE_SUMMARY.csv at the pinned parent provide the
local empirical motivation; no claim of novel CUDA Graphs or novel padding.
