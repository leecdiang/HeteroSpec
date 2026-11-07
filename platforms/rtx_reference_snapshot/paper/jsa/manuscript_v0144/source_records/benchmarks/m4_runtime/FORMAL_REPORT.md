# M4 prospective runtime profitability-control study

Formal attempt: `unattended-20260924t125921z-formal`. Selected policy: `E8_M000`.
Direct token-ID pairs: 180 per speculative condition; mismatches: 0.
Energy: NOT_CLAIMED.

## Provenance correction

The frozen runner recorded the build-manifest SHA-256 in the freeze-hash fields because its `frozen()` function returned the last loop path. The original markers and measurements remain unchanged. This post-measurement audit verified the actual calibration-freeze file against the clean commit at formal start, then rechecked the frozen source, models, policy selection, qualification, and complete raw attempts. The formulas below are unchanged from the frozen analysis script. See `FORMAL_ANALYSIS.json` for both digests and the audit details.

## Primary results

| Measure | Estimate | 95% prompt bootstrap CI |
| --- | ---: | ---: |
| Target / guard geometric mean | 1.3114 | 1.2487–1.3787 |
| Target / fixed k=2 geometric mean | 1.3469 | 1.2867–1.4088 |
| Guard / offline oracle geometric mean | 1.0278 | 1.0137–1.0446 |

Median additive oracle regret: 9.99 ms; p90: 822.22 ms.

## Control trace

Fallback fraction: 0.306; speculative committed-token fraction: 0.703; accepted draft fraction: 0.814.
Measured guard and transition work: 0.12 ms total (0.0000% of guard latency).

## Prospective strata

| Stratum | Prompts | Target / guard | Guard / oracle |
| --- | ---: | ---: | ---: |
| HumanEval | 30 | 1.5547 | 1.0099 |
| HumanEval:code_completion | 30 | 1.5547 | 1.0099 |
| Spec-Bench | 30 | 1.1062 | 1.0460 |
| Spec-Bench:coding | 1 | 1.4409 | 1.0091 |
| Spec-Bench:humanities | 1 | 1.0076 | 1.0719 |
| Spec-Bench:math | 2 | 1.4384 | 0.9936 |
| Spec-Bench:math_reasoning | 5 | 1.2506 | 1.0581 |
| Spec-Bench:qa | 3 | 1.0519 | 1.0397 |
| Spec-Bench:rag | 7 | 1.0022 | 1.0816 |
| Spec-Bench:roleplay | 1 | 0.9971 | 1.0029 |
| Spec-Bench:stem | 1 | 1.1914 | 1.0010 |
| Spec-Bench:summarization | 5 | 1.0156 | 1.0454 |
| Spec-Bench:translation | 4 | 1.1029 | 1.0280 |

Bootstrap resampled prompts 10,000 times with seed 20260924; repetitions were reduced to per-prompt medians before resampling. The offline oracle is descriptive and was not available to the policy.

