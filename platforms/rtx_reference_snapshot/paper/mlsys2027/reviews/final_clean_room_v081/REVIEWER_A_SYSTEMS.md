Clean-room review based only on manuscript-v0.8.1.pdf and appendix-v0.8.1.pdf. No repository evidence, prior reviews, source files, handover documents, web search, or experiment records were consulted.

# Reviewer A — Systems / Significance

## Summary

This paper asks when speculative decoding on consumer systems is both admissible under a matched greedy output contract and faster after the full post-prefill execution cost is charged. It organizes evidence from four hardware campaigns, preserving favorable, unfavorable, and correctness-blocked outcomes with their distinct comparators. Two new direct generated-ID studies find that serializing target verification changes RTX agreement from 75/90 to 90/90 pairs, while B570 improves from 60/90 to 78/90 and remains blocked. For B570, the authors freeze a target-partition hypothesis after exposed discovery cases, reserve 24 HumanEval tasks, and predict all 72 complete serialized output sequences with target-only micro-batch-one execution; 12 of those sequences diverge from the reference. A 358H study shows that an isolated NPU drafting advantage does not survive the measured stateful interface, whose replay-plus-proposal call occupies most of the NPU path's time. Separate M4 studies show opposite historical profitability regimes. A prospective M4 continuation guard preserves direct-ID equality and beats target-only on 60 held-out prompts, but fixed speculation is faster in the paired secondary comparison. The strongest contribution is a configuration-scoped, prospectively tested diagnosis of execution-path admissibility; the other cases illustrate why local component opportunity and realized benefit must be evaluated separately.

## Reader comprehension test

**A. What the paper is about (at most three sentences).** Speculative decoding can have promising component measurements yet fail either a matched-output requirement or the integrated post-prefill latency test. The paper studies these boundaries on four consumer systems and prospectively predicts a B570 output trajectory from a controlled target execution partition.

**B. Single strongest scientific contribution.** The frozen B570 target-partition hypothesis predicts 72/72 complete held-out serialized sequences, including 12 sequences with reference divergence, from target-only execution without live drafting (main pp. 3, 5, §§3.1, 5.2; appendix p. 6, §J).

**C. Single strongest empirical result.** The 72/72 complete-sequence prediction is the most discriminating result because it anticipates both equal and unequal reference outcomes, rather than merely reproducing a pass count (main p. 5, §5.2; appendix p. 6, §J). The separate RTX 75/90-to-90/90 direct-ID change is a useful practical result (main pp. 5, 7, §5.1, Fig. 3).

**D. Practical systems lesson.** Qualify the actual execution path against the intended output contract; when it fails, isolate the target partition; on an admissible path, time the full stateful loop and committed output, including correction and replay (main pp. 2, 6, §§2.1–2.4, 6, Fig. 2).

**E. Distinction from a generic consumer-hardware benchmark.** The prospectively frozen, sequence-level target-partition prediction is a falsifiable mechanism study. The paper also separates historical text-derived equality from fresh direct generated-ID qualification and measures a complete draft interface instead of inferring gain from isolated throughput (main pp. 2–3, 5–6, §§2.1–2.4, 3.1, 5.2–5.3).

## Main contribution as I understood it

A prospective B570 experiment shows that target-only micro-batch-one execution is sufficient to predict the complete serialized speculative output trajectory on a reserved workload, thereby locating an execution partition that matters to qualification without claiming a unique kernel or universal cause (main pp. 3, 5, §§3.1, 5.2; appendix p. 6, §J).

## Strongest evidence

The authors distinguish exposed discovery from reserved validation, commit H1 before reserved inference, and commit all 72 predicted sequences before live outcomes. They report 72/72 complete direct-ID matches, 24/24 prompt classifications, and 12/12 first-divergence indices on four divergent prompts; predicted reference equality is only 60/72, so the predictor is doing more than anticipating agreement (main p. 3, §3.1; p. 5, §5.2; appendix p. 6, §J). This is scientifically stronger than a retrospective correlation between a target-forward proxy and latency: the proposed partition made sequence-level predictions that could have failed. The appendix's selection, endpoint, and chronology details materially increase confidence, while the paper appropriately confines sufficiency to the tested B570 stack.

