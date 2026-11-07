Artifact-only review.
Sources consulted:
  - manuscript-v0.8.2.pdf
  - appendix-v0.8.2.pdf

No README, handover, source files, repository evidence, prior reviews,
Git history, PR descriptions, experiment logs, or web searches were used.

## 1. Paper summary

This paper studies speculative decoding as an execution-path decision with two distinct gates: whether the chosen implementation reproduces a matched greedy target's generated token IDs, and whether a qualified path is faster after all stateful work is charged. It assembles separately frozen campaigns on an M4, RTX 5070 Ti Laptop, Arc B570, and Core Ultra X7 358H with an Arc B390, principally using a Qwen3-8B target and Qwen3-0.6B draft. Historical M4 studies show opposite post-prefill profitability regimes, but their equality evidence comes from parsed, re-tokenized text and their sessions differ. Fresh direct-ID HumanEval30 qualification studies find RTX batching at 75/90 pairs and serialization at 90/90, whereas B570 improves from 60/90 to 78/90 and remains blocked. For B570, a target-only micro-batch-one hypothesis selected on exposed discovery tasks is frozen before reserved inference and predicts 72/72 complete serialized sequences on 24 reserved tasks, including 12 divergent repetition pairs. This is evidence that the tested target execution partition suffices to reproduce trajectories, without identifying a unique kernel or universal cause. On 358H, the isolated NPU draft advantage vanishes in a full-prefix replay-plus-proposal interface, and a later optimization candidate fails qualification before timing. A prospective M4 Guard is exact and beats target-only on 60 held-out prompts, but fixed speculation is faster in a post-study paired comparison. The contribution is disciplined, configuration-scoped diagnosis and a practical qualification-before-cost workflow, rather than a generally faster new decoder (manuscript pp. 1–9; appendix pp. 1, 5–6).

## 2. Central thesis

Local draft or target-forward opportunity cannot establish a useful speculative path: generated-output qualification and complete realized cost must be measured at the actual execution boundary. On one B570 stack, target execution partition alone is a sufficient predictor of serialized output, while a separate 358H case shows that stateful integration can consume an isolated device advantage (manuscript §§2, 5–6).

## 3. Top contributions, ranked

1. **Frozen B570 predictive mechanism test:** target-only micro-batch one predicts 72/72 complete reserved serialized sequences, including residual failures relative to the reference (manuscript §5.2, p. 5; appendix §J, p. 6).
2. **Fresh direct-ID path qualification:** two distinct prospective studies turn a historical verification concern into explicit RTX and B570 pass/fail endpoints (manuscript §5.1, p. 5; appendix §I, pp. 5–6).
3. **Realized-cost diagnosis on 358H:** complete round accounting connects negative integrated speedups to target work or the measured replay-plus-proposal interface; the subsequent candidate is correctly stopped on output qualification (manuscript §§5.3, 7.1, pp. 6–7).

## 4. Single strongest contribution

The B570 prediction is the strongest advance. Its **importance** is to move beyond observing that batch shape correlates with mismatch: a specified target-only partition predicts even the serialized path's *wrong* tokens on unseen tasks, turning numerical path dependence into a testable systems diagnosis. Its **nontriviality** lies in the exposure audit, frozen H1/H2 tree, complete sequence endpoint, and prospective prediction before the live outcomes, not in micro-batch one as a novel algorithm. Its **evidence** is 36/36 exposed discovery matches followed by 72/72 reserved complete-ID matches, 24/24 reference-equality classifications, and 12/12 first-divergence indices; predicted reference equality remains only 60/72 (manuscript §5.2, p. 5; appendix §J, pp. 5–6). The result establishes sufficiency on this stack, not exclusive causality or a kernel diagnosis.

## 5. Single strongest empirical result

On 24 reserved B570 HumanEval prompts with three repetitions each, all **72/72 complete generated-token-ID sequences** predicted by target-only execution with target `nubatch=1` match subsequent live serialized speculative outputs. Four prompts remain reference-divergent and their 12/12 first-divergence indices are also predicted (manuscript §5.2, p. 5; appendix §J, p. 6).

## 6. Strengths

