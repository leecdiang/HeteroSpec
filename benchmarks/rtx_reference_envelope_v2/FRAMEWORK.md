# Reference constraints, mappings, and cost boundaries

## 1. What can be advanced now

The existing work already supports a conditional research framework. It does not
yet establish a novel hardware architecture or a universal reference-preserving
lowering. The useful question is:

> For a declared numerical reference and backend, which transformations retain
> the required behavior, what physical freedoms remain, and where does their
> implementation incur avoidable cost?

Separate three relations: equal real-arithmetic expressions; repeatable floating-
point outputs under a declared deployment; preservation of an existing reference.
None implies the other two in general. Likewise, matching finite observations
does not identify the kernel, reduction DAG, or universal correctness.

## 2. Evidence already available

Immutable URLs and scope are in [SOURCES.json](SOURCES.json).

| Evidence | Established | Not established |
|---|---|---|
| PR104 E1 | 72 exposed full-tensor contexts; PQ/QB equal at QK/softmax/AV; MQ differs first at QK in all 54 q>1 contexts | Long unmasked contexts, universal equality, actual reduction tree |
| PR104 E2 | Six-session request comparisons; PQ/QB ratios 1.015593–1.065803 across family/path strata; 9/72 task contrasts regress | Uniform speedup, hardware benefit, kernel attribution |
| PR111 | Mathematically legal original q2 QB violates a necessary frozen Vulkan MUL_MAT batch condition; bounded CPU address/semantic checks pass | Actual GPU placement or measured fallback cost; equality of the batch condition is not sufficient support |
| PR116 | 24 exposed contexts × five layouts × two fresh processes = 240 qualified instrumented calls; PQ/QB/QH_C/QH_D agree in these observations | Clean repeated execution, timing, 48 independent inputs, full requests |
| PR118 r2 | Warmup matched, next PQ/q1 output differed in 32/4096 words; 1 started, 0 qualified, 71 unstarted | Cause, QB-specific fault, any valid speed sample |
| PR110 | One shared scheduler under five mapping labels yields equal schedules; tested crops and explicit abstract FP32 reference | Independent architectural comparisons, full geometry, recovered RTX arithmetic, calibrated PPA |

PR104's tensor key extent is 256, including padding. Visible-key ranges are
Qwen 1–109, SmolLM2 1–130, and Llama 1–127. Three model families do not by themselves
provide broad numerical/backend coverage. PR116 uses a selected 24-context subset
of that evidence, not a new holdout. Do not pool old experiments as new replication.

## 3. Four constraints, each with its own observable

| Constraint | Necessary questions | Evidence and failure classification |
|---|---|---|
| Logical mapping | Are query indices, masks, positions, GQA groups, strides and restored outputs identical in meaning? | Descriptor/address oracle and structured inputs; semantic mismatch |
| Numerical execution | Are precision, conversions, fused operations and reduction dependencies compatible with the declared reference? | Stage and ordinary bytes; numerical mismatch or unknown mechanism |
| State formation | Did operands/KV arise from the same producer and state history, with correct ownership/commit? | Operand/state provenance, selected snapshots, request traces; state mismatch |
| Execution lifecycle | Do allocation, aliasing, synchronization and reuse preserve inputs and outputs across calls? | Input before/after, repeated execution, placement and completion; lifecycle failure |

Backend support and measured placement are additional admission requirements.
A CPU fallback is neither a qualified all-GPU mapping nor a GPU numerical
counterexample; it may be a separately measured deployment path.

For workload x, backend b, lifecycle l and reference contract R, define
`A_R(x,b,l)` as the **observationally qualified** set of mappings. Record the exact
scope/coverage rather than treating membership as a proof for unseen workloads.
An empty or unknown set is an informative boundary, not a reason to loosen R.

For a mapping m in this set, record a cost vector: resident completed graph,
input-inclusive call, allocation/initialization, required packing/restoration,
storage, and (if measured) device activity/traffic. Cost differences apply only
to matching contracts and measurement boundaries. The pointwise minimum is an
**oracle envelope**, not a deployable selector or a fair tuned baseline by itself.

## 4. Hypotheses and disconfirming outcomes

| ID | Hypothesis | Decisive measurement | Result that weakens/rejects it |
|---|---|---|---|
| H-L | PR118's failure depends on execution/storage lifecycle | Same-input controlled lifecycle interventions, then independent clean repetitions | Persistent failures with no qualified lifecycle; no cost work on that cell |
| H-M | More than one full-tensor mapping preserves the reference over a useful domain | Qualification plus controlled shape/stride/mask changes | Equality only on exposed short contexts, or loss of support/reference preservation |
| H-C | Qualified mappings have useful, predictable cost differences | Paired blocked timing; complete copy/packing costs; geometry strata | Differences disappear, reverse after costs, or cannot be predicted on held-out regimes |
| H-H | Fixed numerical dependencies leave exploitable physical scheduling freedom | Full-head/channel model, strong static/dynamic baselines, real resource accounting | Strong baseline matches candidate, ideal headroom small, or candidate overhead erases gain |
| H-S | State management contributes material critical-path cost | Whole-request phase accounting and causal intervention | Cost dominated elsewhere; numerical KV causality alone is insufficient |

