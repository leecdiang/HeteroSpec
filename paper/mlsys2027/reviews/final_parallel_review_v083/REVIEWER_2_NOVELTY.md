Artifact-only review.
Sources consulted:
  - manuscript-v0.8.3.pdf
  - appendix-v0.8.3.pdf

No README, handover, source files, repository evidence, prior reviews, Git history, PR descriptions, experiment logs, or web searches were used.

## 1. Paper summary

The paper argues that speculative decoding on consumer systems should be evaluated in three steps: qualify the generated output under a specified execution path, diagnose a blocked path with controlled predictions, and measure the cost of the entire integrated loop. It assembles separately frozen studies of an M4, an RTX 5070 Ti Laptop, an Arc B570, and a Core Ultra X7 358H. The fresh RTX direct-ID study finds 75/90 batched and 90/90 serialized matches; the corresponding B570 study finds 60/90 fast and 78/90 serialized matches, so B570 fails the stated 90/90 gate. On B570, a target-only micro-batch-one path is chosen after exposed discovery and frozen before reserved live speculative outputs. It matches all 72 complete generated-ID sequences for 24 reserved HumanEval prompts, including 12 repetitions on four reference-divergent prompts. This is evidence that the tested target partition suffices to predict the serialized trajectory, not identification of a numerical root cause. The 358H decomposition finds that isolated NPU draft throughput does not translate into integrated speedup: the qualified NPU path is 0.352× target-only, and its combined replay/reconstruction-plus-proposal call takes 58.35% of integrated time. A later intervention cannot pass qualification. Finally, a held-out M4 guard preserves direct IDs and beats target-only, but a secondary paired comparison finds fixed speculation faster. The historical speedups have weaker, text-derived output comparators and are not strict-ID performance results. (Manuscript pp. 1–2, 4–9; appendix pp. 5–8.)

## 2. Thesis

The defensible new finding is a prospectively frozen, complete-sequence prediction of one correctness-blocked B570 execution path from a target-only partition control. The qualification and realized-cost studies give this finding practical context, but the three are distinct case studies rather than a validated general mechanism or transferable optimization method. (Manuscript pp. 1, 6–10.)

## 3. Top contributions, ranked

1. **B570 predictive target-partition sufficiency:** 72/72 reserved complete-sequence predictions, including 12/12 reference-divergent repetitions, after outcome-exposed discovery and a stated freeze. This is the strongest distinction from retrospective numerical-path diagnosis. (Manuscript p. 6, §5.2; appendix pp. 6–8, §J, Tables A6–A7.)
2. **Fresh output-path qualification with strict generated IDs:** different results for RTX serialization and B570 serialization under each study's frozen 90/90 gate, cleanly separated from older timing. The measurement is valuable, though qualification itself and batch-shape sensitivity are established ideas. (Manuscript pp. 5–6, §5.1, Fig. 3B; appendix p. 6, Table A5.)
3. **Integrated 358H cost accounting:** a qualified CPU/NPU comparison, with complete progress and timed regions, showing a state-interface bottleneck on the tested NPU adapter and target-side dominance on CPU. This is a concrete systems case, not a new cost identity or state-reuse technique. (Manuscript pp. 2, 7–8, §§2.3, 5.3; appendix p. 1, §D.)

## 4. Strongest contribution

The B570 result is the closest thing to a distinctive scientific contribution. A post hoc observation that micro-batch one happens to agree would be unsurprising after known batch-shape effects. Here the authors first show that their target-only harness reproduces the 90/90 reference sequences, use 12 outcome-exposed prompts only to select the hypothesis, freeze the target-only UB1 predictor and the reserved task IDs, then commit 72 predicted complete generated-ID arrays before running reserved serialized speculation. Four reserved prompts actually diverge from the UB128 reference, and the frozen predictor gets their first-divergence positions and complete trajectories right in all 12 repetitions. This is harder to dismiss as simply predicting the majority reference-equal prompts. The protocol supports **tested-path sufficiency**, while the paper appropriately declines to infer a unique kernel, numerical operation, general B570 property, or RTX transfer. Its main remaining novelty question is whether a single fixed-model, fixed-stack partition control is sufficiently general to be a publication-level systems insight. (Manuscript pp. 3, 6, §5.2; appendix pp. 6–8, §J, Tables A6–A7.)

