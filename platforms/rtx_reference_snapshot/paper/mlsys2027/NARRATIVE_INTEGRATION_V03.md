# Initial-draft integration v0.3

Status: **INITIAL DRAFT FROZEN FOR OVERLEAF COLLABORATION** (2026-09-22).

## Exact source and migration

Starting main: `9014e4b8a89031cfa26fc2c03180181bee124d86`. The repository was fetched; local main was fast-forwarded to this exact SHA and confirmed clean. The requested branch `paper/mlsys2027-initial-draft-v0.3` was then created from it. Earlier uncommitted editorial work was safely checkpointed on its prior branch and replayed onto this new branch; that checkpoint is not treated as the scientific or figure baseline. The temporary pre-PR-24 schematic copy was removed. Active assets now come directly from the specified current main. The integrated artifact checkpoint is `8ea0be7ae0e18e733e12405b136f58460473dfba`; a following documentation commit records the freeze.

`NARRATIVE_V03_BASELINE.json` hashes the complete current-main figure tree and records PR #24 provenance. Earlier v0.1/v0.2 scientific and figure baselines remain intact and are still checked. No file under `figures/` was edited, regenerated, or deleted.

## Narrative and manuscript changes

The active story is observed outcomes → measured translation boundaries → detailed diagnoses → prospective runtime motivation. The abstract and introduction use the author's bounded research question about integrated post-prefill speculative decode in the tested configurations. The PR #20 retrospective-synthesis statement and independently frozen primary outcomes remain explicit in Section 3.1. Separate M4 sessions, co-varying hardware/runtime stacks, estimator distinctions, sensor boundaries and bounded later controls are retained.

Section 5 is now “From Local Opportunity to Realized Gain.” Its opening limits the two diagnoses to identified configurations and explicitly leaves the M4 contrast independent. The translation wrapper is inserted immediately after that opening, before the first detailed subsection. LaTeX's normal wide-float placement produces the intended figure order on pp. 4–7. All references use semantic labels.

| Figure | Question answered | Source |
|---|---|---|
| 1, M4 | What outcome contrast was observed? | Unchanged v0.4 single-column forest plot |
| 2, translation | Where are the measured evaluation boundaries? | Unchanged final v0.5 Candidate B after PR #24 |
| 3, verification | Which physically favorable paths remain qualified? | Unchanged v0.4 quantitative plot |
| 4, state | Does isolated draft advantage survive tested integration? | Unchanged v0.4 358H comparison |

The old overview input and its reference sentence were removed without replacing it with a new overview table. The nearby duplicate verification table was removed from the main flow. Its historical source stays byte-identical. Appendix A3 preserves M4 1.02–1.08, RTX batched 0.98–1.01, RTX serial 2.14–2.43, B570 fast 1.24–1.64 and B570 serial 1.98–1.99 in its caption, with path qualification beside all 11 source cells. Exact source cells are displayed to six decimal places; this is a lookup, not a new estimator or analysis.

The old appendix infographic is replaced by Table A4 using `figures/style_v04/tables/appendix_table.tex` unchanged. All eight cases and evidence classes are retained; B570 remains inadmissible, RTX serialized remains secondary, and 358H remains P/M. Tables A1/A2 retain frozen statistics and sensor boundaries. The inventory is explicitly descriptive and non-exhaustive.

## Caption and scientific-boundary preservation

- M4 retains both estimates/CIs, exact-pair counts, separate studies/sessions and the exclusion of workload-only causality.
- Translation uses “does not survive the tested stateful integration” in its manuscript caption, aligning with PR #24 without modifying the asset or its historical caption source. Component signals, evaluation arrows, blocked RTX, diagnostic B570, combined OpenVINO replay/proposal, normalized complete costs, committed correction/bonus output, independent M4, non-exhaustiveness and prefill/loading exclusion remain explicit.
- Verification retains context cells/ranges rather than confidence intervals, open/filled qualification, scoped exactness, secondary RTX and inadmissible B570. Its 1x line is a target-decode-step reference, not profitability parity; the proxy is not complete target-side cost.
- State retains Phase-1 versus Phase-3 boundaries, arithmetic totals 13.25/27.54 s against 9.58 s, target/replay shares, prompt-GM estimates and CIs, residuals, inseparable replay/proposal and the distinction between bar aggregates and headline estimators. No intrinsic NPU weakness or measured persistence benefit is claimed.
- Accounting remains a measurement method. No equation novelty, cross-stack hardware causality, acceptance-as-committed-progress substitution or estimator harmonization was introduced.

## Runtime and independent hardware coherence

Section 7's requirements, persistent-state interface, correctness-qualified path registry and planned evaluation remain intact. Its only substantive wording update makes a new frozen software study explicit and disallows retrospective rescue of the closed hardware campaigns. The section is still proposed/unmeasured and occupies its normal span across pp. 7–9. No runtime result is fabricated and no text is compressed to reduce page count.

The full paper remains coherent before software results are added. The separate compile-time hardware-only check removes the runtime reservation and leaves 8 body pages plus 1 reference page with resolved references and a complete observation-to-diagnosis-to-synthesis argument. The collaboration manuscript itself retains the full reservation.

## Validation and layout

`make all`, `make hardware-only`, and unmodified-invocation `make check` pass. Results:

- Full: 10 body + 1 reference page; separate appendix: 3 pages.
- Original numerical validator unchanged: 228/228 checks pass.
- Narrative: 260 protected-file checks, all 57 prior prose numerical macros, unchanged scientific ledger/source records and complete figure tree.
- Figures: five original independent numerical replays retained; active v0.4 artists checked against frozen data; final mechanism hash/text checked; four actual PDF placements at native widths checked; 11 lookup cells, five legacy ranges and eight inventory cases checked.
- PDFs: anonymous text/metadata/links, embedded fonts, 13 complete-author references, zero overfull boxes, zero undefined references/citations, expected semantic figure/table numbers.
- All 11 main pages and 3 appendix pages inspected after the final build. Verification also inspected in 96-dpi grayscale. No clipped text, overlapping labels or detached captions. The final body page's unused right column and normal appendix float spacing are accepted for this initial draft; no template or figure-font adjustments were used.

The figure validator was extended for the newly active assets and appendix objects; historical numerical replays and hash protections remain. The narrative scope now uses the exact current-main baseline and admits the historical review file plus integration records. This resolves the earlier review-document path issue directly; no numerical assertion was removed or in-memory exception used. The protected tree expanded to include all final mechanism assets.

QA receipts: `evidence/NUMERICAL_QA.json`, `NARRATIVE_V03_QA.json`, `NARRATIVE_FIGURE_V03_QA.json`, `PDF_QA.json`, and `NARRATIVE_OVERLEAF_V03_QA.json`. Raw/processed science, closeouts, the original numerical validator and official style remain unchanged. No experiments were rerun.

## Overleaf handoff

`make overleaf` creates `manuscript/output/overleaf-initial-draft-v0.3.zip` with 35 required source/dependency files. Only relative dependency paths are relocated; selected publication assets and official style files retain their bytes. The extracted package compiles independently with pdfLaTeX/TeX Live 2025. Both resulting documents match the delivery PDFs' page counts and page-by-page text. SHA-256 manifests are included; the package QA receipt records its hash.

The initial draft is ready for shared editing. Upload the ZIP, set `main.tex` as the main document, and use `appendix.tex` for the separate appendix. No actual shared Overleaf project was created or uploaded. The title, abstract and final submission decisions remain provisional, and the runtime contribution remains unimplemented/unmeasured.
