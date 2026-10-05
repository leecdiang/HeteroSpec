# Independent Reviewer B — Experimental rigor / reproducibility

Review basis: source PR #27 manuscript at `b326ff7f20d9bac5afff6f53a6e9d9d8a7aaa7ae`, supplied to the review workspace from current main. This report was prepared independently, without reading another review. No manuscript, experiment source, policy, raw observation, or closed result was edited. No timing was performed.

## Overall assessment

The manuscript already observes unusually clear evidence boundaries. It does not promote blocked-path timing, does not claim Guard wins over Always-Spec, retains the historical negative M4 result, separates ratio-of-medians runtime estimation from older hardware estimators, and explicitly discloses the freeze-hash defect and unavailable 358H raw traces. I found no demonstrated invalidity of the frozen M4 headline results. The main risks are the exact meaning and strength of “prospective,” the limited claim demonstrated by a guard that loses to fixed speculation in aggregate, and the difference between an internally consistent evidence bundle and independently witnessed historical provenance.

## Independently checked evidence versus recorded assertions

Checked directly:

- Read the complete manuscript, including runtime and appendix, the preregistration/protocol, calibration freeze and grid, closeout/formal report, runtime ledger and 358H pin/compact evidence, inventory/selection scripts, original runner and recovery/recomputation code.
- Recomputed deterministic split membership directly from the frozen inventory using SHA256(`20260924|family|task_id`). The 16 qualification, 40 calibration, and 60 held-out tasks match the frozen files exactly, are mutually disjoint, and contain equal HumanEval/Spec-Bench counts in each split.
- Inventory records 36 exposed Spec-Bench IDs and 30 exposed HumanEval IDs, leaving 444 and 134 eligible, respectively; it lists 129 scanned files. Membership selection uses eligibility and IDs, not timing values.
- The nine-candidate frozen grid is E in {2,4,8}, margin in {0,.05,.10}; the frozen score table selects E8_M000 with the smallest recorded calibration regret. Selection and tie-break semantics match the protocol and code.
- The original `frozen()` function/recovery code support the stated variable-shadowing failure mechanism: source/data/calibration/policy checks can still execute while the return path used for the recorded digest is wrong.
- The compact 358H JSON explicitly records no formal performance data, no R2 execution, same-prefix target divergence, and proposal playback without live draft inference. The paper's stack-scoped reading is consistent with it.

Not independently established at this report's initial writing:

- The M4 raw archive was not yet present in the workspace; numerical recomputation and direct-token equality were not independently rerun by this reviewer. Existing audit receipts and the published verifier are evidence of a previous check, not my own execution. The coordinator should add the fresh archive QA result separately.
- The supplied tree had no `.git` directory. I could inspect the recovery analyzer's `git show` comparison but could not independently compare the actual formal-start commit or prove chronological freeze integrity from Git objects here.
- Completeness of historical exposure detection cannot be proven solely from the inventory: scanning is bounded to named directories, selected suffixes and filename patterns. Local untracked histories outside these rules, human prior knowledge, or every possible prior exposure are not ruled out by hashes.
- 358H v0.2 complete R0/R1 outputs and local v0.3 raw diagnostic traces are absent. Their compact findings and hashes are auditable; their derivation cannot be fully reconstructed from this checkout. This is already acknowledged in the appendix.

## Critical scientific risks

### B1. Prospective does not mean historically uninformed (P1; wording fix required)

The M4 family-level positive/negative outcomes were known, and they informed the motivation to use this stack and examine profitability control. That is legitimate hypothesis development. The new experiment is prospective with respect to the newly frozen protocol, candidate selection on calibration, and held-out prompt outcomes—not with respect to choosing the broad research question without historical knowledge. Excluding historical M4 task IDs and freezing before held-out measurements materially protects prompt-level evaluation; it does not erase prior family-level knowledge or prove complete blinding.

Required action: in Section 7 or its appendix explicitly state this distinction in one sentence. For example: “Historical M4 outcomes informed the study design; prospective here refers to freezing the policy before measuring the reserved prompt outcomes.” Prefer “no recorded prior M4 exposure in the frozen inventory” over an unqualified “previously unexposed” where the latter implies a universal audit. Do not rebrand the new experiment as retrospective: the documented separation is meaningful.

### B2. Guard profitability does not demonstrate benefit of adding control (P1; contribution calibration required)

Target/Guard 1.3114x versus Target/Always-Spec 1.3469x supports profitable execution with active fallback, not evidence that control is necessary, lowers risk, or improves request selection over fixed k=2. The preregistration asks about lower held-out latency regret but the primary report appropriately does not assert superiority. A 30.6% fallback rate demonstrates activity only; it does not establish that each fallback was beneficial. No new counterfactual policy search or ex-post subgroup selection can repair this within the closed study.

Required action: retain the fixed comparator prominently and explain the contribution as a prospective test of a simple realized-cost control mechanism on an exact path. Do not call the result a demonstrated safeguard, risk reduction, or superior admission policy. Existing explicit non-superiority language is good; preserve it during any narrative tightening.

### B3. Calibration selection is valid development, but not evidence for the selected policy's optimality (P1/P2)

