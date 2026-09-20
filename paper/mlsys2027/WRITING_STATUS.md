# MLSys 2027 writing status

Status date: **2026-09-19**.

Authoritative scientific control file: `PAPER_FRAMEWORK_HANDOFF.md`.

Scientific audit status: **ROUNDS 1–12 COMPLETE + TERMINAL REVALIDATION COMPLETE**.

Legend:
- READY — scientifically closed enough to draft from the handoff.
- FUTURE — not part of current evidence; requires a new preregistered study if pursued.

| Section | Status | Notes |
|---|---|---|
| Introduction | READY | Final scientific thesis and contribution order frozen; exact title wording remains open. |
| Background: speculative decoding | READY | Explain algorithm without claiming heterogeneous SD novelty. |
| Realized-cost accounting | READY | Use `D_real + R_target + X`; keep `V_k^micro` separate; do not claim the accounting identity as new theory. |
| Correctness contract | READY | Bind claims to runtime/config/path/workload; token exactness != functional HumanEval correctness. |
| Methodology: M4 | READY | Distinguish historical MLX-LM precision failures from final llama.cpp Q8_0 path. |
| Methodology: RTX 5070 Ti Laptop | READY | Preserve “Laptop”; disclose weaker raw per-run Git provenance. |
| Methodology: B570 | READY | Use `V2_serialized` / serialized `V_2^micro`; no admissible optimization result. |
| Methodology: 358H | READY | Phase 0–3 closed; STRONGLY_SUPPORTED source reconstruction limitation stays explicit. |
| Statistics / uncertainty | READY | Preserve campaign-specific estimators/bootstraps; prompt CIs do not capture all session/thermal uncertainty. |
| M4 results | READY | Representative negative + separately preregistered code-conditioned positive; primary energy neutral within uncertainty. |
| RTX results | READY | Raw-fast vs correctness-admissible serialized distinction; bounded numerical argmax flip. |
| B570 results | READY | Timing/energy diagnostic only; serialization != exactness. |
| 358H results | READY | CPU 0.734x, NPU 0.352x; exact; measured target/state-interface mechanisms. |
| Cross-platform regime map | READY | Mechanism/regime map only; no hardware leaderboard. |
| Energy | READY | Boundary-separated only; no global J/token ranking. |
| Discussion | READY | State reuse / path selection / workload-aware policy are implications, not measured contributions. |
| Related work | READY | Must position against heterogeneous SD, MLSys 2026 systematic SD performance study, runtime-controlled `τ/c` evaluation, correctness-first batch SD, and numerical determinism work. |
| Limitations | READY | Use the current reviewer attack list in the handoff. |
| Abstract | READY | Draft only from the frozen thesis and bounded novelty statement. |
| Conclusion | READY | Draft only from the frozen thesis; do not inflate generic claims. |
| Appendix | READY | Provenance, exactness, bootstrap, telemetry and deviations can be assembled from the ledger. |
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
- claim heterogeneous speculative decoding, a generic cost formula, acceptance-insufficiency, or batch-shape nondeterminism as first work.

## Ready-to-write scientific thesis

A speculative path is profitable under this study only when the path that remains admissible after the frozen correctness contract and the realized stateful draft/target costs fit within the output progress committed per round. The tested systems expose profitable, exact-but-negative, fast-but-inadmissible, and state-interface-bound regimes.

Use `PAPER_FRAMEWORK_HANDOFF.md` directly for claim taxonomy, evidence ledger, related-work novelty boundaries, figure plan, reviewer attacks, decisions, and the terminal audit log.

## Manuscript construction update — 2026-09-20

**Manuscript v0.1 — hardware-complete / runtime-reserved** is now built in `manuscript/`. The READY table above remains the scientific-readiness record. All hardware sections, a stable hardware conclusion, five figures, three main tables, two appendix tables, references, and a separate appendix have been drafted. Section 6 is explicitly a proposed interface/evaluation reservation with results pending. No experiment or measured runtime intervention was added.

The title, abstract and final conclusion are provisional; author review is still required. The authoritative handoff has not been replaced or edited. See `MANUSCRIPT_STATUS.md` for the final page allocation, QA, limitations and delivery details.
