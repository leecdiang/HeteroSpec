Artifact-only review.
Sources consulted:
  - manuscript-v0.8.2.pdf
  - appendix-v0.8.2.pdf

No README, handover, source files, repository evidence, prior reviews,
Git history, PR descriptions, experiment logs, or web searches were used.

## 1. Paper summary

This paper argues that speculative decoding on consumer systems must be evaluated in two steps before a speed claim is meaningful: the actual execution path must preserve a specified output sequence, and the integrated stateful loop must beat a matched target-only baseline. It presents distinct campaigns on M4, RTX 5070 Ti Laptop, Arc B570, and Core Ultra X7 358H, carefully distinguishing historical comparisons reconstructed from CLI text from new direct generated-token-ID studies. The strongest new result is a prospectively frozen B570 mechanism test. A target-only greedy path with target micro-batch one first explains 36/36 exposed discovery sequences; its prediction then matches all 72 complete serialized-speculation sequences on 24 separately reserved HumanEval prompts. Crucially, four reserved prompts are predicted to remain divergent from the reference, so the result is more than predicting universal equality. Fresh direct-ID qualification finds RTX agreement improves from 75/90 batched to 90/90 serialized, whereas B570 improves from 60/90 to 78/90 and remains blocked. The 358H measurements show that an isolated NPU drafting advantage is lost at the tested full-prefix replay interface; a proposed stateful intervention fails qualification before performance testing. On M4, a frozen continuation guard preserves 180/180 direct-ID sequences and beats target-only on 60 held-out prompts, but the fixed speculative policy is faster in the paired secondary comparison. The contribution is a disciplined, path-scoped empirical method and a specific predictive mechanism result, rather than a universal hardware ranking or a new universally superior controller. (Main pp. 1–10; appendix §§I–J, pp. 5–6.)

## 2. Central thesis

Local drafting and verification microbenchmarks do not establish an admissible or profitable speculative decoder. On the tested stacks, direct-ID qualification, controlled target-partition prediction, and complete post-prefill cost accounting expose failures that component metrics obscure. (Main §§2, 5–7, pp. 2, 5–9.)

## 3. Top contributions, ranked

1. **Frozen B570 target-partition prediction:** 72/72 complete reserved serialized trajectories predicted by target-only micro-batch-one execution, including 12/12 first-divergence indices across four divergent prompts (main §5.2, p. 5; appendix §J, p. 6).
2. **New direct-ID path qualification:** matched protocol families show RTX 75/90 → 90/90 and B570 60/90 → 78/90 under serialization, with opposite gate outcomes and no retrospective certification of old timing (main §5.1, pp. 5, 7; appendix §I, pp. 5–6).
3. **Realized-cost diagnosis:** exact 358H CPU/NPU paths lose despite isolated NPU draft throughput, with measured complete target, draft-interface, and residual regions; the attempted wider target setting is honestly stopped at correctness qualification (main §§5.3, 7.1, pp. 6–8; appendix §D, p. 1).

## 4. Single strongest contribution

The B570 reserved prediction turns a plausible post hoc explanation into a prospective test. Its importance is that output qualification is often treated as a binary sanity check; here an execution partition predicts the *particular wrong trajectory* of a still-blocked path. It is nontrivial because target-only micro-batch one reproduces serialized speculative output without live draft inference, while the target reference uses another partition; four reserved prompts have stable divergences rather than all outputs simply matching. The evidentiary chain is 90/90 target-harness/reference reproduction, 36/36 exposed discovery agreement to select H1, pre-outcome commitment of all 72 reserved complete predictions, 72/72 matches, 60/72 reference equality, and matching first-divergence indices and tokens on four prompts. The manuscript and appendix disclose the decision tree, reserved IDs, selection rule, and chronology, but not the complete predicted arrays or hashes for independent verification within these PDFs. The finding is sufficient partition reproduction on one stack, not proof of a unique kernel or general mechanism. (Main §5.2, p. 5; appendix §J, p. 6.)

## 5. Single strongest empirical result

