# Independent final adversarial review — revised v0.5

## Scope and mock decision

Read the revised main manuscript (all sections, relevant figure captions and table wrappers), separate appendix, runtime numerical macros, and `SUBMISSION_COMPARATOR_SCOPE_V05.md`. I did not read other reviews or the comparator audit before forming this assessment. This is a manuscript/evidence-scope review, not an independent replay of archived model runs or a new literature search.

**Mock decision: Weak Reject; confidence 4/5 on the contribution/evidence assessment.** The revision is materially more candid and internally defensible. I would not reject it for claiming universal hardware rankings, inventing direct-ID success counts, claiming Guard beats fixed speculation, or claiming a successful 358H persistence intervention: the text now explicitly avoids those claims. I would still question whether the remaining empirical contribution clears a selective systems-conference bar. Disclosure repairs inference; it does not supply the missing experiment or incremental systems result.

## Surviving substantive objections

### 1. The remaining novelty is a limited characterization contribution

The introduction, accounting section, and related work concede that heterogeneous placement, cost/commit accounting, adaptive speculation, state reuse, and numerical divergence are established. The reported lessons—measure the complete loop, account for state management, and validate the actual execution path—are useful but familiar. Thus the paper must succeed through unusually strong new characterization. Four configuration-scoped case studies provide breadth, but the narrow model family and uneven historical evidence make that case only moderately compelling. The numerical RTX example and 358H timed decomposition are the strongest concrete additions. The manuscript needs to argue why these particular observations materially change practitioners' decisions, beyond providing cautionary examples.

This is **not a fixable novelty-wording defect**. Removing novelty overclaims was correct; acceptance still depends on the scientific value of the narrower observations. A characterization paper need not invent an algorithm, but candor alone cannot substitute for a consequential discovery.

### 2. Four stacks are not four replications of a common hypothesis

Hardware, OS, runtime, backend, draft quantization, workload, and sessions co-vary. The text acknowledges this repeatedly. Accordingly, the platform count cannot support architectural generalization, portability, or a frequency estimate of speculative failures. M4's opposite outcomes establish two observations, not a causal workload effect. Neither measured failure mechanism explains that contrast.

The surviving concern is research cohesion: the paper joins heterogeneous historical campaigns into two retrospective diagnoses and a separate control study. This is a reasonable case-study design, but less compelling than a common controlled campaign demonstrating when each proposed boundary predicts outcomes. Additional wording cannot turn these cases into controlled replications.

### 3. Guard demonstrates executable control, not a reason to use the controller

Guard's 1.3114x held-out speedup and 180/180 direct-ID equality are valid positive observations within the stated scope. Always-Spec is 1.3469x on the same evaluation, however. The aggregate point estimates imply Guard has approximately 2.71% higher geometric-mean latency than Always-Spec (1.3469 / 1.3114); the manuscript supplies no direct paired confidence interval for this comparison. The separate baseline-relative confidence intervals do not establish a significant difference in either direction.

The selected policy is a simple cumulative-cost threshold after eight rounds with zero margin, with permanent fallback. Its novelty is expressly disclaimed. Fallback on 30.6% of executions establishes activity, not improved choices. No evidenced tail protection, worst-case reduction, robustness advantage, or deployment saving supplies an alternative reason to choose it. The guard can inherit profitability from the already-profitable speculative path while making some requests worse. The 1.0278x oracle ratio is a descriptive proximity result, not a control benefit.

A direct paired Guard/Always-Spec interval would clarify the existing comparison without requiring new model runs, but would not itself rescue the contribution. New evidence of incremental utility would be needed for a controller-focused acceptance case. I would not demand a serving-controller benchmark merely because such controllers exist; I would demand a benefit aligned with this paper's actual one-request setting.

### 4. Historical comparator repair leaves a weaker central correctness story

The revised distinction is appropriate: historical M4/RTX/B570 success counts establish agreement after CLI parsing and re-tokenization; 358H and prospective M4 use direct generated IDs. A text representation can be many-to-one with respect to generated token sequences. Including displayed prompt text in the historical HumanEval parser additionally means those comparisons are not clean generated-output-ID traces. The addendum correctly forbids inference of hidden direct-ID success or mismatch counts.

This leaves the historical positive paths below the manuscript's intended strict generated-ID contract. Calling them “admissible within the recorded comparator” is formally defined, but creates two levels of admission in the central correctness narrative. A historical path's text agreement cannot certify a same-generated-sequence performance comparison under the intended contract. Conversely, the separately captured RTX token divergence remains affirmative narrow evidence that the cheap path violates that contract; it should not be discarded because the success controls use weaker comparison.

