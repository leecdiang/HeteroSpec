# RTX platform closure v1

Status: design only; this PR launches no RTX process. There is deliberately no clock deadline, overnight cutoff, or wall-clock kill time.

## Why this study

RTX already has a strong fixed-panel result in PR104: PQ-to-QB speculative-request latency reductions on the C path were 3.064% for Qwen, 6.174% for SmolLM2, and 2.829% for Llama. PR120–123 later showed that mapping conclusions depend on actual CUDA Graph replay, reference admissibility and the complete cost window. New B570 evidence is a useful warning: a real q2 request can preserve the reference and reduce target-verification wall time while the full QB/PQ request-panel benefit remains below the practical screen and draft economics remain unfavorable.

The RTX closure study asks whether the already-qualified RTX path retains its layout benefit, and what the full speculative-service cost is when real q>1 execution, endpoint/state correctness, identical PQ controls and target-only economics are measured together. This is finite-panel platform closure, not unseen-input population confirmation or an accelerator proposal.

## B570 series review (PR131–135)

- PR131: a narrow GQA admission/dispatch repair failed exact AV reference at key512/q2; 7,160/8,192 AV values differed, maximum absolute difference about 1.22e-9. It correctly stopped before timing.
- PR132: preserving the original noncontiguous AV reduction path with zero V batch stride passed all six synthetic key256/512 × q1/2/4 coordinates byte-for-byte. Operator qualification only.
- PR133: real Qwen3-8B Q8_0 + Qwen3-0.6B Q8_0 speculative q2/key256/GQA32:8 ran on all 36 target layers and preserved endpoint, logits and state traces. Its initial cost pilot had a 5.123 s discrepancy between identical PQ controls, making the apparent aggregate gain unreliable.
- PR134: four-input formal panel, 64 measured requests, exact endpoint/logit/state qualification. QB/dual-PQ service ratio 0.995144 (0.4856% reduction), below the registered 2% screen; QB/target-only service ratio 2.619763. Target verification was about 7.33% faster, but draft prefill/decode cost was about 12.367 s per request.
- PR135: draft context thread parameter 8→1, 64 measured requests, all 346 candidate logits vectors preserved. DRAFT1/dual-baseline service ratio 1.003994 (0.3993% slower). Source inspection found one-task GET_ROWS/SET_ROWS and graph-plan worker clamping, so the parameter change does not prove fewer workers ran.

B570 does not predict RTX results. It tells us not to reopen the same QH/padding micrographs or treat phase-time deltas as physical bottlenecks.

## Design principles

- Reuse the exact qualified RTX runtime/model path and previously exposed inputs; never port a B570 patch.
- Keep historical references, failures and ledgers immutable. If the exact reference cannot be tied to the selected inputs and runtime, stop and register a new prospective reference rather than retroactively replacing the old one.
- Use dual identical PQ arms, target-only R, and QB. Separate the QB-versus-PQ layout effect from whether speculation repays draft cost.
- Measure complete fresh-context service as primary; keep request-only and phase windows secondary.
- No actor, RTL, PPA, new accelerator, QH, padding, selector or broad counter sweep in this study.
- Register RTX-specific accounting before execution. B570 cumulative charges do not transfer to RTX.

## Files

- EXPERIMENT_PLAN.md: gates, arms, measures and stop criteria.
- PREREGISTRATION_TEMPLATE.json: fields to freeze before the first native request.
- RUNBOOK.md: execution order and evidence package.

The plan is complete when every gate has a documented PASS, FAIL, BLOCKED or NOT_RUN disposition. Time of day is not a scientific stopping condition.