## 5. Strongest empirical result

The frozen B570 UB1 target-only predictor matches **72/72 complete generated-token-ID sequences** over 24 reserved prompts × 3 repetitions, while the UB128 reference matches the same live serialized outputs in only **60/72**. All four reference-divergent prompts are predicted correctly in 3/3 repetitions each, with matching first-divergence indices in **12/12** pairs. This contrast, rather than the raw 72/72 alone, makes the result informative. (Manuscript p. 6, §5.2; appendix pp. 6–8, Tables A6–A7.)

## 6. Strengths

1. The paper states an exact output contract and labels historical text-derived agreement, direct-ID qualification, and frozen predictor/live agreement separately. (Manuscript p. 2, §2.1.)
2. The B570 holdout uses a conservative recorded-exposure exclusion, deterministic selection, explicit complete-sequence criterion, and a recorded prediction-before-live chronology. (Manuscript pp. 3, 6; appendix pp. 6–8.)
3. It reports negative and blocked results, including the failed B570 gate and the 358H intervention stopped before formal performance testing. (Manuscript pp. 5, 8.)
4. It measures 358H complete committed progress and integrated timed regions instead of equating draft throughput or a target-forward proxy with end-to-end gain. (Manuscript pp. 2, 7; appendix p. 1.)
5. It credits prior work on numerical nondeterminism, verification bottlenecks, heterogeneous placement, and adaptive control, and explicitly says the M4 guard has no incremental benefit over fixed speculation. (Manuscript pp. 8–9, §§7–8.)

## 7. Weaknesses

1. **MAJOR — significance:** The only clearly distinctive positive mechanism result is a predictor on one B570 stack, one Qwen pair, one workload family, one greedy setting, and one serialized path. There is no second-backend predictive transfer or independent mechanism intervention; the broader evaluation sequence is sensible but mostly known practice. (Manuscript pp. 6, 9–10.)
2. **MAJOR — missing evidence:** The PDFs publish a digest, chronology, summary ledger, and 12-character per-prompt digests, but not the 72 full committed arrays or full live arrays. An artifact-only reader cannot independently compare those arrays or verify temporal ordering beyond the authors' recorded chronology. This limits independent scrutiny of the central novelty claim; it is not evidence that the underlying archive is absent. (Appendix pp. 7–8, Tables A6–A7.)
3. **MODERATE — missing comparison:** The target-partition predictor is compared with UB128 reference and live serialized output, but no similarly frozen alternative partition or simple predictor is tested on the reserved set. The H2 fixed-proposal branch is not built because H1 passes. This does not invalidate H1 sufficiency, but it limits causal discrimination and the claim's conceptual distance from trying a known batch-shape control. (Manuscript p. 6; appendix p. 6, §J.)
4. **MODERATE — scope:** The four hardware studies are frozen separately and have different runtimes, contexts, references, quantization in one case, and evidence endpoints. The 358H diagnosis cannot explain the M4 contrast, and no cross-platform causal progression is established. (Manuscript pp. 3, 5–6, 10.)
5. **MINOR — clarity:** The abstract devotes substantial space to the negative 358H/M4 results and hardware counts. Although the 72/72 is prominent, a reader could still read the paper as a broad consumer-hardware benchmark rather than a narrowly predictive execution-path study. (Manuscript p. 1, title, abstract, first introduction page.)

## 8. Claim–evidence audit

