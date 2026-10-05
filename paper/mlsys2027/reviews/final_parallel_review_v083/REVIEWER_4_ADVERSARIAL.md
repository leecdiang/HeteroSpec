Artifact-only review.
Sources consulted:
  - manuscript-v0.8.3.pdf
  - appendix-v0.8.3.pdf

No README, handover, source files, repository evidence, prior reviews, Git history, PR descriptions, experiment logs, or web searches were used.

## 1. Paper summary

The paper studies why promising local measurements of speculative decoding do not necessarily yield an output-preserving, faster integrated runtime on consumer systems. It defines a strict generated-token-ID contract, distinguishes historical equality inferred from re-tokenized CLI text from fresh captured-ID comparisons, and reports independently frozen case studies on an M4, RTX 5070 Ti Laptop, Arc B570, and Core Ultra X7 358H. Fresh HumanEval30 qualifications show RTX batched at 75/90 equal pairs and serialized at 90/90, whereas B570 fast and serialized reach 60/90 and 78/90, respectively. A subsequent B570 study selects a target-only micro-batch-one predictor on exposed discovery prompts, freezes its outputs before reserved live runs, and reports 72/72 complete-sequence prediction on 24 reserved prompts. Four of those prompts diverge from the reference; the paper expressly limits the inference to tested-path predictive sufficiency. On 358H, both directly qualified CPU and NPU draft integrations are slower than target-only, despite favorable isolated NPU draft throughput; measured combined replay/proposal or complete target work accounts for much of their time. A later 358H intervention fails qualification before formal performance evaluation. Finally, an M4 Guard policy passes direct-ID checks and beats target-only on held-out prompts, but fixed speculation is faster in a post-study paired comparison. The paper offers a disciplined evaluation sequence and bounded empirical diagnoses, not a new broadly validated accelerator or controller. (Manuscript pp. 1–10; appendix §§B, D, H–J, pp. 1–8.)

## 2. Thesis

An execution path must first meet its output contract, then a blocked path can be diagnosed with frozen trajectory predictions, and only a qualified path's complete realized cost can support a speed claim. The reported consumer-system cases demonstrate each boundary under specific stacks and workloads. (Manuscript §§2, 5–7, pp. 2, 5–9.)

## 3. Top contributions, ranked

1. Prospectively frozen B570 target-partition prediction, with 72/72 complete generated-ID agreement on reserved live runs, including four reference-divergent prompts (manuscript §5.2, p. 6; appendix §J, pp. 6–8).
2. Fresh, explicitly separated direct-ID qualification of RTX and B570 paths, exposing the difference between a qualifying serialized RTX path and still-blocked B570 paths (manuscript §5.1, pp. 5–6; appendix §I, pp. 5–6).
3. Complete-region 358H cost accounting showing the gap between isolated NPU draft throughput and the integrated post-prefill runtime (manuscript §5.3, p. 7; appendix §D, p. 1).

## 4. Strongest contribution

The B570 reserved prediction is the most nontrivial result. A frozen target-only execution with `nubatch=1` reproduces whole live serialized sequences, including the first divergence position and token on four prompts where the ordinary target reference differs. Selection uses 12 exposed discovery prompts, while the 24 reserved prompts are selected after an exposure audit and predictions are recorded before live outcomes. This moves beyond explaining previously observed mismatches after the fact. The appendix provides a content digest, relative event chronology, a 24-prompt ledger, and the four divergent token IDs. It establishes predictive sufficiency for this specific path, although the PDFs alone cannot independently recompute the arrays and the result does not identify a numerical operation or generalize to other backends. (Manuscript §5.2, p. 6; appendix §J, pp. 6–8.)

## 5. Strongest empirical result

The frozen B570 UB1 target-only predictor agrees with **72/72 complete generated-token-ID sequences** in 24 reserved HumanEval prompts × three live repetitions; ordinary reference-to-live equality is **60/72**, with all four reference-divergent prompts predicted correctly in all three repetitions. The first-divergence indices also agree in 12/12 divergent repetition pairs. Every displayed live sequence has length 128. (Manuscript §5.2, p. 6; appendix §J, Tables A6–A7, pp. 7–8.)

