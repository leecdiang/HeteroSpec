# MLSys 2027 writing status

Status date: 2026-09-19.

Authoritative scientific control file: `PAPER_FRAMEWORK_HANDOFF.md`.

Scientific audit status: **ROUNDS 1–12 COMPLETE**.

Legend:
- READY — scientifically closed enough to draft from the handoff.
- FUTURE — not part of current evidence; requires a new preregistered study if pursued.

| Section | Status | Notes |
|---|---|---|
| Introduction | READY | Final thesis and contribution order frozen. |
| Background: speculative decoding | READY | Explain algorithm without claiming heterogeneous SD novelty. |
| Realized-cost accounting | READY | Use corrected `D_real + R_target + X`; keep `V_k^micro` separate. |
| Correctness contract | READY | Bind claims to runtime/config/path/workload; token exactness != functional HumanEval correctness. |
| Methodology: M4 | READY | Distinguish historical MLX-LM 4-bit failure from final llama.cpp Q8_0 path. |
| Methodology: RTX 5070 Ti Laptop | READY | Preserve “Laptop”; disclose weaker raw per-run Git provenance. |
| Methodology: B570 | READY | Use `V2_serialized`; no admissible optimization result. |
| Methodology: 358H | READY | Phase 0–3 closed; STRONGLY_SUPPORTED source reconstruction limitation stays explicit. |
| M4 results | READY | Representative negative + preregistered code-conditioned positive. |
| RTX results | READY | Raw-fast vs correctness-admissible serialized distinction. |
| B570 results | READY | Timing/energy diagnostic only. |
| 358H results | READY | CPU 0.734x, NPU 0.352x; exact; measured verification/state-interface mechanisms. |
| Cross-platform regime map | READY | Mechanism/regime map only; no hardware leaderboard. |
| Energy | READY | Boundary-separated only; no global J/token ranking. |
| Discussion | READY | State reuse / path selection / workload-aware policy are implications, not measured contributions. |
| Related work | READY | Must include Dovetail, DuoDecoding, Mirror-SD and systematic SD performance-modeling work; no firstness claim. |
| Limitations | READY | Reviewer attack list is frozen in handoff. |
| Abstract | READY | Draft only from frozen thesis. |
| Conclusion | READY | Draft only from frozen thesis. |
| Appendix | READY | Provenance, exactness, bootstrap, telemetry and deviations can be assembled from ledger. |
| New runtime state-reuse implementation | FUTURE | Separate preregistration and measurements required; not necessary to reinterpret current data. |

## Non-negotiable evidence discipline

For every manuscript table/figure:
- cite the exact source report / analysis file;
- retain source commit / archive reference;
- record aggregation script and estimator;
- mark primary / secondary / mechanism / diagnostic evidence;
- state correctness status;
- state energy sensor boundary where applicable.

Do not:
- convert diagnostics into primary optimization claims;
- call B570 serialized fallback globally exact;
- use target-forward `V_k^micro` as full realized target-round cost;
- use accepted draft tokens/round as direct `C`;
- use isolated NPU tok/s as realized draft cost;
- imply HumanEval token exactness is functional pass@k;
- rank M4/RTX/B570 energy as a common calibrated domain;
- claim heterogeneous speculative decoding or a generic cost formula as first work.

## Ready-to-write scientific thesis

A correctness-admissible speculative path is profitable only when the realized stateful draft interface and complete target-side round cost remain below the progress actually committed per round. The four consumer systems expose profitable, exact-but-negative, fast-but-inadmissible, and state-interface-bound regimes.

See `PAPER_FRAMEWORK_HANDOFF.md` Sections 22–28 for the final audit and reviewer constraints.