| Claim | Rating | Artifact-only assessment |
|---|---|---|
| A. Execution-path qualification | **WELL SUPPORTED** | The contract, gate, exclusions, and distinction among H/Q/P are explicit. Qualification remains relative to the frozen reference, workload, and path, not universal correctness. Manuscript pp. 2, 5–6, §§2.1, 5.1; appendix pp. 5–6, §I, Table A5. |
| B. RTX direct-ID | **WELL SUPPORTED** | The prospective batched 75/90 versus serialized 90/90 outcome is stated with a 90/90 gate and trace capture. It does not certify older RTX speedups or offer fresh latency. Manuscript pp. 5–6, Fig. 3B; appendix p. 6, Table A5. |
| C. B570 direct-ID | **WELL SUPPORTED** | Fast 60/90 and serialized 78/90 remain blocked. The separate reserved predictor study's reference/live result is 60/72, not a contradictory reclassification. Manuscript pp. 5–6, §§5.1–5.2; appendix pp. 6–7, Tables A5–A6. |
| D. B570 target-partition mechanism | **SUPPORTED WITH CAVEAT** | Harness/reference 90/90, discovery 36/36, and frozen reserved predictor/live 72/72 support sufficiency of the tested UB1 target-only path. They do not isolate a kernel or prove that target partition is the unique cause of the discrepancy. Manuscript p. 6, §5.2; appendix pp. 6–8, §J. |
| E. 72/72 held-out prediction | **SUPPORTED WITH CAVEAT** | The PDFs give the freeze sequence, times, content digest, 24-row ledger, 72/72 total, and four divergent cases; the actual complete arrays and independently checkable chronology are not inside these PDFs. The stated result is strong conditional on the recorded provenance. Manuscript pp. 3, 6; appendix pp. 6–8, Tables A6–A7. |
| F. 358H realized-cost | **SUPPORTED WITH CAVEAT** | Direct-ID-qualified 0.734× CPU and 0.352× NPU prompt-GM speedups, round progress, and arithmetic timed regions substantiate the tested interface cost. Replay/reconstruction and proposal share a call, so their separate costs and a state-persistence speedup are not measured. Manuscript pp. 5, 7–8, Fig. 4; appendix p. 1, §D. |
| G. M4 runtime | **WELL SUPPORTED** | 180/180 direct-ID pairs per speculative condition, target/Guard 1.3114×, target/Always-Spec 1.3469×, and post-study paired Guard/Always-Spec latency 1.0271 [1.0130, 1.0436] are reported with their different statuses. The freeze-hash metadata recovery is disclosed. Manuscript pp. 8–9, §7, Table 3; appendix p. 5, §H. |

## 9. Audit of the 72/72 claim

| Question | Answer | Explanation |
|---|---|---|
| Visible in the PDFs? | **YES** | Main abstract/intro and §5.2 give the headline; appendix Tables A6–A7 enumerate all 24 prompts, each at 3/3, and identify four informative divergences. The underlying arrays are not printed. Manuscript pp. 1, 6; appendix pp. 7–8. |
| Complete generated-token-ID sequences? | **YES** | The stated endpoint compares lengths and every committed generated ID through 128 or an earlier inclusive EOG, excluding prompts and uncommitted proposals. All displayed reserved live lengths are 128. Appendix pp. 6–8, §§I–J, Tables A6–A7. |
| Frozen before live outcomes? | **PARTIAL** | The PDF records a finalized prediction-file digest at T0+1722.38 s and first live outcome at T0+1813.75 s, a 91.37 s lead. The digest alone does not timestamp itself; the order relies on the reported chronology, whose original records are outside the two PDFs. Appendix p. 7, §J. |
| Separate reserved discovery? | **YES** | Twelve exposed discovery prompts (36 repetitions) select H1; 31 tasks with recorded B570 associations are excluded from 164; 24 reserved IDs are selected from 133 eligible by fixed hash ranking. “No known exposure” is audit-scoped. Manuscript pp. 3, 6; appendix p. 6, §J. |
| Falsifiable? | **YES** | Exact 72/72 complete-array equality was the all-or-nothing primary criterion; any one unequal sequence would fail it. The four divergent prompts and first positions make more discriminating checks visible. Appendix pp. 6–8, §J, Tables A6–A7. |
| Avoids unique-cause leap? | **YES** | The text repeatedly limits inference to target-partition sufficiency on the tested stack and disclaims a unique operation, kernel, universal UB1 rule, or shared RTX cause. Manuscript pp. 1, 6, 10; appendix p. 6, §J. |

## 10. Historical versus fresh evidence

**MOSTLY CLEAR.** The H/Q/P definitions on manuscript p. 2, the explicit Table 2 endpoint labels on p. 5, Figure 3's split panels on p. 6, and appendix Tables A4–A6 distinguish historical re-tokenized CLI text, fresh direct-ID qualification, and frozen predictor/live comparison. The abstract and first-page introduction also say fresh qualification does not certify historical timing (p. 1). Some cognitive burden remains because identical-looking 90/90 counts and speedup figures from distinct sessions appear close together. In particular, readers must not combine fresh RTX 90/90 strict-ID qualification with the historical serialized 0.404×/0.650× timings as if they were one trial. M4 historical 1.387× is also text-path, whereas the later 1.3114× guard study has direct-ID evidence and a different held-out population/estimator. (Manuscript pp. 1–2, 4–6, 8–9; appendix pp. 1, 5–6.)

