# JSA author-review reconstruction v0.14.0

**Reference-Preserving Speculative Decoding on Consumer Systems: Diagnosis, Repair Scope, and Paid Cost**

This complete English manuscript reconstructs the evidence in PR #70 around diagnosis, implementation repair scope, and paid ordinary/matched cost. It is an author-review draft, not a submitted paper. No model inference, new warmup, merge, journal submission or data publication is performed in this revision.

## Read and review

- `output/jsa-manuscript-v0.14.0.pdf`: main paper; editable entry `main.tex`.
- `output/jsa-supplement-v0.14.0.pdf`: independent supplementary material S1; entry `supplement.tex`.
- `output/overleaf-author-source-v0.14.0.zip`: S2 author source bundle.
- `Highlights.txt`: five separate submission Highlights, each at most 85 characters.
- `RECONSTRUCTION_ZH.md`: Chinese account of the scientific reconstruction.
- `CLAIM_EVIDENCE.md` and `CLAIM_EVIDENCE.csv`: claims, actual sources and permitted scope.
- `EXPERIMENT_DESTINATIONS.md` and `EXPERIMENT_DESTINATIONS.json`: every planning-ledger experiment group and its destination.
- `AUTHOR_TODO.md`, `JSA_REQUIREMENTS_RECHECK.md`, `REFERENCE_AUDIT.json`: unresolved author information and submission checks.
- `output/NUMERICAL_QA.json`, `output/BUILD_QA.json`, `output/SOURCE_PACKAGE_REBUILD_QA.json`, `output/VISUAL_QA.json`, `output/REMOTE_INHERITANCE_QA.json`: actual validation records.
- `VALIDATION_LOG.md` and `provenance/AUTHOR_QA_SNAPSHOT.json`: validation scope and the portable author-side snapshot.

## CPU-only rebuild

Use Python 3 with NumPy and Matplotlib, a TeX Live installation with `latexmk`, pdfLaTeX/BibTeX, and Poppler (`pdftotext`, `pdfinfo`, `pdffonts`). On the authoring environment the primary runtime's Python is suitable. From this directory:

```bash
python build.py
```

This authenticates copied sources, checks frozen evidence, regenerates editable tables and separate PDF/SVG figures, compiles both documents, rejects overfull/undefined-reference diagnostics, and packages author sources. It does not run the archived historical build scripts or any runtime implementation. `python scripts/reconstruct.py` repeats only CPU arithmetic and figures. `python build.py --no-package` rebuilds without creating a nested ZIP. `--skip-assets` compiles the supplied figures/tables after editorial checks; use the full default for numerical reconstruction.

Run `python scripts/check_package.py` after building to extract the final ZIP into an empty directory and repeat the full CPU build, checking both PDF bytes/text, generated figure/table bytes and numerical QA. `python scripts/render_qa.py` renders every page and numbered contact sheets for manual inspection; rendering alone does not count as visual review. NumPy, Matplotlib and optional Pillow dependencies are listed in `requirements.txt`; the exact authoring environment is recorded in the portable QA snapshot.

In Overleaf, upload the ZIP and set `main.tex` or `supplement.tex` as Main document, using pdfLaTeX. Tables and vector figures are supplied, so Python is not required for ordinary Overleaf compilation. The class and bibliography style are included. This package was tested by a fresh local extraction/rebuild; no claim is made about a live Overleaf account run.

## Source and scientific boundary

Base commit: `00ea8f7c3a49b900bf5f21a95876e9a3a6dd610f`, a child of v0.13.0 head `21aa7b29142a1e3b7130b8e4a6a252777a91af80`. The new independent branch is `paper/jsa-v014-rewrite-20261009`; the review target is the reconstruction-plan branch while it remains open. Historical manuscript versions, experiments and freeze tags are preserved.

`evidence/` contains the **unchanged 26 inherited export files**; `historical_sources/` contains **16 unchanged source copies**. `source_records/` preserves all 133 authenticated files read for this revision. The receipts record Git blob and SHA-256 identities. This is an authenticated source subset, not a full local clone or a full private raw archive audit. Repo-wide preservation is checked separately against the remote baseline tree.

RTX full-response equality, B570 first-EOG/cap128 endpoint equality, and historical re-tokenized-text agreement remain distinct. B570 stays 119/120, with 15 complete ordinary/matched/candidate pairs and 14 old-N1 pairs. Suffix work is paid. RTX request gains are 1.742× ordinary and 1.035× matched, while the matched draft-free path already gives 1.683×. Seven matched request regressions and the reversed second round remain. Single-family limits, failed wider geometry, qualified-but-slower width, and the negative B570/M4/358H operating decisions remain visible.

The records are author-side validation, not external peer review or commercial similarity checking. Authors must confirm identity, affiliations, contributions, funding, conflicts, permanent data access and AI disclosure before submission. The second model-family extension has a natural insertion point but no promised or fabricated result.