1. The direct-ID contract, text-path distinction, gate failures, and blocked timing are kept visible even where speedups appear attractive (manuscript §§2.1–2.2, 4–5; appendix §§B, I).
2. The B570 validation is outcome-predictive and prospectively frozen, with a reserved set and a failure-sensitive complete-sequence endpoint (manuscript §§3.1, 5.2; appendix §J).
3. Complete 358H accounting uses committed output, correction/bonus work, and measured draft-interface cost rather than substituting acceptance or isolated throughput for end-to-end work (manuscript §§2.3, 5.3; appendix §D).
4. The paper reports negative and stopped interventions faithfully; M4 Guard is not claimed to beat fixed speculation (manuscript §7; Table 3).
5. The figures connect the two gates and component-to-runtime gap to a reproducible engineering workflow, with explicit exclusions of prefill, loading, serving concurrency, and hardware rankings (manuscript Figures 2–4, §§6, 9).

## 7. Weaknesses

1. **MAJOR — significance/scope:** The cleanest mechanism rests on one B570 runtime, one model pair, greedy `k=2`, one task family, and 24 reserved prompts. No second target backend shows whether the predictive partition insight transfers, so its systems generality is uncertain (manuscript §9, p. 10; appendix §J).
2. **MODERATE — missing evidence:** The PDF states freeze chronology, archived validation, and 72/72 sequence equality but does not print the complete predicted and observed arrays or the actual digest values. The independent artifact-only reader can inspect the endpoint and four divergence examples, not independently verify the full prediction or freeze (appendix §J, p. 6; §A, p. 1).
3. **MODERATE — significance:** The new M4 controller does not establish incremental value against fixed speculation: Guard/Always-Spec latency is 1.0271 [1.0130, 1.0436] in a post-study comparison. The 358H optimization is stopped before formal performance. These endpoints strengthen honesty but leave no demonstrated new deployment improvement (manuscript §7, pp. 7–9).
4. **MODERATE — missing comparison:** RTX's fresh qualification and historical serialized latency are separate studies with different host state; the qualified RTX path has no matched fresh performance endpoint. This limits the concrete cost of the strict qualification decision (manuscript §§4.2, 5.1; appendix §I).
5. **MINOR — clarity:** Many overlapping labels—historical “exact,” text-path qualified, direct-ID qualified, primary, secondary, diagnostic—and several campaign-specific estimators demand substantial reader effort despite careful caveats. Appendix Table A4's short “exact” cells are especially easy to quote without its comparator caption (manuscript Tables 1–2; appendix Tables A1, A4–A5).

## 8. Claim–evidence audit

| Claim | Judgment | Evidence and boundary |
|---|---|---|
| A. Execution-path qualification | **SUPPORTED WITH CAVEAT** | Contract and gate are explicit (manuscript §2.1, p. 2); historical M4/RTX/B570 equality is parsed and re-tokenized text, whereas fresh studies and 358H use direct IDs. “Admissible” is only workload- and comparator-conditional, not universal certification (manuscript §§2.1–2.2; appendix §B, p. 1). |
| B. RTX direct-ID | **WELL SUPPORTED** | Prospectively frozen 75/90 batched versus 90/90 serialized, direct complete-ID comparisons, 25/30 and 30/30 exact prompts, no performance inference (manuscript §5.1, p. 5; Figure 3B, p. 7; appendix §I/Table A5, p. 6). |
| C. B570 direct-ID | **WELL SUPPORTED** | Fresh fast 60/90, serialized 78/90, with both below the 90/90 gate; separate from historical 45/90 and 60/90 text-path figures (manuscript §5.1, p. 5; appendix §I/Table A5, pp. 5–6). |
| D. B570 target-partition mechanism | **SUPPORTED WITH CAVEAT** | Target-only UB1 matches 36/36 exposed discovery and predicts 72/72 reserved serialized trajectories, including divergence, which supports sufficient partition reproduction (manuscript §5.2, p. 5; appendix §J, pp. 5–6). It neither isolates a specific operation nor excludes another route to the same tokens. |
| E. 72/72 held-out prediction | **SUPPORTED WITH CAVEAT** | The protocol and aggregate endpoint are exceptionally specific; all predicted complete arrays are reported committed before live runs and 12 first-divergence indices match (manuscript §§3.1, 5.2; appendix §J). The PDFs give four token examples and validation counts, not the raw 72 pairs or actual hashes to audit independently. |
| F. 358H realized cost | **SUPPORTED WITH CAVEAT** | Complete round terms reconstruct aggregate speedups 0.7227 CPU and 0.3477 NPU; 87.34% target side on CPU and 58.35% replay-plus-proposal on NPU (manuscript §5.3/Figure 4, pp. 6, 8; appendix §D). Replay and proposal are inseparable; source reconstruction and session uncertainty constrain causal extrapolation. |
| G. M4 runtime | **WELL SUPPORTED** | Disjoint 40/16/60 splits, direct-ID 48/48 qualification and 180/180 for each speculative condition, held-out Guard 1.3114× versus target-only and fixed 1.3469×; the paired secondary ratio favors fixed (manuscript §§7.2–7.3/Table 3, pp. 7–9; appendix §H, p. 5). This supports exact profitable execution, not a Guard benefit over fixed. |

