# Reconstruct paper: Phase-Scoped Query Layouts for Reference-Preserving Speculative Decoding

## Status
Complete manuscript/documentation reconstruction. No new GPU/model runs, scientific data changes, prior-PR merges, release update or journal submission. This file is a **proposed PR description**, not an existing GitHub PR.

## Change set
Add `paper/jsa/manuscript_v0150/` with full English main article and supplement, editable vector figures, bibliography, reported-value data, source/claim maps, build/check scripts and author checklist. Preserve all earlier manuscripts and experimental archives unchanged.

## Scientific storyline
Reference contract → explicit Query/Mask/GQA/layout design → phase guard and cache reuse → identical-input attention correspondence → frozen three-family complete-output confirmation → same-reference PQ/QB/GS repair costs → distinct draft increment → B570 projection/retained-state boundaries.

Core evidence uses pinned PR91/94, PR98, PR99 and PR101. The latest B570 result remains separately sourced even if not merged into main. The paper does not use the repository's historical name in its title because of the unrelated ACL HeteroSpec article.

## Important retained limits
- Bitwise operator correspondence is finite and not a numerical determinism theorem.
- QB's Vulkan portability is untested; the B570 projection frontier motivates that boundary.
- Only32/40 B570 operator calls qualify; all8 scale/MUL sham failures remain excluded.
- Driver-body preregistration gap for P1A/B remains disclosed.
- KV-source suffix sensitivity is conditional on the validated necessary-state boundary0 receiver, not arbitrary opaque cloning.
- Existing stock-reference failures/null speedups remain unchanged; no diagnostic timer promoted to paid performance.
- Small PQ/QB benefits and per-task regressions remain visible; no invented CI or cross-date claim.

## Verification
Run `python scripts/check_reported_data.py` and `python scripts/build.py` in the new directory. Review `provenance/RECONSTRUCTION_QA.json` for the actual local checks. They verify reported data and the manuscript, **not** a new GPU reproduction or full raw native archive rerun.

## Review requested
Scientific scope, source correspondence, method lowering/cache obligations, fair comparator definitions, B570 state contract, author declarations and public artifact accessibility. No merge is requested automatically.
