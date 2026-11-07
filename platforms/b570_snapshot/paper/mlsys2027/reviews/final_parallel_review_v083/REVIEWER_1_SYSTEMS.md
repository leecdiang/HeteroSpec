Artifact-only review.
Sources consulted:
  - manuscript-v0.8.3.pdf
  - appendix-v0.8.3.pdf

No README, handover, source files, repository evidence, prior reviews, Git history, PR descriptions, experiment logs, or web searches were used.

## 1. Paper summary

The paper studies whether speculative decoding's favorable local measurements survive two systems constraints: preservation of a specified greedy output trajectory and the complete cost of executing the draft and target together. Its consumer-device campaigns are separate case studies, not a controlled hardware comparison. Historical M4 studies show both a 0.842× slowdown on a representative prompt set and a 1.387× speedup on HumanEval, but their equality endpoint is reconstructed CLI text. New direct generated-token-ID studies find that serialization qualifies the tested RTX path at 90/90 pairs after batching qualifies only 75/90, while the B570 remains blocked at 78/90 even after serialization. On B570, an outcome-exposed discovery set identifies target-only micro-batch-one execution as a predictor of the serialized trajectory. The predictor and 72 capped, complete ID sequences are frozen before reserved live outcomes; all 72 match, including 12 repetitions across four reference-divergent tasks. On 358H, a faster isolated NPU draft yields slower integrated decoding; a combined prefix-reconstruction-and-proposal call occupies 58.35% of NPU path time, while target-side work occupies 87.34% of CPU path time. A subsequent 358H intervention fails output qualification. Finally, a qualified M4 cost guard beats target-only on 60 held-out prompts but loses a paired secondary comparison against fixed speculation. The contribution is a carefully bounded diagnostic and qualification sequence, rather than a new universally faster speculative decoder. [Manuscript pp. 1–2, 4–10; Appendix pp. 5–8.]

## 2. Thesis

An execution path must be qualified against its intended output before its speed can count as an optimization; component throughput or target-forward batching alone cannot establish realized speedup. A frozen target-partition predictor can explain the tested B570 trajectory at the level of predictive sufficiency, while complete timing exposes a different integration bottleneck on the tested 358H path. [Manuscript §§2, 5–6.]

## 3. Top contributions, ranked

1. **Prospective B570 trajectory prediction:** 72/72 reserved complete generated-ID sequences predicted by target-only micro-batch-one execution, including all 12 reference-divergent repetition pairs. This turns a plausible diagnosis into a falsifiable, held-out mechanism test. [Manuscript §5.2; Appendix §J.]
2. **Direct-ID path qualification:** two fresh, frozen 90-pair gates show RTX serialized 90/90 versus batched 75/90, and B570 serialized 78/90 versus fast 60/90, with historical timing kept separate. [Manuscript §5.1, Fig. 3; Appendix Table A5.]
3. **Realized-cost accounting on 358H:** exact-output CPU/NPU paths are both slower despite the NPU's isolated draft advantage, with complete target and combined draft-interface timing. [Manuscript §§4.2, 5.3, Fig. 4; Appendix §D.]

## 4. Strongest contribution

The B570 frozen prediction is strongest. A target-only path that uses micro-batch one matches a serialized speculative path's *entire* capped greedy trajectory, even when both depart from the UB128 reference. Predicting the four divergent tasks is substantially more discriminating than reproducing the 20 reference-equal tasks: it rules out the trivial explanation that both paths merely returned the ordinary reference sequence. The design separates exposed discovery (12 tasks, 36/36) from deterministic reserved selection after a conservative exposure audit; it fixes predictor semantics and all 72 predicted arrays before the first reserved live run. The reported 72/72 agreement, 24/24 classifications and 12/12 first-divergence locations support a useful path-level hypothesis. The paper appropriately does not identify a kernel, floating-point operation, or universal micro-batch rule. The number of *distinct* divergent trajectories is four, so this remains a strong case-specific prediction rather than broad mechanism generalization. [Manuscript pp. 3, 6; Appendix pp. 6–8.]

