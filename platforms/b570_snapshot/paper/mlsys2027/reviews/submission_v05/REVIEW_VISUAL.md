# Reviewer H: visual communication audit

## Scope and verdict

Reviewed the actual 11-page `paper/mlsys2027/manuscript/output/manuscript-v0.4.pdf`: ten body pages and one reference page. The filename is v0.4, but the rendered Figure 2 is the selected mechanism diagram referenced by the current source. Read `main.tex`, all ten main section sources, the four included figure wrappers, and the Section 7 table source. No other reviewer reports were read.

**Verdict: visually usable, with targeted presentation revisions recommended; no observed clipping, overlap, missing glyph, or illegible primary result that blocks reading.** The four-figure hardware sequence is coherent. Keep the Section 7 results as a table; a new runtime results plot would add little and could blur the distinction between speedup and oracle regret. The highest-value refinements are explicit table direction cues, caption hierarchy, and final-page balance. These recommendations change presentation only and do not reopen closed findings.

## Inspection record and limits

- Visually viewed PDF pages **1, 2, 3, 4, 5, 6, 7, 8, 9, 10, and 11** as 120-dpi page rasters using `pdftoppm` and `view_image`.
- Additionally viewed **pages 4, 5, 6, 7, and 9 at 72 dpi in grayscale**, retaining complete page geometry: Figure 1, Figure 2, Figure 3, Figure 4, and runtime Table 3, respectively. This checks native column/text-width placement without evaluating enlarged standalone assets alone.
- Temporary renders are outside the repository in `/workspace/scratch/3a33e8c9848c/visual-review-original/`. Truncated intermediate PNGs were rerendered under distinct reviewer prefixes before inspection; no conclusions rely on a failed image load.
- This is an on-screen PDF inspection, not a physical print proof, calibrated contrast measurement, assistive-technology audit, experiment replication, or validation of the underlying numerical evidence. A 72-dpi raster is a conservative screen proxy, not a guarantee of physical display scaling. The separate appendix was not inspected. References were checked for visual layout only, not bibliographic accuracy.

## Page-level presentation

| PDF pages | Observation | Recommendation |
|---|---|---|
| 1 | Long full-width abstract and dense introduction, but clean title hierarchy and stable margins. | No layout repair needed. Content compression could help scanning, but does not require a new visual. |
| 2-3 | Definitions and methodology are dense; equations remain legible. Table 1 spans both columns cleanly and preserves platform scope. | Keep table width and font size. Do not shrink these to recover space. |
| 4 | Table 2 and Figure 1 create a useful numerical overview followed by a simple visual contrast. Table 2's `Second.` and `Diag.` abbreviations are more compressed than its other labels. | If adjusting the table, prefer readable evidence-class labels or a compact key; preserve correctness beside timing. |
| 5 | Mechanism Figure 2 anchors Section 5, but the diagram and its nine-line caption occupy a substantial fraction of the page. | Retain the diagram; tighten duplicated prose across caption and adjacent section while retaining essential scientific qualifications. |
| 6 | Figure 3 is spacious, aligned, and adjacent to the qualification discussion. Its long caption carries much of the encoding explanation. | Put a short encoding key near the plot if revising the asset; retain the detailed caption distinctions. |
| 7 | Figure 4 dominates the upper page and has the longest caption. The Section 7 introduction begins low in the right column and continues on page 8. | Keep the two-panel visual; improve caption hierarchy before adding any new material. The section break is acceptable. |
| 8-9 | Section 7 is mostly prose; Table 3 appears at page 9 top left, shortly after its first callout on page 8. This is a reasonable float distance. | Table 3 needs clearer metric direction, not another plot. |
| 10 | The last body page uses only the left column, which ends well above the bottom; the whole right column is blank before references are forced onto page 11. | Consider ordinary final-page column balancing if allowed by the conference style. This is a polish issue, not evidence of a page-limit violation. Do not add content merely to fill it. |
| 11 | References fit one page. URLs wrap, including a continuation at the right-column top, but no clipping was observed. | No visual correction required. |

## Four hardware figures: sequence, scale, and captions

### Figure 1, page 4: opposite M4 regimes

The one-column two-row interval plot makes the central contrast immediately visible. The parity line is clear, intervals are visible, and the workload labels are legible at native column width. Grayscale loses no information because the two outcomes are separated by position and labeled directly. The caption correctly retains token equality, separate-study status, campaign-specific intervals, and the lack of workload-only causal identification.

The caption is visually heavier than the minimal plot. There is also generous space between the axis label and caption. If polishing, modestly trim internal empty space and remove repetition shared with Section 4.1, while retaining the separate-study and token-equality qualifications. There is no reason to add more plotted categories or force this into a hardware ranking.

### Figure 2, page 5: local opportunity to realized outcome

