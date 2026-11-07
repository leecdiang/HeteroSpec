Artifact-only review.
Sources consulted:
  - manuscript-v0.8.3.pdf
  - appendix-v0.8.3.pdf

No README, handover, source files, repository evidence, prior reviews, Git history, PR descriptions, experiment logs, or web searches were used.

## 1. Paper summary (150–250 words)

The paper argues that speculative decoding on consumer systems needs three distinct assessments: whether the actual execution path preserves a specified output, whether a blocked trajectory can be predicted by an isolated target path, and whether attractive component measurements survive the cost of an integrated decode loop. It assembles separately frozen case studies on M4, RTX 5070 Ti Laptop, Arc B570, and Core Ultra X7 358H/Arc B390, while warning against treating these as a controlled hardware ranking. Fresh direct-generated-ID qualification on common HumanEval30 task IDs finds RTX batched 75/90 and serialized 90/90 equal pairs; B570 fast and serialized achieve 60/90 and 78/90, so neither B570 path qualifies. In a distinct B570 follow-up, a target-only micro-batch-one predictor selected on exposed discovery cases is frozen before reserved serialized outcomes and matches 72/72 complete generated-ID sequences on 24 reserved prompts, including four reference-divergent prompts. The result supports predictive sufficiency of the tested target partition, not identification of its numerical root cause. On 358H, an NPU's isolated drafting advantage disappears inside a qualified stateful implementation: mean replay-plus-proposal consumes 58.35% of its 27.54-second post-prefill request time. A subsequent intervention fails qualification. A held-out M4 cost Guard preserves direct IDs and beats target-only, but its 1.3114× speedup trails fixed speculation's 1.3469×; the paired secondary analysis finds Guard slower. Historical timing uses a weaker parsed-text comparator and remains explicitly separate. (Manuscript pp. 1, 4–9; appendix pp. 5–8.)

## 2. Thesis (at most three sentences)

Local batching or draft throughput does not itself imply an output-preserving, profitable speculative path. Qualify generated-token behavior on the intended path, use a frozen predictor to probe a blocked trajectory, and measure complete realized round costs before claiming a runtime gain. The paper supports that sequence in a small set of explicitly bounded implementations. (Manuscript pp. 1–2, 5–9.)

## 3. Top contributions, ranked

1. **Frozen, held-out B570 trajectory prediction:** target-only `nubatch=1` matches all 72 serialized complete-ID sequences, including the 12 reference-divergent repetitions; the claim is predictive sufficiency on one configuration. (Manuscript p. 6 §5.2; appendix pp. 6–8 §J.)
2. **Fresh, strict execution-path gates:** RTX serialization qualifies at 90/90 while B570 serialization improves but remains blocked at 78/90; these observations are carefully distinguished from historical performance. (Manuscript pp. 5–6 §5.1, Fig. 3; appendix p. 6 Table A5.)
3. **Stateful cost accounting on 358H:** a direct-ID-qualified CPU/NPU comparison locates measured time in complete target work and a combined replay-plus-proposal call, explaining why isolated draft throughput misleads for this interface. (Manuscript pp. 4, 7 §5.3, Fig. 4; appendix pp. 1–2 §D.)

## 4. Single strongest contribution

The B570 predictor is strongest because it turns a diagnosis into an advance, falsifiable prediction of **entire generated trajectories**, not just agreement counts or a post hoc match at the first mismatch. The discovery cases are explicitly outcome-exposed; a separately chosen 24-prompt reserved set and prediction-file commitment precede its live serialized runs. Especially informative are four prompts where the UB128 reference disagrees yet the UB1 predictor matches the serialized path, including first divergence indices 73, 88, 93, and 103. A trivial predictor that merely repeats the reference would miss these. Evidence comprises the 72/72 primary endpoint, 60/72 reference/live comparison, a chronology with prediction finalization 91.37 seconds before live start, a full-file digest and per-prompt ledger. The PDF does **not** print the 72 arrays or independently establish the chronology; hence it is strong reported evidence with an artifact-only audit limit. Repetitions are stable, leaving 24 distinct prompt trajectories and four distinct divergent examples. (Manuscript pp. 3, 6 §5.2; appendix pp. 6–8 §J, Tables A6–A7.)

## 5. Single strongest empirical result

