# B570 Verification Mechanism — Formal v2 Closeout

**Status: NOT RUN**. Under preregistration v2, V2 runs only after an exact correctness PASS and is a target-forward mechanism proxy, never end-to-end speedup.

| context n | path | PP1 median ms | PP2 median ms | V2 ratio |
|---:|---|---:|---:|---:|
| — | — | — | — | NOT RUN |

Primary gate value: `V2_exact(512) = NOT RUN`. Secondary: `V2_exact(2048) = NOT RUN`. Each valid cell contains 20 repetitions; raw samples, means, standard deviations and CVs are preserved in the processed JSON. Cell-level telemetry covers the whole combined PP1/PP2 process and is diagnostic, not per-operation energy.

## Post-gate diagnostic extension (diagnostic-v1-20260912-170834)

The original formal correctness result remains **FAIL** and unchanged. A later explicitly post-hoc diagnostic extension measured frozen HumanEval30 prevalence and raw mechanisms; it cannot rescue or replace the gate. See `B570_DIAGNOSTIC_EXTENSION.md`.

The post-gate fast-path mechanism values are `V2_raw(512)=1.2426` and `V2_raw(2048)=1.6373`. A preregistered serialized fallback passed its six-prompt correctness probe (18/18 exact), but its subsequent V2 observations overlap or cannot be separated from a ToDesk reconnection; `2.0352` and `2.0177` are retained as remote-contaminated raw provenance, not admissible V2_exact.
