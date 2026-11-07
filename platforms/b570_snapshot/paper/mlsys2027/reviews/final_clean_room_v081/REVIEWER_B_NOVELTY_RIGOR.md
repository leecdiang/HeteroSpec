Clean-room review based only on manuscript-v0.8.1.pdf and appendix-v0.8.1.pdf. No repository evidence, prior reviews, source files, handover documents, web search, or experiment records were consulted.

# Reviewer B — Novelty / Rigor

## Summary

The paper studies whether speculative decoding on four consumer systems preserves the intended generated-token sequence and whether favorable component measurements translate into faster post-prefill decoding. It separates historical timing campaigns, whose M4/RTX/B570 equality checks reconstruct tokens from CLI text, from new direct-ID qualification studies. In the latter, serialization raises RTX agreement from 75/90 to 90/90 but raises B570 only from 60/90 to 78/90, leaving B570 blocked. A B570 follow-up tests whether target-only execution with micro-batch one can predict the serialized path. After exposed discovery cases, the authors freeze a predictor and a separately selected 24-task set; all 72 complete live sequences match the predictions, including 12 divergent repetition pairs across four tasks. The result identifies a sufficient target execution partition for the tested trajectory, without identifying a kernel or a universal cause. On a 358H, isolated NPU draft throughput does not survive the measured stateful interface: integrated CPU and NPU draft paths are exact but slower than target-only. Separate M4 studies show opposite historical timing regimes, and a held-out M4 continuation Guard is exact and faster than target-only but slower than fixed speculation. The paper frames path qualification and complete realized cost as prerequisites for interpreting gains. Its causal and portability claims are appropriately narrower than its platform count might first suggest.

## First-pass notes and comprehension test

Recorded after reading the main manuscript in full and before opening the appendix: the problem is whether an attractive physical speculative path both preserves generated IDs and yields integrated decode gains. I understood three contributions: new RTX/B570 direct-ID path qualification, a frozen B570 target-partition predictor on reserved tasks, and measured 358H state-interface cost. The strongest result was the 72/72 complete-sequence prediction. The requested belief is that qualification and realized state costs must be established before local batching or draft speed is treated as an optimization (main pp. 1–2, §§1–2; pp. 5–6, §5).

A. The paper evaluates speculative decoding as an execution path with an output contract and full post-prefill cost. It uses targeted studies to separate correctness-blocked paths, a held-out B570 trajectory predictor, and stateful integration losses (main pp. 1, 5–6, §§1, 5).

B. The single strongest scientific contribution is the prospectively frozen B570 target-only micro-batch-one predictor of complete serialized speculative output sequences on reserved tasks (main pp. 3, 5, §§3.1, 5.2).

C. The single strongest empirical result is 72/72 complete predicted sequences matching live B570 output, including all 12 divergent repetition pairs on four tasks (main p. 5, §5.2; supplement p. 6, §J).

D. Qualify the exact intended path first; if it fails, test the target execution partition before blaming live drafting, and then measure complete realized cost on a qualified path (main pp. 1, 6, §§1, 6).

E. The reserved complete-sequence prediction is an outcome-predicting mechanism test, whereas a generic multi-device benchmark would report performance and correctness counts without a frozen, falsifiable trajectory prediction (main pp. 3, 5, §§3.1, 5.2).

## Strongest claim

The strongest claim is that “target-only micro-batch one thus reproduces the tested serialized trajectory without live draft computation” and isolates a **sufficient** target execution partition (main p. 5, §5.2). The 36/36 exposed discovery matches, prospectively committed 72 predictions, 72/72 live matches, and matched first-divergence positions support sufficiency for this tested stack and reserved set (main pp. 3, 5, §§3.1, 5.2; supplement p. 6, §J). They do not identify the underlying numerical operation, show that partition is the unique cause, or establish a rule for RTX or other backends. The paper generally states those limits explicitly (main pp. 5, 10, §§5.2, 9).

## Predictive-mechanism audit