On the reserved B570 follow-up, **72/72 complete predictor-to-live generated-token-ID sequences** match across 24 prompts × three repetitions, whereas the reference matches live in **60/72**; all four reference-divergent prompts are predicted divergent and their 12 first-divergence repetition indices match. All 24 ledger rows report length 128, so “complete” means the frozen 128-committed-token endpoint, not unbounded continuation. (Manuscript p. 6 §5.2; appendix pp. 7–8 Tables A6–A7.)

## 6. Strengths (at most five)

1. The H/Q/P distinction explicitly prevents parsed-text equality, fresh direct-ID qualification, and predictor-to-live agreement from being silently pooled. (Manuscript p. 2 §2.1.)
2. The B570 reserved study has a visible selection rule, exposed/disjoint discovery designation, freeze chronology, falsifiable all-sequences threshold, and divergent cases. (Manuscript pp. 3, 6; appendix pp. 6–8 §J.)
3. The cost accounting counts committed correction/bonus progress, includes replay in the draft-side measured call, distinguishes aggregate arithmetic ratios from prompt geometric means, and avoids an invented replay-only estimate. (Manuscript pp. 2, 7; appendix pp. 1–2 §D.)
4. Negative results are retained: B570 remains blocked, 358H intervention stops at qualification, and M4 Guard loses to fixed speculation in a paired secondary analysis. (Manuscript pp. 6, 8–9.)
5. Related Work credits earlier consumer-system losses, numerical variation, heterogeneous placement, cost modeling, and adaptive control instead of presenting each topic as new. (Manuscript p. 9 §8.)

## 7. Weaknesses (at most five)

1. **MAJOR — significance/scope:** The most novel predictor mechanism is demonstrated on one B570 Vulkan stack, one model pair, one `k`, one 128-ID HumanEval endpoint, and 24 reserved prompts. All repeated outcomes are stable and only four prompts are reference-divergent. This is a convincing local existence result, but transfer and prevalence are unknown. (Manuscript pp. 6, 10; appendix pp. 6–8.)
2. **MODERATE — missing evidence:** The PDFs provide hashes, a chronology table, and a per-prompt ledger, but no full predicted/live arrays or independently inspectable temporal proof within these two artifacts. A reader can assess the design and reported result, not independently recheck every ID or the freeze order from the PDFs alone. The chronology is appropriately attributed to recorded study evidence, not to the hash itself. (Appendix pp. 7–8 §J.)
3. **MODERATE — clarity:** The abstract and first introduction page are highly numerical, naming four platforms, multiple denominators, Guard, and historical versus prospective comparisons before a compact central visual or simple example. The primary result is present, but the argumentative center competes with later runtime outcomes. (Manuscript p. 1.)
4. **MODERATE — missing comparison:** Fresh RTX/B570 direct-ID gates have no paired fresh latency endpoint, and historical cost measurements use different settings/comparators. This blocks a quantified correctness-versus-cost tradeoff for the very paths that motivate the title. The manuscript states this boundary clearly. (Manuscript pp. 5–6 §5.1, Fig. 3; appendix p. 6 §I.)
5. **MINOR — clarity:** Figure 2 mostly restates a short evaluation sequence; appendix Tables A4 and A7 occupy sparsely filled pages (especially appendix pp. 3–4 and 7–8), making an already dense evidence hierarchy harder to navigate. (Manuscript p. 5; appendix pp. 3–4, 7–8.)

## 8. Claim–evidence audit

