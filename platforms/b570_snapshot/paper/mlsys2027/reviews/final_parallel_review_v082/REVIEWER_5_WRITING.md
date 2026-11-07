Artifact-only review.
Sources consulted:
  - manuscript-v0.8.2.pdf
  - appendix-v0.8.2.pdf

No README, handover, source files, repository evidence, prior reviews,
Git history, PR descriptions, experiment logs, or web searches were used.

## 1. Paper summary

This paper studies when speculative decoding on four consumer systems preserves a chosen greedy generated-token sequence and when locally promising components produce a faster complete post-prefill loop. It distinguishes historical comparisons of re-tokenized CLI text from newly frozen direct generated-ID qualification studies. On shared HumanEval30 tasks, serialization changes RTX agreement from 75/90 to 90/90, but B570 from 60/90 to only 78/90, leaving that path blocked. A subsequent B570 experiment selects a target micro-batch-one hypothesis on exposed discovery prompts, then predicts all 72 complete serialized sequences from 24 reserved prompts before live outcomes. Twelve of those sequences diverge from the reference; prediction does not confer qualification. A 358H CPU/NPU study shows that an isolated NPU draft-throughput advantage disappears in a stateful interface that replays the committed prefix on every proposal call; both exact integrated paths lose to target-only. Separate historical M4 studies show a slowdown on representative prompts and a gain on code prompts, with different sessions and text-based comparators. A prospectively frozen M4 continuation guard preserves direct IDs and beats target-only on 60 held-out prompts, but fixed speculation is faster in a post-study paired comparison. The paper proposes a bounded practice: qualify output paths, isolate the target execution partition after failure, and measure complete realized costs on qualified paths. Its evidence is rich but deliberately configuration-specific (manuscript pp. 1–10; appendix pp. 1–6).

## 2. Central thesis

A favorable draft or target-forward microbenchmark is insufficient for a useful speculative path: the actual execution path must first satisfy an explicit output contract, and complete stateful cost must then beat the matched target-only path. Target execution partition can be a sufficient predictor of otherwise surprising serialized output on the tested B570 stack (manuscript pp. 2, 5–6).

## 3. Top contributions, ranked

1. **Prospective B570 mechanism test:** a frozen target-only micro-batch-one predictor matches 72/72 reserved complete serialized sequences, including the 12 reference-divergent pairs (manuscript p. 5; appendix p. 6).
2. **Direct-ID path qualification:** fresh RTX and B570 comparisons show different effects of serialization under a predeclared 90/90 gate, while expressly separating these from historical timing (manuscript pp. 1, 5, 7; appendix pp. 5–6).
3. **Realized-cost accounting on 358H:** exact CPU/NPU paths both lose despite isolated NPU drafting throughput; complete target-side work and the synchronous prefix-replay-plus-proposal region locate the measured costs (manuscript pp. 5–6, 8; appendix p. 1).

## 4. Single strongest contribution

The B570 reserved prediction is the most nontrivial result. It turns an outcome-informed diagnostic into a precommitted, falsifiable prediction of entire generated-ID trajectories, including divergences rather than merely predicting whether a prompt will pass. The discovery decision is stated as H1 at 36/36 on 12 exposed tasks; 31 potentially exposed tasks are excluded from a 164-task audit and 24 reserved IDs selected deterministically from 133 eligible tasks. On the reserved set, 72/72 sequences, 24/24 equality classifications, and 12/12 divergent first positions agree (manuscript pp. 3, 5; appendix p. 6). This is persuasive evidence of *sufficiency for the tested trajectory*. The PDFs do not display all predicted arrays or external timestamps, so an artifact-only reader cannot independently replay the chronological claim or infer the unique physical cause.

## 5. Single strongest empirical result

**72/72 complete generated-ID sequence predictions** on 24 reserved B570 HumanEval tasks × three repetitions, precommitted before serialized outcomes; this includes **12/12 first-divergence indices** on four prompts. Actual and predicted reference agreement is only **60/72**, so this is a successful prediction of a still-blocked path, not a correctness rescue (manuscript p. 5; appendix p. 6).

## 6. Strengths

