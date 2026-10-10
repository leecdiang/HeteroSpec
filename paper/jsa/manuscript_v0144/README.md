# JSA author manuscript v0.14.4

**Reference-Preserving Speculative Decoding on Consumer Systems: Diagnosis, Repair Scope, and Paid Cost**

Cross-review, lossless supplement compression, semantic visual refinement and a full humanizer prose pass in Draft PR [#75](https://github.com/leecdiang/HeteroSpec/pull/75), stacked on scientific-edit PR [#74](https://github.com/leecdiang/HeteroSpec/pull/74), HEAD `e6236d220a5123c691153f2558b8d4dc5d92b0c6`. Changes stay in the new `paper/jsa/manuscript_v0144/` directory. Earlier manuscripts and measurements are preserved.

| Deliverable | File |
|---|---|
| Main, 12 pages | [PDF](output/jsa-manuscript-v0.14.4.pdf), [main.tex](main.tex) |
| Supplement, 13 pages, down from 27 | [PDF](output/jsa-supplement-v0.14.4.pdf), [supplement.tex](supplement.tex) |
| Complete editable author sources, code and bound exports | [Author ZIP](output/overleaf-author-source-v0.14.4.zip) |
| Separate flat submission sources | [Main ZIP](output/editorial-manager-main-flat-source-v0.14.4.zip), [supplement ZIP](output/editorial-manager-supplement-flat-source-v0.14.4.zip) |
| Chinese cross-review and scientific issues | [CROSS_REVIEW_ZH.md](CROSS_REVIEW_ZH.md) |
| Changes and figure conventions | [RECONSTRUCTION_ZH.md](RECONSTRUCTION_ZH.md), [FIGURE_LAYOUT.md](FIGURE_LAYOUT.md) |
| Full prose review and exact edit receipt | [HUMANIZER_REVIEW_ZH.md](HUMANIZER_REVIEW_ZH.md), [receipt](provenance/HUMANIZER_EDIT_RECEIPT.json) |
| Actual verification and scope | [VALIDATION_LOG.md](VALIDATION_LOG.md), [SCIENTIFIC_AUDIT.md](SCIENTIFIC_AUDIT.md) |
| Evidence navigation | [26 claims](CLAIM_EVIDENCE.md), [28 experiment groups](EXPERIMENT_DESTINATIONS.md) |
| Author facts and submission items | [AUTHOR_TODO.md](AUTHOR_TODO.md), [JSA_REQUIREMENTS_RECHECK.md](JSA_REQUIREMENTS_RECHECK.md) |

The supplement uses the same normal `final,5p,times,twocolumn` class options and serif type as the main. Compression comes from two columns, inline contents and full-width table reflow. All S1–S7 sections, 23 subsections, 12 supplementary tables, scientific content, result values, failures, missingness and citations remain. The two new figures are included within the 13 pages. The body font, leading and margins use the normal class settings; no negative spacing or graphic scaling of table text is used. The saved official JSA guide permits LaTeX double-column submissions; current live portal acceptance is not established.

Figure 2 makes the donor labels explicit: ordinary N0 for MBPP/72, Alt. = E_k1_ub2 for HumanEval, with UB1/r3 and UB2/r2 columns. All categorical observations remain unchanged. Figures S1/S2 clarify B570 same-context phase binding, endpoint/paid-work/missingness contracts, and 358H measured speeds versus conditional ceilings. Figure 1C now separates the four phase switches and leaves air at arrow endpoints. Figure 2 uses undirected equality links over the complete categorical matrices and aggregate continuation bars. The remaining figures align target/reference, alternate/draft and constraint roles across both documents; colors do not encode timer domains or the sign of a speed gain. The ASV reference's restrained serif, blue/ochre/green, fine-line and panel conventions continue across all seven figures.

The [humanizer](https://github.com/blader/humanizer) pass uses pinned v3.1.0 instructions and two whole-text readings. Nineteen manuscript files were reviewed; 63 paragraph blocks in 17 files were revised. Every pre-edit source is exactly recoverable. The pass preserves numbers, mathematics, bound commands, all inline tables, all seven figure blocks and layout settings; scientific qualifications and negative/missing findings were also manually checked. Declarations and Highlights were read and retained.

## Rebuild

Python 3 with NumPy, Matplotlib, pdfplumber and Pillow; TeX Live with pdfLaTeX, BibTeX, latexmk and required fonts; Poppler.

```bash
python3 build.py
python3 scripts/check_package.py
python3 scripts/flat_sources.py
python3 scripts/render_qa.py
```

The default build authenticates all 22 supplied figure/table assets against `provenance/LOCKED_REVISION_ASSETS.json`, rechecks the frozen numerical exports and standard-library scientific audit, compiles both PDFs, then verifies no-loss content, recorded prose edits and plotted inputs. It preserves supplied artwork/table layout. `scripts/semantic_figures.py` redraws all seven figures from the retained initial v0.14.4 scientific inputs; `revision_figures.py` delegates to it. The original shared `visual_figures.py` styling is retained. `SEMANTIC_VISUAL_REVISION.json` records the exact initial/current asset hashes, controlled prose edits and color roles. `scripts/reconstruct.py` retains its original numerical computation and historical table-generation routines; the current build uses `recompute_only.py` to preserve the reformatted tables.

`provenance/V0143_BASELINE_CONTENT.json` authenticates the 268 baseline source members against #74 Git blobs and supplies portable text/table/asset comparison receipts. `output/LOSSLESS_COMPRESSION_QA.json` checks every original supplementary section, 537 generated data cells plus inline tables, 26 claim rows and 28 experiment entries. The initial scientific-input objects for all seven figures remain exactly equal. Of 191 protected baseline files, 183 remain byte-identical; only the eight explicitly authorized main figure PDF/SVG assets are restyled. Current PDF, numerical, figure-value, humanizer and package receipts are under `output/`; `validation/INHERITED_*` describes earlier rounds.

For Overleaf, choose `main.tex` or `supplement.tex` and pdfLaTeX; Python is unnecessary for compiling the supplied assets. The separate flat archives contain one entry each and are rebuilt locally. Local compilation does not establish live Overleaf or Editorial Manager acceptance.

The cross-review records the remaining single-family, same-contract external-comparison and independent-session limitations. B570's missing payload remains unavailable. No new inference or hardware experiment was performed; private raw-archive audits remain inherited. Author declarations, access decisions and final reference confirmation stay pending.
