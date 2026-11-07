# Revision Priority

Derived from the two v0.8.2 PDFs, six independent reviews, and `CONSOLIDATED_REVISIONS.md`. Counts refer to independent reviewers; a proposed edit is not evidence that a new experiment has been performed. CR IDs retain the consolidated report's exact definitions and conflicts.

## P0 — Must fix before submission

**No shared P0 scientific blocker.** The AC identifies one especially decision-relevant evidentiary reservation (CR-01), but no reviewer consensus establishes a validity failure requiring new science.

## P1 — Strongly recommended

| Issue | Reviewer count | Location | Exact recommended edit | Estimated manuscript impact | Risk of causing new problems |
|---|---:|---|---|---|---|
| CR-01: B570 prediction commitment inspectability | 5/6 | Main §5.2 p. 5; appendix §J p. 6 | From existing records, print the actual digest and endpoint/serialization rule, freeze-before-live markers, and a 24-prompt manifest binding three prediction/outcome sequence hashes and lengths; preserve four divergent examples. Do not portray a digest alone as proof of timestamp. | High: makes the central result auditable in the submission artifact. | Medium: reconciliation may uncover mismatches; space and anonymity need checking. **CONFLICT:** reviewers differ on full-array versus compact manifest extent. |
| CR-05: historical text versus direct-ID endpoints | 6/6 | Main §§2.1, 4–5 and Table 2 pp. 2, 4–5; appendix A4–A5 pp. 4, 6 | Add an endpoint key and comparator labels; replace bare “exact” for historical rows with “text-path agreement”; explicitly separate 60/90 historical text, 78/90 fresh IDs, and 60/72 reserved reference equality. | High: prevents an invalid cross-campaign reading. | Low: copy and caption consistency. |
| CR-09: central contribution and case-study scope | 6/6 | Title, abstract, introduction p. 1; §9 p. 10 | Lead with the frozen B570 complete-trajectory prediction and named tested stack; describe four independently frozen, configuration-specific cases rather than a matched hardware ranking. | High: changes the first-read acceptance test. | Low if numerical endpoints remain untouched. |
| CR-04: sufficiency versus unique cause | 6/6 | Abstract p. 1, §5.2 p. 5, Figure 3 p. 7, §9 p. 10 | State that target-only greedy micro-batch one reproduces the serialized B570 trajectory on this workload; note observationally equivalent paths and unknown numerical root cause. | High: calibrates the mechanism claim. | Low. |
| CR-10: nearby work at novelty boundary | 4/6 | Introduction p. 1; Related Work §8 pp. 9–10 | Compare the closest cited correctness/path and cost studies using their described endpoints; identify the prospective reserved full-trajectory prediction as the distinct test without claiming first discovery of path dependence. | High: addresses the weak-reject significance case. | Medium: precise prior-work characterization must be checked before editing. |
| CR-11: M4 Guard versus Always-Spec | 6/6 | Abstract p. 1; §7/Table 3 pp. 7–9 | Keep 1.3114× Guard and 1.3469× fixed-policy target-relative results adjacent; label the adverse paired ratio, direction, post-study status, conditional CI, and hindsight oracle. | Medium-high: prevents target-only gain being mistaken for policy improvement. | Low. |
| CR-12: 358H interface boundary | 4/6 | §§5.3, 7.1, 9 pp. 6–8, 10; Figure 4 p. 8 | Say “full-prefix replay/reconstruction plus proposal” and that its components were not isolated; state the candidate has no qualified speed endpoint. | Medium-high: protects causal interpretation. | Low for wording; high for any unplanned new intervention. |
| CR-02: simpler predictor comparison | 2/6 | §5.2 p. 5; appendix §J p. 6 | Put the already reported reserved 60/72 default-reference equality beside 72/72 micro-batch-one prediction, with 24-prompt/72-run units and four divergent prompts. Do not label an unrun alternative partition as a negative control. | Medium: makes the incremental prediction explicit. | Medium if new experiments or hypotheses are accidentally implied. |
| CR-03: transfer scope | 6/6 | §§5.2, 9 pp. 5, 10; appendix §J p. 6 | Explicitly limit inference to the tested B570 stack/model/greedy width/task family and name cross-backend transfer as future work. A separately frozen replication is optional for stronger generality. | Medium: bounds the systems claim. | Low for prose; high for a new experiment. **CONFLICT:** R4 sees significance as possibly below bar without transfer; others do not require it for the current bounded claim. |

