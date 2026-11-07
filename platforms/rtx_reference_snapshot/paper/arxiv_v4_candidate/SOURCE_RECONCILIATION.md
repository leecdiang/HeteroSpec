Current revision: see `anc/review_round3/QA_FINAL.json` and the repository synthesis. The records below document earlier rounds; they do not describe the current PDF hash or unchanged figure-source status.

# v3 → v4 source reconciliation and release review

Historical first-pass record below. The 2026-10-21 cross-review refinement is recorded in `anc/review_round2/REVIEW.md` and `QA_FINAL.json`; its current figures include documented presentational changes, so the first pass's byte-unchanged-figure statement is not a claim about the refined files. Scientific data are preserved.

## Editing baseline and scope

The user-uploaded `HeteroSpec_arXiv_Submission_RTX104_Consolidated_20261015(1).zip`
is the editing baseline. Its complete 62-member inventory and SHA256 are in
`anc/review/V3_SOURCE_IDENTITY.json`. An untouched build produces 17 pages and
passes the original 357 checks and 16 tests. Public arXiv v3 title, abstract and
section structure were checked; public source-tar byte identity was not authenticated.

The previous PR138 draft is replaced, not patched as though it preserved all v3
content. The complete original methods, qualification tables, state matrices,
regressions, references and supplementary sections are restored first.

## Section-by-section disposition

| v3 source | v4 location | Disposition |
|---|---|---|
| Introduction | §1 | Keep the method and prior-work contrast; add the distinct service questions. |
| Reference and execution model | §2 | Preserve complete endpoint, state transaction and composition definitions. |
| Phase-scoped query-layout design | §3 | Preserve address/mask equations, proof, domain guards, phase/cache obligations and finite mask experiment. |
| Experimental design | §4 | Preserve original k3 resident-request protocols and weighting; add explicitly separate follow-up roles. |
| Numerical preservation and repair cost | §5 | Preserve complete original results, seven-arm comparisons, all six E2 sessions and 72-context replay. |
| State formation and transfer | §6 | Preserve original state and backend failures; add scoped GQA/AV repair without retroactive qualification. |
| Architectural implications | §9 | Preserve same-capability baselines and limits; integrate the new request results without claiming hardware benefit. |
| Related work and scope | §10 | Retain every original reference and original scope limit; add service-window and incomplete-follow-up limits. |
| Conclusion | §11 | Separate local layout benefit, net draft value and hardware evidence. |
| S1 implementation | S1 | Complete finite mask/width history retained. |
| S2 CUDA costs | S2 | All original output and 21 cost-comparison cells retained. |
| S3 RTX replication | S3 | All six-session estimates, confidence intervals, task ratios and E1 coverage retained. |
| S4 Vulkan state | S4 | All partition schedules, projection differences, shams and controls retained. |
| S5 components | S5 | All 80 cells, nonmonotonic examples, 44/112 coverage and missing-vector limits retained. |
| S6 backend port | S6 | Complete stopped pilot and necessary-support-condition audit retained. |
| S7 reproduction | S9 | Access/history retained; new experiment and manuscript-audit identities added. |

New §7/S7 contain mapping/replay/representation/observer evidence. New §8/S8
contain complete finite-panel service contracts, all eight input aggregates and
all 32 input/session blocks. All 56 original source labels and all 25 original
bibliography keys remain. All eight original figure files are byte-unchanged.
The original 15 report-data CSV/JSON files tested by the preservation audit are
unchanged; exact evidence and file hashes are in `SOURCE_RECONCILIATION.json`.

## Corrections to the earlier candidate

1. An unescaped percent sign had truncated the earlier abstract in TeX. Every
   percentage is now escaped and the complete abstract was inspected in the PDF.
2. Original implementation detail, state matrices and most original figures had
   been omitted. They are restored rather than summarized away.
3. The manual ratio drawing used inconsistent coordinate distances. The new
   figure uses explicit PGFPlots numeric axes, saved block data and labelled
   log scale for the speculative-service panel. No confidence bars are invented.
4. The HumanEval/65 B570 ratio is 0.9920027931021794, rounded to 0.992003, not
   0.992060. The source ratio and all other cells are regenerated from saved CSVs.
5. RTX compact-QH ratios 1.002216/1.001598 compare with QB_A, not a dual-QB mean.
   Corresponding QB_B ratios are shown separately.
6. Draft1's complete negative result is distinct from the separate draft-prefill
   submission follow-up. The latter is qualified but has no complete clean timing
   record in the reviewed PR135 tree. The tested baseline is not called optimal.
7. The new service-reference vector comparisons are tied to matching R/PQ
   references; they do not assert every speculative row equals a serial-R row.
8. Build warning detection uses real TeX log syntax. A missing library or overflow
   cannot pass merely because the checker searches for the wrong escape sequence.

## Language and visual review

The scientific content was frozen before a 20-passage academic-English edit
using the retrieved Humanizer 3.1.0 workflow. All numeric multisets, formula
payloads and citation/label/input sequences remain unchanged during that pass.
The review record contains exact before/after passages and hashes. This is
language editing, not an AI-authorship test.

The complete 23-page PDF was rendered and inspected, including all ten figures
and the full supplementary tables. An orphaned conclusion ending was removed
and the final supplement columns balanced. All fonts are embedded; no text
falls outside the page. Build logs have zero overfull boxes, missing glyphs or
unresolved citations/references. Report checks pass 484/484; tests pass 25/25.

## Release decision

Ready for author/peer review, not automatically submitted to arXiv. No new
experiment is required for the stated finite-panel claims. Stronger claims about
an optimized serving ceiling, physical bottlenecks, unseen inputs or hardware
benefit remain unestablished and are not made. The paper source/visual audit is
not external authentication of the experiment machines' full raw archives.
