# Manuscript build — v0.8.8

Title: **Predicting Execution Paths and Bounding Optimization in Speculative Decoding**.

The existing Draft PR #51 now carries an author revision based on v0.8.7. Prior review scores remain bound to old artifacts. [Current handover](../HANDOVER_CURRENT.md), [global readout](../reviews/system_revision_v088/GLOBAL_SYSTEM_READOUT_V088.md), [review response](../reviews/system_revision_v088/REVIEW_RESPONSE_V088.md) and [delivery](../evidence/DELIVERY_V088.md) state the current scope.

## Portable document build

Use `output/overleaf-system-revision-v0.8.8.zip`. Extract into a clean directory and run:

```sh
latexmk -pdf main.tex
latexmk -pdf appendix.tex
```

The ZIP contains all TeX/figure/bibliography/style dependencies and SHA256SUMS.json; it does not execute models. The official vendored 2025 style remains unchanged; use of it is not a certification of unpublished 2027 rules. The main body keeps the existing ten-page repository target.

## Repository checks

From the repository root:

```sh
python3 -B paper/mlsys2027/scripts/analyze_global_v088.py
python3 -B paper/mlsys2027/scripts/crosscheck_global_v088.py
python3 -B paper/mlsys2027/scripts/prepare_global_v088.py
python3 -B paper/mlsys2027/manuscript/scripts/build_v088.py
python3 -B paper/mlsys2027/scripts/validate_revision_v088.py
```

The new calculation is post-study with known outcomes; it preserves primary GM/CI/seed and blocked nulls. Build uses two new source-ZIP extractions and compares raw page text exactly. PDF completeness is checked before acceptance; any incomplete intermediate output is rejected, with at most one logged exact-command rerun. Automated PDF checks do not replace final page inspection. `VISUAL_QA_V088.json` binds actual inspected PDF hashes.

## Evidence and outputs

Extract `output/anonymous-evidence-index-v0.8.8.zip` into a clean directory and run `python3 -B verify.py`. This standard-library verifier preserves previous numerical inputs/verifiers and adds 19-prompt latency descriptors and candidate cross failures. Full raw-capsule identities remain in INDEX.json; compact state checks are not raw KV/sampler bytes and cannot prove original absolute chronology or omitted assets.

Outputs: `manuscript-v0.8.8.pdf`, `appendix-v0.8.8.pdf`, `overleaf-system-revision-v0.8.8.zip`, `anonymous-evidence-index-v0.8.8.zip`. `hardware-only-v0.8.8.pdf` is internal only. Final hashes/pages/source mapping are in [FINAL_ARTIFACT_MANIFEST_V088.json](../evidence/FINAL_ARTIFACT_MANIFEST_V088.json). Older artifacts, scripts, arrays, macros and Figure 3 source/asset/geometry are preserved. No new inference, merge, release or submission.

<details>
<summary>Historical v0.8.7 living-pointer text, retained as history; not current instructions</summary>

# Manuscript v0.8.7 — RTX evidence integration candidate

This branch is based on main `87b811e21a164468232cfea3c2404a1ebc869477`; v0.8.7 is pending merge. Read [the current handover](../HANDOVER_CURRENT.md) and [exact manifest](../evidence/FINAL_ARTIFACT_MANIFEST_V087.json). Prior v0.8.6 artifacts and receipts retain their original identities.

## Delivered artifacts

Main is **10 body + 2 reference pages**; the separate appendix is **14 pages**. The 9+2-page hardware-only proof removes the runtime section for an internal check while retaining full-paper summaries; it is not a submission manuscript.

- `output/manuscript-v0.8.7.pdf`
- `output/appendix-v0.8.7.pdf`
- `output/hardware-only-v0.8.7.pdf`
- `output/overleaf-rtx-integration-v0.8.7.zip`
- `output/anonymous-evidence-index-v0.8.7.zip`

The original B570 prospective prediction remains central. New Tables 3–4 and Appendix Q integrate same-set RTX candidate comparison and matched qualification–cost, without pooling older cohorts or converting blocked timing into speedup.

## Build and verification

Prerequisites: Python 3.11+, pypdf, numpy, PyMuPDF, pdfLaTeX, BibTeX, latexmk and Poppler. No models or GPU runtime are needed. From the repository root, these entries were actually executed for this delivery:

```sh
python3 -B paper/mlsys2027/scripts/prepare_evidence_v087.py
python3 -B paper/mlsys2027/manuscript/scripts/build_v087.py --qa-root /path/to/new-build-directory
python3 -B paper/mlsys2027/manuscript/scripts/qa_pdf_v087.py --build /path/to/new-build-directory/fresh
python3 -B paper/mlsys2027/scripts/validate_integration_v087.py
```

Use a new build directory for another build. Makefile defaults now invoke v087 build/check/package entries. `make all` creates both clean extractions and runs automated QA; `make check` validates the evidence and logs from the build directory recorded in its receipt. This delivery ran the explicit entries above and `make check`; it does not claim that the new `make all` target itself was separately executed. Fresh builds can change PDF metadata and bytes; identify each new artifact before reviewing it.

Both independent source-ZIP extractions regenerate all aux/bibliography files and build main, appendix and internal proof. Raw extracted page text must match exactly without normalization. Final explicit TeX passes resolve cross-references after latexmk. Source-to-ZIP byte transformations, complete bibliography authors, embedded fonts, anonymous PDF text/metadata/actions, logs and page limits are checked. Separate final-hash-bound visual QA records all 37 pages.

For a minimal source reproduction, extract the ZIP into an empty directory and run `latexmk -pdf main.tex` and `latexmk -pdf appendix.tex`, then rerun TeX if a log reports unresolved references. The compact evidence package needs only Python stdlib: extract into an empty directory and run `python3 -B verify.py`. It recomputes original studies and post-study descriptors from preserved inputs, then the new V4 trajectory/timer projection. Two independent clean executions were performed; ten invalid-evidence cases were rejected.

The anonymous index is a known-outcome projection, not a prospective freeze or a new experiment. Its INDEX identifies unchanged full H2 and V4 anonymous capsules by exact name/length/hash. Native absolute timer endpoints are omitted from the compact export; recorded intervals and frequencies remain exact, and the raw author capsules retain endpoints. Internal reviews and author paths are absent from both ZIPs.

## Audit scope and limits

Figure 3's 71 checks were rerun. The prior [RTX V4 independent native-log audit](../evidence/RTX_V4_INDEPENDENT_RAW_CLOSEOUT_20261002.md) already verified nine sealed capsules, all 228 native live/timed arrays and raw QPC-to-statistic calculations on CPU. That receipt is reused, not relabeled as a new nine-capsule replay here. Historical v086 archive/numeric/runtime/secondary receipts remain historical; current QA does not claim their entire suites were freshly rerun.

No GPU/model forward occurred in v087 integration. Scientific arrays, old macros, Figure 3, vendor style and prior artifacts stay unchanged. Exact old v084 sequence ZIP and 358H runtime raw traces remain unavailable. Offline hashes and ordinal mappings do not authenticate original absolute time, exposure completeness or omitted weights/runtime/compiler/driver. Build success is separate from [submission-level review](../reviews/submission_v087/).

</details>