## 11. Population and exclusions

**SIGNIFICANCE CONCERN.** The central predictor population is 24 reserved HumanEval tasks from 133 tasks remaining after 31 of 164 are excluded for any recorded B570 association; it comprises three repeat-stable greedy runs per prompt at a 128-token cap on a particular Vulkan/B570, Qwen3-8B/0.6B Q8_0, k=2, context-1024 setting. Discovery uses 12 already exposed prompts and selects H1 at 36/36. This is a defensible held-out test *within that recorded inventory*, but the repetitions are not 72 independent prompts, no broader prompt/model/runtime distribution is sampled, and no-known-exposure is not proof of never run. The fresh 30-task HumanEval gate, separate 358H 30-prompt comparison, historical M4 24/30 samples, and M4 60-prompt held-out runtime study do not enlarge the B570 predictor's target population. The paper mostly states these boundaries accurately. (Manuscript pp. 3, 6, 9–10; appendix pp. 6–8.)

## 12. First-page test

Using only the title, abstract, and first introduction page, the three-minute impression is a carefully measured consumer-systems paper centered on correctness qualification, one successful frozen trajectory predictor, and negative integrated-cost cases. The **72/72** and its 24-prompt population appear in both abstract and introduction, alongside reference-divergent trajectories and the explicit non-unique-cause limit. The three contributions are spelled out near the end of p. 1. The title and platform-by-platform numbers create a **moderate generic-benchmark confusion risk**: a skim could expect transferable consumer-hardware comparisons, while p. 1 correctly says the systems are separate cases and not a matched ranking. Novelty is present early, but “predictive target-partition sufficiency” needs more interpretive emphasis relative to the routine qualification and descriptive cost claims. (Manuscript p. 1 only.)

## 13. Figures and tables

Here “necessary” means useful to the paper's main evidentiary argument, not every detail required in the main body.

| Item | Necessary? | Readable and informative? | Redundancy or misleading risk |
|---|---|---|---|
| Table 1, systems (main p. 3) | Yes | Compact map of backend, draft placement, evidence scope. | Could imply matched platforms if caption caveat is skipped; caption states otherwise. |
| Figure 1, M4 regimes (main p. 4) | Supporting | Clear opposite campaign GMs and intervals. | Two sessions differ, so visual distance must not be read as a causal workload effect; caption makes this explicit. |
| Table 2, headline outcomes (main p. 5) | Yes | Endpoint and class columns are essential to interpret mixed evidence. | Dense mixed-endpoint table; the B570 timing precision can visually look like a qualified result despite “Diag.” |
| Figure 2, evaluation sequence (main p. 5) | Optional | Easy to read, expresses decision order. | Mostly restates prose and may suggest a causal chain across studies, which caption disclaims. |
| Figure 3, proxy versus gate (main p. 6) | Yes | Split panels clearly separate historical proxy and fresh direct-ID counts. | Proximity may invite a cost–qualification tradeoff inference; explicit caption says these are not matched cells. |
| Figure 4, 358H components (main p. 7) | Yes for cost case | Contrasts isolated draft rates with integrated arithmetic totals and timed regions. | Percent bar alone cannot separate replay from proposal; different arithmetic and prompt-GM estimators are disclosed in caption. |
| Table 3, M4 guard (main p. 9) | Supporting | Direct comparison to fixed speculation is important and readable. | Oracle is a hindsight comparator; labels and prose avoid calling it an achievable policy. |
| Tables A1–A2, estimators/energy (appendix p. 2) | Supporting | Useful for nonuniform estimators and measurement boundaries. | Detailed conventions can obscure the main result, but appendix placement is appropriate. |
| Table A3, target-forward cells (appendix p. 3) | Supporting | Supplies the 11 points behind Fig. 3A. | Context ranges are not uncertainty intervals or matched hardware tests; caption warns. |
| Table A4, evidence inventory (appendix p. 4) | Optional | Useful compact endpoint/status summary. | Repeats Table 2 and prose, but the row-level comparator labels help. |
| Table A5, direct-ID gate (appendix p. 6) | Yes | The four counts and exact gate are the cleanest qualification lookup. | No fresh latency endpoint, plainly labeled. |
| Table A6, reference versus predictor (appendix p. 7) | Yes | The 60/72 versus 72/72 contrast is the mechanism result's strongest display. | In the appendix rather than main p. 6, where the central novelty would benefit from a compact display. |
| Table A7, 24-task ledger (appendix p. 8) | Yes | Readable at PDF zoom; shows all four informative divergences and all prompt-level counts. | Truncated per-task digests and counts do not themselves expose full arrays; caption specifies what is displayed. |

