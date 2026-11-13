# JPDC writing guide and official LaTeX kit

This directory prepares the next writing round; it is **not a manuscript rewrite**.

- Target: *Journal of Parallel and Distributed Computing* (JPDC), regular article.
- Selected title: **Parallelizing Quantized LLM Inference Under a Fixed Numerical Reference**.
- Publication preference: subscription/non-open-access route. Do not opt into paid OA or optional co-submission without the author's decision.
- `AUTHORING_GUIDE.zh.md`: project-specific Chinese summary and writing recommendations, **not an Elsevier-authored document**.
- `els-cas-templates.zip`: unchanged complete CAS v2.4 bundle, downloaded from the official CDN linked in the supplied guide. Includes single-/double-column templates, classes, styles, documentation and sample figures.
- `PROVENANCE.md`: source verification, licensing, test scope and limitations.
- `check-template.py`: offline ZIP integrity / required-source check. No GPU or model use.

## Use the official template

```sh
python3 check-template.py
unzip els-cas-templates.zip -d build
cd build/els-cas-templates
latexmk -pdf -interaction=nonstopmode -halt-on-error cas-dc-template.tex
```

Use a complete TeX Live or MiKTeX installation. The official blank template still contains example author/frontmatter fields: replace them before any real submission. For the paper, copy the template under a new filename; do not edit the vendored archive. `cas-sc-template.tex` is the single-column alternative. JPDC's supplied guide allows double-column LaTeX; we recommend `cas-dc` for planning the regular-article page budget, not as a mandatory journal requirement.

The stock template uses author-year `natbib`; the supplied JPDC guide describes numeric citations. For the future manuscript copy use `\usepackage[numbers]{natbib}` instead of the stock author-year line, and check citation ordering in the compiled output. The guide permits consistent reference formatting at initial submission; do not claim the unmodified stock sample is JPDC-styled.

No paper body, experiments, baselines or old evidence are changed here. This kit does not submit a manuscript, create a release, or make editorial claims.
