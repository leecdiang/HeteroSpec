# RTX execution protocol: develop, qualify, measure, generalize

## A. Scope and degrees of freedom

This is a new prospective experiment, not a retry of a sealed PR118 run. Its
first execution begins only when the author dispatches RTX. That dispatch permits
routine implementation and progression below within the selected resource budget.
The design PR itself performs no GPU work. Use a fresh UUID run root, configurable
through `HETEROSPEC_*`; do not assume a particular drive, interpreter, Node API,
compiler location, or globally available profiler.

### Scientific invariants

- Preserve existing reference bytes, logical inputs/masks/GQA, arithmetic precision,
  and the definition of the compared workload. Any change creates a new explicitly
  labeled condition; it cannot silently qualify the old one.
- Record actual backend placement, input/output sizes and ordering, loaded numerical
  modules, completed synchronization, before/after input identity, and code identity.
  Descriptor support alone is not placement. Unknown evidence remains unknown.
- No tolerance may turn bitwise preservation failure into success. Expected valid
  MQ differences are scientific observations, not infrastructure failures.
- Retain every attempt, invalid sample, amendment and missing cell. No best-of-retry,
  success-only aggregate, overwritten raw run, or retrospectively selected threshold.
- Commit the implementation and analysis code before a formal block. Record both
  Git identity and actual runtime file hashes. Keep paths relative/configurable.

### Implementation freedoms

During preparation/D0, the executor may repair paths, quoting, builds, serialization,
bindings, process supervision, failure cleanup, data transport and evidence capture.
It may use the existing supported Python/C++/PowerShell execution facilities,
including a small new launcher, instead of inheriting the previous orchestration.
No mandated shared Node service, universal process ledger, exact archive layout,
fixed wrapper API, or new external review is a prerequisite for scientific progress.
Never bypass a platform access denial or fabricate missing observations.

Use a brief `AMENDMENTS.jsonl`: what changed, why, affected invariants, old/new
revision, evidence location, and whether prior formal data remain comparable.
Routine development changes need no author round trip. Do not cap revisions by an
arbitrary tiny count; cap elapsed work and retained resources instead.

During a formal block, do not change numerical/runtime/host source or policy. A
non-scientific transfer/reporting repair may occur afterward without recollecting
the original data. An execution or analysis defect invalidates the affected block;
preserve it, repair in development, freeze a new revision and start a new block.
Never combine versions without an explicit comparability argument. One replacement
formal block per affected stage is allowed within the dispatch budget; repeated
failure returns to diagnosis and reports partial status, rather than endless restarts.

Hardware/driver/runtime upgrades create a separately qualified cohort. The original
stack is preferred for continuity; unavailable exact binaries are not permission to
claim historical byte reproduction with substitute binaries. A new-stack cohort can
still answer prospective questions after its own reference is explicitly declared.

## B. Budget, readiness, and failure isolation

Default first dispatch: **8 hours elapsed**, including preparation and delivery;
reserve the final **1 hour** for analysis/publication. Per-stage maxima below are
ceilings, not promised allocations and not additive entitlement. Stop starting new
work at the earlier of a stage/global/resource limit. An unfinished matrix is PARTIAL.
Record actual scientific counts and stage elapsed time; do not pretend those are
complete OS lifetimes or all engineering cost.

| Stage | Default ceiling | Role |
|---|---:|---|
| P0 inventory/source/data preparation | 1 h | Resolve selected inputs and implementation paths |
| D0 lifecycle development/diagnosis | 2 h; 48 native hosts; 1600 graph evaluations | Find a stable, understood or explicitly mitigated execution path |
| N1 repeated clean qualification | 1 h; core 216 hosts / 7344 evaluations; up to 72 additional one-call diagnostic hosts | Validate the 24-context × three-layout panel |
| T1 core timing | 2 h; core 432 hosts / 16416 evaluations; optional profiling up to 36 hosts / 1368 evaluations | Six acquisition blocks of qualified comparisons |
| R1 extension | 1 h in first dispatch | Optional bounded subset; full design can continue in a later dispatch |
| M1 CPU model | 1 h in first dispatch | Optional minimum full-geometry baseline/headroom result |
| W1 whole requests | Deferred by default | Separate prospectively sized dispatch after costs justify it |
| Delivery | Reserve 1 h globally | Tables, failures, source and reproducible analysis |