1. The primary text repeatedly labels comparator, timing boundary, evidence class, and blocked paths; it avoids converting a precise CI on a mismatching B570 path into admissible speed (manuscript pp. 2, 4–5).
2. The reserved B570 endpoint predicts complete sequences and residual failures, a substantially sharper test than post hoc class labels (manuscript p. 5; appendix p. 6).
3. Direct-ID RTX/B570 studies have a common task/model/protocol family and a stringent full-workload gate, with explicit runtime/reference differences that prevent a hardware-only causal comparison (manuscript p. 5; appendix pp. 5–6).
4. The 358H decomposition uses committed output including correction/bonus tokens and discloses that replay and proposal share a timed region (manuscript pp. 2, 6, 8; appendix p. 1).
5. M4 Guard's unfavorable fixed-speculation comparison and the stopped 358H intervention are reported plainly (manuscript pp. 7–9).

## 7. Weaknesses

1. **MAJOR — significance/scope:** The title and four-system sweep promise a broad consumer-systems result, but the strongest novel mechanism concerns one B570 backend, model pair, greedy width, context, and HumanEval slice. The cross-system cases have different software, quantization, session conditions, and comparator standards; there is no second backend transfer of the target-partition predictor (manuscript pp. 3, 10).
2. **MODERATE — clarity:** The first page compresses four campaigns, two generations of comparator, the B570 validation, 358H cost, and a negative M4 control result into one dense abstract and introduction. Acronyms such as RTX/B570/358H and “target partition” appear before enough execution-path intuition; the main scientific question competes with a runtime-policy subplot (manuscript p. 1).
3. **MODERATE — missing evidence:** The appendix gives reserved task IDs, four divergence positions/tokens, aggregate checks, and assertions of precommitment, but not a compact, inspectable commitment chronology or the complete prediction/outcome arrays in the PDF. Thus the most important prospective claim is well described but only partly reconstructable from these artifacts alone (manuscript p. 5; appendix p. 6).
4. **MODERATE — missing comparison:** The held-out mechanism result has no transfer to another backend or an explicit alternative target-only partition control evaluated on the same reserved set. The H2 branch is deliberately not run after discovery success, so the evidence establishes sufficiency rather than discrimination among plausible sufficient predictors (appendix p. 6; manuscript p. 10).
5. **MINOR — clarity:** Figure 3 juxtaposes historical target-forward proxies and fresh qualification counts, although they are not same-run cost/correctness observations. Caveats are present, but an initial visual scan invites a causal or tradeoff reading that its data cannot support (manuscript p. 7).

## 8. Claim–evidence audit

| Claim | Assessment | PDF basis and limit |
|---|---|---|
| A. Execution-path qualification is needed before a strict output-preserving speed claim | **WELL SUPPORTED** | Output contract and evidence classes are defined on manuscript p. 2; blocked RTX/B570 outcomes are separated from admissible ones on pp. 4–7. This is an evaluation discipline, not proof that every deployment needs exact IDs. |
| B. RTX serialization restores direct-ID qualification | **WELL SUPPORTED** | Fresh 75/90 batched versus 90/90 serialized under 90/90 gate (manuscript pp. 1, 5, 7; appendix pp. 5–6). It does not certify old RTX timings or establish a hardware-general rule. |
| C. B570 serialization remains blocked under direct IDs | **WELL SUPPORTED** | Fresh fast 60/90 versus serialized 78/90, both short of 90/90 (manuscript pp. 1, 5, 7; appendix p. 6). Different historical 60/90 text-path fallback and later reserved 60/72 are separately labeled. |
| D. B570 target partition is the mechanism | **SUPPORTED WITH CAVEAT** | Reference reproduction 90/90, discovery 36/36, and reserved 72/72 support sufficiency of target-only micro-batch one for the tested trajectories (manuscript p. 5; appendix p. 6). They do not identify a kernel, uniquely exclude other sufficient changes, or establish cross-backend causality. The text mostly makes this narrower claim. |
| E. Frozen 72/72 held-out prediction | **SUPPORTED WITH CAVEAT** | Explicit freeze order, selected IDs, all-sequence endpoint, 72/72 and 12/12 divergent positions appear in manuscript pp. 3, 5 and appendix p. 6. The PDFs assert rather than expose the full arrays and timestamp/hash evidence for independent artifact-only verification. |
| F. 358H realized-cost explanation | **SUPPORTED WITH CAVEAT** | 90/90 exact per CPU/NPU path, mean totals 13.25/27.54 s vs 9.58 s, cost shares and accounting reconstruction appear on manuscript pp. 5–6, 8 and appendix p. 1. The 58.35% NPU region combines prefix replay and proposal; replay's individual causal contribution and benefit of persistent state are unmeasured. |
| G. M4 runtime guard achieves qualified profitable execution | **WELL SUPPORTED** | 180/180 exact per speculative condition; Guard 1.3114× [1.2487, 1.3787] versus target-only, and fixed speculation 1.3469×; paired Guard/fixed ratio 1.0271 [1.0130, 1.0436] shows Guard slower (manuscript pp. 8–9; appendix p. 5). Any incremental control benefit would be overstated, but the paper explicitly disclaims it. |