## 5. Strongest empirical result

The B570 predictor/live endpoint is **72/72 exact capped generated-token-ID sequences** on 24 reserved HumanEval tasks × three repetitions; the same live runs match the frozen reference only **60/72**, and the predictor gets the first divergence index right in **12/12** repetition pairs over four tasks. The sharp within-run contrast makes the result informative about the tested execution partition. [Manuscript §5.2; Appendix Tables A6–A7.]

## 6. Strengths

1. The paper defines the output contract, timed regions, and evidence classes explicitly; it declines to call blocked-path speed a deployable gain. [Manuscript §2.]
2. The B570 discovery/reservation boundary, 31-task conservative exclusion, digest, chronology, and divergence examples make the prediction test unusually transparent in the PDFs. [Manuscript §5.2; Appendix §J.]
3. RTX/B570 fresh direct-ID counts are segregated from historical text-derived timing, preventing a common correctness/performance conflation. [Manuscript Fig. 3, Table 2; Appendix §I.]
4. 358H accounts for complete committed progress and separates arithmetic total-time ratios from prompt-geometric-mean headline ratios; it does not subtract incompatible proxy measurements to invent replay-only cost. [Manuscript §§2.3, 5.3; Appendix §D.]
5. The M4 Guard result and failed 358H intervention are reported honestly: neither is sold as an incremental optimization success. [Manuscript §7, Table 3; Appendix §H.]

## 7. Weaknesses

1. **MAJOR — significance/scope:** The central predictive mechanism is validated on one B570 Vulkan stack, one Qwen pair, greedy k = 2, capped HumanEval outputs, with only four independent reference-divergent reserved tasks. There is no second backend or model test of the target-partition prediction. This limits the reach of the systems lesson even though the within-stack result is sound. [Manuscript §9; Appendix §J.]
2. **MODERATE — missing evidence:** The appendix shows a prediction-file SHA-256, chronology, truncated per-task digests, and divergence tokens, but not the 72 full arrays or an independently inspectable commitment artifact in the anonymous PDFs. The reader can assess the declared protocol and selected discriminating examples, but cannot reproduce the 72 full-sequence comparisons from the PDFs alone. [Appendix pp. 7–8.]
3. **MODERATE — significance:** The paper offers a qualification/diagnostic workflow, but no successful improved runtime relative to a qualified fixed-speculation comparator. The M4 Guard is 2.71% slower than Always-Spec in the reported paired secondary estimate, and the 358H intervention never reaches performance evaluation. This is a legitimate negative systems result but narrows immediate deployment value. [Manuscript §7, Table 3.]
4. **MODERATE — missing comparison:** On 358H, replay/reconstruction and proposal share one synchronous timing region, so the work cannot establish how much gain state persistence would recover. The proposed intervention is blocked. A narrower accounting claim is well measured; the actionable counterfactual remains unknown. [Manuscript §§5.3, 7.1; Appendix §D.]
5. **MINOR — clarity:** The narrative traverses historical M4/RTX/B570 performance, new RTX/B570 qualification, B570 prediction, 358H accounting, then two runtime decisions. Even with careful labels, Table 2's B570 60/90 text-path row near fresh B570 60/90 direct-ID counts can slow first-pass comprehension. [Manuscript pp. 4–9.]

## 8. Claim–evidence audit

