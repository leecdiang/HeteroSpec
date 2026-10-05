# Current reconstruction — v0.10.0

The intervention reconstruction is reviewed on a stacked branch based on PR #53, not yet accepted main evidence. Read `../reviews/reconstruction_v010/` for exact source binding, independent raw reviews, reviewer simulation and QA.

Build current documents with `python scripts/build_v010.py`; this creates versioned main/appendix PDFs and an anonymous portable source ZIP, then independently extracts/rebuilds that ZIP. Figures: `python scripts/intervention_figures_v010.py` requires independently recomputed intervention evidence.

Historical v0.9.0 outputs, source ZIP and build scripts remain at their original repository paths. To reproduce v0.9.0, use its immutable ZIP or the original fixed commit `3a0d3c9eb1c8778141bf546b5cdd25ad1e5243e4`; historical build scripts on an edited tree do not freeze their dependencies. No old output is overwritten by the v0.10.0 build.

The author evidence packet includes private provenance; the anonymous package strips identifying metadata and uses its own content hashes. Neither is described as publicly released. No new inference, GPU experiments, timing or energy measurements were performed.

---

Final artifacts: [main PDF](output/manuscript-v0.10.0.pdf) (10 body +2 references), [appendix](output/appendix-v0.10.0.pdf) (24 pages), [portable source ZIP](output/overleaf-intervention-reconstruction-v0.10.0.zip), [anonymous evidence](output/anonymous-intervention-evidence-v0.10.0.zip), and [author evidence transport manifest](output/author-evidence-packet-v0.10.0.zip.parts/MANIFEST.json). Reassemble the same author ZIP with `python scripts/restore_author_packet_v010.py`; all part and ZIP/member hashes are checked. [Final artifact manifest](../evidence/FINAL_ARTIFACT_MANIFEST_V010.json) binds exact bytes. [Independent review and revision](../reviews/reconstruction_v010/) preserve initial/final PDF hashes and all three internal simulation reports; no acceptance probability is reported.

Run `python scripts/evidence_package_v010.py`, then unpack the anonymous evidence ZIP and run `python -B verify_v010.py` for full endpoint-bounded arrays and preserved cost arithmetic. B570 comparison is CAP128; all144 untruncated native captures are retained separately (60/63 post-cap IDs), excluded from equality. No common-prefix-only comparison is used.

The author ZIP retains large raw inventories, source/attempt bindings, handoff/sham/remote-seal records, selected complete raw captures and exact reviewer packets. Its `reviews/` directory maps to `../reviews/reconstruction_v010/`; extract those members there before reconstructing the complete author package with `python scripts/closeout_v010.py`. Raw archive/Actions artifact identities and CPU-only audit commands are in `rtx/REVIEW_REPORT.md` within that packet. It is not the full1.2GBarchive and contains no omitted weights/runtime binaries. The anonymous package makes export arithmetic inspectable; it is not full independent runtime replication.

<details>
<summary>Historical delivery notes (superseded for the current v0.10.0 manuscript)</summary>

# Manuscript build — unchanged v0.9.0 delivery; B570 integration pending

