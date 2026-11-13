# Repository evidence status — 2026-11-13

A CPU-only JPDC evidence closeout is prepared in [benchmarks/jpdc_closeout_20261113](benchmarks/jpdc_closeout_20261113/README.zh.md). It independently recomputes five A5000 timing panels, S3 stratified-root inference and the two-case free-service negative result; maps code guarantees to their actual scope; records the fixed OASST Apache-2.0 correction and post-cleanup raw-data limits. See [machine-readable status](benchmarks/jpdc_closeout_20261113/STATUS.json).

No model/GPU/backend context, placement, forward, new experiment, manuscript edit, merge or submission was performed. PR221 raw CPU payloads remain unlocated in accessible scopes; the JPDC-specific author guide returned HTTP 403. These gaps are explicit, not reported as passed. Full current-content validation of all S3 recovery candidates was not run. No additional GPU experiment is necessary for the narrowed claims in this closeout.

The older repository/manuscript status below is retained as historical context; this update does not verify or change the manuscript build or publication state.

---

# Historical repository status — 2026-10-21

All **25 PRs open at the start of this maintenance request** were merged using their exact head SHAs. Archive-integration head: `55953777cdb6303a0cc4a3ad73679c2fc2e73d73`. The complete ledger is [MERGES.json](docs/closeout_20261021/MERGES.json). New experiment-design PRs are intentionally separate from those completed merges.

Current manuscript: `paper/arxiv_v4_candidate/`. The contribution-led v4 source was rebuilt locally from the delivered patch; the PDF is byte-identical to the reviewed 23-page arXiv candidate. Public version is still v3. This repository operation performs no arXiv/journal/Zenodo submission.

| Area | Current disposition |
|---|---|
| Original CUDA three-family request and 72-context evidence | Retained with original contracts |
| B570 GQA/request and thread policy | Qualified fixed panels; original negative costs retained |
| RTX k1 service panel | Completed; incremental layout benefit unresolved; drafting economics separately reported |
| B570 draft-prefill submission | Numerical qualification exists; clean cost closeout incomplete in archived PR135 |
| CPU8 / old engineering attempts | SOURCE_BLOCKED, ENTRY_BLOCKED, 0/8, no F0; archived only |
| New RTX / B570 closeout | Design and CPU tooling only; no native run in this maintenance task |

See [closeout decisions](docs/closeout_20261021/README.md). Earlier status files and manuscript versions are history, not the current build entry. The source-only CI from PR127 is branch-limited/manual and is not Windows acceptance; its merge does not dispatch it.