The full-width diagram is a useful bridge from the M4 contrast to the two diagnoses. Four stages, restrained arrows, the blocked/diagnostic branch, and the separated M4 outcome text support the intended reading. It does not visually assign either diagnosed mechanism to the M4 contrast. Terms in the stateful-realization box connect to the accounting definitions.

At 72 dpi, the smallest explanatory text and math subscripts require more attention than the section prose, although the stage headings and route remain readable. Preserve the full text width; reducing the diagram to one column would be harmful. Pale rules and the small blue qualification marker are faint in grayscale, but they carry no indispensable meaning because boxes, labels, and arrows remain. The nine-line caption repeats several statements already inside the diagram and nearby text. This is a density issue, not a need for more boxes or arrows. Any compression must retain that arrows are evaluation boundaries, measured mechanisms are non-exhaustive, and blocked timings remain diagnostic.

### Figure 3, page 6: verification opportunity versus qualification

This is the strongest status-aware encoding: filled versus open marks, circles versus squares, and direct status labels together separate qualified, blocked, secondary, and diagnostic paths. The right-side labels prevent a fast but inadmissible mark from being read as a usable optimization. Grayscale preserves these distinctions. The one-step reference and common axis support the intended physical-proxy comparison without turning it into a hardware leaderboard.

Two limitations remain visible. Very close context cells merge at native size, especially the serialized B570 marks and near-one-step cells; the caption acknowledges this and points to the lookup. Range segments can initially resemble confidence intervals until the caption is read. An optional compact in-plot key such as “marks: context cells; spans: measured range” would reduce that initial ambiguity. Do not jitter the values in a way that implies new quantitative separation. Native width is appropriate, and no font reduction is advisable.

### Figure 4, page 7: isolated advantage versus realized cost

The paired panels effectively explain why isolated throughput and integrated timing cannot be interchanged. Panel (a) uses circle/diamond shape as well as color; panel (b) uses solid fill versus hatching. Both survive grayscale. The baseline line and direct total labels are clear. The small residuals are handled numerically in the caption instead of being enlarged misleadingly. The replay-plus-proposal segment remains combined, consistent with the stated measurement boundary.

The caption is the main weakness: roughly eleven full-width lines combine the takeaway, estimator explanations, scientific boundaries, percentages, residuals, intervals, and plot-reading notes. Preserve the arithmetic-mean versus prompt-GM distinction prominently because speedup labels sit over arithmetic-time bars. Move secondary detail to adjacent prose or the existing appendix only if the retained caption remains self-contained about measurement boundaries and uncertainty. Short descriptive panel headings could improve scanning, but another quantitative panel is unnecessary. Tiny interval bars in panel (a) are hard to resolve at native size; that reflects the displayed scale and should not be “fixed” by magnifying the uncertainty independently of the axis.

## Section 7 runtime presentation

Table 3 on page 9 is compact and readable at native column width. It presents the two prospective speedup estimates and the descriptive oracle comparison with their intervals, while the caption identifies direct-token exactness and the distinct oracle meaning. Its precision and estimator context are better served by a table than by a bar chart.

The material communication risk is that the first two rows are target/condition ratios, where larger indicates greater speedup, while the third is Guard/offline-oracle latency, where closer to one is preferable. The shared `Latency ratio` / `GM` headers and uninterrupted rows invite a hurried reader to compare all three as the same kind of success metric. The caption does explain the difference, so this is not an incorrect table. A small presentation revision would make it safer:

1. Group the first two rows under “Speedup versus target-only (higher is better).”
2. Separate the final row with a little space or rule and label it “Latency relative to offline oracle (lower is better).”
3. Preserve the existing values, intervals, exactness statement, and hindsight qualification without inventing a direct Guard-versus-Always-Spec comparison.

**An extra runtime results visual is not materially necessary.** Plotting the same three ratios together would amplify the mixed-direction problem. A small control-flow sketch could be optional if policy comprehension becomes a demonstrated reader problem, but the present prose already states when Guard first decides, what it compares, and that fallback is permanent. Such a sketch would not establish additional experimental evidence, and it should not displace the stronger hardware figures or their qualifications. Retain the table, improve its grouping, and use prose to preserve the explicit statement that Guard is profitable against target-only while fixed speculation has the higher aggregate point estimate.

## Prioritized disposition

- **Recommended before final submission:** clarify Table 3's row groups/direction; improve Figure 4 caption hierarchy without dropping measurement qualifications.
- **Useful polish:** balance the final body page if style permits; reduce repeated prose and surplus internal space around Figures 1-2; add a compact range-versus-CI key to Figure 3 if the asset is otherwise revised.
- **Keep:** the four-figure sequence, native widths, filled/open and shape encodings, hatched cost decomposition, the one-column runtime table, and all closed scientific findings.
- **No new experiment, new number, extra runtime plot, or figure redesign is required by this visual audit.**
