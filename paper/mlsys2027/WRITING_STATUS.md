# MLSys 2027 writing status

Status date: 2026-09-18.

Authoritative scientific control file: `PAPER_FRAMEWORK_HANDOFF.md`.

Legend:
- READY — evidence is sufficiently closed to draft.
- AUDIT — draftable only with explicit ledger/provenance checks still pending.
- HOLD — do not freeze.

| Section | Status | Notes |
|---|---|---|
| Introduction | AUDIT | Main question is stable; final headline ordering waits for cross-platform claim audit. |
| Background: speculative decoding | READY | Algorithmic explanation is stable. |
| Cost / break-even model | AUDIT | Minimal formula is provisionally supported; full formula audit is Round 6. |
| Correctness contract | AUDIT | Token-ID equality is stable; dedicated contract audit remains Round 8. |
| Methodology: M4 | AUDIT | Platform closed; deep provenance/statistics audit pending. |
| Methodology: RTX 5070 Ti Laptop | AUDIT | Platform closed; preserve Laptop designation. |
| Methodology: B570 | AUDIT | Platform closed; serialized `V2_exact` terminology needs correction in paper-facing text. |
| Methodology: 358H | AUDIT | Phase 0–3 closed and merged; source-provenance limitation must remain explicit. |
| M4 results | AUDIT | Include representative negative + preregistered code-conditioned positive. |
| RTX results | AUDIT | Include raw-vs-admissible verification distinction. |
| B570 results | AUDIT | No correctness-admissible optimization result; timing/energy diagnostic. |
| 358H results | AUDIT | CPU 0.734x, NPU 0.352x; both exact; verification/state-interface mechanisms. |
| Cross-platform final table | AUDIT | Can be drafted from ledger, but final wording waits for Round 10. |
| Discussion | HOLD | Wait for formula, stats, correctness, energy, and cross-platform audits. |
| Related work | AUDIT | Requires literature/novelty pass. |
| Limitations | READY | Existing boundaries are explicit; refine after dedicated audits. |
| Abstract | HOLD | Freeze after final thesis/contribution ordering. |
| Conclusion | HOLD | Freeze after Round 12. |
| Appendix | AUDIT | Can be assembled incrementally from provenance material. |

## Internal evidence discipline

For every table/figure intended for the paper, maintain:
- source report / analysis file;
- source commit;
- exact aggregation script;
- primary / secondary / diagnostic / post-hoc classification;
- correctness status;
- energy sensor boundary if applicable.

Do not convert a diagnostic result into a primary optimization claim.
Do not use `V2_exact` for the B570 serialized fallback as a global statement while full-workload exactness is 60/90.
Do not use isolated NPU throughput as the 358H end-to-end draft cost.