Default new storage budget 8 GiB, including raw data, working copies and archives;
reserve 512 MiB for closure. Reuse immutable inputs rather than duplicating entire
old archives. Keep at least 10 GiB free disk headroom, or choose a smaller workload
before starting. Default task-owned host RAM cap 8 GiB; one GPU worker at a time.
Before each geometry, estimate memory and leave max(1 GiB, 10% device memory) free.
An OOM isolates that geometry; do not automatically shrink it and retain its label.
Timeout defaults: 120 s/native host, 600 s/build or archive command. Long contexts
may use a prospectively recorded longer timeout within the global budget.

Supervise task-owned subprocesses with an existing reliable facility (e.g. Windows
Job Object), timeouts and recorded exit status. If clean termination cannot be
established, stop new GPU work and report. Do not kill unrelated GPU/desktop jobs.
Missing global process telemetry is a reporting limitation, not a reason to rebuild
the whole supervision system. Keep stdout/stderr and fail-safe closure simple.

Record device, driver/runtime, clocks/power policy, AC, temperature, memory and
competing workload when observable. Numerical diagnosis may run under ordinary
desktop load if resources and completion are safe; flag load. Clean timing requires
a quiet, stable window. Default: two pre-block samples 5 s apart with utilization
≤5%, AC connected, temperature ≤55 C and sufficient free memory. Recheck up to
10 minutes with ≥30 s spacing, recording all samples; no busy-loop or favorable
sample erasure. If telemetry is unavailable, numerical work may proceed, while
timing is labeled environment-unqualified. These cutoffs are engineering controls,
not correctness theorems. A different policy must be fixed before the block and
reported as a separate condition; do not relax it after seeing speedups.

Unexpected incorrect reference/output/input mutation stops the affected clean
configuration and routes it to D0. Known unsupported mappings are marked UNSUPPORTED,
not retried or hidden. A failed candidate does not prevent measuring a qualified
baseline, but their pair has no eligible speed ratio. Backend/device corruption or
uncertain worker cleanup stops all GPU work. Profiler/transport/optional-model
failures block only the evidence that depends on them.

## C. P0: resolve dependencies and freeze the research questions

Read CONTRIBUTING.md and this directory. Resolve PR118's pinned parent, PR116
selected input/reference CAS and graph constructors, PR104 original 72-context
descriptors, and PR111 support conditions. Use SOURCES.json. Fetch only what is
needed. The PR110 model is needed for M1 critique/reuse, not for earlier stages.

Produce `INVENTORY.json`: available files, paths, hashes, source/build/compiler
identities, input/reference identities, tools, actual storage headroom and missing
dependencies. Read data, not just earlier summary tables, before using it. Resolve
the 24 context IDs from PR116's registration/reference index; do not reconstruct
them from a Cartesian product or invent layer/phase/q labels. Assert 24 unique
contexts: three families × two phases × q1..4 with the frozen layer selection.

Implement a minimal new entrypoint with separate `diagnose`, `qualify`, `time`,
`expand`, `model`, and `analyze` actions as applicable. Names/CLI are flexible; write
the exact working commands to `COMMANDS.md` before handoff. No GPU smoke hidden in
CPU build/tests. CPU tests should target risks: address mapping/aliasing, incorrect
output detection, timer units/sync, missingness, timeout cleanup and analysis signs.
Reuse valid existing tests. Do not add a large unrelated test bureaucracy.

## D. D0: isolate repeated-execution failure

Anchor: PR118 r2 first Qwen/layer0/prefill/q1/PQ graph. Warmup matched; next output
contained 512 where the reference began with 0.042083740234375. Inputs-after and
intermediate stages were missing. At q1 the builder selects a common arithmetic
path; this is not evidence against QB. `input()` already marks inputs: inspect
actual allocation/lifetimes rather than assuming a missing input flag.

Start by obtaining the exact inputs and a minimal replay of two completed graph
evaluations. Retain every attempt, including NOT_REPRODUCED. Capture input hashes,
ordinary bytes, tensor buffer/offset/span/alias metadata, graph identity, backend
ownership, synchronization return and completion. Capture inputs-after on failure
when the device remains safe; do not hang cleanup trying to rescue them. Missing
data remain missing. Hash host buffers before and after as well as device inputs.

