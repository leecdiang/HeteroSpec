# Coordinated meta-review v0.5

Source PR #27 HEAD: `b326ff7f20d9bac5afff6f53a6e9d9d8a7aaa7ae`; merged main at discovery and resume: `7b22e0e7cbb3915597109951b6a709c1a92e5627` (same source tree). New branch: `paper/mlsys2027-submission-review-v0.5`, created from the exact source HEAD. No manuscript revision preceded the complete coordinating read or independent A–I reports.

## Single contribution

The paper measures how an exact-output contract and the actual stateful execution interface change which speculative-decoding opportunities remain usable, and prospectively tests realized-cost continuation on one qualified path. The contribution is the concrete measured consequences, not invention of qualification, accounting, heterogeneous placement, or a threshold algorithm. The runtime experiment tests execution of the decision process; it does not demonstrate that adding Guard improves on fixed speculation.

## Decisions (not a vote count)

| Issue | Reviewers | Priority | Evidence | Action / files | Scientific risk | Page impact | Decision |
|---|---|---|---|---|---|---|---|
| Energy neutrality implied by CI crossing parity | C | P0 wording | Frozen M4 package ratio 1.013 [0.990,1.034]; no equivalence test | Say improvement not established in outcomes/appendix; render corrected table wording without changing frozen table or generator | Low; narrows inference | Neutral | Accept |
| Initialization scope too broad | A | P1 | runtime_runner.cpp: sampler/spec init, prefill and common_speculative_begin precede timer | Name timed generation-loop initialization and excluded setup in §7 | Low; matches executed code | +1 sentence | Accept |
| Vague empirical contribution | A,D,E,F,G | P1 | Path controls, measured regions, prospective M4 endpoint | Align abstract, intro, §6, §7, conclusion around measured qualification and realization constraints | Medium; avoid framework/algorithm priority claim | Net reduction | Accept |
| Guard usefulness exceeds comparative evidence | A,B,D,E,F,G | P1 | Always-Spec point estimate exceeds Guard; fallback is activity | State experiment's question and no demonstrated advantage of adding control; keep both policies and oracle | Low | Neutral | Accept |
| Prospective could imply no prior outcome knowledge | B,D,E | P1 | Historical family outcomes known; ID exclusion and policy freeze documented | State history informed design; prospective refers to held-out prompt outcomes after freeze; scope exclusion to inventory | Low | +2 sentences | Accept |
| 358H/M4 could look like a transferred intervention | A,E,G | P1 | Separate protocols/stacks, no 358H R2 | Present complementary tests of two decisions, not one intervention/ablation chain | Low | Reduction | Accept |
| Metadata recovery versus uninterrupted validation | B,E,I | P1 | Wrong digest retained; archive recovery and formal-start comparison | Keep exception, add nearby pointer; distinguish archive replay from historical Git audit in docs | Low | Neutral | Accept |
| Fallback denominator / oracle meaning | B,C,H | P2 | 55/180 executions; oracle minimum of two measured condition medians | Name execution denominator; distinguish table speedup and hindsight latency ratio, neither global policy bound nor online input | Low | +2 table rows | Accept |
| Calibration grid and CI conditioning | B,C | P2 | Frozen nine-candidate grid; selected-policy prompt bootstrap | Give grid and conditional inference in appendix | Low | +3 sentences appendix | Accept |
| Direct runtime prior art | D | P1 | Primary TurboSpec v3 and BanditSpec proceedings verified by coordinator | Explicitly acknowledge disabling speculation; append one BanditSpec citation | Low | +1 paragraph / reference | Accept |
| Contract rationale and transition implementation | A | P2 | Direct-token contract; suffix removal before decision | Explain matched output requirement; add brief state-suffix detail | Low | +2 sentences | Accept |
| Implementation detail versus readable narrative | A,G | P2 | Rule/reference/freeze needed; candidate IDs/tie breaks are artifact detail | Keep rule and reference in main; grid/tie-break rationale in appendix; condense §6 and limitations | Low | Net reduction | Accept selectively |
| Figure 4 caption density | H,G | P2 | Existing values already in main/appendix | Shorten only repeated interpretation; retain numerical anchors, uncertainty, timing and estimator distinctions | Low | Reduction | Accept narrowly |
| Stale README and hidden Git prerequisites | I | P2 | paper README still says future runtime; validators use git show | Update current navigation and exact offline/full-validation commands | Low | None | Accept |
| Extra runtime plot / algorithm schematic | A,F,H | REJECT | Current table and prose already convey evidence | Retain four immutable figure assets; improve table grouping only | Avoids implied algorithmic weight | Saves space | Reject |
| Balance final column or modify existing artwork | H | P3 | Source PDF has ordinary final-page whitespace, no clipping | Reassess after edits; no geometry/font/asset changes just to fill space | Unnecessary layout risk | Unknown | Defer; retain natural layout if sound |
| Add MemSpec and broader recent-work list | D | P3 / REJECT for now | Abstract lead only; full primary text unavailable; no new priority claim needed | Record freshness lead; do not add unverified detailed distinctions or indiscriminate citations | Avoids weak sourcing | Saves space | Reject conditional addition |
| Controller complexity, tuning, subgroup promotion, new hardware runs | All relevant | REJECT | Closed experimental scope; comparative gain unestablished | Record residual risk; no new evidence search | High if pursued | None | Reject |

