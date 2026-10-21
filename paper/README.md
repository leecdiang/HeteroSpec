# Manuscript entrypoint

The current author-review source is [arxiv_v4_candidate](arxiv_v4_candidate/README.txt). It replaces the earlier short PR138 reconstruction with the complete author-supplied v3-source-reconciled article, subsequent RTX/B570 evidence, and the 2026-10-21 cross-review refinement. It has not been submitted to arXiv or a journal.

From that directory:

```sh
python -B scripts/build.py
```

The reviewed PDF has 23 pages (13 article/references + 10 supplement), ten editable figures, 484 reported-value/source checks and 31 regression/mutation tests. PDF SHA256: `a2b844c631ef11bff5f5db0cbbc37b7966fe4d552f5b1b19681e2be8529bd6df`.

The source subtree is `34a2e1edeeb9478205aaaaa2ec8084f0c6d166c3`; all 100 committed files match the locally built and reviewed sources by Git blob/tree identity. The downloadable source ZIP additionally contains its package manifest. Review evidence is under [anc/review_round2](arxiv_v4_candidate/anc/review_round2/REVIEW.md); previous QA is retained under `anc/review` as history, not the current certificate.

These checks concern the manuscript and saved report data. They are not independent native-model execution or external authentication of full raw logits. Existing experimental failures, CPU8/F0 status, older manuscript directories and unrelated draft PRs are unchanged.
