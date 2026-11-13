# Scientific figures

The six main figures follow the manuscript argument: observed dependency,
execution method, component attribution, opportunity for local cuts, complete
application value, and the distinction between execution efficiency and live
work. Three companion figures retain mixed-quantization service, the complete
width-cost balance, and historical geometry.

## Reproduction

From the author-package root:

```bash
python scripts/build_figures.py
python scripts/check_figures.py
```

For actual PDF rasterization and a grayscale review sheet:

```bash
python scripts/check_figures.py --render
```

The builder uses Python, NumPy and Matplotlib. It saves editable SVG, vector PDF
and 300 dpi PNG for every figure. It uses the P052 font family when installed,
with STIXGeneral as the plotting fallback. Inkscape/Cairo exports the SVG to PDF
with embedded fonts. If Inkscape is unavailable, the builder uses Matplotlib PGF
with pdfLaTeX and `mathpazo`. The Inkscape path avoids the CFF/OpenType font-type
mismatch produced by direct Matplotlib PDF export with this P052 installation.

The checker additionally uses PyMuPDF and Poppler's `pdffonts`. Pillow is needed
only for the optional rendered previews. No network request, model loading,
GPU measurement or resampling of the published statistical intervals occurs.

## Figure map

| File stem | Size, inches | Evidence and retained observations |
|---|---:|---|
| `extent_intervention` | 6.875 × 2.50 | Measured positions 765–768; extents 768/1024; own-path and exchanged-extent native AV replay; saved output indices 29 and 81. |
| `execution_method` | 6.875 × 3.72 | Ordered physical groups, whole/local cut placement, separate arithmetic grouping at a=4 and a=1, and one resident owner. The eight-column grouping is a schematic. |
| `factorial` | 6.875 × 3.28 | Eight fixed-factor comparisons and all 128 task-root ratios. Original 99% adjusted intervals; the two intervals crossing 1 have hollow markers. |
| `geometry_opportunity` | 6.875 × 3.02 | Natural 20/2,224-cycle opportunity and 2,244/2,224 physical-call census, beside all 12 controlled B570 cells. Segments show the min–max of three paired observations. |
| `service_controls` | 6.875 × 3.35 | All 12 fixed target-only comparisons and all 176 published root ratios; original 99% adjusted intervals and ratio-of-total estimates. |
| `width_tradeoff` | 6.875 × 3.58 | All four equal-work cells and 16 origin ratios; four live k7/k3 comparisons with original 98.75% intervals; absolute cycle, verified-row and proposal counts. |
| `mixed_q4` | 3.35 × 3.15 | All six request-service arms and all 24 exposed-root means. The grouped D4 penalty relative to the fastest M remains visible. |
| `supp_width_cost` | 3.35 × 2.48 | Signed Local-packed k7−k3 host-phase deltas, including the negative draft-sync delta, residual costs and complete-service total. |
| `supp_historical_geometry` | 6.875 × 2.45 | All 14 measured historical cells, their inside controls and the explicitly unmeasured cell. |

`generated/analysis.json` contains the inherited numerical summaries.
`data_added/application_root_ratios.json` supplies the published individual
application ratios. The new `data_added/rewrite_figure_sources.json` records
exact pinned sources for the extent example, natural opportunity census,
arithmetic grouping and phase interface; it adds no measurements. The physical
width q and the weight format Q8_0 remain distinct.

`revision/FIGURE_INPUT_IDENTITY.json` preserves Git-blob and SHA-256 identities
for all 22 restored numerical input files. `FIGURE_MANIFEST.json` records the
input hashes, physical size, exporter and actual plotted-marker coverage for
each output. `generated/FIGURE_LAYOUT_CHECK.json` records text bounds;
`generated/FIGURE_PDF_CHECK.json` records the delivered PDF checks.

## Visual conventions and checks

The palette and P052 typography retain PR220's visual language: blue `#3F6C9B`,
green `#4F7F5F`, ochre `#B8753B` and neutral gray `#62696D`. Color is redundant
with panel position, labels, marker shape, marker fill or hatching. Physical
extent 1024 uses diagonal hatching; factor-model estimates use diamonds or
squares; controlled inside appends use hollow circles. The source was checked
in grayscale as well as color. The plots do not depend on red–green separation.

PDFs contain vector graphics and embedded fonts. Main-figure text is 7.7–9.2 pt,
apart from the deliberately larger natural-opportunity count. Single-column
supplemental labels are at least 7.4 pt. The checker verifies source identity,
scatter coverage, text bounds and overlap, referenced exports, physical sizes,
font embedding, valid extracted text and the absence of rasterized PDF panels.
These checks supplement inspection of actual PDF renders and compiled pages.

Natural opportunity counts, controlled append latency, full request service,
equal-work operations and live work counts occupy separate panels with their
own units and cohorts. Confidence intervals remain those of the original
studies. The controlled three-repeat ranges and descriptive exposed-root panels
are not assigned new population intervals. No uncertainty is invented for the
exact work counts or schematic diagrams.
