Artifact-only review.
Sources consulted:
  - manuscript-v0.8.2.pdf
  - appendix-v0.8.2.pdf

No README, handover, source files, repository evidence, prior reviews,
Git history, PR descriptions, experiment logs, or web searches were used.

## 1. Paper summary

This paper studies why seemingly favorable components of speculative decoding need not produce an exact, faster integrated decoder on four consumer systems. It distinguishes historical comparisons of token arrays reconstructed from CLI text from newer direct generated-token-ID comparisons, and treats failed equality as a gate that blocks a workload-wide performance claim. Two separately frozen HumanEval30 qualification studies compare batched and serialized paths: RTX improves from 75/90 to 90/90 direct-ID-equal pairs, whereas B570 improves from 60/90 to 78/90 and stays blocked. An outcome-informed B570 discovery set motivates a target-only micro-batch-one predictor. The authors report freezing that predictor and 24 reserved task IDs before reserved inference, committing 72 complete predicted ID sequences before live serialized outcomes, and matching all 72. Four reserved tasks retain predictable divergences from the reference; thus the observation supports sufficiency of this target execution partition on the tested stack, not a unique numerical cause. On a separate 358H setup, both integrated draft placements are exact and slower than target-only, despite an isolated NPU throughput advantage; a timed synchronous call combines prefix replay and proposal. A proposed follow-up fails qualification and has no performance endpoint. Finally, a held-out M4 continuation guard is exact and faster than target-only, but a fixed speculative policy is faster in a post-study paired comparison. The hardware campaigns, their estimators, comparators, sessions, and runtime configurations differ, limiting cross-platform and causal inferences. (Manuscript pp. 1–10; appendix pp. 1, 5–6.)

## 2. Central thesis

Speculative decoding should qualify the actual execution path against a specified output contract before treating its latency as an admissible gain. Local batching or draft throughput must then be reconciled with complete, stateful post-prefill cost. The claimed mechanisms and runtime results are deliberately configuration-specific. (Manuscript §§2, 5–7, pp. 2, 5–9.)

## 3. Top contributions, ranked

1. The frozen B570 target-partition prediction on reserved tasks, including exact prediction of reference-divergent complete sequences. (Manuscript §5.2, p. 5; appendix §J, p. 6.)
2. Prospective direct-ID path qualification on RTX and B570 with a uniform within-study 90/90 gate and explicit separation from historical timing. (Manuscript §5.1, p. 5; appendix §I, pp. 5–6.)
3. The 358H integrated cost measurement, which records committed output and complete target-side work rather than substituting isolated draft throughput or accepted draft counts. (Manuscript §5.3 and Fig. 4, pp. 6, 8; appendix §D, p. 1.)

## 4. Single strongest contribution

The B570 prediction is the most distinctive contribution. It turns an observed mismatch into a prospective, exact sequence prediction: target-only execution under `nubatch=1` matches 36/36 outcome-exposed discovery trajectories, and the frozen predictor subsequently matches 72/72 reserved serialized trajectories, including the four prompts with a repeat-stable reference divergence. That is more informative than predicting equality on prompts where both paths already match the reference. The discovery/validation split, pre-outcome commitment, all-or-nothing endpoint, and published divergence locations make the test nontrivial and falsifiable. Its evidential limit is equally important: the PDF reports the commitment and independent validation but does not print the 72 full sequences or the commitment digest, and the result isolates a sufficient partition on one configuration rather than identifying a kernel or uniquely proving causation. (Manuscript §§3.1, 5.2, pp. 3, 5; appendix §J, p. 6.)

## 5. Single strongest empirical result

The frozen target-only B570 predictor matches **72/72 complete generated-token-ID sequences** on 24 reserved HumanEval prompts with three repetitions each. It also predicts 24/24 prompt equality classifications and 12/12 first-divergence indices among the four reference-divergent prompts; reference equality itself remains only 60/72. The effective diversity is 24 prompts, and the especially diagnostic divergence pattern spans four prompts, not 72 independent tasks. (Manuscript §5.2, p. 5; appendix §J, p. 6.)

## 6. Strengths

