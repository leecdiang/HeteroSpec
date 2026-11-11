# Novelty and Secondary-Case Calibration — Phase 5

## CR-10

Existing cited work already covers consumer-system gains and slowdowns, verification and cost limits, numerical path dependence, heterogeneous CPU/GPU/NPU placement, analytical performance modeling, state reuse, and adaptive control. Related Work now states those boundaries in three compact paragraphs using exactly the prior citation set. The Introduction places established background immediately before the paper's three contributions.

The paper's distinct tested evidence remains: prospective direct-ID path qualification; a B570 target-partition predictor frozen before reserved complete-trajectory outcomes; and one realized 358H combined state-interface accounting result. It does not claim to discover slowdown, numerical sensitivity, placement costs, or adaptive control. No firstness claim was added.

**CR-10: ADDRESSED.** The closest-work and revised-phrase record is `RELATED_WORK_BOUNDARY_AUDIT_V083.md`.

## CR-11

Guard remains profitable against target-only: 1.3114× [1.2487, 1.3787]. Fixed Always-Spec has 1.3469× [1.2867, 1.4088]. The post-study paired secondary Guard/Always-Spec latency ratio is 1.0270760219826773 [1.0129560055428655, 1.0435592653980876], displayed as 1.0271 [1.0130, 1.0436]; above one means Guard is slower. Prompt medians favor Guard on 24, Always-Spec on 36, with zero ties. Abstract, runtime opening/interpretation, Related Work, and conclusion now explicitly state that no incremental control benefit is demonstrated. Table 3 already puts both target-relative rows together and separately labels the adverse paired row; **NO CHANGE NEEDED** to its values, row order, or caption.

**CR-11: ADDRESSED.** See `M4_GUARD_INTERPRETATION_AUDIT_V083.md`.

## CR-12

The 358H NPU's 58.35% region is the synchronous combined full-prefix replay/reconstruction-plus-proposal call. Replay and proposal cannot be separated by the recorded timer, so no replay-only percentage or intrinsic NPU weakness is inferred. §5.3 now names this boundary directly. Figure 4 caption already said replay-only time was unmeasured, so it and the asset were unchanged. The later intervention stopped at qualification; no formal R2 performance endpoint exists.

**CR-12: ADDRESSED.** See `H358_INTERFACE_BOUNDARY_AUDIT_V083.md`.

## New citations

**NONE.** Related Work retains exactly the same citation-key set; `references.bib` is unchanged. No external literature search was performed.

## Numerical invariants

**PASS.** Frozen RTX/B570 counts remain 75/90, 90/90, 60/90, 78/90, 36/36, 72/72, 60/72, 24/24, and 12/12. M4 value macros, raw paired-secondary result and prompt counts, Table 3, and all 358H CPU/NPU value sources remain unchanged. No result or statistical method changed.

## First-page story

**CENTRAL STORY CLEAR.** The title and abstract still lead qualification → frozen B570 prediction → realized integration cost. The Introduction keeps exactly three headline contributions and now places established adjacent work immediately before them. The 72/72 complete generated-token-ID prediction and tested-path sufficiency remain visible on page 1. See the bounded reading results in `SECONDARY_CASE_COMPREHENSION_AUDIT_V083.md`.

## Build and visual QA

Clean-directory main and appendix builds pass. Main: 10 body pages + 2 reference pages. Appendix: 8 pages. No overfull boxes or unresolved citations/references. All pages were rendered and inspected, with focused checks of page 1, Related Work, M4 Table 3, §5.3, Figure 4 caption, Limitations, and Conclusion; no clipping or awkward break was found.

## Deferred issues

CR-14 central B570 timeline visualization; CR-15 Figure 2 redesign; CR-18 Figure 4 in-panel visual labeling; Table 1 hardware-scope presentation.

## Scientific integrity

No new experiment, no new inference, no new performance result, and no closed evidence modification. Phase-1–4 evidence values, Figure 3, Figure 4 asset, and protected `benchmarks/`, `artifacts/`, `reports/`, and `analysis/` trees are unchanged.
