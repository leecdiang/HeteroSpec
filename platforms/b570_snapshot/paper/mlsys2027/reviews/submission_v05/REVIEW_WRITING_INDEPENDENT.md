# Independent writing review G

## Scope and judgment

This review was prepared from the unchanged `main.tex`, all ten section sources, the separate `appendix.tex`, generated numerical definitions, and relevant table/figure source captions. I did not read other reviews or prior review commentary. This is an editorial assessment, not a new analysis of the archived experiments. No manuscript source was modified.

The paper has a defensible empirical story, and its unusually explicit inference boundaries are a strength. It is not yet as direct or unified as a submission-level narrative should be. The reader repeatedly encounters campaign governance, assertions of limited scope, and statements of what is not claimed before being able to state the positive contribution. The most consequential writing problem is therefore not insufficient caution; it is the placement and repetition of caution around an already modest contribution.

The strongest specific story is: in these consumer configurations, correctness qualification changes which measured verification paths can be used; complete stateful accounting changes the interpretation of isolated draft speed; and separately frozen runtime studies show the consequences of applying those two requirements. The 358H candidate stops at qualification. The M4 guard remains profitable against target-only, while Always-Spec has the higher aggregate speedup point estimate. The latter is a prospective bounded demonstration, not evidence that adapting improves performance. The manuscript should make that hierarchy visible early.

## Abstract

The current abstract is scientifically restrained and reports the crucial Guard-versus-fixed qualification. However, the opening question is cumbersome: “favorable local indicators,” “gains,” “integrated post-prefill speculative decode,” and “tested consumer configurations” all arrive before the reader receives a concrete finding. “We combine four retrospective hardware/runtime case studies … with separately frozen runtime studies” describes the research assembly more clearly than the intellectual result.

The abstract also gives a long sequence of values and eligibility outcomes without enough hierarchy. It spends two sentences on the M4 historical contrast, then compresses the RTX/B570 mechanism into one clause, then gives two 358H speedups, then introduces a new prospective M4 experiment. That sequence makes the paper feel like a campaign report. The ending correctly limits Guard, but “establishes bounded profitable control” is abstract phrasing that can still sound stronger than the comparative result. Give the observed Guard and Always-Spec results directly.

One asymmetry is avoidable: the historical HumanEval exact-pair count is included, but the prospective result says only “with exact outputs.” In a condensed abstract, the prospective 180/180 count **for each speculative condition** is the more useful exactness count because it accompanies the new runtime result and prevents ambiguity about pooled comparisons.

### Proposed abstract

> Fast drafting and cheap target batching do not guarantee faster speculative decoding on the consumer configurations studied here. We characterize four hardware/runtime configurations using greedy token equivalence to matched target-only execution and timing that excludes loading and initial prompt prefill. On the same MacBook Air M4 in separate sessions, a representative workload reaches 0.842× speedup, whereas a separately preregistered HumanEval workload reaches 1.387×; both are token-exact, but the contrast does not isolate workload effects. Path controls identify two failures of local promise. Correctness qualification excludes the tested cheap verification paths on RTX 5070 Ti Laptop and Arc B570. On Core Ultra X7 358H, an isolated NPU draft advantage does not survive stateful integration: exact CPU- and NPU-draft paths reach 0.734× and 0.352×, with complete target-side work and replay-plus-proposal dominating their respective costs. Separately frozen runtime studies test the resulting decisions. Qualification blocks the 358H intervention before formal performance evaluation. On 60 held-out M4 prompts, a one-way realized-cost guard achieves 1.3114× speedup over target-only (95% CI [1.2487, 1.3787]), compared with 1.3469× for fixed speculation; each speculative condition is token-exact in 180/180 comparisons. These results support configuration-specific diagnosis and demonstrate profitable prospective control, without establishing an advantage over fixed speculation.

This version retains the same scientific strength. It does not turn the historical M4 contrast into a causal workload result, imply a Guard advantage, pool exactness counts, or invent a 358H runtime performance result. If length is tight, remove historical point estimates before removing the explicit Guard comparator or qualification outcome.

## Introduction and contribution specificity

The introduction's first paragraph establishes an appropriate problem, and its second paragraph correctly prevents a hardware-only reading. The third paragraph is the strongest: it identifies concrete qualification and integration failures. Its final paragraph, however, spends roughly equal rhetorical effort describing what the authors assembled and disclaiming novelty. “Our contribution combines…” is less useful than stating what the measurement establishes.

