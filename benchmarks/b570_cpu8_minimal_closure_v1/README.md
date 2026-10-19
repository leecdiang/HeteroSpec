# B570 CPU8 A2 — source-only split, candidate implementation

**STATUS: SOURCE_BLOCKED / ENTRY_BLOCKED / formal 0/8. Draft only.**

Start here to save platform context:

1. [A_SCOPE_V2.md](A_SCOPE_V2.md) — binding A source-only review separately from B/C Windows native guarantees; exact legacy operation mapping, budgets and evidence requirements.
2. [SOURCE_COMPOSITION.json](SOURCE_COMPOSITION.json) — SHA256 inventory of **123 current source/import files**: 106 preserved, 13 prospective replacements, 3 new helper modules. **Not** a native/frozen/source-review PASS.
3. [source_candidate/](source_candidate/) — candidate bytes at the source-relative deployment paths; do not execute as-is. [tests/test_a2_contract.py](tests/test_a2_contract.py) adds synthetic checks, **not executed** during this Github-only revision.
4. [PLATFORM_HANDOFF.md](PLATFORM_HANDOFF.md) — single current handoff; inherited old prompts and receipts do not authorize a native run.
5. [CPU8_ACCEPTANCE_PLAN.md](CPU8_ACCEPTANCE_PLAN.md) and [NATIVE_ENTRY_PLAN.md](NATIVE_ENTRY_PLAN.md) — B/C conditional bounds and fixed four B rows; B 1200 process-second figure is **not proven**, U≤360 remains UNKNOWN.

A independent P0–P2 review must bind every pinned source/config/test/input byte against the exact **review/PINNED_SOURCE_COMPOSITION.json** and current immutable Git commit. Hidden reviewer provider process counts and costs stay UNKNOWN, separately reported, not part of B/C Windows Job. A's review-only finalizer can only emit SOURCE_REVIEW_EVIDENCE_CONSISTENT; external authentic review approval is still required for SOURCE_REVIEW_PASS.

No B570/native, GPU, model, actor, RTL, F0 or formal test executed, no PR merge. Old v6/PR119 raw and closed UUIDs unchanged.
