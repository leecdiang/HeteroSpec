# Scientific baseline v0.12.0

Title: **State and Cost Limits of Reference-Preserving Speculative Decoding**.

This is the reconstructed scientific baseline after merging research PRs #57–66. It supersedes v0.11 for current scientific conclusions; versioned earlier PDFs and studies remain historical records. It is an author-reviewed research draft, not a submitted paper or an external peer-review decision.

- Main: `output/manuscript-v0.12.0.pdf` (6 body pages + 1 references page).
- Supplement: `output/appendix-v0.12.0.pdf` (3 pages).
- Portable source: `output/portable-source-v0.12.0.zip`.
- Evidence and source identities: `evidence/`.
- Whole-baseline review: `../reviews/baseline_v012/BASELINE_REVIEW.zh-CN.md`.

From this directory, run `python build.py`. Dependencies: Python 3, NumPy, Matplotlib, latexmk with pdflatex/BibTeX, and Poppler. The script recomputes public RTX arithmetic and qualification-hash joins, generates the cost figure, compiles both PDFs, checks LaTeX overflow and references, and packages sources. No model execution or GPU access occurs.

The main result is a bounded reference-preserving RTX instance, accompanied by natural state/current-path evidence and cost boundaries. Ordinary-reference request speed is **1.74157×**, while matched draft-free execution already gives **1.68256×**; the incremental speculation speed on the matched path is **1.03507×**. Generation speed is **1.17012×** versus ordinary and **1.16924×** versus matched. All refer to the same 24-task, four-repeat campaign and its original timer boundaries, not globally best ordinary decoding.

B570 endpoint repair is real on its finite panels but has no ordinary-reference cost gain. Wider RTX drafting at fixed UB4 is qualified but slower. Four platforms do not establish four equivalent mechanism replications; late repair evidence predominantly uses Qwen3.

The portable source is an author provenance package: evidence JSON/CSV contains project/source identities and is **not an anonymous submission artifact**. The PDFs have anonymous authors and no account or repository identifiers in extracted text. An anonymous evidence package and final author verification would be separate submission preparation. Private raw archives, weights and frozen native runtimes are not embedded; public-table validation does not independently certify their contents.

The official MLSys 2027 call checked on 2026-10-08 explicitly retains the 2025 style and a 10-page body limit, with a separately uploaded appendix. This baseline uses that retained style, but no venue submission has been made. Formal licensed-corpus plagiarism checking has not been performed.
