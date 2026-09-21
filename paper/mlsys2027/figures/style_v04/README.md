# Restrained scientific figure candidates v0.4

Exact base: `afda6a192f3e9359eb5f5d7d24d3313bf59ef2f3` on `paper/mlsys2027-narrative-v0.2`. This directory adds style alternatives without modifying the validated scientific tables, existing assets, provenance pointers, manuscript prose or figure wrappers.

| Candidate | PDF | SVG | Recommendation |
|---|---|---|---|
| Figure 1 A, restrained figure | [PDF](pdf/figure1A.pdf) | [SVG](svg/figure1A.svg) | Alternative if an overview float is retained |
| Figure 1 B, booktabs table | [PDF](pdf/figure1B_table.pdf) | [SVG](svg/figure1B_table.svg) | Alternative lookup table; [LaTeX](tables/figure1B_table.tex) |
| Figure 1 B, optional prose | [PDF](pdf/figure1B_prose.pdf) | [SVG](svg/figure1B_prose.svg) | Remove overview float; reuse existing introduction or replace its summary, do not add redundant prose |
| M4 forest plot | [PDF](pdf/m4.pdf) | [SVG](svg/m4.svg) | RESTYLE |
| Verification | [PDF](pdf/verification.pdf) | [SVG](svg/verification.svg) | RESTYLE |
| 358H | [PDF](pdf/state.pdf) | [SVG](svg/state.svg) | RESTYLE |
| Appendix inventory | [PDF](pdf/appendix_table.pdf) | [SVG](svg/appendix_table.svg) | REPLACE WITH TABLE, appendix-only; [LaTeX](tables/appendix_table.tex) |

The final recommendation is **REMOVE FROM MAIN** for Figure 1. The reasoning, measured page cost and per-figure decisions are in [FIGURE_STYLE_REVIEW_V04.md](../FIGURE_STYLE_REVIEW_V04.md). Nothing is removed from the manuscript by this branch.

Inspect [STYLE_PROOF.pdf](qa/STYLE_PROOF.pdf) for all seven candidates at native width with their preserved caption context and [STYLE_COMPARISON.pdf](qa/STYLE_COMPARISON.pdf) for same-width current/style pairs. PNGs are previews only. Print PDFs at 100%, without fit-to-page scaling. Sources and methods remain those of the [unchanged original manifest](../data/figure_manifest.json) and [source lock](../data/source_lock.json).

## Reproduce

From a full repository checkout, using Python with matplotlib, pandas, numpy, PyMuPDF and Pillow; `pdflatex` with standalone/mathptmx/booktabs/tabularx/caption, and Poppler `pdftocairo`/`pdffonts`:

```bash
python paper/mlsys2027/figures/style_v04/scripts/plot.py
python paper/mlsys2027/figures/style_v04/scripts/tables.py
python paper/mlsys2027/figures/style_v04/scripts/proof.py
python paper/mlsys2027/figures/style_v04/scripts/validate.py
python paper/mlsys2027/figures/style_v04/scripts/manifest.py
python paper/mlsys2027/figures/style_v04/scripts/notebook.py
```

No call to the old extractor or experiment scripts is needed. `validate.py` imports no plot helper: it verifies unchanged input hashes and actual plotted artist coordinates/CI segments/bar widths, compiled table content, vector exports, embedded fonts and bounds. `STYLE_MANIFEST.json` and `SHA256SUMS` identify the final PDF/SVGs. `frozen_inputs.json` locks scientific data, provenance and current manuscript files to the exact requested base. `qa/validation.json` is a style-invariance pass, not a new statistical analysis.

`style_audit.ipynb` is a small executed audit companion that invokes the invariant checks and prints their scope and results; it does not re-estimate science or produce publication figures. Its plain Python cells execute top-to-bottom; no Jupyter kernel or notebook-viewer inspection is claimed. The publication PDF/color/grayscale views were inspected separately. Notebook regeneration additionally needs `nbformat`.

Keep the [caption handoff](CAPTION_HANDOFF.md) with the candidate figures: exactness counts, context sets, detailed percentages, residuals, speedup intervals and boundary caveats moved out of the artwork remain there. Figure labels and includes must be integrated separately; this task intentionally edits no manuscript wrapper.
