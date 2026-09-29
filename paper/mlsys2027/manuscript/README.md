# v0.8.1 submission-readiness candidate

Literature and positioning revision; closed science, all figures, numeric macros and the scientific author-freeze tag remain unchanged. Three headline contributions now cover execution-path qualification, frozen B570 prediction and realized 358H cost. Title unchanged pending author review. Current outputs: `output/manuscript-v0.8.1.pdf`, `appendix-v0.8.1.pdf`, `hardware-only-v0.8.1.pdf`, `overleaf-submission-readiness-v0.8.1.zip`.

Build with `python scripts/build_v081.py` using a Python environment with pypdf and TeX Live/latexmk. It creates fresh temporary build directories, compiles the separate appendix and internal hardware proof, verifies all fonts/anonymity/citations/layout and rebuilds the ZIP independently with plain `latexmk -pdf main.tex` and `latexmk -pdf appendix.tex`. Run `python scripts/validate_readiness_v081.py` for immutable-scope checks. These commands invoke no measurement/model runners and overwrite only v0.8.1 outputs/QA receipts. Render and visually review the final PDFs after prose changes. The legacy Makefile and older scripts reproduce older versions and are not the v0.8.1 entrypoint.

Evidence: `../evidence/*V081*`; exactly three focused review records: `../reviews/submission_v081/`. Main 10 body + 2 reference pages; appendix 6; internal proof 9 + 2. The source ZIP is an author-collaboration bundle, not an anonymous repository artifact release. Author title/profile/conflict review and final submission remain pending; keep PR Draft and unmerged.

---

# v0.8 B570 mechanism integration

The current author-review Draft PR adds the frozen B570 target-only UB1 predictor and reserved 72/72 complete-sequence validation to Section 5 and the appendix. It changes no closed experiment, prior numeric macro, Figure 3 PDF or official style. The main body is ten pages plus references, appendix six pages. Outputs are `output/manuscript-v0.8.pdf`, `appendix-v0.8.pdf`, `hardware-only-v0.8.pdf`, and `overleaf-mechanism-integration-v0.8.zip`.

From this directory, use `latexmk -pdf -output-directory=build main.tex` and `appendix.tex` with `TEXINPUTS` and `BSTINPUTS` including `vendor/official/mlsys2025style/`; compile `\def\HardwareOnly{1}\input{main.tex}` for the hardware proof. Run `python scripts/package_overleaf_v08.py` and `python scripts/validate_mechanism_v08.py`. The source ZIP was built in an independent directory and matched page counts/extracted text. Full historical/large-archive replay requires a complete authenticated repository checkout; the v0.8 local QA receipt distinguishes rerun checks from prior receipts.

Earlier build and scientific history follows.

---

# v0.7 prospective direct-ID qualification integration

Current author-review sources and outputs use v0.7. The new RTX/B570
qualification studies are separate from historical timing: RTX 75/90 to
90/90; B570 60/90 to 78/90, with a frozen 90/90 gate. Figure 3 separates
historical physical opportunity and fresh qualification. The historical
comparator record, old outputs and approved figures remain preserved.

Build with `make all hardware-only overleaf`, then `make check`. With an
existing Tectonic executable, run
`python scripts/build_v07.py --tectonic PATH_TO_TECTONIC` from the manuscript
directory. Run `python scripts/render_v07.py` and inspect every page.
All checks are offline; no model inference or parameter search is required.
Portable archive checks replay retained evidence, not omitted weights.

Delivery: `manuscript-v0.7.pdf`, `appendix-v0.7.pdf`,
`hardware-only-v0.7.pdf`, and `overleaf-direct-id-integration-v0.7.zip` under
`manuscript/output/` (or `output/` in the manuscript directory).
See the v0.7 scope/audit, versioned QA receipts, `MANUSCRIPT_STATUS.md`, and
`reviews/submission_v07/` for final pagination and independent review.
This is a draft for author review; the PR must remain Draft and unmerged.
Earlier status sections below are historical.

---

# Manuscript v0.6 — paired M4 secondary analysis

