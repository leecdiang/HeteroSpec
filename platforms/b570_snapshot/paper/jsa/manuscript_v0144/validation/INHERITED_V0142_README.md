# JSA author manuscript v0.14.2 — visual reconstruction

**Reference-Preserving Speculative Decoding on Consumer Systems: Diagnosis, Repair Scope, and Paid Cost**

Inherits Draft PR #72 at `a686af6b4fb537b84a5e52a3736633d21c752801`. This revision redraws five main figures around the existing scientific argument, following the author's ASV visual reference. It preserves the frozen evidence and limits prose changes to captions, panel references and a B570 causal-scope clarification.

| Delivery | Entry |
|---|---|
| Main, 13 pages, normal Elsevier 5p double column | [PDF](output/jsa-manuscript-v0.14.2.pdf), [main.tex](main.tex) |
| Independent supplement, 27 pages | [PDF](output/jsa-supplement-v0.14.2.pdf) |
| Complete editable author sources and bound exports | [Overleaf ZIP](output/overleaf-author-source-v0.14.2.zip) |
| Separate flat submission source packages | [Main](output/editorial-manager-main-flat-source-v0.14.2.zip), [supplement](output/editorial-manager-supplement-flat-source-v0.14.2.zip) |
| Visual rationale and exact evidence mapping | [FIGURE_LAYOUT.md](FIGURE_LAYOUT.md) |
| Chinese change record | [RECONSTRUCTION_ZH.md](RECONSTRUCTION_ZH.md) |
| Ready-to-use text-editing prompt for 6.1sol | [VISUAL_HANDOFF_TO_SOL.md](VISUAL_HANDOFF_TO_SOL.md) |
| Validation and scope | [VALIDATION_LOG.md](VALIDATION_LOG.md), [SCIENTIFIC_AUDIT.md](SCIENTIFIC_AUDIT.md) |
| Claims, experiments and unresolved author facts | [claims](CLAIM_EVIDENCE.md), [experiments](EXPERIMENT_DESTINATIONS.md), [AUTHOR_TODO.md](AUTHOR_TODO.md) |

The 12–15-page goal is the author's layout target, not a verified JSA page limit. The retained `elsarticle` class uses `final,5p,times,twocolumn`; this is an author manuscript layout, not a promise about final journal typesetting. Normal margins and body size remain unchanged. Main cost tables round display values to three decimals; exports and supplementary tables retain their precision. The typography fix uses vector Latin Modern Typewriter for code identifiers.

## Rebuild

Python 3, NumPy, Matplotlib; TeX Live with pdfLaTeX, BibTeX, latexmk and Latin Modern; Poppler. Pillow supports page contact sheets; pdfplumber supports the additional figure check.

```bash
python3 build.py
python3 scripts/check_visuals.py
python3 scripts/check_package.py
python3 scripts/flat_sources.py
python3 scripts/render_qa.py
```

In Overleaf select `main.tex` or `supplement.tex` with pdfLaTeX. Supplied PDF figures and editable tables allow compilation without Python. No live Overleaf or Editorial Manager upload was performed. PDF and SVG figure sources are in `figures/`; the drawing code is `scripts/visual_figures.py`; quantitative figure inputs and source hashes are in `output/FIGURE_INPUTS.json`.

The full CPU rebuild authenticates 133 bound source copies, 26 evidence exports and 16 historical copies. The separate standard-library checker is retained under its original filename `audit_v0141.py`; its current receipt identifies v0.14.2. Original v0.14.1 narrative receipts are explicitly archived in `validation/INHERITED_V0141_*`. Those historical records are not this revision's receipts.

Only committed sources and exports were checked. No new model experiment or complete private raw-archive audit occurred. The single-model-family limitation, missing B570 payload, author declarations and bibliography confirmation remain open. Journal requirement notes are inherited from #72; this visual revision does not reverify current submission rules or claim journal acceptance.
