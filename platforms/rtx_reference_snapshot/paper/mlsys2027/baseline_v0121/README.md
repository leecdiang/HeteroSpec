# Evidence-frozen editorial revision v0.12.1

Title: **State and Cost Limits of Reference-Preserving Speculative Decoding**.

This revision refines the v0.12.0 scientific baseline merged in PR #67 at main `c38ae79dedf8b5016bc7db8ece315cbd25b82812`. It preserves all 26 inherited evidence files byte-for-byte. The original `baseline_v012/` remains unchanged.

- Main: `output/manuscript-v0.12.1.pdf` (6 body pages + 1 references page).
- Supplement: `output/appendix-v0.12.1.pdf` (3 pages).
- Portable author source: `output/portable-source-v0.12.1.zip`.
- Revision explanation: `EDITORIAL_CHANGES.md`.
- Full author self-review: `../reviews/editorial_v0121/EDITORIAL_REVIEW.zh-CN.md`.
- Current venue fit: `../reviews/editorial_v0121/VENUE_FIT.zh-CN.md`.
- Fresh finite-window phrase check: `../reviews/editorial_v0121/TEXT_OVERLAP_CHECK.json`.

Run `python build.py` in this directory. Dependencies are Python 3, NumPy, Matplotlib, latexmk with pdflatex/BibTeX, and Poppler. The script verifies inherited source hashes, RTX public qualification joins, median-before-ratio arithmetic, 12 comparisons and task-bootstrap intervals. It generates three source-checked figures, compiles both PDFs, checks overflow/undefined references and Type 3 fonts, and packages source files. No model execution or GPU access occurs.

The mainline is natural numerical state × current execution path, finite target-path constraints, and independent output/amortization gates. RTX generation speed is **1.17012×** versus paid ordinary decoding and **1.16924×** versus matched draft-free execution. Resident-request speed is **1.74157×** versus ordinary and **1.03507×** versus matched; the matched path already gives **1.68256×** without speculation. These are one 24-task, four-repeat campaign's aggregates under its original timers. Seven matched-request task medians regress, and the second matched-request repetition has aggregate speed below one.

B570 endpoint repair loses to ordinary and matched decoding. Wider RTX drafting at fixed UB4 qualifies but becomes slower. Four platforms are not four equivalent causal-mechanism replications; late repair evidence predominantly uses Qwen3.

The inherited `evidence/SOURCE_BINDINGS.json` and `evidence/TEXT_OVERLAP_CHECK.json` remain explicitly v0.12.0 provenance. The latter does not check v0.12.1 prose. The fresh check is in the review directory and is not Turnitin/iThenticate or a whole-literature audit. Current public-table checking inherits original-host private-archive verification.

References list all authors. arXiv references print their complete identifiers rather than duplicate long URLs; `REFERENCE_URLS.json` retains primary locators. The PDFs use anonymous authors. The portable source contains provenance identities and is an author package, not an anonymous submission artifact. Weights, native runtimes and private raw archives are not embedded.

The official MLSys 2027 call checked on 2026-10-08 retains the 2025 style, a 10-page body limit and separately uploaded appendix. This revision uses that review format. It has not been submitted to any venue. The review still regards MLSys research acceptance as uncertain and leans Weak Reject; journal-fit recommendations are conditional on author goals and budget.