| Claim | Judgment | PDF evidence and limit |
|---|---|---|
| A. Execution-path qualification as prerequisite | **SUPPORTED WITH CAVEAT** | Direct-ID gate and blocked/qualified outcomes are explicit; the 90/90 rule is a chosen strict contract for the frozen workload, not proof of universal correctness. Manuscript pp. 2, 5–6 §§2.1, 5.1; appendix p. 6 Table A5. |
| B. RTX direct-ID | **WELL SUPPORTED** | 75/90 batched and 90/90 serialized, 25/30 and 30/30 prompt equality respectively, same frozen HumanEval30 study protocol; no fresh speed claim. Manuscript pp. 5–6 §5.1/Fig. 3; appendix pp. 5–6 §I/Table A5. |
| C. B570 direct-ID | **WELL SUPPORTED** | 60/90 fast and 78/90 serialized; neither reaches 90/90, with no discarded mismatch. Separate 60/72 reserved comparison is not substituted for this study. Manuscript pp. 5–6; appendix p. 6 Table A5 and p. 7 Table A6. |
| D. B570 target-partition mechanism | **SUPPORTED WITH CAVEAT** | UB1 target-only matches 36/36 exposed discovery and frozen predictions match 72/72 reserved live outputs, including 12 divergent repetitions. This establishes trajectory reproduction by this path, not a unique operation, causal kernel, or general UB1 rule; “mechanism” is a predictive/path-level term. Manuscript p. 6 §5.2; appendix pp. 6–8 §J. |
| E. 72/72 held-out prediction | **SUPPORTED WITH CAVEAT** | Reported 72/72 complete-ID endpoint, 24 task ledger rows, SHA-256 prediction-file digest, recorded chronology. The PDFs omit raw arrays and independently verifiable timestamps; 72 observations are three stable repeats per 24 prompts. Manuscript p. 6 §5.2; appendix pp. 7–8 Tables A6–A7. |
| F. 358H realized cost | **WELL SUPPORTED** | Direct-ID 90/90 on both paths, post-prefill totals 9.58 s baseline, 13.25 s CPU and 27.54 s NPU; 87.34% CPU target-side and 58.35% NPU combined replay/proposal. No replay-only or persistence savings identified. Manuscript pp. 4, 7 §5.3/Fig. 4; appendix pp. 1–2 §D. |
| G. M4 runtime | **SUPPORTED WITH CAVEAT** | Guard and fixed paths each 180/180 direct-ID; target/Guard 1.3114 [1.2487, 1.3787], target/fixed 1.3469 [1.2867, 1.4088]; post-study paired Guard/fixed latency 1.0271 [1.0130, 1.0436]. The paired contrast is secondary, the Guard freeze has a recovered metadata defect, and no incremental control gain is shown. Manuscript pp. 8–9 §7/Table 3; appendix p. 5 §H. |

## 9. Focused 72/72 audit

| Question | Answer | Explanation |
|---|---|---|
| Is the result visible to a reviewer? | **PARTIAL** | Main p. 6 reports counts and process; appendix pp. 7–8 show digest, timing table, four divergent examples and all 24 per-task outcome/digest rows. They do not display complete arrays or permit direct ID-by-ID recomputation from these PDFs. |
| Are complete generated-token-ID sequences the specified unit? | **YES** | The endpoint includes length and all generated IDs through 128 committed tokens or earlier inclusive EOG, with prompt IDs excluded and no dropped mismatch; predictor/live equals 72/72. “Complete” remains cap-relative; every displayed live length is 128. Appendix pp. 6–8 §§I–J. |
| Were predictions frozen before live outcomes? | **PARTIAL** | The recorded chronology puts the 72-array finalization at T0+1722.38 s, first live outcome at T0+1813.75 s, with no post-freeze edits reported. A content digest establishes identity only; the PDFs cannot independently authenticate the temporal records. Appendix p. 7 §J. |
| Is discovery separate from reserved validation? | **YES** | Twelve outcome-exposed discovery prompts supply 36/36; the audit excludes 31/164 previously B570-associated tasks and hash-selects 24 from 133 eligible. “No known exposure” is explicitly limited to audited records. Manuscript pp. 3, 6; appendix p. 6 §J. |
| Is the prediction falsifiable? | **YES** | H1/H2/stop tree, precommitted IDs, arrays, endpoint, exact 72/72 criterion, and no partial-match substitute give a concrete failure condition. The four divergent prompts make simple reference replay an inadequate explanation. Appendix pp. 6–8 §J. |
| Does interpretation avoid a unique-cause leap? | **YES** | It repeatedly excludes a particular numerical kernel, a universal UB1 rule, a shared CUDA/B570 cause, and a production certificate. Manuscript pp. 6, 10; appendix p. 6 §J. |

## 10. Historical versus fresh evidence separation

**MOSTLY CLEAR.** The abstract says “fresh direct-ID,” the introduction warns that it does not certify historical timing, §2.1 defines H/Q/P, Table 2 labels historical rows “Text-path,” Figure 3 explicitly separates historical proxy from fresh direct-ID, and §9 repeats the limit. A rushed reader can still carry “90/90” from RTX serialized qualification to the older 0.404×/0.650× timing rows or confuse historical M4 90/90 with the new M4 runtime 180/180. The front page could spell out that the historical RTX/M4 speed ratios have no direct-ID certification under their historical configurations. (Manuscript pp. 1–2, 4–6, 9–10; appendix pp. 1, 6.)

