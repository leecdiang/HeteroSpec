# Continuation: source guards, frontier evidence, and the 5% research path

This study follows the review of paper PR #222 at
`e8a4981ef7db8f05cff7144fd4edc6e5a4109343`. It adds a source audit, a proposed
strong-control figure, one preregistered native CPU diagnostic, independent
reviews, and a concrete architecture hypothesis to research PR #221. It does
not modify the manuscript, numerical cores, production admission gate, or the
earlier research evidence.

**The new result is a qualified positive CPU frontier comparison with an
explicit output counterexample outside its consumer contract. The 5% service
goal and production qualification remain unproven.** The source-level audit
also finds that the packed path does not inherit loop4's rejection contract.
The next optimization should address real work and memory reuse, while keeping
the output and state obligations explicit.

## Completed work and limits

| Work | New evidence | What it does not establish |
| --- | --- | --- |
| [Strong-control replot](paper_audit/README.md) | Five same-panel contrasts per deployment, 220 root points, original intervals retained; the omitted W-L4-D4 control is now visible | New timings, independent bootstrap, isolated cut/packing effect, or matched per-phase cost decomposition |
| [Source guard audit](guard_audit/SOURCE_AUDIT.md) | 10 obligations, 20 source identities, 35 exact source regions; predicates and failure boundaries distinguished | All runtime branches exercised, native negative-case qualification, or a numerical error in the frozen measured deployment |
| [Native q4 frontier diagnostic](q4_frontier/RESULTS.md) | Two fixed synthetic CPU histories; all eight preregistered comparisons pass their specified contracts; the extra fifth vector differs | Historical R compatibility, all-output interchangeability, natural acceptance, real-model/GPU coverage, or performance |
| [Architecture hypothesis](guard_audit/ARCHITECTURE_HYPOTHESIS.md) | Current group-to-CTA mapping inspected; a narrowly defined two-group weight-fragment reuse candidate and three-arm experiment | An implemented kernel, a measured memory-traffic reduction, novelty, or 5% system improvement |
| [Independent cross-review](review/CROSS_REVIEW.md) | Separate source, figure and raw-evidence checks; receipt weaknesses fixed before the CPU run | GitHub CI or a substitute for production/GPU qualification |

