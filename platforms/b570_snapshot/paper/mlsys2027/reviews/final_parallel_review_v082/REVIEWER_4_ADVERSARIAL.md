Artifact-only review.
Sources consulted:
  - manuscript-v0.8.2.pdf
  - appendix-v0.8.2.pdf

No README, handover, source files, repository evidence, prior reviews,
Git history, PR descriptions, experiment logs, or web searches were used.

## 1. Paper summary

This paper studies why apparently favorable components of speculative decoding do not necessarily produce exact, faster post-prefill decoding on four consumer systems. It insists on qualifying the generated output against a matched target-only reference before treating timing as an admissible optimization result, and distinguishes isolated target-forward and draft measurements from complete round cost. Historical M4 campaigns show a slowdown on 24 representative prompts (0.842×) and a gain on a separate HumanEval30 campaign (1.387×), though those historical comparisons reconstruct IDs from parsed text and differ in session conditions. New direct generated-ID qualification studies on HumanEval30 find that serialization changes RTX agreement from 75/90 to 90/90 and B570 agreement from 60/90 to 78/90, leaving B570 blocked. A subsequent B570 study selects a target micro-batch-one hypothesis on exposed discovery prompts, freezes it and the reserved predictions, then matches 72/72 complete live speculative token sequences on 24 reserved prompts, including 12 divergent pairs. A 358H CPU/NPU comparison shows that NPU isolated draft throughput does not yield integrated profit in a full-prefix replay interface; its proposed follow-up cannot pass qualification. Finally, an M4 continuation guard is direct-ID exact and faster than target-only on 60 held-out prompts, but a paired secondary analysis finds it slower than fixed speculation. The work is candid about these boundaries and presents a sequence of qualification, mechanism isolation, and complete-cost measurement. (Manuscript pp. 1–10; appendix §§B, D, H–J.)

## 2. Central thesis

Speculative-decoding profitability must be evaluated on an output-qualified execution path with complete realized costs. The tested B570 residual divergence can be predicted from a target execution partition, while the tested 358H NPU draft advantage disappears at its stateful interface. These are bounded mechanisms, not a universal hardware diagnosis. (Manuscript §§2, 5–6.)

## 3. Top contributions, ranked

1. **Prospective B570 trajectory prediction:** after exposed discovery and a recorded freeze, target-only micro-batch-one execution predicts all 72 complete generated-ID sequences of the reserved serialized speculative runs, including divergence locations. (Manuscript §5.2; appendix §J.)
2. **Fresh path qualification:** two direct-ID studies separate RTX serialization's 90/90 pass from B570 serialization's still-blocked 78/90, without laundering historical text-based timing into direct-ID performance evidence. (Manuscript §5.1; appendix §I.)
3. **Integrated cost diagnosis:** 358H round records reconcile committed progress and measured CPU/NPU cost regions, showing a negative NPU result despite favorable isolated drafting. (Manuscript §5.3, Fig. 4; appendix §D.)

## 4. Single strongest contribution

The B570 reserved prediction is the strongest contribution. It matters because a speculative trajectory that diverges from its nominal target-only reference might otherwise be blamed on live drafting, correction logic, or a generic device error; a target-only path predicting the actual speculative sequence gives a more actionable localization. The result is nontrivial because the frozen predictor matches *complete* token-ID sequences and the 12 divergent repetition pairs' first-divergence indices, rather than only counting whether a prompt passed. The discovery set is outcome-exposed, but the 24-task, 72-sequence reserved endpoint and predictions were frozen before live serialized inference, and the appendix gives IDs and four divergence examples. This supports **sufficiency for the tested partition and configuration**, not identification of a unique kernel or causal prevalence beyond the tested prompts. (Manuscript pp. 3, 5–6, §5.2; appendix §J, p. 6.)

## 5. Single strongest empirical result