## 11. Actual population and exclusions

**ACCEPTABLE SCOPE LIMITATION**, with a material significance cost. The studies cover single-request post-prefill greedy decoding of Qwen3-8B Q8_0 with a 0.6B draft on frozen M4/RTX/B570 native stacks, and a differently quantized symmetric INT4 OpenVINO draft on 358H. Historical representative 24Q and HumanEval30 use distinct sessions and parsed-text comparators; fresh gate experiments use HumanEval30, `k=2`, three repetitions and differing backends, references and contexts. The predictor uses 24 reserved HumanEval tasks selected after a 31/164-task B570-association exclusion, all observed lengths 128, and one B570 configuration. The M4 Guard uses 40 calibration, 16 qualification and 60 held-out prompts split between HumanEval and Spec-Bench, fixed `k=2`. These are not a random population sample, a serving workload, general hardware ranking, functional code test, or cross-backend transfer result. The manuscript identifies these exclusions; the title's plural “consumer systems” remains defensible for a set of case studies, but its broad phrasing can invite a broader generalization. (Manuscript pp. 3, 8–10; appendix pp. 5–8.)

## 12. First-page test

**Three-minute impression from title, abstract, and first introduction page only:** This is a careful systems measurement paper about output qualification and realized speculative-decoding cost, with a distinctive 72/72 frozen B570 prediction and a set of negative/qualified platform results. The abstract already states the major non-causal limitation of that prediction and the M4 policy's negative incremental result. The introduction ranks three contributions by the bottom of page one. (Manuscript p. 1.)

**Risk of generic “benchmark your own system” reading:** Moderate. The title foregrounds a broad measurement principle, and the abstract lists several hardware outcomes. A hurried reviewer might mistake the contribution for a collection of expected device-specific slowdowns until reaching the “frozen target-only predictor” sentence and the contribution list. Opening with one sentence on the counterintuitive reference-divergent B570 predictions would sharpen the hook. (Manuscript p. 1.)

**72/72 visibility and novelty timing:** The number is in abstract lines 14–16 and intro lines 40–44; novelty appears early. The terms “target-partition sufficiency,” “direct-ID,” and “reserved live outcomes” are meaningful but dense before their operational definitions on pp. 2 and 6. The reader sees *what* happened immediately and *why matching divergent full trajectories is a stronger test* only later. (Manuscript pp. 1–2, 6.)

## 13. Figures and tables

| Exhibit | Necessary, readable, informative? | Redundancy or misleading risk |
|---|---|---|
| Main Table 1 (p. 3) | Necessary map of hardware, backend, draft placement and distinct evidence scopes; readable. | Could add explicit “fresh gates differ” footnote because its runtime build rows describe historical campaigns. |
| Figure 1 (p. 4) | Informative, compact depiction of the two M4 speed regimes and intervals, with separate-study warning. | A quick visual could imply workload-only causality; caption explicitly rejects that inference. |
| Table 2 (p. 5) | Necessary quantitative inventory and unusually helpful Endpoint/Class columns. | The B570 60/90 text-path row beside negative timing can still be quoted out of context; “Diag.” is too abbreviated for a headline table. |
| Figure 2 (p. 5) | Readable, but **not necessary**: a generic flow of local opportunity → gate → cost with a blocked branch. | Restates text and uses valuable space that could elevate the B570 freeze/validation story or definition of complete sequence. |
| Figure 3 (p. 6) | Necessary visual separation of historical proxy and fresh output gate; panel B makes 90/90 threshold immediately apparent. | Panel A aggregates unmatched context cells, and markers/labels are small at page scale. Caption correctly denies a matched cost–qualification experiment. |
| Figure 4 (p. 7) | Necessary and the clearest cost-mechanism illustration; readable throughput dots and timing bars. | The hatched target side and combined replay/proposal are properly distinguished. Percent shares plus many explanatory caption sentences make the caption long, but prevent a replay-only causal inference. |
| Main Table 3 (p. 9) | Necessary for the M4 runtime verdict and the post-study paired contrast; concise. | “Guard/oracle” is latency regret while first rows are speedups, a unit-direction switch the caption explains; could visually separate the oracle row more decisively. |
| Appendix A1–A2 (p. 2) | Useful exact estimator and sensor-boundary lookup, readable. | Fine in supplement. |
| Appendix A3–A4 (pp. 3–4) | A3 is useful exact proxy context lookup; A4 is readable endpoint inventory. | A4 substantially duplicates main Table 2 and lands alone on a half-empty page after a large blank region; compress or omit. |
| Appendix A5–A6 (pp. 6–7) | Necessary concise direct-ID gate and reference-vs-predictor comparison. | Repeat main Figure 3B and §5.2, but worthwhile as a reproducibility lookup. |
| Appendix A7 (p. 8) | Important ledger of every reserved task, match count, length and divergence; readable when enlarged. | Half-page top whitespace; 12-character per-task digests do not substitute for full arrays. |