## 14. Related Work, using only the PDFs

The paper fairly credits existing consumer-hardware gains/slowdowns and output-agreement testing (Chordiya), verification/batch bottlenecks (Liu et al. 2026b), round-cost accounting/control (Kim), heterogeneous GPU/CPU and CPU/NPU placement (Dovetail, DuoDecoding, Mirror-SD, Ruiz y Mesa, Lever), numerical batch-shape dependence and deterministic inference (Yuan, Gond, Zhang), and adaptive speculation (TurboSpec, BanditSpec, HeteroSpec). Its explicit “not new” statements for accounting, numerical path dependence, and adaptive control are appropriate. (Manuscript pp. 1–2, 9, §8.) The narrower differentiator is prospective full-sequence prediction of *a blocked path's exact trajectory* using a target-only partition change, with a distinct reserved set. The PDFs do not establish that no earlier study has made an equivalent held-out trajectory prediction; absent outside literature lookup, that novelty claim remains a scoped assessment, not an exhaustive prior-art verdict. The 358H and M4 sections should continue to avoid implying original heterogeneous execution or an improved adaptive policy. Unsafe formulations would be “first to show batch-shape-dependent output mismatch,” “identified the numerical root cause,” or “general solution for consumer speculative decoding”; the manuscript generally avoids them. (Manuscript pp. 6–10.)

## 15. Strongest objection

If I were arguing against acceptance, I would say... the paper's evaluation discipline is sound but its novelty is concentrated in a single fixed-stack, fixed-workload predictive replication of an already plausible batch-shape effect. Most of the 72/72 cases are also reference-equal (60/72), only four prompt trajectories test the divergent prediction, and no second backend or reserved alternative mechanism distinguishes the target partition from related path changes. The qualification counts and 358H component breakdown are valuable engineering characterization, while the M4 policy fails to improve on fixed speculation. The PDF does not expose the full committed arrays or independently inspectable timing of their freeze. Together these make the broad framing larger than the demonstrated transferable insight. (Manuscript pp. 6–10; appendix pp. 6–8.)

## 16. Strongest case for acceptance

If I were arguing for acceptance, I would say... the work directly addresses a serious systems evaluation failure mode: local speed opportunities and conventional algorithmic correctness do not certify the actual generated sequence or integrated benefit on a specific runtime. The prospective B570 protocol turns an easy after-the-fact story into an exact, all-or-nothing reserved prediction that succeeds on all 72 complete sequences, crucially including 12 reference-divergent runs. The manuscript is unusually disciplined about blocked paths, distinct evidence classes, uncertainty boundaries, stopped interventions, and a negative adaptive-control result. That combination yields a useful reproducible evaluation pattern even though it is not a universal mechanism or optimization. (Manuscript pp. 1–2, 5–10; appendix pp. 5–8.)

## 17. Requested changes

**MUST FIX**

1. In manuscript §5.2/p. 6 and appendix §J/pp. 7–8, make the central evidentiary distinction prominent: **60/72 reference-equal cases versus 12/12 reference-divergent predictor successes across four prompts**. Move a compact A6-style comparison into the main paper beside the 72/72 claim. Describe the 24 prompts, rather than 72 repetitions, as the independent held-out task count.
2. Supply an anonymized, reviewer-accessible record of all 72 complete committed prediction arrays, corresponding live arrays, full hashes, and independently inspectable freeze/live event ordering, or state explicitly that reviewers can verify only the summarized PDF ledger. The current appendix digest/chronology is helpful but does not make the central comparison independently auditable from these PDFs. This requests evidence access, not a changed result. (Appendix pp. 7–8.)

**SHOULD FIX**

