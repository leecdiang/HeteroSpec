# HeteroSpec

**Phase-Scoped Query Layouts for Reference-Preserving Speculative Decoding**  
Chengzhan Li · University of Electronic Science and Technology of China

The current author-review manuscript is [paper/arxiv_v4_candidate](paper/arxiv_v4_candidate/README.txt). The public preprint remains **arXiv:2610.03228v3**; the v4 candidate has not been submitted.

## Start here

| Task | Entry |
|---|---|
| Read/build the current paper | [Manuscript entry](paper/README.md) |
| Recompute reported values, no GPU | `python -B paper/arxiv_v4_candidate/anc/check.py` |
| Understand/reuse the layout interface | [Query-layout integration kit](src/query_layout/README.md) |
| Check completed versus blocked evidence | [Current state and closeout](docs/closeout_20261021/README.md) |
| Audit this integration | [Exact 25-PR merge ledger](docs/closeout_20261021/MERGES.json) |
| Prepare journal review | [Reproduction and submission checklist](docs/closeout_20261021/REVIEWER_GUIDE.md) |

The 2026-10-21 integration merged all 25 previously open PRs at pinned heads. An archival merge preserves a study's outcome; it does not turn failed, blocked or unstarted work into a PASS. In particular, CPU8 remains SOURCE_BLOCKED / ENTRY_BLOCKED, 0/8 and no F0. Historical RUN scripts and prompt files are records, not current execution instructions.

RTX holds the primary new-input/length-transfer closeout. B570 has one separate draft-prefill submission-cost closeout. M4, 358H, old CPU8 and hardware/RTL branches are not reopened. The current plans require machine-side registration before any model execution.

No model measurements, old reference bytes, failed results or resource ledgers were changed by repository maintenance. Report-level checks are not independent replay of all raw vectors. Third-party runtime/model licenses retain their own scope; see [LICENSE_SCOPE.txt](LICENSE_SCOPE.txt).

[Preserved previous README](docs/history/README_before_20261021.md) · [Previous status](docs/history/REPO_STATUS_before_20261021.md)