Make the contribution paragraph do three explicit jobs, in this order:

1. State the empirical findings: an inexpensive batched target path can be unavailable under the selected output contract; isolated NPU throughput can misrepresent the complete integrated draft cost.
2. State the methodological contribution at its real scale: path-specific qualification and complete cost/commit accounting connect those findings to the allowed runtime decisions, without claiming a new accounting theory.
3. State the prospective outcomes with their comparator: 358H has no qualified intervention pair; M4 Guard is faster than target-only but its point estimate is below Always-Spec.

A compact three-sentence paragraph is sufficient; a large “contributions” list would not itself solve the problem. Preserve the independent historical M4 contrast as motivation for measuring outcomes, rather than presenting it as a mechanism explained by the two diagnoses. The current text already respects this distinction, but repeats it too often.

Move most of the introductory prior-art enumeration to Related Work. Keep a short sentence identifying this as configuration-scoped empirical evidence rather than a new speculative algorithm. At present the reader meets five citation keys and four non-novel areas immediately after the contribution, weakening recall of what the paper did establish.

## Sections 4–7: flow and the stitched-project impression

The basic sequence—outcomes, diagnoses, implications, runtime studies—is sound. The stitched-project impression comes from how often that sequence is announced and defended, and from a full hardware conclusion immediately before the runtime paper begins.

| Location | Editorial issue | Recommended revision |
|---|---|---|
| Section 4 opening | “Empirical puzzle” promises an explanation of the whole outcome table; Section 5 intentionally leaves the M4 contrast unexplained. | Say that the table establishes the observed outcomes and selects two failures for diagnosis. This aligns the promise with the evidence. |
| Section 4.1 | The historical M4 contrast is surrounded by separate caveats about pooling, capability, unified memory, session causality, discovery estimates, MLX history, energy, and an unexecuted synthetic ceiling. | Keep session confounding beside the contrast and energy scope beside energy. Move the historical MLX/discovery detail and synthetic-ceiling deviation to the existing limitations/appendix discussion, with a compact pointer if required. |
| Section 4.2 → Section 5 | The last sentence already makes a useful transition to measured boundaries. Section 5 then restates outcomes, scope, and the unassigned M4 contrast. | Let the transition carry the connection and start Section 5 with the two measured boundaries. |
| Section 5.1 opening | The first detailed example under “Execution-path qualification” is M4, expressly not an instance of the diagnosed failure. | Lead with the RTX opportunity and failed qualification. Use M4 later as a bounded reference, or retain it only in the figure caption/table if sufficient. |
| Section 5.2 | The isolated NPU advantage failing to survive integration appears at the start, again after the timing decomposition, and again in the Phase-2/Phase-3 discussion. | State the contrast once, explain it with the measured regions, and finish with the implication for using complete costs. Keep replay and proposal inseparable. |
| Section 6 | “Hardware-Study Synthesis,” the `hardwareconclusion` label, and three summary paragraphs create a first conclusion. Much of the content reappears in Section 7's opening and Section 10. | Reduce this to a short bridge at the end of Section 5, or retitle/recast it as the two concrete decisions that Section 7 tests. Avoid another outcome inventory. |
| Section 7.1 | Detailed intervention history arrives before the reader can easily distinguish the historical exact 358H paths from the new unqualified intervention. | Lead with that distinction: historical CPU/NPU paths were exact but slow; this separate candidate did not qualify, so no formal performance result exists. Then give the persistent-state and UB2 reasons. |
| Section 7.2–7.3 | The guard's implementation and calibration occupy substantial space before the modest comparative outcome becomes visible. | Preview the outcome/comparator in Section 7's opening, then retain the policy definition and frozen selection as the evidence for a prospective test. Do not suggest that fallback itself proved beneficial. |

The two runtime cases are asymmetric, and that is acceptable. The paper should explicitly present them as two observed outcomes of the same decision sequence, not as two completed optimization successes. No amount of stylistic smoothing should imply that the 358H runtime branch has a performance evaluation.

## Terminology and caveats