| Claim | Judgment | PDF evidence and boundary |
|---|---|---|
| A. Execution-path qualification | **WELL SUPPORTED** | §2 defines strict generated-ID equality; §5.1 and Fig. 3 report frozen 90/90 gate outcomes, and §7.1 actually stops the 358H intervention after failure. Eligibility is workload/path specific, not universal. [Manuscript pp. 2, 5–6, 8; Appendix §I.] |
| B. RTX direct-ID | **WELL SUPPORTED** | Batched 75/90 and serialized 90/90 over the fresh shared HumanEval30 protocol; Appendix A5 gives 25/30 and 30/30 equal prompts. Fresh latency is absent, and historical driver/reference differ. [Manuscript §5.1, Fig. 3B; Appendix pp. 5–6.] |
| C. B570 direct-ID | **WELL SUPPORTED** | Fast 60/90, serialized 78/90 in the new study; both below the gate. Distinct reserved follow-up has reference/live 60/72. These counts must not be merged with older text-path 45/90 and 60/90. [Manuscript §§5.1–5.2; Appendix Tables A5–A6.] |
| D. B570 target-partition mechanism | **SUPPORTED WITH CAVEAT** | Target-only UB1 predicts 36/36 discovery and 72/72 reserved serialized trajectories, including divergent outputs, supporting tested predictive sufficiency. The changed target partition is not isolated to a unique numerical operation; only one stack/path was studied. [Manuscript §5.2; Appendix §J.] |
| E. 72/72 held-out prediction | **SUPPORTED WITH CAVEAT** | Protocol, freeze chronology, full-file digest, task ledger and four divergence examples are visible; complete arrays and independently verifiable temporal artifacts are not themselves embedded in the PDFs. “Complete” means generated IDs up to the frozen 128-token/EOG endpoint. [Manuscript pp. 3, 6; Appendix pp. 6–8.] |
| F. 358H realized cost | **WELL SUPPORTED** | 90 exact pairs/path, 13.25-s CPU and 27.54-s NPU mean versus 9.58-s baseline, 87.34% target side on CPU, 58.35% combined replay/proposal on NPU. Replay alone and persistence savings are unmeasured. [Manuscript Fig. 4, §5.3; Appendix §D.] |
| G. M4 runtime | **WELL SUPPORTED** | Held-out 60 × 3 design, 180/180 direct-ID pairs per speculative policy, Target/Guard 1.3114×, Target/Always-Spec 1.3469×, secondary Guard/Always-Spec latency 1.0271 [1.0130, 1.0436]. The metadata hash defect is described and recovery asserted, while the secondary contrast was post-study. [Manuscript §7.3, Table 3; Appendix §H.] |

## 9. Audit of the 72/72 result

| Test | Verdict | Explanation |
|---|---|---|
| Reviewer-visible | **PARTIAL** | Appendix §J provides task IDs, lengths, pair counts, truncated sequence hashes, a full prediction-file digest, freeze-relative times, and four first-divergence token examples. It does not expose the complete arrays or independent timestamped artifact in these PDFs. |
| Complete generated-token-ID sequences | **YES** | Endpoint is the first 128 committed generated IDs or inclusive earlier EOG, with prompt and uncommitted proposal IDs excluded; sequence length and every generated ID must match. All 24 ledger lengths are 128. “Complete” is within this capped output contract. [Appendix pp. 5–8.] |
| Frozen before live outcomes | **YES** | The stated chronology finalizes 72 arrays at T0 + 1722.38 s and starts first live outcome at T0 + 1813.75 s, a 91.37-s gap; the digest identifies the frozen contents, while chronology is a documented assertion. [Appendix p. 7.] |
| Separate reserved discovery | **YES** | Twelve outcome-exposed discovery tasks choose H1 at 36/36. A 31/164 exclusion audit and deterministic rank select 24 reserved tasks among 133 eligible tasks, with no known B570 exposure in audited records. [Manuscript pp. 3, 6; Appendix p. 6.] |
| Falsifiable | **YES** | H1, inputs, 72 arrays, endpoint, and all-or-nothing 72/72 criterion precede live outcomes. Four predicted deviations from reference make failure plainly possible; H2 would only have been tried if H1 failed discovery and was not run. [Appendix §J.] |
| Avoids unique-cause leap | **YES** | The manuscript explicitly limits its inference to tested target-partition sufficiency and disclaims a kernel, operation, universal UB1 rule, or common RTX/B570 cause. [Manuscript §§5.2, 9; Appendix p. 6.] |

## 10. Historical text equality versus fresh direct-ID

