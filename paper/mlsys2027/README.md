# MLSys 2027 paper workspace

Target venue: **MLSys 2027 Research Track**.

This directory is the controlled writing workspace for the HeteroSpec paper. It is intentionally separated from platform reports and raw experiment archives.

## Authoritative control file

`PAPER_FRAMEWORK_HANDOFF.md` is the scientific framework handoff / evidence ledger / decision log and is the single source of truth for paper claims.

If an older outline/status note conflicts with the handoff or repository evidence, update the living note rather than weakening the evidence.

## Current writing policy

- Write from tracked repository evidence; do not backfill missing measurements from prose or memory.
- Preserve the strict token-exact correctness contract used by the experiments.
- Keep diagnostic and correctness-admissible results visibly distinct.
- Do not compare energy numbers across incompatible sensor boundaries as if they measured the same thing.
- Do not attribute cross-platform effects to one hardware feature unless the repository contains an isolated control.
- The 358H Phase-3 campaign is complete and merged; it is no longer provisional.
- Use **RTX 5070 Ti Laptop** everywhere; do not shorten it to desktop-like “RTX 5070 Ti” when the distinction matters.
- Do not call the B570 serialized fallback globally exact while its full-workload result is 60/90 exact pairs.
- Do not treat isolated draft-device tok/s as realized speculative draft cost when the runtime reconstructs state.

## Files

- `PAPER_FRAMEWORK_HANDOFF.md` — authoritative scientific ledger, claim taxonomy, decision log, audit queue.
- `FORMAT_REQUIREMENTS.md` — MLSys 2027 submission constraints.
- `EVIDENCE_AUDIT_2026-09-18.md` — compact repository evidence/status audit.
- `OUTLINE.md` — initial paper structure; contains pre-Phase3 placeholders and is not frozen.
- `WRITING_STATUS.md` — section-level drafting/audit gates.
- `template/README.md` — instructions for importing the official style unchanged.

## Current thesis candidate

A concise working thesis is:

> Speculative decoding on consumer hardware is profitable only when the execution path that satisfies the chosen correctness contract also amortizes target verification and the realized stateful draft cost; faster drafting or high acceptance alone is insufficient when verification, state reconstruction, or runtime integration dominates.

This is a bounded systems result across the tested runtimes, workloads, quantizations, and devices—not a universal statement about Metal, CUDA, Vulkan, NPUs, or speculative decoding.

## Immediate next steps

Follow the bounded audit queue in `PAPER_FRAMEWORK_HANDOFF.md`:
1. M4 deep audit.
2. RTX 5070 Ti Laptop deep audit.
3. B570 deep audit.
4. 358H deep audit.
5. Unified formula/mechanism audit.
6. Statistics, correctness, energy, cross-platform, reviewer audits.
7. Freeze thesis/contributions only after those checks.

Do not start runtime implementation, final-title freeze, arXiv release, or manuscript-prose expansion from this status file.