## 6. Strengths

1. The paper repeatedly distinguishes historical text-path agreement, fresh direct-ID qualification, and frozen predictor/live agreement; it does not retrofit the fresh gate onto historical latency (manuscript §§2.1, 4–5, pp. 2, 4–6).
2. The B570 prediction is temporally frozen, includes reference-divergent outcomes, and retains a blocked reference gate instead of relabeling prediction as correctness (manuscript §5.2, p. 6; appendix §J, pp. 6–8).
3. The 358H accounting includes all committed tokens and a complete post-prefill timer, while explicitly leaving replay and proposal inseparable (manuscript §§2.3, 5.3, pp. 2, 7; appendix §D, p. 1).
4. Failed qualification stops the 358H intervention's formal speed evaluation; the M4 Guard result is reported against fixed speculation even though Guard loses that comparison (manuscript §7, pp. 8–9).
5. Prompt-level paired estimators, confidence intervals, measurement boundaries, and deviations are described with unusually candid limitations (manuscript §§3.2, 9, pp. 3, 10; appendix §§B, E, H, pp. 1–2, 5–6).

## 7. Weaknesses

1. **MAJOR — significance:** The most novel mechanism evidence rests on one B570 Vulkan configuration and four distinct reference-divergent reserved prompts. The other 20 reserved prompts match the reference as well as the predictor, and three repetitions are stable copies of each prompt's trajectory. The 72/72 denominator is legitimate for the frozen endpoint, but conveys more apparent diversity than 24 distinct trajectories and four genuinely discriminating ones. This limits the paper's contribution beyond established batch-shape numerical sensitivity. (Manuscript §§5.2, 8–9, pp. 6, 9–10; appendix §J, Tables A6–A7, pp. 7–8.)
2. **MODERATE — missing evidence:** The anonymous PDFs give hashes, a chronology, a per-prompt ledger, and examples, but not the 72 prediction arrays or live arrays. They report an independent validator without exposing inputs in these artifacts. Thus the decisive equality and temporal freeze are well documented *as reported*, yet cannot be independently audited from the submitted PDFs alone. This is a verifiability limitation, not evidence that the ledger is wrong. (Appendix §J, pp. 6–8.)
3. **MODERATE — significance:** The integrated runtime work yields no demonstrated improved control: the 358H intervention never qualifies, and on M4 Guard is 1.0271× slower than Always-Spec by paired latency ratio, with its advantage over target-only inherited from a profitable fixed path. The negative outcomes are valuable engineering evidence but leave the central actionable gain as an evaluation discipline rather than a validated new method. (Manuscript §7 and Table 3, pp. 8–9.)
4. **MODERATE — scope:** The four systems are independent campaigns with co-varying runtimes, references, contexts, and sometimes quantization. Fresh direct-ID RTX/B570 tests have no matching latency endpoint; historical positive M4 speedup is only text-path qualified. Consequently the work cannot infer a cross-system tradeoff between exactness and performance or a transferable operating regime. This is a significance limit, not a flaw in the stated path-scoped claims. (Manuscript §§3–5, 9, pp. 3–6, 10; appendix §§I–J, pp. 5–6.)
5. **MINOR — clarity:** The general evaluation sequence in Figure 2 adds little to the text, while the central 72/72 evidence requires navigating Figure 3, §5.2, and multiple appendix pages. A concise main-text summary of 24 distinct prompts, 20 reference-equal and four divergent, would make the main inference easier to calibrate. (Manuscript Figures 2–3, pp. 5–6; appendix §J, pp. 7–8.)

## 8. Claim–evidence audit

