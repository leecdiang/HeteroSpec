Artifact-only review.
Sources consulted:
  - manuscript-v0.8.2.pdf
  - appendix-v0.8.2.pdf

No README, handover, source files, repository evidence, prior reviews,
Git history, PR descriptions, experiment logs, or web searches were used.

## 1. Paper summary

The paper examines whether speculative decoding on four consumer systems both preserves a specified output sequence and produces a realized post-prefill speedup. It separates favorable component observations, such as draft throughput and target-forward batching, from complete runtime cost and generated-token-ID qualification. Historical campaigns report opposite M4 outcomes on separately run representative and HumanEval workloads, RTX slowdowns on serialized controls, a correctness-blocked B570 path, and exact but slower CPU and NPU drafting on a 358H. The historical M4/RTX/B570 equality comparator reconstructs token arrays from CLI text, a weaker standard than direct generated IDs. Two newer, independently frozen HumanEval30 studies apply the latter standard: RTX serialization changes agreement from 75/90 to 90/90, whereas B570 serialization changes it from 60/90 to only 78/90. A B570 follow-up selects target-only greedy micro-batch one using exposed discovery prompts, freezes a complete-sequence predictor before live reserved inference, and matches all 72 serialized speculative sequences on 24 reserved prompts, including twelve divergent pairs. The 358H cost breakdown shows an isolated NPU draft advantage disappearing at a synchronous stateful interface whose replay and proposal time are inseparable. A separate M4 continuation guard is exact and faster than target-only on 60 held-out prompts, but is slower than fixed speculation in a post-study paired comparison. The distinctive research result is the prospective B570 trajectory prediction; the rest chiefly disciplines and bounds systems measurements rather than establishing a new algorithm or portable controller. (Manuscript pp. 1–10; appendix pp. 1–6.)

## 2. Central thesis

Speculative decoding should be evaluated by qualifying the actual output path before crediting a speedup, then accounting for complete realized stateful cost. A target execution partition can suffice to predict a particular correctness failure, even when a live draft is absent from the predictor. This is a configuration-scoped systems result rather than a universal decoding principle. (Manuscript §§2, 5–6, pp. 2, 5–7.)

## 3. Top contributions, ranked

1. **Prospective B570 mechanism prediction:** target-only `nubatch=1` predicts 72/72 complete serialized speculative ID sequences on a reserved set after an explicit discovery/validation freeze, including the remaining mismatches against reference (manuscript §5.2, p. 5; appendix J, p. 6).
2. **Direct-ID execution-path qualification:** separate RTX and B570 studies expose how serialization qualifies one tested path but leaves the other blocked, with a clear boundary from historical text-path timing (manuscript §5.1, p. 5; appendix I, pp. 5–6).
3. **Realized-cost diagnosis on 358H:** exact, unprofitable CPU/NPU paths and timed complete regions show why isolated draft throughput does not translate through this state interface (manuscript §5.3 and Fig. 4, pp. 6, 8; appendix D, p. 1).

## 4. Single strongest contribution

**The frozen B570 prediction** matters because it advances a correctness observation into a falsifiable, complete-output prediction of *which* reference divergences persist and *where*, on reserved prompts. Matching 72/72 sequences, 24/24 prompt classifications, and 12/12 first-divergence indices is more informative than reporting a mismatch rate. It is nontrivial to obtain the serialized trajectory using target-only execution when the nominal speculative path includes a draft; the target-only harness also reproduces 90/90 reference sequences before changing `nubatch` (manuscript pp. 3, 5; appendix J, p. 6). The evidence supports sufficiency of the tested target partition for these outputs, not identification of the unique causal operation. Because the hypothesis was selected on exposed discovery prompts and tested on one backend, model pair, and workload, the contribution is a strong *case-specific* mechanistic prediction, not a general predictive theory of speculative correctness.

## 5. Single strongest empirical result

