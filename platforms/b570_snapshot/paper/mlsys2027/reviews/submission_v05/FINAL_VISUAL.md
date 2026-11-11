# Final visual QA — submission v0.5

Verdict: PASS. No material layout or visual-readability issue requires a manuscript change.

## Inspection performed

All 15 pages were actually opened as page images with `view_image`: main pages 1–11 and separate appendix pages 1–4. The supplied `main-05.png` and `main-10.png` were truncated render artifacts; pages 5 and 10 were independently re-rendered from `manuscript/output/manuscript-v0.5.pdf` at 110 dpi and inspected as `v05-render/qa-p5-05.png` and `qa-p10-10.png`. This was a raster-output problem, not a PDF-layout defect. Main pages 6–7 were additionally rendered with `pdftoppm -gray` and visually inspected.

| Pages actually viewed | Findings |
| --- | --- |
| Main 1 | Title, author block, abstract, opening columns and anonymous footnote fit cleanly. |
| Main 2 | Equations and numbering fit the columns; no collision or clipping. |
| Main 3 | Table 1 is readable, aligned, and contained within the text width. Normal dense two-column body layout. |
| Main 4 | Figure 1 labels, parity line and intervals are legible; full caption is attached and readable. Paragraph continuation below the float is visually ordinary. |
| Main 5 (regenerated) | Table 2, Figure 2 and caption fit without overlap. Diagram text is smaller than body text but remains readable; no artwork modification needed. |
| Main 6 | Figure 3 markers, axis and row status labels are clear. Caption explicitly identifies range segments and comparator scope. Grayscale retains open/filled and circle/square distinctions. |
| Main 7 | Figure 4 panel labels, legend, baseline and bar annotations fit. Grayscale retains circle/diamond and solid/hatched distinctions. Dense caption is readable and separated from body copy. |
| Main 8 | Long section and subsection headings fit; standard two-column text with no clipped lines. |
| Main 9 | Table 3 ratio grouping is clear: Target/Guard and Target/Always-Spec are under “Speedup versus target-only (higher is faster)”; Guard/offline oracle is separated by a rule under “Descriptive hindsight latency ratio.” Values and CI columns align. The float leaves some white space, but no material reading problem. |
| Main 10 (regenerated) | Limitations and conclusion finish on body page 10. A partly empty final column is acceptable; nothing spills onto the references page. |
| Main 11 | References occupy one page; wrapped URLs and the across-column entry continuation remain inside the margins. |
| Appendix 1 | Title, sections A–D and anonymous footnote fit cleanly. |
| Appendix 2 | Tables A1–A2 and lower prose are readable; no row/caption collisions. |
| Appendix 3 | Tables A3–A4 fit with comfortable separation. A4 has some narrow-column word wrapping, but labels remain understandable and no content is clipped. |
| Appendix 4 | Section H finishes cleanly; unused lower-page space is acceptable. |

## Page budget and scope

The viewed main PDF consists of 10 body pages followed by 1 references-only page. The separately viewed appendix has 4 pages. Thus the requested body ≤10 + references 1 + appendix 4 arrangement is visually satisfied.

This is an on-screen visual review of rasterized PDF pages, not a physical print proof, accessibility audit, font-embedding audit, or independent numerical/statistical validation. Grayscale was directly checked for Figures 3–4 (main pages 6–7), not every page. Existing artwork and manuscript source were left untouched. No cosmetic edits are recommended before submission on the basis of this review.
