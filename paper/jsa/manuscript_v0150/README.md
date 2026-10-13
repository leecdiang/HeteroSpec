# Phase-Scoped Query Layouts for Reference-Preserving Speculative Decoding

**Version 0.15.2, author-review revision, 13 October 2026.** The title, main method and five main figures are retained. This revision builds on PR102 at `2dce88ea37194beb1b4b09f139e5bc48000af3ba`. The directory name remains stable for existing links. It is not a journal submission or an approval of the pending author declarations.

## Reading and delivery

- `output/main.pdf`: 11-page article with explicit pointers to the supplementary figures and completed bibliographic fields.
- `output/supplement.pdf`: 11-page supplement with evidence contracts, all reported comparisons, two new task-level figures, causal boundaries and the historical ledger.
- `output/figures/`: seven separately numbered vector PDFs, five main and two supplementary; editable sources remain in `figures/`.
- `output/JSA_v0152_author_package.zip`: complete review package, including sources, figure PDFs, data, checks, manuscript PDFs and author worksheets.
- `output/JSA_v0152_flat_sources.zip`: source files with no subdirectories, compiled after extraction for Elsevier Editorial Manager preparation.
- `Highlights.txt`, `Figure_captions.tex`, `Supplement_figure_captions.tex`, `Title_page.txt`: editable submission support files.
- `JSA_REQUIREMENTS_20261013.md` and `AUTHOR_CHECKLIST.md`: recovered journal rules, verified publisher guidance and remaining author decisions.

Build outputs and ZIPs are generated locally, not committed. The final package's exact file hashes are in `output/FINAL_MANIFEST.json`.

## Why two supplementary figures

The main figures already cover graph design, fixed-input correspondence, aggregate cost, partition classes and retained-state interventions. Another main figure or B570 pipeline would largely repeat those results; a pipeline could also suggest an unproved causal chain. The added figures instead expose task variation hidden by the aggregates:

- Figure S1 aligns the same 12 tasks across three families and compares repair cost with the separate draft decision. It plots 72 ratios, including every regression. SmolLM2's cheaper repair and unprofitable draft are visible on every task.
- Figure S2 shows both adjacent sessions for each task in target-only and speculative execution: 72 pairs, 144 points. Qwen3 and Llama target-only reversals are visible alongside Llama's speculative task-level exceptions.

Both use the existing palette and typography, fixed task ordering, explicit ratio directions, parity lines and redundant point shapes. Figure S1 uses a shared logarithmic ratio axis; Figure S2 uses a shared linear axis. Neither includes fitted relationships, fabricated uncertainty, pooled campaigns or new measurements. The near-parity Llama GSM8K141 regression remains at full coordinate precision and is identified at six decimals in the caption.

The generator derives all supplementary coordinates directly from the pinned report's arm medians. A separate checker recomputes them without importing the generator, verifies the actual plotted coordinates and connecting segments, and checks shared denominators, task qualification, axis coverage and regression directions. See `provenance/SUPPLEMENT_FIGURE_CHECKS_V0152.json`. PDF checks and final author-side review are recorded in `provenance/FINAL_QA_V0152.json` and `provenance/FINAL_REVIEW_V0152.json`.

The v0.15.1 scientific corrections remain: PR93/PR97 direct evidence citations, the S6 historical-endpoint pointer, aggregate session reversals, Stage-Replay's prior cache-transplantation controls, and the partition/projection/state boundary. The 186 reported-value checks and the prior independent recomputation of 21 aggregate, 42 session and 252 task ratios remain applicable. No GPU experiment, native timing-record audit or complete 675 MB raw-archive reconstruction was performed.

## Recovered JSA guide

The repository had preserved a complete verification of the author's 9 October 2026 official 18-page guide print. The original PDF was not committed. Its two audit records are copied byte-for-byte into `provenance/`, with original paths, commit/blob identities and hashes documented in the current requirements audit. Their old v0.13.0 manuscript checks are historical; the journal rules are applied to this draft.

The saved guide permits two-column LaTeX, sets a 250-word abstract limit and 1–7 keywords, and does not state a body page ceiling. The current 217-word abstract, five keywords and four highlights fit those recorded rules. All tables now have explicit numbered prose references. Preprint DOIs, the actual web-access date and qualified software-build identifiers are supplied. Live guide access on 13 October remained blocked, so changes after the snapshot and actual Editorial Manager upload fields still require a final check.

Funding, competing interests, CRediT roles, the declarations-tool document, author biography/photo, historical AI details, final human review and an Option C data-access arrangement remain pending. `Author_declarations_pending.txt` is a worksheet, not a completed declaration. Chengzhan Li remains the sole and corresponding author with the UESTC Qingshuihe address. No mentor is added based on a possible future conversation.

## Build and package

Use Python 3.10+ and a TeX distribution with pdfLaTeX, BibTeX, `elsarticle`, TikZ/PGFPlots, `microtype`, `booktabs`, `tabularx`, `longtable`, `enumitem`, `xurl`, `flushend`, `preview` and standard Times-compatible fonts. PDF QA also needs `pdfplumber` and Poppler (`pdffonts`).

```sh
python3 scripts/check_reported_data.py
python3 scripts/generate_supplement_figures.py --check
python3 scripts/check_supplement_figures.py
python3 scripts/build.py
python3 scripts/export_figures.py
python3 scripts/qa_final.py
python3 scripts/package_submission.py
```

To regenerate the supplementary TikZ sources from the fixed medians, run the generator without `--check`. The source package helper builds both documents from the extracted flat ZIP in a clean temporary directory. No GPU, network or shell escape is required. On Overleaf, choose `main.tex` or `supplement.tex` with pdfLaTeX. The existing renamed `psql-num.bst` derivative retains numbered, first-citation-order references and linked titles; the saved JSA guide allows consistent initial-submission reference formatting.

## Historical records

The original `GITHUB_IMPORT.json`, `PACKAGE_MANIFEST.json`, `RECONSTRUCTION_REVIEW_ZH.md`, `provenance/RECONSTRUCTION_QA.json`, `provenance/PDF_CHECKS.json` and original font reports describe the v0.15.0 import/build only. The v0.15.1 QA/review files describe that earlier revision. They are retained as history, not current-file integrity certificates. Use the v0.15.2 QA and final manifest for this revision. Experiment records and earlier manuscript directories are unchanged.
