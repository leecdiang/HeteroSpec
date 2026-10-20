# B570 CPU8 A2 — source-only split, candidate implementation

**STATUS: SOURCE_BLOCKED / ENTRY_BLOCKED / formal 0/8. Draft only.**

Start here to save platform context:

1. [A_SCOPE_V2.md](A_SCOPE_V2.md) — binding A source-only review separately from B/C Windows native guarantees; exact legacy operation mapping, budgets and evidence requirements.
2. [SOURCE_COMPOSITION.json](SOURCE_COMPOSITION.json) — SHA256 inventory of **123 current source/import files**: 106 preserved, 13 prospective replacements, 4 new helper modules. **Not** a native/frozen/source-review PASS.
3. [source_candidate/](source_candidate/) — candidate bytes at the source-relative deployment paths; do not execute as-is. [tests/test_a2_contract.py](tests/test_a2_contract.py) adds synthetic checks, **not executed** during this Github-only revision.
4. [PLATFORM_HANDOFF.md](PLATFORM_HANDOFF.md) — single current handoff; inherited old prompts and receipts do not authorize a native run.
5. [CPU8_ACCEPTANCE_PLAN.md](CPU8_ACCEPTANCE_PLAN.md) and [NATIVE_ENTRY_PLAN.md](NATIVE_ENTRY_PLAN.md) — B/C conditional bounds and fixed four B rows; B 1200 process-second figure is **not proven**, U≤360 remains UNKNOWN.

A independent P0–P2 review must bind every pinned source/config/test/input byte against the exact **review/PINNED_SOURCE_COMPOSITION.json** and current immutable Git commit. Hidden reviewer provider process counts and costs stay UNKNOWN, separately reported, not part of B/C Windows Job. A's source-only finalizer can only emit SOURCE_REVIEW_EVIDENCE_CONSISTENT; source_review_origin_v7 requires outside-candidate provider request/response capture and an independently authenticated reviewer before SOURCE_REVIEW_PASS. Both are UNVERIFIED.

No B570/native, GPU, model, actor, RTL, F0 or formal test executed, no PR merge. Old v6/PR119 raw and closed UUIDs unchanged.

## Three-P1 source-repair candidate (not approved)

The stacked Draft PR127 now fixes the unassigned suspended root cleanup route, B failure guard/child/outside-owner identity, and the pre-/post-F0 hash cycle using a pinned formal template. Source-only targeted regressions and runtime-independent archive checks are required before review; the complete current A review packet contains 123 source/import files plus 14 auxiliary inputs, including the updated native-entry and C acceptance plans. Previous 12-input inventories are historical snapshots, not current approval. Full independent P0–P2 and B/C native gates remain NOT_RUN.

## Source-only CI evidence and status

The external GitHub Actions workflow `.github/workflows/b570-a3-source-only.yml` executed successfully at `9c4a356b893b5b7193c5f42d96db78b1222df6f1` (run `39360981060`): 123 source/import + 14 auxiliary identity matches, 111 Python AST parses, 58 candidate source-only tests and 29 original boundary tests. **These are real Linux source-level checks; all native fixtures remain synthetic.** Later commits must rerun CI at their own head. A full authenticated independent P0–P2 review is still NOT_DONE; B entry and C CPU8 are NOT_RUN, formal 0/8, no F0. B00 assignment-failure negatives are newly identified prospective native prerequisites with separate, not-yet-proven budgets.
