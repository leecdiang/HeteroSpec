# Reviewer C — Statistical review

Source reviewed: `b326ff7f20d9bac5afff6f53a6e9d9d8a7aaa7ae` (PR #27 handoff/current source supplied by coordinator).

Independent review: I read the manuscript, appendix, frozen formal analysis/protocol, analysis implementation, historical evidence validator, numerical macros, and relevant historical summaries without reading another reviewer report. No manuscript or experimental file was edited. Line references below are to this source. No hardware execution or policy search was performed.

## Overall assessment

The major estimands and uncertainty boundaries are unusually explicit and largely correct. I found no numerical discrepancy in the runtime headline claims, no statement of Guard-over-Always-Spec statistical superiority, no “near oracle” claim, and no promotion of the 358H runtime diagnostic to an admissible speedup. The primary correction is an energy-equivalence implication in the historical study. A smaller correction should make the fallback denominator explicit. Existing analysis should remain frozen.

## Required scientific wording correction

**C1 — A confidence interval containing parity does not establish energy neutrality.**

- Locations: `manuscript/sections/04_outcomes.tex:12`; `manuscript/appendix.tex:52`; `manuscript/tables/04_energy.tex:10`.
- Current wording: “energy is neutral within uncertainty” / “energy neutral within uncertainty.”
- Evidence: `tables/values.tex:16–18` and frozen HumanEval energy summary report baseline/speculative package J/token ratio **1.013 [0.990, 1.034]**. No equivalence margin or equivalence test is documented.
- Correction: “The interval includes parity; a package-energy improvement is not established.” Table form: “Primary package-energy interval includes parity; threshold variant secondary.”
- Reason: failure to exclude parity supports uncertainty about improvement, not a positive conclusion of equality. Retain the exact estimate, interval, sensor boundary, and secondary classification.
- Priority: P0 claim calibration; small textual change, no new analysis.

## Clarifications worth implementing

**C2 — Identify fallback as a request-execution count.**

- Location: `manuscript/sections/07_runtime_codesign.tex:25`.
- Current wording: “Guard falls back in 30.6% of requests.” This is defensible, but readers may interpret the denominator as the 60 unique held-out prompts.
- Evidence: `scripts/platform/m4_runtime/analyze_runtime_study.py:112,151,164–165` counts Guard observations, one per prompt/repetition. `FORMAL_ANALYSIS.json` contains fallback round counts summing to **55**, denominator **180**, fraction **0.3055555555555556**. The independent archive verifier uses the same denominator at `recompute_evidence_bundle.py:232`.
- Correction: “Guard falls back in 30.6% of its 180 request executions.” The count 55/180 may be placed in the appendix if desired, generated from the frozen summary rather than hand-maintained as a new empirical literal.
- Do not describe 30.6% as the proportion of unique prompts, failure probability, or demonstrated avoided slowdowns. Fallback activity is descriptive, and repetitions are correlated within prompts.
- Priority: P2 estimand clarity.

**C3 — Make uncertainty's conditioning explicit at the runtime result if it can be done without repetition.**

- Locations: `sections/07_runtime_codesign.tex:22`, `appendix.tex:77`.
- Existing text correctly says prompt bootstrap, three repetitions reduced to per-condition medians, and no independent repetition sampling. `sections/03_methodology.tex:16` and limitations already explain session/thermal uncertainty.
- Optional addition in appendix only: the intervals condition on the frozen selected policy and the observed per-prompt medians; they do not integrate over alternate calibration samples, policy reselection, or future system sessions.
- This is a residual inference boundary, not a request to change bootstrap design or inflate the intervals post hoc.
- Priority: P3; existing disclosures may be sufficient.

**C4 — Preserve the oracle's restricted, measured-comparator meaning.**

- Locations: `sections/07_runtime_codesign.tex:25`, Table 3 caption, `appendix.tex:77`.
- Current descriptions are correct. The comparator is the minimum of two measured condition medians, not a minimum over all possible within-request policies and not an online-available quantity. The Guard's observed latency can be below it on a prompt, through switching and/or timing variation; the word “regret” therefore does not imply a universally nonnegative policy regret.
- Optional appendix phrase: “The oracle selects between two measured fixed conditions; it is not a lower bound over all policies.” Do not call **1.0278×** an optimality guarantee, a worst-case bound, or a demonstrated online selection accuracy.
- Priority: P2/P3 depending on narrative emphasis. No need to add new quantitative comparisons.

## Numerical and methodological audit

| Claim | Audit finding |
|---|---|
| Guard 1.3114 [1.2487, 1.3787] | Correct rounded Target/Guard GM. Frozen unrounded value 1.311386908421982. |
| Always-Spec 1.3469 [1.2867, 1.4088] | Correct rounded Target/Always-Spec GM. Frozen unrounded value 1.3468940491822108. |
| Guard/oracle 1.0278 [1.0137, 1.0446] | Correct rounded GM of Guard/min(Target, Always-Spec) using condition medians. Frozen unrounded value 1.0277867248209298. |
| 30.6% fallback | Correct rounding of 55/180 Guard executions; not a 60-prompt binary fraction. |
| 180/180 exact | Correct denominator **per speculative condition**, paired against corresponding target reference over 60 prompts × 3 repetitions. Manuscript and table retain “both conditions” correctly. Not 180 independent prompts or a universal exactness guarantee. |
| 540 observations | Correct 60 × 3 × 3, including target observations; not an effective sample size of 540. |
| 48/48 qualification per condition | Correct 16 qualification prompts × 3 repetitions; independent of the 60 formal prompts. |
| Runtime estimator | Median of three latencies **separately per condition**, then prompt ratio, then equal-prompt GM. Correctly distinguished from historical GM of matched repetition ratios. |
| Runtime CI | 10,000 unstratified prompt resamples; Python Random seed 20260924; linearly interpolated 2.5/97.5 percentiles; one stream consumes Guard speedup, Always speedup, then oracle ratio. Appendix correctly preserves finite-bootstrap convention. |
| Historical estimators | GM of three paired ratios then prompt GM for M4, RTX, and B570; median of three paired ratios then prompt GM for 358H. Appendix accurately records 100,000 resamples for historical HumanEval M4 and 10,000 for others, including the distinct endpoint conventions. |
| 358H aggregate costs | Arithmetic component totals/accounting identities are expressly distinguished from headline prompt GM. Figure caption also warns against interpreting its mean bars as the headline ratio. |
| 358H Phase-1 uncertainty | Five-repetition cell bootstrap is correctly labelled as repetition bootstrap in the figure caption, separate from Phase-3 prompt uncertainty. |
| Spec-Bench strata | Frozen report contains cells as small as n=1 and n=2. Manuscript appropriately avoids subgroup effect claims. Keep those strata out of primary inferential rhetoric. |
| Cross-study M4 comparison | Historical and prospective estimators/populations are explicitly separated; the manuscript does not estimate improvement across campaigns or attribute historical contrasts solely to workload. |
| Energy and diagnostics | Runtime energy is NOT_CLAIMED; B570 timing/energy remain diagnostic. Historical M4 neutrality wording is the exception needing correction above. |

### Read-only deterministic verification actually performed

Loaded the frozen `FORMAL_ANALYSIS.json` per-prompt medians and called the original analyzer's pure `summarize()` function with a fresh `random.Random(20260924)`; this did not run its main function or write files. The resulting entire `overall` object equalled the frozen object exactly, reproducing all three point estimates, six CI endpoints, and existing additive summaries. Independently checked all 60 oracle medians equal `min(target_median_ns, always_median_ns)`, and checked frozen fallback-round counts sum to 55 with fraction 55/180.

This is a check of processed frozen prompt medians and original statistical formulas, **not an independent raw-token/archive reconstruction**. The coordinator's full archive verification is still required for raw-data provenance and direct-token exactness. Historical estimator formulas and bounds were checked against the existing validator and manuscript; the coordinator should run all 228 numerical checks.

## Statistical recommendations to reject

1. Do not “harmonize” historical estimators or CI endpoint conventions after results are known.
2. Do not infer Guard-vs-Always-Spec equality or superiority from overlapping marginal CIs. The text correctly confines itself to the point-estimate ordering. No new paired test is needed to support that wording.
3. Do not add a binomial correctness reliability bound treating 180 repeated exactness pairs as independent prompts.
4. Do not search alternative family weights, strata, policies, or bootstrap methods for a more favorable controller result. The equal 30/30 family mixture and frozen pooled bootstrap are the reported estimand.
5. Do not promote small-stratum observations, the offline oracle, or retrospective M4 contrast as deployment guarantees or controlled causal effects.
6. Do not replace inconvenient fixed-speculation superiority in aggregate with an unmeasured claim of tail-risk reduction or avoided regressions.

## Remaining statistical risk

Sixty held-out prompts support the reported conditional aggregate result for this selected M4 policy and balanced workload mixture. They do not establish population-wide benefit, policy-selection stability, superiority to Always-Spec, tail-risk reduction, or robustness to other sessions. Those are limits to preserve, not reasons to reopen the experimental program.
