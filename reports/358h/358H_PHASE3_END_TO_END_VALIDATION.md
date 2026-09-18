# 358H Phase-3 end-to-end validation

## Result

**COMPLETE — correctness-admissible, not profitable.** The frozen heterogeneous OpenVINO-draft / llama.cpp-Vulkan target system passed every paired greedy token-ID comparison, but neither draft device accelerated the frozen HumanEval30 workload. The primary metric is post-prefill decode end-to-end time, not whole-request user-perceived latency.

| Path | Exact pairs | Exact prompts | GM speedup (95% prompt-bootstrap CI) | Median prompt speedup | Faster prompts |
|---|---:|---:|---:|---:|---:|
| CPU draft k=2 | 90/90 | 30/30 | 0.734x [0.693, 0.771] | 0.772x | 0/30 |
| NPU draft k=2 | 90/90 | 30/30 | 0.352x [0.333, 0.369] | 0.368x | 0/30 |

The Stage-A gate also passed: CPU 18/18 and NPU 18/18 exact pairs. There were no mismatches, no fallback claim, and no post-data parameter changes.

## Frozen workload and binding

- HumanEval30, three paired repetitions per task; 90 shared target-only baselines, 90 CPU-draft observations, and 90 NPU-draft observations.
- Greedy Qwen3-8B Q8_0 target on explicit llama.cpp b10839 Vulkan0; 37/37 model layers and 36/36 KV layers on Vulkan0 in each campaign session log.
- Frozen Qwen3-0.6B symmetric INT4 OpenVINO IR. CPU/NPU placement is supported by the frozen explicit-device compilation and cache-binding qualification evidence; OpenVINO GenAI's LLMPipeline does not expose `EXECUTION_DEVICES` for every formal observation.
- k=2, output cap 128, prompt prefill excluded from all paired primary timing boundaries.

## Performance

| Path | Baseline tok/s | Speculative tok/s | Baseline ms/token | Speculative ms/token |
|---|---:|---:|---:|---:|
| CPU draft k=2 | 13.365 | 9.658 | 74.825 | 103.540 |
| NPU draft k=2 | 13.365 | 4.647 | 74.825 | 215.186 |

The estimation unit is the HumanEval prompt: each prompt's three paired speedups is reduced to its median, and the geometric mean is bootstrapped over 30 prompts (10,000 resamples, seed 20260919).

HumanEval functional execution/pass@k was not evaluated. Correctness in this report means generated token-ID equality with the target-only baseline.

## Acceptance and committed work

| Path | Weighted acceptance | Mean committed tokens/round C | 0 / 1 / 2 accepted rounds | Bonus / correction rounds |
|---|---:|---:|---:|---:|
| CPU | 75.31% | 2.463 | 954 / 603 / 3120 | 3156 / 1497 |
| NPU | 75.13% | 2.458 | 963 / 612 / 3111 | 3150 / 1509 |

Realized C is above the Phase-2 central assumption of 2 but below the optimistic C=3 regime. High acceptance was therefore insufficient to overcome target verification and draft-state reconstruction.

## Measured system decomposition

Each row is the arithmetic mean of 90 full requests. `draft replay + proposal` is an indivisible synchronous OpenVINO LLMPipeline call: it reconstructs the committed prefix and produces the proposal, so replay-only and proposal-only values are not available without changing the measured system.

| Path | Total ms/request | Draft replay + proposal | Target verification | Residual |
|---|---:|---:|---:|---:|
| CPU | 13253.13 | 1673.51 (12.63%) | 11574.81 (87.34%) | 4.81 (0.04%) |
| NPU | 27543.78 | 16071.08 (58.35%) | 11467.64 (41.63%) | 5.06 (0.02%) |

The target verification tax is substantial for both paths. On NPU, complete committed-prefix replay plus proposal becomes the dominant cost; it erases the isolated NPU draft throughput advantage. The tiny residual does not support a claim that Python handoff is the primary mechanism on this implementation.

## Phase-2 prediction validation

Phase 2 predicted BORDERLINE results under a favorable zero-overhead model: CPU central values ranged from about 0.756x to 0.904x and NPU from 0.840x to 0.906x. Phase 3 measures the previously missing real-system costs. The observed CPU 0.734x is near the pessimistic end of the CPU prediction envelope; NPU 0.352x is far below its favorable bound because the real prefix-replay subsystem cost is large. This supports H2: target verification plus state/runtime overhead erases the NPU compute gain in the qualified system.

## Energy

No end-to-end energy claim is made. CPU package energy was qualified only for Phase-1 draft-only windows; it is not a whole-system or end-to-end Phase-3 measure. NPU end-to-end energy remains **NOT_ADMISSIBLE**.

## Evidence

- Processed summary: `analysis/358h_phase3_summary.json`.
- Per-prompt and per-round records: `analysis/358h_phase3_prompt_summary.csv` and `analysis/358h_phase3_rounds.csv`.
- Authoritative raw archive: `artifacts/358h_threshold_validation/phase3-final-20260918-144458/`.
- Formal host-state, interaction, randomization, and terminology disclosure: `reports/358h/358H_FORMAL_EXECUTION_AMENDMENT.md`.
- Byte-complete committed recovery artifact: `artifacts/358h_threshold_validation/phase3-final-20260918-144458/358h_phase3_complete_evidence.tar.gz`.

