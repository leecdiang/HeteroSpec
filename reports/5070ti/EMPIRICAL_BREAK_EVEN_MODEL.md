# Empirical Break-even Model

## Result

Under the measured custom CPU/OpenVINO → RTX harness, no finite break-even target latency is predicted for `k=1`, `k=2`, or `k=4` when target verification cost scales proportionally with target autoregressive latency. The searched range was 30–600 ms/token; none of 2,000 question-level bootstrap resamples crossed 1.0.

| k | Observed geomean at 8B | Predicted speedup at 600 ms/token | Asymptotic upper bound |
|---:|---:|---:|---:|
| 1 | 0.505x | 0.622x | 0.668x |
| 2 | 0.463x | 0.579x | 0.624x |
| 4 | 0.354x | 0.448x | 0.484x |

The asymptotic bound is below one because measured target verification time per committed output already exceeds paired baseline decoding time, before draft and orchestration costs are added. Target scaling alone therefore cannot make this particular harness break even.

## Empirical model

For each of the 60 questions and each frozen `k`, the measured speculative time is decomposed as:

```text
T_spec = T_draft + T_verify + T_residual
```

where residual is the observed wall time not attributed to instrumented draft or target calls. For a hypothetical target latency `L`, relative to the measured Qwen3-8B latency `L0 = 60.16 ms/token`:

```text
T_baseline(L) = T_baseline(L0) × L/L0
T_spec(L) = T_draft + T_residual + T_verify(L0) × L/L0
speedup(L) = T_baseline(L) / T_spec(L)
```

Acceptance, committed-token behavior, draft cost, and residual are frozen at their measured question-level values. Confidence bands resample whole questions, not individual verification rounds, preserving within-question dependence.

## Interpretation boundary

This is a characterization of the current custom harness. It does not assert that every speculative implementation has the same verification scaling. The 8B Transformers-native control reaching approximately 1.015x demonstrates that integrated assistant KV caching and scheduling can change the cost structure materially. Consequently, “no finite break-even” means no target-size-only rescue for the measured custom path—not a universal impossibility result.

The observed Qwen3-14B CPU-assisted result (0.718x with only 8/12 exact matches) is retained as an external diagnostic check, but is not used to fit this correctness-qualified 60Q model.

## Artifacts

- `analysis/break_even_observations.csv`
- `analysis/break_even_curve.csv`
- `analysis/break_even_thresholds.csv`
- `analysis/break_even_summary.json`
- `reports/figures/figure6_empirical_break_even_curve.png`
- `reports/figures/figure6_empirical_break_even_curve.pdf`
