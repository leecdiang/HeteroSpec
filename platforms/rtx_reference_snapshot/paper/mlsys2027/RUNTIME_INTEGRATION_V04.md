# Final runtime integration v0.4

Completed 2026-09-26 (Asia/Shanghai); audit and writing began 2026-09-25.

## Baseline and authority

Actual fetched, clean main: `bbf0c555cc50242f85c086eac342c9deb5c2e945`, matching the supplied preparation baseline. Branch: `paper/mlsys2027-runtime-integration-v0.4`. No newer conflicting paper rewrite was present. The final delivery revision is the Draft PR's head (also available with `git rev-parse paper/mlsys2027-runtime-integration-v0.4`).

The current skill catalog has Humanizer and PDF skills, but no dedicated experiment/provenance/statistical-validation or academic-synthesis skill. Historical Data Analytics skills listed in the old handoff were not assumed available. Repository validators, direct Python recomputation, native LaTeX, Git, the selected GitHub plugin, and a targeted primary-source literature check were used. Humanizer was used only after scientific/citation freeze. PDF skill supported rendering and visual QA. No subagents were spawned; the three review lenses were performed explicitly by the coordinating editor.

M4 authority is the merged preregistration, calibration freeze, qualification, formal analysis/report and closeout, plus the complete portable archive and its independent verifier. `RUNTIME_BASELINE_V04.json` locks all 41 runtime evidence/source files to current main. `RUNTIME_LEDGER_V04.md` extends rather than rewrites the immutable hardware ledger. The independent archive replay reproduces every core result and verifies 62 payload files.

358H authority is commit `12f387d117fb52cc0ecc688931b9925abb29e71e`, confirmed locally and through the selected GitHub plugin. Six byte-identical paper evidence snapshots retain report, compact diagnostic, protocols, transition and architecture records with exact SHA-256 provenance. The experimental branch was not merged. Complete local raw 358H diagnostic traces and v0.2 R0/R1 outputs are unavailable here; the supplied closeout and pinned compact evidence support the scoped narrative, not a claim of new raw-trace revalidation. See the evidence ledger for the precise boundary.

## Narrative and title decision

Title retained: **Speculative Decoding Across Consumer Systems: Gains, Failures, and Runtime Costs**. It covers both the characterization and measured control without suggesting a universal controller or a new speculative algorithm.

Section 7 is **Qualification and Realized-Cost Runtime Control**, with three subsections:

1. An intervention stopped by qualification: 358H implementation eligibility and scoped UB2 correctness diagnostics, no formal speed result.
2. A prospective cost guard on M4: complete elapsed cost per committed token, calibration-only reference, frozen policy, one-way fallback and forbidden online inputs.
3. Held-out evaluation: disjoint splits, qualification, exactness, ratio-of-medians estimator, formal results and their limits.

This replaces the proposal/interface catalog rather than appending a separate software paper. Sections 1–6 motivate two decisions, path qualification and complete-cost control; Section 7 tests them while preserving the closed hardware argument. The conclusion now answers the opening question with both measured components.

Outside Section 7: abstract, introduction, methodology, state diagnosis, synthesis, related work, limitations and conclusion were revised. Section 2's accounting and contract remain intact. Section 4 changes only float queue locations. Abstract retains the negative/positive separate M4 observations and exact negative 358H outcomes; it includes one runtime speedup and the fixed-speculation limitation. Methods distinguish the new estimator from historical campaign estimators. Related work adds TurboSpec v3 without modifying any of the 13 existing bibliography entries. Limitations and appendix disclose the freeze-hash recording defect and independent recovery.

## Claims and displays

M4 policy E8_M000: first decision after 8 rounds, margin zero. Both speculative conditions qualify at 48/48 direct-token exact; formal held-out execution is 60 prompts, 3 repetitions, 3 conditions, 540 observations, each speculative condition 180/180 exact, zero mismatches.

- Target/Guard GM: 1.3114×, 95% prompt-bootstrap CI [1.2487, 1.3787].
- Target/Always-Spec GM: 1.3469× [1.2867, 1.4088]. Guard does not beat this aggregate point estimate.
- Guard/offline oracle GM: 1.0278× [1.0137, 1.0446], descriptive hindsight unavailable online.
- Fallback: 30.6%. Runtime energy: NOT_CLAIMED.

358H: qualification blocked the candidate intervention before formal performance evaluation. No v0.2 R2 or v0.3 speedup exists. The UB2 divergence is scoped to the frozen tested target stack. Same-prefix controls and proposal playback support numerical-path divergence, not a proven rollback-boundary bug or a universal hardware/backend limitation.