The frozen B570 target-only micro-batch-one predictor matches **72/72 complete generated-token-ID sequences** from live serialized speculation over 24 reserved HumanEval tasks × three repetitions; it also predicts the twelve residual reference-divergent repetition pairs and their first-divergence indices. The predicted/live reference-equality count is 60/72, so the path remains blocked (manuscript §5.2, p. 5; appendix J, p. 6).

## 6. Strengths

1. The 72/72 endpoint is prospective after discovery, uses whole output sequences, and includes divergent cases rather than selecting only correct cases (manuscript pp. 3, 5; appendix p. 6).
2. The paper candidly distinguishes historical text-derived equality from fresh direct-ID comparisons and does not transfer the latter qualification to older timings (manuscript §§2.1, 4, 5.1, pp. 2, 4–5).
3. Negative and stopped interventions are retained: B570 remains blocked, 358H runtime intervention has no formal performance endpoint, and M4 Guard loses to fixed speculation (manuscript pp. 5, 7, 9).
4. The 358H decomposition counts committed output, correction/bonus work, and synchronous replay-plus-proposal within the measured boundary; it avoids inferring a replay-only cost (manuscript pp. 2, 6, 8; appendix D, p. 1).
5. Related Work acknowledges close consumer-hardware, cost-accounting, numerical, heterogeneous-placement, and adaptive-control antecedents (manuscript §8, pp. 9–10).

## 7. Weaknesses

1. **MAJOR — significance:** The strongest mechanism result has one target backend, one model pair, greedy `k=2`, one family of code prompts, and 24 reserved tasks. A second backend or materially different partition would determine whether it is a transferable insight rather than an unusually thorough case study (manuscript §9, p. 10).
2. **MODERATE — missing comparison:** There is no reserved-set comparison with a simpler competing predictor, such as reference-only/default target execution, or another precommitted target shape. The 60/72 reference equality and 72/72 predictor equality imply an advantage for this set, but an explicit comparator would clarify what the partition hypothesis adds beyond an obvious same-path replay (manuscript §5.2, p. 5; appendix J, p. 6).
3. **MODERATE — scope:** Historical multi-system timing and prospective correctness use different comparator classes and sessions. The figure juxtaposing historic target-forward proxy cells with new direct-ID gates is informative but cannot jointly establish cost versus correctness of one intervention (manuscript Fig. 3, p. 7; §9, p. 10).
4. **MODERATE — significance:** Complete-cost accounting is acknowledged prior art; the M4 Guard is slower than Always-Spec, and the 358H persistence/UB2 intervention never yields qualified performance data. These components strengthen the evaluation narrative but are limited standalone research advances (manuscript §§2.3, 7–8, pp. 2, 7–10).
5. **MINOR — clarity:** “Target-partition isolation” can sound like unique causal identification. Target-only `nubatch=1` is a sufficient predictive control under the tested stack; the operation or numerical cause remains unknown (manuscript §§5.2, 9, pp. 5, 10; appendix J, p. 6).

## 8. Claim–evidence audit

