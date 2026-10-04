# Independent systems-significance acceptance review: HeteroSpec v0.8.9

**Recommendation: 3 / 6 — weak reject. Confidence: 4 / 5.**

This is an internal simulated MLSys perspective, not a committee decision. I reviewed the frozen v0.8.9 object specified in `FIXED_PACKET.json`: all current main text (12 physical pages, 10 body pages) and appendix text (16 pages). I visually inspected main pages 4, 5, 7 and 9, and appendix pages 11 and 13. I did not read earlier reviews, meta-reviews, author responses or closeout verdicts; did not edit the manuscript; and did not execute models, GPUs or historical verification suites. A small direct calculation from the retained 19-row RTX prompt-median CSV reproduces the primary 0.6773510334393157 GM and zero serialized-faster prompts. This is a significance review with sampled rendered inspection, not a complete original-record audit.

## Judgment

The bounded empirical claims are credible and carefully delimited. My concern is the additional systems knowledge at the MLSys acceptance threshold, rather than a demonstrated validity error. The strongest new result is B570's prospective, draft-free reproduction of complete non-reference trajectories. RTX adds a same-set failure discriminator and a successful replay description. However, the manuscript mostly establishes that selected programs reproduce a numerical execution path using the same numerical stack. It does not yet show enough explanatory compression or concrete debugging benefit beyond established shape-sensitive inference, exact-output qualification and complete-cost measurement to make the systems contribution clearly sufficient.

The current framing appropriately avoids claiming a new optimizer, unique numerical cause, necessary proposal history, hardware ranking or production performance. I do not penalize the lack of those broader claims as a validity defect. A bounded diagnosis paper can clear the threshold without a successful optimizer. Here it is borderline because the central trajectory result's practical consequence is primarily choosing a reproducer, and that consequence remains underdeveloped.

## Strongest acceptance argument

1. **A failed reference gate does not describe the divergent output.** The B570 experiment selects its candidate on exposed discovery, freezes its program and complete prediction arrays separately, and then obtains 72/72 reserved complete matches on 24 repeat-stable prompts. Four distinct prompts disagree with the reference; the predictor reproduces the entire remaining capped output. This is stronger than observing numerical sensitivity or reporting first-difference positions. It establishes a simple, draft-free execution description that survives a falsifiable prospective test (main §4.1, p.4, lines 194–218; Figure 1, p.5; appendix J, pp.5–7, Tables A6–A7).

2. **RTX is a substantive boundary, not an asserted portable explanation.** On the same 19 exposure-audited prompts, UB2 and UB1 reference each achieve 51/57, but fail on different tasks. `/18` distinguishes the reference from UB2, `/25` distinguishes UB2 from the reference, and `/15` defeats both. H2 and fresh R ONLY match all complete outputs. The cross-comparison prevents equal totals from hiding different behavior (main §4.3 and Table 2, pp.4–5; appendix Q.3 and Table A18, pp.13–14).

3. **The paper resists common invalid systems inferences.** Prediction success does not qualify a path; a numerical score change does not imply an immediate sampled decision change; a faster isolated draft is not an integrated speedup; a guard that beats target-only need not improve fixed speculation. The B570 fork null result and the negative M4 comparison are useful counterexamples rather than discarded failures (main §§4.2, 5.2, 6.2).

4. **The supporting cost constraints are actionable within their premises.** RTX serialization qualifies but loses on every prompt; 358H cannot reach total-time parity by removing draft/residual costs alone while target work and progress stay fixed; M4 has extremely little hindsight opportunity between the two measured fixed modes. These are useful ways to stop spending effort on an already-bounded direction (main §5, §6.2, Table 6; appendix P.2–P.3).

On this reading, the contribution is a reproducible method for separating execution-description sufficiency from compatibility and cost, supported by carefully frozen counterexamples. A reviewer who values this empirical diagnostic methodology could reasonably support weak acceptance.

## Strongest rejection argument

