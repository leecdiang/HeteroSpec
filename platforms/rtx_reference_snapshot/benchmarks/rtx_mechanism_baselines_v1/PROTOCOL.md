# Mechanism protocol: graph submission, length boundary and input representation

## Research questions and prior evidence

Pinned PR121: `d82ec4097adfa032886040e075e71e41cfeb5855`.
Read its RESULT.md, collector.cpp, collect.py, hs113_graph.h, graph_base.h,
RUNTIME_MANIFEST.json, source/data contracts and repository CONTRIBUTING.md.
Reuse numerical DLLs, graph builder and independently owned persistent inputs.
Create a new entrypoint and UUID; never resume a sealed PR121/120 run.

From PR121 HOSTS.csv, q2 ordinary completed host-graph means in microseconds:

| keys | PQ | QB_A | QH_C |
|---:|---:|---:|---:|
| 1023 | 212.3673 | 139.8775 | 152.0467 |
| 1024 | 78.3548 | 59.9065 | 71.4135 |
| 1025 | 212.7213 | 140.9229 | 152.0750 |

At q2/256, permuted→compact Q changes QB_A 50.1485→49.9004 and QH_C
60.9313→50.5823. These are observed means, not isolated kernel or packing times.
The earlier all-QB holdout rule supplied no advantage over fixed QB. Do not fit
another selector in this task or claim that these selected boundaries are blind
holdout. This is a prospectively controlled followup of known observations.

H1: part of completed cost is submission overhead removable with graph replay.
H2: the 1024 discontinuity follows a backend execution-path change.
H3: QH's deficit includes a representation-conversion cost that can be reduced
by a compatible input layout, subject to charging upstream conversion.
These are hypotheses, not findings. They can be false, partially supported or
unresolved. Physical traffic, kernel identity and clock normalization require
actual evidence. Fewer graph nodes are not proof of fewer kernels.

## C0: bounded capability and telemetry check

Before GPU work, inspect existing compiler/runtime/source identities and available
profiler tools, including their local help and device/driver compatibility. Use
already available facilities; no compulsory OS repair, driver update, admin clock
locking, large package installation or new supervision framework. Initial setup
cap45minutes; routine repairs count against the six-hour total.

Inspect PR121's saved telemetry and the collector's exact query/CSV parser. New
queries belong to this new UUID. Check argument/column alignment, units, locale,
multiple-device handling, executable identity and raw output. Compare a bounded
set of idle and task-active readings with another available source (e.g. NVML or
profiler) when feasible. Record versions and shared provenance: two interfaces to
one driver are not independent physical calibration. Do not arbitrarily divide
implausible clock values by10/1000 or invent a root cause. Invalid channels remain
UNKNOWN; do not use them in a gate or frequency-normalized model.

Preserve PR121's device identity, AC, reported utilization/temperature/free-memory
quiet checks when those channels remain credible. Freeze any replacement gate
before timing. Endpoint quietness is not continuous exclusivity. If another
channel is suspect, label it rather than pretending it establishes isolation;
uncertain device identity/resources or unsafe cleanup stops affected GPU work.
Do not retroactively alter historical eligibility. No per-latency exclusions.

Graph modes:

- OFF: inherited graph-disabled configuration, explicitly recorded.
- ON: backend graph capture/instantiation/replay actually observed, with a graph
  signature bound to shapes/strides/op parameters/layout/runtime and completion.
  Removing an environment variable, seeing a success exit, or seeing a GGML DAG
  is insufficient. Use actual CUDA API/graph trace or trustworthy backend counters.
  Retain evidence of launches, capture/rebuild/update counts and steady replay.
- REQUESTED_BUT_UNVERIFIED / UNSUPPORTED / NUMERICAL_FAILURE: reported outcomes,
  never relabeled ON or pooled into successful ON costs.