| Claim | Judgment | Basis and boundary |
|---|---|---|
| A. Execution-path qualification | **WELL SUPPORTED** | A strict reference-relative complete-ID gate is defined, failed pairs block the workload-global claim, and the fresh studies count all 90 pairs per path. The gate is empirical and workload-specific, not universal correctness. Manuscript §2.1, p. 2; §5.1, p. 5; appendix §I/Table A5, pp. 5–6. |
| B. RTX direct-ID | **WELL SUPPORTED** | 75/90 batched versus 90/90 serialized with repeat-stable outcomes and a frozen gate. No fresh latency or exact replay of historical driver state is claimed. Manuscript §5.1/Figure 3B, pp. 5–6; appendix §I/Table A5, pp. 5–6. |
| C. B570 direct-ID | **WELL SUPPORTED** | 60/90 fast and 78/90 serialized, both blocked. Separately, the reserved study's reference/live 60/72 is not substituted for the earlier study. Manuscript §§5.1–5.2, pp. 5–6; appendix §§I–J/Tables A5–A6, pp. 5–7. |
| D. B570 target-partition mechanism | **SUPPORTED WITH CAVEAT** | UB1 target-only predicts all reserved serialized sequences, including four reference divergences. That shows tested-path trajectory sufficiency; no isolated kernel, unique numerical cause, architecture-wide mechanism, or all-backend transfer is identified. Manuscript §5.2, p. 6; appendix §J, pp. 6–8. |
| E. 72/72 held-out prediction | **SUPPORTED WITH CAVEAT** | The manuscript and appendix report complete arrays, content digest, freeze chronology, all-prompt ledger, and 72/72 equality. The PDFs do not contain the raw arrays for independent recomputation, and the effective number of distinct reference-divergent prompt cases is four. Manuscript §5.2, p. 6; appendix §J/Tables A6–A7, pp. 7–8. |
| F. 358H realized cost | **SUPPORTED WITH CAVEAT** | Direct-ID-qualified 90/90 paths, complete timed regions and committed-token denominator support negative integrated speedups and measured shares. The 58.35% NPU call combines replay/reconstruction and proposal, so replay cost or persistence benefit cannot be isolated. Manuscript §5.3/Figure 4, p. 7; appendix §D, p. 1. |
| G. M4 runtime | **WELL SUPPORTED** | 60 held-out prompts, 180/180 direct-ID pairs per speculative condition; Guard 1.3114× and Always-Spec 1.3469× versus target-only, while paired Guard/Always-Spec latency is 1.0271 [1.0130, 1.0436]. The latter is openly marked post-study secondary; the formal 358H intervention is stopped. Manuscript §7/Table 3, pp. 8–9; appendix §H, pp. 5–6. |

## 9. Audit of 72/72

| Question | Judgment | Explanation |
|---|---|---|
| Visible? | **PARTIAL** | The PDF shows the 24-task ledger, 72/72 count, short per-task output hashes, four divergent IDs, a prediction-file SHA-256, and chronology, but omits the full arrays and full per-task hashes. Appendix §J, pp. 7–8. |
| Complete generated-token-ID sequences? | **YES** | Endpoint is the first 128 committed generated IDs or inclusive earlier EOG; equality requires sequence and length equality. Table A7 shows length 128 for every reserved task. Prompt IDs and uncommitted proposals are excluded by design. Appendix §J, pp. 6–8. |
| Frozen before live outcomes? | **YES, as documented** | H1 semantics and reserved IDs precede reserved inference; 72 arrays complete at T0+1722.38 s, first live outcome at T0+1813.75 s. The digest alone does not prove timing; the chronology supplies that claim. Appendix §J, pp. 6–7. |
| Separate reserved from discovery? | **YES, within audited exposure records** | Twelve explicitly exposed prompts select H1; 31/164 tasks with any recorded B570 association are excluded; 24 of 133 eligible tasks are selected by hash. Unknown exposure outside the audit cannot be ruled out. Manuscript §3.1, p. 3; appendix §J, p. 6. |
| Falsifiable? | **YES** | A single predictor/live token or length mismatch would fail the prespecified 72/72 criterion, and four reference-divergent prompts make success discriminating rather than purely agreement on reference-equal cases. Appendix §J, pp. 6–8. |
| Avoids unique-cause leap? | **YES** | The authors expressly deny an identified operation/kernel, universal UB1 rule, or shared RTX/B570 root cause. Manuscript §§5.2, 9, pp. 6, 10; appendix §J, p. 6. |

