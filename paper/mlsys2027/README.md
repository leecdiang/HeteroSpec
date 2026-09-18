# MLSys 2027 paper workspace

Target venue: **MLSys 2027 Research Track**.

This directory is the controlled writing workspace for the HeteroSpec paper. It is intentionally separated from platform reports and raw experiment archives.

## Current writing policy

- Write from tracked repository evidence; do not backfill missing measurements from prose or memory.
- Preserve the strict token-exact correctness contract used by the experiments.
- Keep diagnostic and correctness-admissible results visibly distinct.
- Do not compare energy numbers across incompatible sensor boundaries as if they measured the same thing.
- Do not attribute cross-platform effects to one hardware feature unless the repository contains an isolated control.
- Keep the 358H section provisional until the formal Phase-3 campaign is completed and merged.
- Use **RTX 5070 Ti Laptop** everywhere; do not shorten it to desktop-like "RTX 5070 Ti" when the distinction matters.

## Files

- `FORMAT_REQUIREMENTS.md` — official MLSys 2027 submission constraints checked against the conference CFP.
- `EVIDENCE_AUDIT_2026-09-18.md` — repository evidence/status audit before drafting.
- `OUTLINE.md` — initial 10-page research-track paper structure.
- `WRITING_STATUS.md` — section-by-section drafting gate.
- `template/README.md` — instructions for importing the official style unchanged.

## Proposed paper thesis

A concise working thesis is:

> Speculative decoding on consumer hardware is profitable only when the execution path that satisfies the chosen correctness contract also amortizes target verification; faster drafting alone is insufficient when verification, state reconstruction, or runtime integration dominates.

The paper should present this as a bounded systems result across the tested runtimes, workloads, quantizations, and devices—not as a universal statement about Metal, CUDA, Vulkan, NPUs, or speculative decoding.

## Immediate next steps

1. Import the official MLSys 2025 style package referenced by the MLSys 2027 CFP, unchanged.
2. Start drafting Introduction, Background/Model, Methodology, and completed-platform Results now.
3. Do not freeze Abstract, 358H Results, Discussion, or Conclusion until 358H Phase 3 closes.
4. Build the final paper from a 10-page main-body budget; references are outside the 10-page limit and appendices are uploaded separately.