## 9. Audit of the 72/72 result

| Question | Judgment | Reason |
|---|---|---|
| Are predictions visible? | **PARTIAL** | The PDF shows prediction rule, task IDs, equality classes in aggregate, and four first-divergence tokens/indices, but not the 72 full predicted arrays (appendix p. 6). |
| Are they complete generated-token-ID sequences? | **YES** | Endpoint is first 128 committed IDs or inclusive earlier EOG; the specified primary endpoint compares all 72 complete arrays, not a digest of a few positions (manuscript p. 5; appendix p. 6). This is a reported property, not an independently recomputed one here. |
| Frozen before live outcomes? | **PARTIAL** | The paper states all predictions and digest were committed before the first live outcome and no changes/reruns occurred; the PDF does not furnish inspectable timestamped commitments or complete arrays (appendix p. 6). |
| Reserved separately from discovery? | **YES** | Twelve named exposed discovery tasks, conservative 31/164 exclusion audit, deterministic selection of 24 other IDs from 133 eligible, and H1 selection before reserved inference are described (manuscript p. 3; appendix p. 6). “No known exposure” is appropriately limited to audited records. |
| Is the test falsifiable? | **YES** | The frozen criterion requires all 72 full sequences; a single mismatch would fail, including on the four reference-divergent prompts (appendix p. 6). |
| Does it establish sufficiency versus unique causality? | **YES, sufficiency only** | The reproduced trajectory without live drafting supports a sufficient tested target execution partition; it cannot uniquely attribute the root operation or imply a universal micro-batch rule (manuscript pp. 5, 10; appendix p. 6). |

## 10. Separation of three evidence generations

**MOSTLY CLEAR.** Section 2.1 (manuscript p. 2) is the essential legend: historical M4/RTX/B570 equality is reconstructed from parsed CLI text, while 358H, new RTX/B570 qualification, and prospective M4 runtime use direct IDs. Table 2 and its lead-in (p. 4), Figure 3 (p. 7), and Appendix A5 (p. 6) reinforce that fresh qualification does not retroactively validate historical timing. The B570 historical text-path 60/90, new direct-ID 78/90 serialized, and later reserved direct-ID 60/72 are especially easy to conflate on a skim. Appendix Table A4's unqualified “exact” cell labels require its long caption to avoid that confusion (appendix p. 4).

## 11. Actual population, exclusions, and scope

The sampled population is frozen prompt sets on named configurations, not consumer GPUs generally: historical M4 24 Spec-Bench prompts and separate 30 HumanEval IDs, historical RTX/B570 controls, fresh direct-ID HumanEval30 on RTX/B570, 24 B570 reserved HumanEval tasks, 30 HumanEval prompts for each 358H Phase-3 path, and 60 balanced M4 held-out HumanEval/Spec-Bench prompts (manuscript pp. 3–5, 8–9). Three repetitions often share a prompt and are not 72 or 90 independent prompts. B570 reservation excludes 31/164 tasks with any audited B570 association; the remaining 133 yield 24 hash-selected tasks. M4 runtime excludes recorded prior exposure, then divides selected prompts into 40 calibration, 16 qualification, and 60 held-out (manuscript pp. 3, 8; appendix pp. 5–6). No serving concurrency, broader model families, pass@k, whole-request latency, population failure rate, or cross-device energy ranking is measured (manuscript pp. 2, 10). **SIGNIFICANCE CONCERN:** the boundaries are candid and internally valid as stated, but a one-backend mechanism limits breadth for a systems venue.