## 10. Historical versus fresh evidence

**VERY CLEAR.** Section 2.1 defines H, Q, P and explains re-tokenized CLI text versus captured generated IDs versus predictor/live complete IDs (manuscript p. 2). Table 2 labels historical M4/RTX/B570 rows as text-path and 358H as direct-ID (p. 5); Figure 3 labels fresh qualification and explicitly says it has no matching latency (p. 6). The limitations repeat that fresh results do not certify older timing (p. 10), and appendix Tables A4–A5 and §J preserve the boundaries (pp. 4, 6–7). A quick reader could still associate adjacent plots as if matched, but captions directly forbid that inference.

## 11. Population and exclusions

**SIGNIFICANCE CONCERN.** The population is separately frozen, single-request decode case studies on four named consumer stacks, one Qwen3-8B target family, mostly Qwen3-0.6B draft, bounded prompts and 128-token output, not serving concurrency, other model families, or whole-request latency. Fresh RTX/B570 qualifications each use 30 HumanEval prompts × three repetitions; B570 predictive validation uses 24 reserved HumanEval prompts selected after excluding 31 of 164 tasks with recorded B570 association; M4 Guard uses 60 held-out prompts split evenly between HumanEval and Spec-Bench. Historical M4 studies use different prompts and sessions. M4 runtime selection excludes recorded prior M4 exposures. This is not a validity concern for the authors' path-scoped results, but severely limits the impact of a broadly titled consumer-systems synthesis. (Manuscript §§3.1, 5.1–5.2, 7.3, 9, pp. 3, 5–6, 8, 10; appendix §§H–J, pp. 5–8.)

## 12. First-page test

Using only title, abstract, and the first Introduction page: in three minutes I would expect a careful empirical systems paper about correctness gates, frozen B570 prediction, and cost accounting, rather than a speedup proposal. The title alone could invite generic consumer-hardware benchmark expectations, but the abstract immediately supplies the RTX/B570 direct-ID numbers, the **72/72** held-out complete-ID result, 358H cost caveat, and Guard's loss to fixed speculation. The Introduction names the three contributions and states both the bounded predictor inference and distinct historical timing. Novelty is visible early, though its size is less obvious: this page does not reveal that only four reserved prompts are reference-divergent or that repeated trajectories are stable. (Manuscript p. 1 only.)

## 13. Figures and tables

| Item | Necessary, readable, informative? | Redundancy or risk |
|---|---|---|
| Manuscript Table 1 (p. 3) | Necessary and readable map of systems, backend, draft placement, endpoint scope. | The compact evidence labels rely on §3/§4 to distinguish historical and prospective paths. |
| Figure 1 (p. 4) | Readable and informative comparison of two M4 observed regimes with intervals and parity. | Could imply workload causality unless its explicit separate-session caption is read; the caption handles this. |
| Table 2 (p. 5) | Necessary, legible headline inventory with endpoint and class columns. | B570's precise diagnostic speedup shares a table with primary speedups; labels prevent a false qualified claim but visual prominence remains high. |
| Figure 2 (p. 5) | Readable but mostly redundant with §2 and §6; not essential empirical evidence. | A simple evaluation sequence could appear causal across studies, although its caption denies that. |
| Figure 3 (p. 6) | Necessary to separate historical proxy and fresh ID counts; labels and 90/90 line are legible. | Panels juxtapose unmatched runs, but title and captions state no matching latency and no causal cost/qualification tradeoff. |
| Figure 4 (p. 7) | Necessary, readable dual view of isolated throughput and integrated timing; bars expose the large NPU call. | The 58.35% region is replay **plus** proposal, and the plot/caption correctly say it is inseparable; avoid visually interpreting all blue time as replay. |
| Table 3 (p. 9) | Necessary and readable for Guard versus fixed speculation; clear direction and post-study status. | The offline oracle label can suggest an attainable policy, corrected by the caption and text. |
| Appendix Table A1 (p. 2) | Informative and compact estimator/CI reproducibility detail. | Not needed in main text. |
| Appendix Table A2 (p. 2) | Informative boundary map for energy claims. | No problematic implication of whole-system energy. |
| Appendix Table A3 (p. 3) | Useful exact numeric lookup for Figure 3A; readable. | Eleven context cells across unmatched contexts do not constitute a trend or common comparison, as caption says. |
| Appendix Table A4 (p. 4) | Useful evidence-class inventory, readable. | Partly repeats Tables 1–2, but emphasizes admissibility. |
| Appendix Table A5 (p. 6) | Necessary exact fresh qualification counts and prompt counts; readable. | No fresh latency endpoint is explicit. |
| Appendix Table A6 (p. 7) | Necessary succinct contrast of reference 60/72 and predictor 72/72; readable. | Aggregate alone hides that 20/24 prompts are reference-equal, supplied by A7. |
| Appendix Table A7 (p. 8) | Necessary and reasonably readable 24-task audit ledger; most informative table for the novelty claim. | Short hashes, rather than sequences, limit independent content audit; all lengths are 128 and three repeats are stable. |