1. Explicit output contract and honest comparator taxonomy: historical re-tokenized text is not silently upgraded to generated-ID evidence. (Manuscript §§2.1–2.2, p. 2; appendix §B, p. 1.)
2. Discovery is identified as outcome-exposed; the reserved B570 endpoint, predictor, task rule, and chronology are specified before reported live outcomes. (Manuscript §3.1, p. 3; appendix §J, p. 6.)
3. Negative and blocked results remain visible, including B570's precise but inadmissible slowdown and the failed 358H intervention gate. (Manuscript §§4.2, 7.1, pp. 4–5, 7.)
4. Prompt-level analysis respects repeated measurements as within-prompt observations, and the paper distinguishes arithmetic total-time ratios from geometric means of prompt speedups. (Manuscript §§2.3, 3.2, 5.3, pp. 2–3, 6; appendix §§B, D, pp. 1–2.)
5. The M4 runtime study uses disjoint calibration, qualification, and held-out splits, compares direct IDs, and candidly reports that the added guard loses to fixed speculation. (Manuscript §7.3 and Table 3, pp. 8–9; appendix §H, p. 5.)

## 7. Weaknesses

1. **MAJOR — scope/significance:** The strongest prospective mechanism is one B570/Vulkan configuration, one Qwen pair, one greedy width, and 24 reserved HumanEval tasks. There is no second-backend transfer or intervention that changes the partition and restores the original reference while preserving all else. The paper appropriately limits its claim, but this constrains how broadly the result advances a systems method. (Manuscript §§5.2, 9, pp. 5, 10.)
2. **MODERATE — missing evidence:** The PDFs specify 72/72 and list reserved IDs and four divergence locations, but do not expose the complete prediction/outcome arrays, the actual commitment digest, or the audited exposure inventory. The reported validator and chronology are credible procedural evidence, yet an artifact-only reader cannot independently verify the exact sequence match or absence of recorded leakage. (Appendix §J, p. 6.)
3. **MODERATE — validity:** Historical M4/RTX/B570 timing comparisons use re-tokenized parsed output, sometimes with prompt text included or normalized. They cannot establish the direct-ID contract used to motivate path admissibility. This is disclosed, but it weakens the performance evidence relative to the paper's central strict-output premise. (Manuscript §§2.1, 4, 9, pp. 2, 4–5, 10; appendix §B, p. 1.)
4. **MODERATE — validity/scope:** The 358H NPU replay and proposal are inseparable within one synchronous timed call; the isolated throughput comparison uses a different boundary. The evidence supports a costly tested interface, not a quantified replay-only penalty, a causal benefit of persistence, or hardware incapability. The attempted intervention stopped at qualification. (Manuscript §§5.3, 7.1, pp. 6–8; appendix §D, p. 1.)
5. **MODERATE — missing comparison:** M4 Guard is evaluated against target-only as its primary endpoint but is slower than Always-Spec in a paired post-study analysis. The 1.3114× primary gain therefore shows a functioning exact policy, not value added by the guard; no serving controller or transfer comparison remedies that gap. (Manuscript §7.3, Table 3, p. 9; appendix §H, p. 5.)

## 8. Claim–evidence audit

