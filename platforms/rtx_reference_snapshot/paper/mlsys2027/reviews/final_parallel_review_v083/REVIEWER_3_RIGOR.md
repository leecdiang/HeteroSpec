Artifact-only review.
Sources consulted:
  - manuscript-v0.8.3.pdf
  - appendix-v0.8.3.pdf

No README, handover, source files, repository evidence, prior reviews, Git history, PR descriptions, experiment logs, or web searches were used.

## 1. Paper summary

The paper studies when speculative decoding on four consumer systems preserves the matched greedy target output and whether apparent component-level opportunity becomes post-prefill speedup. It distinguishes historical comparisons based on re-tokenized CLI text from fresh generated-token-ID qualification and a frozen trajectory-prediction endpoint. On a shared HumanEval30 protocol, RTX batched and serialized paths agree with the direct-ID reference in 75/90 and 90/90 runs, respectively; B570 fast and serialized paths agree in 60/90 and 78/90, so both B570 paths fail the stipulated all-pairs gate. A B570 target-only micro-batch-one predictor, chosen after 36/36 discovery matches but committed before live reserved outcomes, matches all 72 complete speculative output sequences on 24 reserved tasks. The 60/72 reference-to-live matches show that this includes four reference-divergent, repeat-stable trajectories. On 358H, direct-ID-qualified CPU and NPU drafting both lose to target-only despite better isolated NPU draft throughput: the measured target side dominates CPU time, whereas a combined replay-and-proposal call occupies much of NPU time. An attempted persistent-state/wider-target intervention fails output qualification, without a formal speed test. A separate M4 cost guard preserves direct-ID output and beats target-only on 60 held-out prompts, but fixed speculation is faster in the post-study paired comparison. The contribution is a disciplined, bounded diagnosis across different evidence and measurement boundaries, not a hardware ranking or demonstrated general control improvement. (Manuscript pp. 1–2, 4–10; appendix pp. 5–8.)

## 2. Thesis

Output qualification and realized full-loop cost must precede a claim of useful speculative decoding. A frozen target-partition predictor can explain the observed B570 trajectory at the level of execution-path sufficiency, while component speed measurements and a cost guard alone do not establish deployable speedup. (Manuscript pp. 1–2, 6–9.)

## 3. Top contributions, ranked

1. Prospectively frozen prediction of complete B570 live token-ID trajectories, including reference-divergent cases, with a reserved set and explicit discovery boundary (manuscript §5.2, p. 6; appendix §J, pp. 6–8).
2. Fresh, direct-ID execution-path gates on RTX and B570 that are carefully separated from older text-derived timing (manuscript §5.1 and Fig. 3, pp. 5–6; appendix §I, p. 6).
3. Qualified 358H round accounting that shows why isolated NPU throughput is an insufficient cost measure for the tested state interface (manuscript §5.3 and Fig. 4, p. 7; appendix §D, pp. 1–2).

## 4. Strongest contribution

The B570 reserved trajectory prediction is the most distinctive contribution. Matching a speculative system's *entire* output sequence with target-only greedy micro-batch one, after committing the predictor before 72 live outcomes, tests a sharper, falsifiable statement than merely reporting disagreement rates or post-hoc first-divergence examples. The reference-divergent four prompts make the result informative beyond the 20 prompts where both paths agree with the reference. Its empirical scope is 24 repeat-stable HumanEval trajectories in one backend/model/setting, and the PDF's chronology is an asserted record rather than independent access to the underlying artifacts. The predictor establishes observational sufficiency for this path, not that one kernel or floating-point operation uniquely caused the difference (manuscript p. 6; appendix §J, pp. 6–8).

## 5. Strongest empirical result

The frozen B570 UB1 target-only predictor matches **72/72 complete generated-token-ID sequences** across 24 reserved HumanEval prompts and three runs each; on the same set the UB128 reference matches the serialized live output in only **60/72**, with the other 12 runs spanning four repeat-stable divergent prompts. This is particularly persuasive as a within-configuration trajectory result, subject to 24 rather than 72 independent prompt cases (manuscript §5.2, p. 6; appendix Tables A6–A7, pp. 7–8).

