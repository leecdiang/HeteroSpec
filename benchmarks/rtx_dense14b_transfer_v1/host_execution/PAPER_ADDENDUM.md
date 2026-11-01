# Proposed addendum for review: larger dense deployment boundary

We evaluated the existing phase-scoped PQ/QB implementation on a new pinned
Qwen3-14B Q8_0 deployment with the original Qwen3-0.6B Q8_0 draft and numerical
library cohort. The host used fixed partial target-weight offload on an RTX5070Ti
Laptop GPU. This changes architecture and CPU/GPU weight placement together;
it is not a causal model-size experiment or a pure GPU scaling measurement.

Native compilation and zero-generation capacity admission succeeded. All40
predeclared feasibility requests completed, covering four already-exposed
inputs, five arms and heavy/callback-off controls. Each R reference was
repeatable, and all observer-control pairs agreed. Nevertheless, target-only
PQ/QB departed from R on both mathematical inputs; speculative PQ/QB also
departed from R on one of them. The first natural-prefix divergences were
output indices16 and82. Complete decision vectors independently reproduce
the greedy rank reversals. These are retained counterexamples, not engineering
retries or evidence to replace the reference.

Within each of the target-only and speculative paths, PQ and QB agree on all
four inputs in endpoint, logical work, captured full logits and serialized
target/applicable draft state. Thus layout-to-layout correspondence persists
in this finite pilot while the stronger shared-UB1-reference property fails.
The evidence does not isolate a particular operator or establish a universal
cause. The observed attention computations are GPU-backed at every layer,
despite CPU residency of17 target-weight layers; no CPU-attention coverage is
claimed. The initial auditor's conflation of weight and operator placement is
disclosed and its original failed result preserved.

The registered gate therefore stopped before the120-request unseen-input
qualification and all paired timing. No speedup, selected-subset estimate or
larger-model performance claim follows. This result qualifies the transfer
boundary of the existing implementation under this particular14B hybrid
deployment. It does not change the previously completed8B/SmolLM2 evidence.

This is a standalone proposed addendum. No manuscript, arXiv submission or
old pull request has been merged or changed by this experiment.