| Claim | Judgment | Basis and limit |
|---|---|---|
| A. Execution-path qualification | **SUPPORTED WITH CAVEAT** | The strict direct-ID contract, explicit gates, and blocked-path reporting are clear. Historical “qualified” timing uses reconstructed CLI-text token arrays and is not strict-ID certification (manuscript §§2.1–2.2, pp. 2, 4; appendix B, p. 1). |
| B. RTX direct-ID | **WELL SUPPORTED** | A separate frozen HumanEval30 protocol reports 75/90 batched and 90/90 serialized complete direct-ID pairs; serialization qualifies this tested endpoint. It is not a matched-cost experiment or retroactive qualification of older RTX timing (manuscript §5.1, p. 5; appendix I/Table A5, pp. 5–6). |
| C. B570 direct-ID | **WELL SUPPORTED** | Fresh fast 60/90 and serialized 78/90 complete-ID pairs both miss the frozen 90/90 gate. Reference/context/front-end differ from RTX and historical B570 (manuscript §5.1, p. 5; appendix I/Table A5, pp. 5–6). |
| D. B570 target-partition mechanism | **SUPPORTED WITH CAVEAT** | Target-only `nubatch=1` reproduces exposed discovery and reserved serialized trajectories; the changed target partition is sufficient on this stack. The study does not uniquely locate a kernel or prove a general numerical root cause (manuscript §5.2, p. 5; §9, p. 10; appendix J, p. 6). |
| E. 72/72 held-out prediction | **WELL SUPPORTED** | The PDFs specify exposure audit, deterministic reservation, frozen H1/tree and complete sequence/digest commitment before live outcomes, plus 72/72 success and divergence detail. Artifact-only review cannot independently inspect the claimed archive or its timestamps (manuscript §3.1, p. 3; §5.2, p. 5; appendix J, p. 6). |
| F. 358H realized-cost | **SUPPORTED WITH CAVEAT** | Exact 90/90 paths and measured component shares show 87.34% target-side CPU time and 58.35% synchronous NPU replay-plus-proposal time. Replay alone and a persistence benefit are unmeasured; source identity has a stated reconstruction limit (manuscript §§5.3, 7.1, pp. 6–8; appendix D/E, pp. 1–2). |
| G. M4 runtime | **WELL SUPPORTED** | On 60 held-out prompts, Guard is 180/180 ID-exact and 1.3114× versus target-only, while fixed is 1.3469×; secondary paired Guard/Always-Spec latency is 1.0271 [1.0130, 1.0436]. The paper explicitly denies incremental Guard benefit (manuscript §§7.2–7.3/Table 3, pp. 7–9; appendix H, p. 5). |

## 9. Audit of the 72/72 result

| Question | Answer | Assessment |
|---|---|---|
| Is the result visible? | **YES** | Abstract and intro p. 1; full result §5.2 p. 5; appendix J p. 6. |
| Are predictions complete generated-token-ID sequences? | **YES** | All 72 arrays/digest were committed; endpoint is first 128 committed IDs or inclusive earlier EOG; task IDs/uncommitted proposals excluded (appendix I–J, pp. 5–6). |
| Frozen before live outcomes? | **YES** | H1, reserved IDs, criterion, predictor, binaries, and complete predictions are described as committed before the first live serialized outcome (manuscript p. 3; appendix J, p. 6). This is a PDF claim, not independent timestamp verification. |
| Reserved separately from discovery? | **PARTIAL** | Thirty-one of 164 tasks with recorded B570 association were excluded, with 24 selected by a deterministic hash; exposed discovery uses twelve other tasks. “No known exposure” is limited to the audited retained records, not proof against unavailable history (manuscript p. 3; appendix J, p. 6). |
| Falsifiable? | **YES** | Any one complete sequence mismatch would fail the frozen 72/72 endpoint, including residual reference-divergent cases (manuscript p. 5; appendix J, p. 6). |
| Sufficiency versus unique causality? | **PARTIAL** | Sufficiency for the tested serialized trajectory is evidenced. Unique kernel, operation, architecture-wide mechanism, and cross-backend causality are expressly not established (manuscript pp. 5, 10; appendix J, p. 6). |

## 10. Separation of evidence generations

**MOSTLY CLEAR.** Sections 2.1 and 4 and Table 2 explicitly mark historical M4/RTX/B570 comparisons as re-tokenized text, §5.1 and Fig. 3B mark fresh direct-ID qualification as separate, and §7/Table 3 mark prospective M4 runtime validation as a third study (manuscript pp. 2, 4–5, 7–9). The first-page abstract and introduction already distinguish fresh qualification from old timing, but the main title and an early “four consumer systems” framing may still encourage a quick reader to infer a single uniformly exact cross-platform benchmark. Appendix B/I repeats the distinction (pp. 1, 5–6).

## 11. Actual population and exclusions

