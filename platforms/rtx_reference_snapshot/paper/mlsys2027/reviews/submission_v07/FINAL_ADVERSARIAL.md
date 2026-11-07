# Independent adversarial submission review — v0.7

This is an independent model simulation, not human peer review or a conference decision. I assessed v0.7 before reading `submission_v05/MOCK_DECISION.md` and did not read other v0.7 reviews. I inspected all 11 main-PDF pages (10 body plus references), all five appendix pages, the rendered Figure 3 page, manuscript source, `DIRECT_ID_QUALIFICATION_SCOPE_V07.md`, `DIRECT_ID_INTEGRATION_AUDIT_V07.md`, both frozen protocols/preregistrations, formal reports/analyses, and independent-validation records. I independently recounted equality flags in the formal comparison tables; I did not independently replay raw captures, execute inference, or conduct a fresh literature search.

Main PDF SHA-256: `da3c5c9951774880f2cc562ee767417d761a8aefcd686ba8e49e2002d3fa0670`.
Appendix SHA-256: `afa4ab81d346c5764be43a24e7a58b43c117e2cbc65c872cf79d1421e3b7b15f`.

## Strongest acceptance argument

The new qualification evidence is substantial within its stated scope. Each study completes 270 executions and 180 candidate/reference comparisons. RTX batching matches 75/90 pairs and serialization matches 90/90; B570 fast matches 60/90 and serialization 78/90, below the unchanged 90/90 gate. Whole-prompt counts are respectively 25/30, 30/30, 20/30, and 26/30. All conditions are repeat-stable. Thus the evidence records deterministic disagreement with a specified reference rather than merely noisy run-to-run behavior. Native RTX commit events and B570 instrumented committed-ID sidecars directly address the earlier observational weakness. Preserved operational failures, complete fresh RTX v2 scheduling, and independent offline validation make selective replacement less plausible.

This can change a concrete engineering decision: reducing verification micro-batching to one must still undergo complete path qualification; it cannot be assumed to preserve the chosen reference. Combined with the 358H decomposition, the paper gives useful examples of favorable component measurements describing an unavailable or unprofitable integrated execution. A negative characterization paper need not supply a faster algorithm. The authors also expose rather than conceal the unsuccessful intervention and controller comparison. Weak acceptance would be defensible if these reproducible consumer-runtime boundaries themselves satisfy the committee's significance threshold.

## Strongest rejection argument and confounds

My concern is the scientific increment beyond documenting specific implementations. The manuscript acknowledges established numerical path dependence, heterogeneous placement, state reuse, complete-cost accounting, and adaptive speculation. New qualification counts strengthen observation but do not identify a transferable condition predicting when serialization works. The B570 residual failures are especially unresolved: its reference uses `llama-completion` with micro-batch 128, while serialized speculation uses another front end with micro-batch one. RTX instead uses the embedded-server CLI and reference micro-batch one. Contexts are 1024 versus 4096. B570's serialized mismatch at generated index one on HumanEval/89 makes reference/prefill differences a pertinent alternative explanation, although that position alone establishes no cause.

These differences do not invalidate the registered B570 endpoint. They limit its explanatory payoff: failure to match that reference is demonstrated; inability of serialized verification itself to preserve an otherwise matched target execution is not isolated. The within-B570 fast-to-serialized comparison remains informative because the intended candidate-path change is micro-batching. Across studies, common tasks, model bytes, greedy k=2, repetitions, and gate provide a common protocol family, not controlled hardware replication. There is no causal hardware ranking or shared CUDA/Vulkan numerical root cause.

The 358H result is another sound but bounded observation. Replay plus proposal consumes 58.35% of NPU-path time, but the joint region does not quantify replay-only causality or demonstrate a persistence remedy. CPU target-side dominance supplies a different bottleneck. The later intervention fails qualification before formal performance. The M4 workload contrast remains confounded by separate sessions. These cases share an evaluation discipline more convincingly than a common explanatory result.

## Required delta and overclaim assessment

**A — Historical comparators:** prospectively, only partially addressed. Historical M4/RTX/B570 re-tokenized-text success remains weaker than direct generated-ID equality. The new studies cannot recertify old performance; the changed RTX driver reinforces that separation.

**B — Common protocol:** meaningful alignment, with consequential front-end, context, and reference differences explicitly retained. “Parallel qualification replications” is acceptable if understood as replication of the question, not identical conditions or effects.

**C — Serialization:** restores qualification on RTX, improves agreement without qualifying B570, and supplies no new formal performance remedy. Figure 3 correctly separates historical cost from prospective qualification. I found no historical-performance promotion, universal serialization guarantee, population failure-rate estimate, or unsupported numerical root-cause claim.

**D — Guard:** the paired secondary analysis resolves the old uncertainty in an unfavorable direction: Guard/Always latency is 1.0270760219826773, CI [1.0129560055428655, 1.0435592653980876], with Guard faster on 24 prompts and Always on 36. Both preserve 180/180 sequences. Guard's profitability against target-only is valid; incremental control utility is unsupported. The paper states this clearly, without disguising the post-study analysis as preregistration.

**E — Fresh contribution judgment:** v0.7 is stronger as a qualification-boundary study than as a unified heterogeneous-systems explanation. The new evidence materially improves validity and the acceptance case. It does not overturn v0.5's principal Weak Reject reason: limited consequential, generalizable scientific payoff.

## Minimum missing contribution and recommendation

The major blocker is significance, not a demonstrated integrity failure or a remaining headline overclaim. The minimum missing scientific contribution is a controlled explanation of one qualification boundary that yields a falsifiable decision beyond “test the actual path”: for example, isolate reference/prefill versus speculative verification effects on identical committed prefixes, then validate the resulting qualification prediction on a reserved configuration. A successful speed remedy is not mandatory. More prompts or additional unexplained stacks alone would not provide this missing contribution. This describes future work only; it does not authorize reopening the frozen studies.

**Recommendation: Weak Reject (3/6).** Scale: 1 strong reject, 2 reject, 3 weak reject, 4 weak accept, 5 accept, 6 strong accept. **Confidence: 4/5**, where 1 is low and 5 high. Confidence is high in the bounded endpoint interpretation and moderate in the selective-MLSys significance judgment; the latter remains legitimately contestable.