Use at most12 extra native capability hosts, each at most64 graph evaluations.
GPU capability probes wait for the matching fresh serial references from R0;
CPU/tool/telemetry preparation can precede reference collection.
Qualify two-realization alternating input updates on q2-k256 for QB and QH_C in
the same persistent buffers, against the matching serial references. This checks
stale captured data/pointers; it is not changing-request/KV/decoder qualification.
Record every update and full output. Do not put input mutation in the main fixed-
input timing loop. Capability calls are separate from formal measurements.

ON activation proof must cover each distinct formal graph signature; signatures
may cover both data realizations only with explicit shape/stride/op identity and
qualified value updates, not an assumed correspondence. A qualification host may
also be traced; count that host once. Trace tools may be used solely for activation
proof even if detailed counters are unavailable. Evidence collection can be moved
to qualification to avoid perturbing clean timing. No unverified fallback inside
a timed ON cell. If mixed replay/fallback occurs, report it as unverified mode.

If ON requires new numerical DLLs/backend rebuild, do not quietly replace the
pinned baseline. Preserve OFF with original runtime and report ON unavailable in
the primary comparison. A rebuilt-runtime experiment is a separately frozen,
requalified, optional cohort only if it fits the original budget; it is not needed
to finish this PR. No bypass of old execution guards.

Choose `dual` or `off-only` before formal timing. If only some ON cells qualify,
keep dual-plan missingness and analyze matched admitted cells explicitly; no
success-only full-panel claim. A changed plan is a new identity: retain old pilot/
qualification receipts with their original binding. Exact preexisting qualification
receipts may be referenced via explicit provenance, never relabeled to new task IDs.

## R0: inputs, references and qualification

Core geometries: q2-k1023, q2-k1024, q2-k1025, q2-k256, q2-compact and q1-short.
Each uses PR121 value realization0/1 and the original coordinate_hash_v1 seed,
full head/channel/key extents, F32 Q/mask, F16 K/V, scale and exact strides. All
q2 inputs use d128/Hq32/Hkv8/causal; q1-short has128keys. This deliberate subset
does not establish q4/long-context/model generality. Preserve original input bytes
from verified old artifacts or reconstruct and check them against the committed
input identities. Never substitute new random tensors under old case names.

Make two fresh serial q1 captures per query, graph OFF, retaining full KV and the
correct mask column. Compare both complete outputs and concatenate in ordinary
query order. Core44 reference hosts. No tolerance relaxation. The same canonical
reference serves OFF and ON and every mapping. It is pinned-stack empirical byte
equivalence on these fixtures, not proof over all floating-point inputs.

For each admitted mode, qualify all12inputs×PQ/QB/QH_C in two fresh hosts, each
2warmups+32measured calls. H1-style preallocated output/record storage, every output
occurrence retained, input before/after equality, full CUDA placement, imported
numeric modules, computation status and synchronization verified. Check actual
graph signature and mode, not just requested flags. Same QB code for both labels.
Failures isolate cells and remain reported; runtime/source changes require new
affected qualification. Commit implementation before formal execution.

## B0: clean graph-mode and geometry contrasts

Each input/block contains an OFF sub-block and, when admitted, an ON sub-block.
Each sub-block has PQ, QB_A, QH_C, QB_B in a four-arm Williams order. Within each
four-block cycle every arm occupies each position and directed adjacent pair once.
The planner balances OFF-first/ON-first twice each per input/cycle and randomizes
input order. Two separately started sessions supply blocks0–3 and4–7.
This is nested balance, not balance of every possible cross-mode arm transition
or control of arbitrary thermal history. Record actual execution order/times.

One fresh host per task,8warmups+30measurements. Capture/instantiate during warmup;
record those costs separately. ON's formal measurements must be steady replay
under its declared signature. If the backend cannot settle within8warmups, declare
a prospective uniform warmup amendment and regenerate the plan before formal
timing; never discard slow formal calls or silently charge an extra warmup budget.
All task-owned graph evaluations, including capture setup, count toward budgets.

Primary view remains QPC [compute entry,completed device sync]. Retain compute
return, explicit sync, readback, cold allocation, source read, preparation/upload,
capture/instantiate and total host wall costs. H1 file writes/JSON stay outside
replay; exact per-call checks/readbacks remain. Separate steady resident-call and
first-use/setup views. Do not substitute device event time for this view.

