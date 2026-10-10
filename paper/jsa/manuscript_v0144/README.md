# JSA author manuscript v0.14.4

**Reference-Preserving Speculative Decoding on Consumer Systems: Diagnosis, Repair Scope, and Paid Cost**

Cross-review and supplement compression, stacked on latest scientific-edit PR [#74](https://github.com/leecdiang/HeteroSpec/pull/74), HEAD `e6236d220a5123c691153f2558b8d4dc5d92b0c6`. Changes stay in the new `paper/jsa/manuscript_v0144/` directory. Earlier manuscripts and measurements are preserved.

| Deliverable | File |
|---|---|
| Main, 12 pages | [PDF](output/jsa-manuscript-v0.14.4.pdf), [main.tex](main.tex) |
| Supplement, 13 pages, down from 27 | [PDF](output/jsa-supplement-v0.14.4.pdf), [supplement.tex](supplement.tex) |
| Complete editable author sources, code and bound exports | [Author ZIP](output/overleaf-author-source-v0.14.4.zip) |
| Separate flat submission sources | [Main ZIP](output/editorial-manager-main-flat-source-v0.14.4.zip), [supplement ZIP](output/editorial-manager-supplement-flat-source-v0.14.4.zip) |
| Chinese cross-review and scientific issues | [CROSS_REVIEW_ZH.md](CROSS_REVIEW_ZH.md) |
| Changes and figure conventions | [RECONSTRUCTION_ZH.md](RECONSTRUCTION_ZH.md), [FIGURE_LAYOUT.md](FIGURE_LAYOUT.md) |
| Actual verification and scope | [VALIDATION_LOG.md](VALIDATION_LOG.md), [SCIENTIFIC_AUDIT.md](SCIENTIFIC_AUDIT.md) |
| Evidence navigation | [26 claims](CLAIM_EVIDENCE.md), [28 experiment groups](EXPERIMENT_DESTINATIONS.md) |
| Author facts and submission items | [AUTHOR_TODO.md](AUTHOR_TODO.md), [JSA_REQUIREMENTS_RECHECK.md](JSA_REQUIREMENTS_RECHECK.md) |

The supplement uses the same normal `final,5p,times,twocolumn` class options and serif type as the main. Compression comes from two columns, inline contents and full-width table reflow. All S1–S7 sections, 23 subsections, 12 supplementary tables, existing paragraphs, result values, failures, missingness and citations remain. The two new figures are included within the 13 pages. The body font, leading and margins use the normal class settings; no negative spacing or graphic scaling of table text is used. The saved official JSA guide permits LaTeX double-column submissions; current live portal acceptance is not established.

Figure 2 makes the donor labels explicit: ordinary N0 for MBPP/72, Alt. = E_k1_ub2 for HumanEval, with UB1/r3 and UB2/r2 columns. All categorical observations remain unchanged. Figures S1/S2 clarify B570 same-context phase binding, endpoint/paid-work/missingness contracts, and 358H measured speeds versus conditional ceilings. Four other main figures remain byte-identical. The ASV reference's restrained serif, blue/ochre/green, fine-line and panel conventions continue across all seven figures.

## Rebuild

Python 3 with NumPy, Matplotlib, pdfplumber and Pillow; TeX Live with pdfLaTeX, BibTeX, latexmk and required fonts; Poppler.

```bash
python3 build.py
python3 scripts/check_package.py
python3 scripts/flat_sources.py
python3 scripts/render_qa.py
```

The default build authenticates all 22 supplied figure/table assets against `provenance/LOCKED_REVISION_ASSETS.json`, rechecks the frozen numerical exports and standard-library scientific audit, compiles both PDFs, then verifies no-loss content and plotted inputs. It preserves supplied artwork/table layout. `scripts/revision_figures.py` can redraw the label correction and two supplements using the unchanged shared drawing style; it does not redraw the other four main figures. `scripts/reconstruct.py` retains its original numerical computation and historical table-generation routines; the current build uses `recompute_only.py` to preserve the reformatted tables.

`provenance/V0143_BASELINE_CONTENT.json` authenticates the 268 baseline source members against #74 Git blobs and supplies portable text/table/asset comparison receipts. `output/LOSSLESS_COMPRESSION_QA.json` checks every original supplementary section, 537 generated data cells plus inline tables, 26 claim rows and 28 experiment entries. Current PDF, numerical, figure-value and package receipts are under `output/`; `validation/INHERITED_*` describes earlier rounds.

For Overleaf, choose `main.tex` or `supplement.tex` and pdfLaTeX; Python is unnecessary for compiling the supplied assets. The separate flat archives contain one entry each and are rebuilt locally. Local compilation does not establish live Overleaf or Editorial Manager acceptance.

The cross-review records the remaining single-family, same-contract external-comparison and independent-session limitations. B570's missing payload remains unavailable. No new inference or hardware experiment was performed; private raw-archive audits remain inherited. Author declarations, access decisions and final reference confirmation stay pending.