**72/72 complete direct-ID sequences predicted** on 24 reserved B570 prompts × three repetitions; 20 prompts are predicted reference-equal and four reference-divergent, with 12/12 divergent repetition-pair first-divergence indices matched. The blocked reference endpoint remains 60/72, making the exact prediction of failures especially informative. The nominal 72 observations include three stable repetitions per prompt, so the independent workload breadth is 24 prompts, four with divergent behavior. (Main §5.2, p. 5; appendix §J, p. 6.)

## 6. Strengths

1. Output contract, timing boundary, and evidence class are explicit before results; the paper never silently promotes historical re-tokenized text equality to direct generated-ID equality (main §2, pp. 2–3; Table 2, p. 4).
2. The reserved mechanism test has a meaningful negative-outcome prediction and clear stop/selection logic, rather than a retrospective fit to aggregate agreement (main §5.2, p. 5; appendix §J, p. 6).
3. New RTX/B570 direct-ID studies disclose blocked paths alongside the one qualifying path; the latter is not used to claim unmeasured fresh speed (main §5.1, p. 5; appendix Table A5, p. 6).
4. Complete committed-token accounting on 358H correctly includes correction/bonus progress and separates prompt-geometric-mean speedups from arithmetic aggregate cost identity (main §§2.3, 5.3, pp. 2, 6; appendix §D, p. 1).
5. The M4 controller result reports the adverse fixed-policy comparison and its post-study status, and the failed 358H intervention has no invented performance result (main §7, pp. 7–9).

## 7. Weaknesses

1. **MAJOR — scope/significance:** The causal mechanism and predictive success center on one B570 build/model pair, one greedy k=2 HumanEval setting, and 24 reserved prompts. The result supports a useful case study, but transfer to a second backend or model family is untested (main §9, p. 10; appendix §J, p. 6).
2. **MODERATE — missing evidence:** The PDFs summarize the 72 sequence predictions, chronology, digest, and independent validation but do not expose the complete arrays or digest values. An artifact-only reviewer can inspect four first-divergence tuples, not independently replay the strongest endpoint (appendix §J, p. 6; appendix §A, p. 1).
3. **MODERATE — validity:** Historical M4/RTX/B570 equality uses parsed/re-tokenized CLI output, with M4 HumanEval including the prompt in the parsed text; those timing outcomes cannot establish the paper's stricter direct-ID contract. The authors mark this boundary, but it reduces the amount of strict-ID performance evidence outside 358H and prospective M4 (main §§2.1, 4, pp. 2, 4; appendix §B, p. 1).
4. **MODERATE — significance/missing comparison:** The M4 Guard beats target-only but loses to fixed speculation, 1.0271× Guard/Always-Spec latency [1.0130, 1.0436] in a post-study secondary analysis. The control demonstrates an exact runtime endpoint, not incremental value from control or comparison with advanced serving controllers (main §7.3, p. 9; appendix §H, p. 5).
5. **MINOR — clarity:** The first page opens as a four-system consumer characterization, while the strongest contribution is the narrower prospective B570 predictor; Figure 3 combines historical cost proxies and new qualification in adjacent panels that require careful reading to avoid interpreting them as paired measurements (main p. 1; Fig. 3, p. 7).

## 8. Claim–evidence audit

