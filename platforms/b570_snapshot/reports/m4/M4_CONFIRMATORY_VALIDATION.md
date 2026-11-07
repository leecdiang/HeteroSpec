# M4 Frozen-k Confirmatory Validation

## Final decision

**M4 PLATFORM = CLOSED — INITIAL SIGNAL NOT GENERALIZED**

Twenty-four previously unseen Spec-Bench prompts were frozen before inference,
with four prompts from each of six workload groups. The selection excluded all
prior M4 diagnostic IDs and used no acceptance or speed information. Qwen3-8B
Q8_0 target, Qwen3-0.6B Q8_0 draft, llama.cpp Metal, greedy decoding and `k=2`
were fixed. Each prompt received three randomized paired repetitions.

| Confirmatory metric | Result |
|---|---:|
| Exact paired outputs | **72/72** |
| Prompt-level geomean speedup | **0.842x** |
| Median prompt speedup | 0.846x |
| 95% prompt-bootstrap CI | [0.809, 0.877] |
| Prompts faster | **1/24 (4.2%)** |
| Package-energy improvement ratio | 0.678x |
| Mean package J/output-token, baseline -> k2 | 1.206 -> 1.729 |
| Memory gate | 139 PASS, 5 WARN, 0 FAIL |

An energy-improvement ratio above one would favor speculation. The observed
0.678x ratio means the baseline was more energy-efficient. GPU J/token rose
from 1.146 to 1.226; CPU J/token rose from 0.060 to 0.503. Package is
Silemetry's CPU + GPU + ANE aggregate and excludes its separate DRAM domain.

## Conditional analysis

The post-run strata were fixed by rank tertiles of accepted tokens per
verification round, eight prompts each.

| Tertile | Accepted tokens/round | Geomean speedup | Faster | Energy improvement |
|---|---:|---:|---:|---:|
| Low | 0.875--1.200 | 0.766x | 0/8 | 0.620x |
| Medium | 1.214--1.583 | 0.846x | 0/8 | 0.687x |
| High | 1.583--1.864 | 0.921x | 1/8 | 0.730x |

Higher acceptance consistently reduces the loss, but even the high tertile is
below break-even in both speed and energy. Therefore the new frozen sample does
not confirm a stable profitable region under this always-on policy.

## Predictor analysis

| Predictor | Pearson correlation with speedup |
|---|---:|
| Acceptance rate | 0.804 |
| Accepted tokens/round | **0.809** |
| Draft mean top-1 probability | 0.512 |
| Draft top1--top2 margin | 0.482 |
| Draft truncated entropy | -0.514 |
| Prompt length | -0.278 |

Draft confidence and entropy provide a moderate pre-execution signal, while
observed acceptance is stronger. This supports discussion of a future
selective runtime policy, but no controller is implemented or evaluated here.

## Robustness and limitations

Prompt-level statistics first aggregate the three repetitions, then bootstrap
the 24 prompts with 10,000 resamples using seed `20260907`. Repetition-level
geomean speedups were 0.910x, 0.819x and 0.801x, showing thermal/session drift
during the long fanless run. Adjacent randomized pairing limits but does not
eliminate this effect. `pmset` recorded no OS thermal or performance warning.

All correctness comparisons passed, and no memory FAIL occurred. Five WARN
runs had limited swap/pressure movement without throttling. Silemetry uses
private IOReport/AppleSMC channels, so energy applies to this fixed host/build.

The initial root-cause 12Q result remains a useful discovery observation, not a
confirmatory estimate. No further M4 model, runtime, `k`, algorithm or workload
expansion is justified by the predeclared stop rule.