## Systems significance

**Beyond “benchmark your own system.”** Yes. The paper offers an evaluation order tied to distinct failure modes: output-path qualification, target-partition isolation after a failed gate, then complete-cost timing of a qualified path (main pp. 2, 6, §§2.1–2.4, 6, Fig. 2). It does not offer a universal performance model, but it identifies why an apparently good local metric can be an invalid basis for an optimization claim.

**How qualification changes evaluation.** It changes which latency results may be interpreted as usable speedups. The B570 0.3087× result is explicitly diagnostic because only 60/90 historical text-path pairs match; fresh direct-ID B570 serialization remains blocked at 78/90. RTX's fresh 90/90 serialized qualification does not retroactively certify historical serialized timing (main pp. 4–5, Table 2, §4.2, §5.1; p. 7, Fig. 3).

**Consequential nature of held-out prediction.** The 72/72 sequence prediction is consequential within its configuration: it advances the paper from characterizing an anomaly to testing an explanatory, output-level mechanism. Its claim is partition sufficiency on one stack, not backend transfer (main p. 5, §5.2; p. 10, §9).

**Realized-cost evidence.** The 358H result is complementary. Figure 4 connects isolated draft throughput to a measured stateful interface: on the NPU path 58.35% of integrated time is the inseparable replay-plus-proposal call, and the 0.352× prompt-level speedup is exact but slow. It gives the qualification-first lesson a second, independent cost boundary, although it cannot quantify replay alone or a persistence intervention (main pp. 6, 8, §5.3, Fig. 4; appendix p. 1, §D).

## Coherence

I read one systems paper with a central evaluation sequence, rather than four interchangeable device case studies. Sections 2 and 6 and Figure 2 explicitly connect admissibility, target-partition diagnosis, and realized cost (main pp. 2, 6). The B570 predictive study carries the distinctive claim; 358H illustrates a different boundary; M4 supplies contrasting outcomes and a runtime endpoint. The weakest transition is into the extended M4 Guard study: Section 7 properly says it is a separate frozen study and not a second successful optimization intervention, yet its policy detail and Table 3 occupy substantial attention after the mechanism/cost synthesis (main pp. 7–9, §§7.2–7.3, Table 3). The hierarchy is present, but a selective reader may briefly perceive the guard as a fourth contribution despite the introduction's explicit demotion of it (main p. 1, §1).

## Strengths

1. The B570 mechanism experiment has a prospective, sequence-level endpoint with divergent cases, making the explanatory claim meaningfully falsifiable within the tested configuration (main pp. 3, 5, §§3.1, 5.2; appendix p. 6, §J).
2. The paper is unusually disciplined about comparators: historical text-path equality, fresh direct-ID qualification, and diagnostic blocked timings are kept distinct (main pp. 2, 4–5, §§2.1–2.2, 4, 5.1, Table 2; appendix pp. 1, 5–6, §§B, I).
3. The measured 358H loop charges target correction and draft state reconstruction and shows why isolated NPU throughput is insufficient to infer integrated gain (main pp. 2, 6, 8, §§2.3–2.4, 5.3, Fig. 4; appendix p. 1, §D).
4. The M4 studies preserve both profitable and unprofitable regimes without pooling separate sessions or attributing their contrast to a single uncontrolled cause (main pp. 3–5, §§3.1–3.2, 4.1, Fig. 1).
5. The manuscript states important negative boundaries: serialization does not universally qualify a path, the 358H intervention stops at qualification, and Guard is slower than fixed speculation in the paired secondary comparison (main pp. 5, 7, 9, §§5.1, 7.1–7.3, Table 3).

## Major concerns

