# Manuscript v0.4 — measured hardware and runtime studies

Title retained: **Speculative Decoding Across Consumer Systems: Gains, Failures, and Runtime Costs**.

Review PDFs: `output/manuscript-v0.4.pdf` and `output/appendix-v0.4.pdf`. Earlier versioned PDFs remain historical. The full manuscript includes the prospective M4 control study and the scoped 358H qualification outcome. See `../RUNTIME_INTEGRATION_V04.md` and `../MANUSCRIPT_STATUS.md` for decisions, provenance and final QA.

## Build and validate

Requires TeX Live/latexmk and the untouched official style in `vendor/official/mlsys2025style`. Python 3 builds assets; NumPy, pandas and pypdf are also required for QA.

```sh
make all
make hardware-only
make check PYTHON=/path/to/python3
make overleaf
```

`make check` preserves the 228 hardware numerical checks, source/style hashes, original bibliography entries, 57 prior prose numerical macros, five original figure replays, active figure source/placement checks, and anonymous PDF checks. It additionally checks the immutable M4 runtime sources/archive, independently recomputes the complete portable evidence bundle, verifies split selection, validates 23 paper macros, checks the pinned 358H compact diagnostic, and rejects stale proposal-only claims. The 358H local raw traces are not included in its pinned compact record and are not replayed. No model execution or new timing occurs.

Runtime macro definitions are generated separately in `tables/runtime_values.tex`, leaving the historical hardware values and generator unchanged. The runtime source map and independent verification receipt are `../evidence/RUNTIME_QA_V04.json`. The old hardware ledger remains immutable; `../evidence/RUNTIME_LEDGER_V04.md` supplements it.

Four main figures retain their original vector assets and native widths: M4 contrast, translation boundaries, verification paths, and 358H stateful costs. The added Table 3 reports M4 runtime ratios and CIs, explicitly separating speedup from descriptive oracle regret. The four existing appendix tables retain their original values. The appendix adds runtime estimators and provenance recovery.

`make hardware-only` remains an internal Section-7-removal/reference test. The abstract, synthesis and conclusion now describe the full measured contribution, so this stripped build is not a standalone hardware paper or a delivery artifact. The primary paper is the full manuscript.

`make overleaf` produces `output/overleaf-runtime-integration-v0.4.zip`, containing the current manuscript, required dependencies, and unchanged official style. No Overleaf project is created or uploaded. The v0.3 collaboration package is historical.

Only the two review PDFs are anonymous artifacts. Internal evidence records identify repository paths and commits; the whole source tree is not an anonymous release. This Draft PR is for author review, not a conference submission, and is not automatically merged.