## 6. Strengths

1. The paper states a precise generated-ID contract and does not rebrand historical text-derived matches as direct-ID qualification (§2.1, p. 2; §9, p. 10).
2. The B570 study separates exposed discovery from reserved validation, commits full sequences before live comparison, and reports a different comparator on the same reserved prompts (§5.2, p. 6; appendix §J, pp. 6–8).
3. Stopped or blocked studies retain their failures: B570 timing is diagnostic and the 358H intervention has no formal performance claim (§§4.2, 7.1, pp. 4, 8).
4. Round cost counts all committed output including corrections/bonus, and distinguishes mixed arithmetic total ratios from prompt geometric means (§§2.3, 5.3, pp. 2, 7; appendix §D, pp. 1–2).
5. M4 Guard is compared to fixed speculation and an explicitly hindsight oracle; the post-study nature of the Guard/fixed comparison is disclosed (§7.3 and Table 3, p. 9; appendix §H, pp. 5–6).

## 7. Weaknesses

1. **MAJOR — significance/scope:** The main 72/72 result has 24 independent, repeat-stable prompts, only four independently reference-divergent examples, one model pair, one backend and one micro-batch setting. It supports a useful case mechanism but leaves transfer and prevalence open (§5.2, p. 6; appendix §J and Table A7, pp. 6–8).
2. **MODERATE — validity/missing evidence:** A content digest and a relative-time ledger are good disclosure, but the PDFs alone do not let a reviewer independently check frozen predictor contents, actual chronology, or the 5,681 validator checks. The 91.37-second pre-live interval is reported, not independently certified by the digest (§J, p. 7).
3. **MODERATE — missing comparison:** B570 target-only UB1 reproduction is an observational predictor, not an intervention that toggles only the live speculative target partition while fixing execution history. A same-prefix paired target/logit or live partition ablation would strengthen causal localization beyond sufficiency (§5.2, p. 6; §7.1, p. 8).
4. **MODERATE — significance:** The M4 Guard beats target-only but loses to Always-Spec (Guard/Always-Spec latency 1.0271 [1.0130, 1.0436]); the 358H proposed intervention never passes qualification. Thus the runtime-decision story is an instructive negative test, not a new performance result (§7 and Table 3, pp. 8–9).
5. **MODERATE — validity/scope:** Historical timing and fresh qualification differ in front end, context, driver/reference and sessions. Prompt bootstrap CIs omit those sources of uncertainty; one cannot attach the direct-ID gate to the older throughput estimates or infer hardware-only contrasts (§§3.1–3.2, 5.1, 9, pp. 3, 5–6, 10; appendix §§B, I, pp. 1–2, 6).

## 8. Claim–evidence audit