Primary contrasts: ON/OFF for QB_A with QB_B sensitivity, and QB/QH_C within
each mode. Secondary PQ/QB. Report all12input contrasts and six geometries; q1
stays a common-arithmetic control. Factor edges are1023→1024,1024→1025 and
permuted→compact at256. Report absolute times for ALL mappings, not only ratios.
Changing key extent also changes the causal frontier; it is not a pure padding
or dispatch intervention. No padding/rounding experiment is required this round.

`analyze.py` provides per-case/per-geometry ratios and differences, matched
ON/OFF contrasts, same-QB controls and factor ratio-of-ratios. It resamples blocks
within sessions; two sessions/two value patterns are not independent populations.
Intervals are descriptive. Require consistent directions in both value patterns
and sessions, alternate-QB support and effects beyond same-unit A/A variation plus
the prior2%/1us practical scale before calling a small mapping difference robust.
This remains an empirical guard, not a significance/equivalence certificate.
The helper deliberately makes no automatic winner or hardware decision.

For mode effects, inspect A/A in BOTH modes and the paired change in A/A; for
factor effects, inspect the matching A/A factor contrast. Publish every block and
leave-one-block-out sensitivity. Missing arms remove that paired cell, not the
record of its attempted execution. Partial cycles have descriptive scope. Never
compare a mean effect against single-call noise or pool different runtime cohorts.

## M0: bounded mechanism traces

At most24 profiled native hosts total (including traced qualification hosts),
at most64 evaluations per host,45minutes collector setup. Trace OFF/ON signatures
needed for admission, then prioritize q2/1023,1024,1025 and permuted/compact256
with QB/QH_C; PQ at the length boundary provides a common-path comparator.
Choose pairs structurally, not by the most favorable individual latency. If budget
only covers a subset, declare it. No mandatory complete profiler-counter matrix.

First aim for a CPU/CUDA timeline: submission/capture/graph launches, actual
kernels, copies, execution gaps and synchronization. Optional deeper metrics only
when supported and necessary. Do not require Nsight Compute to finish a timeline
study; do not call a timeline a bandwidth/occupancy measurement. All profiled
outputs must qualify. Profiler timing is not pooled into clean latency estimates.

Use actual backend source tied to the binary or correlated trace to explain a
dispatch boundary. A candidate explanation without the pinned source/trace is a
hypothesis. Stable differences with no trace are a valid limited delivery. If a
trace shows a removable launch/packing cost, pursue that software explanation
before assigning it to a hardware bottleneck. Missing trustworthy clocks restrict
frequency attribution, not automatically every completed-cost observation.

## P0: optional integrated Q conversion/update transaction

Proceed only with a frozen producer decision and remaining budget. Four logical
inputs: q2/q4-k256, each original value0/1. q2 references come from R0; q4 needs
16 fresh serial reference hosts (4queries×2captures×2values). Complete two-host
qualification for each of four pipelines (32 hosts), then eight balanced blocks
(128 hosts). Prefer verified ON; use OFF if ON unavailable on this domain and
freeze that choice before producer timing. The default dual planner uses ON;
if only P0 needs OFF, prospectively amend its mode and plan hash, preserve B0's
original plan and analyze them separately. Do not relabel B0 receipts.

All pipelines start from the SAME preexisting immutable, model-style permuted
host Q and resident full KV/mask. Use preallocated destination Q buffers:

| Arm | Materialization inside timer | Mapping |
|---|---|---|
| QB_permuted | copy complete Q into permuted destination | QB |
| QH_permuted | same copy | QH_C with its internal packing |
| QB_compact | actual transpose/pack into compact destination | QB |
| QH_compact | same transpose/pack | QH_C with compact Q |