## 12. First-page test (title, abstract, introduction page only)

**Three-minute impression:** A serious, unusually candid measurement paper about qualifying speculative execution paths before treating batching or draft throughput as speed evidence. The headline I retain is “B570 target-only micro-batch one predicts 72/72 serialized outputs,” followed by “RTX serialization qualifies; B570 still fails.” The dense abstract makes the 358H and Guard stories feel coequal before I know how they connect.

**Consumer benchmark confusion:** Yes, possible. The title and “four consumer systems” can initially suggest a matched, cross-hardware benchmark; the introduction does say campaigns were separately frozen and session conditions differ, but the full hardware/software co-variation warning arrives on pp. 3–4. A title or abstract modifier such as “case studies” would better set expectations.

**72/72 visibility:** Very visible in abstract and right column of p. 1, including “complete generated-token-ID sequences” and a separate reserved set. The meaning of target execution partition still takes until Section 5 to become concrete.

**Novelty early:** The numbered contributions on p. 1 correctly elevate direct-ID qualification, reserved B570 prediction, and 358H accounting. The novelty boundary against numerical path dependence and prior systems work is asserted in a long closing intro sentence, then explained much more usefully in Related Work on pp. 9–10.

## 13. Key figure and table assessment

| Display | Necessity, readability, information, and risk |
|---|---|
| **Table 1, p. 4** | Necessary scope map; model/runtime and draft placement are readable. Consider placing the common k, cap, and comparator generation in a compact note; “evidence scope” phrases alone are terse. |
| **Table 2, p. 4** | Necessary ledger of qualified, secondary, and diagnostic outcomes. “Matching pairs” mixes text-path and direct-ID evidence, although caption states this; a visible comparator column would prevent accidental cross-row equivalence. The RTX secondary speedups sit alongside primary results despite fresh direct-ID qualification being a separate study. |
| **Figure 1, p. 5** | Clear, economical display of opposite M4 speedups and parity. It cannot identify workload causality because sessions differ; caption correctly says so. Some redundancy with Table 2 is acceptable because this visual makes the contrast memorable. |
| **Figure 2, p. 6** | Helpful conceptual order for a novice, but the small boxes and unusually long caption duplicate Sections 2 and 6. It provides no new empirical relation; shrink and use the space to clarify B570's actual target partition or the three evidence generations. The arrow can look like a sequential intervention study, which text explicitly denies. |
| **Figure 3, p. 7** | Panel B is essential and immediately legible; the 90/90 gate, open/filled marks, and counts carry the qualification claim. Panel A's 11 historical cells are informative but combine differing context definitions and measurements unrelated to B's runs; the juxtaposition risks a same-run cost/correctness interpretation despite the caption. “RTX batched near 1” must never be read as an admissible speedup. |
| **Figure 4, p. 8** | Essential visual distinction between isolated throughput and integrated post-prefill costs. Means and prompt geometric-mean speedups are differentiated in captions. Label replay-plus-proposal as a single region directly in the NPU bar or main text, because the colored bar might otherwise be read as replay-only cost. Its long caption bears much of the necessary estimator and boundary detail. |
| **Table 3, p. 9** | Necessary to show both the registered target comparisons and unfavorable post-study paired contrast. The separate secondary rule and direction “above one means Guard slower” are clear. “Guard / offline oracle” is regret rather than speedup; its explanation is essential and present. |
| **Appendix A1–A5, pp. 2–6** | A1/A5 are useful for estimator and direct-ID reconstruction; A3 retains all Figure 3A cells. A2 is a compact sensor-boundary reminder. A4 largely duplicates Table 2 and its “exact” shorthand can obscure the text-path qualifier. None displays the 72 complete prediction arrays. |