| Claim | Rating | Evidence and boundary |
|---|---|---|
| A. Execution-path qualification | **SUPPORTED WITH CAVEAT** | The contract, explicit gate, blocked cases, and direct-ID follow-ups implement the claimed discipline. Historical campaign qualification uses parsed/re-tokenized text, a weaker comparator, and no finite prompt test certifies a path generally. Manuscript §§2.1–2.2, 4, pp. 2, 4–5; appendix §§B, I, pp. 1, 5–6. |
| B. RTX direct-ID | **WELL SUPPORTED** | Frozen common HumanEval30 protocol, 75/90 batched versus 90/90 serialized, all 30 prompts repeat-stable; only serialized meets the specified gate. This is qualification, not fresh timing or historical certification. Manuscript §5.1/Fig. 3, pp. 5, 7; appendix §I/Table A5, pp. 5–6. |
| C. B570 direct-ID | **WELL SUPPORTED** | In the separately frozen protocol, fast 60/90 and serialized 78/90, both below the gate; sidecar endpoint, launch deviation, and comparator are described. The counts cannot be directly compared with older text-path 45/90 and 60/90. Manuscript §5.1/Fig. 3, pp. 5, 7; appendix §I/Table A5, p. 6. |
| D. B570 target-partition mechanism | **SUPPORTED WITH CAVEAT** | Target-only micro-batch one reproduces 36/36 exposed discovery and predicts reserved trajectories; the controls isolate a sufficient target partition. They neither run H2 after H1 passes nor identify a unique kernel or prove universal causality. Manuscript §5.2, p. 5; appendix §J, p. 6. |
| E. 72/72 held-out prediction | **SUPPORTED WITH CAVEAT** | The precise endpoint, freeze order, deterministic reserved rule, 24 IDs, four divergence tokens/indices, and validator count are reported. Full ID arrays, digest value, and audit records are absent from these PDFs; 72 sequences are repeated observations on 24 prompts. Manuscript §§3.1, 5.2, pp. 3, 5; appendix §J, p. 6. |
| F. 358H realized-cost finding | **SUPPORTED WITH CAVEAT** | Both direct-ID exact paths are slower (CPU 0.734×, NPU 0.352×); full-region accounting reports 87.34% target-side CPU time and 58.35% NPU replay-plus-proposal call time. Replay-only and proposal-only costs cannot be separated, and persistent-state performance was never measured. Manuscript §§4.2, 5.3, 7.1/Fig. 4, pp. 5–8; appendix §D, p. 1. |
| G. M4 runtime | **SUPPORTED WITH CAVEAT** | On 60 held-out prompts, Guard is 1.3114× versus target-only with 180/180 direct-ID agreement; fixed speculation is 1.3469× and the paired post-study Guard/Always latency ratio is 1.0271. The freeze-hash defect was recovered according to the appendix, but the PDF alone does not expose its archive. The incremental benefit of control is unsupported. Manuscript §7.3/Table 3, p. 9; appendix §H, p. 5. |

## 9. Audit of the 72/72 claim

| Question | Judgment | Reason |
|---|---|---|
| Is the evidence visible in the PDFs? | **PARTIAL** | IDs, counts, chronology, endpoint, and the four divergence token pairs are visible; full sequences, actual hashes, and archived validators are not. Appendix §J, p. 6. |
| Are predictions complete generated-token-ID sequences? | **YES** | The specified endpoint is 128 committed IDs or earlier inclusive EOG, and all 72 complete arrays are reported committed and compared. This is a reported property, not arrays printed in the PDF. Appendix §§I–J, p. 6. |
| Were predictions frozen before live outcomes? | **YES** | The PDF explicitly says all 72 predictions and their digest were committed before the first live serialized outcome, with no edits or selective reruns. Artifact-only inspection cannot independently timestamp the commitment. Appendix §J, p. 6. |
| Was validation reserved separately from discovery? | **PARTIAL** | Twelve discovery prompts were exposed, while a deterministic rule selected 24 reserved IDs after excluding 31 tasks with any B570 association in 8,706 audited records. The PDF properly calls this “no known exposure,” not proof against unrecorded exposure. Manuscript §3.1, p. 3; appendix §J, p. 6. |
| Was the endpoint falsifiable? | **YES** | Success required every complete sequence to match, with no partial threshold; the divergent first-token locations provide an additional check. Appendix §J, p. 6. |
| Does it show sufficiency rather than unique causality? | **YES** | H1 passes without running H2; the authors explicitly restrict the inference to a sufficient partition on the tested stack and disclaim a unique kernel or universal cause. Manuscript §5.2, p. 5; appendix §J, p. 6. |

## 10. Separation of equality and validation evidence

**MOSTLY CLEAR.** Section 2.1 (manuscript p. 2), Table 1/2 captions (p. 4), Section 4 and Figure 1 (pp. 4–5), Section 5.1/Figure 3 (pp. 5, 7), and appendix §§B, I (pp. 1, 5–6) repeatedly distinguish historical parsed-text equality from fresh generated-ID qualification. Section 5.2 and appendix §J (manuscript p. 5; appendix p. 6) identify a *third* endpoint: prospective prediction of a serialized output trajectory, which may itself differ from the reference. The repeated labels “qualified” and “exact” in the historical inventory/Table A4 could still be misread if skimmed without their captions; a three-column comparator/endpoint/evidence-class key would reduce that risk. Fresh study counts never certify older speedups.