| Claim | Assessment | PDF basis and limit |
|---|---|---|
| A. Execution-path qualification as a prerequisite for the paper's strict output contract | **WELL SUPPORTED** | Contract, comparator classes, and stop rule are explicit in §2.1 (p. 2); failures are reported rather than optimized through in §§4–7 (pp. 4–9). It is an operational contract on tested configurations, not a universal theorem. |
| B. RTX direct-ID serialization qualifies whereas batching does not | **WELL SUPPORTED** | 75/90 versus 90/90, with a frozen 90/90 gate (§5.1, p. 5; Fig. 3, p. 6; appendix Table A5, p. 6). This is no fresh latency result and is not a causal GPU comparison. |
| C. B570 fast and serialized direct-ID paths remain blocked | **WELL SUPPORTED** | 60/90 versus 78/90 under the same stipulated gate (§5.1, pp. 5–6; appendix Table A5, p. 6). Stable mismatch is still mismatch. |
| D. Target partition suffices to reproduce the tested B570 trajectory | **SUPPORTED WITH CAVEAT** | Discovery 36/36; frozen reserved prediction 72/72, including four divergent prompts (§5.2, p. 6; appendix §J, pp. 6–8). This identifies predictive execution-path sufficiency, not a unique numerical cause or an independently randomized live target-partition intervention. |
| E. Frozen held-out 72/72 complete-ID prediction | **SUPPORTED WITH CAVEAT** | Full-array definition, digest, relative chronology, and row ledger are visible (appendix §J, Tables A6–A7, pp. 6–8); the PDFs assert, but alone cannot independently verify, freeze-time artifact history. Three runs of each prompt are repeat-stable, so the effective diversity is 24 trajectories. |
| F. 358H realized-cost explanation | **SUPPORTED WITH CAVEAT** | Exact CPU/NPU 90/90, totals 13.25/27.54 s versus 9.58 s, CPU 87.34% complete target-side, NPU 58.35% combined replay plus proposal (Table 2, p. 5; Fig. 4 and §5.3, p. 7; appendix §D, pp. 1–2). Replay-only versus proposal-only and any benefit from persistence cannot be estimated. |
| G. M4 runtime Guard preserves output and is profitable but yields no incremental benefit | **WELL SUPPORTED** | Qualification 48/48 each, held-out direct IDs 180/180 each, target/Guard 1.3114 and target/Always-Spec 1.3469; paired Guard/Always-Spec 1.0271 [1.0130, 1.0436] (§7.3 and Table 3, pp. 8–9; appendix §H, pp. 5–6). The last comparison is transparently post-study secondary. |

## 9. Audit of the 72/72 prediction

| Criterion | Judgment | Explanation |
|---|---|---|
| Visible to a PDF reviewer | **PARTIAL** | Aggregate, 24 task IDs, lengths, per-prompt digest prefixes, four divergence tokens, a full prediction-file SHA-256, and relative-time ledger appear in appendix §J, pp. 6–8. The 72 complete arrays and independently inspectable archive are not printed in the PDFs. |
| Complete generated-token-ID sequences | **YES** | Definition includes the whole sequence and length to 128 committed IDs or inclusive earlier EOG, not just initial divergences; Table A7 reports 128 for each listed prompt (§J, pp. 6–8). This is a reported endpoint, not an external replay performed here. |
| Frozen before live outcomes | **PARTIAL** | The stated order has completed predictions at T0 + 1722.38 s and first live outcome at T0 + 1813.75 s, a 91.37 s gap; hash and claimed audit corroborate content identity. Their actual timestamp ordering cannot be independently established from these two PDFs (§J, p. 7). |
| Separate reserved discovery | **YES** | Twelve named exposed discovery tasks select H1 after 36/36. An audit removes 31 of 164 tasks with B570 association; 24 are deterministically selected from the remaining 133, with the caveat that “no known exposure” is record-bounded (§5.2, p. 6; appendix §J, p. 6). |
| Falsifiable | **YES** | The primary requirement is 72/72 complete-sequence equality with no dropped mismatch, and H2 would run only after H1 discovery failure. A divergent live token anywhere would have defeated the endpoint (§5.2, p. 6; appendix §J, pp. 6–7). |
| Avoids a unique-cause leap | **YES** | It repeatedly says target-partition sufficiency on the tested configuration and explicitly disclaims unique kernel, floating-point operation, shared CUDA/B570 cause or universal UB1 rule (§5.2, p. 6; §9, p. 10; appendix §J, p. 6). |

The strongest discriminating evidence is 4/24 reference-divergent prompts, or 12/72 repeated pairs; all 20 reference-equal prompts also agree with the predictor. Repetition stability adds reliability but does not make 72 independent prompt-level replications (appendix §J and Table A7, pp. 6–8).

## 10. Historical versus fresh evidence separation

**VERY CLEAR.** The three H/Q/P classes appear in §2.1 (manuscript p. 2); Table 2 captions and endpoints make the historical text-derived timing boundary plain (p. 5). Figure 3 explicitly labels historical proxies and fresh direct-ID qualification with “no matching fresh latency endpoint” (p. 6). Appendix Tables A4–A6 and §§I–J retain distinct comparators (pp. 4, 6–7), and §9 repeats the non-transfer caveat (p. 10). There is still a risk that a quick reader conflates the same platform names across Table 2 and Fig. 3, but the paper supplies the needed warnings.