| Claim | Judgment | Evidence and precise limit |
|---|---|---|
| A. Execution-path qualification | **WELL SUPPORTED** | The intended generated-ID contract, blocking rule, comparator classes, and distinction between probe and workload-wide gate are defined explicitly; failure can block performance inference even with favorable timing. This is an operational contract, not a claim of universal model semantics (main §§2.1–2.2, p. 2). |
| B. RTX direct-ID | **SUPPORTED WITH CAVEAT** | Fresh shared-task study reports 75/90 batched and 90/90 serialized, all repetitions stable; only serialized reaches its gate. The PDF supplies protocol and counts, while raw ID arrays are outside the PDFs, and different driver/reference settings bar retrospective timing certification (main §5.1, p. 5; Fig. 3B, p. 7; appendix §I/Table A5, pp. 5–6). |
| C. B570 direct-ID | **SUPPORTED WITH CAVEAT** | Fresh 60/90 fast and 78/90 serialized counts establish that neither path qualifies on the tested task set; the source-instrumented endpoint and recovery from a pre-inference launcher failure are explained. Complete raw traces are not printed and these are not population failure-rate estimates (main §5.1, p. 5; appendix §I/Table A5, pp. 5–6). |
| D. B570 target-partition mechanism | **SUPPORTED WITH CAVEAT** | Target-only H1 changes target nubatch to one; target harness first reproduces 90/90 references and exposed discovery matches 36/36. The 72/72 reserved prediction supports *sufficient reproduction* of the serialized trajectory, not a unique kernel, numerical cause, or general backend rule (main §5.2, p. 5; appendix §J, p. 6). |
| E. 72/72 held-out prediction | **SUPPORTED WITH CAVEAT** | The selection rule, 24 IDs, pre-outcome commitment chronology, success rule, 72/72 result, 60/72 reference equality, four divergence tuples, and validation-check count are reported. Complete arrays and digest values remain outside the PDFs, so the result is documented rather than independently auditable from the two PDFs alone (main §5.2, p. 5; appendix §J, p. 6). |
| F. 358H realized cost | **SUPPORTED WITH CAVEAT** | Direct round records give C=2.4631/2.4584 and (D,R,X)=(0.4304,2.9767,0.00124)/(4.1251,2.9435,0.00130), with reconstructed arithmetic ratios 0.7227/0.3477; primary prompt-GM speedups are 0.734/0.352. Replay plus proposal is one inseparable call, so its replay-only share and a persistence gain cannot be inferred (main §5.3 and Fig. 4, pp. 6, 8; appendix §D, p. 1). |
| G. M4 runtime | **SUPPORTED WITH CAVEAT** | Disjoint 40/16/60 splits, frozen E8 margin-zero rule, 180/180 direct-ID equality for each speculative condition, Target/Guard 1.3114 and Target/Always-Spec 1.3469 are reported. The freeze-hash metadata defect is transparently recovered; the Guard/Always-Spec 1.0271 contrast is post-study secondary and conditional bootstrap intervals omit session/recalibration variation (main §7.2–7.3/Table 3, pp. 7–9; appendix §H, p. 5). |

## 9. Audit of the 72/72 claim

1. **Visible? PARTIAL.** The endpoint, prompt IDs, counts, four divergent token substitutions, and first-divergence indices are visible; individual predictions for all 72 runs are not (main §5.2, p. 5; appendix §J, p. 6).
2. **Complete generated-token-ID sequences shown? NO.** The text asserts complete arrays and a committed digest, but prints neither the full arrays nor digest values. Four first-divergence tuples are useful spot evidence, not complete traces (appendix §J, p. 6).
3. **Frozen before live outcomes? PARTIAL.** The chronology explicitly states commitment of predictor, endpoint, IDs, binaries, criterion, and all 72 arrays before first live serialized outcome, with no edits or selective reruns. PDFs alone cannot independently inspect timestamps or committed content (main §5.2, p. 5; appendix §J, p. 6).
4. **Reserved separately from discovery? PARTIAL.** Twelve exposed tasks are named, 31/164 tasks with any recorded B570 association are excluded, and 24 IDs are hash-selected from 133 remaining. Separation is strong within audited records; unknown exposures cannot be excluded from the PDFs (main §3.1, p. 3; appendix §J, p. 6).
5. **Falsifiable? YES.** The predeclared endpoint requires 72/72 whole-sequence matches with no partial threshold. Predicting four divergent prompts, 12 divergence locations, and 60/72 reference equality exposes the hypothesis to specific failure, not merely a generic exactness count (main §5.2, p. 5; appendix §J, p. 6).
6. **Sufficiency versus unique causality distinguished? YES.** The paper says target micro-batch one is sufficient to reproduce these trajectories while declining kernel identification, a universal rule, a shared RTX/B570 root cause, or a production certificate (main §§5.2, 9, pp. 5, 10; appendix §J, p. 6).

## 10. Three evidence modes

