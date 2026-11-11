# JSA author manuscript v0.14.3 — English scientific edit

**Reference-Preserving Speculative Decoding on Consumer Systems: Diagnosis, Repair Scope, and Paid Cost**

This revision starts from the latest visual PR #73, branch `codex/jsa-v0142-asv-visual-20261010`, at `f7d2a863265e6d619d3582d702e57cec1cfa9be2`. It rewrites the English argument around the supplied five figures and keeps their artwork, all eight editable data tables, frozen exports, estimators and comparison panels unchanged. The previous manuscript directories remain separate.

| Delivery | Entry |
|---|---|
| Main, 12 pages, normal Elsevier 5p double column | [PDF](output/jsa-manuscript-v0.14.3.pdf), [main.tex](main.tex) |
| Independent supplement, 27 pages | [PDF](output/jsa-supplement-v0.14.3.pdf), [supplement.tex](supplement.tex) |
| Complete editable author sources and bound exports | [Overleaf ZIP](output/overleaf-author-source-v0.14.3.zip) |
| Separate flat submission sources | [Main ZIP](output/editorial-manager-main-flat-source-v0.14.3.zip), [supplement ZIP](output/editorial-manager-supplement-flat-source-v0.14.3.zip) |
| Chinese editorial change note | [RECONSTRUCTION_ZH.md](RECONSTRUCTION_ZH.md) |
| Figure reading and preserved scientific scope | [FIGURE_LAYOUT.md](FIGURE_LAYOUT.md) |
| Actual checks and limits | [VALIDATION_LOG.md](VALIDATION_LOG.md), [SCIENTIFIC_AUDIT.md](SCIENTIFIC_AUDIT.md) |
| Complete evidence navigation | [26 claims](CLAIM_EVIDENCE.md), [28 experiment groups](EXPERIMENT_DESTINATIONS.md) |
| Unresolved author facts | [AUTHOR_TODO.md](AUTHOR_TODO.md) |

The author's 12–15-page target is met without changing the retained `final,5p,times,twocolumn` class options, body size, leading, margins or spacing. This is an author manuscript layout; it does not establish a JSA page limit or final publisher typesetting. Display ratios follow the existing figures and main tables; underlying precision is retained.

## Rebuild

Python 3, NumPy and Matplotlib; TeX Live with pdfLaTeX, BibTeX, latexmk and Latin Modern; Poppler. Pillow supports contact sheets and pdfplumber supports figure checks.

```bash
python3 build.py
python3 scripts/check_visuals.py
python3 scripts/check_package.py
python3 scripts/flat_sources.py
python3 scripts/render_qa.py
```

The default build recalculates frozen results but **does not regenerate figures or tables**. `scripts/recompute_only.py` authenticates all 18 supplied PDF/SVG/table assets against `provenance/LOCKED_VISUAL_ASSETS.json`, executes the unchanged `reconstruct.compute()`, and copies the baseline figure-input receipt. Drawing scripts remain available as historical editable sources, but were not run in this round.

For Overleaf, select `main.tex` or `supplement.tex` with pdfLaTeX. The supplied figures and tables compile without Python. Separate flat ZIPs serve the submission workflow. Neither workflow was tested in a live Overleaf or Editorial Manager session.

Current receipts are under `output/`: numerical and independent scientific QA, figure-value checks, asset preservation, editorial inheritance, PDF diagnostics, visual review and source-package rebuild. Archived `validation/INHERITED_*` records describe prior rounds, not fresh checks. The experiment JSON/claim CSV retain legacy `v0141` field names for checker compatibility; their locations and current revision identify v0.14.3.

This round checked the committed sources and exports, not the complete private raw archive. No model experiments were run. The single-model-family limitation, B570 missing old-N1 payload, author declarations, permanent access decision and bibliography confirmation remain unresolved.