## 11. Population and exclusions

**ACCEPTABLE SCOPE LIMITATION**, with a substantial significance cost. Four separately frozen consumer cases share primarily Qwen3-8B/0.6B, greedy k = 2 and mostly HumanEval; 358H uses a symmetric INT4 OpenVINO draft rather than native Q8_0. M4 representative and HumanEval results are different sessions, not a matched workload experiment. Fresh RTX/B570 gates use 30 shared tasks; B570 prediction excludes 31/164 tasks with known B570 association and validates 24/133 eligible ones. M4 Guard excludes prior-exposed IDs and uses 40 calibration, 16 qualification, 60 held-out tasks balanced by two families. All timing omits initial prefill/loading; serving concurrency, longer output, model-family transfer and functional code correctness are untested. These restrictions are explicit, so I do not treat them as a hidden validity failure, but they confine system-level applicability (§§3, 7.3, 9, manuscript pp. 3, 8–10; appendix §§H–J, pp. 5–8).

## 12. First-page test

Reading only the title, abstract and first Introduction page, my three-minute impression is a careful systems-forensics paper with a strong predictive B570 hook rather than a new speedup algorithm. The 72/72 complete-ID, prospective freeze, 24 prompts, and reference-divergent qualification are unusually visible in the abstract and Introduction (p. 1). The first page also states that prior consumer-hardware gains/slowdowns, heterogeneous placement and numerical path dependence exist, then names three precise contributions. This largely averts “benchmark your own machine” confusion. The broad title's “consumer systems” and four-system enumeration can still initially suggest a hardware survey, while the decisive novelty is the one-stack B570 prediction; foregrounding that specific methodological distinction one sentence earlier in the abstract would sharpen positioning. The caveat against a unique numerical cause already appears on page 1.

## 13. Key figures and tables

| Item | Necessary/readable/informative/redundant/misleading assessment |
|---|---|
| Table 1, manuscript p. 3 | **Useful, readable.** Establishes co-varying runtimes, models and evidence scopes; necessary to block hardware-ranking inference. Its historical comparator caveat is in caption. |
| Figure 1, manuscript p. 4 | **Useful, readable.** The opposing M4 outcomes and non-overlapping intervals are immediate. It is not a workload-causal comparison, as caption says; slight redundancy with Table 2 is justified by this visual contrast. |
| Table 2, manuscript p. 5 | **Necessary, readable.** Best overview of speed, endpoint, sample and class. “Second.”/“Diag.” abbreviations and close adjacency of text-path/direct-ID rows require careful reading; the caption handles the key risk. |
| Figure 2, manuscript p. 5 | **Readable but optional/redundant.** Its generic flow restates the prose without experiment counts; it should not be read as an intervention chain across systems, a caveat supplied in caption. Could give room to the B570 mechanism evidence. |
| Figure 3, manuscript p. 6 | **Necessary and informative.** Panel separation prevents improper joining of historical proxy and fresh qualification; 90/90 gate and blocked labels are legible. Proxy ranges connect nonmatched contexts, explicitly not uncertainty; no matching latency is emphasized. |
| B570 discovery/validation schematic, manuscript p. 6 | **Necessary and readable.** Communicates exposure, freeze and 72/72 versus 60/72 in one place; its 72 repeated runs should not be mistaken for 72 independent prompt trajectories. |
| Figure 4, manuscript p. 7 | **Necessary but dense.** Isolated throughput and arithmetic integrated decomposition make the interface cost visible. The CPU 87.34% and NPU 58.35% regions are combined terms; caption correctly refuses replay-only attribution. Distinct prompt-GM speedups are annotated to prevent ratio-of-bars confusion. |
| Table 3, manuscript p. 9 | **Necessary and readable.** Keeps Guard, Always-Spec and post-study paired contrast adjacent; the oracle is properly labeled hindsight. The ratio direction changes between rows and is explained, though a “lower latency is better” marker could reduce reading effort. |
| Tables A1–A3, appendix pp. 2–3 | **Useful audit support.** Exact estimators, sensor domains and all 11 proxy cells prevent selective presentation; A3 is not a controlled cost comparison. |
| Table A4, appendix p. 4 | **Somewhat redundant.** A compact evidence inventory reinforces classes already in Table 2, with useful blocked/diagnostic distinctions; not misleading. |
| Table A5, appendix p. 6 | **Necessary audit support.** Equal prompt counts accompany direct-ID pairs and frozen gate, separately from timing. |
| Tables A6–A7, appendix pp. 7–8 | **Necessary and highly informative.** Same-set comparator and the full 24-prompt ledger identify four actual divergent prompts; digest prefixes do not reveal complete sequences but are clearly labeled as such. |