Use these one-factor contrasts, conditional on what the first replay reveals:

| Arm | Change from baseline | Question |
|---|---|---|
| D0-A | Original clean ordinary-only graph; resident inputs; two calls then repeated calls | Does the failure reproduce? |
| D0-B | Re-upload the same exact inputs before each call | Is persistent input corruption/ownership involved? |
| D0-C | Allocate persistent non-aliased input/output storage, keeping arithmetic identical | Does allocator aliasing/lifetime matter? |
| D0-D | Rebuild/reallocate between calls in one process | Is graph/allocator reuse required? |
| D0-E | One call in each fresh process | Is process-resident state required? |
| D0-F | Separate diagnostic graph retaining QK/softmax/AV/intermediate witnesses | Where is the first observed divergence? |

These are planned contrasts, not six mandatory native APIs. Implement the closest
supported version, document actual changes and any confounding. D0-F can change
allocation and mask the bug; do not identify root cause from its success alone.
Do not run every arm if a decisive smaller experiment suffices. Start with three
fresh-process repetitions per selected arm and up to 34 calls/host, constrained
by the D0 ceiling. Add minimal targeted checks only while they discriminate live
hypotheses. Backend/compiler changes are separate conditions, not invisible fixes.

A plausible cause should be supported by an intervention and reversal when feasible.
If only a workaround is established, label MITIGATED_CAUSE_UNRESOLVED. A re-upload
or reallocation workaround changes the lifecycle/cost boundary: charge it and do
not report its numbers as the old resident-reuse timing. A stable workaround can
proceed to N1 under its explicitly declared lifecycle. If only fresh-process single
calls work, retain that result and measure that cost view; resident T1 is blocked.

Freeze the selected host implementation and lifecycle before N1. A default D0
readiness check is three fresh processes with 34 exact successful calls each on
the anchor. This is an engineering checkpoint, not proof for other geometries.

## E. N1: qualify the complete original tensor geometry

Core layouts: PQ, QB, QH_C. QH_D is a prespecified extension/contrast; MQ is a
known potentially non-preserving diagnostic, not a correctness-qualified timing
baseline unless it independently satisfies the declared contract in that cell.

Default matrix: **24 contexts × 3 layouts × 3 fresh processes = 216 hosts**.
Per host: two warmups and 32 further calls = 34, total **7344 calls**. This repeated
test is development/qualification evidence, not the clean performance result.
Preserve every full output occurrence (deduplication by hash is permitted), input
before/after checks and completion. Check ordinary output byte-for-byte against
the pinned PR116 ordinary reference, with exact shape/order and finite checks.
Use diagnostic companion graphs to compare QK/softmax/AV for each newly modified
arithmetic/mapping implementation; a diagnostic graph does not qualify clean reuse.

Use full Q/K/V/mask shapes, actual strides, head/channel counts, GQA and padding.
No head0/channel0/64-key crop. Validate every dependency's support and real device
placement. Record required CONT/REPEAT/copy/restoration nodes and allocation size.
Host-side materialization must be declared and charged. Initially retain
`GGML_CUDA_DISABLE_GRAPHS=1`; graph capture changes are optional separate conditions.

Classify each cell independently: QUALIFIED, NUMERICAL_MISMATCH, INPUT_MUTATION,
UNSUPPORTED, PLACEMENT_UNQUALIFIED, LIFECYCLE_FAILURE, MISSING_DEPENDENCY, UNSTARTED.
A finite candidate mismatch is a valid boundary finding, but disqualifies that
candidate's reference-preserving cost comparison. q1 is a common-path diagnostic,
not an arm that can be discarded when it contradicts an attractive result.

New-stack cohort: preserve historical reproduction as unavailable/failed; define
the prospective reference as serial one-query execution with original position,
mask and full KV semantics under that stack. Generate it independently of the
candidate and retain its repetitions. Do not call a newly generated reference a
reproduction of PR116. Report old-stack and new-stack cohorts separately.

## F. T1: trustworthy, matched cost comparisons

Prerequisite: a qualified lifecycle and eligible cells from N1. Cost views:

1. `resident_graph`: completed graph_compute + required completion synchronization.
   Required GPU packing, mask work and output restoration stay inside the graph.
2. `resident_call`: the above plus required ordinary output readback, as a separately
   reported view. Validation/hashing is outside this interval, but affects replay.