| Chronology step | Classification | PDF evidence and limit |
| --- | --- | --- |
| Discovery | CLEAR | Twelve outcome-exposed tasks and 36 serialized sequences are named as exploratory; H1 matches all 36 (main p. 5, §5.2; supplement p. 6, §J). |
| Hypothesis freeze | CLEAR | The H1/H2 tree selects H1 after 36/36, and H1 is committed before reserved inference; H2 is not built (main pp. 3, 5, §§3.1, 5.2; supplement p. 6, §J). |
| Reserved set | PARTIALLY CLEAR | The audit excludes 31/164 tasks and SHA-256 ranking selects 24 from 133 eligible; IDs are listed. “No known exposure” is limited to retained records, which the PDFs cannot independently verify (main p. 3, §3.1; supplement p. 6, §J). |
| Predictions frozen | CLEAR as reported | The paper says all 72 complete arrays and their digest were committed before the first live outcome, with no edits; the digest and underlying timestamped artifacts are not printed in the PDFs (main pp. 3, 5, §§3.1, 5.2; supplement p. 6, §J). |
| Live outcomes | CLEAR as reported | Three live repetitions on each of 24 reserved tasks, 72/72 complete matches, 24/24 classes, and 12/12 divergent first indices are specified (main p. 5, §5.2; supplement p. 6, §J). |
| Validation | PARTIALLY CLEAR | The supplement reports 5,681 independent input, output, hash, endpoint, and chronology checks. The PDF gives checks and selected IDs/tokens, but no independently inspectable prediction ledger; this is a limit of paper-only review, not evidence of a violation (supplement p. 6, §J). |

## Held-out evidence audit

The endpoint was falsifiable as presented: success required **all** 72 complete predictor-to-live ID arrays, not merely reference-equality classes or selected divergence tokens; a single mismatched sequence would fail it (main p. 5, §5.2; supplement p. 6, §J). Separation is credible within the documented audit: 31 recorded B570-associated tasks are excluded, deterministic selection fixes 24 reserved IDs, and the manuscript explicitly disclaims proof about unavailable records (main p. 3, §3.1; supplement p. 6, §J). Repetitions are stable, however, so the 72 comparisons comprise 24 task trajectories, of which only four differ from the reference. The reported 60/72 reference equality is a useful trivial-predictor comparator; the scientific increment is predicting those four divergent trajectories and their locations (main p. 5, §5.2; supplement p. 6, §J). The manuscript appropriately distinguishes this prediction from a universal mechanism (main pp. 5, 10, §§5.2, 9).

## Sufficiency versus causality

The distinction is mostly consistent. The main paper states “sufficient target execution partition, not a unique kernel, universal rule, or RTX mechanism” (p. 5, §5.2), and the limitations repeat that the work does not prove an architecture-wide cause (p. 10, §9). The sentence “a controlled B570 follow-up isolates target execution partition as a sufficient predictor” (p. 1, §1) is defensible, but “isolates” can suggest stronger causal exclusion than the observed equivalence of two trajectories warrants. The 358H controls also reproduce a divergence without live NPU drafting, yet explicitly leave the responsible floating-point/backend operation unidentified (main p. 7, §7.1). I would preserve the sufficiency claim and avoid expanding “isolation” into root-cause language.

## Historical / fresh evidence separation

The separation is unusually explicit: main §2.1 labels historical M4/RTX/B570 comparisons as re-tokenized CLI-text comparisons; Table 2 and Figure 1 repeat that label; §5.1 and Figure 3B identify the new direct-ID qualification endpoints; §5.2 isolates the later B570 prediction; and §9 denies retroactive certification (main pp. 2, 4–5, 7, 10). The supplement documents the distinct endpoint definitions in §§B and I (pp. 1, 5–6). A reader scanning Table 1 and Table 2 could still treat “matching pairs” and “Primary” as direct-ID-qualified performance, especially for historical M4, because the table needs its caption to correct that interpretation (main p. 4, Tables 1–2). Figure 3 is better protected by its two-panel caption (main p. 7). The separation is adequate for a careful reader, but broad synthesis must keep the historical comparator qualification attached.

