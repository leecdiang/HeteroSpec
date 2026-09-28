# Reviewer response: direct paired M4 Guard versus Always-Spec

Reviewer concern: Separate Target/Guard and Target/Always-Spec confidence
intervals do not provide a direct paired inference between the speculative
conditions.

Action: Added a reviewer-requested post-study paired secondary analysis from
the already-frozen held-out raw observations. This contrast was not the
registered primary endpoint; the aggregate results were known. The analysis
plan was committed before calculation at `8e7be49` as a procedural timestamp,
not preregistration or blinding. No analysis choice changed after the result.

For each of 60 prompts, divide the Guard median of three formal repetitions
by the Always-Spec median. The geometric-mean latency ratio is
**1.0270760219826773**, with exact 95% paired prompt-bootstrap interval
**[1.0129560055428655, 1.0435592653980876]**. Values above one mean Guard
is slower. The interval lies entirely above parity: Guard had higher latency
than Always-Spec in this frozen comparison. Descriptive counts: Guard faster
24 prompts, Always-Spec faster 36, exact ties 0.

The standalone fixed-seed bootstrap uses 10,000 paired-prompt resamples,
Python Random seed 20260924, frozen held-out order, and the original linear
percentile convention. Two separate calculation implementations reconstruct
all raw prompt medians, match the primary medians exactly, and reproduce the
headline estimate, exact finite-bootstrap endpoints, and counts. Table 3,
Section 7, the limitations, and appendix state the direction and post-study
status. All empirical manuscript values are sourced through macros.

No new timing, model execution, policy search, controller tuning, subgroup
promotion, serving-controller benchmark, or reinterpretation of the primary
endpoint was performed. Protected primary data, policy, results, correctness,
energy status, archive bytes, original freeze-hash defect, and stop markers
remain unchanged. Guard remains profitable against target-only; both
speculative conditions remain 180/180 direct-token exact.

This analysis sharpens the existing negative/control conclusion. It is not
presented as an acceptance-rescuing positive result. The experiment still
demonstrates executable exact control, with no previously established
incremental Guard benefit; the missing direct comparison now shows higher
Guard latency under this secondary estimator. It does not establish universal
Always-Spec dominance, robustness, risk reduction, near-optimality, or utility
beyond this M4 model/runtime pair, fixed k=2, held-out set, and post-prefill
boundary. Its uncertainty excludes session and recalibration variation.

## Validation and delivery

The versioned QA receipts record all 228 historical numerical checks, all
117 prior runtime gates plus new secondary checks, all 62 archive payloads,
638 independent secondary checks, hardware-free rejection tests, unchanged
historical assets and primary evidence, and manuscript/appendix/hardware-only
builds. The PDF and visual receipts record page budget, anonymity, embedded
fonts, references, citations, overfull boxes, and fresh rendered-page review.
Final page counts and detailed counts are in `../MANUSCRIPT_STATUS.md` and
`../evidence/NARRATIVE_PDF_V06_QA.json`. This is a draft PR for review;
no automatic merge is authorized.

## Integration with latest main

Synced with main `9b996dd702e5807b3cacc9db9c69aa7eb80035a4` after PR #29. Its approved
figures and three compact primary Table 3 rows are retained; the secondary
contrast remains in a separate block. The only textual merge conflict was the
table caption, which now states both the oracle latency-regret boundary and
the post-study paired ratio direction. The analysis plan, raw reconstruction,
JSON/report, formula and exact interval are unchanged. All validation and PDFs
were refreshed on the combined version. No new model execution occurred.
