# Manuscript entrypoint

## Current author-review candidate — 2026-11-01

The latest integrated source is [scope_state_revision_20261101](scope_state_revision_20261101/README.txt). It incorporates the final RTX three-date scope study and B570 producer–consumer study on top of PR145's P0 manuscript, followed by a figure and typography review.

```sh
cd paper/scope_state_revision_20261101
python -B scripts/build.py --cached-bbl
```

The reviewed PDF has **31 pages** (15 article/references + 16 supplementary material), **12 editable figures** and **41 references**. **1,668 report/source checks and 71 analysis/regression tests pass.** All 31 pages were rendered and inspected; the 12-figure review retained ten encodings and redrew two. The 52 non-generated scientific CSV/JSON files checked against the supplied latest source remain byte-identical. Release receipts and generated presentation summaries are distinguished from scientific inputs.

- PDF SHA256: `cd374ac9bf8a5cb161e6e4cb4bc5a48d23c33a8ab58b3d45e43b32d90dfa4df1`
- Exact 162-file manuscript Git tree: `9a0d1aa04e9da302ff05d1ce31d0224b97afcdb0`
- [Review and decisions](../docs/research/visual_review_20261101/REVIEW.md)
- [Artifact identity and scope](../docs/research/visual_review_20261101/IDENTITY.json)

The publication source ZIP additionally includes `PACKAGE_MANIFEST.json`. The PDF and full render/build logs are supplied separately to the author; no binary PDF is claimed to be committed here. Build with the included bibliography or install BibTeX to regenerate it. Report-only reconstruction is not native inference or external validation of bulk raw tensors.

This is a new manuscript directory. Earlier `arxiv_v4_candidate`, historical paper trees and all benchmark evidence remain unchanged. The previous entrypoint is retained [verbatim](../docs/research/visual_review_20261101/PREVIOUS_PAPER_README.md). The new PR is stacked on PR145's branch; no experiment PR, manuscript PR or main branch is merged by this update. No arXiv/journal submission is performed.