3. `input_inclusive`: actual CPU materialization + input upload + completed graph
   + required readback. In the default resident host, measure materialization/upload
   once and combine with the first warmup's completed call as a **first-call phase
   sum**; it supplies one observation per host, not 30 repeated input-inclusive
   samples or a natural request wall time. Charge re-upload/reallocation on every
   call whenever the chosen lifecycle requires it. A repeated input-inclusive
   cohort is a separate prospectively budgeted condition, not extra hidden calls.
4. `cold_setup`: initialization, graph construction and allocation separately; actual
   complete worker time includes checks/teardown and is not kernel latency.

No profiler, file write, validation or diagnostic stage readback inside the paid
graph interval. Use Windows QPC (ticks + frequency) for completed host latency.
CUDA events may add a device-stream view if supported and correctly ordered, but
cannot replace end-to-end completion. Do not subtract guessed observer overhead.
Report clock granularity/calibration and zero/nonpositive intervals as invalid.

Default: six acquisition blocks, each 24 contexts × 3 layouts = 72 fresh hosts.
Each host executes eight warmups then 30 timed calls, **432 hosts / 16416 calls**.
All warmups and measured ordinary outputs must be exact, with comparisons outside
the paid window and inputs checked before/after. This is checked resident replay;
readbacks may perturb cache residency. A separately qualified burst without per-call
readback is optional and must not be silently mixed with this primary view.

Each context sees all six permutations of PQ/QB/QH_C once across the six blocks.
Seed and record context ordering; rotate or randomize it by block. No layout is
always first. Pair by context, block, lifecycle and cost view. A missing arm yields
a missing pair; retain other valid data. Spread blocks across at least two machine
sessions where feasible, recording actual times; six loops are not six independent
days. Do not run profiler and timing concurrently on the GPU.

Pilot length/timer sanity may adjust the number of calls once **before** formal
blocks, with a count/resource recalculation and reason. Defaults above define the
first plan, not a reason to abandon work over a small timing-resolution issue.
Do not adapt sample count based on favorable/unfavorable candidate results.

Comparisons of resident_graph require the same declared lifecycle. If one mapping
needs extra transfers/reallocation to remain correct, also compare the actual
required-call costs with those operations charged; an attractive graph-only ratio
does not establish a deployment gain. Do not generate uncharged extra input-inclusive
or profile calls. Update planned counts before any optional cohort starts.

### Estimands and analysis

- Primary: `T_QB / T_QH_C` for qualified q2..4, resident_graph. Secondary:
  `T_PQ / T_QB`; other cost views and strata explicitly labeled. Ratio >1 favors
  denominator. Report absolute microseconds as well as ratios.
- Raw calls → host mean/median/p95/max → paired context/block contrasts. Within-host
  calls are technical repetitions. Aggregate with equal context weights, then equal
  block weights; use geometric mean ratios/log contrasts and arithmetic differences.
- Publish every context, q1 control, family/phase/q stratum, regression and missing
  pair. Provide complete-case aggregate coverage and a full planned-panel status;
  never imply missing failed contexts share the observed speedup.
- Default practical screen: geometric ratio >1.02 **and** mean improvement >1 µs,
  with repeat/block consistency shown. It is a decision heuristic, not significance
  or an accuracy bound. A lower uncertainty bound above the screen is stronger
  evidence; otherwise label borderline/inconclusive. Never alter the screen post hoc.
- With six blocks, report paired block contrasts and leave-one-block-out sensitivity.
  A 10,000-resample block bootstrap may be descriptive, retaining all contexts/arms
  within each sampled block; explain limited sample size/temporal independence. Do
  not bootstrap individual calls as independent runs or claim population inference.
- No latency trimming. A predeclared interference/thermal/identity failure marks the
  entire affected block invalid with raw records retained; it is not an outlier rule
  based on the size/sign of measured latency. Fewer than three valid blocks gives
  descriptive timing only, not a robust practical-gain conclusion.

### Optional device profiling

Use an already available compatible Nsight/CUPTI collector in separate diagnostic
hosts. First target six representative contexts (three families × q1/q4 at one
declared phase); add the other phase only if needed and affordable. Preserve
profile-on/off output checks and collector version/configuration. Actual kernel
names, durations, launch counts, copies, occupancy and traffic are measured only
if the collector supports them. Logical graph nodes are not kernel launches;
tensor bytes are not DRAM traffic; elapsed time does not identify a reduction DAG.
If no collector works within 30 minutes, mark those metrics UNKNOWN and continue
valid host timing. Do not invent an attribution to fill the mechanism section.