## Novelty

The distinctive part is the advance from correctness counts to a prospectively frozen **complete-output trajectory** prediction, including residual mismatches, under a specified target-partition intervention (main p. 5, §5.2). That is a stronger diagnostic than observing that speculation can alter greedy output. Direct-ID qualification on two paths and the 358H full-cost decomposition make the diagnostic consequential for system evaluation (main pp. 5–6, §§5.1–5.3). The established or incremental pieces are slowdown on consumer systems, batching-dependent numerical variation, heterogeneous draft placement, profitability accounting, and adaptive continuation; the paper itself cites close prior art for each and disclaims novelty in those phenomena (main pp. 9–10, §8). Its M4 Guard is a useful negative control, not a demonstrated control improvement (main p. 9, Table 3 and §7.3).

## Major concerns

1. **The predictive result is narrow relative to its prominence.** All reserved cases use one B570 stack, one model pair, one HumanEval task family, and a single target partition; only four of 24 task trajectories are divergent, with three stable repetitions each (main p. 5, §5.2; supplement p. 6, §J). The claim survives this limitation as a configuration-scoped sufficiency result. Whether that scope carries a broad systems novelty argument is the key judgment. The paper does **not** claim cross-backend transfer, so missing RTX replication is a scope limitation rather than a validity flaw (main pp. 5, 10, §§5.2, 9). Broader transfer would strengthen significance, but is not required to substantiate the actual claim.

2. **The freeze and exposure protection are reported rather than independently inspectable in the PDFs.** The main paper and supplement give the selection rule, task IDs, sequence counts, chronology, and validator count, but the prediction digest, committed arrays, and dated freeze evidence remain outside the PDFs (main p. 3, §3.1; supplement p. 6, §J). Paper-only review can assess the design but cannot verify the crucial temporal ordering. This is not an allegation of leakage; it limits evidentiary confidence in the unusually strong prospective framing.

3. **The historical performance synthesis rests on a weaker output comparator than the new qualification claims.** Table 2 headlines opposite M4 regimes, secondary RTX losses, and B570 diagnostic timing, while §2.1 and §9 say those historical equalities derive from parsed CLI text and cannot establish the stricter generated-ID contract (main pp. 2, 4, 10, §§2.1, 4, 9). The paper is candid, but the breadth of “path-qualified” performance evidence is correspondingly narrower than a quick reading of four-platform results suggests.

4. **The 358H explanation is cost localization, not a demonstrated state-reuse remedy.** Figure 4 and §5.3 time replay plus proposal jointly, and §7.1 reports that the persistence-oriented intervention did not qualify for formal performance testing (main pp. 6–8, §§5.3, 7.1; Figure 4). The result convincingly diagnoses this interface as expensive; it does not isolate replay-only cost or establish that removing replay would make the NPU path profitable. The manuscript acknowledges this, but it constrains the third claimed contribution.

## Most damaging alternative interpretation

The harshest plausible reading is that the paper combines known consumer-device slowdowns, known batch-sensitive greedy differences, and one same-stack target-only reproduction that predicts mostly reference-equal stable prompts, without a new general mechanism or deployable control. The manuscript counters this **partly**: the 72/72 frozen complete-sequence endpoint includes four residual divergent task trajectories and first-divergence indices, a more demanding result than benchmark counts (main p. 5, §5.2; supplement p. 6, §J). It also explicitly acknowledges the prior phenomena (main p. 9, §8). It cannot counter the observation that the predictor's demonstrated scope is one configuration. That is a significance boundary, not a refutation of the held-out result.

## Misinterpretation test