## Preserved disagreements and adjudication

* **A versus G on detail:** A wants a credible fallback implementation; G wants less runtime bookkeeping. Keep one concrete suffix-removal sentence and the exact measured boundary; do not add pseudocode, code listings, or more registry history.
* **C's P0 versus other reviewers' no-P0 finding:** C identifies an inferential wording defect, not an incorrect measurement. Correct the energy sentence/table interpretation; do not change the estimate, CI, or experiment classification.
* **E versus F on acceptance:** E judges familiar phenomena plus no incremental controller benefit insufficient. F would champion the specific controls and preserved negative evidence as an empirical systems contribution. Both positions survive revision. Do not average them into an asserted consensus acceptance.
* **H versus A on visuals:** Both favor the runtime table. H's direction cues materially help; a new figure and broad artwork changes do not. Preserve all closed figure bytes and geometry.
* **B/I on provenance:** A portable archive PASS proves integrity and numerical reconstruction; historical Git-byte comparison is a separate check. Neither proves every unrecorded historical exposure absent. Disclose all three levels distinctly.

## Abstract proposals

A emphasizes constraints and continuation; D emphasizes which opportunities survive; F centers the two measured boundaries; G prioritizes the narrative seam. The coordinated abstract uses the boundary-led opening and fewer historical numbers, retains the negative M4 observation and 358H stop, and reports both runtime speedup point estimates. It omits oracle regret from the abstract, preserving it in the main table. No proposal is adopted for drama or asserted priority.

## Residual risks accepted

Modest technique novelty; no demonstrated Guard benefit over fixed speculation or adaptive controllers; confounded retrospective consumer cases; one selected M4 configuration and finite balanced workload; session/calibration uncertainty outside the prompt CI; strict contract not universal deployment policy; compact-only 358H diagnostic provenance; recovered rather than originally correct freeze metadata. None is solved by prose or new experiments in this revision.

## Evidence-driven P0 addendum

Source audit and an independent comparator audit established that historical M4, RTX workload controls, and B570 compare re-tokenized CLI text, not directly generated IDs. Correct current prose, captions and wording-only table overlays; retain all closed counts, evidence classes and frozen assets. The intended direct-ID contract and prospective M4 direct-ID results remain distinct. This is a material claim-scope correction, not a newly observed mismatch. See COMPARATOR_AUDIT.md and evidence/SUBMISSION_COMPARATOR_SCOPE_V05.md. A fresh-context writing review supplements the initial writing review to preserve independence.
