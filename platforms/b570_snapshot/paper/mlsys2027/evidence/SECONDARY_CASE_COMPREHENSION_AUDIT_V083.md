# Secondary-Case Comprehension Audit — v0.8.3 Phase 5

These are bounded offline reading checks, not a reviewer simulation or accept/reject assessment.

| Test and reading scope | Question | Answer supported by the active manuscript |
|---|---|---|
| A — Introduction + Related Work | What was established before? | Consumer-system gains and slowdowns, verification parallelism and cost limits, numerical path sensitivity, heterogeneous placement/modeling, state reuse, and adaptive control are presented as existing work with the manuscript's existing citations. |
| A — Introduction + Related Work | What is distinctive here? | Prospective direct-ID qualification of tested paths, a B570 target-partition predictor frozen before reserved complete-trajectory outcomes, and explicit realized accounting for one 358H combined state interface. No firstness or broad hardware claim is made. |
| B — Abstract + runtime section + Table 3 | Did Guard outperform fixed speculation? | **NO.** The post-study paired Guard/Always-Spec latency ratio is 1.0271 [1.0130, 1.0436], above parity; fixed speculation is faster on this comparison. No incremental control benefit is shown. |
| B — same scope | Was Guard profitable versus target-only? | **YES.** Target/Guard speedup is 1.3114× [1.2487, 1.3787]. This is a different comparator from Guard/Always-Spec. |
| C — §5.3 + Figure 4 caption + runtime intervention | Is 58.35% measured replay-only cost? | **NO.** It belongs to the combined replay/reconstruction-plus-proposal OpenVINO call. |
| C — same scope | Are replay and proposal inseparable in the recorded timing? | **YES.** The section and caption say they share one timed region. |
| C — same scope | Did the later intervention establish a performance result? | **NO.** Qualification stopped it; no formal R2 performance run occurred. |

All three tests yield the intended distinctions. Table 3 layout and Figure 4 caption already made their comparator and measurement boundaries visible, so neither was edited.