## 14. Related Work

Based on the PDFs alone, §8 (manuscript p. 9) fairly concedes that speculative decoding, cost/commit accounting, consumer gain/slowdown, heterogeneous execution, numerical path dependence, deterministic inference and adaptive control are prior art. In particular it credits Chordiya for consumer backend characterization and batch-shape argmax observations; Kim and Liu et al. for runtime cost/verification effects; Zhang et al., Yuan et al. and Gond et al. for correctness/numerics; and the heterogeneous/adaptive systems for placement and control. The differentiation is a frozen complete-trajectory prediction on a blocked path plus fresh direct-ID path qualification and measured 358H interface decomposition, not a newly discovered numerical phenomenon or beneficial control policy. I cannot check whether the summarized prior papers fully cover those distinctions from the two supplied PDFs alone. Avoid claiming priority for correctness gating in general or for cost accounting alone; the manuscript mostly observes that boundary (§§1, 2.3, 8, pp. 1–2, 9).

## 15. Single objection against acceptance

If I were arguing against acceptance, I would say... the only genuinely distinctive positive result is a frozen prediction on 24 repeat-stable prompts and one B570 configuration, of which only four prompts distinguish predictor from reference; it remains an observational, target-only reproduction without a live target-partition causal ablation. The other cases offer careful negative characterization, and the one prospective runtime policy loses to fixed speculation. The paper's considerable breadth may exceed the generalizable mechanism or optimization advance established by its restricted sample (§§5.2, 7, 9, manuscript pp. 6, 8–10; appendix §J, pp. 6–8).

## 16. Single argument for acceptance

If I were arguing for acceptance, I would say... the paper sets an unusually explicit output contract, keeps text-derived and direct-ID evidence separate, freezes a testable complete-sequence predictor before a genuinely reserved live set, reports all blocked gates, and measures complete 358H loop costs instead of treating isolated throughput as realized speed. These are substantive systems-method contributions even though the resulting interventions do not accelerate every tested path (§§2–7, manuscript pp. 2–9; appendix §§D, I–J, pp. 1–2, 6–8).

## 17. Requested changes

**MUST FIX**

- In §5.2 immediately after “72/72,” explicitly state that the three runs are repeat-stable and the validation spans **24 distinct trajectories**, with four reference-divergent prompts. The current numbers are correct; this addition keeps the experimental unit visible at the main-text point of interpretation (manuscript p. 6; appendix Table A7, p. 8).
- In §5.2 and the Conclusion, consistently phrase H1 as *predictive/observational target-partition sufficiency* in the tested configuration. State in the same paragraph that the study did not switch only the target micro-batch in the live speculative loop while holding its execution history fixed. This guards against reading “mechanism” as a unique causal numerical localization (manuscript pp. 6, 10).

**SHOULD FIX**

- Add a compact same-prefix/logit or live-partition intervention for the four divergent B570 prompts if feasible, with reference and UB1/UB128 target execution on identical committed prefixes; otherwise specify this as the next discriminating experiment in §9. It would separate a predictive proxy from an intervention-induced trajectory change (manuscript §§5.2, 9, pp. 6, 10).
- Give a reviewer-accessible anonymous artifact locator or a directly checkable commitment procedure for the complete prediction arrays and chronological freeze markers in appendix §J. The printed SHA-256 proves identity conditional on possession of the file, not that it preceded the first live outcome (appendix p. 7).
- In §7.3/Table 3, keep the post-study paired Guard/Always-Spec comparison prominent and avoid a positive “runtime control” interpretation solely from beating target-only; fixed speculation is the relevant incremental baseline (manuscript p. 9).