**VERY CLEAR.** The abstract names “fresh direct-ID studies”; the first Introduction page says they do not certify historical timing; §2.1 defines H/Q/P evidence; Table 2 labels historical rows “Text-path” and Fig. 3 explicitly separates historical target-forward proxies from fresh ID gates with “no matching fresh latency endpoint.” Appendix §§B and I reinforce the comparators and non-transfer of certification. The coincident numerical 60/90 B570 values still require attention, but the manuscript consistently labels their distinct origins. [Manuscript pp. 1–2, 5–6; Appendix pp. 1, 5–6.]

## 11. Population, exclusions, and scope

**SIGNIFICANCE CONCERN.** Fresh qualification covers 30 shared HumanEval prompts × three repetitions, one Qwen3-8B/0.6B Q8_0 pair, greedy k = 2, capped 128 IDs, and separately configured RTX CUDA and B570 Vulkan runs. The B570 predictor's 24 reserved tasks come from 133 eligible HumanEval tasks after excluding 31/164 with any B570 association in 8,706 audited records; 12 explicitly exposed tasks are discovery, and “no known exposure” is limited to the audit. The reserved three repetitions are repeat-stable, making the 72 comparisons mainly 24 distinct trajectories, four distinct reference-divergent ones. M4 Guard uses 60 held-out prompts balanced across HumanEval and Spec-Bench, but one M4 configuration and an already favorable fixed speculation condition. Historical cases differ in sessions, front ends, contexts, and sometimes quantization. These restrictions are disclosed and do not themselves invalidate the within-path tests, but they cap generalizable MLSys significance. [Manuscript §§3, 5, 7, 9; Appendix §§I–J.]

## 12. First-page test

Using only the title, abstract, and first Introduction page: the title promises a systems qualification and realized-cost study rather than an optimized decoder. In three minutes I would identify the central story as a sequence of *qualify output → predict a blocked trajectory → charge full integration cost*, though the four platforms and Guard result make it feel initially broad. The abstract's **72/72 complete-ID prediction** is prominent and the Intro immediately repeats its reserved/frozen nature and caveat. Generic “benchmark your own system” confusion is mitigated by a prospective predictor of reference-divergent B570 trajectories; the exact target-partition hypothesis should be stated even more concretely in the abstract or first Intro paragraph. Novelty is asserted early as frozen prediction and direct-ID qualification, while the distinction from existing batch-shape/numerical-path work is only sketched on that page. [Manuscript p. 1 only.]

## 13. Figures and tables

| Item | Necessary / readable / informative | Redundancy or risk |
|---|---|---|
| Table 1, frozen systems | Necessary and compact; flags independent stacks and evidence classes. [Manuscript p. 3.] | “Evidence scope” mixes historical and later work; add a separate fresh follow-up marker for a quick scan. |
| Figure 1, M4 regimes | Readable and informative to prevent cherry-picking the profitable code workload. [p. 4.] | Same hardware but differing sessions means the juxtaposition cannot identify workload causality; caption says so. |
| Table 2, headline outcomes | Necessary numerical overview with comparator and class columns. [p. 5.] | It combines historical text-path and 358H direct-ID rows; correct labels mitigate, but visual separation would help. |
| Figure 2, evaluation sequence | Readable conceptual map. [p. 5.] | Somewhat redundant with §§2 and 6; it should remain only if space allows the more substantive evidence figures. |
| Figure 3, proxies and direct-ID | Necessary and readable, especially “no matching fresh latency endpoint” and 90/90 gate. [p. 6.] | Side-by-side panels can imply paired measurements at first glance, but the explicit captions correct this; do not connect panel A/B marks. |
| Figure 4, 358H throughput/cost | Necessary, informative and generally readable. [p. 7.] | The prominent 58.35% blue segment combines reconstruction *and* proposal; legend and caption explicitly say inseparable. A viewer should not interpret it as replay-only. |
| Table 3, M4 runtime | Necessary; reports Guard, fixed speculation, oracle and secondary paired contrast in one place. [p. 9.] | Secondary contrast's inline typography is crowded; its post-study status is adequately explicit. |
| Appendix A1–A2, estimators/energy | Useful lookup; readable. [Appendix p. 2.] | Exact bootstrap-order details are specialized but justify endpoint reproduction. |
| Appendix A3–A4, proxy/evidence inventory | A3 is necessary for Fig. 3A's 11 cells; A4 is a useful status map. [Appendix pp. 3–4.] | A4 overlaps Table 2 and prose but helps prevent endpoint category errors. |
| Appendix A5–A6, qualification/prediction | Necessary, crisp comparison of distinct direct-ID gates and reserved predictor/reference result. [Appendix pp. 6–7.] | Keep the 78/90 versus 60/72 populations explicit. |
| Appendix A7, reserved ledger | Necessary reviewer-facing granularity; readable task rows and divergent IDs. [Appendix p. 8.] | Only truncated hashes and first-divergence token pairs are visible, so the table alone cannot audit full-array equality. |

