Artifact-only review.
Sources consulted:
  - manuscript-v0.8.3.pdf
  - appendix-v0.8.3.pdf

No README, handover, source files, repository evidence, prior reviews, Git history, PR descriptions, experiment logs, or web searches were used.

## 1. Paper summary

This paper studies when speculative decoding on consumer systems preserves the intended greedy output and when favorable local measurements survive complete execution. It distinguishes historical agreement of re-tokenized CLI text from fresh comparisons of captured generated token IDs and from a separate frozen predictor of live trajectories. Fresh HumanEval30 qualification finds that serialization raises RTX equality from 75/90 to 90/90 pairs, while B570 rises from 60/90 to 78/90 and remains blocked. On B570, an outcome-exposed discovery set selects a target-only micro-batch-one hypothesis; its predictions are fixed before reserved live runs and match all 72 complete sequences from 24 prompts and three repetitions. Four reference-divergent prompts supply the most informative portion of this result. The authors correctly frame it as target-partition sufficiency on one tested path, rather than identification of a unique numerical operation.

Other case studies show that integrated costs can defeat isolated opportunity. The direct-ID-qualified 358H CPU and NPU draft paths are slower than target-only; full-prefix replay and proposal share a costly NPU interface call. Historical M4 studies show opposite profitability regimes under text-derived agreement, but in separate sessions. A later M4 direct-ID-qualified Guard beats target-only on held-out prompts yet loses a paired secondary comparison with fixed speculation. The work's contribution is a disciplined, bounded evaluation method, a prospective trajectory prediction, and measured cost anatomy, not a broadly faster speculative decoder. [Manuscript pp. 1–10; Appendix pp. 1–8]

## 2. Central thesis

An apparently cheap draft or target-forward step says little about whether the complete execution path preserves output or improves decode latency. For a tested path, qualify generated IDs first, use reserved trajectory prediction to diagnose a blocked path, and charge complete realized costs before making a performance claim. [Manuscript pp. 1–2, 5–8]

## 3. Top contributions, ranked

1. Prospectively frozen B570 target-only UB1 prediction of **72/72 complete reserved live generated-ID sequences**, including 12/12 first-divergence positions on four reference-divergent prompts. [Manuscript p. 6, §5.2; Appendix pp. 6–8, §J]
2. Fresh path-scoped direct-ID qualification: RTX batched 75/90 versus serialized 90/90; B570 fast 60/90 versus serialized 78/90, under explicit 90/90 gates and with no claim of matching fresh latency. [Manuscript pp. 5–6, §5.1, Fig. 3B; Appendix pp. 5–6, §I]
3. Direct-ID-qualified 358H complete-loop accounting showing how an isolated NPU draft advantage disappears at its state interface, with separate CPU target-side dominance. [Manuscript pp. 4–7, Table 2, Fig. 4; Appendix pp. 1–2, §D]

## 4. Strongest contribution

The B570 prediction is the best reason to accept. Reproducing a mismatch after viewing it would be weak; here the paper describes exposed discovery separately, excludes recorded B570-associated tasks, freezes the H1 rule and reserved IDs, commits 72 complete predictions before any reserved serialized outcome, and reports all 72 comparisons rather than choosing only favorable prompts. The 20 reference-equal prompts are less discriminating, but the four divergent prompts make the result substantially harder to explain as mere agreement with the ordinary reference: their first different IDs and indices are predicted, with complete trajectories equal thereafter. Appendix §J gives a content digest, relative chronology with a 91.37-second prediction-to-live interval, IDs, per-prompt hashes, and divergence tokens. This supports a path-level predictive mechanism, without isolating a floating-point kernel or proving transfer. The PDF itself does not include the complete arrays or underlying timestamped archive, so the artifact-only evidence is a detailed, checkable report of the commitment rather than independent replay. [Manuscript pp. 3, 6, §5.2; Appendix pp. 6–8, §J, Tables A6–A7]

## 5. Strongest empirical result