The inferential population is measured paths and prompts on Qwen3-8B/0.6B Q8_0 (358H has a symmetric INT4 OpenVINO draft), mostly greedy `k=2` and a 128-token cap, across four distinct hardware/software stacks. Historical M4 uses 24 representative Spec-Bench and 30 separately frozen HumanEval IDs; the prospective RTX/B570 studies share 30 HumanEval tasks but have different runtime, context, and reference settings. The B570 prediction excludes 31 of 164 HumanEval tasks with known B570 associations and selects 24 reserved tasks from the remaining 133; twelve exposed discovery tasks choose the hypothesis. M4 Guard uses 40 calibration, 16 qualification, and 60 held-out prompts split between HumanEval and Spec-Bench, excluding recorded prior M4 exposure. Serving concurrency, other models, functional code correctness, prefill/loading, and whole-request latency are outside scope (manuscript §§3, 7, 9, pp. 3, 8, 10; appendix H–J, pp. 5–6). **SIGNIFICANCE CONCERN:** these restrictions do not invalidate the measured case claims, but sharply bound the generality of the principal novelty claim.

## 12. First-page test

Reading only the title, abstract, and introduction on p. 1, the three-minute impression is a careful consumer-system evaluation with a distinctive frozen target-partition prediction. **Consumer-benchmark confusion:** moderate risk from the broad title and four-system opening, softened by explicit “campaign-specific comparators,” warnings about text-path versus direct-ID timing, and the sentence that hardware cases were independently frozen. **72/72 visibility:** strong—it appears in the abstract, introduction, and contributions list, with “complete generated-token-ID sequences” and reserved timing. **Novelty early:** fairly clear in the contribution list, although direct-ID qualification alone sounds like a methodical measurement upgrade and realized-cost accounting sounds familiar; the precise B570 prediction is the claim that makes this more than an inventory. (Manuscript p. 1.)

## 13. Figures and tables

| Item | Necessity, readability, information, and possible confusion |
|---|---|
| Table 1, platform scope (p. 4) | Necessary for stack and comparator boundaries; compact and readable. Hardware/software co-variation is explicit. |
| Table 2, headline outcomes (p. 4) | Necessary synthesis of profitable, unprofitable, blocked, and secondary results; “Matching pairs” could still be skimmed as uniform exact-ID equality despite a good caption. Consider spelling out “text-derived” in those cells. |
| Figure 1, M4 contrast (p. 5) | Readable, useful visual demonstration of opposite observed outcomes; mostly redundant with Table 2, but prominently flags different sessions and historical comparator. No causal workload contrast should be inferred. |
| Figure 2, evaluation pipeline (p. 6) | Conceptual guide is useful, but text heavy and partly repeats §§2 and 6. The arrows cannot establish the empirical diagnoses; caption correctly says so. Space could be reallocated to a B570 prediction diagram. |
| Figure 3, opportunity and qualification (p. 7) | Panel B is necessary and clear, placing all four direct-ID endpoints against the gate. Panel A's proxy ranges come from different historical studies, and side-by-side placement invites an unwarranted same-run cost/qualification interpretation; its caption carefully warns against this. |
| Figure 4, 358H cost (p. 8) | Important, visually readable contrast of isolated throughput and integrated time. Stacked bars express measured shares, but the blue NPU segment combines replay and proposal and must not be read as replay-only; caption handles this. Arithmetic means and prompt-GM headline speedups are distinct. |
| Table 3, M4 runtime (p. 9) | Necessary for comparing Guard, fixed speculation, and the offline comparator. The post-study paired contrast is separated and labeled. Oracle regret is contextual, not an achievable controller target. |
| Appendix Table A1, estimators (p. 2) | Necessary for reproducibility of heterogeneous intervals, though detailed bootstrap order statistics are more provenance than contribution. |
| Appendix Table A2, energy (p. 2) | Useful boundary guard against cross-platform ranking; readable and concise. |
| Appendix Table A3, proxy cells (p. 3) | Necessary lookup for Fig. 3A; confirms eleven contexts are not uncertainty bars. “Qualified shared path” follows the weaker historical comparator, which a reader must connect to caption. |
| Appendix Table A4, evidence inventory (p. 4) | Helpful but largely repeats Table 2 and Figure 2. Historical “exact” labels remain a possible skimming hazard despite the caption's comparator warning. |
| Appendix Table A5, direct-ID counts (p. 6) | Necessary clean tabulation of the new gates; partly duplicates Fig. 3B but supplies exact-prompt counts and direct-ID comparator. |

