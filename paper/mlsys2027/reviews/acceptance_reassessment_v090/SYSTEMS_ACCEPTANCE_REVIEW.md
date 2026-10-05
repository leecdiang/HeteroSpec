# Independent systems acceptance review — frozen v0.9.0

**Recommendation: 3/6 — weak reject. Confidence: 4/5.** This is an internal research-track assessment, not a conference decision or an acceptance probability.

The manuscript provides credible, carefully bounded execution-reproduction and cost results. Its strongest contribution is prospective complete-output prediction of a reference-divergent native path by a simpler target-only program. I nevertheless judge the incremental systems insight and demonstrated diagnostic value slightly below the MLSys research-track acceptance threshold. My recommendation concerns the contribution's significance, rather than a discovered contradiction in its central numerical results. Negative results and a debugging contribution can merit acceptance without a faster decoder; the issue here is how much the reported cases establish beyond already documented numerical path sensitivity, correctness gating, and verification cost limits.

## Scope and review independence

I first read `REVIEW_RUBRIC.txt` and `FIXED_PACKET.json`. I read the entire supplied main-text extraction, physical pages 1–12, including all ten body pages and references, and the entire supplement extraction, pages 1–17. I visually inspected main PDF pages 4, 5, 7 and 10 and supplement pages 7, 14 and 15. These pages cover the central predictor claims, tables, cost breakdown, novelty comparison, commitment ledger, host amendment and RTX estimator. I found no consequential clipping or table/figure mismatch on these sampled renders.

The reviewed PDFs have these independently checked SHA-256 identities:

| Artifact | SHA-256 |
|---|---|
| `manuscript-v0.9.0.pdf` | `1edbf7e147a506a47536b2c32672d5dc6db43cf128ad56d9cd213c991d42987d` |
| `appendix-v0.9.0.pdf` | `5dc5d2ebb645f4057104985b42f91f98e2879ed89d185880ab02440826767b32` |

I inspected selected retained packet records and performed direct arithmetic described below. I did not consult the project repository, earlier reviews, meta-reviews, author responses, prior verdicts or another reviewer's output. I did not execute models, GPUs, supplied verifiers or bootstrap suites, retrieve full capsules, or change submission PDFs. The accompanying `REVIEW_COVERAGE_SYSTEMS.json` records exact input hashes, inspection coverage and limits.

## Strongest argument for acceptance

The B570 experiment advances beyond recording a mismatch. A program selected on discovery and frozen before reserved execution produces all 72 complete capped native outputs on 24 distinct prompts, including four trajectories that differ from the UB128 reference. Its 155 non-reference positions include 151 after the first difference. The useful result is a concrete reduction in the inputs and orchestration needed to reproduce those frozen discrepancies: target-only UB1 succeeds without draft weights, proposals or the native speculative outer loop. Predicting the entire later divergent suffix is a stronger test than locating a first different token. It is also stronger evidence than fitting a description after seeing the reserved native answer.

RTX supplies a useful contrast. The predefined target-only UB2 candidate fails, while separately orchestrated H2 and fresh target-only tape replay both match all 57 native outputs. Equal overall match counts for the UB1 reference and UB2 candidate hide different failed prompts; `/25` even reconverges after one different ID. This makes a concrete case for checking full trajectories and program input contracts rather than treating a capacity parameter or aggregate agreement count as a numerical-path description.

The cost analysis also has operational value. Fresh RTX serialization passes its own direct-ID gate but is slower on every selected prompt. The 358H calculation proves, for its measured baseline, progress and target work, that eliminating all draft and residual cost still cannot reach parity under the original prompt estimator. M4's almost nonexistent opportunity between its two measured fixed modes helps explain why a cost guard can be active yet lose to fixed speculation. The paper states the counterfactual premises, uses prompt-level units, and avoids converting correlated token positions or repetitions into independent evidence. These are good systems measurement practices.

The official CFP includes testing/debugging, inference and runtimes, and evaluates research using novelty, quality, interest and impact [1]. On that interpretation, a reviewer could reasonably accept this as a useful empirical diagnostic methodology with unusually disciplined scope and retained evidence.

## Strongest argument for rejection, and my decisive concern

The central distinction is real but narrow: a sealed program predicts finite outputs on the same frozen numerical stack. The paper does not show that the selected reproducer resolves a discrepancy, validates a correction, improves an investigation, or yields a transferable description of the responsible execution state. It explicitly does not claim these outcomes, so their absence is not a falsification. It does limit the demonstrated payoff of the new diagnostic framing.

