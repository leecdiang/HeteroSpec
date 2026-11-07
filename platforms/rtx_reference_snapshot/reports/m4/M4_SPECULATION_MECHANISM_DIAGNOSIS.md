# M4 Speculative-Decoding Mechanism Diagnosis

## Conclusion

The evidence does not support attributing the M4 result to unified memory
alone. It supports a narrower mechanism: llama.cpp can verify a two-token
causal batch for almost the cost of one target decode, an idle resident draft
adds negligible interference, and profitability is dominated by the shape of
accepted runs. The original 12Q `k=2` result remains a positive signal, but its
1.350x point estimate is not promoted as a replicated effect size.

## Target verification microbenchmark

The target was prefixed once, then candidate KV was rolled back after each
measurement. Every timed `llama_decode` was followed by `llama_synchronize`.
Seven randomized repetitions were collected per cell.

| Prefix tokens | T_decode(1) | T_verify(2) / V2 | T_verify(4) / V4 | T_verify(6) / V6 |
|---:|---:|---:|---:|---:|
| 512 | 100.87 ms | 103.11 ms / **1.022** | 156.48 ms / 1.551 | 230.08 ms / 2.281 |
| 2,048 | 99.97 ms | 107.58 ms / **1.076** | 163.03 ms / 1.631 | 231.66 ms / 2.317 |
| 8,192 | 115.49 ms | 119.22 ms / **1.032** | 176.54 ms / 1.529 | 265.78 ms / 2.301 |

This is the clearest explanation for the `k=2` sweet spot. Two-token
verification costs only 1.02--1.08 single-token decodes across the tested
prefixes. Width four and six no longer have this near-free batching property.

## Cross-platform cost view

| Metric | 275HX CPU -> RTX custom | M4 llama.cpp Metal `k=2` |
|---|---:|---:|
| Target baseline | 60.16 ms/token | 83.03 ms/token |
| Draft generation | 36.80 ms/drafted token | 32.31 ms/drafted token |
| Verification | 130.42 ms/round (`k=1`) | 103.11 ms/round (`k=2`, 512 prefix) |
| Weighted acceptance | 66.7% | 61.1% |
| Accepted tokens/round | 0.667 | 1.209 |
| 12Q speedup | 0.733x | 1.350x initial decision run |

The columns are diagnostic rather than a controlled hardware-only comparison:
runtime, quantization, `k`, memory architecture and implementation all differ.
The useful result is that M4 combines lower verification cost with more than
one accepted token per verification round. The follow-up decomposition's
runtime/KV residual is not reported as a stable scalar because its session
timing did not reproduce the original 12Q magnitude.

## Draft residency and bandwidth contention

Five randomized repetitions compared target-only decode with the same target
plus an idle loaded draft (`--spec-type none`). Median 64-token decode times
were 5,211.56 and 5,245.31 ms respectively: a **+0.65%** resident-draft tax.
Thus model residency alone creates little measurable contention in this bounded
configuration. This does not prove that active target and draft kernels never
compete for unified-memory bandwidth.

## Acceptance crossover

The built-in synthetic acceptance control was run at `k=2`, three randomized
repetitions per point, on one fixed 64-token prompt.

| Requested setting | Observed acceptance | Accepted/round | Median speedup |
|---:|---:|---:|---:|
| 20% | 10.3% | 0.205 | 0.595x |
| 40% | 24.3% | 0.486 | 0.600x |
| 60% | 57.1% | 1.143 | 0.809x |
| 80% | 88.6% | 1.773 | 0.978x |
| 100% | 100.0% | 2.000 | 1.036x |

For uniformly synthetic acceptance, crossover is near the extreme high end.
This curve must not be substituted for real-workload behavior: real accepted
tokens arrive in structured contiguous runs and draft/target execution paths
are content-dependent.

## Workload dependence and reproducibility

Across the original 12Q `k=2` run, acceptance versus speedup had Pearson
correlation 0.893 and Spearman correlation 0.923. A bounded three-repeat paired
check confirmed the direction on two diagnostic prompts:

| Question | Acceptance | Paired speedups | Geomean |
|---:|---:|---|---:|
| 438 (high acceptance) | 83.0% | 1.154x, 1.241x, 1.116x | **1.169x** |
| 395 (low acceptance) | 35.6% | 0.707x, 0.712x, 0.693x | **0.704x** |

All repetitions remained exact. This validates the mechanism direction but
also shows that the single-run 12Q effect size is session-sensitive. The safe
claim is: M4 + llama.cpp has a real profitable region for high-acceptance
workloads, while low-acceptance workloads remain clearly negative.

## Research decision

- Keep `k=2` as the only profitable candidate.
- Describe 1.350x as the initial 12Q positive signal, not a replicated mean.
- Attribute the positive region to cheap two-token verification plus structured
  acceptance and tight runtime state reuse; treat unified memory as an enabling
  condition, not an isolated cause.
- The approved full paired replication is reported in
  `M4_CONFIRMATORY_VALIDATION.md`; it did not generalize the positive signal.
  The M4 platform is closed and 60Q is not authorized.
