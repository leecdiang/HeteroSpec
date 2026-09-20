# Paper-size color and grayscale QA — v0.3

Status: **PASS / PUBLICATION-CANDIDATE** for four selected main assets and one appendix asset. This is not a claim of integrated manuscript pagination or author acceptance.

The committed manuscript PDF and TeX figure sources were inspected directly. Selected vector PDFs were rendered by Poppler at 96 and 180 dpi, in color and grayscale, at their native insertion widths. All selected color/grayscale artwork and the three native-width proof pages were inspected. Same-width OLD/SELECTED comparison sheets were inspected in color; grayscale status checks used the native-size grayscale outputs. OLD native manuscript pages were inspected as well. Physical sizes are encoded in the PDFs; screen zoom is not a claim of calibrated physical display size.

| Asset | Width × height | Color | Grayscale | Specific check |
|---|---|---|---|---|
| Figure 1 | 6.75 × 3.63 in | PASS | PASS | Four aligned cases; no common metric axis; M4 shared micro-study qualifier visible; blocked RTX has no speedup. Filled/open + text distinguish qualification. |
| Figure 2 | 6.75 × 3.58 in | PASS | PASS | Ranges/cells and explicit statuses readable; filled/open and circle/square redundant with text/line style. Context and proxy limitations visible. |
| Figure 3 | 3.25 × 2.40 in | PASS | PASS | Compact hybrid: two forest rows, asymmetric CIs, direct estimates/exactness and clear 1× line. Functional-correctness caveat retained in caption. |
| Figure 4 | 6.75 × 3.75 in | PASS | PASS | Totals, baseline and separate prompt-GM headlines readable; true-width residuals labeled; component hatching and CPU/NPU shapes survive grayscale. |
| Figure 5 / A1 | 6.75 × 4.10 in | PASS | PASS | Categorical positions, explicit status and evidence classes; neither B570 diagnostic appears qualified. Appendix-only placement avoids a repeated main overview. |

No text extends outside exported canvas bounds. PDF resources are vector-only; text uses embedded STIX TrueType fonts and SVG glyph paths. White background, restrained blue/gray, no gradients, shadows, vendor colors, or color-only status distinctions.

The additional five-page `figure_story_proof.pdf` places the selected artwork with its proposed captions at the same physical widths. All five grayscale pages were inspected; no clipping, overlap or overfull TeX boxes were found. This is a figure-only narrative proof, not rebuilt manuscript pagination.

The actual old Figure 4 already uses absolute time. The choice of NEW is based on its visible totals, baseline, intervals and estimator labels, not an invented old normalization defect. OLD Figures 1/5 are enlarged only on equal-width comparison sheets, explicitly labeled; the native OLD proof retains 3.25-in width. The independently checked comparison geometry confirms all 20 panel placements use the intended equal widths.

Reviewer-overreach pass: overview values are heterogeneous summaries; micro cost is not complete target work; exactness is workload/path-scoped; M4 studies do not identify workload-only causality; post-prefill time is not whole-request latency; replay-only time is unmeasured; appendix rows are not universal causal categories. Caption suggestions carry these limits. No new scientific claim is introduced by the redesign.