Updated 2026-10-04. The separately authorized B570 prefill diagnostic study is **COMPLETE and CLOSED**. Its [delivery](https://github.com/leecdiang/HeteroSpec/blob/196ed563b36d0e16a3cdb667b6996a4afd98da1d/benchmarks/b570_prefill_diagnostic_v1/DELIVERY_REPORT.md) and [independent review](https://github.com/leecdiang/HeteroSpec/blob/main/paper/mlsys2027/reviews/b570_prefill_review_20261004/REVIEW_REPORT.md) supersede the PREPARE_ONLY study status preserved below.

All 360 planned formal units are valid, with zero failed formal attempts. T0/N0 and sealed T1/N1 each match 72/72 complete arrays and endpoints. Native/reference agreement changes from 60/72 to 72/72; all four original diagnostic tasks recover reference output and none of the 20 controls regresses. The 24 tasks were previously exposed; three repetitions establish stability. The independent review checks 120 G0 arrays, 30 sham pairs, frozen source identities and local prediction-seal order. The [read-only CPU audit](https://github.com/leecdiang/HeteroSpec/actions/runs/37178393741) validates all 30 remote parts and 4,073 manifest files.

The new evidence supports a bounded predictor-guided prefill intervention confirmed on native execution. It strengthens the practical diagnostic contribution. Generality, omitted external asset authentication and local-only chronology remain limitations; no performance, energy, functional-pass-rate or unique-kernel result is added. Historical v0.9.0 internal ratings of 3/6 are not updated scores for the new study or acceptance probabilities.

The manuscript delivery remains **v0.9.0**, fixed content `01682f3b992a11b36b309fbd6c9e9950f1dc5d89`: 10 body + 2 reference pages and a 17-page appendix. Its TeX/PDFs/ZIPs are unchanged by this evidence review. The B570 intervention has not yet been integrated into a new manuscript. Build and artifact instructions remain in the preserved delivery documentation below.

[Integration PR #52](https://github.com/leecdiang/HeteroSpec/pull/52) targets main and includes the previously reviewed #51 ancestor plus this study, review receipts and current-status reconciliation. Resolve the actual PR/main state on GitHub; this file does not predict its own containing merge SHA. Prior draft/unmerged wording below describes its historical delivery. The scientific author-freeze remains `mlsys2027-v0.8-author-freeze`, peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`.

Next: integrate the intervention and reference-recovery chain into the contribution, results and controls of a new manuscript, then independently review that exact delivery. The original B570/RTX/358H/M4 campaigns remain CLOSED. Public release and conference submission are separate decisions.

<details>
<summary>Preserved status before B570 prefill integration</summary>

# Manuscript build and delivery — v0.9.0 reassessment

Updated 2026-10-03. The [fresh reassessment](../reviews/acceptance_reassessment_v090/ACCEPTANCE_REASSESSMENT_V090.md) supersedes the review status in the preserved history below. The manuscript remains v0.9.0.

Two new reviewers independently recommend **3/6 weak reject, confidence 4/5**. Both read all 12 main and 17 appendix text pages, inspect selected renders, and directly check retained arrays and costs. Their arithmetic agrees with the bounded claims; neither identifies a new material defect in the checked results. The remaining blocker is demonstrated systems significance: the simpler reproducer has not yet guided a discriminating intervention confirmed on native execution. These are internal simulated judgments, not acceptance probabilities. Historical v0.8.9 scores (3/6 and 4/6) are different reviewers' assessments of a different packet; there is no score evidence of improvement.

The [B570 diagnostic study plan](../reviews/acceptance_reassessment_v090/DIAGNOSTIC_STUDY_PREPARE_ONLY.md) is **PREPARE_ONLY, not execution-ready or executed**. It proposes one target-prefill intervention on the four known divergent cases plus 20 regression controls, after new baseline, sham-transfer, state and instrumentation qualification. Five conditions with three repetitions would yield 360 planned complete arrays; these are not new observations. The [source check](../reviews/acceptance_reassessment_v090/PREPARE_SOURCE_AUDIT.json) establishes caller-level facts only, not a prefill cause. Original B570/RTX/358H/M4 campaigns remain CLOSED.

Frozen delivery: [main PDF](../manuscript/output/manuscript-v0.9.0.pdf), 10 body + 2 reference pages; [appendix](../manuscript/output/appendix-v0.9.0.pdf), 17 pages; [document source](../manuscript/output/overleaf-diagnostic-revision-v0.9.0.zip); [anonymous scientific package](../manuscript/output/anonymous-evidence-index-v0.9.0.zip). All four are byte-identical to content commit `01682f3b992a11b36b309fbd6c9e9950f1dc5d89`. The [artifact manifest](../evidence/FINAL_ARTIFACT_MANIFEST_V090.json) retains its original identity. No TeX build, historical verifier/bootstrap, model or GPU ran in this review round; earlier build and whole-page QA remain historical receipts for the same hashes.

New [systems review](../reviews/acceptance_reassessment_v090/SYSTEMS_ACCEPTANCE_REVIEW.md), [evidence review](../reviews/acceptance_reassessment_v090/EVIDENCE_ACCEPTANCE_REVIEW.md), and [coverage/consistency QA](../reviews/acceptance_reassessment_v090/REVIEW_COVERAGE_QA.json) retain their individual judgments and limits. Only six living status files and new review/plan files change. Original scientific records, manuscript sources/PDFs/ZIPs, prior reviews, and scripts remain unchanged. Existing Draft PR #51 stays open and unmerged; no release or conference submission. Base/main stays `87b811e21a164468232cfea3c2404a1ebc869477`; author-freeze tag remains object `a3e33d405a53b8ee9fe4018d166b651001daa305`, peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`.

<details>
<summary>Preserved v0.9.0 diagnostic revision status and earlier history</summary>

# Manuscript build and delivery — v0.9.0

Updated 2026-10-03. This status supersedes the preserved history below. Read the [revision response](../reviews/diagnostic_revision_v090/REVISION_RESPONSE_V090.md) for the implemented acceptance-reassessment requests and their limits.

v0.9.0 explains the tested B570/RTX reproduction tasks, adds complete-trajectory failure extents, and aligns the 358H optimization budget with the original prompt estimator. It quantifies M4 opportunity between two measured fixed modes and carries those conclusions through the whole paper. All analyses use retained records after outcomes were known. Original observations, primary GM/CI/seeds and all historical artifacts remain unchanged.

Current files: [main PDF](../manuscript/output/manuscript-v0.9.0.pdf) (10 body + 2 reference pages), [separate appendix](../manuscript/output/appendix-v0.9.0.pdf) (17 pages), [portable document source](../manuscript/output/overleaf-diagnostic-revision-v0.9.0.zip), and [anonymous scientific package](../manuscript/output/anonymous-evidence-index-v0.9.0.zip). The new scientific package retains every v0.8.8 member byte-identically and adds the new diagnostic calculator/data. The hardware-only PDF is an internal section-removal proof, not a submission artifact. [Manifest](../evidence/FINAL_ARTIFACT_MANIFEST_V090.json) and [revision QA](../evidence/REVISION_V090_QA.json) bind the files and checks.

Two clean source-ZIP builds agree on exact raw per-page text. Final 40-page visual coverage comprises 26 manually inspected final pages and 14 exact pixel matches to manually inspected pages from the current revision's first candidate. Fonts, citations, anonymity and page limits pass. The new diagnostic calculator passes twice in clean extractions. Historical verifier/bootstrap suites are not rerun; 319 protected files and all 30 historical scientific ZIP members retain their original bytes.

The [fixed v0.8.9 reassessment](../reviews/acceptance_reassessment_v089/ACCEPTANCE_REASSESSMENT_V089.md) remains historical: systems 3/6 weak reject, evidence 4/6 weak accept. These are not v0.9.0 scores or acceptance probabilities. Concrete reproduction inputs and conditional budgets are now clearer; no actual bug fix or measured debugging saving is demonstrated. Main-track significance remains open to a fresh assessment. No further B570 experiment is needed for the current finite claims.

Existing [Draft PR #51](https://github.com/leecdiang/HeteroSpec/pull/51) keeps branch `paper/mlsys2027-rtx-integration-v0.8.7`. Revision parent is `c39461230f34554151dcfddafffb41ab938517dd`; main remains `87b811e21a164468232cfea3c2404a1ebc869477`. The author-freeze tag remains peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`. **B570/RTX/358H/M4 remain CLOSED.** This revision authorizes no new model/hardware experiment, merge, release or conference submission.

From the repository root, compile with `make -C paper/mlsys2027/manuscript all` and check with `make -C paper/mlsys2027/manuscript check`. The build packages the current portable sources, compiles two independent fresh ZIP extractions and the internal proof, and checks raw page text equality. It does not run hardware/model inference. A newly compiled PDF needs a matching visual receipt before the manual-QA gate passes. `make overleaf` in this directory rebuilds the document source ZIP only. For new scientific arithmetic, unpack the v0.9.0 anonymous scientific ZIP and run `python3 -B verify_v090.py`; its unchanged `verify.py` belongs to the historical full suite and was not rerun in this revision.

<details>
<summary>Preserved v0.8.9 status and earlier history</summary>

# Readme — v0.8.9 review closeout

Updated 2026-10-03. This current status supersedes all historical wording below. [Final review](../reviews/system_revision_v089/FINAL_REVIEW_V089.md) records the complete request mapping and remaining significance concern.

v0.8.9 completes the missed A6 prospective-path endpoint wording and the A9 Section Q entry. The scientific prose, observations, primary estimates and [v0.8.8 global system analysis](../reviews/system_revision_v088/GLOBAL_SYSTEM_READOUT_V088.md) remain unchanged. Assessment: **Share with caveats**; finite claims are supported, while main-track significance remains an author judgment. This is an author closeout, not a fresh committee vote.

Current artifacts: [main PDF](output/manuscript-v0.8.9.pdf) (10 body + 2 references), [separate appendix](output/appendix-v0.8.9.pdf) (16 pages), [document source ZIP](output/overleaf-system-revision-v0.8.9.zip), and unchanged [anonymous scientific evidence v0.8.8](output/anonymous-evidence-index-v0.8.8.zip). The internal hardware-only proof is not a submission artifact. [Manifest](../evidence/FINAL_ARTIFACT_MANIFEST_V089.json) and [delivery identity](../evidence/DELIVERY_V089.md) bind the final files.

Two clean ZIP builds pass with exact raw per-page text equality. Three changed appendix pages were manually checked; the other 36 pages exactly match previously inspected pixels. Scientific CPU/data verification receipts are reused after hash verification, not described as new executions. [Closeout QA](../evidence/REVIEW_CLOSEOUT_V089_QA.json) records the scope.

The [official 2027 format check](../reviews/system_revision_v089/VENUE_PRECHECK_20261003.md) confirms 2025 style and the 10-page body limit. Style/bst bytes stay fixed. The CFP and homepage disagree by one hour on the deadline; the note preserves both times pending OpenReview confirmation.

Existing [Draft PR #51](https://github.com/leecdiang/HeteroSpec/pull/51) retains branch `paper/mlsys2027-rtx-integration-v0.8.7`. Parent is `4a4854575dcd1f652975bb008ceccbae0300d6c2`; main is `87b811e21a164468232cfea3c2404a1ebc869477`. The author-freeze tag remains peeled to `1d3b556c93b477680788dfd1eb0737dfe9eee28c`. **B570/RTX/358H/M4 remain CLOSED.** No model execution, merge, release or conference submission is authorized by this closeout.

Run from this manuscript directory:

```sh
python3 -B scripts/build_v089.py
python3 -B ../scripts/validate_closeout_v089.py
python3 -B scripts/qa_pdf_v089.py
```

For a portable document build, extract the v0.8.9 source ZIP into a fresh directory and run `latexmk -pdf main.tex`, then `latexmk -pdf appendix.tex`. The package builds documents without models. `make check` expects the final hash-bound visual receipt; a changed rendering needs renewed inspection before delivery.

<details>
<summary>Preserved v0.8.8 status and earlier history</summary>

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

</details>

</details>

</details>

</details>

</details>
