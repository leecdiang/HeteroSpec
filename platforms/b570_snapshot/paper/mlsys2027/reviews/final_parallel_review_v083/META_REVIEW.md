# MLSys-Style Meta Review

## 1. Submission summary

The paper asks whether speculative decoding on consumer systems preserves a specified greedy generated-ID sequence and whether local throughput advantages survive complete post-prefill execution cost. Separate M4, RTX, B570, and 358H cases support an execution-path qualification workflow. Its distinctive result is a frozen B570 target-only micro-batch-one predictor matching 72/72 reserved serialized runs, comprising 24 repeat-stable prompts, four of which diverge from the reference. Fresh RTX serialization qualifies at 90/90 direct-ID pairs, whereas B570 serialization remains blocked at 78/90. On 358H, integrated CPU and NPU draft paths are slower than target-only. A qualified M4 Guard beats target-only but loses to fixed speculation. [Manuscript pp. 1–2, 5–9; Appendix pp. 6–8.]

## 2. Consensus strengths

- The prespecified, pre-live B570 prediction is a falsifiable step beyond retrospective numerical-path diagnosis; all four reference-divergent prompts are correctly predicted across three runs, including first-divergence positions. [Manuscript p. 6; Appendix pp. 6–8.]
- Direct-ID qualification is clearly distinguished from historical text-derived agreement and historical timing. Failed gates are retained as blocked outcomes. [Manuscript pp. 2, 5–6; Appendix p. 6.]
- Complete 358H timing and the unfavorable M4 fixed-policy comparison are candidly reported, with estimator and measurement boundaries visible. [Manuscript pp. 7–9; Appendix pp. 1–2, 5–6.]

## 3. Consensus weaknesses

- The discriminating B570 evidence is four distinct reference-divergent trajectories on one model/runtime/backend; three stable repetitions do not add independent prompts, and predictor transfer is untested. [Manuscript pp. 6, 10; Appendix pp. 6–8.]
- The PDFs show a prediction-file digest, reported chronology, short hashes, and a task ledger, but not the 72 full predicted/live arrays or an independently inspectable temporal commitment. [Appendix pp. 7–8.]
- Fresh RTX/B570 gates have no matched fresh latency. The 358H replay/proposal region cannot be decomposed, its later intervention is blocked, and M4 Guard is slower than fixed speculation. [Manuscript pp. 6–9; Appendix pp. 1, 6.]

## 4. Disagreement with R1–R6 recommendations

| Reviewer | Recommendation | Main decision weight |
|---|---|---|
| R1 Systems | WEAK ACCEPT | The bounded prospective diagnosis clears a measurement-paper bar despite limited transfer. |
| R2 Novelty | WEAK REJECT | Known batch-shape effects and a single predictive stack leave insufficient generalizable novelty. |
| R3 Rigor | WEAK ACCEPT | The frozen complete-sequence test and evidence discipline outweigh narrow causal isolation. |
| R4 Adversarial | WEAK REJECT | Four distinct divergent prompts and no new speed advantage are too narrow for MLSys significance. |
| R5 Writing | WEAK ACCEPT | A coherent, falsifiable local result merits acceptance with clearer granularity and audit limits. |
| R6 Champion | ACCEPT | Exact path qualification and honest negative systems evidence suffice without transfer. |

I side narrowly with R1/R3/R5 on publication of a scoped measurement contribution. R2/R4 identify the decisive limitation, but their significance threshold would discount the precommitted prediction of the *non-reference* trajectories and the disciplined negative integration evidence more than I would. I do not adopt R6's firmer accept because independent transfer and PDF-level audit access remain absent. [Manuscript pp. 5–10; Appendix pp. 6–8.]

## 5. Strongest acceptance case

H1 was selected using outcome-exposed discovery, then its complete reserved predictions were fixed before live results. It matched all 72 capped generated-ID sequences, including 12/12 repetitions across four prompts where the UB128 reference fails; the reference matches only 60/72 on the same reserve. This is a substantive, prospective path-level test, reinforced by honest direct-ID gates and full-loop cost accounting. [Manuscript pp. 5–7; Appendix pp. 6–8.]

## 6. Strongest rejection case

The novel positive diagnosis is one B570 Vulkan/Qwen configuration, 24 deterministic prompt trajectories and just four discriminating reference divergences. It does not isolate a unique live-loop numerical cause or transfer to a second backend. The other studies do not demonstrate a new qualified optimization over fixed speculation, and the central complete arrays and temporal freeze cannot be independently checked from these PDFs. [Manuscript pp. 6–10; Appendix pp. 7–8.]

## 7. Scientific validity

**ADEQUATE.** The path-scoped claims follow from the reported protocol and comparisons, but independent PDF-only verification of full arrays and temporal commitment is limited. Predictive sufficiency must not be read as unique causal localization. [Manuscript pp. 2, 6, 10; Appendix pp. 6–8.]

## 8. Novelty