Added one native LaTeX vector table (Table 3, p. 9), with three M4 ratios/CIs and explicit descriptive oracle labeling. Generation uses `runtime_values.py`; `validate_runtime.py` checks exact formatted values and evidence links. No fifth figure was added, no existing figure/table was removed, and the validated hardware figure tree is byte-identical. All four main figures retain native widths on pp. 4–7. Runtime Table 3 was checked in native-size 96-dpi grayscale as well as the full page render.

## Page budget and visual review

Baseline: 10 body + 1 reference page; 3 appendix pages. First integration: 10 + 1 and 4, but hardware floats drifted into runtime. Removing repeated introductory material and queuing ordinary wide floats earlier restored the hardware sequence. Final: **10 body + 1 reference page; 4 appendix pages**. Section 7 spans pp. 7–9; Section 8 starts p. 9; conclusion is complete on p. 10. The 9-body-page hardware-only build is retained only as a Section-7-removal/reference test; it is not the primary or standalone paper.

All final 11 main pages and 4 appendix pages were rendered at 1,400-pixel long edge and visually inspected. Appendix A3/A4 now share a hardware lookup page; a normal page break places runtime reproducibility on p. 4. No clipping, overlap, unreadable display, overfull box, or detached caption was found. Ordinary final-page whitespace is retained; the main conclusion shares p. 10 with limitations rather than dangling alone. No font, margin, line-spacing or template geometry was changed.

## Validation and humanization

Canonical `make all`, `make hardware-only`, and `make check` pass. QA Python: `/Users/lee/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3` (or any Python with NumPy, pandas and pypdf).

- 228/228 original hardware numerical comparisons; original numerical validator and asset generator unchanged.
- 260 protected-file checks and all 57 prior prose numeric macros retained.
- 117 runtime checks, 23 exact source-backed macros, split rank/disjointness, full independent archive replay, and pinned 358H diagnostic controls.
- Five original independent figure replays, active source coordinates/hashes, four native-width PDF placements, 11 appendix lookup cells, eight historical inventory cases.
- Anonymous text/metadata/links; all fonts embedded; 14 references with complete author lists; zero overfull boxes or unresolved citations/references.
- Current Overleaf package builds independently and preserves page-by-page text and page counts (receipt in `RUNTIME_PACKAGE_QA_V04.json`).

Validators evolved narrowly: compare change scope against the new audited main; preserve the original bibliography as an exact prefix while adding one citation; add separately locked runtime evidence/macros and stale-claim checks; version narrative/figure receipts; update delivery version and bibliography count. No hardware protection or numeric assertion was disabled, and no in-memory exception was used.

`reviews/INTERNAL_REVIEW_V04.md` records rigor, systems contribution and presentation findings before the final prose pass. Humanizer skill: `/Users/lee/.codex/skills/humanizer/SKILL.md`. Eight sentence-level edits simplified nominal phrasing, clarified subjects and removed rhetorical repetition. Every numerical literal, TeX command and citation sequence matched before/after; every scientific assertion was manually compared. `RUNTIME_STYLE_V04.json` records exact edits and hashes. The subsequent appendix page break is a separate layout-only change, not a claim/style change. Canonical validation was rerun afterward.

Whole-paper coherence was checked continuously: abstract predicts the hardware and runtime evidence; introduction asks the answered bounded question; diagnoses motivate qualification/control; related work limits novelty; limitations cover both; conclusion integrates both. The negative campaigns remain visible and no stale future-runtime claim remains in active prose. Historical evidence documents and old review artifacts retain their historical status and bytes.

## Files and remaining risks

Changed source groups: manuscript main/appendix, sections 1/3/4/5/6/7/8/9/10, bibliography, Makefile/README, packaging and QA entrypoints; new runtime macro generator/validator and table. Added versioned evidence locks, pinned snapshots, runtime ledger, literature/style/validation/package receipts, review record and this integration report. Updated current manuscript/writing status. Added v0.4 PDFs and collaboration ZIP without replacing historical versions.

Remaining risks are scientific rather than build failures: modest controller novelty and no head-to-head comparison with serving controllers; one M4 model/runtime pair and finite held-out scope; thermal/session uncertainty outside prompt bootstrap; small Spec-Bench strata; 358H compact rather than locally replayable raw evidence. The metadata exception is disclosed and independently reconciled, not erased. Author scientific review remains necessary.

No new hardware/runtime timing was performed.
No closed experiment result was modified.
Open a Draft PR against main; do not merge automatically.