## 14. Related Work, from the PDFs only

The discussion gives fair credit to the algorithm, consumer Apple-silicon wins and losses (Chordiya), conditional cost models (Kim), verification dominance, edge/cloud profitability, heterogeneous CPU/GPU/NPU placement, numerical path dependence and deterministic inference, and adaptive control. It explicitly says slowdowns/correctness gating, numerical sensitivity, state reuse and adaptive control are established. The claimed differentiation is narrower: prospective captured-ID path gating on RTX/B570, frozen prediction of complete B570 serialized trajectories, and direct accounting of one replay-plus-proposal interface. This is reasonable **as the authors characterize the cited literature**; I did not inspect the cited works independently. The one unsafe novelty impression is the phrase “target-partition mechanism” if taken to identify the underlying numerical operation; the paper itself consistently disclaims that. A tighter related-work comparison of what the prior batch-shape argmax observations *did not predict* would make the novel predictive test more legible. (Manuscript pp. 1, 6, 9 §8; appendix pp. 2, 6–7.)

## 15. Single acceptance objection

If I were arguing against acceptance, I would say... the highest-novelty 72/72 result is an excellently structured but single-backend, 24-prompt, cap-128 trajectory reproduction whose full arrays and freeze evidence cannot be inspected inside the submitted PDFs, while the fresh gates lack matching latency and the remaining hardware/runtime observations are either historical under weaker comparators or negative implementation-specific case studies. The paper is candid, but a conference-level systems claim may need one more independently varied setting to show significance beyond a local B570 path. (Manuscript pp. 6, 9–10; appendix pp. 6–8.)

## 16. Single acceptance argument

If I were arguing for acceptance, I would say... the paper contributes a useful empirical method and a rare prospective, exact-trajectory test on a correctness-blocked path: a target-only execution partition predicts 72/72 serialized IDs including reference divergences, while 358H measured costs and the M4 Guard failure show why qualification and full-loop accounting must be separate decisions. The carefully bounded negative results and explicit H/Q/P evidence classes are themselves valuable for systems researchers. (Manuscript pp. 1–2, 6–9; appendix pp. 6–8.)

## 17. Localized revisions

**MUST FIX**

- In the abstract and §5.2 (manuscript pp. 1, 6), add an immediately understandable one-sentence example: “On four reserved prompts the baseline reference differs, yet a frozen target-only micro-batch-one run predicts the serialized output, including its first divergence position.” This explains why the 72/72 is more than repeated reference agreement.
- In §5.2 or Table A7 caption (manuscript p. 6; appendix p. 8), explicitly state that all 24 reserved outputs hit the 128-token cap and that the 72 runs represent 24 repeat-stable prompt trajectories. Keep the 72/72 execution-level endpoint, but let readers see the independent task diversity promptly.
- In §J (appendix p. 7), retain the distinction between the prediction-file content hash and the recorded temporal chronology, and specify a reviewer-accessible method for examining the full generated arrays and timestamps if the venue permits a supplement/artifact. The PDF-only record does not itself prove timing or permit sequence-by-sequence checking.

**SHOULD FIX**

- Replace the general Figure 2 on manuscript p. 5 with the compact discovery → freeze → reserved validation schematic now in §5.2 on p. 6, moving the 36/36 versus 72/72 and 60/72 distinction closer to the central contribution.
- Add a sentence directly below Table 2 on manuscript p. 5: historical M4/RTX timing ratios are qualified only by their text-path comparator and have no matched fresh direct-ID latency experiment. The caveat exists elsewhere, but this is the likely screenshot readers will reuse.
- Reword the first paragraph of §7 (manuscript p. 8) to preface Guard as a test of the framework with a negative incremental result, keeping it visually subordinate to the central predictor. Table 3 should use clear subheadings for target-relative speedup, oracle regret, and Guard/fixed latency.
- In Related Work §8 (manuscript p. 9), compare the paper's *precommitted full-trajectory prediction* directly with the prior target-only batch-shape observations, instead of relying mainly on a broad list of established topics.

