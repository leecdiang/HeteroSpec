# Reference-Compatible Parallel Execution for Quantized LLM Inference

**Working manuscript | 11 November 2026 | Draft**

This branch records the latest verified pre-submission manuscript and its claims/evidence register. It is not an arXiv replacement, journal submission, or experimental result branch.

## Source identity
- Author: Chengzhan Li; 14-page reading PDF (10-page main text + 4-page supplement).
- Reading PDF `HeteroSpec_Final_20261111.pdf`: SHA256 `81376232b6765983bc91b8765fa2ed06e57a09edfe88c68db476f61210a6fd61`.
- IEEE PDF `HeteroSpec_Final_20261111_IEEE.pdf`: SHA256 `8d8abaa4fe47eed08a67cdce7828bc319a2f473aba64da20ee4781025d7af2ca`.
- Editable author archive `HeteroSpec_Final_20261111_Author.zip`: SHA256 `e56013eace463b0615cf69dd130155b90bd2a26385286029891904689084f78b`.
- arXiv source `HeteroSpec_Final_20261111_arXiv_Source.zip`: SHA256 `1cf4cfd02a9307f8c890cb9fea3c6e3f72ee339a734594291f192fac5be074d6`.
- The corresponding author-owned archives were delivered in the ChatGPT conversation. **This GitHub tree currently contains the full extracted reading text, source identity, claims/evidence and metadata; it does not yet contain the editable TeX/figure binaries.** The source-import handoff is in `IMPORT_SOURCE.md`. Do not claim a clean GitHub checkout builds until that import is completed and verified.

## Scientific statement
The implementation derives phase plans from fixed producer behavior, physical KV extents, verified arithmetic recipes and output/state ownership. Application-level resident-service reductions relative to measured fixed target-only controls are 17.21%, 25.54% and 11.52% for the specified Linux Qwen3-8B, Qwen3-14B and Llama-8B deployments. Packing and LOCAL increments are separately measured. The 32B mixed-Q4 5.61% ordinary-service reduction is relative to **graph-level scalar-column execution**, not to a qualified backend-internal loop in a full-model service panel.

Windows and Linux reuse sixteen **task identities/input records** but establish separate numerical references and collect new measurements. The four q=8 equal-work origins are one APPS and three GSM8K records and differ from the sixteen-root live cohort.

## Evidence cutoff
PR218 (`f419a89d54f4ec93b4c9c328b4ea9f416ae3c989`) completed S1 numerical qualification and S2 bounded G/B/C **operator** comparisons. It remained Draft/unmerged at that cutoff. B2 and full-model S3 performance are not included in this manuscript version. New results require a versioned amendment and evidence review.

## Draft review checklist
1. Import the fixed author ZIP and commit actual TeX, figures, scripts, data, bibliography and build receipts.
2. Build main and journal PDFs from the committed source in a clean directory and compare to the pinned files.
3. Review the `CLAIMS_EVIDENCE.*` register and verify every remaining external reference.
4. Decide native evidence access, author metadata/disclosures and submission packaging.

Do not merge experimental PRs, modify the existing arXiv record, or submit this manuscript as part of this Draft PR.
