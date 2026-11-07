# HeteroSpec: JSA structural manuscript v0.13.0

Author-review draft. Not submitted, merged, or a new experiment campaign.

**Title:** Execution State and Cost Boundaries of Reference-Preserving Speculative Decoding

Base: `f3fd2aecc6288c661033ee83d5216db6481dac3f` (main after PR #68). Historical manuscripts and experimental artifacts remain unchanged.

## Argument and structure

The manuscript follows three linked system decisions: distinguish retained state from the current execution path; qualify a finite repair against the registered output contract; evaluate ordinary-reference deployment gain and matched-target incremental gain. Earlier prediction, bridge, and offline-selection studies establish why reproduction alone does not justify added machinery. The positive RTX case is followed by qualified width/B570 cost failures and historical M4/358H opportunities and limits.

The body contains runtime architecture and related work, execution/measurement contracts, evidence roles and exposure, diagnosis, finite repair, paid costs and workload boundaries, design implications, threats, and conclusion. The supplement retains the detailed late-study inventory. This is a substantive restructuring with additional use of saved historical experiments, not an increase in experimentally demonstrated portability.

## Files and reproduction

- `main.tex`: manuscript; `appendix.tex`: separate supplement.
- `output/jsa-manuscript-v0.13.0.pdf`: 24-page single-column review manuscript.
- `output/jsa-supplement-v0.13.0.pdf`: 8-page supplement.
- `output/overleaf-jsa-v0.13.0.zip`: self-contained author source bundle. Set Overleaf main document to `main.tex`; select `appendix.tex` to build the supplement.
- `CLAIM_EVIDENCE_MAP.md`: claim, evidence, estimator, and inference boundaries.
- `JSA_RECONSTRUCTION_REVIEW.zh-CN.md`: Chinese author-side review and next work.
- `RECONSTRUCTION_BINDINGS.json`: 16 byte-exact historical source bindings.
- `evidence/`: 26 preserved late-study exports, including inherited source bindings.
- `historical_sources/`: frozen source extracts, not new raw data.
- `build.py`: new CPU-only verifier and packager; `frozen_verifier.py`: inherited late verifier, used only for verification.

Use Python 3 with packages in `requirements.txt`, TeX Live with `latexmk`, `pdflatex`, `bibtex`, and Poppler (`pdfinfo`, `pdftotext`, `pdffonts`). Run:

```sh
python3 build.py
```

No inference, hardware campaign, warmup, or figure regeneration occurs. Public RTX task medians, qualification joins, ratio identities, selected width/workload summaries, M4 summaries/oracle, and B570 costs are recomputed. Historical extracts are checked against Git blob identities. Saved aggregates whose raw archives are omitted remain inherited evidence, not independently rerun results. `BUILD_QA.json` states these limits.

The 24-page count uses Elsevier's 12-point single-column preprint template and includes references/declarations; it cannot be compared directly with the prior six-page two-column format. Text extraction reports approximately 7,188 words, including captions, references, and declarations. There is no asserted JSA page-limit compliance.

## Submission preparation

Official JSA scope and Elsevier LaTeX/AI guidance were consulted; JSA's dedicated Guide for Authors returned an access error. `JSA_REQUIREMENTS_AND_DEPENDENCIES.json` records exact sources and uncertainty. This draft uses the official downloadable Elsevier class, numbered references, a 161-word abstract, and six keywords. These are conservative author-draft choices, not a completed journal checklist.

Pending author work: real title-page information and affiliations, funding/conflict statements, persistent data access and raw-material decision, human verification of all claims/references, final AI declaration, JSA-specific submission instructions, and later figure refinement. `HIGHLIGHTS.txt` is an optional candidate; whether JSA requires it remains to be checked. The Overleaf folder bundle is a working source package. Elsevier Editorial Manager may require flattening files into one source folder; this bundle is not advertised as a ready-to-upload EM submission archive.

## Visual scope

The three inherited figure PDFs are unchanged. Basic fitting, fonts, references, table legibility, and page rendering are checked; a dedicated visual optimization phase is deferred as requested.
