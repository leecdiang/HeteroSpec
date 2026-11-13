# Final pre-submission manuscript — 2026-11-11

This edition starts from **HeteroSpec_PreSubmission_Author_Reconstructed_20261111.zip**, SHA256 `fb99d81f679e742fc85b8dbf84a82b0213c28adc5653be5ec458e82c71567905`. It is a revision of the recovery package, not the older Refined manuscript and not a byte-identical retrieval of missing files.

`main.tex` builds the reading version plus supplement; `journal.tex` retains IEEEtran's Computer Society class style and builds the main paper only. The final standalone supplement is extracted from the combined PDF, preserving its printed cross-references/page numbers. Experimental data under `data/` and the six display equations are unchanged. `SOURCE_MANIFEST.json` retains the historical ancestry of those data; `revision/BASELINE_IDENTITY.json` identifies this edition's actual recovery input. Published field projections added during this revision live only in `data_added/`.

## Evidence cutoff

The new strong-loop operator results are pinned to **PR218 `f419a89d54f4ec93b4c9c328b4ea9f416ae3c989`**. At this cutoff the PR is open/Draft/unmerged; S1 qualification and S2 operator measurements are complete. The full-model S3 comparison and matched-history B2 stage have no performance results at that commit. The old32B service improvement retains its graph-level loop baseline. Newer source commits are not silently incorporated.

The package recomputes15 application ratios, all96 mixed-Q4 request timings,16 registered q=8 interval endpoints from128 arm/root aggregates, and12 factor endpoints at their documented reconstruction levels. The newS2 file contains36 published paired ratios, not every raw elapsed-time receipt;12 cell and3 equal-cell geometric summaries can be rechecked. Application CIs and14B direct-factor CIs remain inherited source intervals. No new model execution is performed.

## Build the complete editable project

Use Python with NumPy and Matplotlib, and a TeX installation with pdfLaTeX, BibTeX, IEEEtran, mathpazo, TikZ, algorithms and the packages in `preamble.tex`. Observed versions: Python3.13.5, NumPy2.3.5, Matplotlib3.10.8, pdfTeX1.40.26 / TeXLive2025-dev, BibTeX0.99d. No proprietary font file is supplied. Licensed fonts installed in the build environment are embedded in the PDFs.

```sh
bash build.sh
```

The script regenerates statistics/tables/figures, runs normal and optimized tests, and builds both entries using BibTeX and repeated LaTeX passes. It performs no network request or GPU work. If the host has no `pdflatex.fmt`, generate it with the TeX distribution's approved format tool (the authoring environment used `fmtutil-user --byfmt pdflatex`); do not count a missing-format failure as a successful final build. The authoring environment had a broken BibTeX wrapper and used an installed `bibtex.original` through a private local symlink. Neither workaround changes the scientific source or system installation.

A minimal arXiv ZIP is also supplied. Its sole document root is `main.tex` (the wrapper and manuscript are combined); figures and `main.bbl` are prebuilt. It compiles with pdfLaTeX without Python, internet or shell escape. The author package contains the editable plotting and data code.

## Review and verification

See `revision/CROSS_REVIEW.md`, `revision/SKILLS_USED.json`, the author-level claim register, one-page changes and the final validation records. The comments are structured passes by one assistant, not external referee votes. Source/aggregate rechecks do not independently reproduce private GPU captures. Weights, raw numerical inputs and some large captures are separately required for a fresh native run.

Main figures retain all fixed controls, root-level points and declared intervals/ranges. Historical Fig.S2 is full width (smallest embedded plot text about7.82pt). The complete RTX geometry table has all48 original displayed means. Statistical axes stay single-axis assets; the two width assets form Fig.7 without conflating their experiments. No test was weakened to hide an overlap or omit an adverse cell.

No experiment was launched, no existing PR merged, and no arXiv/journal submission made. This session exposed GitHub read actions only; publication materials do not claim an already-created remote PR.