## 14. Related Work, as represented in the PDFs

The paper grants appropriate prior credit to speculative decoding itself, prior cost/commit accounting, heterogeneous CPU/GPU/NPU placement, adaptive stopping and verification allocation, state reuse, numerical path dependence, determinism, and a particularly close consumer-Apple study with both gains/slowdowns, batch inefficiency, greedy equality, and batch-shape argmax changes (manuscript §8, pp. 9–10). On the PDF's own descriptions, the **new** aspect is the precommitted complete-output prediction from a target-partition control after direct-ID qualification, not the realization that batching can change argmax, that overhead can erase speedups, or that costs should be measured completely. The distinction from cost models predicting *profitability* is sensible because this predictor concerns *output trajectories*. I cannot establish exhaustive priority without literature lookup and make no claim that the cited descriptions are complete. Any wording suggesting first discovery of numerical path dependence, correctness gating, state reuse, or a new profitability formula would be unsafe; current §8 generally avoids it.

## 15. Single strongest objection

If I were arguing against acceptance, I would say... the only clearly distinctive result is a 72/72 prediction from executing the target under the same micro-batch-one partition as the serialized speculative path, selected after seeing twelve discovery prompts, on one backend and one model/workload. It is a rigorous and useful diagnosis, but could be seen as a carefully validated, partly obvious replay of the relevant execution shape rather than a generalizable systems mechanism. The remaining four-system synthesis uses mixed historical comparators and the runtime intervention shows no advantage over fixed speculation (manuscript §§5.2, 7–9, pp. 5, 7–10; appendix J, p. 6).

## 16. Single strongest acceptance argument

If I were arguing for acceptance, I would say... systems papers should reward falsifiable diagnosis of an output-preservation failure, not only new fast algorithms. Here a frozen target-only partition predicts all 72 complete live serialized trajectories, including the mismatches and their indices, after a conservative exposure audit; direct-ID studies establish the path gates; exact negative 358H and M4 runtime results keep the accounting honest. That combination turns familiar concerns about numerical paths and overhead into an unusually disciplined decision sequence for the tested configurations (manuscript pp. 1, 5–9; appendix pp. 5–6).

## 17. Requested revisions

**MUST FIX**

- In §5.2 or appendix J, add an explicit reserved-set predictor comparison row: default/reference target-only trajectory versus `nubatch=1` trajectory against the live serialized sequences, identifying the 12 divergent pairs. The existing 60/72 and 72/72 counts imply it, but an aligned comparison would isolate the incremental predictive value and prevent “matching the same path” from sounding tautological (manuscript p. 5; appendix p. 6).
- In the abstract, §5.2 heading/body, and conclusion, consistently phrase the finding as *sufficiency of the tested target partition for reproducing the serialized trajectory*, and avoid any reading that a unique numerical cause was isolated (manuscript pp. 1, 5, 10).

**SHOULD FIX**

- Give the B570 result a compact diagram or table showing discovery → frozen H1 → committed complete predictions → live reserved comparison and four divergent examples; this is more central to novelty than the largely conceptual Figure 2 (manuscript pp. 3, 5–6; appendix p. 6).
- On p. 1 and Table 2, put “historical text-derived comparator” immediately beside the legacy timing counts, and distinguish those from fresh strict-ID qualification and prospective M4 runtime in short labels (manuscript pp. 1, 4).
- In §8, sharpen the close-prior-art comparison in one compact paragraph: prior batch-shape greedy changes and cost gating versus this study's frozen complete-sequence target-partition prediction. Avoid implying that direct-ID equality or complete costs are themselves novel (manuscript pp. 9–10).