1. **The integrated systems claim spans different evidence grades.** Most cross-system timing headlines use historical re-tokenized text equality, whereas the stringent direct-ID contract is demonstrated separately on fresh RTX/B570 settings and in the 358H/M4 runtime studies. The paper discloses this, but the central practitioner sequence could still be read as if all speedup outcomes were admissible under one common strict ID contract. A selective systems decision may hinge on whether the historical performance results are sufficiently informative once that boundary is understood (main p. 2, §2.1; pp. 3–5, §3.1, Table 2, §4, §5.1; appendix p. 6, §I).
2. **The strongest mechanism result has a narrow domain.** The 72/72 study covers one B570 platform, model pair, build, greedy setting, and reserved HumanEval workload; 60/72 predictions are reference-equal and the decisive divergent evidence comes from four prompts. This is enough for tested partition sufficiency, but it leaves open how often the same diagnostic method explains qualification failures in other paths. Broader transfer is not claimed and RTX replication is therefore a significance boundary, not missing evidence for the stated B570 claim (main pp. 5, 10, §§5.2, 9; appendix p. 6, §J).
3. **The extra runtime-policy thread risks diluting the central contribution.** Guard beats target-only but does not beat fixed speculation, and its comparison with Always-Spec is a post-study secondary analysis. Section 7 is careful about this, yet the amount of policy machinery could make readers judge the paper as multiple studies whose strongest outcomes do not reinforce one another. The mechanism and cost argument is stronger than any claim about adding control (main pp. 7–9, §§7.2–7.3, Table 3; appendix p. 5, §H).

## Main-paper sufficiency

The core story is understandable from the main paper alone. The first page names the three central contribution dimensions, the direct-ID qualification numbers, and the 72/72 held-out sequence prediction (main p. 1, abstract, §1). Section 3.1 supplies the discovery/reservation/freeze structure, and §5.2 gives the divergent-case checks (main pp. 3, 5). The appendix increases confidence by specifying the exposure audit, deterministic reserved IDs, exact endpoint, and chronology, but none is required to recognize the central claim (appendix p. 6, §J). The main text could state even more plainly that 12 of the 72 predictions concern sequences that diverge from the reference; this appears in §5.2 but is not in the abstract (main pp. 1, 5).

## Practitioner consequence

A practitioner would establish direct generated-ID equivalence for the exact target/reference path intended for deployment before interpreting latency; keep partially mismatching timings diagnostic; isolate target micro-batching when serialized output diverges; then measure the full post-prefill loop and committed-token denominator, including correction, state replay, and transfers where present. This is more operational than “measure carefully,” though the B570 partition diagnostic is not yet a universal debugging recipe (main pp. 2, 5–6, §§2.1–2.4, 5.1–5.3, 6).

## Significance boundary

The strongest established result is complete-sequence predictive sufficiency of target-only micro-batch-one execution for the reserved B570 serialized trajectory, under the frozen tested stack (main p. 5, §5.2; appendix p. 6, §J). The paper does not establish a unique target kernel cause, that UB1 guarantees correctness, a B570 explanation of RTX, general backend portability, a state-persistence speedup, or an incremental benefit of M4 Guard over fixed speculation (main pp. 7, 9–10, §§7.1–7.3, 9).

## Cross-backend transfer check

The paper does not claim that its B570 predictor transfers to RTX: it calls the RTX numerical diagnostic separate and explicitly disavows a shared mechanism (main p. 6, §5.1; p. 10, §9; appendix p. 2, §E). Lack of RTX replication therefore does not invalidate the actual B570 sufficiency result. It does limit how broadly the paper can pitch the partition as a reusable diagnostic across systems, which matters for MLSys significance (main pp. 5–6, §§5.2, 6).

## First-page test: title, abstract, and hierarchy

