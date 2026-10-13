# Phase-Scoped Query Layouts for Reference-Preserving Speculative Decoding

**Version 0.15.3, author-review revision, 13 October 2026.** The title, main method and five main figures are retained. This revision builds on PR102 at `e22c3565366094baa2980594b42223e57565455f`. The directory name remains stable for existing links. It is not a journal submission or an approval of the pending author declarations.

## Reading and delivery

- `output/main.pdf`: 12-page article with explicit pointers to the supplementary figures and completed bibliographic fields.
- `output/supplement.pdf`: 11-page supplement with evidence contracts, all reported comparisons, two task-level figures, causal boundaries and the historical ledger.
- `output/figures/`: seven separately numbered vector PDFs, five main and two supplementary; editable sources remain in `figures/`.
- `output/JSA_v0153_author_package.zip`: complete review package, including sources, figure PDFs, data, checks, manuscript PDFs and author worksheets.
- `output/JSA_v0153_flat_sources.zip`: source files with no subdirectories, compiled after extraction for Elsevier Editorial Manager preparation.
- `Highlights.txt`, `Figure_captions.tex`, `Supplement_figure_captions.tex`, `Title_page.txt`: editable submission support files.
- `REFERENCE_AUDIT_20261013.md`: source-linked audit of every existing reference and the missing-work search.
- `JSA_REQUIREMENTS_20261013.md` and `AUTHOR_CHECKLIST.md`: recovered journal rules, verified publisher guidance and remaining author decisions.

Build outputs and ZIPs are generated locally, not committed. The final package's exact file hashes are in `output/FINAL_MANIFEST.json`.

## JSA first-submission access preparation

The author selected JSA as the first target and confirmed that this preparation should retain a single author. The scientific article and its PDFs remain v0.15.3. `SUBMISSION_CONFIRMATIONS_ZH.txt` collects the remaining author facts in seven reply fields; it does not repeat the coauthor decision or fill unknown declarations with “none”.

`REVIEW_ACCESS_PLAN_ZH.txt` describes the proposed reviewer route. Two local packages are prepared: `output/JSA_v0153_review_core.zip` for offline report/figure review and `output/JSA_v0153_native_source.zip` for inspection of the fixed CUDA native source. The core includes source reports retrieved at their cited commits, rather than requiring a reviewer to open the private GitHub links. The native source is extracted from the hash-verified PR98 V02 capsule with upstream notices preserved. Model acquisition information is in `review_access/MODEL_ACCESS.json`; all eight named GGUF files match the pinned publisher metadata by size and SHA256. No model weights were downloaded.

See `review_access/ACCESS_STATUS.json` for the exact package hashes, coverage and uncompleted work. Raw archive parts remain separately inventoried; these packages do not constitute a complete native-record restoration or GPU reproduction. `review_access/DATA_AVAILABILITY_DRAFT.txt` and `DEPOSIT_METADATA_DRAFT.json` are author worksheets, not claims that a deposit exists. No live reviewer link or DOI has been created, no repository has been made public, and project sharing rights/licenses remain to be confirmed. Original manuscript availability language is unchanged pending a real deposit.

The new access preparation does not supersede the earlier scientific/PDF QA; it changes support materials only. The author package can be regenerated to include this preparation. Historical delivery manifests and reviews describe their original package versions, not the expanded package's current file count or hash.

## Layout and reference finalization

The seven-row supplementary comparison matrix preserves all 21 ratios and regression counts. Removing the S4 float barrier and the forced one-column ledger transition eliminates the large unused column areas on pages 5 and 9. Both historical ledgers remain full-width, complete tables. Figure S2 names its Section S4 provenance even when it floats into the following section. Fonts and plotted values are unchanged.

The fresh audit covers all 22 prior bibliography entries, including the unused Qwen3 library entry. LLM-42 now uses its verified SOSP 2026 publication; the MLSys paper has complete pages. PR91 and PR94 have distinct direct citations, and source-account attributions replace unsupported personal-name attribution for the audits and historical ledger. Full URLs and access dates are displayed for web/software/companion sources. Complete author lists remain in the bibliography source with consistent six-name abbreviation in print.

Five relevant papers and a primary Vulkan diagnostic report are added with specific methodological comparisons. The same-project early public report is identified by a matching frozen-prediction SHA256 and cited as historical work, not independent replication. The resulting library has 30 entries; the article prints 26 and the supplement 14. The only unused library entry is Qwen3. See `provenance/REFERENCE_AUDIT_V0153.json` for versions, formal publication status, checked primary sources, unresolved access limits and omitted candidates. `provenance/REFERENCE_CHECKS_V0153.json` checks citation coverage and actual PDF hyperlinks, not literature completeness.

## Why two supplementary figures

