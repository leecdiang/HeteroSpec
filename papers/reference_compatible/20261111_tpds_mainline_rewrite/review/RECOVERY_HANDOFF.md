# Recovery and completion of the approved TPDS rewrite

The interrupted 11 November rewrite was recovered with its source, numeric inputs,
editable figures, completed PDFs, review diffs, and release scripts intact. The
remote repository had no branch or PR for this afternoon rewrite at the recovery
check. Its previous upload had saved figure/PDF blobs, but had not created a commit.

The recovered manuscript is the 10-page TPDS rewrite with a separate 5-page
supplement. It is distinct from the earlier paper in PR #220. The original working
snapshot remains intact. The recovered project is the current author-review release.

The second independent content review confirmed the mechanism directions and
recomputed the displayed application, packing, width and B2 comparisons. The
visual reviewer inspected every page and the grayscale encodings of the main
comparison figures. The recovery changed only first-use acronym definitions in
the abstract, introduction and mechanism section. After recompilation, only main
pages 1 and 2 changed; pages 3–10 and all five supplementary pages retain their
previous rendering. All 35 numerical/evidence tests pass again.

PR #218 still has commit `4fe337a8ff349d547023f9dd60b8e114e5323207` at the recovery
check. B2 results are available; no full-model S3 results have been delivered.
No GPU inference was performed for either the rewrite or this recovery.

## Resume from this package

- Read `README.md` and `REVIEW_GUIDE_ZH.md`.
- Edit `abstract.tex`, `sections/` and `supplement_body.tex`.
- Build with `bash build.sh`, or use `bash build.sh --tex-only` for bundled figures.
- Check `REWRITE_EVIDENCE.json` for source, data, figure and PDF identities.
- Keep application-level speculative gains separate from component attribution.
- Retain the negative live-width results and the mixed-Q4 strong-baseline boundary.

`RECOVERY_VALIDATION.json` gives the recovery checkpoint. The GitHub PR provides
the published branch and commit identity; it is an author-review draft.
