# HeteroSpec final recovery-based author package

Start with `CHANGES_CN.md`, `CLAIMS_EVIDENCE.md` and `FINAL_SOURCE_MANIFEST.json`.
`paper/main.pdf` is the14-page reading version (10main+4supplement); `paper/journal.pdf` is the10-page IEEEtran Computer Society class-style main paper.
Rebuild offline with `cd paper && bash build.sh`. Minimal arXiv source is a separate ZIP with a single main.tex root; it needs neither Python nor network to compile.

Original experimental data and definitions are retained. New PR218 operator evidence is fixed at f419a89d; full-model strong-baseline speed is not established at that cutoff. The package's checks do not launch a model or independently reproduce private GPU captures.

The `validation` directory records executed tests and clean builds. `visual_review` contains the rendered contact sheets and grayscale/color-vision screening. No font files are distributed.

The optional publication package is separate. This session did not create a remote PR or submit the manuscript.