**72/72 complete generated-token-ID sequences** predicted by target-only micro-batch-one execution on 24 reserved B570 HumanEval prompts × three repetitions, including **12/12** first-divergence-index matches among divergent pairs; only **60/72** of those live outputs agree with the reference, so the path remains blocked. This is a trajectory prediction, not an admissible speedup or a proof of unique causation. (Manuscript §5.2, p. 5; appendix §J, p. 6.)

## 6. Strengths

1. The strict output contract, historical text comparator, fresh direct-ID comparator, and blocked timing are repeatedly and explicitly separated. (Manuscript §§2.1–2.2, 4–5; appendix §§B, I.)
2. The B570 follow-up distinguishes exposed hypothesis selection from reserved prediction; it reports the failed reference-equality endpoint as well as successful trajectory prediction. (Manuscript §5.2; appendix §J.)
3. The 358H accounting includes correction/bonus output in committed progress and complete target-side work, avoiding a misleading accepted-draft proxy. (Manuscript §5.3; appendix §D.)
4. The paper reports negative and stopped interventions, including B570 qualification failure, the unprofitable 358H paths, and the Guard disadvantage against fixed speculation. (Manuscript §§4, 7.)
5. It gives unusually explicit estimator, sensor, provenance, and freeze exceptions instead of presenting a pooled hardware ranking. (Manuscript §§3, 9; appendix §§B–E, H–J.)

## 7. Weaknesses

1. **MAJOR — significance:** The broad qualification-and-cost prescription overlaps closely with the prior work the paper itself credits. The most distinctive predictive result is one model pair, backend/build, batch setting, and 24 reserved HumanEval prompts; no second backend validates that specific partition predictor. The paper appropriately limits the claim, but its general systems contribution may be too small for acceptance. (Manuscript §§1, 5.2, 8–9.)
2. **MODERATE — missing evidence:** The B570 target-partition result is predictive and sufficient on the observed trajectories, yet does not separate which target numerical operation, execution shape, or state transition causes divergence. The H1 versus H2 decision tree never runs H2 because H1 passes discovery. This limits mechanistic resolution, without negating the frozen prediction. (Manuscript §5.2; appendix §J.)
3. **MODERATE — missing comparison:** The 358H replay-plus-proposal region is inseparable, and no qualified persistent-state or widened-target intervention is timed. Thus the attractive hardware-level implication, how much a better state interface would recover, is unmeasured. The paper explicitly acknowledges the stop. (Manuscript §§5.3, 7.1, 9; appendix §§D, H.)
4. **MODERATE — significance:** The M4 Guard has a valid profitable target-only endpoint, but Always-Spec is faster on the same reserved prompts (paired Guard/Always-Spec latency 1.0271×, CI [1.0130, 1.0436]). The study does not establish incremental value from control; its distinct contribution is mostly implementation feasibility under a complete-cost rule. (Manuscript §7.3, Table 3.)
5. **MINOR — clarity:** Table A4 calls historical M4 and RTX entries “Qualified” and “exact” even though its caption says these mean re-tokenized-text agreement. A reader scanning its cells could mistake them for the manuscript's strict generated-ID contract. (Appendix Table A4, p. 4; manuscript §2.1.)

## 8. Claim–evidence audit

