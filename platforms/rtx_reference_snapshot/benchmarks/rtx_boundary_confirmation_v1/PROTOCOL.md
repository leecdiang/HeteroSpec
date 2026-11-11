# Research protocol: measured boundaries with concurrent null controls

## 1. Questions and inherited evidence

Pinned parent: PR120 `c6eb66368bc876332afe82f9df5ea51fe0b4b5ec`.
Relevant source directory: `benchmarks/rtx_reference_envelope_v2/`.
Read its RESULT.md, native.cpp, hs113_graph.h, D0_FINDINGS.json and CONTRIBUTING.md.

PR120's persistent external input buffers fixed the observed K/V storage reuse.
Use that lifecycle for every arm here. Preserve the numerical DLLs, precision,
graph-capture setting, complete geometry, ordinary reference definition and required
packing/restoration costs. Requalify a changed host/observer; do not rerun old UUIDs.

Primary questions:

- Can a selected host measurement method distinguish a useful mapping difference
  from same-QB execution variation at the **same aggregation unit**?
- Does QB versus QH_C change reliably across length, GQA, storage, mask or dimension
  contrasts when only that declared factor changes?
- Do those effects survive a second acquisition session and, optionally, new q3
  geometries? What remaining mechanism evidence would justify hardware work?

Primary pair: QB_A/QH_C, resident completed graph, q2/q4. Secondary: PQ/QB_A.
QB_B is an independently executed instance of exactly QB, never a new implementation.
Retain QB_A/QB_B and recompute both primary/secondary pairs using QB_B. No choosing
the faster QB slot. No equality tolerance can repair a byte-reference failure.

## 2. Preparation and permissions

Publishing the PR does not launch RTX. When the author forwards RTX_PROMPT.md, the
executor may implement and advance these stages within this scoped budget without
asking permission at every routine repair or stage. Platform restrictions still
apply. Old source/approvals/terminal runs are immutable. Use a fresh configurable
UUID root and copy/import only necessary pinned implementation components.

Read the generated plan before implementation. It describes logical tasks, not
actual filesystem inputs. Resolve source, compiler, exact numerical modules,
input/reference hashes, device/backend and source/build identities in a separate
execution freeze. Record numerical qualification independently from timing status.
Commit correctness-critical implementation before formal execution. Test actual
mapping/alias flags, source/hash binding, negative outputs, clocks and cleanup.

Development may fix Python/tool interfaces, paths, compilation, buffered evidence,
timeouts and serialization. Keep a short amendment record. No full-machine process
ledger, dedicated new supervision framework, remote raw upload or mandatory external
review is a prerequisite. Do not invent unavailable observations. A new numerical
stack is a separate cohort and loses historical byte-reproduction claims.

## 3. Q0: references and numerical qualification

Create inputs from DATA_AND_RECEIPTS.md; freeze their exact bytes before collection.
For each query of each new input, capture serial q1 execution in two independent
fresh processes with the original full KV, query position/mask and precision.
Verify both captures, concatenate in declared ordinary order, and retain the full
reference. A capture against no reference is not a successful candidate comparison.
Use single-visible-key/GQA/address CPU oracles to check semantic indexing, and retain
the expected scale and op parameters. Full FP64 is optional mathematical diagnosis,
not the deployed byte reference.

For H1, qualify all 52 core inputs × PQ/QB/QH_C × two new processes × (2 warmup+
32 further calls). Both QB labels use the same host code; no alternate arithmetic
or silent layout-dependent paths. H0 needs the eight pilot anchors × two QB hosts
with the same repeated checks. Optional holdout references/qualification wait until
the rule is frozen, so its outputs cannot leak into method/prediction selection.

Every observed output and input-before/after must match full bytes, be correctly
sized/ordered, and have actual device placement and completed synchronization.
Use PR120's owned-input buffers, not re-upload as a way to hide destructive reuse.
All full heads, channels, keys and original logical masks remain present. CPU oracle
success alone does not establish CUDA numerical qualification.

Any failure isolates that input/mapping/method. Continue independent qualified
work while preserving missingness; uncertain cleanup or global device corruption
stops GPU execution. A change to mapping/host semantics returns affected cells to
qualification. All formal calls still check correctness; qualification is not a
license to stop observing later failures.

## 4. A0: same-QB pilot and measurement-method selection

Eight manifest anchors: q1 short/long, q2/q4 at 256 and1024 keys, and d64 q2/q4 at
256 keys; realization0. For H0 and H1, six paired blocks, each with QB_A and QB_B
in balanced AB/BA order. Methods are interleaved by the planner. Default eight
warmups and30 measured calls. All input/reference bytes are identical within a pair.

H0 is the PR120 checked-replay observer: retain its per-call file writes and timing
boundary as a declared legacy condition. H1 moves per-call file creation/JSON work
out of the timed replay loop, preallocates output/receipt storage and retains every
output occurrence. Readback and byte checks stay outside graph timing. This tests
an observer change, not an arithmetic optimization. See exact boundaries below.