## 11. Actual population and exclusions

The study population is sequential post-prefill greedy decoding, 128-token cap, mostly one Qwen3-8B Q8 0 target and Qwen3-0.6B Q8 0 draft family, on the listed runtime/backend/model placements. The historical M4 representative sample is 24 Spec-Bench prompts (four per six groups); HumanEval campaigns use 30 tasks and three paired repetitions. The B570 prospective mechanism uses 12 outcome-exposed discovery tasks and 24 reserved HumanEval tasks selected from 133 eligible after 31 of 164 with recorded B570 association were excluded. The M4 runtime splits 40 calibration, 16 qualification, and 60 held-out prompts balanced between HumanEval and Spec-Bench, excluding known prior M4 exposure. No functional execution/pass@k, production serving concurrency, broad model families, loading, initial prefill, universal backend population rate, or cross-platform causal ranking is measured. (Manuscript §§3, 7.3, 9, pp. 3, 8–10; appendix §§H–J, pp. 5–6.) **SIGNIFICANCE CONCERN:** narrowness is material to the generality of the contribution, although the paper usually bounds each inference accurately; it does not alone invalidate the configuration-specific results.

## 12. First-page test (title, abstract, introduction on p. 1 only)

**Three-minute impression:** an empirical systems paper about qualifying exact output paths and accounting for realized costs, anchored by an unusually concrete held-out B570 mechanism test. The title's “consumer systems” and abstract's four-platform overview could initially suggest a general consumer-hardware benchmark; the introduction promptly says the synthesis is bounded and explicitly separates historical timing from prospective direct-ID studies. The abstract visibly states **72 complete generated-token-ID predictions out of 72** and mentions the residual divergences, so the main novelty does not require hunting through the paper. The first-page introduction gives the 36/36 discovery versus 72/72 separately frozen reserved contrast and names prospective qualification and mechanism isolation as contributions. It also clearly says the M4 guard has no demonstrated incremental advantage. The presentation is dense, but it does not hide adverse outcomes. (Manuscript p. 1 only.)

## 13. Figures and tables

| Item | Necessity, readability, information, and risk |
|---|---|
| Table 1 (manuscript p. 4) | Necessary scope map. Runtime/backend and draft placement are legible; explicit historical comparator in caption helps. Could add the new studies' distinct contexts in a note to discourage direct hardware comparison. |
| Table 2 (p. 4) | Necessary headline inventory with evidence class, exact pairs, and faster prompts. The CI on a B570 inadmissible diagnostic is visibly labeled; a skimmer may still read 0.3087× as an admissible speedup, so visually separate or shade blocked rows. |
| Figure 1 (p. 5) | Useful concise display of opposite M4 regimes. Error bars and parity communicate well; captions explain distinct studies and text comparator. It must not be interpreted as a causal workload ablation, and the caption says so. |
| Figure 2 (p. 6) | Useful conceptual accounting map, but information overlaps Sections 2 and 6. Qualifying arrows and non-exhaustiveness labels prevent a misleading deterministic pipeline interpretation. Its density is high for a figure. |
| Figure 3 (p. 7) | Essential: pairs local target-forward proxy with the fresh direct-ID gate while explicitly denying a same-run cost/correctness experiment. Panel A's compressed 11-cell context ranges and glyph legend take effort to decode; appendix Table A3 provides exact values. Panel B makes the 90/90 gate clear. |
| Figure 4 (p. 8) | Essential to the 358H cost argument. The shared mean baseline and bars convey integrated loss. The isolated throughput panel and integrated time panel have different sampling units; the caption makes this clear. The NPU colored region must be read as replay **plus** proposal, never replay alone. |
| Table 3 (p. 9) | Essential for assessing Guard against both target-only and Always-Spec. Explicit post-study secondary labeling is good; latency ratios switch direction between rows, requiring careful reading despite the caption. |
| Table A1 (appendix p. 2) | Useful reproducibility detail for frozen bootstrap estimators, especially the differing endpoint order statistics; too detailed for the main paper. |
| Table A2 (appendix p. 2) | Necessary guardrail on energy-domain interpretation. Clear and compact. |
| Table A3 (appendix p. 3) | Necessary lookup for Figure 3A; confirms ranges are context spans, not uncertainty. “Qualified shared path” remains historical text-path terminology, as caption explains. |
| Table A4 (appendix p. 4) | Some redundancy with Table 2/Figure 2, but provides useful evidence-class synthesis. “Qualified; exact” may be overread as direct-ID exact without the caption; spell the comparator within the row labels. |
| Table A5 (appendix p. 6) | Essential fresh qualification counts. Simple and readable; putting this compact table in the main text would strengthen the paper's central methodological distinction. |