| Claim | Assessment | Ground and limit |
|---|---|---|
| A. Execution-path qualification | **WELL SUPPORTED** | Contract and gate are defined; failures block workload-global claims, and historic comparator is labeled separately. The gate certifies only the tested workload/configuration. (Manuscript §2.1, pp. 2, 5; appendix §I.) |
| B. RTX direct-ID qualification | **WELL SUPPORTED** | New 75/90 batched and 90/90 serialized sequence comparisons, stable over 30 prompts × three repetitions, with 90/90 gate and appendix protocol. No fresh speed claim follows. (Manuscript §5.1, p. 5; appendix Table A5, §I, p. 6.) |
| C. B570 direct-ID qualification | **WELL SUPPORTED** | New fast 60/90 and serialized 78/90 direct-ID comparisons; both fail the declared gate. The separate old 45/90 and 60/90 text counts are explicitly distinguished. (Manuscript §5.1, p. 5; appendix Table A5, §I, p. 6.) |
| D. B570 target-partition mechanism | **SUPPORTED WITH CAVEAT** | Target-only nubatch=1 matches 36/36 exposed discovery and 72/72 reserved serialized sequences, after reproducing its reference. This identifies a sufficient *tested* execution partition, not a unique operation or proof of causal exclusivity. (Manuscript §5.2, pp. 5–6; appendix §J, p. 6.) |
| E. 72/72 held-out prediction | **WELL SUPPORTED** | Appendix names the 24 reserved IDs, freeze/endpoint, 72 predictions committed before live outcomes, 12 divergent pairs, and independent validation. It remains a same-family, one-stack reserved validation, not population generalization. (Manuscript §5.2; appendix §J, p. 6.) |
| F. 358H realized-cost account | **SUPPORTED WITH CAVEAT** | Direct C and timed regions reconcile arithmetic aggregate ratios; CPU target side is 87.34%, NPU combined replay/proposal 58.35%. Replay versus proposal contributions and a persistence benefit cannot be separately estimated; compact diagnostic traces are not locally replayed in the PDF. (Manuscript §5.3, Fig. 4, §9; appendix §§D, H.) |
| G. M4 runtime | **SUPPORTED WITH CAVEAT** | 60 held-out prompts, 540 observations, 180/180 exact per speculative condition, and Target/Guard 1.3114× [1.2487, 1.3787] support exact profitable execution. Guard's incremental utility is not supported; post-study paired comparison favors fixed speculation. Freeze-hash defect is audited but the appendix cannot itself expose the private archive. (Manuscript §§7.2–7.3, Table 3; appendix §H.) |

## 9. Audit of the 72/72 prediction

| Question | Judgment | Reason |
|---|---|---|
| Are predictions visible? | **PARTIAL** | The PDF specifies all 24 IDs, aggregate matches and four first-divergence tokens/indices, but does not print all 72 complete predicted ID arrays or their digest value; these are described as committed in an archive outside the PDF. (Appendix §J, p. 6.) |
| Are they complete generated-token-ID sequences? | **YES** | Endpoint is first 128 committed IDs or inclusive earlier EOG; the 72/72 success criterion compares complete arrays, with no partial threshold. (Appendix §§I–J, p. 6.) |
| Were they frozen before live outcomes? | **YES** | The stated chronology commits all 72 arrays and digest before the first of 72 live serialized outcomes, with no edits or selective reruns. The PDF reports the freeze rather than supplying the private timestamped archive for independent inspection. (Manuscript §§3.1, 5.2; appendix §J.) |
| Was the reserved set separate from discovery? | **YES** | Twelve exposed discovery tasks select H1; an audit excludes 31 B570-associated tasks from 164, leaving 133 candidates for deterministic selection of 24 reserved IDs. “No known exposure” is limited to audited records. (Manuscript §3.1; appendix §J.) |
| Was the test falsifiable? | **YES** | A predeclared 72/72 exact sequence criterion would fail on any mismatch; predicted reference equality and divergence indices add checkable secondary detail. (Manuscript §5.2; appendix §J.) |
| Does it show sufficiency versus unique causality? | **PARTIAL** | Yes for sufficiency: target-only UB1 reproduces this serialized trajectory without live drafting. No for unique causality: it does not identify a unique kernel or exclude other paths yielding the same output. This is also the authors' stated boundary. (Manuscript §5.2, §9; appendix §J.) |

## 10. Comparator distinctions

**VERY CLEAR.** The abstract identifies “fresh direct-ID studies”; §§2.1 and 4 explain that historical M4/RTX/B570 comparisons re-tokenize parsed CLI text; §5.1 and appendix §I expressly prohibit retroactive strict-ID certification of historical timing. The distinct B570 reserved prediction is then presented in §5.2 and appendix §J. Figure 3 separates old cost cells from new qualification counts. Table A4's shorthand “exact” is the main local hazard, despite its explanatory caption. (Manuscript pp. 1–2, 4–7; appendix Tables A3–A5.)

## 11. Actual population and exclusions