**MODERATE.** The novel element is the prospective complete-trajectory prediction on a blocked path, not batch-shape sensitivity, cost decomposition, heterogeneous placement, or adaptive control themselves. [Manuscript pp. 6, 9; Appendix pp. 6–8.]

## 9. Systems significance

**MODERATE.** The qualification and realized-cost discipline is reusable, while the predictor's prevalence or portability and any successful incremental runtime benefit remain unknown. [Manuscript pp. 5–10.]

## 10. Experimental rigor

**HIGH.** Frozen gates, reserved selection, prompt-level estimators, explicit stops, and negative comparisons are unusually careful. This rating concerns design and reported analysis, not independent raw-artifact verification or broad sampling. [Manuscript pp. 3, 5–9; Appendix pp. 1–2, 6–8.]

## 11. Coherence

**ADEQUATE.** Qualification, B570 prediction, and 358H realized cost form a bounded systems argument; the separate M4 regimes and Guard test make the presentation dense and should remain supporting evidence. [Manuscript pp. 1, 4–9.]

## 12. Single main blocker or NONE

**Limited external scope of the central prediction:** one B570 stack and four distinct reference-divergent reserved prompts constrain a stronger MLSys significance claim. This is a blocker to firmer acceptance, not a contradiction of the tested-path result. [Manuscript pp. 6, 10; Appendix pp. 6–8.]

## 13. New experiment required

**OPTIONAL.** Several reviewers independently identify transfer as the chief *significance* limit, but none establishes a scientific invalidity that requires a new run for the bounded claim. **Cross-backend transfer REQUIRED: NO. Textual changes suffice: YES** for the scoped weak-accept decision, provided the 24-prompt/four-divergence granularity and PDF-only audit boundary are explicit. A second frozen transfer test could change the strength of the recommendation. [Manuscript pp. 6, 10; Appendix pp. 7–8.]

## 14. Exactly one highest-value revision likely to alter decision

Run a separately frozen, complete-sequence target-partition prediction on a genuinely independent backend or model with reserved reference-divergent cases, and report success or failure under the same pre-live criterion. A successful informative transfer would directly address R2/R4's significance objection; it is optional for the present path-scoped result. [Manuscript p. 10; Appendix pp. 6–8.]

## 15. Final recommendation

**WEAK ACCEPT**

## 16. Confidence

**4/5.** The PDFs expose the protocol, endpoints, chronology as reported, and enough granularity for a scope judgment; they do not permit independent full-array or freeze-time audit. [Appendix pp. 6–8.]

## 17. Rationale (250–500 words)

**Scope.** I interpret the submission as a measurement and diagnosis paper about specified execution paths, not a new decoder or a hardware ranking. The historical M4, RTX, and B570 timings use text-derived agreement, whereas the new RTX/B570 gates use captured generated IDs and have no matched fresh latency. The paper mostly keeps these evidence classes separate. It also discloses that the B570 reserve contains 24 repeat-stable prompts, 20 reference-equal and four reference-divergent, within a 128-ID/EOG generated-output contract. This limits population and cross-backend claims. [Manuscript pp. 2–6, 10; Appendix pp. 6–8.]

**Validity.** The B570 H1 selection followed 36/36 exposed discovery matches; reserved IDs, predictor semantics, and 72 predicted arrays were then fixed before reported live outcomes. Predictor/live matches 72/72, compared with reference/live 60/72 on the same set. Correct prediction of all four divergent prompt trajectories makes reference echo an inadequate explanation, though the target-only harness does not isolate the responsible numerical operation inside the live loop. The digest binds content if the file is available; the chronology is reported separately, and the PDFs alone do not let a reviewer recompute all full-array matches or independently authenticate freeze timing. These limits warrant careful wording, not a finding that the result is false. [Manuscript p. 6; Appendix pp. 6–8.]

**Significance.** R2 and R4 reasonably view one backend and four discriminating trajectories as too little transfer evidence, especially since the 358H intervention stops at qualification and Guard loses the fixed-speculation comparison. I nevertheless find the prospective blocked-path prediction, direct-ID gates, and complete 358H cost accounting jointly useful to systems researchers who must decide whether a fast-looking path is admissible and profitable. The 358H 58.35% region measures reconstruction *plus* proposal, not recoverable replay alone; Guard's 1.3114× target-relative speedup does not beat Always-Spec, whose paired secondary latency comparison favors the fixed policy. I give the bounded evidence more weight than the novelty skeptic and adversarial reviewer, without inferring transfer or a deployable improvement. [Manuscript pp. 6–9; Appendix p. 1.]

**Presentation.** The abstract and conclusions are generally candid, but the 72/72 headline should immediately state 24 distinct prompts and four reference-divergent ones, with the same-set 60/72 comparison moved next to the main claim. The full-array audit limit should be stated plainly if an anonymous artifact cannot be made accessible. These textual changes support a weak accept; an independently frozen transfer study would be the clearest route to a stronger decision. [Manuscript pp. 1, 6, 10; Appendix pp. 7–8.]