## 14. Related Work

On the PDFs alone, the credit is unusually fair. The paper expressly acknowledges existing consumer-hardware gains/slowdowns, verification dominance, cost/commit accounting, heterogeneous placement, numerical path dependence, deterministic inference, state reuse, and adaptive control. It locates its difference in fresh direct-ID path qualification separated from historical timing, pre-outcome full-trajectory prediction on B570, and one integrated 358H interface accounting, not in inventing speculative-decoding cost theory or a superior controller. (Manuscript Introduction, p. 1; §2.3, p. 2; §8, p. 9.) I cannot verify the cited papers' substance without reading them, and this review makes no claim of missing external citations. The unsafe novelty framing would be treating batch-shape sensitivity, correctness gates, or heterogeneous cost as new in themselves; the manuscript generally avoids it. The remaining concern is whether the narrower combination is sufficiently significant for the venue.

## 15. Single strongest objection

If I were arguing against acceptance, I would say... the paper's most distinctive positive claim is a rigorously frozen but very narrow prediction of four distinct reference-divergent B570 prompt trajectories within one model/backend setting; 20 other reserved prompts are reference-equal and the repetitions are stable. The broad consumer-systems synthesis cannot establish transferable mechanism or a new runtime advantage: RTX/B570 direct-ID tests lack paired latency, 358H's new intervention is blocked, and M4 Guard loses to fixed speculation. The work is careful and useful, but the scientific advance beyond known execution-shape sensitivity and prudent measurement practice is too small for acceptance. (Manuscript §§5–9, pp. 5–10; appendix §J/Table A7, p. 8.)

## 16. Single strongest argument for acceptance

If I were arguing for acceptance, I would say... the paper makes a genuinely prospective, falsifiable full-sequence prediction on a correctness-blocked execution path, gets all 72 live comparisons including the 12 divergent repetitions right, and carefully refuses to identify an unmeasured kernel or claim that a profitable historical path is directly qualified. This rare discipline, combined with complete 358H accounting and frank negative interventions, makes a reusable systems methodology even without a new speedup. (Manuscript §§2, 5–7, pp. 2, 5–9; appendix §J, pp. 6–8.)

## 17. Requested changes

**MUST FIX (for an acceptance case):** In §5.2 immediately after the 72/72 sentence and in the abstract's B570 sentence, state that this is 24 distinct prompts, of which 20 are reference-equal and four reference-divergent, with three repeat-stable trajectories each. Keep 72/72 as the prespecified endpoint, but foreground the smaller discriminating set. In §9, explicitly say that this evidence demonstrates prediction on the tested path rather than a general numerical mechanism. This is a localized presentation repair, not a demand for a new backend experiment. (Manuscript pp. 1, 6, 10; appendix Table A7, p. 8.)