**VERY CLEAR.** Section 2.1 explicitly assigns historical M4/RTX/B570 agreement to reconstructed token arrays from parsed CLI text and direct-ID status to 358H, new RTX/B570 qualification, and prospective M4. Sections 4 and 5.1 repeat that new direct-ID qualification is separate from old timing; Fig. 3 labels panel A historical physical opportunity and panel B prospective direct-ID qualification. Section 5.2 then specifies reserved prospective prediction as a third, stronger mechanism endpoint. Table 2, Fig. 3, appendix Tables A3/A5, and appendix §J preserve the separation. The remaining presentation hazard is readers skimming Table 1 or Table A4's unqualified word “exact” without the caption and comparator notes. (Main §§2.1, 4, 5.1–5.2, pp. 2, 4–7; appendix pp. 3–6.)

## 11. Population, exclusions, narrowness

The experiments concern greedy post-prefill decoding, Qwen3-8B Q8_0 target and Qwen3-0.6B Q8_0 draft except symmetric INT4 OpenVINO drafting on 358H, fixed k=2 in the focal studies, particular llama.cpp/Metal/CUDA/Vulkan and OpenVINO stacks, single-request execution, and HumanEval/Spec-Bench prompts capped at 128 generated tokens. Historical M4 uses 24 representative prompts and 30 separate HumanEval prompts; new RTX/B570 studies each use 30 HumanEval prompts × three repetitions. B570 validation reserves 24 of 133 eligible HumanEval tasks after conservatively excluding 31 with recorded B570 association from 164; 12 exposed tasks drive H1 selection. M4 runtime splits 40 calibration, 16 qualification, and 60 held-out prompts after excluding recorded prior M4 exposure, balanced by HumanEval/Spec-Bench family. Excluded boundaries include loading, initial prefill, concurrent serving, other model families, code execution/pass@k, and full system energy. **SIGNIFICANCE CONCERN**, because one backend's mechanism result carries the central novelty; the paper appropriately scopes its validity rather than hiding this narrowness. (Main §§3, 7.3, 9, pp. 3, 8, 10; appendix §§H–J, pp. 5–6.)

## 12. First-page test

**Three-minute impression:** A careful systems paper about correctness-gated performance, with a prominent 72/72 frozen prediction and an unusually candid negative Guard comparison. The first page presents numerical endpoints, evidence types, and core caveats efficiently. **Consumer benchmark confusion:** The title and first abstract sentence invite a broad cross-device ranking, yet the introduction immediately calls the synthesis retrospective and the headline timing comparators campaign-specific. A reader skimming only the title and Table 2 might still overread the four platforms as a matched benchmark. **72/72 visibility:** Excellent: it appears in the abstract and first-page introduction, with “complete” and “separately frozen reserved” qualifiers. **Novelty early:** The first-page ranked contributions place prospective direct-ID qualification and frozen target-partition prediction before cost characterization, and acknowledge established heterogeneity and deterministic-inference work. A shorter first abstract sentence that foregrounds the path prediction could further sharpen the strongest contribution. (Main p. 1 only.)

## 13. Figures and tables

| Item | Assessment |
|---|---|
| Table 1 (main p. 4) | Necessary scope map; compact and readable. The evidence-scope cell is valuable. “Qualified” should always carry its comparator, as the caption does; hardware/software co-variation is stated. |
| Table 2 (main p. 4) | Necessary numerical inventory of profitable, negative, and blocked outcomes. The classes and caption prevent B570's narrow CI from becoming an admissible speed claim. “Matching pairs” risks skimming as direct-ID exactness; the caption and text repair it. |
| Figure 1 (main p. 5) | Useful, readable comparison of opposite M4 observed regimes and separate CIs; nonpaired-session caveat is in the caption. It is not evidence of a causal workload effect. |
| Figure 2 (main p. 6) | Conceptual map is helpful for separating local opportunity, qualification, and realized costs. Text density and small formulas make it somewhat redundant with §2 and §6, but the blocked/qualified branch adds genuine orientation. |
| Figure 3 (main p. 7) | Panel B is essential and quickly communicates the direct-ID gate; panel A makes the local proxy concrete. Adjacent panels could mislead as same-run cost/correctness coordinates, but the caption expressly says otherwise. Tiny context-cell marks need appendix Table A3. |
| Figure 4 (main p. 8) | Essential visual juxtaposition of isolated NPU throughput with larger integrated NPU latency. Readable units and arithmetic baseline; the distinction from prompt-GM headline estimates and inseparable replay/proposal region is correctly flagged. |
| Table 3 (main p. 9) | Essential for the unfavorable Guard versus fixed-policy result. The separate post-study row prevents it being mistaken for the registered primary contrast; ratio directions are stated. |
| Appendix Table A1 (p. 2) | Necessary for exact estimator/bootstrap conventions, although finite-bootstrap index detail is unlikely to affect interpretation. |
| Appendix Table A2 (p. 2) | Useful compact guardrail against whole-system energy comparisons. |
| Appendix Table A3 (p. 3) | Necessary lookup for all 11 Figure 3A context cells; clear that ranges are not uncertainty. |
| Appendix Table A4 (p. 4) | Some redundancy with main Table 2, but useful evidence-class synthesis. Its “exact” wording requires the caption's text-path qualification. |
| Appendix Table A5 (p. 6) | Essential clean separation of fresh direct-ID counts from historical timing; qualification threshold is transparent. |