## P2 — Nice to improve

| Issue | Reviewer count | Location | Exact recommended edit | Estimated manuscript impact | Risk of causing new problems |
|---|---:|---|---|---|---|
| CR-07: statistical units | 3/6 | §§3.2, 5.2, 7.3; appendix H–J | State 24 prompts / 72 repetitions / four divergent prompts / 12 divergent pairs together; qualify prompt-bootstrap CIs as conditional. | Moderate | Low |
| CR-08: exposure audit | 2/6 | §3.1; appendix §J | Add excluded task IDs or a compact audited inventory and keep “no known exposure in audited records.” | Moderate | Medium |
| CR-14: discovery-to-prediction visual | 3/6 | §§3.1, 5.2; Figure 2; appendix §J | Show exposed discovery, freeze boundary, reserved prediction, live outcomes, and one complete divergent sequence in a compact table/timeline. | Moderate | Low |
| CR-15: Figure 2 density | 6/6 | Figure 2 p. 6 | Reduce text and implied cross-case arrows; choose concise main-text map or appendix relocation after space allocation. | Moderate | Low; **CONFLICT** on placement. |
| CR-16: Figure 3 endpoint separation | 6/6 | Figure 3 p. 7 | Directly label panel A historical proxy/different contexts and panel B fresh direct-ID gate/no latency. | Moderate | Low |
| CR-18: Figure 4 labels | 3/6 | Figure 4 p. 8 | Label NPU region “replay + proposal (inseparable)” and stacked totals arithmetic means; distinguish headline prompt-GM ratios. | Moderate | Low |
| CR-20: Table 1 scope | 3/6 | Table 1 p. 4 | Add “independently frozen case studies; not a matched hardware comparison” and note co-varying stacks. | Moderate | Low |
| CR-17: blocked-row treatment | 2/6 | Table 2 p. 4; appendix A5 | Label B570 diagnostic timing as blocked directly in the row. | Small-moderate | Low |
| CR-06: strict RTX latency endpoint | 1/6 | §§4.2, 5.1; Figure 3B | State explicitly that fresh direct-ID qualification has no matching fresh latency; report timing only if genuinely recorded under a matched frozen path. | Small-moderate | Low for disclosure; medium for new measurement |
| CR-19: direct-ID gate counts | 1/6 | Figure 3B; appendix A5 | Move or duplicate the four-row exact-prompt counts beside Figure 3B if space allows. | Small | Low |

## P3 — Do not touch unless trivial

| Issue | Reviewer count | Location | Exact recommended edit | Estimated manuscript impact | Risk of causing new problems |
|---|---:|---|---|---|---|
| CR-13: evaluation cost illustration | 1/6 | §6 | Add actual run count if recorded; never invent wall-clock budget. | Small | Medium if unmeasured |
| CR-21: appendix A4 repetition | 2/6 | Appendix A4, §J | Compress repeated rows only if the comparator key remains and ledger space is needed. | Small | Low |
| CR-22: caption length | 1/6 | Figures 1, 4 | Shorten repeated definitions while keeping caveats next to the figures. | Small | Low |

## Changes that reviewers explicitly do NOT require

- **No new experiment as a condition of the current bounded claim.** The AC calls a second backend study optional; R4 would value it more heavily for significance, a recorded disagreement.
- **No second-backend mechanism transfer as a validity prerequisite** for the tested B570 prediction. It is needed only to claim transfer.
- **No new 358H state-persistence speedup claim** or forced performance run after an unqualified candidate; a future intervention would require its own gate and matched full-loop timing.
- **No mandatory extra figure or larger prompt set.** Several reviewers suggest a compact prediction table/timeline or more diverse reserve as useful, not a shared P0 requirement.
- **No presentation of historical text-path timings as strict direct-ID qualified results.** Label the comparator rather than manufacturing new retroactive evidence.
