# Phase-Scoped Query Layouts for Reference-Preserving Speculative Decoding

**Version 0.15.0 — complete reconstructed author-review manuscript (13 October 2026).**

The paper's core is a specific runtime method: decouple attention query geometry from target-wide batching using query/mask views, phase activation and layout-sensitive graph reuse. The numerical-replay, complete-output and implementation-cost claims are distinct. B570 PR101 is incorporated as a complementary projection/state-boundary study, not a Vulkan QB port.

## Files
- `main.tex` + `sections/`: complete English main article.
- `supplement.tex` + `supplement/`: contracts, all reported primary costs, failed controls and the complete28-group legacy disposition index.
- `figures/`: five original, editable TikZ/PGF vector figures (not screenshots).
- `references.bib`: related-work and commit-pinned companion evidence references.
- `psql-num.bst`: renamed LPPL-compatible derivative of `elsarticle-num`; retains linked reference titles and DOIs but removes redundant printed long URL lines. Revert to the official journal style if required at submission.
- `data/`: reported-value CSV/JSON, task regressions, historical ledger destinations.
- `CLAIM_EVIDENCE.md`:16 bounded main claims and evidence pointers.
- `RECONSTRUCTION_REVIEW_ZH.md`: structural decisions and author-side consistency review.
- `AUTHOR_CHECKLIST.md`: items requiring author judgment before submission.
- `PR_BODY.md`: ready-to-use description of a future documentation/manuscript PR.
- `scripts/build.py`: portable PDF build with BibTeX executable fallback.
- `scripts/check_reported_data.py`: count/ratio/contract/citation consistency checks; not a raw GPU audit.
- `scripts/install_into_repo.py`: opt-in copy into a NEW repository directory; refuses overwrite. It does not commit, push, merge or create a PR.

## Build
Install a TeX distribution with `elsarticle`, TikZ/PGFPlots, `microtype`, `booktabs`, `tabularx`, `longtable`, `enumitem`, `xurl`, `flushend` and standard Times-compatible fonts.

```sh
python scripts/check_reported_data.py
python scripts/build.py
```

The script produces `output/main.pdf` and `output/supplement.pdf`. On Overleaf, upload the source directory and choose `main.tex` or `supplement.tex`; use pdfLaTeX. The source does not require shell escape or an external image service.

## Evidence and provenance
Pinned reconstruction main: `f5b7b8e9a6d02b228cb0e7b7b3932e89327cfb63`.
Core CUDA evidence: PR91/94 and PR98; final B570 evidence: PR99 and PR101, the latter pinned at `26706c9fb4818ec3465e45acea029c4ab88a390f`.
`provenance/SOURCE_MANIFEST.json` identifies report texts and original Git blobs. The named earlier review Markdown was not located in the available Library; its user-quoted recommendations, retrieved source reports and ledger are the reconstruction brief.

The companion tables here are **transcribed reported results**. The local checker verifies arithmetic, denominators, source keys and stated boundaries. No new GPU experiment was run, no full675MB native archive was downloaded/re-audited here, and original-host PASS reports are not represented as new independent audits. Historical evidence is retained through all28 explicit destinations and immutable repository pointers; it is not all embedded in this ZIP. Original repository files are untouched.

## Repository integration
This directory is the source import of the delivered v0.15.0 author package, proposed on a separate Draft PR. The earlier statement that GitHub writing was unavailable was incorrect; the current connector provides branch/commit/PR creation.

The PR adds only `paper/jsa/manuscript_v0150/`; prior papers and experimental data remain unchanged. PR101 is cited by immutable commit rather than merged by this import. This is not a new GPU experiment, raw-archive audit, journal submission or arXiv update.

Prebuilt `output/main.pdf` and `output/supplement.pdf` remain in the delivered conversation package rather than the Git source change. Run `python scripts/build.py` to generate them locally. The original delivery manifest is retained as `PACKAGE_MANIFEST.json` and therefore includes those two intentionally untracked PDFs and the original README hash; use `GITHUB_IMPORT.json` for the exact imported-source byte inventory. Original PDF QA records describe the delivered build, not a new GitHub CI run.

`PR_BODY.md` remains the supplied review-description template. `scripts/install_into_repo.py` is retained for offline package users; it is not necessary inside this repository directory.

## Publication status
This is an author-review draft, not an accepted/submitted paper. Confirm scientific wording, exact converted-model descriptions, funding/conflicts, AI-use disclosure, public artifact access and current venue requirements. There is no fourth-family, general determinism, exact kernel-schedule or cross-platform QB claim.