Measure a single native interval: CPU copy/transpose → Q upload/completion as
required → graph compute/completion → ordinary readback. Preserve sub-boundaries,
exact physical Q bytes, logical equivalence, persistent input safety, outputs and
readback each call. Do not add separately measured CPU/GPU means and call that an
integrated result. No per-call file writes, allocation or source generation hidden
inside one arm only. Full KV/mask setup and cold allocations remain separately
charged; the stated workload assumes resident KV/mask. Original Q production by
a model is outside the boundary and explicitly UNKNOWN.

This evaluates whether explicit conversion pays when charged, not whether a real
Q producer can emit compact storage for free. Direct-to-compact model production
and a natural request experiment are deferred until an actual producer exists.
Do not replace the common input with synthetic generator timing as a model proxy.

Primary P0 comparison is QH_compact/QH_permuted. QB_compact/QB_permuted measures
the conversion tradeoff on the stronger mapping; report both mapping comparisons.
There is no duplicate identical arm in this four-pipeline panel, so P0 does not
inherit B0's A/A precision certificate. Its results remain descriptive, with all
value/session directions and practical margins; fine effects may stay unresolved.

## Decisions, budget and closure

Six hours elapsed including implementation, last45minutes for closure; one GPU
worker,8GiB task-owned memory/new storage,10GiB free disk headroom, native120s
timeout. Existing known-safe supervisor and bounded cleanup are sufficient.
Capability extra-host cap12 and profiled-host cap24 are separate ceilings, not
entitlements; do not double-count hosts serving both qualification and trace.
Full dual planned matrix1132hosts/40092calls; extra probes at their worst-case
ceilings add at most36hosts/2304calls. Record actual counts, including any backend
setup evaluations. Do not claim these are kernel counts or whole-machine ledgers.

Priority: reference/qualification and B0, signature evidence, focused M0, optional
P0. A complete first four-block cycle is a valid partial delivery if time expires.
Ordinary path/build/API/export repairs can be handled autonomously, with short
amendments. Changed scientific conditions require a new freeze/affected
qualification, not repeated author permission. No best-of-retries. A damaged
timing block is preserved and excluded by a non-latency rule; no mandatory rerun.
Partial unsupported modes and unavailable counters are results, not reasons to
start an infrastructure project. Numerical errors/unsafe cleanup stop affected
GPU work; correctness is never relaxed to finish a matrix.

Keep compact generated tables, source, actual commands, capability/mode evidence
summary, source/runtime identities, failures, real counts and RESULT.md in Git.
Raw traces/outputs/ticks stay local under CONTRIBUTING, with hashes/location and
fresh CPU restore/recomputation when feasible. CAS+occurrences may replace massive
hardlink fanout. Do not claim external review or remote raw authentication.
Update this Draft PR with actual results, push and stop; no merge/release.

Admissible endpoints: SOFTWARE_SUBMISSION_EFFECT, REPRESENTATION_COST_EFFECT,
BACKEND_BOUNDARY_OBSERVED, MECHANISM_UNRESOLVED, GRAPH_MODE_UNAVAILABLE, or
NO_REMAINING_USEFUL_SOFTWARE_EFFECT. None independently establishes accelerator
benefit. Hardware entry requires a physical bottleneck remaining after strong
software baselines plus system critical-path relevance, neither guaranteed here.

## Research positioning and primary sources

- NVIDIA CUDA Graphs documentation explains setup amortization and reduced CPU
  launch costs: https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/cuda-graphs.html
- Nsight Systems documentation describes tracing capabilities; inspect the actual
  installed version/permissions: https://docs.nvidia.com/nsight-systems/UserGuide/index.html
- FlashInfer (MLSys2025), especially Appendix A, already fuses query heads with
  query length for GQA reuse: https://arxiv.org/html/2501.01005v2

Do not claim head/query fusion itself is new. The research target is the measured
feasible/cost boundary under a declared reference contract. External fused engines
can be contextual baselines later, but cannot silently replace byte-equivalence
with a looser tolerance; failure to meet this contract also does not mean their
mathematical algorithm is incorrect. No new novelty claim follows from this PR's
design alone. Sources consulted2026-10-18.