The evidence concerns one Qwen3-8B/0.6B Q8 0 pair on M4, RTX 5070 Ti Laptop and B570, with a symmetric INT4 OpenVINO draft on 358H; particular llama.cpp builds, CUDA/Metal/Vulkan/OpenVINO paths, greedy k=2, mostly HumanEval30, three repetitions and 128-token cap. M4's 24 Spec-Bench prompts and later balanced 60-prompt runtime set are separate. Tests use sequential requests and post-prefill timing, excluding load/prefill, concurrent serving and other model families. Historical comparators use parsed-text re-tokenization. B570 reserved tasks exclude known B570 associations in audited records; the M4 runtime study similarly excludes recorded outcome exposure. The study does not execute HumanEval code or measure functional pass@k. **SIGNIFICANCE CONCERN:** this scope is sufficient for the claimed case observations but thin for a field-level execution-path prescription or general mechanism. It is not, by itself, a validity defect because the manuscript mostly respects these boundaries. (Manuscript §§3, 9; appendix §§I–J.)

## 12. First-page test

From the **title, abstract, and introduction on page 1 only**, a three-minute reader sees a coherent systems problem: qualification of output paths before judging realized post-prefill cost. “Consumer systems” might initially suggest a broad benchmark, but the abstract immediately names bounded configurations and both profitable and blocked cases; Table 1 is deferred. The frozen **72/72 complete sequence prediction is conspicuous** in abstract and intro. Novelty appears early as prospectively frozen direct-ID qualification and controlled B570 target-partition prediction, with a 358H stateful-cost case. The exact relationship to close prior work is merely acknowledged by citation on page 1 and requires §8 to evaluate. The first page does not claim a successful adaptive-policy improvement: it states the M4 Guard is slower than fixed speculation. (Manuscript p. 1 only.)

## 13. Figures and tables

| Item | Necessity, readability, information and possible distortion |
|---|---|
| Table 1 (p. 4) | Necessary compact hardware/runtime scope and quantization difference. Readable; an explicit “not matched hardware comparison” note reinforces its meaning. |
| Table 2 (p. 4) | Necessary inventory of gains, slowdowns, pair counts, and classes. Dense but readable. Diagnostic B570 CI could look like a valid optimization result if “Diag.” or caption is missed; text corrects this. |
| Figure 1 (p. 5) | Necessary to retain the opposite M4 outcomes. Clear parity line and CIs; caption properly says separate studies with session differences, so visual juxtaposition should not be read as causal workload contrast. |
| Figure 2 (p. 6) | Useful organizing schematic, but text-heavy and partly repeats §§2 and 6. Its arrows could imply a universal pipeline; caption limits it to evaluation boundaries and non-exhaustive mechanisms. Most expendable main figure if space is scarce. |
| Figure 3 (p. 7) | Necessary split between old target-forward proxies and new direct-ID gates. Panel B is decisive. Panel A has tiny, configuration-mixed cells and deliberately no qualification encoding; the two panels cannot establish a cost/correctness frontier. Caption says so. |
| Figure 4 (p. 8) | Necessary visualization of isolated NPU speed and integrated loss. Bar segments and direct labels communicate the measured dominant regions. “Replay + proposal” is a combined region and should never be read as isolated replay time; caption is clear. |
| Table 3 (p. 9) | Necessary because it presents Guard's primary target-only gain beside fixed speculation and the secondary paired loss. The ratio direction and post-study status are explicit; oracle row is descriptive and carefully labeled. |
| Table A1 (appendix p. 2) | Necessary for reproducing campaign-specific estimators/CI conventions. Technical but legible; reveals nonuniform endpoints. |
| Table A2 (appendix p. 2) | Useful and concise sensor-boundary guardrail; prevents a false energy ranking. |
| Table A3 (appendix p. 3) | Necessary lookup behind Fig. 3A and for context-specific proxy values. Caption clearly rejects CI and complete-cost interpretations. |
| Table A4 (appendix p. 4) | Useful summary but partly redundant with Table 2 and potentially misleading in isolated cells: “Qualified”/“exact” for text-path comparisons sounds like the direct-ID contract. Rewrite cell labels, not merely the caption. |
| Table A5 (appendix p. 6) | Necessary direct-ID counts and gate status; readable and distinct from historical timing. |

