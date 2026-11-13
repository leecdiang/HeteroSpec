# Final release validation — 11 November 2026

## Delivered documents and layout

- Main manuscript: 10 pages, including references, in IEEEtran's official `10pt,journal,compsoc` mode.
- Standalone supplement: 5 pages, with its own bibliography and S-numbered figures/tables.
- Main figures 1–6 appear on pages 2, 4, 7, 7, 8 and 9. All results figures precede the conclusion and bibliography.
- Six main figures, three supplementary figures, two main tables and eleven supplementary tables are included.
- The complete 15-page release was rendered and inspected. The final targeted inspection covers the repositioned application/width figures, short headings, intact conclusion and balanced reference columns.
- The class controls the body font, leading, columns and margins. An IEEEtran reference-break command balances the final columns; a space reservation keeps the conclusion together.
- Both final logs contain zero LaTeX warnings, unresolved references, duplicate labels, missing characters, overfull boxes or underfull boxes.

The vector figure exports cause two pdfTeX page-group notices in the main paper
and one in the supplement when several PDFs share a page. The rendered figures
and complete pages were inspected; there is no clipping or compositing defect.

## Numerical fidelity

- All **35 data/evidence tests pass**.
- All **22 inherited numeric inputs** retain their original Git blob and SHA-256 identities: 19 original data files and three published projections.
- All **128 B2 operation records** retain the source blob identity. The four process-cluster geometric summaries are reconstructed from the records, with all 16 process ratios retained.
- The independent claim check reconstructs the displayed application reductions, direct factorial effects, mixed-Q4 service comparisons, live-width results, workload counts, phase deltas and boundary frequency.
- Original estimands, multiplicity families and interval provenance remain recorded. No new GPU inference or experimental sample was generated during this rewrite.

## Figures

- All **nine figure PDFs** are vector exports with embedded fonts and no raster images.
- All expected plotted observations are present; the checker reports **zero clipped markers**.
- Canvas bounds, text overlap, figure references and original input identities pass.
- PDF/SVG/300 dpi PNG versions are included with their generating Python code.
- The actual PDF renders and grayscale encodings were inspected. Text, position, marker shape, fill and hatching supplement the retained blue/ochre/green palette.

`FIGURE_MANIFEST.json`, `generated/FIGURE_PDF_CHECK.json` and
`generated/FIGURE_LAYOUT_CHECK.json` retain the per-figure details.

## Clean-extraction builds

Two archives were extracted into separate fresh directories:

1. **Full author package:** `bash build.sh` rebuilt numerical projections, tables, all nine figures and both PDFs, and reran all 35 evidence tests successfully.
2. **Compact LaTeX source:** `bash build.sh --tex-only` rebuilt both PDFs from the bundled vector figures and generated table macros.

Both clean builds preserve the delivered 10/5-page counts, exact extracted page
text and all 15 rendered pages at the checked 72 dpi. All nine regenerated figure
PDFs preserve the delivered text and rendered appearance.
`CLEAN_EXTRACTION_CHECK.json` records the exact outcomes, including whether each
complete PDF is also byte-identical. The full build requires no network, model
weights or GPU execution.

Archive membership and every archived file's bytes were compared with the
staged source project after the final validation records were added. The compact
archive intentionally contains the TeX compilation inputs; the full package also
contains raw numeric projections, figure source, editable graphics and reviews.

## Writing and primary sources

The abstract, seven main sections and supplement received the completed
Humanizer/concise-writing pass, followed by a scientific-fidelity review. Ten
actual scientific/writing skills and their pinned sources are recorded in
`SKILLS_APPLIED.md`. All 16 bibliography entries have verified primary identities.
The TPDS mode was checked against the current official author guidance and the
actual official template download.

After that pass, the final assembly shortened headings, clarified one related-work
sentence, repositioned wide figures and balanced references. These edits preserve
all numerical results and experimental interpretations. The handoff hashes in
earlier review reports identify those earlier checkpoints; final source/PDF hashes
are in `../REWRITE_EVIDENCE.json`.

## Evidence cutoff

The manuscript starts from PR #220 at
`8aea751bde42cd69bf923ed4524972f9af98d694` and includes the completed B2 panel from
PR #218 at `4fe337a8ff349d547023f9dd60b8e114e5323207`. The latter head and completion
status were checked at 09:13:56 UTC on 11 November 2026. Its S1/S2 operator evidence
and B2 width panel are complete; the full-model S3 strong-loop service stage was
still running. The manuscript preserves that distinction.

## Recovery completion

The interrupted rewrite was recovered and reviewed independently again. Only first-use acronym definitions changed. All 35 evidence tests pass again; the resulting main PDF remains 10 pages, with only pages 1–2 changing in the rendered output. The five-page supplement is byte-identical. `RECOVERY_CONTENT_REVIEW.md`, `RECOVERY_VISUAL_REVIEW.md`, and `RECOVERY_VALIDATION.json` record the additional checks. The clean-extraction record is refreshed for the final recovery archives.