## G. R1: boundary and generalization panel

Run after core qualification, or independently as numerical boundary research if
T1 is blocked by environmental timing conditions. First recover the other 48
PR104 contexts if their immutable snapshots are available; this expands layer
coverage to 72 but remains exposed data. It is not required for core T1 completion.

Use a deterministic manifest rather than a full Cartesian explosion. Defaults:

| Factor | Development anchors | Prespecified boundary/holdout values |
|---|---|---|
| q | 1,2,4 | 3; 8,16 only as synthetic extension outside current q≤4 admission |
| Actual visible keys | 128,1024 | 127,129,255,256,257,1023,1025,4096 |
| (d,Hq,Hkv) | (128,32,8), (64,32,32) | (128,8,1), (128,8,8), (64,16,4) |
| Q/storage | compact, actual model stride | legal aligned offset/padded stride; verify bounds |
| Mask | causal and full visible prefix | nonempty irregular mask; single-visible-key oracle |
| Lifecycle | qualified resident path | fresh allocation/process; graph capture only separately |

For the default controlled panel, select **36 development + 36 held-out logical
fixtures** before collecting their outputs: 18 length/q sweeps, 9 head/GQA/dimension
contrasts and 9 stride/mask contrasts in each set, balanced over the anchor geometries.
Pair boundary values around dispatch changes, not just friendly powers of two.
Use full tensors and fixed seeded finite data with benign and cancellation/dynamic-
range patterns. Generate masks with at least one visible key. Count and disclose
illegal/rejected fixtures instead of silently replacing them. The precise fixture
manifest must be published before its runs; these counts are a default stratified
design, not instructions to invent missing model geometries or impossible strides.

Where feasible, use two data realizations per selected geometry to separate shape
from value effects. The manifest must distinguish logical fixture, seed, layout,
repetition and process; none is interchangeable with an independent natural prompt.
If the first-dispatch budget permits only a prespecified 12+12 prefix, report the
remainder UNSTARTED and the reduced scope. No extrapolation from that prefix to all72.

For new synthetic inputs, construct the serial single-query reference independently
under the pinned backend and retain full stages. Use a separate scalar/high-precision
oracle and structured exact cases to validate indexing/math meaning; the FP64 result
is not the byte reference and does not excuse a reference mismatch. A q>4 result is
an operator experiment, not qualification of the current decoder admission policy.

New natural snapshots are an additional optional cohort. Select unused prompt IDs,
length bins and layer rules before outputs, recording prior exposure honestly.
Default 12 contexts: three families × two phases × two visible-length bins (roughly
512 and2048 if available), with q and layer assigned in advance. Use existing approved
local models; do not download weights. If the prompt/model is unavailable, report
missingness and keep synthetic scope. Preserve full position/KV producer metadata.
Capture-on/off matching is required before captured tensors support request claims.

Only qualify and time eligible mappings. Freeze any mapping selector using development
data before held-out results. Compare always-PQ, always-QB, best fixed qualified
mapping, frozen selector (including selection/preparation costs) and oracle envelope.
An unsupported baseline is a coverage limitation, not infinite time or automatic
candidate victory. Never switch an actual request mapping without later W1 validation.

An optional external attention comparator (for example a pinned deterministic
FlashInfer configuration) is useful if a compatible implementation is already
available. First match dtype, scale, mask/position, GQA, output semantics and the
same stored operands; measure adapter/packing costs and qualify the existing byte
reference. Determinism alone is not compatibility. If outputs differ, report a
different-contract performance reference separately, not a defeated qualified
baseline. Missing this comparator does not block core results; it limits claims
against mature external implementations. No library installation or runtime change
inside a frozen cohort, and no inferred full-decoder comparison from an operator API.

## H. M1: full-geometry model and hardware decision

Can begin now from authentic PR104 descriptors, independent of the D0 outcome.
First audit PR110: all mapping names use one scheduler; do not reuse their equality
as an empirical architecture comparison. Build one documented reference model and
actually distinct policies/constraints. Do not fit each candidate separately to
make its prediction favorable.

