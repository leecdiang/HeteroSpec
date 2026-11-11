# B570 Reviewer-Visible Commitment Integration — Phase 2

## Phase-1 dependency

The Phase-1 independent ledger validator returned **PASS** before and after integration. Its reconstructed totals remain 24 reserved prompts, three repetitions each, 72/72 predictor/live equality, 60/72 reference/live equality, 24/24 prompt classification, and 12/12 first-index agreement over four divergent prompts. CR-01 was **FULLY ADDRESSABLE FROM EXISTING RECORDS**; CR-02 was **ADDRESSABLE FROM EXISTING RECORDS**.

## Anonymous fields exposed

The PDF shows reserved task IDs, per-prompt sequence lengths and equality counts, a unique 12-hex-character prefix of each repeat-stable predictor/live sequence digest, the complete prediction-file content SHA-256 (as two consecutive 32-character lines), zero-based first-divergence indices and tokens, and relative event timing. All displayed result values are generated from the verified Phase-1 ledger.

## Fields intentionally withheld

Git commit IDs, repository identifiers and URLs, usernames, local paths, hostnames, branch names, and identifying artifact URLs are absent from the anonymous PDF. An independent push timestamp is unavailable and is not represented as known. No optional machine-readable supplementary export was made; the PDF claim does not depend on one.

## Reviewer-visible evidence

The appendix exposes a two-row comparison and a 24-row commitment table for 72 reserved pairs: frozen UB1 predictor/live 72/72, frozen UB128 reference/live 60/72, prompt classification 24/24, and first-divergence agreement 12/12 across four reference-divergent prompts. Its full prediction-file content SHA-256 is `0201ccd1f67492510d34be567aa83f1c38d3bd1f162a970c05d3cea9d3957826`. The generated table displays 12-character per-sequence digest prefixes only after confirming uniqueness among all 24 displayed prompts and within-prompt repeat stability.

## Chronology wording

The appendix says: “The recorded study chronology fixes the prediction file before the first live serialized reserved outcome.” The relative timeline is computed from Phase-1 recorded timestamps: H1 freeze $T_0$; prediction completion $T_0+1722.38$ s; first live outcome $T_0+1813.75$ s. Completion precedes live start by 91.37 s. The appendix explicitly says the content digest identifies bytes and does not supply the temporal ordering by itself. It makes no claim of an independently timestamped push or public wall-clock proof.

## PDF QA

The v0.8.2 appendix has 6 pages; `appendix-v0.8.3-phase2-preview.pdf` has 8. All eight pages were rendered and visually inspected. The 24-row table, task IDs, digests, timeline, divergence arrows and tokens are readable without clipping; the ledger occupies a dedicated full-width float page. No orphan caption was observed. The final appendix and unchanged main both build in a fresh directory. Their final TeX logs contain zero overfull boxes and zero unresolved references or citations. All PDF fonts are embedded. Extracted PDF text and metadata were checked for repository, path and commit identifiers: **PASS**. Both halves of the full prediction-file content digest are present in extracted text. The preview retains the existing appendix metadata subject label `v0.8.2`; the filename and content identify it as the Phase-2 preview.

## CR-01 status after Phase 2

**ADDRESSED IN APPENDIX.** An artifact-only reviewer can inspect the frozen file identity, ordering boundary, 24 prompt outcomes, exact-match comparator, and the four informative divergences.

## CR-02 status after Phase 2

**ADDRESSED IN APPENDIX.** The observed reference trajectory agreement (60/72) and frozen UB1 predictor agreement (72/72) appear together with their distinct roles. UB128 is not described as a failed mechanism predictor.

## Scientific change

Presentation only: no new scientific observation, no new inference, and no modification of closed evidence or the main manuscript.
