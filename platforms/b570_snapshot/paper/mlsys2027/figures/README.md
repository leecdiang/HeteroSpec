# MLSys 2027 figure narrative refactor — v0.3

**PUBLICATION-CANDIDATE:** four main figures and one appendix inventory, based on current main `1a11361f8526ec361e20dd6878d6e67352fb7bbd`. The manuscript checkpoint and previous candidates are now available and were directly compared. Scientific inputs are closed and unchanged; no experiments or manuscript prose were modified.

The figure story is: favorable local measurements do not translate robustly into realized gain in the tested cases; correctness filtering and stateful runtime costs diagnose two observed failures. M4's opposite workload-study regimes are a first-class observation, without workload-only causal attribution.

| Role | Decision | Vector PDF | Vector SVG | Width |
|---|---|---|---|---|
| 1 · empirical puzzle | REDESIGN BOTH | [PDF](pdf/figure1.pdf) | [SVG](svg/figure1.svg) | 6.75 in |
| 2 · correctness diagnosis | TAKE NEW | [PDF](pdf/figure2.pdf) | [SVG](svg/figure2.svg) | 6.75 in |
| 3 · M4 contrast | HYBRID | [PDF](pdf/figure3.pdf) | [SVG](svg/figure3.svg) | 3.25 in |
| 4 · stateful integration | TAKE NEW | [PDF](pdf/figure4.pdf) | [SVG](svg/figure4.svg) | 6.75 in |
| A1 · regime inventory (legacy asset 5) | TAKE NEW, appendix only | [PDF](pdf/figure5.pdf) | [SVG](svg/figure5.svg) | 6.75 in |

## Review first

- [Captioned figure-story proof](qa/figure_story_proof.pdf): read the selected sequence without manuscript prose; final physical widths.
- [Actual OLD/NEW comparisons](comparison/OLD_NEW_COMPARISON.pdf): OLD against both prior v0.2 and selected v0.3; ten equal-width pages.
- [OLD native-width proof](comparison/OLD_NATIVE_WIDTH.pdf): retains original single/double-column sizes. OLD Figures 1/5 are explicitly enlarged only in equal-width comparisons.
- [Actual decisions and tradeoffs](FIGURE_REVIEW.md), [manifest and hashes](FIGURE_MANIFEST.md), [caption suggestions](FIGURE_CAPTION_SUGGESTIONS.md), [integration kit](integration/FIGURE_INTEGRATION.md).

## Reproduce from a repository checkout

Python 3.12; matplotlib 3.10.8, numpy 2.3.5, pandas 2.2.3, Pillow, pypdf and PyMuPDF. Notebook generation additionally uses nbformat and IPython. Poppler renders previews; `pdflatex` with geometry/times/graphicx/amsmath/amssymb/caption builds the optional captioned story proof. STIX fonts ship with Matplotlib.

```bash
python paper/mlsys2027/figures/scripts/extract.py
python paper/mlsys2027/figures/scripts/plot.py
python paper/mlsys2027/figures/scripts/render_qa.py
python paper/mlsys2027/figures/scripts/compare.py
python paper/mlsys2027/figures/scripts/validate_comparison.py
python paper/mlsys2027/figures/scripts/build_story_proof.py
python paper/mlsys2027/figures/scripts/build_notebook.py
python paper/mlsys2027/figures/scripts/build_manifest.py
```

`plot.py` independently validates each figure immediately after rendering. Its validator imports no extraction or plotting helpers, and replays frozen timing medians, bootstrap protocols and paired decompositions. `validate_comparison.py` reconciles original TeX plotting values and checks actual placed PDF widths. Extraction retains original units, grains and evidence classes; header-only historical scaffolds and contaminated B570 diagnostics remain excluded.

`figure_audit.ipynb` remains an executed audit companion, not a source of publication screenshots. Its plain Python cells run top-to-bottom in a fresh namespace with display capture; no Jupyter-kernel execution is claimed. PDF/SVG are authoritative, PNGs preview-only. Generated comparison PNGs and intermediate vector crops can be reproduced from `compare.py` and need not be committed.

Source commit, SHA256 and Git blob IDs are retained for all 40 consumed sources in `data/source_lock.json`. The new overview is extracted to `data/figure1_overview.csv`; all other plotting tables preserve the closed values. Comparison source/crop provenance and prior candidate hashes are in `comparison/comparison_lock.json`; prior v0.2 PDFs are retained under `comparison/prior_v02/`.

The actual manuscript style sets text width 6.75 in and column gap 0.25 in. [Visual QA](qa/VISUAL_QA.md) documents native-size color/grayscale inspection. Print proofs at 100%. The old title, prose and float layout remain untouched; [integration notes](integration/FIGURE_INTEGRATION.md) identify references that the narrative owner must reconcile. No automatic merge.
