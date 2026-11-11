# Independent Reviewer A — MLSys systems review

Review baseline: PR #27 source HEAD `b326ff7f20d9bac5afff6f53a6e9d9d8a7aaa7ae`. Read the complete main manuscript, Sections 1–10, appendix, runtime integration/evidence ledger, M4 closeout/formal report, and relevant M4 runner code. I did not read another reviewer's report. This review assesses systems contribution and its presentation; it is not a fresh statistical or raw-archive audit. File locations below refer to the source manuscript before revision. No manuscript, implementation, or experimental record was changed.

## Summary and strongest defensible contribution

The strongest contribution is **a measured account of how correctness qualification and complete stateful execution cost change which speculative-decoding paths are usable, followed by a prospective test of continuation control on one surviving path**. This is an empirical systems contribution supported by implementations and a bounded runtime experiment. It is not a new threshold algorithm, a universal profitability model, or a demonstration that the Guard is preferable to fixed speculation.

The paper's most useful systems observation is more specific than “acceptance is insufficient”: a physically attractive verification path can disappear under the chosen output contract, and a fast device can lose its apparent advantage at the actual state interface. These are distinct failure boundaries, supported by different experiments. The paper should make this contribution easy to state without first explaining the study chronology.

## Strengths

1. **The performance-admissibility distinction changes interpretation of measurements.** Sections 2 and 5 do not label a timing win a usable optimization when its tokens fail the selected contract. RTX path controls give a concrete cost consequence; B570's partially improved serialization prevents promoting one execution setting into a generic exactness guarantee. This is more valuable than a platform-speed ranking.
2. **The stateful 358H analysis measures an interface rather than inferring overhead from incompatible proxies.** Section 5 separates isolated draft throughput, complete target work, and replay-plus-proposal, while leaving the latter inseparable. The direct component totals provide a useful explanation of exact negative results.
3. **Positive and awkward results are retained.** M4 historical studies are separate-session observations, B570 is still blocked, 358H Phase 3 is exact but slow, and Always-Spec has a higher runtime point estimate. This gives the characterization credibility.
4. **The runtime experiment is real and implementable.** Section 7 specifies the frozen global target reference, cost/progress signal, one-way transition, first eligible decision, calibration objective, forbidden inputs, held-out split, and charged timing boundary. The M4 code retains committed history and trims candidate state before selecting continuation (`scripts/platform/m4_runtime/runtime_runner.cpp:155–176`). The archive/closeout describe a reproducible offline audit.
5. **The paper already limits novelty responsibly.** Sections 2 and 8 acknowledge cost accounting, numerical variation, heterogeneous placement, feedback control, and state reuse as prior art. The 358H runtime section clearly does not report a speedup.

## Major concerns

### A1. The contribution statement is too procedural to carry the acceptance argument

`sections/01_introduction.tex:9` says “Our contribution combines ...” and concludes with “this bounded empirical connection.” That specifies ingredients but leaves a reviewer to infer what reusable knowledge they obtain. The abstract (`main.tex:35`) spends most of its space inventorying campaigns. Section 6 then repeats the inventory before reaching its actionable sequence (`sections/06_synthesis.tex:3–7`).

Required editorial improvement: state the contribution affirmatively as the two measured boundaries and the consequences for execution-path selection/continuation. Organize the introduction's contribution paragraph around (i) observed admissibility consequences, (ii) measured realization consequences, and (iii) the bounded prospective controller test. These are parts of one argument, not three claims of independent novelty. Do not claim a new formal framework merely because the measurements can be organized into one.

### A2. The Guard demonstrates feasible profitable execution, not the value of choosing Guard

`sections/07_runtime_codesign.tex:25–27` correctly retains Always-Spec's higher aggregate point estimate. This is the central systems weakness, not a phrasing defect. The current experiment shows that the measured online signal can drive nontrivial continuation decisions while the overall path remains exact and profitable relative to target-only. It does **not** show that adding the Guard provides a performance advantage, lower tail risk, or more robust workload generalization. The 30.6% fallback fraction demonstrates activity, not decision benefit. The oracle describes hindsight proximity and cannot answer the missing comparative utility question by itself.