## 14. Related Work, from these PDFs only

The related-work discussion credits basic speculative decoding and explicit cost/committed-token accounting (Leviathan; Liu et al. 2026b; Kim), prior Apple consumer positive/negative regimes and batch-shape argmax issues (Chordiya), heterogeneous placement and cost models (Dovetail, DuoDecoding, Mirror-SD, Ruiz y Mesa, Lever), adaptive policies (TurboSpec, BanditSpec, HeteroSpec), numerical path dependence and determinism (Zhang, Yuan, LLM-42), and state reuse (Yuan et al. 2026). The differentiation is fair as *presented*: a frozen, direct-ID target-partition prediction of individual serialized trajectories, with strict evidence-class accounting, is narrower than claiming the first correctness issue, heterogeneous system, cost model, or adaptive rule. The paper expressly avoids claiming its failed 358H intervention defeats successful heterogeneous co-design or its M4 Guard outperforms sophisticated controllers. I cannot verify priority or the summaries of cited works beyond the two supplied PDFs. Unsafe novelty language would be any implication that batch-shape numerical divergence, correctness gating, state replay cost, or adaptive continuation were first discovered here; the actual manuscript mostly avoids it. (Main §8, pp. 9–10; first-page contribution paragraph, p. 1.)

## 15. Single strongest objection

If I were arguing against acceptance, I would say... the paper's distinctive frozen predictor is still a one-stack, one-model, one-workload case in which only four of 24 reserved prompts diverge; the PDFs do not include all 72 committed arrays for independent inspection. Much of the remaining four-system performance narrative uses historical text-path agreement that does not meet the paper's own direct-ID contract. The M4 controller loses to fixed speculation and the 358H intervention never reaches performance testing. That leaves a disciplined and suggestive case study, but arguably too little demonstrated transfer or realized new performance benefit for a broad MLSys contribution. (Main §§5, 7, 9, pp. 5–10; appendix §J, p. 6.)

## 16. Single strongest acceptance argument

If I were arguing for acceptance, I would say... the paper makes an empirically consequential systems distinction and then tests it prospectively. The B570 experiment predicts *which exact complete trajectories will occur*, including the wrong ones, after freezing a target-only mechanism hypothesis and reserving previously unexposed prompts. That is much stronger than diagnosing an observed mismatch or reporting a coarse accuracy fraction. Fresh RTX/B570 direct-ID qualification demonstrates that serialization can cross the strict gate on one tested path while still failing on another; 358H measured round regions explain why local NPU throughput is no speed guarantee. The paper accurately labels historical and secondary evidence, reports a failed intervention and an inferior Guard policy, and gives practitioners a reproducible sequence of qualification, partition isolation, and full-cost measurement. This bounded but substantive methodology deserves acceptance despite limited transfer. (Main §§2, 5–7, 9, pp. 2, 5–10; appendix §§I–J, pp. 5–6.)

## 17. Requested changes

**MUST FIX**

- In main §5.2 and appendix §J, add a compact public-in-paper representation of the reserved test commitment: at least the digest value, its serialization definition, commitment ordering, and an access pointer or table of all 24 per-prompt complete-array hashes plus lengths. The full arrays can remain in an artifact, but the PDF should enable a reviewer to bind the announced 72/72 endpoint to a specific pre-outcome commitment.
- In main Table 2 and appendix Table A4, replace or qualify every standalone “matching/exact” impression in row labels with an explicit comparator tag (text-path versus direct ID), preserving the already clear captions. This matters because historical timing is prominent.