**72/72** complete generated-token-ID predictions matched B570 live serialized output across **24 reserved HumanEval prompts × 3 repetitions**, while the frozen UB128 reference matched only **60/72** live sequences. All 12 divergent repetition pairs across four prompts had their first-divergence index predicted; every reserved live sequence has length 128 in the visible ledger. These are 24 repeat-stable prompt trajectories, not 72 independent prompts. [Manuscript p. 6, §5.2; Appendix pp. 6–8, §J, Tables A6–A7]

## 6. Strengths

1. The H/Q/P output-evidence taxonomy prevents historical re-tokenized text counts from quietly becoming direct-ID certification. [Manuscript p. 2, §2.1]
2. The B570 frozen prediction has a separate discovery set, deterministic reserved selection, pre-live commitment, informative divergent cases, and a visible per-prompt ledger. [Manuscript pp. 3, 6; Appendix pp. 6–8]
3. Negative and stopped results are reported honestly: B570 timing remains diagnostic; the 358H intervention fails qualification; M4 Guard loses to fixed speculation. [Manuscript pp. 4–5, 8–10]
4. The 358H accounting charges prefix reconstruction inside the synchronous draft call and complete target-side round work, avoiding a misleading isolated-draft inference. [Manuscript pp. 2, 7; Appendix pp. 1–2]
5. Separate estimators, prompt-level bootstrap units, timer boundaries, energy domains, and post-study analysis status are made explicit. [Manuscript pp. 3–4, 8–10; Appendix pp. 1–2, 5]

## 7. Weaknesses

1. **MAJOR — significance/scope:** The distinctive predictor is validated on one B570 Vulkan/model/runtime path and one HumanEval slice. No second backend or model tests whether target-partition sufficiency is a reusable diagnostic. All three repetitions are stable and 20/24 reserved prompts agree with the reference, leaving four highly informative divergent trajectories. [Manuscript pp. 6, 10; Appendix pp. 6–8]
2. **MODERATE — missing evidence:** The anonymous PDFs provide prediction-file digest, chronology, first-divergence examples, and per-prompt short hashes, but not the 72 complete arrays or primary audit records. Thus this review cannot independently verify temporal ordering, exclusion completeness, or full equality from the PDFs alone. This is a transparency limit of the artifact, not evidence that the reported validation failed. [Appendix pp. 6–8, §J]
3. **MODERATE — validity/scope:** Different front ends, contexts, references, versions, quantization, and sessions separate many cases. The descriptive M4 contrast cannot establish a workload-only cause, and fresh direct-ID qualification has no matching latency endpoint. The paper largely observes these restrictions, but its broad framing can invite overgeneralization. [Manuscript pp. 3–6, 10]
4. **MODERATE — clarity/significance:** The manuscript spans historical hardware campaigns, RTX/B570 fresh qualification, a B570 predictor, 358H integration, a stopped 358H intervention, and M4 Guard. The strong prediction thread competes for space with weaker, heterogeneous timing cases; the main text could more directly quantify the four divergent reserved prompts and the 24 versus 72 effective granularity. [Manuscript pp. 1, 3–9]
5. **MINOR — missing comparison:** No experimentally qualified state-persistent 358H alternative isolates replay cost, and Guard has no demonstrated gain over Always-Spec or transfer. These are limits to the intervention claims, which the paper mostly states accurately. [Manuscript pp. 7–10; Appendix p. 5]

## 8. Claim–evidence audit

