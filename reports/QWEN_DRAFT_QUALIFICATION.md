# Qwen3-0.6B Draft Device Qualification

> Update (2026-09-05): the original asymmetric INT4 IR remains disqualified on NPU, but a separately exported symmetric INT4 NPU artifact has passed bounded NPU compilation and 30-run generation qualification. See `reports/NPU_QWEN_QUALIFICATION.md`. CPU/iGPU results in this report are unchanged.

- Formal measured runs: 30/30
- Matrix complete: PASS
- ITT run markers: CPU 15/15; GPU.0 15/15
- Identical prompt token hashes across devices: PASS
- Identical greedy output token hashes across devices: PASS
- Invalidated preliminary runs excluded: 2
- NPU: FAIL qualification (real frozen INT4 IR compile failure; no fallback and no alternate IR)

## Aggregate results

| Device | Context | TTFT mean ms | TPOT mean ms | Throughput tok/s | Completion mean ms |
|---|---:|---:|---:|---:|---:|
| CPU | 512 | 17.74 | 17.75 | 56.33 | 2272.55 |
| CPU | 2048 | 21.23 | 21.01 | 47.59 | 2690.03 |
| CPU | 8192 | 33.49 | 33.34 | 29.99 | 4268.33 |
| GPU.0 | 512 | 14.12 | 13.32 | 75.07 | 1705.99 |
| GPU.0 | 2048 | 17.09 | 16.00 | 62.50 | 2049.43 |
| GPU.0 | 8192 | 22.42 | 21.21 | 47.15 | 2716.31 |

## Decision

CPU and Intel GPU.0 qualify for subsequent Qwen draft-device experiments. NPU is excluded under the frozen-artifact fairness rule. Intel package telemetry and device activity traces were captured; independent Intel GPU/NPU power domains remain unavailable as documented at Gate 0.