The closest literature makes the threshold consequential:

| Primary work inspected | Already established | Increment here |
|---|---|---|
| Chordiya, *Lossless but Not Free* [2] | Consumer backend slowdowns, correctness gates, quantized Metal verification limits, and target-only batch-dependent argmax changes without speculative machinery | Prospective full-sequence prediction of a native reference-divergent path, rather than observing numerical changes |
| Yuan et al., *Understanding and Mitigating Numerical Sources of Nondeterminism* [3] | System configuration changes can alter greedy trajectories; controlled numerical analysis and a mitigation | Tests of specified full-trajectory reproduction programs on frozen consumer stacks |
| Gond et al., *LLM-42* [4] | Shape-consistent verification, rollback and scheduling to construct deterministic inference | Describing an existing native path that can remain reference-incompatible |
| Zhang et al., *Correctness Forensics* [5] | Correctness-first forensics, explicit synchronization invariants, corrective mechanisms and residual batch-dependent numerical mismatch | Prospective candidate comparisons, with no new invariant or validated correction |
| Liu et al., *Performance or Illusion?*, MLSys 2026 [6] | Verification dominance and theoretical-versus-measured speedup limits in a production engine | Conditional budgets for a particular consumer interface and the original prompt estimator |

I do not conclude that these papers duplicate the prospective experiment. Rather, the novelty is concentrated in the empirical reproduction test, while most supporting systems lessons specialize established observations. Sealing complete answers before live execution is valuable protection against post hoc explanation, but procedural strength alone does not demonstrate a substantial new systems capability.

The RTX contrast particularly limits interpretation. Matching UB2 capacity does not match actual occupied shapes, target forwards or KV histories. Failure therefore rejects a fairly weak candidate description, not target-only execution as a class. The successful replay shares numerical routines and retains a feedback-generated proposal tape that preserves much of the native verification structure. Separate orchestration is a useful check, but success is less surprising than it would be for a genuinely simpler, discriminating execution description. The paper is candid about these limits; I still do not see a strong general rule an investigator can take from these two stacks to an unseen discrepancy.

The four-stack supporting story cannot supply that generality through breadth alone: backends, OS, quantization, references and timing boundaries jointly change, and the separate campaigns answer different questions. The 358H budget is mathematically useful but assumes exactly the target work and progress an implementation redesign may change. The M4 guard has no policy advantage. Together these are credible cases, rather than a validated portable diagnostic method or a new optimization. This combination is why I land just below acceptance, despite good technical care.

## Technical quality and actual defects

I found no new demonstrated arithmetic or endpoint inconsistency in the principal claims I recalculated. Complete-array matching is sufficient for the stated finite reproduction endpoints; unique causation, minimal history, functional code correctness and population failure rates would require different evidence, and the manuscript does not claim them. The immediate B570 fork result is also appropriately separated from the persistent alternate continuation: unchanged sampled decisions cannot explain delayed divergence from a single numerical block.

The retained record describes actual protocol/provenance problems, but they are disclosed and their remaining consequences are scoped:

* **M4 metadata defect:** the intended freeze-hash field held a build-manifest digest. The supplement describes recovery from retained links and keeps stopped/error markers. I did not independently authenticate that recovery against omitted originals, so I accept the recovered prospective ordering conditionally rather than treating a digest as trusted time.
* **RTX V3 capture defect:** simultaneous EOG/cap terminal behavior defeated the older parser. V3 remains failed, with no live A outcomes; V4 is a separately described protocol/cohort. The packet does not silently pool V3 prefixes into the formal denominator.
* **RTX V4 host-policy amendment:** the fan/host policy changed after predictor capture. The supplement reports pre-live authorization and retention of the original stop, and does not claim physical irrelevance. This prevents calling V4 an unchanged-host replication. It does not by itself contradict the observed pre-live prediction/live equality under the amended completion conditions.

These are material limitations, not evidence here of manipulated measurements or an invalid full-array count. Likewise, debug logging and excluded prefill constrain RTX's practical cost claim: the result excludes this configuration as an optimization within the instrumented post-prefill boundary, not in every deployment. No new logging-free experiment is a validity prerequisite for that bounded statement.

## Independent retained-record arithmetic

