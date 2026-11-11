# JSA author manuscript v0.14.1

**Reference-Preserving Speculative Decoding on Consumer Systems: Diagnosis, Repair Scope, and Paid Cost**

Inherits open Draft PR #71 at `c1f11267cdb4016c9b8ecf2514b0cec3ad7809dd` and the scientific plan in #70. All historical manuscripts/evidence remain preserved. No model experiment, merge, submission or public data release.

| Delivery | Entry |
|---|---|
| Main: **12 pages**, normal Elsevier 5p double column | [PDF](output/jsa-manuscript-v0.14.1.pdf), [main.tex](main.tex) |
| Independent supplement: **27 pages**, normal 12pt single column | [PDF](output/jsa-supplement-v0.14.1.pdf), [supplement.tex](supplement.tex) |
| Full author sources, CPU code, plots and bound exports | [Overleaf ZIP](output/overleaf-author-source-v0.14.1.zip) |
| Separately rebuilt flat submission sources | [Main ZIP](output/editorial-manager-main-flat-source-v0.14.1.zip), [supplement ZIP](output/editorial-manager-supplement-flat-source-v0.14.1.zip) |
| Revision, validation and figure choices | [Chinese record](RECONSTRUCTION_ZH.md), [validation](VALIDATION_LOG.md), [figure layout](FIGURE_LAYOUT.md) |
| Evidence and pending facts | [claims](CLAIM_EVIDENCE.md), [all experiments](EXPERIMENT_DESTINATIONS.md), [AUTHOR_TODO](AUTHOR_TODO.md) |

The author's 12–15-page target is not a JSA page rule. Measured sequence: **30 single-column → 14 content-unchanged double-column → 12 final pages**. The unchanged official class uses `final,5p,times,twocolumn`, an author layout rather than exact final JSA typesetting. No normal font/leading/margin reduction or negative spacing is used. Body prose in Sections 1–8 is 6,394 → 5,908 words by TeXcount 3.1.1; frontmatter/declarations, headers and captions are separately recorded.

## CPU-only rebuilding

Use Python 3 with NumPy/Matplotlib, TeX Live with pdfLaTeX/BibTeX/latexmk and Poppler (`pdfinfo`, `pdftotext`, `pdffonts`, `pdftoppm`) on PATH. Pillow is used for contact sheets. From this directory:

```bash
python3 build.py
python3 scripts/check_package.py
python3 scripts/flat_sources.py
python3 scripts/render_qa.py
```

`build.py` authenticates included source copies, verifies frozen exports, regenerates five PDF/SVG figures and editable tables, runs the additional standard-library scientific audit, compiles both documents and packages author sources. `--no-package` avoids a nested ZIP; `--skip-assets` compiles supplied assets after editorial checks. Archived historical/runtime scripts are never invoked. In Overleaf upload the structured ZIP, select `main.tex` or `supplement.tex`, and use pdfLaTeX; supplied assets make Python unnecessary for ordinary compilation. No live Overleaf account was tested. Exact toolchain versions are in [TOOLCHAIN_QA.json](output/TOOLCHAIN_QA.json).

The final Overleaf ZIP was extracted and fully rebuilt; both PDF byte/text hashes, all generated assets and numerical QA agree in the recorded environment. Two flat ZIPs each contain one document entry, with all TeX/bibliography/class/artwork at one level. Their extraction/builds pass. Flat supplement PDF bytes agree; flat main differs only in five embedded `PTEX.FileName` strings after figure-path rewriting. All other logical objects, decoded streams, text and all twelve rendered RGB pages agree. This verified provenance-metadata difference is documented, not assumed to be a timestamp difference. Local compilation does not establish Editorial Manager acceptance; no login/upload/submission occurred.

## Fresh receipts and access boundary

- [Content-unchanged layout](output/BASELINE_LAYOUT_QA.json), [compatibility patch](validation/CONTENT_UNCHANGED_LAYOUT.patch), [word-count scope](output/WORD_COUNT_QA.json).
- [Numeric reconstruction](output/NUMERICAL_QA.json), [independent arithmetic](output/SCIENTIFIC_QA.json), [source-text review](output/SCIENTIFIC_TEXT_REVIEW_QA.json), [scientific scope](SCIENTIFIC_AUDIT.md).
- [Clean build](output/FINAL_CLEAN_BUILD_QA.json), [structured-package rebuild](output/SOURCE_PACKAGE_REBUILD_QA.json), [flat rebuild](output/FLAT_SOURCE_REBUILD_QA.json), [verified PDF difference](output/FLAT_MAIN_PDF_DIFFERENCE_QA.json).
- [Main visual review](output/MAIN_VISUAL_QA.json), [supplement visual review](output/SUPPLEMENT_VISUAL_QA.json): all **39** final pages freshly rendered/viewed. PNGs are reproducible scratch files.
- [Baseline preservation](output/INHERITANCE_QA.json), [artifact hashes](output/SHA256SUMS.json), [official packaging checks](JSA_REQUIREMENTS_RECHECK.md).

All 26 claims and 28 experiment groups have exact roles/destinations. The main retains decisive comparisons, failures and method conditions. The supplement adds linked navigation and stable S1–S7 sections. The second-family insertion plan is in AUTHOR_TODO; the main retains the single-family limitation.

Fresh checks authenticate 133 source bindings, 26 evidence exports and 16 historical copies; the latter 42 also match retained v0.14.0. Git tree identities are checked separately for this round's actual baseline. This is source/export validation, not a new complete private raw-archive audit or hardware replay. `INHERITED_V014_*` records and original-host audits remain explicitly historical.

Authors still need to confirm identities/affiliations, CRediT, funding/interests, permissions/permanent data access, final AI disclosure and human scientific/language/bibliographic review. JSA's current guide returned 403; latest journal-specific fields remain unconfirmed. No missing B570 row/raw comparison/interruption cost is supplied.