Both methods must be numerically qualified. Prefer the buffered H1 if qualification
passes and its A/A data support its use; document any choice of H0 using only A/A,
implementation feasibility and resource evidence. Do not select a method because
it makes QH_C win or maximizes any mapping speedup. A/A mean, block contrasts,
per-anchor spread and session/position information all matter; a near-zero pooled
mean can hide opposite biases. Do not certify 2% resolution from a nonsignificant
A/A test or from a q1 average near1.

If H0 is selected, generate a plan with `--qualification-method H0` and qualify
every required input/layout under H0 before confirmation. Anchor-only H0 qualification
does not transfer to the full panel. Existing exact qualifying receipts may be
referenced explicitly instead of rerunning them; never relabel old task identities.
Extra fallback work counts against the same global budget and can leave B0 partial.

Record METHOD_DECISION.json before B0: selected method, host/policy hashes,
pilot plan/receipt IDs, warmup/sample count, reasons, known limitations and smallest
effect scale supported by evidence. Default30 calls can become50 based on pilot
variance/runtime. Generate a new plan; retain the original30-call pilot bound to
its original plan, and analyze the two plans separately. No relabeling of receipts.
Do not repeatedly tune until a favorable pilot appears. One bounded observer repair
and one new pilot within90minutes are allowed; preserve both. If resolution remains
coarse, proceed once to B0 with that limitation or publish A0 only if time expires.

An H2 paired persistent-worker/burst experiment is not required. If a concrete
remaining issue warrants it, first amend tasks/process counts, qualify its new
lifecycle and freeze it as a separate method. Never mix H0/H1/H2 timings. Do not
avoid per-call correctness checks merely to obtain a favorable timing boundary.

## 5. B0: paired-factor confirmation with A/A in every geometry

The planner fixes 24 q2/q4 geometries plus two q1 controls, each with two data
realizations. For q2 and q4 separately:

| Factor | Conditions, other factors at d128/Hq32/Hkv8/permuted-Q/causal |
|---|---|
| Key extent/visible-length boundary | 255,256,257 and1023,1024,1025 |
| GQA | Hkv1/8/32 at256 keys |
| Q storage | compact versus model-style permuted at256 keys |
| Mask | causal, irregular, single-visible at256 keys |
| Head dimension | d64 versus d128 at256 keys; each uses its declared conventional scale |

The supplied factor graph contains20 edges, each changing one declared factor.
Changing d also changes its conventional1/sqrt(d) scale, explicitly part of that
dimension condition. Changing key extent changes the causal frontier as specified;
do not interpret it as a pure kernel-dispatch intervention with everything else held
fixed. Storage pairs contain the same logical Q values, with different physical
bytes/strides. Hq remains32; no general claim about query-head count follows.

Four arms per input/block: PQ, QB_A, QH_C, QB_B. Eight acquisition blocks use two
complete four-row Williams cycles. In each cycle, every arm occupies each position
once and each ordered neighboring pair occurs once. Context order is seeded and
varies by block; the planner also rotates row assignment across inputs. This
balances immediate carryover, not arbitrary long thermal histories or interactions.

Blocks0–3 and4–7 use separately started acquisition sessions. Record actual start/end,
power mode, clock observations and session IDs; no mandatory reboot or invented
independent date. If only one session is feasible, preserve it and report descriptive
scope. Stage/collector runtime must remain fixed. A block affected by an independently
detected global environment failure is retained and excluded; do not drop slow
samples based on latency. An incomplete cycle is not still a fully balanced design.
Finish never-started tasks within budget after a pure CPU retention repair, without
repeating completed GPU tasks or changing their eligibility from their measured values.

The selected method is the same for all four arms. Use a fresh host per task by
default. Host startup/allocation are outside resident_graph, but record them and do
not hide these deployment costs. This is a measured operator boundary, not E2 speedup.

## 6. Analysis and decision

The supplied analyzer uses host means, paired by input/block, then equal value-
realization weights within a geometry, then equal geometry weights for the planned
panel. Inner calls and two value realizations do not become extra independent
acquisition blocks. Bootstrap resamples whole blocks within actual session strata;
with only two sessions, intervals remain descriptive. Report all block contrasts,
leave-one-block-out sensitivity, missingness, position/order diagnostics and effects
per value realization. Do not pool source/runtime/method revisions.

Compare A/A and mapping effects at the same level: input, geometry or full panel.
The analyzer's conservative screen asks whether BOTH QB_A and QB_B versions of a
mapping contrast clear the 2% and1us practical thresholds plus the corresponding
same-unit A/A interval envelope. This is a **heuristic, not a calibrated significance
or equivalence test**. It is not a proof of no effect when unresolved. Noise at an
individual-call level must not be used as the threshold for an averaged estimator.

Eight complete blocks and at least two actual sessions are required for this
screen; smaller observations are descriptive. Full-panel summaries require the
full planned panel in each summarized block, so one missing input is not silently
replaced by the favorable surviving population. Per-input/geometry results remain
available when a panel aggregate is unavailable. Report expected/observed scope.

