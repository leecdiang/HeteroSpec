# Manuscript navigation

## Public preprint

[arXiv:2610.03228v4](https://arxiv.org/abs/2610.03228v4), revised 22 October 2026, is the public preprint **Phase-Scoped Query Layouts for Reference-Constrained Speculative Decoding**. The later repository revisions below are distinct author-review sources; a directory name containing `v4` does not establish identity with the public release.

## Merged historical revisions

- [27 October P0 revision](arxiv_v4_candidate/README.txt), integrated through [#145](https://github.com/leecdiang/HeteroSpec/pull/145): evidence/work audit and narrative revision, labeled not submitted.
- [1 November scope/state revision](scope_state_revision_20261101/README.txt), integrated through [#153](https://github.com/leecdiang/HeteroSpec/pull/153) and [#154](https://github.com/leecdiang/HeteroSpec/pull/154): the checked-in historical author-review manuscript described below. It is not designated as the newest research manuscript or public release.

To build the merged 1 November revision from the repository root:

```sh
cd paper/scope_state_revision_20261101
python -B scripts/build.py --cached-bbl
```

Its recorded review reports **32 pages** (15 article/references + 17 supplement), **12 figures**, **41 references**, **1,680 report/source checks** and **86 analysis/regression tests**; the separate original runtime contract suite reports 12 passing tests. These are the retained revision's validation results, not a new validation run performed by repository maintenance.

- Recorded PDF SHA256: `59f0da87153cbb00fc4aea2e1a39a9abf43e9aed7baade8e0d2f9b6dc2cd76ee`
- Recorded 167-file manuscript Git tree: `d30655956e2268128945cceec9b0b59cf7b2d8af`
- [Review and dispositions](../docs/research/targeted_revision_20261101/REVIEW.md)
- [Validation record](../docs/research/targeted_revision_20261101/QA_FINAL.json)
- [Preserved earlier entrypoint](../docs/research/targeted_revision_20261101/PREVIOUS_PAPER_README.md)

The recorded review reports a rebuilt publication ZIP with a byte-identical PDF and unchanged pre-existing scientific inputs. It distinguishes retrospective analysis from new measurements, finite qualification from online guarantees, and source-host audits from independent-host replication. See the retained review for the full claims and delivery boundaries. Neither this documentation update nor the historical integration constitutes a submission or fresh author approval.

## Newer unmerged candidate

[PR #164](https://github.com/leecdiang/HeteroSpec/pull/164) contains **HeteroSpec: Reference-Preserving Query Batching for Quantized Inference**, a separate 3 November candidate built on #154. At the inspected head `06c5780d1a3e3e37b780d50274b6ab3e07bc96dc`, it remains an open draft, unmerged and unsubmitted. Use its [pinned source and build entry](https://github.com/leecdiang/HeteroSpec/blob/06c5780d1a3e3e37b780d50274b6ab3e07bc96dc/paper/reference_batching_20261103/README.md); that directory is not implied to exist in `main`.

The candidate's own evidence boundary separates frozen native results from its shared implementation candidate's CPU/source-integration validation. Later backend experiments and prefix-reuse plans remain separate PRs; see the [repository research map](../README.md). Do not attribute their findings to this manuscript without checking its pinned source and evidence manifest.

Historical manuscript directories and frozen evidence remain intact. Active manuscript work should continue on its existing branch; this page only routes readers between versions.