| Claim | Judgment | Evidence and boundary |
|---|---|---|
| A. Execution-path qualification is required for the specified exact-output contract | **WELL SUPPORTED** | Contract and H/Q/P classes in manuscript p. 2, §2.1; actual path gates in pp. 5–6, §5.1. It is a methodological rule conditional on strict greedy ID equality, not a universal deployment objective. |
| B. RTX direct-ID serialization qualifies where batching fails | **WELL SUPPORTED** | 75/90 batched and 90/90 serialized under the frozen 90/90 gate; manuscript pp. 5–6, Fig. 3B; Appendix pp. 5–6, §I, Table A5. No fresh matched latency. |
| C. B570 direct-ID fast and serialized paths remain blocked | **WELL SUPPORTED** | 60/90 and 78/90 in the fresh study, plus separate reserved reference/live 60/72; manuscript pp. 5–6; Appendix pp. 6–7, Tables A5–A6. Historical 45/90 and 60/90 are text-path endpoints and must stay separate. |
| D. B570 target partition suffices to predict tested serialized output | **SUPPORTED WITH CAVEAT** | Discovery 36/36, reserved predictor/live 72/72, four reference-divergent trajectories; manuscript p. 6, §5.2; Appendix pp. 6–8, §J. The evidence establishes tested predictive sufficiency, not a unique cause, kernel, general UB1 law, or cross-stack transfer. |
| E. Frozen held-out prediction achieved 72/72 complete sequences | **SUPPORTED WITH CAVEAT** | Explicit pre-live commitment, digest and relative timestamps, all-prompt ledger; manuscript pp. 3, 6; Appendix pp. 6–8. PDF lacks raw arrays and independently verifiable chronology; 72 repetitions comprise 24 repeat-stable prompts. |
| F. 358H realized cost defeats isolated NPU draft advantage | **WELL SUPPORTED** | Direct-ID 90/90 per path, slower complete loops, Figure 4 timings: NPU 27.54 s versus 9.58 s arithmetic baseline, 58.35% combined replay/proposal; CPU 13.25 s and 87.34% target side. Manuscript pp. 4–7; Appendix pp. 1–2. Replay-only and hypothetical persistence benefits remain unidentified. |
| G. M4 Guard is qualified and faster than target-only, but adds no measured benefit over fixed speculation | **WELL SUPPORTED** | 180/180 direct-ID matches per speculative condition; Target/Guard 1.3114, Target/Always-Spec 1.3469; post-study paired Guard/Always-Spec latency 1.0271 [1.0130, 1.0436]. Manuscript pp. 8–9, §7.2–7.3, Table 3; Appendix p. 5, §H. Secondary contrast is explicitly labeled post-study. |

## 9. Audit of the 72/72 prediction

| Criterion | Assessment | Reason |
|---|---|---|
| Visible in paper | **YES** | Abstract and introduction highlight it; manuscript p. 6 gives protocol/result and Appendix pp. 6–8 give Tables A6–A7 and four divergent examples. |
| Complete generated-token-ID sequences | **PARTIAL** | Endpoint expressly compares all committed generated IDs, lengths, and earlier EOG, without prompt IDs or dropped mismatches. All visible reserved lengths are 128; hashes and equality counts are shown, but the full arrays are not printed in the PDFs. [Appendix pp. 6–8] |
| Frozen before live outcomes | **PARTIAL** | Recorded chronology says predictions finalized T0+1722.38 s and first live outcome T0+1813.75 s, a 91.37-second gap; digest binds file contents. Artifact-only review cannot inspect the underlying dated commitment record. [Appendix p. 7] |
| Separate reserved from discovery | **YES** | Twelve explicitly outcome-exposed discovery IDs, conservative exclusion of 31/164 B570-associated tasks, and 24 deterministic reserved IDs from 133 eligible tasks are described. Audit scope is qualified as “no known exposure.” [Manuscript p. 3; Appendix p. 6] |
| Falsifiable | **YES** | One failed full sequence would fail the 72/72 endpoint; 24 task IDs, per-prompt digests, divergence IDs/positions, file digest, and validator description make a concrete refutation possible given the archived arrays. [Appendix pp. 6–8] |
| Avoids unique-cause leap | **YES** | The authors explicitly deny identification of a specific numerical operation/kernel and avoid a universal UB1 or shared RTX/B570 explanation. [Manuscript pp. 1, 6, 10; Appendix p. 6] |

The repetition-wise perfect score is impressive as a frozen trajectory match, but its independent prompt support is 24 and its most discriminating reference-divergent support is four prompts. Repeating a stable trajectory three times tests stability, not 72 distinct failure locations. [Appendix pp. 6–8]

## 10. Historical versus fresh versus predictive distinction