**OPTIONAL**

- Replace or shrink Fig. 2 and use the space for a same-set summary of B570 20 reference-equal and four reference-divergent prompt counts in the main text (manuscript pp. 5–6).
- Extend direct-ID qualification and the frozen predictor to another model/backend, and rerun latency on a freshly qualified matching path, while preserving separate claims for any changed front end, context or driver (manuscript §9, p. 10).

## 18. Recommendation

**WEAK ACCEPT.**

## 19. Confidence

**4/5.** I can assess the design and displayed evidence closely from both PDFs, but did not independently replay an anonymous artifact or inspect source-level chronology.

## 20. Decision rationale

The novelty is not speculative decoding, consumer variability, correctness checks or adaptive control individually. It is the disciplined combination of a direct-ID path gate with a prospectively committed, complete-sequence predictor on a separately reserved B570 set. The 72/72 result is stronger than an after-the-fact explanation, especially on four reference-divergent prompts, yet its independent diversity is 24 tasks on one path and it identifies sufficiency rather than a unique cause. The 358H decomposition is a valuable complete-loop counterexample to isolated NPU throughput; the M4 Guard is honestly negative against fixed speculation. Statistical reporting uses prompt units and distinguishes the arithmetic breakdown from geometric-mean speedups, while its intervals omit session/state variation. The abstract and figures make comparator boundaries unusually clear. I lean weakly toward acceptance for rigorous, falsifiable systems characterization and useful methodology, conditional on tightening the independent-unit and causal-language points; a venue requiring demonstrated transfer or a successful optimization could reasonably weigh the narrowness against it (manuscript §§2–9, pp. 2–10; appendix §§B, D, H–J, pp. 1–2, 5–8).

## Special Questions

**Q1.** **E — coherent B+C+D:** execution-path qualification, predictive mechanism on B570, and heterogeneous realized runtime cost form a coherent bounded story. Consumer-hardware characterization alone undersells it (manuscript §§1, 5–7, pp. 1, 5–9).

**Q2.** **CLEARLY YES.** Frozen complete-ID prediction on reference-divergent reserved cases and exact cost-boundary accounting are more than benchmarking one system, though transfer is unknown (§5.2 and §5.3, pp. 6–7).

**Q3.** **YES.** Prospective 72/72 is central to publishability; absent the freeze and complete-ID endpoint, the B570 observation would be a considerably weaker post-hoc match. Treat it as 24 repeat-stable prompt trajectories (§5.2, p. 6; appendix §J, pp. 6–8).

**Q4.** **MAYBE.** A second backend with the same prospectively frozen partition-to-trajectory prediction, especially with reference-divergent examples, would materially strengthen significance and could raise my rating; failure to transfer would also sharpen the bounded claim (§9, p. 10).

**Q5.** **NO.** Lack of second-backend transfer does not invalidate a correctly stated one-configuration predictive result. It limits generality (§9, p. 10).

**Q6.** **Useful supporting.** The 358H exact-output negative path and 87.34%/58.35% measured regions establish why isolated device speed does not answer realized-cost questions, but cannot separate replay from proposal or quantify a successful persistence intervention (§5.3 and Fig. 4, p. 7).

**Q7.** **Useful supporting.** M4 shows the qualification-to-runtime decision sequence can be executed, but Guard has no incremental benefit over Always-Spec; presenting it as a new speedup would distract (§7.3 and Table 3, p. 9).

**Q8.** **NONE FOUND** among the manuscript's explicit headline conclusions. Potentially ambiguous shorthand is “target-partition sufficiency” in §5.2 (p. 6) if interpreted as a unique causal operation; the adjacent text and §9 explicitly bound it to predictive reproduction in this configuration. The 72/72 phrasing could suggest 72 independent trajectories to a hurried reader, so report 24 distinct prompts alongside it.