## 14. Related Work (PDF only)

The paper credits prior speculative decoding theory (Leviathan), cost/performance studies (Liu et al.; Kim et al.; Lyu et al.), heterogeneous designs and predictive performance models (Dovetail, DuoDecoding, Mirror-SD, Ruiz y Mesa et al., Lever), adaptive controllers (TurboSpec, BanditSpec, HeteroSpec), numerical/path dependence and correctness forensics (Zhang et al.; Yuan et al.; LLM-42), state reuse (Yuan et al.), and especially consumer Apple-silicon gains/losses and batch-shape changes (Chordiya) (manuscript pp. 9–10). That is fairer than calling batching failure or numerical nondeterminism new. The strongest distinction is the pre-frozen direct-ID path qualification plus reserved target-partition sequence prediction, not a new greedy-numerics phenomenon. The 358H state-interface observation is a measured case rather than invention of state reuse, and Guard is not claimed as a superior adaptive policy. A clearer, earlier comparison to the closest consumer-hardware and correctness papers would make the novelty boundary easier to assess from p. 1.

## 15. Single strongest objection

If I were arguing against acceptance, I would say... the paper's one genuinely sharp mechanism result is a 24-prompt, single-B570-backend target-partition predictor whose full predictions and commitment chronology are not inspectable in the submitted PDFs; the remaining platforms mix historically text-qualified timing, different sessions and stacks, a qualified but negative state interface, and an M4 controller slower than fixed speculation. The resulting cross-system story is valuable engineering discipline but may be too narrow to substantiate the breadth suggested by the title (manuscript pp. 1, 3–10; appendix p. 6).

## 16. Single strongest acceptance argument

If I were arguing for acceptance, I would say... systems papers need falsifiable, output-aware diagnoses of why apparently cheap speculative work does not translate into usable speed. The paper does that unusually well: fresh direct-ID gates distinguish RTX and B570, a separately reserved 72/72 full-sequence prediction locates a sufficient B570 execution partition including failures, and exact 358H timings show precisely which measured state-interface region consumes local promise. It also reports an unfavorable Guard/fixed result and scopes every comparison instead of polishing away blocked paths (manuscript pp. 2, 5–9; appendix pp. 5–6).

## 17. Revision priorities

**MUST FIX**

- In abstract and first-page contributions, call these *configuration-specific case studies* and state that historical speedups use text-path agreement while fresh RTX/B570 studies are qualification-only. This will stop a first reader from mentally pairing fresh IDs with historical latency (manuscript p. 1; Table 2, p. 4).
- At the first mention of “target partition,” give the operational intervention: target-only greedy decoding with target micro-batch one versus the UB128 reference, matching serialized output without a live draft. Preserve “sufficient on the tested stack” in abstract, Section 5.2, and conclusion (manuscript pp. 1, 5, 10; appendix p. 6).
- Add an artifact-visible, compact chronology in Appendix J: discovery rule and 36/36 decision; reserved-ID hash rule; prediction commitment before first live run; outcome count. Include a machine-readable supplement or compact per-prompt prediction/outcome digest table if page limits permit, with the four divergent indices already shown. This makes the 72/72 central result more reviewable without publishing raw private paths (appendix p. 6).

**SHOULD FIX**

- Add an explicit comparator column or badges to Table 2 and avoid bare “exact” labels in Appendix A4 for historical re-tokenized-text counts. Name the three distinct B570 denominators (historical 60/90 text, fresh 78/90 direct ID, reserved 60/72 reference equality) near Figure 3 or Section 5.2 (manuscript pp. 4–5, 7; appendix p. 4).
- Reorganize the abstract into a single throughline of qualification → partition prediction → realized cost, then one short M4 sentence. Move Guard's exact CI and fixed-speculation comparison to the results section if space is tight. The lack of incremental control benefit must remain explicit (manuscript pp. 1, 8–9).
- In Figure 3, visually separate historical microbenchmarks from fresh qualification panels and print “different runs/contexts” on the figure, not only the caption. In Figure 4, put “replay + proposal, inseparable” on the cost panel (manuscript pp. 7–8).
- Discuss why repeating 72 sequences across 24 prompts is a stringent sequence endpoint but does not amount to 72 independent prompt samples or imply a failure-rate estimate (manuscript p. 5; appendix p. 6).

