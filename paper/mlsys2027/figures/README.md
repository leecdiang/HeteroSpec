# Independent MLSys 2027 figure candidates

These five candidates were constructed from repository evidence at
`62d1c134b096882c37ce58c1d0ac140236acd9c3`. The paused manuscript and its Figure 1–5 assets were unavailable. No manuscript prose was accessed or changed.

**Status: PUBLICATION-CANDIDATE at the tested native insertion widths.** This is not a claim of final manuscript integration or author approval.

The user-requested numbering takes precedence over the older outline: Figure 2 is verification-path admissibility; Figure 3 is the M4 workload contrast.

| Figure | Vector PDF | Vector SVG | Native width |
|---|---|---|---|
| 1 · correctness and realized accounting | [PDF](pdf/figure1.pdf) | [SVG](svg/figure1.svg) | 3.25 in |
| 2 · verification-path admissibility | [PDF](pdf/figure2.pdf) | [SVG](svg/figure2.svg) | 6.75 in |
| 3 · M4 workload contrast | [PDF](pdf/figure3.pdf) | [SVG](svg/figure3.svg) | 3.25 in |
| 4 · 358H isolated vs realized | [PDF](pdf/figure4.pdf) | [SVG](svg/figure4.svg) | 6.75 in |
| 5 · categorical regime map | [PDF](pdf/figure5.pdf) | [SVG](svg/figure5.svg) | 6.75 in |

## Reproduce from a repository checkout

Python 3.12 with matplotlib 3.10.8, numpy 2.3.5, pandas 2.2.3, Pillow,
pypdf and PyMuPDF was used. Notebook generation additionally uses nbformat and IPython.
Poppler `pdftoppm` renders the final PDFs. STIXGeneral/STIX fonts ship with Matplotlib.

```bash
python paper/mlsys2027/figures/scripts/extract.py
python paper/mlsys2027/figures/scripts/validate.py
python paper/mlsys2027/figures/scripts/plot.py
python paper/mlsys2027/figures/scripts/render_qa.py
python paper/mlsys2027/figures/scripts/build_notebook.py
python paper/mlsys2027/figures/scripts/build_manifest.py
```

`plot.py` invokes the independent numerical validator after **each** figure.
It checks input hashes, output size, vector-only marks and text bounds. Final visual review remains required after any changes.

`figure_audit.ipynb` is a reproducible audit companion, with executed cells and saved outputs. In this authoring environment, both Jupyter TCP and IPC sockets were unavailable; `build_notebook.py` executes its plain Python cells sequentially in a fresh namespace and captures displays. The notebook remains standard nbformat and can be run in Jupyter. A Jupyter-kernel execution is not claimed for this environment. The generated HTML notebook preview was not browser-inspected because a browser binary was unavailable; its embedded figure images were separately inspected. This does not affect the numerical or final-figure visual passes.

PDF/SVG files are authoritative. `qa/*png` are previews only. The proof PDF preserves the actual paper insertion sizes; print at 100%, not fit-to-page.

## Evidence and review

- [Figure manifest](FIGURE_MANIFEST.md): per-figure claim, sources, exact values, estimators, evidence status, caveats and final SHA256.
- [Source lock](data/source_lock.json): exact source commit, SHA256, Git blob SHA1 and bytes for all consumed inputs.
- [Caption suggestions](FIGURE_CAPTION_SUGGESTIONS.md): proposed captions only; no manuscript edits.
- [Figure review](FIGURE_REVIEW.md): provisional design decisions, missing old assets and required integration procedure.
- [Visual QA](qa/VISUAL_QA.md): actual-size/grayscale checks and fixes.
- [Insertion proof](qa/insertion_proof.pdf): two native-width proof sheets, not a mock manuscript.

The official [MLSys 2027 CFP](https://mlsys.org/Conferences/2027/CallForResearchPapers) points to the [2025 style package](https://media.mlsys.org/Conferences/MLSYS2025/mlsys2025style.zip). Its `mlsys2025.sty` sets `textwidth=6.75in` and `columnsep=0.25in`, giving a 3.25-in single column. The Times-based style motivates the compatible STIX typography; no manuscript layout is inferred.

Integration stays on a dedicated branch. If the manuscript checkpoint appears, rebase onto its exact checkpoint SHA, preserve that workspace's prose, and compare actual OLD/NEW assets before selecting replacements. Do not merge automatically.