**VERY CLEAR.** Section 2.1 defines H (parsed text re-tokenization), Q (fresh captured generated-ID comparison to reference), and P (frozen predictor against reserved live serialized IDs). Table 2 flags historical M4/RTX/B570 rows as text-path and 358H as direct-ID; Figure 3 splits historical target-forward proxy from fresh ID qualification and says it does not certify historical timing. Section 5.2 and Appendix Tables A5–A7 distinguish the B570 78/90 fresh qualification, 60/72 separate reserved reference/live comparison, and 72/72 predictor/live result. This distinction is also in the abstract and limitations. [Manuscript pp. 1–2, 5–6, 10; Appendix pp. 5–8]

## 11. Population and exclusions

**ACCEPTABLE SCOPE LIMITATION**, with material significance cost. The work samples four independently frozen consumer configurations, one Qwen3 target family, mostly Q8 0 native models, one INT4 heterogeneous draft, greedy k = 2, one concurrent request, HumanEval30 and selected Spec-Bench subsets. The B570 predictor uses 24 deterministic reserved HumanEval tasks after 31 of 164 tasks with any recorded B570 association are excluded; “no known exposure” is explicitly bounded by the audited records. M4 Guard uses disjoint 40/16/60 calibration/qualification/held-out prompts balanced across HumanEval and Spec-Bench. The prompt bootstrap intervals do not include session or runtime-state variation, and generated code is not executed. These restrictions curtail external reach but do not invalidate the carefully stated within-path outcomes. [Manuscript pp. 3, 8–10; Appendix pp. 5–6]

## 12. First-page test

On the title, abstract, and first introduction page alone, my three-minute impression is a systems measurement paper with a real prospective diagnostic result rather than simply a four-device benchmark. The title says “execution-path qualification” and “realized costs”; the abstract immediately shows RTX 75/90→90/90, B570 60/90→78/90, and the frozen 72/72 predictor, including reference-divergent trajectories. The introduction enumerates contributions and states no unique numerical cause. Thus **generic benchmark confusion is low** and **72/72 visibility and novelty are early and clear**. The density of model, device, gate, and evidence-class terms is high; a one-sentence explanation that UB1 target-only predicts the otherwise blocked serialized trajectory would improve the non-specialist first pass. [Manuscript p. 1]

## 13. Figures and tables

| Item | Necessary / readable / informative | Redundancy or misleading risk |
|---|---|---|
| Table 1, systems (manuscript p. 3) | **Necessary**, readable, explains nonmatched configurations and endpoint scope. | A fresh-study configuration row might keep the later prospective setting distinct from historical runtimes. |
| Figure 1, M4 (p. 4) | Informative visual contrast, readable point estimates/CIs. | Could suggest workload causality until its long caption clarifies separate sessions and text-path agreement; retain the caveat. |
| Table 2, headline outcomes (p. 5) | **Necessary**, concise endpoint and class columns prevent inadmissible speed interpretations. | No material misleading issue; numbers are historical except 358H as labeled. |
| Figure 2, evaluation sequence (p. 5) | Readable. | Mostly **redundant** with §2 and §6; flow boxes do little evidentiary work and might imply a single shared intervention chain if caption missed. |
| Figure 3, proxy and qualification (p. 6) | **Necessary** for the paper's core separation; panel B makes 90/90 gate unmistakable. | Panel A mixes contexts and historical runs; tiny marks and proximity to panel B can invite a paired cost/qualification reading. Caption appropriately denies it. |
| Figure 4, 358H (p. 7) | **Necessary**, clear isolated-throughput versus realized-cost contrast and component fractions. | The arithmetic mean bar is not the prompt-GM speedup; this is explicitly labeled but the two estimators deserve prominent placement. Replay and proposal are inseparable. |
| Table 3, M4 runtime (p. 9) | **Necessary**, readable, includes unfavorable paired Guard/fixed result. | Offline oracle is hindsight, not a deployable policy; caption and prose clarify. |
| Table A1, estimator policies (Appendix p. 2) | Useful and readable for exact finite-bootstrap conventions. | No material risk. |
| Table A2, energy boundaries (p. 2) | Useful: guards against unsupported cross-system energy ranking. | Some repetition of main-text caveat is justified. |
| Table A3, proxy cells (p. 3) | Necessary to interpret all eleven marks in Figure 3A. | Contexts differ and table labels this. |
| Table A4, inventory (p. 4) | Readable synthesis of evidence classes. | Some repetition of Tables 1–2; could be compressed. |
| Table A5, fresh qualification (p. 6) | **Necessary**, provides prompt as well as pair counts and the gate. | No fresh latency endpoint, expressly labeled. |
| Table A6, B570 comparator (p. 7) | **Necessary**: 60/72 reference versus 72/72 predictor is the central contrast. | Should not be read as an estimate of independent prompt-level success probability. |
| Table A7, B570 ledger (p. 8) | **Necessary** for per-prompt visibility and four divergent cases; legible at page size. | Shows short hashes and counts, not the arrays; all 24 lengths are 128. |