The main figures already cover graph design, fixed-input correspondence, aggregate cost, partition classes and retained-state interventions. Another main figure or B570 pipeline would largely repeat those results; a pipeline could also suggest an unproved causal chain. The added figures instead expose task variation hidden by the aggregates:

- Figure S1 aligns the same 12 tasks across three families and compares repair cost with the separate draft decision. It plots 72 ratios, including every regression. SmolLM2's cheaper repair and unprofitable draft are visible on every task.
- Figure S2 shows both adjacent sessions for each task in target-only and speculative execution: 72 pairs, 144 points. Qwen3 and Llama target-only reversals are visible alongside Llama's speculative task-level exceptions.

Both use the existing palette and typography, fixed task ordering, explicit ratio directions, parity lines and redundant point shapes. Figure S1 uses a shared logarithmic ratio axis; Figure S2 uses a shared linear axis. Neither includes fitted relationships, fabricated uncertainty, pooled campaigns or new measurements. The near-parity Llama GSM8K141 regression remains at full coordinate precision and is identified at six decimals in the caption.

The generator derives all supplementary coordinates directly from the pinned report's arm medians. A separate checker recomputes them without importing the generator, verifies the actual plotted coordinates and connecting segments, and checks shared denominators, task qualification, axis coverage and regression directions. See `provenance/SUPPLEMENT_FIGURE_CHECKS_V0153.json`. PDF checks and final author-side review are recorded in `provenance/FINAL_QA_V0153.json` and `provenance/FINAL_REVIEW_V0153.json`.

The v0.15.1 scientific corrections remain: PR93/PR97 direct evidence citations, the S6 historical-endpoint pointer, aggregate session reversals, Stage-Replay's prior cache-transplantation controls, and the partition/projection/state boundary. The 186 reported-value checks and the prior independent recomputation of 21 aggregate, 42 session and 252 task ratios remain applicable. No GPU experiment, native timing-record audit or complete 675 MB raw-archive reconstruction was performed.

## Recovered JSA guide

The repository had preserved a complete verification of the author's 9 October 2026 official 18-page guide print. The original PDF was not committed. Its two audit records are copied byte-for-byte into `provenance/`, with original paths, commit/blob identities and hashes documented in the current requirements audit. Their old v0.13.0 manuscript checks are historical; the journal rules are applied to this draft.

The saved guide permits two-column LaTeX, sets a 250-word abstract limit and 1–7 keywords, and does not state a body page ceiling. The current 217-word abstract, five keywords and four highlights fit those recorded rules. All tables now have explicit numbered prose references. Preprint DOIs, the actual web-access date and qualified software-build identifiers are supplied. Live guide access on 13 October remained blocked, so changes after the snapshot and actual Editorial Manager upload fields still require a final check.

Funding, competing interests, CRediT roles, the declarations-tool document, author biography/photo, historical AI details, final human review and an Option C data-access arrangement remain pending. `Author_declarations_pending.txt` is a worksheet, not a completed declaration. Chengzhan Li remains the sole and corresponding author with the UESTC Qingshuihe address. No mentor is added based on a possible future conversation.

## Build and package

Use Python 3.10+ and a TeX distribution with pdfLaTeX, BibTeX, `elsarticle`, TikZ/PGFPlots, `microtype`, `booktabs`, `tabularx`, `longtable`, `enumitem`, `xurl`, `flushend`, `preview` and standard Times-compatible fonts. PDF and reference QA also need `pdfplumber`, `pypdf` and Poppler (`pdffonts`).

```sh
python3 scripts/check_reported_data.py
python3 scripts/generate_supplement_figures.py --check
python3 scripts/check_supplement_figures.py
python3 scripts/build.py
python3 scripts/export_figures.py
python3 scripts/qa_final.py
python3 scripts/check_references.py
python3 scripts/package_submission.py
```

To regenerate the supplementary TikZ sources from the fixed medians, run the generator without `--check`. The source package helper builds both documents from the extracted flat ZIP in a clean temporary directory. No GPU, network or shell escape is required. On Overleaf, choose `main.tex` or `supplement.tex` with pdfLaTeX. The renamed `psql-num.bst` derivative retains numbered references in first-citation order and linked titles, displays complete web URLs/access dates, and abbreviates lists longer than six authors; the saved JSA guide allows consistent initial-submission reference formatting.

## Historical records

The original `GITHUB_IMPORT.json`, `PACKAGE_MANIFEST.json`, `RECONSTRUCTION_REVIEW_ZH.md`, `provenance/RECONSTRUCTION_QA.json`, `provenance/PDF_CHECKS.json` and original font reports describe the v0.15.0 import/build only. The v0.15.1 and v0.15.2 QA/review files describe those earlier revisions. The narrower v0.15.2 bibliography recheck is superseded by the comprehensive v0.15.3 source audit. They are retained as history, not current-file integrity certificates. Use the v0.15.3 QA and final manifest for this revision. Experiment records and earlier manuscript directories are unchanged.