The closest prior work already covers numerical output changes with shape, correctness forensics, exactness gates, and speculative-decoding cost limits (main §8 and Table 7). Prospective sealing strengthens the evidence but does not alone create a new systems mechanism. B570's successful UB1 target-only path uses the same target stack as the native UB1 execution. RTX's richer replay recomputes substantially the same acceptance, sampling and KV operations with shared numerical routines. Failure of a capacity-only UB2 program is less explanatory than failure of an actual shape/history-matched target-only implementation, because equal capacity never established equal occupied forwards in the first place (main §2.2; Table 1; §4.3, lines 270–273).

Consequently, the current extra knowledge is largely: one simplification reproduces one path, another simplification does not reproduce another path, and an implementation retaining the native proposal-conditioned state machine does reproduce it. That is scientifically real, but small. Table 6's first two engineering decisions—retain a sufficient description or retain richer replay—do not yet identify a root-cause class, validate a correction, or show that a debugging task becomes materially easier. The strongest optimization decisions in the paper come from the separate cost and qualification studies and do not depend on trajectory prediction.

The numerous scope qualifications make this limitation honest. They do not by themselves make the remaining contribution significant enough. I would weakly reject on significance while recognizing the work as a sound and potentially useful empirical diagnostic study.

## Which engineer decisions actually depend on trajectory prediction?

| Decision | Does prediction add information beyond a gate? | Exact supported consequence and limit |
|---|---|---|
| Construct a B570 reproducer without draft weights/proposals | Yes | UB1 target-only reproduces all tested native capped trajectories, including four divergent cases. An engineer can use that simpler harness as an empirically supported reproducer on this frozen stack. This does not show native drafting is causally irrelevant or that the harness predicts a changed stack. |
| Choose an RTX diagnostic execution description | Yes | Reject this UB2 target-only candidate as a full-cohort reproducer; retain H2/R ONLY replay as a demonstrated reproducer. Equal UB labels are inadequate as an equivalence contract for this candidate. It does not follow that every target-only implementation fails or proposals/history are necessary. |
| Design output regression checks for the native path | Yes, narrowly | The frozen candidate supplies complete expected outputs for these tests, including non-reference outputs. It tests reproducibility of the existing path, not losslessness against the designated reference. No actual bug-fix regression case is demonstrated. |
| Deploy native B570 or RTX batching as strict replacements | No | Reference qualification already blocks them. Predicting their errors does not change that verdict. |
| Deploy measured RTX serialization for lower latency | No | Its own direct-ID gate plus paired instrumented cost rejects it as a latency optimization. A's prospective predictions are not needed for B's verdict. |
| Optimize only 358H draft/replay/residual cost | No | The fixed-progress target-work bound supplies the relevant exclusion. |
| Prefer M4 Guard over fixed speculation | No | The matched three-condition timing and fixed-mode opportunity analysis decide this. |

This separation should become the paper's practical story. It makes the real trajectory contribution concrete without borrowing significance from cost conclusions that are independently established.

## Top three changes with high value from existing records

### 1. Turn Table 6's first two rows into explicit debugging workflows

**Locations:** main §7, pp.8–9, especially lines 428–438 and Table 6; Table 1, p.3; appendix J, M and Q.

Show what an engineer removes from a B570 reproduction task—draft loading, proposal generation and native speculative orchestration—and what remains necessary for the demonstrated RTX reproducer: prompt, a sequential proposal tape, locally computed target decisions and KV reconciliation. Give the exact complete-output check that validates each simplification. State observed properties separately from properties inferred from the source. Explain the next legitimate investigation: whether a candidate fix changes both the native path and its reproducer, requiring fresh validation.

**Expected effect:** Converts “retain a sufficient description” into a concrete reusable systems diagnostic. It could materially improve the acceptance case without new inference.

**Limit:** Do not invent measured debugging time savings, prove independence from the native numerical implementation, or claim the same simplification will survive a changed implementation. Those are not in the present records.

### 2. Add one compact worked discrimination case from complete arrays and tapes

**Locations:** main §4.1–§4.3, pp.4–5; Figure 1 and Table 2; appendix A7, A18 and retained proposal/event records.

