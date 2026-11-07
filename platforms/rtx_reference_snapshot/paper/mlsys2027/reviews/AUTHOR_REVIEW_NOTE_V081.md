# HeteroSpec v0.8.1 Author Review Note

This note supports a 10–15 minute human author review of Draft PR #37. It is not a conference decision simulation. Read the exact final main PDF alongside Sections 1, 5, 8 and 9; use the separate appendix for chronology details. The merge recommendation below is conditional on finalization QA and human approval, not permission for an automatic merge.

## 1. What changed since v0.8

- Related Work now includes **Lossless but Not Free**, **Compiler-Assisted Speculative Sampling**, **Lever**, and **ACL 2026 HeteroSpec**, with primary-source metadata and complete author lists.
- Broad consumer-hardware novelty was narrowed: gains/slowdowns, ineffective parallel verification, correctness gating and numerical path dependence are prior art.
- The contribution list converged from five items to three: **execution-path qualification**, **B570 predictive mechanism evidence**, and **realized 358H integration cost**.
- M4 Guard remains in the abstract, runtime study and paired comparison, but is no longer headline novelty. It is exact and profitable against target-only, with no demonstrated incremental benefit over Always-Spec.
- Repeated caveats were compressed; exact local comparator/mechanism boundaries and the full canonical Limitations remain.
- The title is now **Execution-Path Qualification and Realized Costs in Speculative Decoding on Consumer Systems**. Main/appendix title metadata and running titles are synchronized; historical titles remain unchanged.
- No new experiments, inference, timing, energy collection, tuning or sweeps were performed. Closed evidence, numerical macros and figure bytes are unchanged. This finalization changes no manuscript claims, section headings or experiment names.

## 2. Strongest scientific contribution

B570 H1 was derived on exposed discovery prompts: after a target-only harness reproduced 90/90 reference sequences, target-only UB1 matched 36/36 serialized discovery sequences. H1 was frozen before reserved inference. All target-only predictions were committed before live serialized outcomes. On **24 reserved prompts × 3 repetitions**, target-only UB1 predicted **72/72 complete serialized sequences**, including residual divergences. The frozen predictions also matched all prompt classifications and divergent repetition-pair first-divergence indices.

This is **held-out predictive mechanism evidence**, rather than a post-hoc debugging anecdote: the hypothesis and predictions preceded the reserved outcomes, and complete sequences were the success criterion. It establishes a sufficient target execution partition on the tested B570 stack. It does not make that path reference-correct: reserved reference equality remains **60/72, BLOCKED**. Prediction of a blocked trajectory and qualification of a usable path are different endpoints.

## 3. What this paper does NOT claim

- UB1 is universally correct.
- Target partition is the unique root cause or a specific faulty kernel has been identified.
- The B570 mechanism explains RTX.
- Intel/Vulkan is generally defective.
- Historical timing is retrospectively direct-ID qualified by the fresh studies.
- Guard improves over Always-Spec. The paired Guard/Always-Spec latency ratio is 1.0270760219826773, with interval [1.0129560055428655, 1.0435592653980876]; Guard is slower on that comparison.
- A 358H persistence benefit was demonstrated. Replay and proposal were inseparable, and the later intervention stopped at qualification.
- The mechanism study establishes a new performance gain, architecture-wide portability, a cross-platform energy ranking or a production correctness certificate.

## 4. Closest-overlap risk

**Lossless but Not Free** already covers consumer hardware gains/slowdowns, ineffective verification parallelism, latency-gap profitability, correctness gating and target-only batch-shape changes. The manuscript explicitly acknowledges these; merely observing slowdown or numerical path dependence is not its novelty distinction.

The distinction must consistently center on **prospective path qualification + frozen mechanism hypothesis + 72/72 held-out complete-sequence prediction + realized state-interface cost**. Compiler-Assisted establishes analytical heterogeneous performance prediction; Lever supplies positive mobile CPU/NPU co-design evidence; ACL HeteroSpec establishes context-adaptive verification allocation. None is diminished to make this paper appear broader.

## 5. Author checks before merge

1. After reading the Abstract, can you clearly restate the principal contribution and distinguish prediction from qualification?
2. Are the Introduction's three contributions sufficiently focused?
3. Is Section 5's discovery → freeze → prediction → validation chain clear?
4. Does Related Work fairly acknowledge the closest work, especially its correctness gates and batch-shape observations?
5. Does any sentence turn a **sufficient path** into a **unique cause**?
6. Is the negative M4 Guard paired result still clear, despite profitability against target-only?
7. Does the new title describe the contribution more accurately than the old broad characterization title?
8. Could a reviewer reduce the practitioner consequence to “measure your system”? Check that qualification, target-partition isolation if blocked, and complete realized-cost evaluation are concrete and bounded by the evidence.

## 6. Current known weakness

The strongest remaining weakness is **breadth / transfer**: the predictive mechanism is validated on **one B570 stack, one model pair, one workload family and one frozen configuration**. The frozen result improves within-stack explanatory evidence; it does not resolve transfer beyond that scope. Additional models/builds, a lower-level numerical mediator and alternative state interfaces remain future scientific questions. No new science is executed to address them in this PR.

## 7. Merge recommendation

**READY FOR AUTHOR MERGE**

Finalization QA verifies the title-only manuscript changes, clean builds, anonymity, complete bibliography author lists, page limit, source bundle and unchanged science. Human authors should complete the checks above and approve the exact candidate before merging. PR #37 remains Draft and unmerged; the submission-candidate tag is created only after author-approved merge and final QA of the merged commit.
