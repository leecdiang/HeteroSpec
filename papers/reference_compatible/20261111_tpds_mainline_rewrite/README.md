# Reference-Compatible Parallel Execution for Quantized LLM Inference

TPDS author-review rewrite, 11 November 2026. The paper asks how a quantized
runtime can parallelize known queries while preserving an established numerical
reference. It proceeds from native interventions to an execution construction,
then to numerical qualification, component attribution and complete-request cost.

## Read and build

- `main.pdf`: the TPDS manuscript.
- `supplement.pdf`: separate supplementary material.
- `main.tex` and `supplement.tex`: the two document roots.
- `sections/` and `abstract.tex`: editable manuscript text.
- `figures/`: vector PDF and SVG figures, with 300 dpi PNG previews.
- `scripts/`: arithmetic reconstruction, tables, figures and evidence checks.
- `data/`: original PR220 numeric inputs, preserved byte for byte.
- `data_added/`: inherited published projections plus the newly incorporated B2
  matched-history operation records.

The document uses the official Computer Society mode of IEEEtran 1.8b:
`\documentclass[10pt,journal,compsoc]{IEEEtran}`. The class sets its body type,
leading, column widths and margins. No manual page compression is applied.
The official template source and format verification are recorded with the
review materials. Main text and supplementary material are separate PDFs.

For a complete offline rebuild, install Python with NumPy and Matplotlib,
TeX Live with pdfLaTeX, BibTeX and the packages named in `preamble.tex`, the current `xr` package used by `supplement.tex` (including its `nocite` external-reference option), Inkscape, PyMuPDF and Poppler tools (`pdffonts`). URW Base35 supplies the P052 plot font. The plot script can fall back
to Matplotlib's PGF backend with pdfLaTeX and mathpazo when Inkscape is absent.

```sh
bash build.sh
```

To compile the manuscript using the included figure and table assets:

```sh
bash build.sh --tex-only
```

Run the main document before the supplement: the supplement imports the main
paper's labels while maintaining its own bibliography. `PYTHON`, `PDFLATEX` and
`BIBTEX` can select installed executables. Numerical reconstruction and figure
generation require no model weights, network request or GPU execution.

## Evidence and interpretation

This rewrite starts from PR220, commit
`8aea751bde42cd69bf923ed4524972f9af98d694`, and incorporates the completed
matched-history A5000 width panel at PR218 commit
`4fe337a8ff349d547023f9dd60b8e114e5323207`. The original data identities remain
in the inherited historical `SOURCE_MANIFEST.json`; its older status notes describe that original snapshot. Current evidence and completion status are in `REWRITE_EVIDENCE.json`. `provenance/pr220_baseline_identity.json` records the
inherited source ancestry. `REWRITE_EVIDENCE.json` binds the new manuscript,
newly added data and figure-to-evidence mapping.

Application-level speculative gains are reported separately from the smaller
packing and cut-placement effects. Equal-work q8 comparisons are separate from
live k7/k3 generation. The 32B service comparison retains its graph-level loop
baseline; the completed stronger-loop comparison supplies operator results.
At the recorded cutoff, its full-model S3 stage remains in progress.

The package checks 15 application ratios, 96 mixed-Q4 measurements, 16 q8
interval endpoints, 108 Vulkan timings, 12 factorial interval endpoints at the
available reconstruction levels, the strong-loop published ratios, and all
128 added B2 operations. Application intervals and 14B direct-factor intervals
are inherited from their original analyses. `generated/` preserves that
provenance in the individual check reports. Licensed weights and large raw
numerical captures are retained separately in the experiment records.

## Editing and visual language

The six main figures follow the argument: physical-range intervention;
execution construction; component effects; boundary opportunity; application
service; and equal-work efficiency versus live work. Three supplementary
figures retain mixed-Q4 alternatives, the complete width-cost account and the
historical geometry cells. Blue, ochre and green retain the earlier manuscript's
visual language. Labels, marker shapes, fill and hatching carry the same
information in grayscale and for readers with color-vision differences.

The rewrite applies eight scientific research/writing skills, a concise-writing
skill and Humanizer 4.0.0. The review packet records their exact sources, actual
prose changes, arithmetic checks, bibliography verification and page inspection.
The historical tests that locked exact old sentences, equations or figure counts
were replaced by data-level checks applicable to this approved reconstruction.
All original data and adverse observations remain represented.

## Review packet

`REVIEW_GUIDE_ZH.md` explains the reconstruction and figure sequence in Chinese.
`review/FINAL_VALIDATION.md` records the final compilation, numerical checks,
page inspection and clean-extraction build. `review/SKILLS_APPLIED.md` links the
ten writing/research skills and records the decisions they informed.