## 14. Related Work

Based only on the PDFs, §8 credits speculative decoding's algorithmic basis, consumer Apple performance and output variation, vLLM verification and cost studies, heterogeneous placement and state reuse, numerical determinism and correctness forensics, and adaptive controls. It explicitly concedes that slowdowns, correctness gating, target batch-shape argmax changes, heterogeneous placement, and adaptive control are established; this is fair positioning. Its narrower distinction is the prospective RTX/B570 direct-ID gate, then a frozen B570 target-partition predictor of complete reserved trajectories, plus measured combined state-interface cost on 358H. The paper should resist any reading that output qualification itself, micro-batch sensitivity, or a generic cost decomposition is new. The citations and characterization cannot be independently checked under this artifact-only scope, but the manuscript's stated differentiation is scientifically cautious. [Manuscript pp. 1, 2, 9; Appendix p. 2.]

## 15. Single strongest objection

If I were arguing against acceptance, I would say... the one genuinely discriminating mechanism result is a four-task set of repeat-stable reference-divergent trajectories on one B570 model/runtime/path, while the broader paper has no demonstrated improvement over qualified fixed speculation and no successful 358H intervention. Existing literature already recognizes numerical batch-path dependence and integration costs, so this is a rigorous but narrowly generalizable diagnosis rather than a sufficiently consequential new MLSys system or broadly validated principle. [Manuscript §§5.2, 7–9; Appendix §J.]

## 16. Single strongest argument for acceptance

If I were arguing for acceptance, I would say... a prospective, complete-trajectory prediction of **72/72** reserved serialized outputs, including every reference-divergent case, is a much stronger systems diagnosis than post hoc attribution of a mismatch to “numerics.” Coupled with correctly gated RTX/B570 paths, exact 358H cost accounting, and candid negative control results, it offers a replicable way to decide whether a proposed speculative path is admissible and whether its component advantages can survive integration. [Manuscript §§2, 5–7; Appendix §§D, I–J.]

## 17. Requested changes

**MUST FIX**

- In §5.2 and the Fig. 3-to-B570 transition, state plainly that the 72/72 result contains **24 distinct reserved prompts, of which four are reference-divergent**, with three repeat-stable executions per task. This prevents a reader from treating 72 as independent trajectories. [Manuscript pp. 5–6; Appendix pp. 6–8.]
- In the abstract and Conclusion, retain the “tested stack/path” qualifier immediately adjacent to “target-partition sufficiency,” and define “complete” as complete within the 128-token/EOG generated-ID endpoint on first mention. The present body/appendix clarify this, but the headline could otherwise travel without the boundary. [Manuscript pp. 1, 10; Appendix p. 7.]

**SHOULD FIX**

