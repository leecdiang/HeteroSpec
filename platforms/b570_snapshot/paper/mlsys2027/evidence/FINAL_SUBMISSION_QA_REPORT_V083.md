# v0.8.3 Final Submission QA

## Source

Release artifacts were built from clean detached source commit `c474c5dd92bee654c2cc2b7e4d4299037d7bf449`. Scientific manuscript source and closed evidence were unchanged. PDF Subject metadata and the corresponding source-ZIP TeX metadata were updated from v0.8.2 to v0.8.3 as release preparation only; page text and rendered pixels were identical before and after.

## Builds

Clean main, appendix, and hardware-only builds passed. A second clean source build had identical extracted text, page counts, and rendered pixels; only PDF metadata/timestamps differed, so reproducibility is **CONTENT-REPRODUCIBLE**. The 41-file source ZIP passed its manifest and privacy audit. Independent extraction and rebuild of main and appendix matched the formal PDFs in page count, extracted text, and rendered pixels.

## Artifact hashes

| Artifact | SHA-256 |
|---|---|
| `manuscript-v0.8.3.pdf` | `75b8da875f75a6836ec4a0bb1a87e5dd8edacb66dbac2c1a5ef4857e5664cbaa` |
| `appendix-v0.8.3.pdf` | `c32a2d3c8b24b44aa1835fc94da82a4298b40c3ec8b0cf6cbd66f9a373ebc510` |
| `hardware-only-v0.8.3.pdf` (internal proof) | `9d7c5b8e3341f0c5da45b7467f505940cab7a904f435c3e23ab438b8b623b95e` |
| `overleaf-submission-readiness-v0.8.3.zip` | `194dad670b4ef9cbc1ecf48c9f20e735c499fd473f049317fbd000038c4f356f` |

## Page budget

Main manuscript: 10 body pages plus 2 reference pages, 12 total. Appendix: 8 pages. Hardware-only proof: 11 pages. All 20 submission-PDF pages were visually inspected.

## Anonymity

**PASS.** Final manuscript and appendix text, raw PDF bytes, metadata, and source-ZIP paths/content were checked for author identity, repository/user paths, hostnames, Git URLs/identifiers, and institutional identification. PDF Author metadata is `Anonymous Authors`. The 24-row B570 ledger and timeline showed no private provenance.

## Fonts

**PASS.** All manuscript and appendix fonts are embedded, with no missing or substituted fonts and zero Type 3 fonts. The inventory is recorded in `FINAL_ARTIFACT_MANIFEST_V083.json`.

## Scientific regression

**PASS.** Prior-phase, Phase-6, Figure-3, and current scientific-invariant validators passed. The frozen RTX, B570, M4, and 358H results remained intact. Historical text-path agreement, fresh direct-ID qualification, B570 predictor-to-live 72/72, and blocked reference-to-live 60/72 remained separate. No new experiment or inference was performed. All three build logs had zero unresolved references/citations and zero overfull boxes.

## Figures/tables

**PASS.** Figures 1–4, Table 1, the B570 timeline and Table A7, and the M4 runtime interpretation were checked against their stated endpoints. Key figures remained interpretable in grayscale. No page clipping, overlap, blank accidental page, or damaged float was found.

## Clean-room verification

Verifier A: **PASS** scientific consistency. Verifier B: **MINOR** appendix ledger discoverability. Verifier C: **PASS** after the release-metadata correction. Independent PDF-only synthesis: **FINAL SUBMISSION QA: PASS**. Individual reports are saved alongside this report.

## Remaining non-blocking limitations

Appendix Table A7 is small and sits below a large blank area on p. 8; readers may need to zoom. The result and chronology are stated on pp. 6–7. The PDF-only reviewers did not independently replay private experiments.

## Final readiness

**READY FOR AUTHOR PR REVIEW.** The candidate anonymous submission set is the formal manuscript PDF, separate appendix PDF, and source ZIP. The hardware-only PDF is an internal proof.
