# 358H telemetry-gate audit

Status: **AUDITED — THE 1% RULE QUALIFIES ENERGY CLAIMS, NOT THE PRIMARY LATENCY QUESTION**

Scope: pre-formal protocol audit only. No formal benchmark result was inspected or collected.

## Finding

The one-percent telemetry-overhead limit was first committed for the Arc B570 board-energy qualification in commit `b9d65e6696d5c018ef1ccb28052e37e16fe02da3` on 2026-09-11. The original 358H onboarding and preregistration v1 were added later in commit `a76322ba38f33b455e81959ba93516bd4041053b` on 2026-09-13. They do not contain a one-percent limit.

The original 358H Phase-0 contract requires the telemetry boundary to be documented and explicitly says to state a limitation when component energy cannot be isolated. Phase 1 lists `component_power_or_energy_if_valid`; Phase 3 lists `energy_per_output_token_if_sensor_boundary_is_valid`. The primary question is draft-device latency and the predictive break-even boundary. Energy is a secondary/conditional outcome.

The one-percent limit entered the 358H materials only in the local, not-yet-committed `preregistration_v2.json` and `358H_POWER_TELEMETRY_PROTOCOL.md`, where it was explicitly described as reusing the B570 energy protocol. It is therefore a conservative 358H **energy-admissibility gate**, not a historical hard gate for the core latency study.

## Answers

1. **Earliest definition:** B570 board-power qualification, commit `b9d65e6696d5c018ef1ccb28052e37e16fe02da3`, not the original 358H protocol.
2. **Meaning:** option (b), an energy-claim qualification rule, later reused as option (c), a conservative 358H engineering gate. It is not option (a) for latency-only Phase 0.
3. **Is energy mandatory primary outcome?** No. The runbook labels latency/draft cost as the primary question and energy as part of the secondary end-to-end question when valid.
4. **Can Phase 1 answer threshold validation from latency?** Yes. Phase 2 consumes `T_d(k)` plus frozen `T_b`, correctness-admissible `V_2`, and `T_x`; no energy term appears in the break-even equation.
5. **Logical conflict?** Yes. Treating failed in-band telemetry as a hard failure for all Phase-1 latency contradicts the original `if valid` language. The correct repair is to separate the primary latency track from the conditional energy track before formal data, not to lower the one-percent threshold.

## Decision

- Keep the one-percent rule unchanged for admitting any telemetry-on timing or energy result.
- Authorize Phase-0 core platform qualification independently of energy qualification when model provenance, explicit binding, power state, clocks, and functional smoke pass.
- Run the primary latency/break-even track with telemetry OFF.
- Admit an energy track only for a sensor/configuration that independently passes its frozen observer-overhead and physical-boundary qualification.
- If CPU Package energy remains unqualified, report `CPU energy: NOT ADMISSIBLE / NOT REPORTED`; do not infer it from TDP, percentages, or another domain.
- NPU energy must not be presented as a symmetric CPU-vs-NPU comparison unless both paths share a qualified and comparable boundary.

## Evidence

- `docs/358H_RUNBOOK.md` on repository main `7327495d181c91844cf7d031cfcb7384433b2089`: primary latency question; Phase-0 limitation rule; `component power/energy if valid`.
- `benchmarks/358h_threshold_validation/preregistration_v1.json` at commit `a76322ba38f33b455e81959ba93516bd4041053b`: requires only a documented telemetry boundary in Phase 0 and makes energy conditional.
- `paper/notes/VERIFICATION_AMORTIZATION_FRAMEWORK.md`: the predictive equation contains latency/cost terms, not energy.
- `reports/b570/B570_ENERGY_TELEMETRY_QUALIFICATION.md` at commit `b9d65e6696d5c018ef1ccb28052e37e16fe02da3`: earliest repository evidence of the frozen 1% rule.
- Local `benchmarks/358h_threshold_validation/preregistration_v2.json`: explicitly says the 1% gate reuses B570.

This audit changes measurement architecture before formal data. It does not reinterpret a failed sensor as passing and does not relax 1% to match observed 3–5% results.

