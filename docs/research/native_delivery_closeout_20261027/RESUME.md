# Resume final artifact validation

The source checkpoint is on PR145, branch `analysis/paper-major-revision-20261025`. The source root is `paper/arxiv_v4_candidate`. Platform delivery review is complete; do not repeat GPU experiments or reopen the completed packaging task.

1. Restore the Mac execution connection. Local working directory: `/tmp/heterospec-delivery-closeout-20261027`; the prior reviewed baseline is under `/tmp/heterospec-revision-20261026`. Do not change the unrelated checkout branch at `/Users/lee/Projects/HeteroSpec`.
2. Read the current PR145 head. Synchronize the committed paper files into the isolated working directory, including current REPRODUCTION_ACCESS.md, release metadata and cached bibliography; remote checkpoint formatting differs from the earlier local draft. The 22 new compact delivery records are exact existing repository blobs indexed in `anc/native_delivery/SOURCE_INDEX.json`.
3. Run `python3.11 -B scripts/build.py` with pdfLaTeX/BibTeX available. Regenerate main.bbl rather than trusting the temporary remote reconstruction. Inspect the resulting check/test totals and TeX logs.
4. Render and inspect all PDF pages, especially the expanded Supplement S10 and two new bibliography entries. Confirm no clipping, overflow, orphaned page or unresolved references. Record the final page count and PDF SHA256.
5. Confirm scientific input files remain unchanged relative to bc5157c and source-pinned delivery blobs still match. Update RELEASE_SCOPE.json, QA_STATUS.json and this revision record from pending to final. Commit these changes to PR145 with an expected-head guard.
6. Create the updated PDF/source/validation bundle. Existing full-bundle identity is `libfile_e890df8f8d748191b9e8176435b1ee23`; latest observed version is 5, filename `HeteroSpec_Native_Results_Full_20261026.zip`. Refresh current version before replacing. No replacement occurred in this closeout checkpoint.
7. Verify the remote source identities and deliver the updated bundle/PDF. Do not merge or submit the manuscript without authorization.

The current blockage is execution-host availability, not a platform-delivery defect.