All nine candidates were evaluated on 40 calibration prompts and the winner was frozen before qualification/formal measurement. That is not held-out leakage. E8_M000 lies at the largest exploration count and smallest margin in the registered grid; this does not establish that E=8/m=0 is an optimum beyond that grid, nor that earlier or more aggressive decisions are intrinsically worse. The calibration baseline and candidate stages are separate sessions/stages, so their scores may also reflect evolving machine state. Independent held-out evaluation prevents treating calibration selection noise as a confirmatory performance result, but does not prove selection stability.

Required action: show the small registered grid in the appendix (currently it says only that it varies exploration and margin), preserve the selected candidate and frozen tie-breaks, and avoid optimality language. Do not extend the grid or rerun calibration.

## Claim wording risks

- **Oracle:** `min(median Target, median Always-Spec)` is an offline two-fixed-path comparator using measured samples. It is not an online-achievable guarantee, causal counterfactual, or global lower bound for all switching policies. A switching policy can in principle beat both fixed paths; measurement variability can also yield ratios below one for individual prompts. Current “descriptive hindsight comparator” is appropriate. Avoid “near oracle,” “optimal decisions,” and interpreting 1.0278x as a proven small worst-case overhead or 2.78% risk bound.
- **60 prompts:** adequate to estimate the declared balanced two-family workload's prompt-GM and report its conditional interval; inadequate for model/platform/workload generalization. Small Spec-Bench categories must remain descriptive. Public benchmark membership also does not establish deployment representativeness.
- **Exactness:** 180/180 is 60 prompts × 3 paired repetitions **per speculative condition**, not 180 independent prompts or proof of universal deterministic equivalence. The present wording is sound; making the denominator explicit beside fallback would improve readability.
- **CIs:** prompt bootstrap intervals are conditional on the frozen campaign, estimator and observed conditions. They do not measure calibration-selection stability or all session/thermal variation, nor do marginal intervals test Guard versus Always-Spec. Current prose already says this for the campaigns and gives the runtime ratio-of-medians estimator.
- **Different M4 campaigns:** do not compare the historical 24Q/HumanEval estimates directly with prospective 60-prompt results as an improvement due to Guard. Different prompts, population weighting, runtime intervention, session and estimator preclude that attribution.
- **358H:** the tested intervention failed eligibility, not a formal runtime speedup test. UB2 failure is target-stack scoped; CPU/NPU state-adapter limitations do not establish hardware inability to retain state. Current text respects this. The “intrinsically blocked” archival label must not become universal prose.
- **Cross-platform diagnosis:** case evidence supports specific observed mechanisms; it cannot establish their prevalence or exhaustiveness. The present framework/limitations correctly separate these.

## Evidence / provenance risks

### B4. Freeze-hash defect is recoverable but reduces automation assurance (P1; preserve disclosure)

This defect breaks the intended machine-readable hash linkage in the start records. The separate committed freeze and unchanged frozen hashes supply an alternate recovery chain. It does not by itself show timing mutation or policy retuning. Conversely, matching files inside an archive alone establishes consistency, not independent historical timestamp authenticity. The main claim is defensible if the formal-start committed bytes and original markers are retained and externally retrievable.

Required action: retain the appendix exception, original STOPPED state and markers. QA must clearly separate byte/hash consistency, numerical recomputation, and commit-history verification. Do not silently patch the experimental runner or describe the recovered run as having passed its original analysis gate. Avoid expanding the main-paper caveat into a disproportionate narrative digression.

### B5. Compact 358H provenance is weaker than portable M4 evidence (P1; residual artifact limitation)

Hashing unavailable raw traces does not make their derivation reproducible. The appendix already discloses this. The qualification failure may be reported as a pinned diagnostic record, but claims such as independently reproducing every diagnostic must not appear in the review or artifact summary. No new hardware execution is required or authorized. If original traces cannot be obtained without new measurement, retain this as a residual limitation.

### B6. Thermal/environment controls limit drift but do not eliminate it (P2; already mostly addressed)

The runtime runner randomizes condition order within task×repetition and retains AC/no-thermal-warning checks. `pmset` warning state is not a controlled die temperature or proof of stationary performance. Three repetitions and one formal session do not estimate between-session variation. The manuscript's interval caveat is correct; apply it explicitly to the prospective runtime claim if general caveats are condensed.

## Required fixes (no experiments)

1. Define the prospective boundary and acknowledge historical design knowledge (B1).
2. Preserve/promote the fact that fixed speculation has the higher aggregate point estimate; do not imply quantified admission benefit (B2).
3. Add the registered grid to the appendix; keep calibration versus held-out separation explicit (B3).
4. In final QA distinguish archive recomputation from historical-commit recovery and acknowledge unavailable 358H traces (B4–B5).
5. State fallback as the fraction of 180 Guard request executions, not an implicit fraction of 60 unique prompts.

## Optional fixes

- Describe the oracle as restricted to the two measured fixed paths, and say it is neither an online input nor a lower bound on all adaptive policies.
- Link the internal report to the independently verified formal-start commit and the independent archive receipt. This supports artifact evaluation without changing anonymous manuscript content.
- Compress repeated caveats in the main text, but retain the explicit prospective boundary, no-fixed-policy-superiority sentence, conditional timing scope, and metadata exception in accessible locations.

## Suggestions deliberately not made

No new timing, policy variant, larger k, additional model, selective rerun, alternative estimator, favorable subgroup analysis, or silent repair of closed code/evidence is warranted by this review. Lack of broader evidence should remain a limitation. I do not require statistical significance between Guard and Always-Spec to report their point estimates, but it must not be asserted without the appropriate frozen comparison.