## 9. Audit of the 72/72 claim

| Question | Answer | Basis |
|---|---|---|
| Is the result visible? | **YES** | Abstract and introduction on p. 1, §5.2 on p. 5, conclusion on p. 10; appendix §J. |
| Are predictions complete generated-token-ID sequences? | **YES** | The stipulated endpoint is all 128 committed IDs or earlier inclusive EOG, excluding prompts/uncommitted proposals; all 72 complete arrays are reported compared (appendix §§I–J, pp. 5–6). Raw arrays are not printed. |
| Frozen before live outcomes? | **PARTIAL** | Chronology explicitly says the predictor, 72 arrays and digest preceded the first live serialized run, with no edits/reruns; artifact-only PDFs do not expose timestamped arrays or digest for independent verification (manuscript §5.2; appendix §J). |
| Reserved separately from discovery? | **YES** | Twelve outcome-exposed discovery tasks versus 24 hash-selected reserved tasks after excluding 31/164 known-associated tasks; “no known exposure” is only as strong as the audited records (appendix §J). |
| Was the test falsifiable? | **YES** | Frozen H1/H2 decision tree and 72/72 complete-sequence criterion; a single mismatch fails, and H2 was not pursued after H1 passed (appendix §J). |
| Sufficiency versus unique causality? | **YES** | The prose says a sufficient target execution partition on the tested stack and explicitly disclaims a unique kernel, common RTX cause, or universal micro-batch rule (manuscript §§5.2, 9; appendix §J). |

## 10. Comparator and validation separation

**MOSTLY CLEAR.** Section 2.1 (p. 2) explicitly differentiates parsed/re-tokenized CLI text in historical M4/RTX/B570 from direct generated IDs on 358H and fresh RTX/B570/M4 runtime studies. Section 4 and Figure 3 (pp. 4–7) repeatedly prohibit retroactive certification; appendix §§B, I and Tables A3–A5 retain separate counts. The introductory juxtaposition of four-system timing and new qualification remains cognitively dense, while appendix Table A4 compresses the old comparator into “exact” entries. The reader can recover the correct distinctions without needing external material, but can miss them in a quick scan.

## 11. Actual population and exclusions

The evidence concerns single-request, greedy, 128-token-cap, largely Qwen3-8B Q8 0 target/Qwen3-0.6B Q8 0 draft executions under specified llama.cpp paths; 358H changes the draft to OpenVINO symmetric INT4. M4 uses 24 Spec-Bench prompts and separate HumanEval30 timing, plus a 60-prompt held-out mixed-family runtime study; fresh RTX/B570 use the same 30 HumanEval IDs and three repetitions; B570 mechanism reserves 24 HumanEval tasks after excluding 31 of 164 with any recorded B570 association. Measurements omit loading and initial prefill, production concurrency, broader models, functional execution/pass@k, complete-system energy comparisons, and unseen backend behavior. Audits rule out *known* prior exposure, not all possible prior runs. Hardware, backend, OS and runtime covary (manuscript §§3, 9; appendix §§I–J). **SIGNIFICANCE CONCERN:** scope is candid and internally valid for these configurations, but the principal predictive finding's value beyond one target implementation is unshown.

## 12. First-page test

In a three-minute title/abstract/introduction-only read (manuscript p. 1), I would see a systems paper about qualification and realized cost, not a proposed faster decoder. “Consumer systems” might initially suggest a four-device benchmark or architectural ranking, but the abstract's distinct RTX/B570, 358H, and M4 findings and the introduction's campaign-specific cautions largely correct that impression. **72/72 is highly visible** in both abstract and introduction. The novelty is visible early as frozen direct-ID qualification and predictive B570 target-partition isolation; the practical evaluation sequence closes the page. The abstract is dense with seven numerical endpoints and could foreground the specific prediction before platform inventory. It responsibly says fixed M4 speculation beats Guard.