Current outputs: `output/manuscript-v0.6.pdf`, `output/appendix-v0.6.pdf`, and
`output/overleaf-guard-always-secondary-v0.6.zip`. The direct Guard/Always-Spec
contrast is reviewer-requested post-study secondary analysis of frozen raw
observations. Guard had higher latency on this held-out comparison. See
`../reviews/M4_GUARD_ALWAYS_SECONDARY_RESPONSE_V06.md` and the committed plan
in `benchmarks/m4_runtime/GUARD_ALWAYS_SECONDARY_ANALYSIS_PLAN.md`. All v0.5
submission-review findings and historical table overlays remain in force.
Current integration base is main `9b996dd702e5807b3cacc9db9c69aa7eb80035a4` after PR #29;
its approved figures and compact primary table layout are preserved alongside
the separate secondary row. No new model execution, timing, or policy tuning occurred.

## Reproduce

From `paper/mlsys2027/manuscript`, with TeX Live, latexmk, Python 3, NumPy, pandas and pypdf installed:

```sh
make all
make hardware-only
make check
make overleaf
```

Full scientific QA requires repository evidence and authentic historical Git objects, not only a source ZIP. Use a full checkout; if shallow, fetch its history (`git fetch --unshallow`). Required pins include `1a11361f8526ec361e20dd6878d6e67352fb7bbd`, `575f7d3c2991bdf00915fa213a644cb9deeb0673`, `bbf0c555cc50242f85c086eac342c9deb5c2e945`, `b326ff7f20d9bac5afff6f53a6e9d9d8a7aaa7ae`, `12f387d117fb52cc0ecc688931b9925abb29e71e`, and `202109717754bc62f889d19b5fbb141bfc3cc529`. The secondary plan commit `8e7be49` and exact starting main `50050f62a44064b11948263d064aa6b1bb7a3359` are also required for scope/history QA. The Overleaf ZIP independently builds the PDFs but does not contain the full artifact audit.

From the repository root, the portable M4 archive can be independently replayed using the Python standard library:

```sh
python3 scripts/platform/m4_runtime/recompute_evidence_bundle.py artifacts/m4_runtime/runtime-profitability-control-20260925/m4_runtime_complete_evidence.tar.gz --expected-sha256 af73b8f0edeae5027357338a627d899b08db425884a1373162932a72f4f119ab
```

The independent secondary check adds 638 raw-record, endpoint, and metadata checks; seven hardware-free tests cover replay and rejected evidence mutations.

`make check` retains 228 historical comparisons, 117 prior runtime checks plus secondary gates, all 62 archive payload hashes and independent recomputation, 260 protected-file checks, 57 historical and 23 primary and six secondary runtime macros, figure replay, source/style hashes, citation/font/anonymity/layout/page gates. New scope checks distinguish historical re-tokenized text from prospective direct generated-ID agreement. The 358H compact diagnostic is pinned; unavailable local raw traces are not replayed. Hash consistency is not complete machine-state or exposure attestation.

The default asset step verifies frozen historical projections instead of regenerating their provenance ledger. The unchanged legacy `build_assets.py` is retained for historical full-history reconstruction. A wrapper runs the unchanged historical numerical validator, saves a fresh `NUMERICAL_QA_V06.json`, and restores the immutable original receipt. Current `_v05.tex` table overlays alter only approved interpretation wording; all old generated tables, numeric macros, figure artwork and data remain unchanged.

The four hardware figures retain their vector sources and native widths. Table 3 separates primary speedups, the descriptive hindsight oracle ratio, and the post-study paired secondary latency ratio. No new figure or experiment is added. `make hardware-only` is only an internal section-removal/reference test, not a standalone manuscript.

Only the two review PDFs are intended as anonymous artifacts. Internal reviews and evidence identify repository paths and commits; the whole repository and collaboration ZIP are not an anonymous artifact release. No Overleaf project is created. Author review is required; no automatic merge.

The new artifacts can be reproduced without measurement hardware:

```sh
python3 scripts/platform/m4_runtime/analyze_guard_always_secondary.py --check
python3 scripts/platform/m4_runtime/verify_guard_always_secondary.py
```

The analyzer accepts the canonical archive or its verified extracted root.
Its standalone bootstrap stream is fixed by the committed plan. The independent
verifier shares only the old hash-verifying archive extractor, with a separate
median, geometric-mean, and finite-bootstrap calculation. It writes a new v0.6
receipt and does not overwrite the primary receipt.