## 14. Related Work assessment (PDF only)

The related-work section credits foundational speculative decoding, cost accounting, heterogeneous placements, adaptive controllers, state reuse, deterministic inference, and prior consumer Apple-silicon positive/negative regimes. It explicitly acknowledges that latency-gap profitability, greedy numerical path dependence, exactness gating, and context-adaptive control are already known (manuscript §§1, 8, pp. 1, 9–10). The differentiation is reasonably narrow: prospective direct generated-ID qualification on the RTX/B570 configurations, followed by B570 reserved-sequence prediction; the 358H result measures one interface, not a new state-reuse invention. It also avoids claiming that Guard beats fixed speculation or that its offline oracle is achievable. The most vulnerable novelty wording is broad “execution-path qualification” without the B570 predictive endpoint; prior work already covers output divergence and correctness forensics. A short comparison matrix specifying *comparator*, *prospective reserved trajectory prediction*, and *measured integrated cost* against the closest cited consumer/correctness work would make the incremental advance easier to judge. No assessment of the cited works beyond their descriptions in these PDFs is implied.

## 15. Single objection against acceptance

If I were arguing against acceptance, I would say... the central prospective mechanism is convincing as a frozen case study but remains one backend and 24 reserved prompts, with only four independent reference-divergent prompt patterns. Full predictions and chronology evidence are outside the submitted PDFs. Historical speedups rest on weaker text comparators, the 358H state mechanism is a combined call rather than an isolated causal replay cost, and the new M4 guard does not improve on fixed speculation. Thus a reader seeking a transferable optimization, an independently inspectable main prediction, or a controlled multi-backend causal mechanism may find the systems advance too narrow. (Manuscript §§5–7, 9, pp. 5–10; appendix §§H–J, pp. 5–6.)

## 16. Single argument for acceptance

If I were arguing for acceptance, I would say... the paper makes a practical empirical contribution by demanding path-specific generated-ID qualification and refusing to count profitable but mismatching execution as a gain. The separate frozen RTX/B570 studies expose a meaningful serialization asymmetry; the B570 predictor commits exact complete outputs before live runs and gets 72/72, including reference-divergent tokens, which is a sharper test than a retrospective correlation. The 358H complete-round accounting and the M4 negative incremental comparison demonstrate disciplined measurement and reporting. The authors explicitly state the narrow comparator and transfer limits rather than concealing them. (Manuscript §§2, 5–7, pp. 2, 5–9; appendix §§D, I–J, pp. 1, 5–6.)

## 17. Actionable edits

**MUST FIX**

- In §5.2 and appendix §J, provide a compact, inspectable commitment record in the PDF: actual pre-outcome digest, timestamp/order identifier, prediction/outcome digest per reserved prompt (or all 72 arrays in an accompanying artifact accessible to reviewers), and a direct pointer from each digest to its endpoint convention. Present four divergent prompts as the high-information subset and distinguish 24 prompt units from 72 repetitions.
- In §5.2/§9, say in the main text that “target-partition sufficiency” is a predictive observation under a controlled harness, with no completed second intervention or unique cause; avoid any causal verb that could imply kernel identification or hardware transfer.

**SHOULD FIX**