| Possible reviewer takeaway | Classification | Basis |
| --- | --- | --- |
| “This is just a benchmark of several consumer devices.” | POSSIBLE MISREADING | The title and four-system/Table 2 framing invite a fast scan, although the abstract and §1 foreground the 72/72 predictor (main pp. 1, 4, title, abstract, Table 2). |
| “The contribution is merely that speculative decoding can be slower.” | POSSIBLE MISREADING | Figure 1 and Table 2 devote space to gains/losses, but §1 and §8 explicitly identify slowdown as prior art and prediction as the distinction (main pp. 1, 4–5, 9, §§1, 4, 8). |
| “UB1 guarantees correctness.” | POSSIBLE MISREADING | UB1 reproduces this tested B570 trajectory, yet §2.1 and §9 say admissibility is workload/configuration conditional and the predictor is not a certificate (main pp. 2, 5, 10, §§2.1, 5.2, 9). |
| “The B570 target partition is proven to be the unique root cause.” | CLEARLY PREVENTED | §5.2 and §9 explicitly say sufficient, not unique kernel or universal cause (main pp. 5, 10). |
| “The B570 result explains RTX.” | CLEARLY PREVENTED | §5.2 expressly excludes an RTX mechanism; §9 excludes a CUDA/B570 common mechanism (main pp. 5, 10). |
| “The M4 Guard improves over fixed speculation.” | CLEARLY PREVENTED | The abstract and Table 3 report fixed speculation ahead, with Guard/Always-Spec latency 1.0271 [1.0130, 1.0436] (main pp. 1, 9, abstract, Table 3). |
| “The fresh correctness studies validate all historical timing.” | CLEARLY PREVENTED | §2.1, §5.1, Figure 3, and §9 directly deny retroactive certification (main pp. 2, 5, 7, 10). |

## Title, abstract, and first page

The title accurately signals execution-path qualification and realized cost, but does not name the paper's strongest distinctive evidence: prospectively frozen prediction. The abstract does identify a frozen reserved B570 follow-up and says the 72/72 endpoint concerns “serialized output sequences,” making a held-out predictive mechanism visible within three minutes (main p. 1, title and abstract). “All 72 serialized output sequences” is close to, but less explicit than, “72 complete generated-token-ID sequences”; the latter would prevent confusion with 72 token positions. The opening sentence and four-system characterization can initially suggest a performance benchmark, but the abstract corrects it by its middle and §1 repeats the three-part contribution hierarchy. **Severity: IMPORTANT** for making the best novelty argument unmistakable, not blocking comprehension.

## Contribution structure and cross-backend boundary

The three stated dimensions appear verbatim in §1 and form the sequence in Figure 2 and §6: qualification, B570 prediction, and realized 358H cost (main pp. 1, 6, §§1, 6; Figure 2). M4 is presented as runtime evidence in §7, with no incremental Guard advantage, rather than as a fourth successful contribution (main pp. 7–9, §7; Table 3). Some diffuseness remains because historical M4 profitability takes §4.1 and Figure 1 before the predictive result appears in §5.2, and the Guard occupies a full later section despite its negative comparison (main pp. 4–5, 7–9). Still, the hierarchy is recoverable from the main paper. No cross-backend transfer is claimed for B570; lack of RTX replication should be weighed for general significance, not converted into an internal-validity objection (main pp. 5, 10, §§5.2, 9).

## Appendix use and main-paper sufficiency

The main paper alone makes the problem, three contributions, 72/72 endpoint, comparator separation, and narrow causal claim understandable (main pp. 1–2, 5–6). The appendix materially increases confidence by giving the 31/164 exclusion rule, deterministic ranking, 24 reserved task IDs, four divergent task IDs and token pairs, and explicit freeze order (supplement p. 6, §J). It also resolves endpoint details for fresh qualification and historical comparators (supplement pp. 1, 5–6, §§B, I). The main text already has the acceptance-critical numbers and caveats; I would not move full ID lists or bootstrap ordering into it. The detailed energy-boundary tables, full historical context lookup, and M4 finite-bootstrap conventions are useful archival material but not necessary to decide the novelty claim (supplement pp. 2–3, Tables A1–A3; p. 5, §H).