**SHOULD FIX**

- In the abstract and §1, foreground the prospective trajectory-prediction contribution earlier than the four-system characterization, and call the cross-platform synthesis separate case studies in one short phrase (main p. 1).
- In §5.2, give both prompt-level and repetition-level denominators together: 24 reserved prompts, four divergent prompts, 72 stable executions, and 12 divergent pairs; explain why three repeats test determinism but do not triple task diversity (main p. 5).
- In §7.3/Table 3, keep the Guard/Always-Spec adverse result adjacent to the Guard/target gain in every summary and state that the CI is a post-study secondary, session-conditional comparison (main p. 9).

**OPTIONAL**

- Add a second backend/model-family transfer test if feasible; a failed transfer with the same frozen protocol would still sharpen the boundary of the mechanism (main §§5.2, 9).
- Simplify Figure 2's dense text and add a stronger visual separation between historical panel A and prospective panel B of Figure 3 (main pp. 6–7).

## 18. Recommendation

**ACCEPT.**

## 19. Confidence

**4/5.** I can assess the PDFs' protocol, claims, tables, arithmetic consistency, and disclosure boundaries, but cannot inspect the private sequence archive or independently verify priority against external literature under this artifact-only assignment.

## 20. Decision rationale

The acceptance case rests on the reserved B570 prediction, not on a universal consumer-hardware benchmark or a successful adaptive policy. The study reports a frozen target-only micro-batch-one predictor that matches all 72 complete serialized trajectories and specifically anticipates four prompts whose outputs remain wrong against the reference. That result, together with new direct-ID RTX/B570 gates and measured 358H full-loop costs, makes execution-path qualification a concrete systems result. I give weight to the authors' refusal to promote historical re-tokenized text matches to direct-ID proof, their blocked-path labels, and their candid disclosure that Guard loses to fixed speculation and a 358H intervention stops before timing. The chief reservations are narrow transfer, absence of complete reserved traces in the PDFs, and limited strict-ID performance breadth. Those should constrain the claims and prompt an improved commitment record, but do not erase the prospective prediction or the useful empirical method. The paper is acceptable as a carefully bounded systems study. (Main §§2, 5–9, pp. 2, 5–10; appendix §§H–J, pp. 5–6.)

## Special Questions

| Question | Answer | Reason |
|---|---|---|
| Q1. Core contribution | **E — coherent B+C+D** | Path qualification, predictive mechanism, and realized cost form a useful decision sequence; C is the strongest novel element (main §§5–6, pp. 5–7). |
| Q2. More than benchmark of own system? | **CLEARLY YES** | Frozen output-trajectory prediction, direct-ID gate, and explicit cost boundaries answer a systems-method question beyond a platform leaderboard (main §§2, 5–6). |
| Q3. Importance of frozen 72/72? | **YES** | The pre-outcome prediction includes exact divergent outputs, which materially raises evidentiary weight over post hoc mismatch explanation (main §5.2; appendix §J). |
| Q4. Would second-backend transfer change recommendation? | **MAYBE** | A positive or well-explained negative transfer would increase confidence and could strengthen the score, while the present bounded result already clears my acceptance bar. |
| Q5. Does absent transfer invalidate current claims? | **NO** | The stated claims concern a tested B570 partition and named stacks; they avoid a universal target micro-batch rule (main §9, p. 10). |
| Q6. Role of 358H | **Useful supporting** | It independently substantiates full realized-cost accounting and the stopping rule; it is not the central novelty (main §§5.3, 7.1, pp. 6–8). |
| Q7. Role of M4 runtime | **Useful supporting** | It tests a frozen complete-cost continuation endpoint and exposes its limitation against fixed speculation; it is not evidence of a better controller (main §7.3/Table 3, pp. 8–9). |
| Q8. Exact overstated claims | **NONE FOUND** | The prominent claims are repeatedly bounded to tested paths, comparator types, and post-prefill cost. The title's breadth and labels that can be skimmed as direct-ID “exact” are presentation risks identified above, not demonstrably false assertions (main pp. 1–10). |