- Move or replicate Table A5 beside Figure 3B; place “historical text comparator,” “fresh direct-ID gate,” and “reserved prediction of serialized IDs” in a small endpoint key near §§4–5.
- For Figure 4/§5.3, consistently name the NPU timed region “full-prefix reconstruction/replay plus proposal,” and make explicit that the isolated throughput result and integrated call do not identify replay's marginal cost.
- In Table 3/§7.3, foreground Always-Spec as the relevant policy comparator and present Guard/Always-Spec as post-study secondary evidence, with an explicit direction label on each latency ratio.
- In §3.2 or §9, note that CIs condition on prompts and the selected policy, and repetitions or sessions do not enlarge the prompt-level sample size; state that 72/72 is a strict finite-set endpoint, not a population confidence claim.

**OPTIONAL**

- Shorten Figure 2 or move some prose into its caption; give Figure 3A direct value/context labels if space permits.
- Add a PDF-only comparison grid against the closest cited correctness and consumer studies, using the actual prediction and comparator distinctions instead of broad novelty language.

## 18. Recommendation

**WEAK ACCEPT**

## 19. Confidence

**4/5.** The PDFs give enough methodological detail to evaluate the claimed endpoints and limits, but they do not expose the underlying archived sequences, hashes, or original timing observations for independent reconstruction.

## 20. Decision rationale (100–200 words)

The paper's best evidence is the frozen B570 reserved-set prediction: 72/72 complete serialized sequences, with four reference-divergent prompt patterns predicted by a target-only partition control. The prospective RTX/B570 direct-ID gates are also valuable because they keep path qualification separate from historical text-path timing. I credit the careful negative reporting: B570 remains blocked, 358H is slower despite isolated draft promise, the attempted 358H runtime change never reaches formal timing, and M4 Guard loses to fixed speculation in the paired secondary comparison. The methodology uses prompt as the sampling unit and distinguishes estimators and timing boundaries. My enthusiasm is limited by the one-configuration mechanism, the small number of independent divergent prompts, lack of a completed transfer or corrective intervention, and the inability to inspect full predicted/observed arrays and commitment evidence in these PDFs. The 358H combined replay/proposal region also prevents a replay-only causal estimate. I would accept the bounded measurement and prediction contribution if the presentation foregrounds those evidential limits and makes the held-out commitment more directly inspectable. (Manuscript §§3, 5–9, pp. 3, 5–10; appendix §§D, H–J, pp. 1, 5–6.)

## Special Questions

| Question | Answer | Basis |
|---|---|---|
| Q1. Main identity | **E — coherent B+C+D** | Qualification gates, frozen B570 predictive mechanism, and realized 358H costs are connected as bounded stages, while each has a distinct endpoint. Manuscript §§5–7, pp. 5–9. |
| Q2. More than a benchmark of own system? | **CLEARLY YES** | The pre-outcome B570 output prediction and direct-ID qualification tests are mechanisms and methodological endpoints, not just timing enumeration. Manuscript §5, pp. 5–7. |
| Q3. Importance of frozen 72/72? | **YES** | It is the strongest test of the specific target-partition explanation, especially the four non-reference trajectories, though repeats are correlated. Appendix §J, p. 6. |
| Q4. Would second-backend transfer change recommendation? | **MAYBE** | A separately frozen replication with the same endpoint on another backend could move the paper beyond a single configuration and materially strengthen significance; failure would appropriately narrow it. Current weak acceptance does not depend on it. Manuscript §9, p. 10. |
| Q5. Does lack of transfer invalidate current claims? | **NO** | The claims, read strictly, concern the tested partitions and interfaces. Manuscript §§5.2, 9, pp. 5, 10. |
| Q6. 358H role | **Useful supporting** | It substantiates the complete-cost boundary but does not prove a persistence fix or a replay-only causal penalty. Manuscript §§5.3, 7.1, pp. 6–8. |
| Q7. M4 role | **Useful supporting** | It demonstrates prospective exact runtime evaluation and an honest negative incremental policy result; it is not a new guard win. Manuscript §7.3, p. 9. |
| Q8. Exact overstated claims | **NONE FOUND in the main bounded conclusions.** | The phrase “isolates a sufficient target execution partition” (abstract/§5.2, manuscript pp. 1, 5) is defensible only as finite-set predictive sufficiency; the paper explicitly denies a unique kernel or universal rule. “Consumes an isolated draft-device advantage” (conclusion, p. 10) is supported for the combined tested interface, not a separated replay cost. These formulations merit tighter proximity to their caveats but are not, as written, broad transfer claims. |