Minimum workload set: all three authentic geometries, q1..4, actual full Hq/Hkv/d,
all output channels and full key extents; plus visible lengths 128,1024,4096 as
explicit synthetic extensions. Include masks, scale, softmax and restoration when
claiming attention cost. An AV-only experiment must retain that label and cannot
stand in for whole attention. Do not crop probabilities without stating the altered
workload; no implicit renormalization or semantics change.

Implement/compare: strong static tiled mapping, strong dynamic work-conserving
baseline, candidate dependency-preserving context/supply mechanism, and optimistic
bound. Baselines receive legal multicast and independent-head parallelism when
resources permit. Every design pays finite context bytes, operand/output storage,
ports/banks, queue/scoreboard/control, buffer copies, synchronization and supply.
Use equal resources and report throughput-latency-storage curves; area/frequency
are UNKNOWN until calibrated. Include setup amortization and ragged utilization.

Required ablations: candidate without dynamic scheduling, without operand reuse,
and with control/storage overhead; identify the component responsible for any gain.
Run at least three declared regimes (compute-, bandwidth-, context/port-limited).
Architecture policies tune on development geometries, then freeze for held-out
length/head/GQA regimes. Publish all slowdowns and sensitivity to reasonable latency/
bandwidth/clock assumptions. Model-grid cells are not statistical experimental trials.

Check workload conservation, dependency order, finite resource occupancy, and an
independent numerical oracle on small adversarial cases. Where claiming actual RTX
compatibility, recover enough of its numerical DAG/semantics to establish that claim;
otherwise declare ABSTRACT_REFERENCE. Calibrate only measurable parameters against
qualified device measurements. Aggregate host latency alone cannot uniquely identify
ports, queues, kernel issue rate or arithmetic depth.

Decision report must answer: does a strong baseline leave material headroom; does
a concrete candidate use it after charging overhead; does it survive full heads,
held-out regimes and plausible parameter variation; is the bottleneck important
to whole requests? Use YES / NO / INCONCLUSIVE, with claim-specific evidence.
No fixed percentage alone authorizes a hardware claim. A software result or a
negative architectural conclusion is an acceptable completed research result.

## I. W1: conditional whole-request validation

Deferred by default; design now, run only after a qualified mapping/selector and a
separately sized platform dispatch. Keep reference model, prompts, sampling/RNG,
proposal budget and target/draft workload contract identical. Compare M_PQ/M_QB/
M_candidate and C_PQ/C_QB/C_candidate as applicable; include original serial R for
endpoint qualification. A target-only gain is not speculative-decoding gain.

Use a prospective small pilot only to estimate variance and runtime, then fix an
independent confirmation panel: default three families × 12 unused prompts × two
paths × three mapping policies × six acquisition blocks, plus declared serial
reference and warmups. Scale it prospectively to actual budget; publish exact counts
before confirmation. Do not promote the pilot or reused PR104 prompts to holdout.

Check full IDs/EOG/stop/length, proposal/accept/reject/rollback workload, and selected
KV/state provenance. Greedy endpoint equality is weaker than sampler/probability
equivalence; define the actual request contract. Instrumented diagnostic requests
remain separate from clean timing. Do not infer identical full control traces from
aggregate counters alone.

Report committed tokens per completed request and cost per committed token. The
phase-sum expression (draft + verification + state/correction + coordination)/tokens
is valid only for non-overlapping intervals; with overlap, use measured request
wall/critical path and separately report component activity. Do not double-count
overlap or add an isolated-kernel speedup directly to request throughput.

Use the measured affected fraction f for a contextual bound
`S_total <= 1 / ((1-f) + f/S_component)` under its assumptions. If the selected
mechanism affects little request time, describe a local result instead of implying
a useful system accelerator. State/transaction hardware needs measured critical-
path cost and a competitive software baseline, not just a numerical KV intervention.

## J. Completion and claims

Deliver the EVIDENCE.md tables, exact runnable commands, source commit, raw location/
hash manifest and limitations. Every stage ends COMPLETE, PARTIAL, BLOCKED or
NOT_STARTED with a reason and actual counts. A clean protocol review is not a
Windows/CUDA qualification. A complete cell matrix is not universal equivalence.
No automatic merge or paper update. Keep the PR Draft until actual RTX results and
their scope are reviewable; update its top description to the latest real state.
