# Phase-Scoped Query Layouts for Reference-Preserving Speculative Decoding

**Version 0.15.1, author-review final revision, 13 October 2026.** The title and central method are unchanged. This revision updates the v0.15.0 paper in PR102, pinned at `b9e23fd8a5309151dc3e71cb2b79311589bcdbe3`. The directory name remains stable for existing links. It is not a journal submission or an approval of the pending author declarations.

## Reading and delivery

- `output/main.pdf`: revised article, 11 pages.
- `output/supplement.pdf`: supplementary material, 9 pages, including the new session-ratio table.
- `output/figures/`: five separate vector PDFs; editable TikZ/PGFPlots sources are in `figures/`.
- `output/JSA_v0151_author_package.zip`: complete review package, including sources, figures, data, checks, PDFs and author worksheets.
- `output/JSA_v0151_flat_sources.zip`: source files with no subdirectories, independently compiled for Elsevier Editorial Manager preparation.
- `Highlights.txt`, `Figure_captions.tex`, `Title_page.txt`: editable submission support files.
- `JSA_REQUIREMENTS_20261013.md` and `AUTHOR_CHECKLIST.md`: verified publisher guidance, current JSA guide access limitation, and remaining author decisions.

Build outputs and ZIPs are generated locally, not committed. The final package's exact file hashes are in `output/FINAL_MANIFEST.json`.

## Changes and verification

The B570 full-output pairing now cites PR93 directly; its 563 physical verification cycles cite PR97. Target-only Qwen3 and Llama PQ/QB session reversals are disclosed separately from the consistently directed speculative session aggregates. The introduction and discussion connect graph layout, actual execution partitions and retained-state formation. Stage-Replay is credited for cache transplantation, common suffix controls and the same-initial-token boundary.

All five figures retain the existing restrained palette, with larger labels, explicit ratio directions and redundant line/shape cues. Tables use clearer comparison groups and prose alignment. The incorrect S7 pointer now targets the historical endpoint discussion in S6. The final prose pass uses the humanizer skill while preserving claims and limitations.

The local checker passes 186 reported-value and manuscript checks. An independent author-side cross-review re-fetched the pinned reports and matched all 21 aggregate ratios, 42 session ratios, 252 task ratios and 21 regression lists. It found no scientific blocker; two wording ambiguities were corrected. This is AI-assisted author-side scrutiny, not journal peer review. See `provenance/FINAL_REVIEW_V0151.json` for scope and `provenance/FINAL_QA_V0151.json` for automated PDF/transcription checks.

No GPU experiment, full native timing-record audit or 675 MB raw-archive reconstruction was performed. The current package contains reported task/session medians and their provenance; these are not individual native timing records. Failed stock qualification, eight rejected scale/MUL shams, the driver-freeze gap, task regressions and limits on portability remain explicit.

## Build and package

Use Python 3.10+ and a TeX distribution with pdfLaTeX, BibTeX, `elsarticle`, TikZ/PGFPlots, `microtype`, `booktabs`, `tabularx`, `longtable`, `enumitem`, `xurl`, `flushend`, `preview` and standard Times-compatible fonts. PDF QA also needs `pdfplumber` and Poppler (`pdffonts`).

```sh
python3 scripts/check_reported_data.py
python3 scripts/build.py
python3 scripts/export_figures.py
python3 scripts/qa_final.py
python3 scripts/package_submission.py
```

The package helper rebuilds both flat manuscripts in a clean temporary directory before creating the archives. No GPU, network or shell escape is required. On Overleaf, choose `main.tex` or `supplement.tex` with pdfLaTeX. The bibliography uses the existing renamed `psql-num.bst` derivative; current JSA reference-style acceptance still needs confirmation.

## Submission status and provenance

Chengzhan Li remains the sole and corresponding author, with the confirmed UESTC full name and Qingshuihe campus. Funding, competing interests, CRediT roles, historical AI-tool details, final human review and public evidence access require author confirmation. `Author_declarations_pending.txt` is a worksheet, not a completed journal declaration. No other author is added based on a possible future conversation.

Official Elsevier policies were checked on 13 October 2026. The JSA-specific Guide for Authors returned access errors/human verification, so anonymity, numerical length limits and journal-specific upload rules remain unverified. The present package must not be described as fully JSA-compliant until those checks and author declarations are complete.

The original `GITHUB_IMPORT.json`, `PACKAGE_MANIFEST.json`, `RECONSTRUCTION_REVIEW_ZH.md`, `provenance/RECONSTRUCTION_QA.json`, `provenance/PDF_CHECKS.json` and original font reports describe the **historical v0.15.0 import/build only**. They are retained as provenance, not current-file integrity certificates. Use the v0.15.1 checks and final manifest for this revision. Experiment records and earlier paper directories are unchanged.