## 14. Related Work

Based solely on the manuscript's descriptions and references, credit is fair. Section 8 acknowledges established slowdown and verification limits (Liu et al.; Kim et al.; Chordiya), numerical batch-shape dependence and determinism (Yuan et al.; Gond et al.; Zhang et al.), heterogeneous placement/state reuse, and adaptive policies. The authors explicitly disclaim novelty in cost/commit equations, output variation, state persistence, or the Guard policy. Their plausible differentiated contribution is the particular combination of prospective path qualification and pre-live complete-trajectory prediction on a blocked B570 execution path, plus quantified 358H interface accounting. I cannot verify prior papers' actual claims from these PDFs, so the judgment concerns the fairness of this manuscript's positioning only. Broad novelty language such as “first evidence that batching changes outputs” or “new adaptive speculative control” would be unsafe; the present text largely avoids it. [Manuscript pp. 2, 8–9, §8; references pp. 11–12]

## 15. Single strongest objection

If I were arguing against acceptance, I would say... the main novel evidence has only one platform/model/backend and 24 deterministic reserved prompts, of which just four exhibit informative reference divergence; the full arrays and timestamped freeze evidence are outside the anonymous PDFs. The remaining hardware cases are heterogeneous, historically text-derived, or negative, and the only held-out runtime policy is slower than the fixed comparator. This is a careful case study, but its general systems insight may be thinner than a top-tier conference contribution. [Manuscript pp. 3–10; Appendix pp. 6–8]

## 16. Single strongest case for acceptance

If I were arguing for acceptance, I would say... a systems paper need not produce a new speedup when it supplies a falsifiable method for deciding whether speedups are even admissible. Here the authors promote correctness gating to a measured execution-path property, keep text-derived historical results separate from direct-ID data, freeze an independent predictor before 72 reserved live trajectories, expose four exact divergent tokens/positions, and account for the full 358H stateful interface. The failed B570 gate, stopped 358H intervention, and slower Guard are reported without claim laundering. The resulting bounded diagnostic sequence is useful, novel in its prospective predictive evidence, and unusually honest about integration costs. [Manuscript pp. 1–10; Appendix pp. 5–8]

## 17. Requested changes

**MUST FIX**

- In manuscript §5.2 (p. 6) and Appendix §J/Tables A6–A7 (pp. 6–8), state adjacent to “72/72” that there are **24 repeat-stable prompt trajectories**, **four** reference-divergent prompts (12 repetitions), and 20 reference-equal prompts. The details are present but the effective granularity needs to be unavoidable at the headline claim.
- In manuscript §3.1 and Appendix §J (pp. 3, 6–7), state exactly which commitment evidence is reviewer-verifiable in the submission and how the full prediction arrays and chronological record can be audited under anonymity. Preserve the current digest and chronology; do not imply the PDF itself contains raw sequences or proves timestamp order from a hash alone.

**SHOULD FIX**

- In manuscript §5.1/Figure 3 and Table 1 (pp. 3, 5–6), give a compact row or note for the fresh RTX/B570 configurations and reiterate that no matched fresh latency was collected. This helps prevent readers from pairing historical V₂ proxy cells with the prospective ID counts.
- In manuscript §7.3/Table 3 (p. 9), keep the post-study status of Guard/Always-Spec in the row label and perhaps add the latency direction in the heading; the present caption is good but compact rows are often read alone.
- In manuscript §5.3/Figure 4 (p. 7), emphasize that 58.35% is **combined replay/reconstruction plus proposal**, while 87.34% CPU target work is complete target-side work. No replay-only savings have been measured.