**OPTIONAL**

- Expand “Second.” and “Diag.” in Table 2 (manuscript p. 5), and consider reducing the Appendix A4 duplication to save the nearly empty appendix p. 4.
- Add a small key to Figure 3A's marker shapes in the figure area, because the caption currently carries the path encoding. (Manuscript p. 6.)

## 18. Recommendation

**WEAK ACCEPT.**

## 19. Confidence

**4/5.** The PDFs let me assess framing, reported results, protocol, and many internal consistency checks; I cannot independently recompute raw-ID equality or authenticate the freeze from the PDFs alone.

## 20. Decision rationale (100–200 words)

The paper's strongest novelty is a prediction experiment rather than another consumer-hardware speed table: a frozen target-only micro-batch-one path reproduces complete serialized B570 trajectories, including reference-divergent examples. Its explicit 72/72 criterion, reserved task selection, digest, chronology and ledger make that claim substantially more rigorous than a retrospective numerical-path anecdote, subject to the PDF-only audit limits. Fresh RTX/B570 direct-ID gates and complete 358H cost accounting reinforce a coherent evaluation discipline. The authors responsibly distinguish historical parsed-text timing from direct IDs, present the negative Guard comparison, and avoid claiming a unique kernel cause. Significance is constrained by one model family, small and repeat-stable reserved set, one predictive backend and no transfer test; the fresh qualification paths also lack matching fresh latency. Communication is accurate but dense on page one, and a generic workflow figure underplays the paper's most distinctive prediction. On balance, the unusually careful, falsifiable local result merits a weak accept, with scope and the strength of cross-system inference clearly bounded. (Manuscript pp. 1–2, 5–10; appendix pp. 6–8.)

## Special Questions

**Q1. Central identity:** **E — coherent B+C+D.** Execution-path qualification (B) structures the paper; frozen B570 predictive mechanism (C) is its most distinctive new test; 358H realized heterogeneous state-interface cost (D) shows why correctness alone does not yield speed. It is not simply A, a hardware ranking. (Manuscript pp. 1–2, 5–9.)

**Q2. More than “benchmark your own system”?** **CLEARLY YES.** The precommitted full-ID trajectory test on a path that differs from its reference makes a specific, falsifiable mechanism-level prediction. General applicability remains untested. (Manuscript p. 6; appendix pp. 6–8.)

**Q3. Frozen 72/72 publication importance?** **YES.** The reservation and chronology turn a plausible after-the-fact explanation into prospective evidence, and the four divergent cases challenge a trivial reference-echo hypothesis. (Manuscript p. 6; appendix pp. 6–8.)

**Q4. Would a second-backend transfer change my recommendation?** **MAYBE.** A genuinely frozen test on an independently varied backend, with failure also reported, would materially improve significance; the result and quality of isolation would determine whether the weak accept becomes firmer. (Current limits: manuscript p. 10.)

**Q5. Does no transfer invalidate current claims?** **NO.** The claims are expressly path/runtime scoped, and sufficiency on the tested B570 path does not logically require transfer. It limits generality. (Manuscript pp. 6, 10.)

**Q6. 358H role:** **Useful supporting.** Qualified post-prefill timing and the 58.35% combined replay/proposal region anchor the realized-cost half of the argument, without proving a state-persistence intervention's benefit. (Manuscript pp. 4, 7–8.)

**Q7. M4 role:** **Useful supporting.** The positive target-relative yet negative fixed-policy comparison is a sober example of framework-guided runtime testing; its many details pull attention from the central B570 result, so compress if space is tight. (Manuscript pp. 8–9.)

**Q8. Exact overstated claim examples:** **NONE FOUND** in the central scientific claims. The potentially broad phrases “target-partition sufficiency” and “state interface consumes an isolated draft-device advantage” are repeatedly qualified to the tested path/interface and do not assert a unique numerical cause or intrinsic NPU deficiency. The title's breadth and abstract density are presentation risks, not demonstrably false claims. (Manuscript pp. 1, 6–7, 10.)