The calculations used new direct standard-library arithmetic on packet records, not the supplied verifier implementations or new experiments. I did not rerun confidence-interval bootstraps.

| Check | Independently obtained result |
|---|---|
| B570 H1 complete arrays | Prediction/live 72/72; reference/live 60/72; non-reference extents 40, 55, 25, 35; total 155, with 151 after first differences |
| B570 fork arrays/events | 195 reachable paired decisions; zero committed-ID or raw top-one changes; 18/72 different complete continuations; exported state-check booleans true |
| RTX A arrays | UB1/live 51/57; UB2/live 51/57; H2/live and R ONLY/live 57/57; `/15`, `/18`, `/25` failure lengths/positions match the tables |
| RTX B captured QPC intervals | Target/serialized prompt-median GM `0.6773510334393157`; reciprocal `1.476339372987154`; 0/19 faster; gates 51/57 batched and 57/57 serialized; each condition occupies each schedule position 19 times |
| 358H processed rows | 90 rows/path; prompt-estimator ceilings CPU `0.8372192092432174`, NPU `0.8448401086171792`; necessary uniform target cuts 16.2780791% / 15.5159891%; pooled ceilings `0.8274529834243383` / `0.8351858523671983` |
| 358H accounting premise | Nonnegative retained other cost; component totals agree with complete time to less than `8e-12` ms in parsed arithmetic; 0/30 prompt-median ceilings reach one for either path |
| M4 540 observations | Guard/Always GM `1.0270760219826773`; Always/two-mode oracle `1.0006919671212657`; implied GM latency reduction `0.0006914886338663662` = 0.0691489%; only tasks 559 and 95 favor target over Always; Guard faster on 24/60 |

These checks establish internal consistency of the retained derivatives. They cannot authenticate omitted binaries, raw KV/sampler state, absolute process chronology, or logging-free/session-general performance. Projected state-check booleans are not independently inspected serialized state bytes. Confidence is therefore high in the scoped counts and arithmetic, lower in original historical provenance, and inherently judgmental in the research-track significance assessment.

## Highest-value next actions

1. **Existing records / presentation:** make the novel diagnostic operation concrete with a compact executable reproduction recipe and one worked discrepancy: the exact program inputs, dependencies eliminated, expected capped arrays and native recheck contract. Where retained source or traces permit, show the relevant execution/state differences between that program and native. If actual shape/history correspondence is unavailable, state that explicitly. This would help readers assess the nontriviality and reuse of the successful simplification; it need not enlarge the claims.
2. **Genuinely new research, separately scoped:** demonstrate one diagnostic resolution using the selected simpler harness—an informative ablation or correction followed by confirmation on the native path. This would convert a tested reproducer into evidence of practical diagnostic value and would most strongly change my acceptance judgment. It is an extension to the contribution, not a prerequisite for the current finite prediction and conditional cost claims. A successful performance optimization or hardware-wide campaign is not required for this extension.

## Public sources and lookup limits

[1] [MLSys 2027 Call for Research Papers](https://mlsys.org/Conferences/2027/CallForResearchPapers): official research criteria, topics, ten-page body limit and separate appendix instructions.

[2] [Chordiya, arXiv:2607.17283v1](https://arxiv.org/html/2607.17283v1): abstract, implementation/results passages and targeted batch-dependent argmax / verification-cost passages, especially §6.1 and §6.5.

[3] [Yuan et al., arXiv:2506.09501v2](https://arxiv.org/abs/2506.09501v2): primary abstract and version metadata. I did not independently audit its complete experimental appendix.

[4] [Gond et al., arXiv:2601.17768v2](https://arxiv.org/html/2601.17768v2): abstract, introduction observations and fixed-shape verifier passages. This was a targeted novelty check, not a reproduction of LLM-42.

[5] [Zhang et al., arXiv:2510.22876v4](https://arxiv.org/html/2510.22876v4): abstract and targeted correctness/numerical-control/limitations passages. I did not consult its linked repository.

[6] [Liu et al., MLSys 2026 proceedings](https://proceedings.mlsys.org/paper_files/paper/2026/hash/554e056fe2b6d9fd27ffcd3367ae1267-Abstract-Conference.html): official primary abstract. I rely on it for verification dominance and bound analysis, not detailed implementation claims.

No exhaustive priority search was performed. The novelty judgment compares the claimed advance to these closest primary works, not to an invented requirement that every empirical MLSys paper identify a unique kernel cause.
