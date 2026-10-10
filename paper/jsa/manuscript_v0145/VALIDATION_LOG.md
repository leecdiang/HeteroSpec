# v0.14.5 validation log

Baseline: Draft #75 at `92b08a0ffab2ca08c835b411d9d7478ccd57603b`. Date: 2026-10-10. CPU-only editorial and packaging work; no new inference.

## Manuscript and evidence

- Authenticate all 299 baseline source members against #75 Git blobs. Exactly 287 remain byte-identical; four TeX files have uniquely reversible closeout edits, and eight build/delivery files have explicit before/after hashes.
- Preserve the v0.14.4 humanizer receipt unchanged; reverse the new layer before running its 19-file / 63-block checks. Compare the four edited files manually against #75 and unchanged result sections.
- Title uses Measured Cost. Abstract: 204 words. Its omitted generation ratios remain in §6 and the cost tables; request ratios and negative findings retain their stated scope.
- All 22 locked figure/table assets equal #75 byte-for-byte. Inherited checks retain 16 original tables, 537 generated data cells plus inline tables, 26 claim rows, 28 experiment entries and all seven scientific-input objects. Numerical and standard-library scientific checks pass.
- Author identity, affiliation and contact in both source entries follow user-provided https://arxiv.org/pdf/2610.03228v1. No funding, conflicts or public-access facts are invented.
- Follow-up title-block adjustment: email below affiliation, clickable mailto address, no repeated author-name parenthesis or email footnote. The title, abstract, body and frozen figure/table assets are unchanged by this adjustment.

## PDF and public arXiv variant

- Main 12 pages; supplement 13 pages; normal Elsevier 5p Times double columns. Zero overfull boxes, undefined references, duplicate labels/targets, missing glyphs or oversized floats. All fonts embedded; no Type 3 fonts.
- arXiv uses one `arxiv.tex` source and a 26-page combined PDF, with supplement starting on page 14, continuous printed page numbers, 30 supplement navigation entries and 18 shared references. Seven scientific figures and all original table/content inputs remain present.
- Stamp-spacing follow-up: the generated arXiv entry uses 20-mm left/right margins, with unchanged type size, column separation and text height. First-page text begins at 56.334 PDF points (19.87 mm including microtype protrusion), about 7 mm farther inward. This repaginates the combined PDF from 24 to 26 pages. The platform stamp is not part of the author PDF; live stamped output was not inspected.
- The arXiv variant changes front matter, a factual AI/reproducibility statement and S7 delivery instructions. S7's exact delivery replacements are recorded separately and preserve numerical sequences, equations and citations. Journal-only unresolved forms remain in the separate author-review files; no public evidence deposit is asserted.
- Clean extraction of the 37-file arXiv ZIP compiles with supplied `.bbl`, clean diagnostics and embedded vector fonts. Repeat compilation is byte-identical. All internal/external links have valid destinations; 34 bookmarks are retained. Local compilation is not live arXiv acceptance.
- Visual review covers all pages of the separate drafts and all 26 combined pages in numbered contact sheets; key title, figure and supplement-transition pages are additionally inspected at enlarged resolution. Figure 1C and Figure 2 retain the latest #75 layout and color roles.

## Portable source checks

- The 306-file author ZIP is extracted into an empty temporary directory and rebuilt. Both separate PDFs, all 22 figure/table assets and the numerical, scientific, lossless, visual-data, humanizer and closeout receipts match; the single-entry arXiv PDF and 37-file source ZIP also match byte-for-byte.
- The separate 20-file main and 19-file supplement flat ZIPs compile from empty directories with identical page counts and extracted text, clean diagnostics and embedded fonts. Their PDF bytes differ from the structured-source PDFs; byte identity is not claimed for the flat variants.
- Final receipts are `output/SOURCE_PACKAGE_REBUILD_QA.json` and `output/FLAT_SOURCE_REBUILD_QA.json`. The package hash is recorded in the rebuild receipt and `output/SHA256SUMS.json` rather than embedded here, avoiding a self-referential archive hash.

## Scope

No merge, arXiv submission or new experiment. Private original-host raw audits remain inherited; unavailable B570 payloads remain missing. The second family, same-contract external-method comparison and independent-session stability remain explicitly open scientific work. The original v0.14.4 validation record is preserved under `validation/`.
