# Mock area-chair decision — revised submission v0.5

Review basis: the current `main.tex`, all ten sections, separate appendix, runtime table/macros, and `META_REVIEW`, `FINAL_SYSTEMS`, `FINAL_RIGOR`, `FINAL_ADVERSARIAL`, `FINAL_WRITING`, and `REVIEW_CHAMPION`. The tiny final writing/adversarial wording repairs are present in the source assessed here. This is a synthesis of the manuscript and reviews, not an independent raw-trace replication, fresh literature audit, or actual conference decision. No manuscript edits or new experiments were made for this assessment.

## Summary

The paper characterizes why favorable component measurements fail to yield usable speculative decoding in selected consumer stacks: an inexpensive verification path can violate the output requirement, and a stateful draft interface can consume an isolated device advantage. Historical campaigns use different comparators; M4/RTX/B570 text-path equality is weaker than the direct generated-ID comparisons in 358H and prospective M4. Separately frozen runtime studies stop a 358H intervention at qualification and evaluate an executable M4 continuation rule. Guard is exact on 180/180 comparisons and faster than target-only on the held-out workload, but adding control has no demonstrated benefit over fixed speculation.

The revision materially improves validity and narrative coherence. The decision now turns primarily on the scientific importance of a bounded characterization contribution, not on the overclaims removed during revision.

## Strengths

- The RTX captured argmax divergence concretely connects numerical execution behavior to the loss of a cheap verification opportunity. B570 supplies a useful counterexample to treating serialization or a small passing probe as a sufficient correctness certificate.
- The 358H timed regions distinguish complete target work from forward-only proxies and realized replay-plus-proposal work from isolated drafting. This is useful evidence about a particular integration boundary, with negative results retained.
- The M4 runtime study has a frozen policy, separate calibration/qualification/held-out prompts, direct-ID observations, the fixed speculative comparator, and an explicit timing boundary. Its 1.3114× Guard speedup [1.2487, 1.3787] is a legitimate conditional result; Always-Spec's higher 1.3469× estimate [1.2867, 1.4088] remains prominently visible.
- Evidence classes, estimator differences, historical knowledge, unexecuted studies, provenance defects, and absent causal isolations are now stated candidly. The final rigor review found no demonstrated integrity failure invalidating the narrow prospective result; this is not a claim of independent replication or perfect provenance.

## Weaknesses

- The principal scientific payoff remains modest. Numerical path dependence, state-management overhead, complete-cost accounting, and adaptive speculation are established. The new contribution is their specific measured manifestation, without a validated transferable prediction or successful bottleneck-directed remedy.
- Four co-varying stacks are case studies, not controlled replications. The M4 contrast confounds workload and session; the 358H joint timing does not identify replay-only causality or persistence benefit. Its later intervention never reaches formal performance evaluation.
- Guard demonstrates feasible execution, not a reason to deploy its control. Fixed speculation has the better aggregate point estimate. Fallback activity and the hindsight-oracle ratio cannot establish benefit, risk reduction, or optimality. A direct paired Guard/Always interval is absent; separate baseline-relative intervals cannot supply that inference.
- The corrected historical comparator scope permanently weakens the uniform strict-contract story. Text-path success cannot certify generated-ID equality. The separately captured RTX divergence remains useful direct exclusion evidence, but the historical serialized positive control is not a demonstrated direct-ID-qualified alternative.
- Prompt bootstrap precision does not cover session, thermal, or recalibration variation. The short, finite, one-configuration prospective study and weaker portions of historical provenance restrict generalization and independent verification.

## Questions

These questions clarify the acceptance case; they are not requests to retune the paper or run experiments within this frozen revision.

1. What concrete practitioner decision changes because of these measured cases beyond the already familiar advice to validate the execution path and measure complete cost? The best answer should rely on the RTX and 358H evidence, without claiming a portable decision rule.
2. Does the committee consider the specific negative controls and implementation-boundary findings sufficiently consequential for a characterization paper, despite the lack of a successful remedy or common controlled campaign?
3. How much weight should the strict-contract framing carry when several historical positive controls establish only text-path agreement? Can the acceptance rationale remain persuasive with those controls explicitly weaker?
4. Is the prospective M4 study valuable as an execution/accounting endpoint alone? It cannot support a controller-improvement rationale. A direct paired contrast would sharpen this limitation, but its absence does not justify asserting either statistically significant harm or improvement.

## Overall assessment

**Mock recommendation: Weak Reject at a selective general MLSys contribution bar.** This judgment follows from contribution strength and cohesion, not reviewer vote counting. The manuscript is now defensible within its stated scope, yet the demonstrated scientific increment is configuration-specific characterization plus a continuation mechanism with no established incremental utility. The 358H intervention does not provide the missing systems remedy, and the separate M4 study is a conceptual endpoint rather than a validation of that remedy.

The champion's acceptance argument remains legitimate: careful negative controls can reveal that a favorable local measurement describes an execution unavailable under the actual contract or interface. A characterization paper need not invent an algorithm or produce a positive speedup to merit acceptance. If the committee finds these particular counterexamples consequential and reproducible enough, a weak acceptance on empirical value is defensible. The systems/adversarial concern is that the cases are not sufficiently general, causal, or surprising to clear that bar. The rigor review supports the narrower claims but does not resolve that significance question; the writing review's lack of blockers likewise is not an acceptance endorsement.

The original champion report predates the material historical-comparator correction. Its references to exact historical M4 outcomes or an exact serialized RTX alternative must be read through the current weaker text-path scope. Its core characterization argument survives, but with reduced evidentiary reach. Neither position is averaged into a consensus.

## Confidence

**Moderate.** Confidence is high that the revised text limits Guard and historical comparator claims appropriately, and that the remaining scientific disagreement is substantive. Confidence is lower in forecasting an actual committee outcome: characterization standards vary, this synthesis does not replay all evidence, and the champion reviewed an earlier source state. The final rigor review's byte checks support the recovery explanation without independently attesting real-world chronology.

## Likely rejection or acceptance reason

**Likely rejection reason:** useful but limited empirical novelty; heterogeneous cases lack a common causal or predictive result, the diagnosed intervention is unevaluated, and the only evaluated controller adds no demonstrated value over fixed speculation.

**Defensible acceptance reason:** unusually concrete negative execution-path controls and stateful-cost characterization that improve how practitioners interpret component-level speculative-decoding claims, accompanied by a candid prospective exact-execution endpoint. Acceptance would be for these bounded empirical findings, not a new algorithm, proven control benefit, four-platform portability, or uniformly strict historical correctness evidence.