The paper can still be a systems characterization paper with a useful proof-of-execution controller. It cannot use the controller's existence to claim that characterization has become a superior optimization. Add one clear sentence naming what the controller experiment actually tests: whether a preregistered complete-cost continuation rule can execute exactly and profitably on untouched requests. Do not add hypothetical deployment stories, a “safety guarantee,” or an unmeasured regret bound. In particular, this is **within-request continuation control**, not a pre-request admission scheduler: every sufficiently long request starts speculatively and pays eight exploratory rounds before the first decision (`sections/07_runtime_codesign.tex:13–17`).

### A3. The Section 7 connection is conceptually legitimate but not a transferred intervention

Sections 4–6 support “qualify paths, then use realized costs”; Section 7 has one stopped 358H intervention and one M4 controller. It does not demonstrate that the controller remedies the replay bottleneck, that state persistence yields speedup, or that the 358H negative result caused the M4 design. Current wording is generally careful, but the repeated “lead to,” “motivate,” and “guide” language can create stronger transfer expectations than the result satisfies (`sections/06_synthesis.tex:7`, `sections/07_runtime_codesign.tex:3,13`).

Make the structural relationship explicit once: the studies examine two different decisions in the same proposed evaluation sequence, on different stacks; they do not form an intervention/ablation chain. Then remove repeated chronological caveats. The 358H qualification result is a boundary test of the methodology, not the successful software contribution. Its device-specific failure cannot establish a general restriction on heterogeneous SD.

### A4. The strict output contract needs a short affirmative systems rationale

The distinction between algorithmic distribution preservation and path-specific greedy equality is clear in Sections 2 and 8. Still, a skeptical systems reviewer can ask why a small batch-shape argmax change should remove a fast path when many deployments accept such numerical variation. The limitations admit alternative contracts, which is appropriate, but admission under an intentionally strict contract is otherwise almost definitional.

Add a concise rationale where the contract is introduced: it permits latency comparisons for the same generated token sequence and treats output preservation as an explicit experimental requirement. Do not imply this is the universally correct deployment objective. The novel evidence is the measured **cost consequence** of satisfying that contract in these stacks, not the obvious rule that a failed requirement excludes a path.

### A5. Generalizable insight remains moderate; prose cannot remove that limitation

The four stacks differ in hardware, software, quantization, and campaigns. The M4 contrast is not causally isolated. The 358H state diagnosis exposes a particular full-prefix interface; its persistence intervention never reaches formal performance evaluation. The CUDA diagnosis does not identify a root kernel. These boundaries are candidly documented (`sections/09_limitations.tex:3–11`) and allow useful case evidence, but they cap predictive and technique novelty.

No new experiments are requested within this revision. The correct editorial action is a sharper empirical claim and a clear residual-risk record. A reviewer who requires a new system technique, portable improvement, or controlled architectural comparison may reject even the improved paper. Do not respond by making the Guard more complex or claiming a universal rule.

## Minor concerns and targeted implementation-detail balance

- **Timing wording:** Section 7 line 15 says the enclosing clock includes “initialization.” In `runtime_runner.cpp:85–98`, sampler/speculative initialization, prefill, synchronization, and `common_speculative_begin` precede `start`; request-local generation state and seed handling then occur inside the timed region. Say “generation-loop initialization” or otherwise use the actual boundary, rather than implying all runtime initialization is charged. No data change is required.
- **One state-transition detail belongs in main prose:** Section 7 line 15 says reconciliation preserves committed history. A short phrase specifying that invalid candidate suffix state is removed before target-only continuation would make exact transition credible. The code implements this on both contexts before the Guard decision (`runtime_runner.cpp:160–176`). A pseudocode figure is unnecessary unless replacing equally long text.
- **Too much internal experiment vocabulary:** “R2” and “formal registry” (`sections/07_runtime_codesign.tex:10`) require artifact knowledge but add little scientific information. Prefer “formal performance evaluation” and “no qualified speculative intervention remained.” Keep exact protocol identifiers in the appendix/ledger.
- **Policy identifier distracts:** `E8_M000` is valuable in the artifact but not necessary to understand “eight rounds, zero margin.” Retain it in the appendix; main prose can use the parameters directly. The candidate grid and tie-break details also fit the appendix while the calibration-only selection and freeze order remain in main.
- **Abstract overload:** Historical M4 positive/negative intervals, exactness count, two exact 358H speedups, runtime interval, and fixed-speculation caveat are too many separate results for one abstract. Keep one historical contrast or a qualitative summary plus the primary runtime comparison. Preserve all omitted abstract numbers in their result sections; do not remove awkward evidence.
- **Conclusion repeats rather than synthesizes:** `sections/10_conclusion.tex:3` can end on the experimental decision consequence: physical availability, output qualification, and full realized cost must be distinguished. It need not repeat every platform outcome or apologize about fixed speculation again if the controller result is stated precisely.

