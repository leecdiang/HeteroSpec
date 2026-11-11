# Qwen3-0.6B Symmetric-INT4 Draft Device Matrix

## Result

**PASS WITH NUMERICAL REPRODUCIBILITY LIMITATION.** The same NPU-compatible symmetric-INT4 OpenVINO artifact completed the bounded matrix on explicitly selected CPU, GPU.0, and NPU devices. No `AUTO` or `MULTI` device selection was used.

This is a qualification observation, not an end-to-end speculative-decoding benchmark. No Intel power-domain comparison was made in this run.

## Frozen test

- Model: `models\qwen3-0.6b-int4-sym-npu-v2`
- OpenVINO: 2026.3.1
- Inputs: identical tokenized prompts of exactly 32, 64, and 128 tokens
- Output: 32 greedy tokens, EOS ignored
- Per cell: 2 warm-ups followed by 5 measured repetitions
- NPU compiler: `PREFER_PLUGIN`
- NPU static maximum prompt length: 128

## Timing and repeatability

| Device | Input tokens | Successful | Mean seconds | Output tok/s | Unique hashes |
|---|---:|---:|---:|---:|---:|
| CPU | 32 | 5/5 | 0.3345 | 95.67 | 2 |
| CPU | 64 | 5/5 | 0.3389 | 94.41 | 1 |
| CPU | 128 | 5/5 | 0.3438 | 93.08 | 1 |
| GPU.0 | 32 | 5/5 | 0.4757 | 67.27 | 2 |
| GPU.0 | 64 | 5/5 | 0.4816 | 66.44 | 1 |
| GPU.0 | 128 | 5/5 | 0.4937 | 64.82 | 5 |
| NPU | 32 | 5/5 | 1.0171 | 31.46 | 1 |
| NPU | 64 | 5/5 | 1.0173 | 31.46 | 1 |
| NPU | 128 | 5/5 | 1.0174 | 31.45 | 1 |

These throughput figures include only generation-call wall time. They exclude one-time model compilation and are not power-normalized.

## Cross-device correctness

- At 64 input tokens, all 15 measured runs across CPU, GPU.0, and NPU produced the same output-token hash.
- At 128 input tokens, CPU and NPU agreed exactly and were deterministic. GPU.0 produced five distinct hashes; divergence began at generated-token index 9 or 22.
- At 32 input tokens, NPU was deterministic. One of five CPU outputs matched NPU; the other four diverged at generated-token index 21. GPU.0 produced two other continuations, diverging at index 16 or 17.
- Every run returned exactly 32 tokens. The variation is therefore numerical greedy-token selection, not truncation, fallback, or execution failure.

## Device decision

- **Primary draft candidate: CPU.** It is the fastest device in this symmetric-artifact matrix and is stable for 64/128-token inputs. The isolated 32-token split must be tolerated by correctness testing at the speculative verifier boundary, not assumed away.
- **Secondary qualification candidate: NPU.** It is fully deterministic in this bounded matrix and agrees with CPU at 64/128 tokens, but is about 3x slower than CPU for this 32-token generation workload. NPU remains useful for heterogeneous feasibility and energy studies; it is not presently the latency-leading draft device.
- **GPU.0: qualified for execution, not preferred for strict reproducibility.** It is slower than CPU here and shows the largest greedy-output variability.

Speculative decoding remains exact because the RTX target must verify every draft token. Draft-device output equality must never be used as a substitute for target-side verification.

## Evidence

- `logs\phase1-sym-matrix-cpu-20260905.json`
- `logs\phase1-sym-matrix-gpu0-20260905.json`
- `logs\phase1-sym-matrix-npu-20260905.json`
- `scripts\phase1_sym_draft_matrix.py`

The two early CPU development attempts that failed before matrix completion are excluded; the final JSON was overwritten only by the complete successful run and carries `status: PASS`.
