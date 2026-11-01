# Manuscript entrypoint

## Approved targeted revision — 2026-11-01

Current source: [scope_state_revision_20261101](scope_state_revision_20261101/README.txt). This follow-up to PR153 implements the author-approved storyline/novelty audit without changing experimental evidence. It separates scope from local-layout cost, clarifies finite qualification versus online guarantees, explains the producer–consumer counterexample, and strengthens the Vosti/LLM-42 comparison. Humanizer and nondefensive editing follow the scientific revision.

```sh
cd paper/scope_state_revision_20261101
python -B scripts/build.py --cached-bbl
```

The reviewed PDF has **32 pages** (15 article/references + 17 supplement), **12 unchanged editable figures** and **41 references**. **1,680 report/source checks and 86 analysis/regression tests pass**; the separate original runtime contract suite has 12 passing tests. All 32 pages were rendered and inspected, with no blocking overflow, unresolved reference/citation or missing glyph. All fonts are embedded.

- PDF SHA256: `59f0da87153cbb00fc4aea2e1a39a9abf43e9aed7baade8e0d2f9b6dc2cd76ee`
- Exact 167-file manuscript Git tree: `d30655956e2268128945cceec9b0b59cf7b2d8af`
- [Review and dispositions](../docs/research/targeted_revision_20261101/REVIEW.md)
- [Validation record](../docs/research/targeted_revision_20261101/QA_FINAL.json)

The actual publication ZIP was extracted and rebuilt; its PDF is byte-identical to the reviewed PDF. Removing the entire ancillary directory also yields the same PDF. The ZIP includes one additional package manifest. PDF, complete logs, exact editorial diff, language edits and page renders are delivered separately; no PDF binary is committed.

All 53 pre-existing CSV/JSON report inputs or derived inputs checked against PR153 remain unchanged. New tables and algebra are explicitly retrospective, with no new measurement or uncertainty test. The proof concerns two finite binary qualification matrices, not the impossibility of modular verification. Source-host native audits, report-only reconstruction and independent-host replication remain distinct.

This PR is stacked on `paper/visual-review-20261101` (PR153), which is stacked on PR145. No PR or main branch is merged. Earlier manuscript directories and frozen benchmarks remain unchanged. The prior entrypoint is [preserved verbatim](../docs/research/targeted_revision_20261101/PREVIOUS_PAPER_README.md). No arXiv or journal submission is performed. The author must still approve the final text and arrange dependable reviewer access to restricted native assets.