The title accurately foregrounds execution-path qualification and realized costs, but it does not signal the prospectively predictive B570 mechanism, the paper's most distinctive result. **MINOR** title concern because the abstract immediately supplies the frozen hypothesis and complete-sequence 72/72 endpoint (main p. 1, title, abstract). A reader of the title plus abstract would know that the held-out prediction was frozen and that 72/72 refers to serialized output sequences, although “complete generated sequences” would be still more explicit. The opening sentence stresses speed, and the four-system framing can initially suggest performance characterization; the qualification and prediction sentences prevent that from being the likely final first-page impression (main p. 1, abstract, §1). **MINOR** abstract wording opportunity, not a scientific blocker. The three contribution dimensions appear explicitly in §1. M4 is identified as runtime evidence without demonstrated Guard benefit over fixed speculation, so its role is correctly subordinate at first pass (main p. 1, §1); the later Section 7 length creates the coherence risk described above.

## Misinterpretation test

| Possible interpretation | Classification | Basis in the PDFs |
|---|---|---|
| “This is just a benchmark of several consumer devices.” | POSSIBLE MISREADING | The abstract opens with four-system characterization and Table 2 foregrounds speedups, but §1 explicitly lists a frozen predictive mechanism and §5.2 tests it (main pp. 1, 4–5, abstract, §1, Table 2, §5.2). |
| “The contribution is merely that speculative decoding can be slower.” | CLEARLY PREVENTED | The introduction acknowledges prior positive/negative characterization and locates novelty in qualification plus the 72/72 held-out prediction (main p. 1, §1; p. 9, §8). |
| “UB1 guarantees correctness.” | CLEARLY PREVENTED | The output contract is workload- and path-conditional; §5.2 restricts partition sufficiency to the tested stack, and §9 rejects a universal micro-batch rule (main p. 2, §2.1; p. 5, §5.2; p. 10, §9). |
| “The B570 target partition is proven to be the unique root cause.” | CLEARLY PREVENTED | §5.2 says “sufficient target execution partition,” not a unique kernel; §9 repeats the limitation (main pp. 5, 10, §§5.2, 9). |
| “The B570 result explains RTX.” | CLEARLY PREVENTED | The RTX numerical diagnostic is labeled separate and said not to explain B570; the limitations reject a CUDA/B570 common mechanism (main pp. 6, 10, §§5.1, 9; appendix p. 2, §E). |
| “The M4 Guard improves over fixed speculation.” | CLEARLY PREVENTED | The abstract says fixed speculation is faster; Table 3 and §7.3 report Guard/Always-Spec latency 1.0271 with an interval above parity (main pp. 1, 9, abstract, §7.3, Table 3). |
| “The fresh correctness studies validate all historical timing.” | CLEARLY PREVENTED | §4 and §5.1 explicitly deny retroactive certification, and Fig. 3 separates the studies (main pp. 4–5, 7, §§4, 5.1, Fig. 3; appendix p. 6, §I). |

## Appendix assessment

**Materially increased confidence.** Appendix §J specifies the conservative exposure audit, deterministic reserve selection, target-only harness comparison, freeze ordering, divergence tokens, and validation endpoint (appendix p. 6). Appendix §I clarifies that the new direct-ID studies are qualification studies, not performance measurements, and records their distinct runtime settings (appendix pp. 5–6). Section D confirms complete committed-token accounting and the inseparable replay-plus-proposal measurement (appendix p. 1).

**Possible main-paper promotion.** The main paper already gives the necessary chronology and 12/12 divergence-index result (main pp. 3, 5, §§3.1, 5.2). If a line is available, stating the number of divergent *complete sequences* alongside 72/72 in the abstract would help convey how nontrivial the endpoint is; moving task lists or audit details is unnecessary (appendix p. 6, §J).

**Not needed for the decision.** Exact bootstrap generator/order-statistic conventions, the full target-forward context lookup, and individual reserved task IDs are useful for reproducibility but need not occupy the page-limited main body (appendix pp. 2–3, 6, Tables A1, A3, §J).

## Decision-critical question

What is the intended evidentiary role of the historical speedup rows in the paper's central qualification-then-cost argument, given that their equality checks are text-derived and the fresh direct-ID RTX/B570 studies use different runtime/reference settings? A concise answer should identify which integrated outcomes can legitimately be read as strict-ID-qualified and which remain campaign-specific illustrations (main pp. 2–5, §§2.1–2.2, 3.1, 4, 5.1, Table 2).