**OPTIONAL**

- Compress Figure 2 or move it to the appendix, freeing room for a concrete two-path token example of reference versus serialized B570 divergence (manuscript p. 6).
- Add an early sentence positioning Chordiya and the numerical correctness literature, then reserve detailed comparisons for Section 8 (manuscript pp. 1, 9–10).
- Shorten Figure 1 and Figure 4 captions after moving essential estimator/boundary definitions into a common reader-facing legend (manuscript pp. 5, 8).

## 18. Recommendation

**WEAK ACCEPT**

## 19. Confidence

**4/5.** I can assess the argument, first-read communication, and internally reported outcomes from both PDFs; I cannot inspect the private predictions, timing traces, or historical provenance from these artifacts.

## 20. Decision rationale

I lean weak accept for the disciplined sequence from output qualification to a falsifiable reserved mechanism prediction and complete realized-cost accounting. The 72/72 B570 endpoint is unusually specific: it predicts full direct-ID trajectories, including failures, after a described discovery/reservation split. The fresh RTX/B570 gate and 358H state-interface measurements make the practical lesson concrete. The paper also earns credibility by showing that Guard is slower than fixed speculation and by refusing to treat blocked timings or old text equality as strict-ID speed claims. Its limits matter: one narrow model/backend family, nonmatched cross-system campaigns, no second backend target-partition transfer, and no full commitment record visible in the PDFs. The title and dense first page currently inflate the apparent scope and obscure the cleanest novelty. Clearer evidence-generation labels and a compact appendix chronology would strengthen the submission; absent those edits, the central bounded result still seems worth a systems audience's attention (manuscript pp. 1–10; appendix pp. 5–6).

## Special Questions

- **Q1. What is the paper primarily?** **E — coherent B+C+D.** Execution-path qualification, predictive B570 mechanism, and heterogeneous realized-cost cases form the intended chain. C is its sharpest novel component; the studies are separately frozen rather than a common intervention chain (manuscript pp. 1, 5–7).
- **Q2. More than a benchmark of its own system?** **CLEARLY YES.** Fresh path gates and a held-out target-only prediction explain a failure mode; 358H times complete stateful regions. The generality remains bounded (manuscript pp. 5–8).
- **Q3. Is frozen 72/72 important?** **YES.** Without precommitted full trajectories and reserved prompts, the B570 target-partition story would be mostly post hoc (manuscript p. 5; appendix p. 6).
- **Q4. Would transfer to a second backend change recommendation?** **MAYBE.** A comparably frozen direct-ID transfer, positive or informative negative, would materially strengthen scope; merely repeating a less controlled observation would not (manuscript p. 10).
- **Q5. Does lack of transfer invalidate current claims?** **NO.** The current claims are explicitly limited to the tested paths and sufficiency on B570 (manuscript pp. 5, 10).
- **Q6. Is 358H essential, useful supporting, or distracting?** **Useful supporting.** It substantiates the other half of the qualification/cost framework, but replay and proposal cannot be separated and the attempted intervention stops before performance (manuscript pp. 6–8).
- **Q7. Is M4 runtime essential, useful supporting, or distracting?** **Useful supporting, but overlong at first read.** Exact profitable Guard execution tests a complete-cost rule; its worse-than-fixed result is honest and informative. It is not needed to establish the B570/358H core and should receive less abstract space (manuscript pp. 1, 7–9).
- **Q8. Exact overstated claims?** **NONE FOUND** in the principal efficacy or causality statements. The title's broad “Consumer Systems” framing and Appendix A4's bare “exact” cells are communication risks rather than explicit unsupported claims; the surrounding text narrows both. “Isolates a sufficient target execution partition” is acceptable because the manuscript immediately disclaims unique kernel and universal cause (manuscript pp. 1, 5, 10; appendix p. 4).
