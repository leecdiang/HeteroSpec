# Author-side validation scope and records

All reconstruction and validation work is CPU-only. No new model request, forward, warmup, inference experiment, merge, submission or public data release is part of this revision.

## Source inheritance

Remote main, #69 and #70 were inspected again before publication. #70 remains an open Draft PR on #69 and its head is the verified planning commit `00ea8f7c3a49b900bf5f21a95876e9a3a6dd610f`; that commit's parent is `21aa7b29142a1e3b7130b8e4a6a252777a91af80`. Main remains `f3fd2aecc6288c661033ee83d5216db6481dac3f`. The independent v014 branch begins at #70, rather than old main. The baseline recursive tree has 5,427 blobs and is not truncated. `provenance/BASELINE_INHERITANCE.json` records the relationship; `output/REMOTE_INHERITANCE_QA.json` records the post-write remote preservation check.

The portable sources authenticate 133 read files against Git blob and SHA-256 identities. The 26 inherited evidence exports and 16 historical copies are byte-identical to their source bindings. Original experiment/report/manuscript files are preserved in the baseline tree. No freeze tag is moved. The local workspace is a materialized authenticated source subset, not a complete Git clone.

## Numerical checks actually executed

`output/NUMERICAL_QA.json` records the full result. The unchanged inherited RTX verifier checks 384 formal observations and qualification/ID-digest joins, 12 comparisons, 48 task-level and two aggregate ratio identities. The new CPU wrapper independently constructs absolute condition medians, regenerated editable tables and five scientific figures; it also checks all 12 historical intervals and 48 saved round summaries. NumPy PCG64/type-7 and historical Python `Random.choices`/order-statistic intervals remain distinct with their original seeds and task order.

Checks retain RTX request ratios 1.741569 ordinary/candidate, 1.035071 matched/candidate and 1.682560 ordinary/matched; all seven request regressions and matched-request round 2 at 0.940220 remain. The 16-mask probe matrix yields 3/7/11/15. RTX and B570 natural-cross matrices are reconstructed from their bound records. B570 remains 119/120, with 15 ordinary/matched versus 14 old-N1 complete task pairs, all three timers and 26 paid suffix IDs. M4's paired secondary Guard latency interval and oracle reduction are reproduced. Fixed-UB checks aggregate saved task ratios and are explicitly not an independent raw timing parse. 358H conditional budgets are source-defined accounting under fixed progress, not forecasts.

## Build, package and visual checks

The main paper has 30 pages and S1 has 25 pages in Elsevier 12pt single-column review format. The abstract has 218 words, six keywords and five Highlights of 70/77/75/74/70 characters. All 18 bibliography entries are cited. `build.py` rejects overfull boxes, undefined/multiply-defined references, oversized floats, missing glyphs, unembedded fonts and Type 3 fonts. All figures are separate PDF/SVG assets, generated from identified data or actual implementation interfaces; tables and equations remain editable.

Both documents were compiled from an empty build directory. The final author ZIP is checked by `scripts/check_package.py`: extraction begins without build/output directories, authenticates every packaged source byte, then repeats the full CPU calculation and compilation. `output/SOURCE_PACKAGE_REBUILD_QA.json` binds the tested final ZIP and reports the actual document, numerical and figure/table equality checks. This local test does not claim use of a live Overleaf account.

All 55 final pages were rendered at 100 dpi and visually inspected using full-size numbered contact sheets. Independent figures were also inspected separately. The execution diagram's crowded labels and the task plot's aggregate-label overlap were corrected; hyperlink rectangles were removed; float placement now puts the five figures near their arguments. `output/VISUAL_QA.json` binds PDF hashes and individual page-render hashes, with observations on tables, equations, figures and references. Rendering code is supplied for repeat inspection.

## Limits and unresolved checks

This is author-side source/export validation. It does not reopen every private raw archive, rehash omitted model/driver binaries, independently certify physical timing, supply external peer review, or constitute a commercial similarity check. Inherited stronger original-host audits are cited as inherited. B570's missing payload and unknown interruption work remain unavailable; no denominator is repaired by interpolation.

The official 18-page JSA guide and accessible current primary sources support the requirements/reference audit. Live ScienceDirect access and later Elsevier-page retries were blocked or timed out; the Editorial Manager attachment workflow was not accessed. Vosti's DOI registration and final publisher pagination for The Illusion of Lossless Speculative Decoding need author rechecking. Actual author identities, affiliations, CRediT, funding, conflicts, permission/data access and final AI declaration are listed in `AUTHOR_TODO.md`. The present model-family scope remains Qwen3; subsequent cross-family evidence has an insertion point and no invented outcome.
