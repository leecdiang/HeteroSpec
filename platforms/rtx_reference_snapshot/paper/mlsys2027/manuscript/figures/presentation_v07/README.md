# Figure 3 v0.7

Run `python figures/presentation_v07/plot.py` from the manuscript directory,
then `python figures/presentation_v07/validate.py`.

Native PDF: 6.75 x 2.12 inches. Vector PDF and SVG; embedded STIX fonts;
white background, muted ink/accent, grayscale-safe shapes and status text.
The v0.5 assets remain byte-identical; M4, 358H and the mechanism schematic
are not regenerated.

Panel A reads the original 11 unrounded target-forward micro cells from
`paper/mlsys2027/figures/data/figure2_micro_cells.csv`. A diamond is the M4
reference, circles fast/batched paths, squares serialized paths. Every mark
is filled: fill carries no historical qualification meaning. Segments span
context observations, not confidence intervals. Vertical offsets preserve
every cell's horizontal coordinate.

Panel B reads two frozen formal analysis JSONs through the sourced record
projection. It displays four candidate paths, direct-ID exact pairs, and
the 90/90 qualification boundary. Open circles and BLOCKED labels identify
three failing paths; only RTX serialization is a filled square and QUALIFIED.
No confidence interval or hardware performance ranking is inferred.

The two panels are separate study families, not same-run cost/correctness
measurements. Micro cost is neither complete target-round cost nor end-to-end
speedup. The caption and manuscript explicitly preserve this boundary.

`qa/verification.json` records data hashes and artist coordinates;
`qa/validation.json` independently checks sources, all cells, counts, labels,
status, dimensions, vector output and fonts. Native 96/200 dpi color/grayscale
PNGs are supplemented by actual PDF renderings from `scripts/render_v07.py`.
Visual disposition is recorded in the v0.7 visual review and evidence receipt.
