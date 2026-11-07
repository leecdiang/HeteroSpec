# HeteroSpec: reference-preserving query batching

This is the 2026-11-03 manuscript candidate built on the PR154 paper baseline (`07bee1c5`, `scope_state_revision_20261101`). The current PDF is **10 pages**, including references and appendices. The preceding manuscript sources remain preserved in the repository. This candidate has **not been merged or submitted** to arXiv or a journal.

## Build

From this directory:

```sh
python3 scripts/reconstruct.py
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The output is `main.pdf`. The reconstruction script uses the Python 3 standard library and the saved records in `data/`; it regenerates the timing table, editable timing figure and `data/RECOMPUTED.json`. It does not run model inference.

Use a standard TeX Live or MiKTeX installation with `latexmk`, pdfLaTeX, BibTeX, the Elsevier `elsarticle` class and the packages imported by `preamble.tex`, including TikZ/PGFPlots. The bibliography style `psql-num.bst` is included. No custom replacement for `elsarticle` is required.

## Source map

| File | Content |
|---|---|
| `main.tex` | Title, abstract, declarations and document assembly |
| `01_introduction.tex` | Existing-reference compatibility and the contribution |
| `02_mechanisms.tex` | Physical-prefix, activation-arithmetic and placement interventions |
| `03_method.tex` | Extent extraction, contiguous grouping, QB lowering and graph identity |
| `04_evaluation.tex` | Systems, comparisons, confirmation panels and timing estimands |
| `05_results.tex` | Repair, model/backend coverage, complete costs and repair scope |
| `06_related.tex` | Related work and the evaluated application domain |
| `07_conclusion.tex` | Main result and design principle |
| `appendix.tex` | Transactional conditions, source integration and artifact entrypoints |
| `data/` | Saved timing inputs, recomputed values, coverage and source identities |
| `figures/` | Editable TeX figures |

## Evidence and implementation status

The current Llama GPU results come from the frozen native implementations in **PR162** (CUDA, `e11d2b75`; scientific snapshot `70086c63`) and **PR163** (Vulkan, `10a70566`). The CUDA Qwen3-14B placement result comes from **PR159** (`38b3d3d3`). Earlier scope and producer-state evidence retains the PR154 baseline's original sources and experimental definitions. See `data/SOURCE_MANIFEST.json` and the artifact appendix for the source mapping.

The accompanying shared planner is a separate integration candidate with **CPU and source-integration validation**. Its refactored code has no new GPU result, and automatic extraction of backend arithmetic policies is not yet connected. The native measurements above are not attributed to this candidate. The coverage table records which model/backend paths actually exercised each repair.