**SHOULD FIX:** Put a small summary of the four divergent task IDs, first-divergence positions, and predicted/live IDs beside §5.2 or Figure 3; the appendix already has the data. Add one sentence in the conclusion distinguishing a measured *combined* replay-plus-proposal call from an isolated replay overhead. (Manuscript pp. 6–7, 10; appendix §J, p. 7.)

**OPTIONAL:** Compress Figure 2 and use the space for the B570 ledger summary; make Table 2's diagnostic B570 row visually distinct; explicitly use “24 prompt trajectories, three repetitions each” wherever the novelty of 72/72 is argued. (Manuscript pp. 5–6.)

## 18. Recommendation

**WEAK REJECT.**

## 19. Confidence

**4/5.** The paper and appendix provide enough methodological detail and internal limits for a confident scope/significance judgment. I cannot independently validate hidden arrays, logs, or prior-work claims from the two PDFs alone.

## 20. Decision rationale

The submission is rigorous in ways that matter: it fixes the strict output endpoint, preserves historical versus direct-ID distinctions, reports failed gates without performance laundering, and freezes its B570 prediction before reserved live outcomes. The 72/72 result is real evidence as presented, especially on the four reference-divergent prompts. My weak reject rests on significance, not an alleged invalid result. Those four distinct divergent trajectories arise on one tightly specified B570 path; repeating each three times does not make the predictive phenomenon broad. The additional direct-ID qualifications have no paired fresh performance measurement, the 358H intervention fails qualification, and M4 Guard offers no advantage over fixed speculation. Existing work is credited for numerical path sensitivity, cost accounting, and adaptive control, leaving a carefully demonstrated but narrow synthesis. Clarity is generally strong and the appendix makes the freeze legible, though the abstract's 72/72 number should be calibrated by its four discriminating prompts. A different venue emphasizing meticulous negative systems case studies might weigh the contribution more favorably. (Manuscript §§5–9, pp. 5–10; appendix §§H–J, pp. 5–8.)

## Special questions

| Question | Answer | Reason |
|---|---|---|
| Q1. Best characterization | **E — coherent B+C+D** | The coherent claim joins execution-path qualification, frozen predictive mechanism, and heterogeneous realized cost. It is not primarily a hardware ranking. Manuscript pp. 1–2, 5–7. |
| Q2. More than “benchmark your own system”? | **CLEARLY YES** | The reserved complete-ID predictor and its pre-outcome freeze are a falsifiable mechanism test, and the cost accounting respects complete round boundaries. Appendix §J, pp. 6–8; manuscript §5.3, p. 7. |
| Q3. Frozen 72/72 publication importance | **YES** | It is the clearest new evidence beyond descriptive performance, with four nontrivial divergence cases. Its scope should be made prominent. Manuscript §5.2, p. 6; appendix §J, pp. 7–8. |
| Q4. Would second-backend transfer change recommendation? | **YES** | A comparably frozen, reference-divergent trajectory prediction on an independent backend would materially address my principal significance concern; result quality and comparable protocol would still matter. Manuscript §9, p. 10. |
| Q5. Does no transfer invalidate current claims? | **NO** | Claims explicitly concern tested paths and do not assert universal transfer. Manuscript §§5.2, 9, pp. 6, 10. |
| Q6. 358H | **Useful supporting** | It concretely demonstrates why isolated draft throughput is insufficient, but replay/proposal is combined and the later intervention is blocked. Manuscript §§5.3, 7.1, pp. 7–8. |
| Q7. M4 | **Useful supporting** | It tests a directly qualified policy and candidly reports no gain over fixed speculation; it is not a positive control contribution. Manuscript §7, pp. 8–9. |
| Q8. Exact overstated claims | **NONE FOUND** | Phrases such as “target-partition sufficiency” are repeatedly bounded to tested trajectories, and the combined 358H call is disclosed. My concerns are evidentiary breadth and impact, not a clearly false or materially overstated sentence. Manuscript §§5.2–5.3, 9, pp. 6–7, 10. |
