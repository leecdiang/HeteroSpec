# Manuscript v0.2 — hardware-complete / runtime-reserved

Provisional title: **Speculative Decoding Across Consumer Systems: Gains, Failures, and Runtime Costs**.

- Main source: `main.tex`; anonymous compiled deliverable: `output/manuscript-v0.2.pdf`.
- Separate appendix: `appendix.tex`; deliverable: `output/appendix-v0.2.pdf`.
- Frozen scientific control: `../PAPER_FRAMEWORK_HANDOFF.md` (unchanged).
- Claim ledger, machine-readable values, numerical checks, PDF checks, and literature audit: `../evidence/`.
- Narrative hierarchy, scope, title alternatives and figure coordination: `../NARRATIVE_REFACTOR_V02.md`.
- Completion and page plan: `../MANUSCRIPT_STATUS.md`.

## Build

Requires TeX Live with latexmk, BibTeX, Times, AMS math, TikZ/PGFPlots, microtype, hyperref and xurl. No style modifications or page-compression settings are used. The official package is resolved directly from `vendor/official/mlsys2025style`; keep its untouched ZIP and SHA256SUMS.

From this directory:

```sh
make all
make hardware-only
make check
```

`make all` needs Python 3's standard library. `make check` additionally needs NumPy and pypdf; select an environment with `make check PYTHON=/path/to/python3`. It independently replays campaign estimators and bootstrap conventions, checks source/style hashes, and verifies compiled PDF anonymity, font embedding, bibliography author completeness, and the main-page boundary. It never reruns an experiment or modifies frozen evidence. Figure coordinates and numeric TeX macros regenerate from the repository; quantitative edits belong in neither generated file.

`make hardware-only` excludes Section 7 at compile time. Its local verification PDF is `build/hardware-only/hardware-only.pdf`; the primary delivered version retains the reserved section. There are no references that require that section for the hardware story. Build intermediates and alternative verification PDFs are ignored. Both v0.2 deliverables are tracked; the prior v0.1 PDFs remain available unchanged.

Four included publication figures are native vector TikZ/PGFPlots sources under `figures/`. Quantitative coordinates are generated from the ledger sources. Main tables cover platforms, headline outcomes, and verification/admissibility, in that order. Separate appendix tables cover frozen statistics and sensor boundaries. The old accounting schematic remains as an unused source. Independent figure candidates are not integrated; see `../NARRATIVE_REFACTOR_V02.md` for role coordination and the current placement map for the unchanged evidence ledger.

## Review boundary

Only the two output PDFs are anonymous review artifacts. Internal evidence documents contain repository paths, source commits and private provenance. The unchanged official vendor examples contain the conference's sample author information and build logs; none is input to our manuscript. Do not distribute the entire source tree as an anonymous artifact without a separate release review.

The default review notice comes from the official style; no submission has occurred. The CFP permits LLM-assisted writing but requires author scientific review. This draft is prepared for that review, not a substitute for it. Runtime state persistence, qualified path selection, and optional profitability control are explicitly proposed only. No runtime intervention or new experiment is claimed.