## 13. Key figure and table assessment

| Item | Necessity, readability, information, and risk |
|---|---|
| Table 1, p. 4 | Necessary scope map; compact and readable. Its comparator caption prevents the four configurations from masquerading as a controlled hardware comparison. |
| Table 2, p. 4 | Necessary negative/positive outcome inventory with gates and classes. Dense but useful; diagnostic B570 CI next to valid speedups is a possible skimming hazard, mitigated by “Diag.” and text. |
| Figure 1, p. 5 | Clear visual of opposite M4 regimes and intervals; somewhat redundant with Table 2 but makes parity and separate studies legible. Caption correctly bars workload-only causal inference. |
| Figure 2, p. 6 | Useful conceptual organizing figure, though largely repeats §§2 and 6 and has many caption caveats. No quantitative new information; consider simplifying, not removing. |
| Figure 3, p. 7 | Essential distinction between target-forward proxy and direct-ID gate. Panel B is very clear; Panel A's unlabeled individual context cells require appendix Table A3, and two panels are not same-run cost/correctness evidence. Caption addresses this. |
| Figure 4, p. 8 | Essential and readable isolated-versus-integrated contrast. Mean bars versus prompt-GM headlines are correctly separated. The prominent 58.35% region combines replay and proposal, so attributing its entire width to replay would mislead; caption and text explicitly prevent that. |
| Table 3, p. 9 | Necessary honest comparison; split registered speedups and post-study Guard/fixed ratio help avoid an incremental-control claim. Oracle is bounded and labeled. |
| Appendix Tables A1–A2, p. 2 | Useful reproducibility and energy-boundary checks; detailed but not redundant with main figures. |
| Appendix Table A3, p. 3 | Necessary numerical lookup for Figure 3A; precise contexts show that ranges are not uncertainty intervals. |
| Appendix Table A4, p. 4 | Useful inventory, but mostly overlaps main Table 2 and the short “exact” labels risk losing the text-path caveat when copied. |
| Appendix Table A5, p. 6 | Necessary side-by-side fresh direct-ID counts; avoids confusing 78/90 with historical 60/90. |

## 14. Related Work assessment from the PDFs alone

Section 8 (manuscript pp. 9–10) credits prior speculative-decoding cost accounting, consumer Apple positive/negative outcomes and batch-shape argmax changes (Chordiya), serving and adaptive controllers, heterogeneous CPU/GPU/NPU placement and predictive models, numerical nondeterminism, deterministic inference, and draft-state reuse. It differentiates the present work by prospective **complete generated-ID** qualification plus a frozen **output-trajectory prediction**, and correctly does not claim novelty for the cost identity, numerical phenomenon, heterogeneous placement, or persistent-state idea. This appears fair on the paper's own account. The riskiest novelty reading is a general “target partition mechanism” or portable qualification recipe: the data establish predictive sufficiency for one B570 configuration, while cited numerical and correctness work already motivates sensitivity to execution shape. The M4 guard's adaptive-policy novelty is appropriately minimized because prior controllers exist and its fixed comparator wins.

## 15. Single strongest objection

If I were arguing against acceptance, I would say... the one genuinely distinctive predictive mechanism is a 24-prompt validation on one B570 backend and one greedy model pair; it does not identify the operation causing divergence or demonstrate the prediction on another target backend. Meanwhile the other clean new runtime endpoint is slower than its fixed-speculation comparator, the 358H intervention has no qualified performance result, and historical profitable/negative timing rests on a weaker text-path contract. Thus the paper's strong measurement discipline may exceed its demonstrated new systems generality (manuscript §§5, 7, 9; appendix §§H–J).

## 16. Single strongest acceptance argument

If I were arguing for acceptance, I would say... the paper changes a loose correlation into a falsifiable held-out prediction: target-only execution with a chosen target partition reproduces all 72 complete serialized B570 trajectories, including their failures against the reference. Together with fresh direct-ID gates and a complete 358H cost decomposition, that result teaches practitioners exactly why a promising fast path can be inadmissible and why a fast isolated draft can fail in a stateful loop. The candid blocked and negative endpoints make this a valuable empirical systems result without requiring an invented speedup (manuscript §§5–7; appendix §§D, I–J).

