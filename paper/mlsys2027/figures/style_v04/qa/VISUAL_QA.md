# v0.4 native-width visual QA

PASS for the seven candidates at the widths encoded in their PDFs. Color and grayscale artwork were inspected at 96 dpi; 180-dpi renders are also generated for detail. The seven captioned proof pages were inspected in grayscale. Screen zoom is not a calibrated physical-size claim; print at 100% to preserve the checked PDF dimensions.

| Candidate | Width | Color / grayscale | Check |
|---|---:|---|---|
| Figure 1 A | 6.75 in | PASS / PASS | Plain tabulation, no arrows/headline; all values and statuses readable. |
| Figure 1 B table | 6.75 in | PASS / PASS | True booktabs source; same cases/values, more compact than A. |
| Figure 1 B prose | 3.25 in | PASS / PASS | Complete optional replacement paragraph; superscript inset prevents crop-edge clipping. |
| Verification | 6.75 in | PASS / PASS | Eleven cells (some overlap), context ranges, 1× reference, filled/open and circle/square semantics; both B570 rows explicitly inadmissible. |
| M4 | 3.25 in | PASS / PASS | Thin original CIs, compact labels, single reference; counts retained in caption. |
| 358H | 6.75 in | PASS / PASS | CPU black circle/NPU blue diamond; CI marks, hatched target segments, uninflated residuals, shared baseline and distinct prompt-GM labels. |
| Appendix table | 6.75 in | PASS / PASS | Eight cases with frozen classifications and exactness; no awkward word break in RTX exactness cell. |

No internal dashboard titles, colored prose, decorative arrows or explanatory footer blocks remain. All annotation text fits its canvas. The baseline is masked only behind the CPU label so the dashed line does not cross its digits. Line widths are thin and consistent. Tables are monochrome. Typography remains Times-compatible at 8–9.5 pt for artwork; no text was shrunk to solve a collision.

Independent checks inspect actual artist coordinates/CI segments/bar widths, compiled table/prose text, vector-only PDF/SVG, embedded PDF fonts, PDF text bounds and exact output hashes. SVG glyphs are outlines. `validation.json` records all seven passes. The residual segment is physically subpixel in print at the actual measured scale; its numeric value remains in the caption, and its vector width is checked directly.

`STYLE_PROOF.pdf` includes every candidate with required caption context. It is a review proof, not a rebuilt manuscript. Figure-only removals/replacements require a separate integration decision; current manuscript prose and wrappers remain frozen. Original source/provenance pointers and confidence intervals remain unchanged. No experimental or statistical reanalysis was performed.