## 14. Related Work, from the PDFs only

The paper gives substantial and fair credit to prior speculative-decoding cost accounting, consumer Apple positive/negative regimes, numerical path dependence, deterministic inference, heterogeneous CPU/GPU/NPU designs, state reuse, and adaptive runtime policies. In particular it acknowledges Chordiya's Apple slowdown and greedy/batch-shape observations; Kim's committed-work/runtime accounting; Yuan/Gond's numerical or deterministic work; and Lever/Ruiz y Mesa's heterogeneous modeling. Its credible distinction is **prospective direct-ID qualification plus frozen prediction of B570 serialized trajectories**, with the 358H interface measured as a case. The unsafe novelty implication would be that it discovered correctness gating, batch-shape-dependent argmax, cost modeling, or adaptive speculation generally; §8 explicitly avoids these. The risk is subtler: the distinctive B570 predictor may be narrower than the paper's overarching framing warrants. This judgment uses only the paper's own descriptions of cited work, not independent reading of those works. (Manuscript §§1, 8, pp. 1, 9–10.)

## 15. Single strongest rejection objection

**If I were arguing against acceptance, I would say...** the paper packages several carefully qualified case studies into a broad practical method, but its strongest novel mechanism is validated only for one B570 configuration and 24 reserved prompts, while its proposed runtime control is slower than a fixed speculative baseline and the 358H interface intervention never reaches performance testing. The 72/72 frozen prediction is real and valuable; it still does not show a mechanism that transfers across paths or an improved design decision beyond this configuration. Close prior work already covers much of the general qualification, numerical path-dependence and complete-cost motivation acknowledged in §8. Thus the central field-level contribution may fall below the bar even though the particular experiments are honest. (Manuscript §§5, 7–9; appendix §§H–J.)

## 16. Single strongest acceptance argument

**If I were arguing for acceptance, I would say...** the paper goes further than a catalog of speculative-decoding slowdowns: it prospectively tests direct-ID path qualification on two systems and freezes a mechanistic B570 predictor before obtaining 72/72 complete reserved sequences, including residual failures against the ordinary reference. This is unusually strong evidence that the target execution partition is sufficient for the observed divergence, and the negative 358H and M4 controls demonstrate a useful discipline of refusing speed claims when qualification or complete cost fails. Its narrow claims and transparent deviations make the evidence useful even without a transferable optimizer. (Manuscript §§2, 5, 7; appendix §§H–J.)

## 17. Revision priorities

**MUST FIX**

- Sharpen the thesis in abstract, §1 and conclusion around the actual new result: a frozen, configuration-specific target-trajectory predictor, with direct-ID qualification as the enabling measurement. State explicitly what advance remains over the close consumer/numerical/cost-accounting prior art without implying a general qualification recipe was invented. (Manuscript pp. 1, 9–10.)
- Replace the historical “Qualified; ... exact” Table A4 cells with “text-path agreement” plus their counts; reserve “direct-ID qualified” for Table A5 and the 358H/M4 prospective entries. (Appendix Table A4, p. 4.)

**SHOULD FIX**

- Add a compact in-PDF validation ledger for §J: frozen predictor and outcome digest values, exact freeze/live ordering identifiers or timestamps, and a short complete-array example for a divergent reserved prompt. This would let artifact-only readers inspect the precommitment more directly, without demanding all 72 arrays in print. (Appendix §J, p. 6.)
- Make the Fig. 3 and §5.2 interpretation maximally precise: the target-only UB1 path is a sufficient output predictor on this setup, not a uniquely identified numerical operation. The manuscript mostly does this already; a sentence describing plausible observationally equivalent partitions would help. (Manuscript pp. 5–7.)
- Present §7's M4 Guard as a feasibility/negative comparative test from its opening paragraph. Its 1.3114× gain against target-only should always be adjacent to the faster 1.3469× Always-Spec and the post-study paired 1.0271× loss. (Manuscript pp. 8–9.)