Factor edges report differences in mapping log-cost contrasts: for example,
log(QB/QH_C) at257 minus the corresponding quantity at256, using matching blocks
and averaging the two realizations. These are exploratory multiple comparisons;
do not present the smallest p-value as a universal geometry rule. Require consistent
direction across the two value patterns and the two session cycles before treating
a local reversal as a plausible boundary. Same-QB position effects and q1 false
differences are reasons for caution, not observations to discard.

Possible outcomes: STABLE_QB_ADVANTAGE, STABLE_LOCAL_QH_ADVANTAGE,
RESOLUTION_LIMITED, NUMERICAL_BOUNDARY, or NO_USEFUL_GENERAL_RULE. No requirement
that QH wins somewhere. Timing alone never changes HARDWARE_HOLD to an accelerator
claim. A stable software result can be the correct endpoint.

## 7. Optional prospective prediction check

The six optional geometries use q3, lengths511/512/513, Hkv4 or8, d128/Hq32,
permuted Q and causal masks, two new value realizations. Their geometry is public
but their output/timing must remain unopened until a rule is frozen. Do not call
confirmation geometries blind holdout simply because values were regenerated.

Freeze a simple rule from B0 or explicitly predict fixed QB; record features,
fallback, cost view, prediction for every optional cell, allowed preparation and
lookup costs, and success criteria before any optional reference/candidate output.
The same eight-block/four-arm design supplies fixed-PQ, fixed-QB, fixed-QH and oracle
comparisons. Oracle selection after measurement is an unattainable envelope, not
a baseline implementation. Score the frozen rule after observation, retaining
wrong predictions and costs. No runtime selector integration or decoder claim.

This extension is optional within the original dispatch budget and may be left
UNSTARTED. No second rule trained on its errors may be called the same holdout.

## 8. Optional mechanism work and hardware decision

For a stable measured contrast, inspect the actual graph and use an already
available compatible profiler in separate hosts, at most12 hosts /30minutes of
collector setup. Choose a small matched pair by prespecified structural contrast
or report the posthoc selection. Check profiled output correctness. Record kernel
identity/counts/durations/copies/traffic only when really observed; graph nodes and
logical tensor bytes are not substitutes. Preserve clean and profiled samples
separately. Profiler unavailability does not block the cost result.

Packing/storage contrasts can identify a useful software hypothesis. Removing a
CONT node by changing Q storage changes required preparation; charge that work in
a separate input-inclusive view. Do not claim kernel causality from elapsed time
alone. No new abstract architecture sweep is required in this round. A later hardware
candidate needs a concrete bottleneck, competitive software/dataflow baselines,
resource charging, a numerical contract and system relevance. B570 can later test
the same constraints independently; no B570 task is dispatched here.

## 9. Budget, closure and flexibility

Default eight hours elapsed, final hour reserved for delivery; one GPU worker,
8GiB task-owned RAM and new storage,10GiB disk headroom, at least max(1GiB,10%) free
device memory,120s native timeout. Suggested ceilings: preparation/qualification
2h, A/A implementation/pilot90min, B0 2h, optional holdout60min; they are not additive
entitlements. Collector time and development repairs count inside the global cap.
Keep task-owned process cleanup bounded with the existing reliable supervisor.
Record actual counts and resources; do not invent a complete OS ledger.

Use PR120's quiet-window practice, with actual power scheme and raw SM-clock/power
observations at both session/block boundaries. A low-rate monitor outside timed
windows is optional and must be identical for all arms. Do not require a laptop to
support locked clocks or privileged clock controls. Endpoint telemetry cannot prove
continuous exclusivity; record this limit. Wait up to10min for a quiet window using
the established spaced samples. If timing remains unavailable, finish numerical/
CPU work and report the blocked scope instead of repairing unrelated system services.

Retain all attempts, exclusions and exact source freezes. Runtime changes invalidate
affected measurements; pure transport/format fixes after collection do not require
GPU reruns. Within budget, one replacement full four-block cycle is allowed only
for a prospectively recorded non-latency-based invalidation; the original remains
reported. Never rerun just favorable or failed candidate points to optimize a ratio.
The plan generator currently emits the initial cycles; register a replacement as a
separate revised plan/cohort with unique IDs, not duplicate task IDs in one analysis.

Prefer CAS blobs plus occurrence records; avoid requiring100000 filesystem hardlinks.
A hardlink failure falls back to retained ordinary files within budget. Compact
JSON/CSV/source go to Git; raw/weights/credentials do not. Local-only raw is an honest
reproducibility limit, not a reason to withhold all results. Deliver real commands,
plan/freeze hashes, RESULT.md, numerical/cost coverage, A/A diagnostics, factor and
prediction tables, failures, raw locations/hashes and next bounded question. Do not
merge or release. Push the scoped source and compact results to this Draft PR.
This initial PR includes CPU helpers, not completed RTX results.
