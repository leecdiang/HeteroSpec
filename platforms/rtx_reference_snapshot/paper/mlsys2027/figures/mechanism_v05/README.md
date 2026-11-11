# Translation mechanism schematic v0.5

**Selected: Candidate B, PUBLICATION-CANDIDATE.** Exactly two layouts of one conceptual mechanism figure. Both preserve the four-stage logic and bounded scientific claims. Based exactly on `974e84540b5193b416e20920629260ff320f759d` (`paper/mlsys2027-figure-style-v0.4`).

| Asset | PDF | SVG | Editable TikZ source | Physical size |
|---|---|---|---|---|
| A: empirical anchors | [PDF](candidate_a/mechanism.pdf) | [SVG](candidate_a/mechanism.svg) | [TeX](candidate_a/mechanism.tex) | 6.75 × 2.40 in |
| B: minimal alternative, selected | [PDF](candidate_b/mechanism.pdf) | [SVG](candidate_b/mechanism.svg) | [TeX](candidate_b/mechanism.tex) | 6.75 × 2.10 in |
| Selected publication asset (identical to B) | [mechanism.pdf](mechanism.pdf) | [mechanism.svg](mechanism.svg) | [mechanism.tex](mechanism.tex) | 6.75 × 2.10 in |

- [A/B design decision and page cost](../MECHANISM_FIGURE_REVIEW.md)
- [Independent scientific validation](../MECHANISM_FIGURE_VALIDATION.md)
- [Proposed captions](CAPTION_SUGGESTIONS.md); selected [caption.tex](caption.tex)
- [A native-width caption proof](qa/proof_a.pdf), [B native-width caption proof](qa/proof_b.pdf)
- [Full-precision evidence](data/evidence.json), [source hashes](data/source_lock.json), [quality checks](data/quality.json)
- [Manifest](MECHANISM_MANIFEST.json), [numerical/vector QA](qa/validation.json), [final SHA256](SHA256SUMS)

The figure separates local indicators, correctness qualification, realized stateful accounting, and observed qualified outcomes. RTX/B570 anchor the qualification diagnosis; 358H NPU anchors the state-interface diagnosis; M4's opposite exact outcomes are not assigned to either mechanism. Arrows denote evaluation boundaries, not a guarantee of speedup. These are configuration-scoped, non-exhaustive diagnoses. There is no common quantitative axis or hardware ranking.

Proposed later placement: Section 5 after its opening paragraph and before the correctness diagnosis, semantic label `fig:translation`. Manuscript prose, wrappers, existing assets, source data and original provenance are unchanged. No numbering is chosen and no integration patch is applied.

## Reproduction

From a repository checkout with Python, NumPy, PyMuPDF, `pdflatex` (standalone, T1 fonts, mathptmx, TikZ/arrows.meta, graphicx, caption), and Poppler `pdftocairo`/`pdffonts`:

```bash
python paper/mlsys2027/figures/mechanism_v05/scripts/extract.py
python paper/mlsys2027/figures/mechanism_v05/scripts/render.py
python paper/mlsys2027/figures/mechanism_v05/scripts/validate.py
python paper/mlsys2027/figures/mechanism_v05/scripts/finalize.py
```

Extraction reads only closed repository sources, performs scoped data-quality checks and corroborates existing estimates. Validation uses independent calculations and original inputs, without importing extraction or drawing helpers. No experiment or bootstrap estimate is rerun. `render.py` is the layout authority; the emitted standalone `.tex` files are editable and directly compilable, but change the generator for reproducible revisions. Selected files are byte-identical aliases of B, not a third layout. Intermediate TeX build files in `qa/build/` are untracked.

Both native PDF and SVG outputs are vector. PDFs embed Times-compatible fonts; SVGs use glyph outlines. PNGs in `qa/` are previews only: both candidates at 96/180 dpi in color/grayscale, independent SVG renders at 96 dpi, and grayscale caption proofs. Native width is 648 px at 96 dpi and 1215 px at 180 dpi. Print the PDFs at 100%, without fit-to-page scaling. Captioned proofs measure blocks, not final manuscript pagination.