**OPTIONAL**

- If feasible in a new study, test the predeclared B570-style predictor on a second backend or a second model/runtime pair; report failures as well as successes. This would address significance and transfer but is not needed to validate the present bounded claim. (Manuscript §§5.2, 9.)
- Reduce Figure 2's text and use the space for the validation ledger or a tighter prior-work differentiation. (Manuscript p. 6.)

## 18. Recommendation

**WEAK REJECT.**

## 19. Confidence

**4/5.** I am confident about the claim boundaries and novelty-versus-scope objection based on the two PDFs, while the private evidence archives and original cited papers are outside this artifact-only review.

## 20. Decision rationale

The paper's 72/72 B570 result is a legitimate frozen prediction of complete token trajectories, not a mere restatement of 60/72 reference equality. Fresh RTX/B570 direct-ID qualification and 358H complete-cost records are also useful, and the authors carefully prevent blocked or text-path timing from becoming stronger claims. My weak rejection rests on significance: the broad systems prescription is close to work the manuscript already credits, while the distinctive mechanism has one configuration and a small reserved same-family workload. The 358H cost bottleneck is tied to one inseparable replay-plus-proposal call, and its improvement attempt fails qualification; the M4 guard runs exactly and profitably but loses to fixed speculation. These facts limit the paper's demonstrated change to systems practice, even though they do not invalidate its bounded findings. A more focused account of the B570 predictive advance, clearer comparative novelty and a directly inspectable freeze summary would materially strengthen it. (Manuscript §§5, 7–9; appendix §§H–J.)

## Special Questions

**Q1. What kind of paper?** **E — coherent B+C+D**, with the greatest novelty in C (predictive mechanism), B (execution-path qualification) as the prerequisite, and D (heterogeneous runtime-cost diagnosis) as bounded support. The coherence is methodological rather than a common cross-platform causal experiment. (Manuscript §§5–7.)

**Q2. More than a benchmark of its own system?** **CLEARLY YES.** Frozen direct-ID gates and the 72/72 target-only predictor test an explanatory hypothesis, and measured cost regions address an interface mechanism. Their external reach remains narrow. (Manuscript §5; appendix §§I–J.)

**Q3. Importance of frozen 72/72?** **YES.** Without reserved pre-outcome complete-sequence prediction, the B570 result would be exposed discovery and an after-the-fact matching observation. (Manuscript §§3.1, 5.2; appendix §J.)

**Q4. Would a second-backend transfer change recommendation?** **YES**, if prospective, same-contract and genuinely successful (or informative about failure boundaries). It would address the principal significance concern; it need not prove a universal rule. (Manuscript §9.)

**Q5. Does lack of transfer invalidate current claims?** **NO.** The paper restricts sufficiency and performance to tested configurations. It affects importance and generality. (Manuscript §§5.2, 9.)

**Q6. 358H case?** **Useful supporting.** Direct round accounting exposes a realized interface loss, but the combined region and stopped intervention prevent a strong causal optimization claim. (Manuscript §§5.3, 7.1; appendix §§D, H.)

**Q7. M4 runtime case?** **Useful supporting**, though disproportionately long relative to its positive novelty. It demonstrates exact prospective complete-cost control and honestly reports that fixed speculation wins. (Manuscript §7, Table 3; appendix §H.)

**Q8. Exact overstated claims?** **NONE FOUND in the central prose, if its stated scope and comparator qualifiers are read.** The potentially misleading shorthand is appendix Table A4's historical “Qualified; 72/72 exact” and “90/90 exact” cells, because those cells refer only to re-tokenized-text comparisons; the caption does qualify them. The phrase “state interface consumes an isolated draft-device advantage” in the conclusion is warranted as an observed integrated interface outcome, but should not be read as an isolated estimate of replay cost or of a persistence intervention. (Manuscript §10, p. 10; appendix Table A4, p. 4.)