The scope correction resolves an overclaim; it cannot retroactively provide the lost token traces. Prospective M4 direct-ID qualification does not repair earlier sessions. That is an **irreducible historical evidence limit** unless archived direct traces are independently found or fresh experiments are performed, with fresh results clearly labeled as such.

### 5. 358H establishes an implementation boundary, not a successful co-design remedy

Phase 3 provides useful direct-ID negative outcomes and timed regions. The NPU replay-plus-proposal region dominates its path, while complete target work dominates the CPU path. But replay and proposal are inseparable, and no measured persistent-state counterfactual establishes how much loss can actually be recovered. “Interface matters” is supported; “persistence would solve the problem” is not, and the revision correctly does not claim it.

The later intervention has no qualified pair and no R2 performance run. CPU state restore/reconcile is unqualified; the NPU state-capable route is unavailable under the frozen IR; UB2 fails qualification. These are honest engineering findings, but they weaken the arc from diagnosis to demonstrated remedy. Same-prefix controls narrow the correctness problem without locating the responsible operation. The compact diagnostic lacks local raw-trace replay, further limiting independent verification of this part.

Do not run or imply unauthorized R2 to improve the story. With current evidence, this section is a stopped intervention and correctness case study, not a second demonstrated runtime optimization.

### 6. Precision and provenance do not remove external-validity limits

Prompt bootstrap intervals are conditional on campaigns and do not capture independent session/thermal variability. Three repetitions and short 128-token outputs in the prospective study leave longer-request behavior and repeated-session stability untested. Historical estimator heterogeneity is disclosed and defensible, but limits clean pooling. Windows raw-run provenance, reconstructed 358H source identity, and the recovered M4 freeze-hash defect are all material qualifications. The recovery explanation is plausible as written; this review has not independently replayed it. These are reasons to bound confidence, not evidence of misconduct.

## Local wording or presentation issues still worth fixing

1. **Section 4, M4:** “Historical MLX failures also do not negate the final qualified Q8_0 Metal result.” Use “text-path-qualified historical Q8_0 Metal result.” Its present local wording invites the stricter contract interpretation even though earlier paragraphs disambiguate it.
2. **Section 5, RTX:** “fails the frozen token-equivalence gate” should specify the recorded comparator for the formal gate, then separately cite the direct token/score reproducer. Otherwise this sentence briefly blends the two evidentiary routes that the revision carefully distinguishes elsewhere.
3. **Section 5, B570:** “Exact subsets may be descriptively useful” should read “text-path-matching subsets” for this historical diagnostic. The heading about serialization not establishing exactness is defensible, but this local subset noun is unnecessarily ambiguous.
4. **Appendix, calibration:** “lowest geometric-mean oracle regret” is inconsistent with the careful main-text avoidance of a regret guarantee. Prefer “lowest geometric-mean latency ratio to the offline oracle.” This is terminology, not a numerical defect.
5. **Appendix, 358H:** “R2 is unauthorized” is internal workflow language. The scientific statement is that no formal runtime performance evaluation was authorized under the qualification protocol and none occurred, or simply that qualification prevented it. Explain the protocol condition instead of expecting a reader to know an internal R2 label.
6. **Frozen artwork:** Caption-level qualifications are much better than leaving old exactness labels unexplained, but a standalone figure can still travel without its caption. This is a presentation risk, not grounds to silently alter immutable evidence. A future publication artwork version could change labels while preserving measurements and provenance if the project permits it.

None of these local fixes would change the mock decision. They are the residual wording issues, not substitutes for new evidence.

## What survives fair skeptical reading

- No unsupported hardware ranking or workload-only M4 causal conclusion is required by the revised claims.
- The stable captured RTX argmax divergence makes the correctness restriction concrete and operationally relevant.
- B570 is correctly retained as a failed global qualification case, not rescued through a matching subset.
- The 358H decomposition charges realized state work and distinguishes complete target cost from a forward proxy.
- The prospective M4 study has explicit held-out selection, direct-ID checks, the fixed baseline, and a candid no-incremental-benefit conclusion.
- The manuscript openly separates historical comparator evidence from direct-ID evidence and stopped interventions from timed experiments.

## Mock program-committee summary

This is now an honest, bounded empirical report rather than an overclaimed heterogeneous speculative system. The strongest acceptance case is practical characterization of correctness restrictions and stateful execution costs on consumer runtimes, backed by direct mechanisms and a prospective exact-execution study. My rejection case is that much of the broad lesson is established, the four cases do not isolate common causal factors, the stateful remedy was never evaluable, and the only deployed control adds no demonstrated benefit over its simple fixed comparator. I would be open to an empirical-track acceptance if the committee values the specific negative cases and artifact sufficiently, but would vote Weak Reject for a selective general systems contribution on the present evidence.