## 17. Actionable edits

**MUST FIX**

- Add to manuscript §5.2 or appendix §J a compact audit-accessible manifest for the 24 reserved IDs with predicted/live sequence digests, reference equality, and first divergence for all cases, plus the committed prediction digest and chronology markers. The PDFs currently assert these rather than exposing enough to independently inspect the entire 72/72 endpoint.
- In the abstract/conclusion, keep “sufficient target execution partition **on the tested B570 stack and workload**” adjacent to the 72/72 claim, so the strongest result cannot be detached from its scope.

**SHOULD FIX**

- Put a one-sentence “historical text-path timing / fresh direct-ID qualification / reserved predictive validation” roadmap directly before Table 2 (§4, p. 4); repeat comparator in Table A4 cells or row labels instead of relying only on its caption.
- Provide a fresh matched latency measurement for the direct-ID-qualified RTX serialized path, if already available under the frozen path, or explicitly flag the absence beside Figure 3B. Do not graft historical RTX timing onto it.
- Tighten Figure 2 and its caption so the B570 predictor and 358H measured interface appear as two independent diagnoses, not a causal chain across devices.

**OPTIONAL**

- Add a second target/backend partition prediction study, preferably with a failure mode or partition choice that could falsify transfer. This would materially raise generality but is not required to state the current scoped claim.
- Report a rough decision-time/iteration-cost illustration for qualification and target-only partition probing, bounded to this evaluation, to make the practitioner value concrete.

## 18. Recommendation

**WEAK ACCEPT**

## 19. Confidence

**4/5.** The PDFs supply detailed protocols, estimators, negative outcomes, and caveats. I cannot independently inspect the private raw arrays, digests, or timing records from these two PDFs.

## 20. Decision rationale

The 72/72 result is a meaningful scientific contribution because it tests an outcome-frozen prediction of complete output trajectories, including the mismatch cases, rather than only reporting timing or post hoc correlation. Fresh direct-ID qualification makes the RTX and B570 execution-path contrast credible within the stated workload, and 358H round accounting supports a practical distinction between isolated throughput and realized stateful cost. The paper also handles a disappointing M4 controller comparison and a stopped 358H candidate honestly. These findings form a coherent systems lesson about admissibility before profitability. I am near the boundary because the predictive mechanism is confined to one backend and does not identify a unique numerical cause; the additional cross-platform results are not a controlled transfer study or a new winning runtime. The strong prospective design, clear inferential limits, and useful failure diagnosis outweigh that limited generality for a weak accept. Exposing more of the reserved prediction manifest would improve auditability (manuscript §§5–9; appendix §§D, H–J).

## Special Questions

| Question | Answer | Reason |
|---|---|---|
| Q1. Paper's main contribution | **E — coherent B+C+D** | Direct-ID qualification, predictive B570 mechanism, and realized 358H cost are distinct but connected gates; the M4 runtime is supporting evidence (manuscript §§5–7). |
| Q2. More than benchmark of own system? | **CLEARLY YES** | Reserved prediction of wrong and right trajectories and complete round accounting give diagnostic knowledge beyond four timing numbers (§5.2–5.3). |
| Q3. Importance of frozen 72/72? | **YES** | It is the decisive evidence distinguishing the mechanism claim from outcome-informed batch-shape speculation (appendix §J). |
| Q4. Would second backend transfer change recommendation? | **MAYBE** | A successful, comparably frozen independent prediction could move this to accept; a failure would still be informative if the scope were revised. Current weak accept does not depend on transfer. |
| Q5. Does lack of transfer invalidate current claims? | **NO** | Their wording is carefully restricted to tested path and workload (§9). |
| Q6. 358H role | **USEFUL SUPPORTING** | It supplies the independent realized-cost gate and a concrete failed optimization, but replay and proposal cannot be separated (§5.3, Figure 4). |
| Q7. M4 role | **USEFUL SUPPORTING** | It shows profitable exact runtime execution while honestly falsifying incremental Guard advantage; its contribution to novelty is modest (§7, Table 3). |
| Q8. Exact overstated claims | **NONE FOUND** | The abstract, §§5–7, and limitations repeatedly confine causality, comparator class, and performance. The phrase “isolates a sufficient target execution partition” is justified only in its stated tested-stack sense, which the paper supplies. |