## Runtime-table judgment

Keep the compact table. The three quantities have distinct meanings and are efficiently shown as text ratios. A new speedup chart risks giving Guard/Always-Spec a competitive framing the paper does not substantiate, while a controller schematic adds little beyond a short recurrence or prose rule. The oracle should remain visibly secondary and retain its ratio direction. Do not move it to the abstract to imply a near-oracle algorithmic result.

## Likely score range and acceptance bar

On an illustrative 1–10 scale (4 = weak reject, 5 = borderline, 6 = weak accept), **4–6; current inclination 5 with moderate confidence**. This is an internal simulation, not an asserted official MLSys scoring rubric.

- Weak reject is justified if the venue/reviewer requires a novel performance technique: the Guard does not improve aggregate performance over fixed speculation, and the failed 358H intervention supplies no optimized result.
- Weak accept is defensible if the paper is assessed as a careful empirical systems contribution: the path-dependent correctness/cost consequences, negative controls, preserved evidence classes, and prospective runtime closure collectively provide useful knowledge.
- Sharper prose can improve the reader's ability to evaluate this contribution; it cannot turn this into an algorithmic paper or establish an unmeasured benefit of control.

## Top five revisions

1. **P1 — Replace the procedural contribution paragraph with the single empirical contribution and its three linked evidentiary parts.** Affect introduction, abstract, synthesis, conclusion. No new metrics or novelty escalation.
2. **P1 — Define the exact question answered by the Guard study and distinguish continuation activity from demonstrated comparative utility.** Affect Section 7 result interpretation and limitations. Keep Always-Spec and oracle results visible.
3. **P1 — Clarify that 358H qualification and M4 continuation are different tests of a shared decision sequence, not a causal intervention chain.** Affect Section 6→7 transition. Do not repeat this caveat in every paragraph.
4. **P2 — Improve implementation credibility with one precise state-suffix transition phrase and a corrected initialization boundary; move protocol IDs/tie-break detail to appendix.** Affect Section 7/appendix, referencing existing code only.
5. **P2 — Shorten abstract and Section 6 repetition; use recovered space for the contract rationale and contribution statement.** Keep <=10 body pages and existing figures/table.

## Independent abstract proposal

The following is a proposal, not a manuscript edit. It intentionally uses fewer numbers and does not claim that the controller outperforms fixed speculation.

> Favorable draft throughput, token acceptance, and batched verification cost need not yield faster speculative decoding once an execution path must preserve outputs and manage state. We study this gap in four retrospective consumer-system case studies under a matched greedy-token contract. Path controls show that correctness qualification can exclude cheap verification, while direct timing shows that an isolated NPU draft advantage does not survive the tested stateful interface. Separate M4 studies retain both profitable and unprofitable exact outcomes without attributing their contrast to workload alone. We then examine two runtime decisions in separately frozen studies: qualification stops a 358H intervention before performance evaluation, and a one-way M4 guard uses complete realized cost to decide whether to continue speculation. On 60 held-out prompts, Guard achieves 1.3114× post-prefill speedup over target-only (95% prompt-bootstrap interval [1.2487, 1.3787]); Guard and fixed speculation each preserve all 180 matched token sequences. Fixed speculation has the higher aggregate speedup estimate. The contribution is an empirical account of execution-path and state-cost constraints, with a prospective test of exact, profitable continuation control on one qualified path.

## Suggestions deliberately not made

No additional timing, policy tuning, workload search, subgroup promotion, hardware ranking, source-record correction, stronger causal explanation, or complicated replacement controller. The closed evidence bounds the paper and the mock score.