3. In abstract and the contribution paragraph on manuscript p. 1, lead with the bounded predictive experiment. Describe RTX/B570 qualification and 358H accounting as supporting case evidence; explicitly say no cross-backend predictor transfer is shown. This would align title-level breadth with the strongest scientific claim.
4. In §5.2/p. 6, explain why UB1 is a nontrivial predictive hypothesis rather than merely a retrospective, obvious batch-shape repair. The H1/H2 tree and prospectively frozen holdout are key; clarify what H2 would have discriminated had H1 failed, while avoiding an unrun-H2 comparison claim. (Appendix p. 6, §J.)
5. In §7/p. 9 and conclusion/p. 10, keep the guard as a negative control result rather than an independent optimization contribution; put the paired Guard/Always-Spec 1.0271 interval next to the 1.3114× target comparison whenever the latter is summarized.

**OPTIONAL**

6. Run the exact prediction protocol on a second backend/model or a second controlled target partition. This would materially strengthen generality but is a new study, not a repair to the current within-stack sufficiency claim.
7. Remove or shrink Figure 2 if page space is needed for the A6-style central comparison. (Manuscript pp. 5–6.)

## 18. Recommendation

**WEAK REJECT**

## 19. Confidence

**4/5.** The central counts, comparison endpoints, and stated limitations are explicit in the two PDFs. I cannot independently inspect underlying arrays or audit the literature beyond what the PDFs say.

## 20. Decision rationale

The paper has unusually careful evidence handling and a credible, falsifiable within-stack result: 72/72 frozen complete B570 predictions, with 12/12 successes where the reference actually diverges. That deserves serious credit. My weak-reject judgment rests on significance and novelty rather than a demonstrated error in the reported experiment. The predictor covers one partition change on one model/backend/workload configuration; a known batch-shape concern makes UB1 an intuitive candidate after discovery, and no transfer or reserved competing mechanism test establishes a broader principle. RTX qualification and the 358H measured interface costs are useful, but mostly characterize particular executions; M4 control has no incremental advantage over fixed speculation. The prose is substantially honest about these limits, and the first page exposes the predictor early. For the central evidence, however, the PDFs offer a ledger and recorded chronology instead of the complete arrays and independently inspectable freeze record. Better access and a tighter predictive-mechanism framing could move this close decision; a second controlled transfer would change its significance most. (Manuscript pp. 1, 6–10; appendix pp. 6–8.)

## Special Questions

| Question | Answer | Rationale |
|---|---|---|
| Q1. Best characterization | **C — predictive mechanism** | The frozen B570 complete-trajectory prediction is distinctive. B (qualification) and D (realized costs) frame it; they are not by themselves equally novel. Manuscript pp. 1, 6–9. |
| Q2. More than “benchmark your own system”? | **SOMEWHAT** | The held-out falsifiable B570 prediction exceeds descriptive benchmarking, but transfer and causal isolation are narrow. Manuscript p. 6; appendix pp. 6–8. |
| Q3. Frozen 72/72 publication importance? | **YES** | Particularly because four reference-divergent prompts yield 12/12 informative complete-sequence predictions; freezing changes the inference from retrospective fit to a bounded predictive test. Manuscript p. 6; appendix pp. 6–8. |
| Q4. Would second-backend transfer change recommendation? | **YES** | A comparably frozen, informative second backend prediction would address the chief significance concern and could merit acceptance if sound. Manuscript p. 10 states transfer is unestablished. |
| Q5. Does no transfer invalidate current claims? | **NO** | The tested-path sufficiency and exact qualification outcomes are expressly local. Manuscript pp. 6, 10. |
| Q6. 358H role | **Useful supporting** | Integrated cost is concretely measured, though replay and proposal are inseparable and the intervention stops at qualification. Manuscript pp. 7–8; appendix p. 1. |
| Q7. M4 role | **Useful supporting** | The direct-ID held-out negative control guards against claiming a general runtime-policy win, though its detail competes with the central B570 narrative. Manuscript pp. 8–9. |
| Q8. Exact overstated claim examples | **NONE FOUND** | The most tempting leaps—unique numerical cause, universal UB1 rule, retrospective strict-ID timing certification, state-persistence benefit, or M4 incremental guard win—are explicitly disclaimed. A broad title can still invite overreading. Manuscript pp. 1, 5–10. |