**OPTIONAL**

- Add a second independently selected backend/partition or non-code workload prediction. This is the strongest path to a larger novelty claim, although the present manuscript can be judged as a bounded case without it (manuscript §9, p. 10).
- Reduce redundant summary inventory in appendix Table A4 and use that space for a precise prediction/control protocol or sequence examples (appendix pp. 4, 6).

## 18. Recommendation

**WEAK ACCEPT**

## 19. Confidence

**4/5.** The PDFs give unusually explicit endpoints and qualifications. Confidence in broader novelty priority is necessarily lower because this review deliberately used no outside literature.

## 20. Decision rationale

The paper's strongest advance is a prospective, complete-token-sequence prediction on a reserved B570 workload. The result is specific, falsifiable, and includes failures against the reference, so it carries more weight than retrospective mismatch characterization. The direct-ID gates and 358H complete-cost breakdown supply practical context, while the authors correctly decline to claim Guard beats fixed speculation or that failed interventions produced speedups. I place less weight on the four-system breadth: legacy timing relies on a weaker text-derived comparator, hardware and software co-vary, and the decisive prediction spans only one target backend, model pair, and code workload. The cost accounting and numerical sensitivity themes have close acknowledged prior art, and the target-only control may look obvious after discovery. Nevertheless, the reserved prediction and careful evidence boundaries constitute a modest but credible systems contribution. A direct baseline predictor comparison and tighter sufficiency wording would make that contribution easier to judge. (Manuscript §§2, 5, 7–9, pp. 2, 5–10; appendix I–J, pp. 5–6.)

## Special questions

| Question | Answer | Reason |
|---|---|---|
| Q1. What is the paper? | **E — coherent B+C+D** | The qualification and predictive B570 mechanism anchor it; the 358H realized-cost case supplies a complementary boundary. The coherence is an evaluation sequence, not a single causal intervention (manuscript §§5–7, pp. 5–9). |
| Q2. More than a benchmark of its own system? | **CLEARLY YES** | The prospective complete-sequence B570 prediction is a falsifiable mechanism test, and the fresh direct-ID gates change what can legitimately be claimed (manuscript §5.2, p. 5; appendix J, p. 6). |
| Q3. Importance of frozen 72/72? | **YES** | Without the reserve and pre-outcome freeze, the most distinctive result would be an outcome-informed replay on one stack (manuscript pp. 3, 5; appendix p. 6). |
| Q4. Would second backend transfer change recommendation? | **YES** | A successful precommitted transfer would address my main significance concern and could move the decision toward ACCEPT; failure would more sharply establish the case-specific boundary. |
| Q5. Does lack of transfer invalidate current claims? | **NO** | Current wording largely scopes the finding to the tested B570 path and does not claim a universal partition rule (manuscript §9, p. 10). |
| Q6. 358H role? | **USEFUL SUPPORTING** | Direct complete-region timing illustrates the second decision boundary, but replay/proposal are inseparable and the proposed intervention stops before performance evaluation (manuscript pp. 6–8). |
| Q7. M4 role? | **USEFUL SUPPORTING** | It tests exact profitable continuation prospectively, but fixed speculation is faster and the policy has no demonstrated incremental value or transfer (manuscript Table 3/§7.3, p. 9). |
| Q8. Exact overstated claims? | **“isolates a sufficient target execution partition”** (abstract, p. 1) and **“mechanism isolation”** (§5.2 heading, p. 5) risk implying causal isolation of the underlying operation. The body/limitations correctly narrow these to trajectory sufficiency. **“the state interface consumes an isolated draft-device advantage”** (conclusion, p. 10) is fair as an integrated-interface observation but should not imply replay-only causality, because replay and proposal share one timer (§5.3/Fig. 4, pp. 6, 8). No major unqualified universal novelty claim was found. |