H-S is a conditional follow-up, not the default hardware direction. A K/V value
that changes a continuation does not demonstrate that allocation/commit/rollback
is a performance bottleneck or that tags can fix upstream numerical divergence.

## 5. Generalization strategy

Use orthogonal changes in q, true visible length, padding, head count, GQA ratio,
head dimension, legal strides/offsets, mask form, phase, and lifecycle. Preserve
full heads, value channels, keys, and mask semantics. Long contexts require truly
visible keys, not padded shapes; synthetic long inputs are not natural long prompts.

Distinguish (a) the exposed 24-context regression panel, (b) controlled synthetic
boundary fixtures, (c) prospectively selected new model snapshots, and (d) actual
whole-request endpoints. Publish all four with their own denominators. A single
backend study supports conditional backend findings, not cross-device universality.
The B570 lane remains independent and can later test the same framework.

Choose tuning inputs before measuring candidate performance. Freeze any selector
or architecture policy before holdout acquisition. Repeated execution of the same
tensor measures repeatability; it does not increase independent input diversity.
Use competing explanations and interventions, not a chain of favorable examples.

## 6. Hardware question and fair baselines

Candidate concept: interleave independent query/head/output work while retaining
the selected numerical dependency DAG; use bounded context storage and a schedulable
operand supply. This is a hypothesis, not a claim that scoreboards, multicast or
multicontext execution are novel. Ordered final writeback does not preserve an
internally reassociated reduction. Model conversions, FMA policy, softmax and GQA.

At least three baselines are needed:

1. Measured strongest qualified software mapping for the stated cost view, including
   QB, PQ and eligible QH alternatives. Tune fairly on development data. Report
   the best fixed mapping and a frozen selector separately from the oracle minimum.
2. A competitive resource-matched architecture with full geometry, equal storage,
   ports, bandwidth, precision, area/clock assumptions and access to legal scheduling/
   multicast. Include a strong dynamic scheduler if the candidate proposes one.
3. An optimistic bound to assess remaining headroom. For a consistent operation,
   latency and bandwidth model, `T >= max(W/P, L_D, B_min/BW)`. `B_min` must be a
   valid compulsory-traffic lower bound; actual traffic substituted here is not a
   universal lower bound. Account for overlap consistently.

Report the baseline/ideal gap and candidate/strong-baseline gap separately.
Do not count five names for one scheduler as five independent architectures.
Use three model geometries, all heads/channels, short/long visible lengths and
different memory/compute regimes. q≤4 can still expose many independent heads and
channels. The PR110 first-head/64-key/two-channel crop cannot answer this question.

If the actual RTX reduction DAG remains unidentified, an explicitly defined
architecture reference may still be studied, but mark it `ABSTRACT_REFERENCE`.
Its results do not establish compatibility with the deployed RTX reference.

Proceed to a small RTL/synthesis study only when a concrete mechanism survives
strong baselines, resource charging and held-out regimes, or a specific circuit
uncertainty must be resolved to decide feasibility. Small RTL can calibrate a
model; it is not automatically an acceleration result. Do not require hardware
to perform something software is functionally incapable of doing: the contribution
can be a demonstrated efficiency tradeoff under the same contract.

Possible valid outcomes include a useful software selector, a quantified mapping
boundary, a hardware opportunity, or a negative result showing that software already
approaches the relevant bound. The study must not force the fourth into the third.

## 7. Related-work boundary

These are prior-art constraints, not comparative benchmark results. Bibliographic
URLs are in SOURCES.json; verify implementation-specific claims before coding.

| Work | Overlap to acknowledge | Distinction this study must actually demonstrate |
|---|---|---|
| Thinking Machines, batch-invariant inference | Fixed reduction behavior across batching | Compatibility and cost within the existing runtime/reference |
| Vosti, arXiv:2609.38981 | Deterministic inference through kernel/state contracts | Measured conditional lowering boundaries; do not claim generic compositional determinism as new |
| LLM-42, arXiv:2601.17768 | Reference verification and rollback around fast execution | Direct qualified mapping costs and actual state/lifecycle requirements |
| DASH, arXiv:2601.21824 | Scheduling deterministic attention dependencies | Forward verification workload, strong full-geometry baselines and concrete mechanism |
| SPECTRA, arXiv:2609.24847 | Dynamic FPGA mapping, multicast, matrix/vector modes | Reference constraints with measured opportunity, not generic dynamic dataflow |
| SpecStream, arXiv:2609.33184 | Streaming committed history and local speculative state | Existing-reference preservation and measured cost, not generic KV separation |
| FlashInfer attention API | Deterministic split/merge configuration options | Actual compatibility under our pinned semantics; do not assume interchangeable kernels |

The eventual chapter can be titled *Architectural Constraints and Opportunities
for Reference-Preserving Verification*. Its claims should follow the completed
evidence levels: constraints, costs, model, implementation. This PR writes a
research framework, not new paper results or an asserted novelty theorem.