Use a B570 divergent case and the three distinguishing RTX tasks to show candidate input, first failing output, relevant proposal/accept/correct/bonus transition, and complete remaining endpoint equality. For RTX, explain why the successful replay computes the decision rather than copying an answer. Where actual forward shapes or state histories are not recorded, label the gap; use source-derived descriptions only as source-derived descriptions. The current V2 `/17` illustration in appendix N.1 shows the style, but a V4 example would connect directly to the main result.

**Expected effect:** Makes the full-trajectory test's value legible, distinguishes candidate failure from a generic mismatch, and exposes whether replay offers useful structure rather than only an elaborate reproduction. This is more valuable than further marginal score summaries or repeated assurances about counts.

**Limit:** Existing arrays and tapes cannot establish a unique numerical cause. A missing trace field cannot be reconstructed as an observed fact merely from shared source.

### 3. Express cost opportunity as explicit conditional engineering budgets

**Locations:** main §5.2, p.6; §6.2, p.8; Table 6; appendix P.2–P.3.

Derive two short decision statements from the existing records. Even after eliminating all other terms, 358H target work must fall by approximately **17.25% CPU or 16.48% NPU** to reach total-time parity at the same baseline/progress. Equivalently, under the separate fixed-per-round target-cost premise, committed progress would have to exceed approximately 2.9767/2.9435 IDs per round instead of 2.4631/2.4584; this is a counterfactual threshold, not a measured proposal improvement. On M4, Always/oracle = 1.0006919671 implies only about **0.069% GM latency reduction** is available from hindsight selection between the two measured fixed modes, compared with Guard's 2.71% extra GM latency.

**Expected effect:** Strengthens the most actionable supporting contribution by quantifying how large an architectural change must be before the bounded direction can matter. The RTX 19-row CSV directly reproduces its 0.677351 GM and 0/19 faster count.

**Limit:** These are post-study conditional arithmetic. They are not prompt-GM bounds for 358H, within-request M4 policy bounds, production costs, or achieved optimizations. Improving clarity may still leave the core trajectory novelty modest.

## Necessary versus optional new evidence

**Necessary to sustain the current bounded claims:** I found no new model/GPU experiment that is logically required. The stated claims can stand on their frozen comparisons, retained arrays, protocol/source checks and disclosed boundaries. Requiring extra hardware, models, uncapped generations, an optimizer or a successful causal intervention would improperly expand the claimed project. The fan-policy amendment, narrow exposure-conditioned RTX set, shared kernels and omitted external bytes are disclosed limitations; they are not automatically invalidating defects. The heavy logging boundary prevents a deployment-performance interpretation, but the manuscript currently confines its cost claim to that boundary.

**Useful new evidence for a stronger significance claim:** One focused diagnostic demonstration would have high value: show a real discrepancy or proposed correction being isolated or regression-tested by the simpler reproducer, with explicit agreement back to native execution. Alternatively, test the first divergent states on the existing distinguishing prompts with matched prefix/proposals/state and a one-block intervention followed by a common continuation policy. That could distinguish causal hypotheses that complete arrays presently cannot. These are optional stronger contributions, not conditions for the truth of today's finite observations.

**Genuinely new evidence required if claims broaden:** A verified numerical root cause needs appropriate controlled state/trace interventions; necessity/minimality needs genuinely discriminating additional candidates; portability needs prospective tests on changed models/stacks; production latency needs a suitable logging-free matched measurement; persistence benefits need a functioning, qualified persistent implementation. Existing-record edits cannot supply those results.

## Final assessment

The current contribution is beyond qualification/cost gates in a narrow but meaningful way: it identifies which tested reproducer succeeds and fails before native outcomes are observed. I am not yet persuaded that this extra knowledge is large enough for MLSys acceptance, because the manuscript leaves the concrete debugging benefit largely implicit and the richer RTX reproduction shares most of the relevant numerical execution. My weak-reject recommendation is a significance judgment, not a claim that the bounded results need a larger research project to become valid. The three existing-record changes above are the highest-value path toward making the present work's practical and scientific contribution assessable.