- Add a small first-page statement of the discriminating counterfactual: UB128 reference differs from serialized B570 output on four reserved tasks, while UB1 target-only predicts the serial output at those positions. [Manuscript p. 1 and §5.2.]
- Make Table 2 visually group historical text-path performance separately from 358H direct-ID performance, and cross-reference the fresh direct-ID-only Figure 3 above the table. [Manuscript p. 5.]
- In §5.3/Fig. 4, give the combined NPU OpenVINO call an unambiguous label such as “full-prefix reconstruction **plus** proposal, inseparable”; keep any potential benefit of persistence explicitly unmeasured. [Manuscript p. 7.]
- If page budget permits, include a reviewer-accessible anonymized commitment artifact or compact recipe for checking the 72 full arrays, rather than relying solely on a file digest and abbreviated task hashes in Appendix §J. [Appendix pp. 7–8.]

**OPTIONAL**

- Move the less central Figure 2 to the appendix to free main-text space for a small prediction/reference/live example. [Manuscript pp. 5–6.]
- Add a matched second-backend or second-model target-partition prediction study if available; clearly mark it separate from the frozen B570 validation. This would materially improve generality, but is not required to validate the current B570 claim. [Manuscript §9.]

## 18. Recommendation

**WEAK ACCEPT.**

## 19. Confidence

**4/5.** I can assess the claims and protocol from both PDFs, including the visible chronology and ledgers. I cannot independently replay the experiments or verify full arrays from these PDFs alone.

## 20. Decision rationale

The novelty is a prospective prediction of an exact, capped generated-ID trajectory on a blocked execution path, rather than discovery of batch-shape sensitivity or a new decoding algorithm. The frozen reserve, all-or-nothing endpoint, and prediction of the four reference-divergent tasks make that contribution credible and useful. The separate direct-ID gates and 358H timing decomposition add disciplined systems evidence; negative intervention and Guard results are reported without claiming an optimization win. Clarity is high after the first page, particularly about text-derived historical equality and the lack of fresh latency. Significance is the borderline dimension: the predictive result covers one stack and four independent divergent prompts, the NPU cost components cannot be separated, and there is no transfer or improved runtime beyond a qualified fixed comparator. I lean weak accept because the discriminating held-out prediction and rigorous qualification discipline together rise above a collection of benchmarks, while treating the paper as a bounded case-study contribution. [Manuscript §§5–9; Appendix §§D, H–J.]

## Special Questions

1. **Q1: E — coherent B+C+D.** Execution-path qualification (B) is the gate, predictive target-partition mechanism (C) is the distinctive test, and heterogeneous realized-cost accounting (D) shows why favorable local measurements need not pay. The M4 guard is a bounded downstream test, not the central contribution. [Manuscript §§5–7.]
2. **Q2: CLEARLY YES.** Freezing complete B570 trajectories before reserved live execution and predicting the otherwise divergent outputs goes beyond benchmarking the author's own system. [Manuscript §5.2; Appendix §J.]
3. **Q3: YES.** Without the freeze and 72/72 held-out comparison, target-partition sufficiency would remain a plausible post hoc diagnosis, materially weakening the publication case. The effective divergent sample remains four tasks. [Appendix §J.]
4. **Q4: YES.** A comparably frozen successful prediction on a genuinely distinct backend would address the principal significance/scope objection and could move my recommendation from weak accept to accept. [Manuscript §9.]
5. **Q5: NO.** Lack of transfer does not invalidate the path-scoped RTX/B570 gates, B570 prediction, or 358H measurements; the paper already disclaims backend-wide causal claims. [Manuscript §§5, 9.]
6. **Q6: Useful supporting.** The 358H complete timing counterexample supplies the second practical boundary; its combined replay/proposal region cannot yet test the state-persistence counterfactual. [Manuscript Fig. 4, §7.1.]
7. **Q7: Useful supporting.** The M4 Guard experiment confirms output qualification and honest comparison to fixed speculation, but the lack of incremental benefit means it should stay secondary in the story. [Manuscript §7, Table 3.]
8. **Q8: NONE FOUND.** The tempting inferences—unique B570 numerical cause, strict-ID certification of historical speedups, replay-only 358H cost, and Guard's superiority to fixed speculation—are explicitly disclaimed in the manuscript. The headline “complete” still merits an adjacent reminder of the 128-token/EOG endpoint. [Manuscript pp. 1–2, 6–10; Appendix §J.]
