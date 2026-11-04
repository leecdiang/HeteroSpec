# HeteroSpec

**Phase-Scoped Query Layouts for Reference-Constrained Speculative Decoding**  
Chengzhan Li · University of Electronic Science and Technology of China

The public preprint is [arXiv:2610.03228v4](https://arxiv.org/abs/2610.03228v4), revised 22 October 2026. See [manuscript navigation](paper/README.md) for the merged 27 October/1 November historical revisions and the newer, unmerged [#164 candidate](https://github.com/leecdiang/HeteroSpec/pull/164). These are distinct source versions, not interchangeable publication artifacts.

## Start here

| Task | Entry |
|---|---|
| Read/build the checked-in manuscript snapshot | [Manuscript entry](paper/README.md) |
| Recompute 1 November snapshot values, no GPU | `python -B paper/scope_state_revision_20261101/anc/check.py` |
| Understand/reuse the layout interface | [Query-layout integration kit](src/query_layout/README.md) |
| Read the 2026-10-21 closeout | [Archived integration state](docs/closeout_20261021/README.md) |
| Audit this integration | [Exact 25-PR merge ledger](docs/closeout_20261021/MERGES.json) |
| Review the integration-era reproduction checklist | [Reproduction and submission checklist](docs/closeout_20261021/REVIEWER_GUIDE.md) |

The 2026-10-21 integration merged all 25 previously open PRs at pinned heads. An archival merge preserves a study's outcome; it does not turn failed, blocked or unstarted work into a PASS. In particular, CPU8 remains SOURCE_BLOCKED / ENTRY_BLOCKED, 0/8 and no F0. Historical RUN scripts and prompt files are records, not current execution instructions.

No model measurements, old reference bytes, failed results or resource ledgers were changed by repository maintenance. Report-level checks are not independent replay of all raw vectors. Third-party runtime/model licenses retain their own scope; see [LICENSE_SCOPE.txt](LICENSE_SCOPE.txt).

[Preserved previous README](docs/history/README_before_20261021.md) · [Previous status](docs/history/REPO_STATUS_before_20261021.md)

## Repository map and later work (2026-11-04 snapshot)

At this review, `main` is [`f4e7c365`](https://github.com/leecdiang/HeteroSpec/commit/f4e7c3651de187213ddf1d4e13cce95db3c91de9), including the B570 prefill closeout in [#143](https://github.com/leecdiang/HeteroSpec/pull/143), historical manuscript revisions in [#145](https://github.com/leecdiang/HeteroSpec/pull/145), [#153](https://github.com/leecdiang/HeteroSpec/pull/153) and [#154](https://github.com/leecdiang/HeteroSpec/pull/154), and native reproduction handoff in [#146](https://github.com/leecdiang/HeteroSpec/pull/146). The merged #146 supplies preparation and handoff material, not new GPU measurements. The later PRs below remain **unmerged**; their files and results are not implied to be present in a checkout of `main`.

### Browse without moving historical files

- [paper/](paper/): checked-in manuscript materials. Later manuscript revisions remain on their own branches and should be reviewed separately.
- [src/](src/) and [scripts/](scripts/): implementation and supporting tools; start with the query-layout integration kit above.
- [benchmarks/](benchmarks/) and [docs/](docs/): experiment entries, protocols, reviews and closeout documentation.
- [runs/](runs/), [reports/](reports/), [artifacts/](artifacts/) and [logs/](logs/): retained records. Follow each study's provenance and evidence manifest rather than treating directory contents as a new completed run.
- [docs/history/](docs/history/): preserved previous repository guidance.

### Unmerged research navigation

| Work | Entry | Status and reading boundary |
|---|---|---|
| RTX held-out/length closeout | [#140](https://github.com/leecdiang/HeteroSpec/pull/140), [#142](https://github.com/leecdiang/HeteroSpec/pull/142), [#144](https://github.com/leecdiang/HeteroSpec/pull/144) | Original design, retained coverage block, then amended finite-panel result. Preserve the Qwen noise limit and Llama reference counterexample. |
| Native reproduction and material delivery | [#147](https://github.com/leecdiang/HeteroSpec/pull/147), [#148](https://github.com/leecdiang/HeteroSpec/pull/148), [#149](https://github.com/leecdiang/HeteroSpec/pull/149), [#150](https://github.com/leecdiang/HeteroSpec/pull/150) | Follow-up to merged #146: #147/#148 report native execution; #149/#150 address material delivery. These follow-up PRs remain unmerged. |
| Shared reference-preserving runtime | [#164](https://github.com/leecdiang/HeteroSpec/pull/164), [#165](https://github.com/leecdiang/HeteroSpec/pull/165), [#166](https://github.com/leecdiang/HeteroSpec/pull/166) | Method/candidate and backend-specific transfer studies; qualification is tied to the stated numerical oracle and deployment. |
| Strong whole-graph comparator | [RTX #168](https://github.com/leecdiang/HeteroSpec/pull/168), [B570 #169](https://github.com/leecdiang/HeteroSpec/pull/169) | Completed reported panels do not establish a general natural-service advantage of local grouping over whole-graph cuts. |
| RTX operator frontier | [#170](https://github.com/leecdiang/HeteroSpec/pull/170), [#171](https://github.com/leecdiang/HeteroSpec/pull/171) | Plan/audit followed by native results. Packed operators improve the prior implementation; equally optimized WB remains slightly faster in the four-input natural panel. |
| Natural prefix reuse | [RTX #172](https://github.com/leecdiang/HeteroSpec/pull/172), [B570 #173](https://github.com/leecdiang/HeteroSpec/pull/173) | **Design + CPU toolkit, not native results** at the inspected heads. Shared held-out execution requires both source/policy freezes. |

This shortlist is not a complete PR inventory or merge approval. Follow each study’s dependency chain and pinned evidence; retain failed attempts and scope limits.

### Interpret the latest results conservatively

- Historical M4/RTX/B570 workload comparisons corrected in [#28](https://github.com/leecdiang/HeteroSpec/pull/28) establish **re-tokenized-text agreement**, not direct generated-token-ID equality. Keep that historical scope separate from the prospective M4 direct-ID results, which the correction left unchanged.

- [Pinned RTX operator results](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/RESULTS.md): crossing-focused append measurements favor local grouping, but the deliberately balanced coordinates are not a natural workload average. Natural complete-service geometric means are 3.2219 s for new QB and 3.1985 s for equally optimized WB.
- [Pinned B570 parallel results](https://github.com/leecdiang/HeteroSpec/blob/8ca17478c292275b3515a91b51d0e791a8fae256/benchmarks/b570_parallel_v1/RESULTS.md): natural WB/QB is 1.00029 with a 95% input-bootstrap interval of 0.99967–1.00120. Boundary-active gains depend on width; q32 reverses in favor of WB in the reported crossing panels.
- Numerical qualification, elapsed-time improvement, portable evidence delivery and manuscript integration are separate milestones. A passing CPU toolkit test is not GPU qualification, and a matching greedy sequence is not full-vector equality.

Documentation maintenance preserves all existing files and paths, including frozen and negative evidence. Coordinate active experiment and manuscript branches separately before integration.
