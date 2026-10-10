# HeteroSpec v0.14.5 — editorial closeout

**Reference-Preserving Speculative Decoding on Consumer Systems: Diagnosis, Repair Scope, and Measured Cost**

This revision aligns the title, 204-word abstract, introduction contributions and conclusion around local diagnosis, configuration-specific repair and measured cost. It builds on Draft PR [#75](https://github.com/leecdiang/HeteroSpec/pull/75), commit `92b08a0ffab2ca08c835b411d9d7478ccd57603b`. Changes stay in `paper/jsa/manuscript_v0145/`; earlier versions remain intact.

| Deliverable | File |
|---|---|
| **arXiv combined PDF, 24 pages** | [Single PDF](output/arxiv-combined-v0.14.5.pdf) |
| Minimal arXiv sources for the combined document | [ZIP](output/arxiv-source-v0.14.5.zip), [update notes](ARXIV_UPDATE_ZH.md) |
| Separate author-review main/supplement | [Main, 12 pages](output/jsa-manuscript-v0.14.5.pdf), [supplement, 13 pages](output/jsa-supplement-v0.14.5.pdf) |
| Complete author sources and reproducibility records | [ZIP](output/overleaf-author-source-v0.14.5.zip) |
| Separate flat journal sources | [Main](output/editorial-manager-main-flat-source-v0.14.5.zip), [supplement](output/editorial-manager-supplement-flat-source-v0.14.5.zip) |
| Rationale and checks | [Closeout review](CLOSEOUT_REVIEW_ZH.md), [validation](VALIDATION_LOG.md), [edit receipt](provenance/CLOSEOUT_EDIT_RECEIPT.json) |

The abstract retains the three request ratios (1.742 ordinary-to-speculative, 1.683 ordinary-to-matched, 1.035 matched-to-speculative), seven task regressions, the round reversal and qualified-but-slower cases. Generation ratios remain in the body and tables. The conclusion explicitly retains the missing second family, same-contract external comparison and independent-session evidence. No new inference or hardware experiment is added.

All seven figures, their 14 PDF/SVG assets and eight generated tables are byte-identical to #75. Figure 1C retains its larger box gaps and arrow clearance. Figure 2 retains its categorical equality links, explicit donor/recipe labels and continuation bars. Shared ASV-derived roles remain blue for target/reference, ochre for draft/alternate and green for constraint/qualification/conditional bounds. The supplement remains 13 pages in normal Elsevier 5p Times double columns.

The [humanizer v3.1.0 instructions](https://github.com/blader/humanizer/blob/225a6f39ac85f76ee48dbad772ea4abe4ed6c9d8/SKILL.md) guided the final prose reading. The original 19-file humanizer receipt is preserved. A separate closeout receipt reverses the four new TeX edits to exact #75 sources before running the inherited checks. Of 299 authenticated baseline source files, 287 remain byte-identical, four carry recorded manuscript changes and eight update build/delivery documentation. Equations, citations, result references, figures, tables and layout commands remain unchanged in the four edited files. Hashes establish recoverability, not semantic equivalence.

## Rebuild

Python 3 with NumPy, Matplotlib, pdfplumber, Pillow and PyMuPDF; TeX Live with pdfLaTeX, BibTeX, latexmk and required fonts; Poppler.

```bash
python3 build.py
python3 scripts/check_package.py
python3 scripts/flat_sources.py
python3 scripts/arxiv_sources.py
python3 scripts/render_qa.py
```

The full build checks frozen numerical exports, the standard-library scientific audit, 22 locked figure/table assets, both PDFs, closeout recovery, inherited humanizer edits, lossless content and visual data. The author ZIP needs no sibling checkout. Historical rendering scripts remain as historical tools; replacing locked assets would require a fresh authenticated revision.

The minimal arXiv ZIP contains 37 required files: manuscript dependencies, seven vector figures, one shared prebuilt bibliography and `00README.json`. A single `arxiv.tex` entry places the main manuscript and shared references before the supplement, with continuous page numbers and a separate supplement contents list. It excludes evidence exports, historical sources, Python code and internal reviews. The builder compiles this entry from an empty directory into one 24-page PDF, checks all links and 30 supplement navigation entries, and verifies byte-identical repeat compilation. This is local validation, not live arXiv acceptance.

The arXiv document inherits Chengzhan Li, the University of Electronic Science and Technology of China, and the contact email from [published v1](https://arxiv.org/abs/2610.03228v1). It replaces internal author-review forms with factual AI-assistance and reproducibility statements; it asserts no unconfirmed funding, conflicts or public deposit. The separate journal drafts retain their author-review forms. Read [ARXIV_UPDATE_ZH.md](ARXIV_UPDATE_ZH.md) before updating arXiv. The complete author ZIP is for editing/reproduction rather than minimal public submission. Neither arXiv submission nor PR merge is performed here.

## Inherited records

`CROSS_REVIEW_ZH.md`, `HUMANIZER_REVIEW_ZH.md`, `RECONSTRUCTION_ZH.md` and `FIGURE_LAYOUT.md` preserve the v0.14.4 history; their version-specific paths and counts describe that round. Its exact validation log is in `validation/INHERITED_V0144_VALIDATION_LOG.md`. Current checks are in `output/` and `VALIDATION_LOG.md`.

The provenance chain still checks 16 original tables, 537 generated cells plus inline tables, 26 claims, 28 experiment entries and seven original scientific-input objects. Private raw-archive audits remain inherited; B570's missing payload remains unavailable.