**OPTIONAL**

- Replace or shrink Figure 2 (p. 5) to make room for a compact B570 freeze/validation graphic or a sharper explanatory sentence about why four predicted divergences are informative.
- Put a short caveat beside Figure 1 (p. 4) that the two M4 studies differ in session as well as workload, despite sharing hardware.

## 18. Recommendation

**ACCEPT.**

## 19. Confidence

**4/5.** The protocol and numerical endpoints are described in substantial PDF detail, but an artifact-only assessment cannot replay the archived arrays, audit records, or external literature. [Appendix pp. 5–8]

## 20. Decision rationale (100–200 words)

I recommend acceptance for a bounded systems contribution, with the B570 frozen prediction carrying the novelty. The result goes beyond observing that numerical paths diverge: a target-only execution partition, selected on exposed discovery prompts, predicts 72/72 complete reserved serialized sequences before their live outcomes, including four reference-divergent prompt trajectories and their first divergent token positions. The fresh RTX/B570 direct-ID gates and the 358H complete-loop timing make the broader evaluation discipline concrete. Rigor benefits from explicit evidence classes, prompt-level estimators, visible failed gates, and an unfavorable Guard comparison. Significance is limited: one model family, narrow paths, no second-backend transfer, no fresh speed endpoint for the qualification runs, and PDF-only audit access to the commitment. Clarity is generally strong because the authors repeatedly delimit text-derived equality, direct-ID qualification, predictive sufficiency, and realized cost. These limitations call for tighter presentation and auditable artifact access, but the prospective diagnostic and honest negative evidence meet an acceptance bar for a measurement-focused systems paper. [Manuscript pp. 1–10; Appendix pp. 5–8]

## Special questions

| Question | Answer | Basis |
|---|---|---|
| Q1. Best characterization | **E — coherent B+C+D** | Execution-path qualification is the organizing method; frozen B570 prediction is the distinctive mechanism result; 358H supplies realized-cost anatomy. [Manuscript pp. 1, 5–7] |
| Q2. More than “benchmark your own system”? | **CLEARLY YES** | A frozen pre-live trajectory prediction, strict output gate, and complete round-accounting test hypotheses that a speed table alone does not. [Manuscript pp. 2, 6–7; Appendix pp. 6–8] |
| Q3. Frozen 72/72 important to publication? | **YES** | This is the clearest prospective, falsifiable contribution and the best distinction from prior descriptive path observations. [Manuscript pp. 1, 6, 9; Appendix pp. 6–8] |
| Q4. Would second-backend transfer change recommendation? | **NO** | It would increase confidence and significance, perhaps strengthening the score, but bounded B570 predictive sufficiency plus qualification/cost discipline already support acceptance. |
| Q5. Does lack of transfer invalidate current claims? | **NO** | Claims explicitly concern the tested stack and disclaim universal UB1, kernel, or shared-platform cause. [Manuscript pp. 6, 10] |
| Q6. 358H? | **USEFUL SUPPORTING** | Direct-ID-qualified negative integration and timed combined interface illustrate the realized-cost boundary; no persistent-state performance intervention is claimed. [Manuscript pp. 7–8] |
| Q7. M4 runtime? | **USEFUL SUPPORTING** | A qualified held-out control is valuable as a test of disciplined runtime claims precisely because fixed speculation wins; its policy itself is not the novelty. [Manuscript pp. 8–9] |
| Q8. Exact overstated claim examples | **NONE FOUND** | The tempting overclaims—unique B570 cause, retrospective strict-ID certification of historical timings, replay-only savings, Guard gain over fixed speculation—are explicitly disclaimed. The title's broad “consumer systems” is acceptable as a collection of bounded cases, though §9 must remain prominent. [Manuscript pp. 1–2, 6–10] |