The contract itself is clear. The manuscript nevertheless asks readers to track “admissible,” “qualified,” “exact,” “token-exact,” “correctness-inadmissible,” “contract passes,” “formal gate,” “small gate,” and “full qualification.” Define and consistently use a small set: **token-exact** for the observed equality result, **qualified path** for a path admitted within its tested scope, and **qualification probe** versus **full-workload qualification** for the different tests. “Exact” should never silently expand into universal correctness. The existing distinction between HumanEval equality and functional correctness should remain.

“Frozen” and “separately frozen” appear so often that they become punctuation. They matter when defining the retrospective hardware synthesis, prospective policy selection, and held-out boundary. They are less useful in every restatement of a result. State the study chronology and freeze boundaries once in Methods, keep the essential reminder at the runtime transition, and let the remaining sentences report the findings.

Similarly, replace internal campaign terminology with reader-facing terms where possible. “Closed Phase-3 heterogeneous runner,” “header-only blocked-preflight derivative,” “formal R2,” and `STRONGLY_SUPPORTED` require knowledge of the project's ledger. The main text can say “completed heterogeneous study,” “excluded preliminary artifact,” “formal runtime performance evaluation,” and “source identity is strongly supported but not proven.” Preserve exact internal labels in reproducibility details where necessary. Appendix references to “R2 is unauthorized” should explain the experimental consequence rather than rely on an unexplained governance code.

The main inferential caveats are indispensable: strict output contract; tested configuration/workload scope; separate-session M4 comparison; post-prefill boundary; blocked B570 timing; forward-only versus complete round costs; aggregate versus prompt estimators; no Guard superiority; no 358H runtime performance. Keep each beside the claim it qualifies and summarize it once in Limitations. Repeating all of them in framing, results, synthesis, captions, limitations, and conclusion does not improve precision.

The abstract/title use “consumer systems” broadly, while the evidence concerns specific model/runtime/device paths. The current text mostly narrows this correctly. Preserve “tested configurations” at the major scope statements; do not solve repetition by removing the model/runtime limits everywhere.

## Conclusion

The conclusion is accurate and avoids a false Guard win. It nevertheless repeats the opening sentence of Section 6 nearly verbatim, and its final phrase—“a measured runtime decision process whose usefulness depends on both the admitted path and its realized cost”—is less concrete than the findings preceding it. “Usefulness” is especially imprecise because the held-out comparison does not show added value over Always-Spec.

A tighter ending should leave three facts in memory: correctness removed measured cheap paths; complete stateful costs reversed the interpretation of isolated drafting; the runtime follow-through yielded a blocked 358H intervention and an exact, profitable M4 guard without an advantage over fixed speculation. An optional replacement is:

> In the tested consumer configurations, cheap component execution did not establish faster speculative decoding. Correctness qualification excluded cheap verification paths, and complete stateful measurements showed why an isolated NPU draft advantage did not survive integration. Separately frozen runtime studies produced two bounded outcomes: the 358H intervention stopped before formal performance evaluation, while an M4 realized-cost guard achieved 1.3114× held-out speedup over target-only with 180/180 exact comparisons. Fixed speculation reached 1.3469× and was also exact in 180/180 comparisons. The evidence supports qualifying the execution path and measuring its complete cost; it does not establish that this guard improves on fixed speculation or generalizes beyond the tested model/runtime configuration.

## Top five editorial changes

1. **Lead with the two specific empirical findings and the bounded prospective outcome.** Replace the abstract's opening question and the introduction's “we combine studies” contribution framing with what was established.
2. **Remove the mid-paper conclusion.** Convert Section 6 into a short bridge from the two measured boundaries to qualification and cost control, reducing the sense that the runtime study is attached after a finished paper.
3. **Consolidate caveats without weakening them.** Keep each essential boundary next to its claim; move repeated qualification history and internal provenance vocabulary to the existing appendix/limitations account.
4. **Make the runtime comparator explicit at first mention.** Guard is 1.3114× versus target-only; Always-Spec is 1.3469×; each has 180/180 exact comparisons. The 358H candidate has no formal runtime performance result. These are the contribution's limits, not a late qualification.
5. **Standardize path/status terminology and finish concretely.** Use a stable vocabulary for observed equality, qualification probes, and qualified scope; replace internal phase codes in the narrative; end with the observed outcomes rather than the broad “usefulness” of a decision process.
