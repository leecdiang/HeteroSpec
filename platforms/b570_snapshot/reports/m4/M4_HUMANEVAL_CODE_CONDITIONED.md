# M4 HumanEval Code-Conditioned Validation

## Decision

**M4 CODE-CONDITIONED PROFITABLE REGIME = CONFIRMED**

This is a separate preregistered workload-conditioned study. It does not
replace or pool with the representative Spec-Bench 24Q result (0.842x). Thirty
HumanEval IDs were sampled uniformly from the canonical 164-task ID space and
committed before prompt download or inspection. The fixed primary comparison
used Qwen3-8B Q8_0, Qwen3-0.6B Q8_0, llama.cpp Metal, greedy decoding,
`k=2`, batch one, a 128-token cap, and three randomized paired repetitions.

| Condition | Prompt geomean speedup | 95% prompt-bootstrap CI | Faster prompts | Exact pairs | Mean acceptance | Accepted/round |
|---|---:|---:|---:|---:|---:|---:|
| Fixed `k=2` (primary) | **1.387x** | **[1.351, 1.422]** | **30/30** | **90/90** | 90.1% | 1.798 |
| `k=2`, `p_min=0.8` | 1.362x | [1.315, 1.409] | 30/30 | 90/90 | 94.8% | 1.819 |
| `k=2`, `p_min=0.9` | **1.396x** | [1.352, 1.439] | 30/30 | 90/90 | 96.5% | 1.816 |

The primary fixed-`k=2` result meets the preregistered speed and correctness
criteria. Every selected prompt is retained; no acceptance- or speed-based
post-selection was performed. Exactness means identical greedy token IDs
between paired baseline and speculative generations, not HumanEval functional
correctness. Generated code was not executed.

## Energy and memory

An energy-efficiency ratio above one favors speculation.

| Condition | Package efficiency ratio | 95% prompt-bootstrap CI | Prompts more efficient |
|---|---:|---:|---:|
| Fixed `k=2` | 1.013x | [0.990, 1.034] | 21/30 |
| `k=2`, `p_min=0.8` | 1.014x | [0.985, 1.042] | 18/30 |
| `k=2`, `p_min=0.9` | **1.041x** | **[1.018, 1.065]** | 22/30 |

Fixed `k=2` has a favorable energy point estimate, but its interval crosses
one and should be described as energy-neutral. The registered `p_min=0.9`
secondary condition shows a modest, statistically separated package-energy
improvement, while its speed advantage over fixed `k=2` is only about 0.6%
and is not treated as a material speed gain. The composite memory gate recorded
348 PASS, 12 WARN, and 0 FAIL runs.

## Reproducibility and provenance

- Preregistration: `benchmarks/m4_code_conditioned_30q/preregistration.json`
- Frozen prompts: `artifacts/m4_humaneval_code_conditioned/humaneval_*.txt`
- Authoritative run record: `artifacts/m4_humaneval_code_conditioned/results.json`
- Authoritative raw power trace: `artifacts/m4_humaneval_code_conditioned/telemetry.csv`
- Prompt-level table: `analysis/m4_humaneval_prompt_summary.csv`
- Machine-readable summary: `analysis/m4_humaneval_summary.json`
- Analysis: `scripts/summarize_m4_humaneval.py`
- Archive checksums and runtime metadata:
  `artifacts/m4_humaneval_code_conditioned/manifest.json`

The HumanEval source is pinned to commit
`6d43fb980f9fee3c892a914eda09951f772ad10d`; the compressed dataset SHA-256
stored in the run is
`b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef`.
The source dataset itself is not vendored. The run record contains local model
paths for audit fidelity; model weights are intentionally excluded from Git.

## Interpretation

The representative and conditioned conclusions coexist:

- Representative frozen Spec-Bench 24Q: fixed `k=2` is negative at 0.842x.
- Predeclared code workload: fixed `k=2` is positive at 1.387x.

Therefore speculation is not generally profitable on this M4 configuration,
but a reproducible profitable regime exists for structurally predictable code
generation with high draft acceptance.