The initial eight diagnostic files were committed as
[`ef2766327e7821fe188d1ad788b2c3b05531eb9a`](https://github.com/leecdiang/HeteroSpec/commit/ef2766327e7821fe188d1ad788b2c3b05531eb9a)
and read back byte-for-byte before native execution. They remain unchanged.
The prior 88 files in PR #221 were preserved exactly.

## 1. The strong-control gain remains around 1%–2%

The proposed Fig. 5 includes the existing `L_P_D4 / W_L4_D4` contrast. The
candidate/control resident-service ratios were recomputed from the original
public totals:

| A5000 deployment | Same-panel time reduction | Published adjusted 99% interval, as time reduction | Additional reduction from the current candidate needed to reach 5% versus this control |
| --- | ---: | ---: | ---: |
| Qwen3-8B | 2.0116% | 1.4441%–2.4411% | 3.0498% |
| Qwen3-14B | 1.0807% | 0.8310%–1.2824% | 3.9622% |
| Llama-8B | 1.5641% | 1.1548%–1.8320% | 3.4905% |

The final column is only `1 - 0.95 / current_ratio`; it is an algebraic
requirement, not a forecast. The endpoint is a 5% reduction in service time,
not a 5% throughput speedup. Intervals are preserved, not regenerated from
absolute request times. The Qwen3-8B D4 relative-order confounding remains,
and this comparison changes cut and projection together. The table does not
replace balanced component-attribution trials.

The available projections lack a same-request per-phase decomposition. That
part of the paper review remains open. The new figure deliberately does not
combine phase times from different panels to create a misleading cost stack.

## 2. Correctness admission needs source-specific boundaries

The audit identifies three concrete distinctions:

1. Backend-loop4 marks its wide node and checks actual CUDA buffers, dimensions,
   strides, offset bounds, device/warp and MMVQ dispatch. The packed grouped
   node is unmarked and enters the generic dispatcher. Its admissible recipe
   must therefore be bound separately; loop4's checks are not packed checks.
2. Placement observation is capture-only. The original RTX observer also
   omits `frontier_packed_*` names; the later reconstructed Linux M2 observer
   broadens coverage. A clean `bad=false` postcheck is not a placement
   observation by itself.
3. Target-group exceptions poison their owner, while trim, draft and sampling
   failures rely on CLI termination. These cannot all be described as one
   recoverable, transaction-level failure rule.

Actual graph reuse does compare the prefix vector and active/layout policy;
the suspected shape-only-reuse defect is not supported. The audit supplies a
method-section replacement paragraph and a machine-readable recipe table.
Its 22 follow-up qualification cases are explicitly `NOT_RUN`.

## 3. What the new native result changes

Here q4 and q8 denote token-row widths, not quantization bit widths. A retained
untrained two-layer F32 CPU fixture, F16 KV and one thread were used. Histories
of length 248 and 252 place the paths around a real 256-cell native attention
extent boundary. Every path used a fresh context and a fixed prefix producer.

The complete run used one model load, 14 contexts, 146 decode calls, 3,612
target rows and four trims. No retry or native timing phase occurred. An
independent reader checked all 30 raw blobs, all 42 stages and the work
accounting without importing the producer's verifier or running a model.

Both histories pass:

- q4+q4 own-path repeat and q8 versus q4+q4 on all eight shared full vectors,
  active state, native geometry and a common forced continuation;
- q8 trimmed to frontier 4 versus q4 on the first four shared vectors and
  the same state/continuation obligations;
- q8 trimmed to frontier 5 versus q4+q1 materialization on the **preregistered
  first four consumer vectors**, materialized state/geometry and the common
  forced continuation.

These are 56 full-vector pairs, 24 active-state pairs and 24 geometry pairs.
They are comparison obligations, not independent statistical samples.

In the last comparison the extra fifth vector differs in 117/128 entries at
P248 and 128/128 at P252, although its argmax is unchanged. Its diagnostic-only
role was declared before execution, not chosen after seeing the result. The
forced continuation does not consume that vector. Consequently, equal KV and
one forced continuation do not justify merging two states whose next real
consumer reads different logits. The original worker's full requested-output
contract is still binding. See the [algorithm implications](guard_audit/ALGORITHM_IMPLICATIONS.md)
for the pending-token, correction and bonus obligations.

The earlier q1-reference failure therefore does not settle every q4/q8
question. This new panel gives positive, tightly scoped evidence for the
complete q4+q4/q8 comparison, and a direct warning against treating KV equality
as full observable-state equality. It does not qualify a production dynamic
policy or a new reference definition for the paper.

Changing native tiling inside one known eight-row macro is also different
from changing speculative transaction depth from k3 to k7. The present worker
keeps k fixed within a request. The new run directly tests the former; it does
not implement or qualify the latter.

## 4. A concrete architecture candidate beyond launch consolidation

For each output-row tile, current packed groups occupy different CTA channel
indices. They access the same weight channel but do not explicitly share a
loaded weight fragment inside one CTA. Both loop4 and current packed already
quantize the wide activation once. Thus the source-visible change is multiple
MMVQ launches becoming one grouped launch, with different group-grid
concurrency; memory-traffic savings are not established.

The first new candidate is **q=8, two independent four-column accumulator
groups in one CTA, reusing the original weight fragment**. Keep the original
four-column K/lane/reduction organization. Simply selecting an eight-column
kernel would change the source's warp allocation and is a different numerical
path. Compiler behavior, register pressure, spills and reduced occupancy must
be checked even when the conceptual arithmetic is unchanged.

The minimal operator study compares backend-loop4, current packed, and the
proposed shared-weight pair on one captured real q8 descriptor. First require
own-path and cross-path bitwise replay, including quantized activation bytes;
then inspect resources and paired operator timings. Any benefit must survive
full-request qualification and complete service timing. Current k3 verification
does not enter multi-group packing, so its decode latency cannot inherit an
unmeasured q8 benefit.

Weight reuse alone is not evidence of a new speculative-decoding method. A
method contribution would need to combine proven legal execution choices,
causal selection using available request information, and architecture-specific
costs, with complete system evidence. The existing [controller](../controller/README.md)
still has no admitted real deployment stage-cost catalog and must not receive
prices from this capture-heavy CPU diagnostic.

## Next experiments, in decision order

| Step | Concrete question and completion rule | Current status |
| --- | --- | --- |
| Recover 32B S3 evidence | Validate the existing job's source/build/reference bindings, eligibility and complete service comparison against its strong backend loop | Public PR #218 head remains the previously observed preparation snapshot; no completed S3 result recovered in this continuation |
| Admit the packed recipe | Bind actual descriptors/dispatch and distinguish reject, qualified fallback, and post-execution invalidation; execute the focused negative cases | Source audit and 22-case design complete; native execution not performed |
| Test two-group weight reuse | Bitwise A/B/C replay, resource cost, then paired operator timings against current packed | Candidate and minimal protocol specified; kernel not implemented or timed |
| Close a real dynamic request | Preserve all actually requested outputs; test natural rejection on both sides of the frontier, pending correction, all-accept bonus, EOG/CAP and continuation on the same owner | CPU forced-history evidence only; next real-request matrix specified separately |
| Admit matched service costs | Fixed binaries, same states, correctly matched request-stage timing, control drift and included controller overhead | No new deployment prices; current policy still abstains without them |
| Test the 5% endpoint and scope | Freeze the policy before held-out requests, compare strongest qualified fixed/runtime controls, stratify lengths, report adverse strata and full lifecycle cost | Not measured; no general 5% claim admitted |

No GPU was used in this continuation. The current session has no verified
target-server execution endpoint, so the source/CPU work above is complete
while GPU and real-service steps remain unexecuted. PR #222's manuscript and
PR #218's existing experiment were left unchanged. The independent visual
review of the last two supplement pages and a full platform configuration
table also remain separate paper tasks.

## Reproducibility and publication boundaries

Source and compact derived summaries are in Git. Build/run logs, binaries,
native job receipts and raw state/vector blobs are retained separately with
hash identities. The source release, old artifacts and model weights are
referenced rather than duplicated. Source identity checks, host-only tests,
native diagnostic comparisons, independent reviews and GitHub CI are different
forms of evidence and must not be described interchangeably.

The proposed figure was visually checked on its own. That check does not
validate a new ten-page manuscript layout or change the paper's submission
readiness. The research PR remains a draft for review.
