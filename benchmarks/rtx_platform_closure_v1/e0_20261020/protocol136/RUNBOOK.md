# RTX platform closure v1 — execution runbook

This runbook is gate-driven and has no clock deadline. It does not authorize execution by itself; the executing agent must confirm the user's authorization, machine identity and budget before launching any native process.

## Before any process

1. Read the latest RTX-specific ledger and reconcile it with all prior RTX experiment roots. Do not use the B570 ledger or its remaining allowance.
2. Recover the exact PR104 qualified model/runtime/source/reference identity. Hash the executable, relevant DLLs, model files, tokenizer, input manifest, environment and driver identity.
3. Select four already-exposed RTX input IDs from the frozen archive and record why each is included. Do not select based on new results.
4. Fill PREREGISTRATION_TEMPLATE.json into a complete PREREGISTRATION.json, including a unique UUID, exact source/model identities, output cap, order schedule, budget reservation and analysis implementation. Commit the design and SHA256 manifest before the first native request.
5. If an exact historical reference cannot be bound, stop and document it. A newly generated reference must have a new identity and may not repair old failures retroactively.

## Qualification before timing

1. Execute R, PQ and QB on each fixed input with complete raw capture outside timing.
2. Check complete native endpoint, every decision-relevant logits vector, state/cycle trace and actual q/key/head/stride/mask/device geometry.
3. Stop a candidate on first mismatch or unsupported shape. Preserve all bytes, stderr/stdout and receipts. Do not run timing for an unqualified candidate.
4. Only after every required candidate passes, run the frozen 4-session × 4-input × 4-arm clean panel with 64 measured requests and 64 separately charged warmups. Respect the committed order schedule. No retries or outlier deletion.

## Timing and observer discipline

- The primary timer covers fresh context/graph creation through completed output/state handling, synchronization and context teardown.
- Model load is separately recorded; request-only is a secondary window.
- No node observer, raw vector write, or post-request byte comparison inside the primary timer.
- If profiling is needed, perform it only after clean timing and calibrate clean/profile/clean. Reject incomplete terminal intervals, missing output projections, inactive-node labels, or observer overhead outside the frozen gate.
- Phase wall intervals and summed kernel durations are not critical-path fractions. Do not infer physical bandwidth/compute limits from operator names.

## Completion and result PR

Publish every input, arm, session, warmup, failure and stop. Include the raw archive or immutable raw-location record, complete hash manifest, analysis code/output, budget/process receipts and an addendum explaining both the layout effect and target-only economics. State whether q>1 was actually observed.

Close the finite platform study only after E0–E2 each have a recorded disposition and E3 is completed or explicitly not needed/unavailable. If an external resource or engineering limit interrupts execution, label it as such and leave scientific gates unresolved. Do not impose a time-of-day cutoff, silently drop a gate, or claim overnight completion as a result.
