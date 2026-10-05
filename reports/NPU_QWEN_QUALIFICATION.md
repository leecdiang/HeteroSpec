# Qwen3-0.6B Intel NPU Qualification

## Result

**PASS for bounded NPU qualification.** Intel AI Boost executed a purpose-built symmetric INT4 Qwen3-0.6B model through OpenVINO GenAI with the device explicitly set to `NPU`. No `AUTO`, `MULTI`, CPU, or GPU fallback was permitted.

## Platform

- NPU: Intel(R) AI Boost (NPU 3720 class)
- NPU driver: `1005540`
- OpenVINO: `2026.3.1-22476-759c5a6ab8c-releases/2026/3`
- OpenVINO GenAI: `2026.3.1.0`
- Python: 3.11, isolated environment `.venv-npu-lab`

## Model correction

The original `qwen3-0.6b-int4-ov` artifact used `INT4_ASYM`, ratio `0.8`, group size `128`, and failed NPU compilation on a `DequantizeOp`. It remains valid for the CPU/iGPU qualification but is not NPU-legal.

A separate model was exported from the original Qwen3-0.6B weights with:

- Task: `text-generation-with-past`
- Weight format: symmetric INT4
- Group size: `128`
- INT4 ratio: `1.0`
- Backup precision: symmetric INT8
- Output: `models\qwen3-0.6b-int4-sym-npu-v2`
- IR weights: `383,231,325` bytes
- Compression result: 196/197 compressible layers INT4 symmetric; the remaining layer INT8 symmetric

The first export attempt completed quantization but was interrupted by a Windows GBK console encoding error. It is not used. The successful v2 export was run with UTF-8 forced, and the complete log is preserved.

## Runtime gates

| Gate | Result |
|---|---|
| Explicit device `NPU` | PASS |
| `PREFER_PLUGIN` compile, static max prompt 128 | PASS |
| Forced `PLUGIN` compiler | PASS |
| One-token generation | PASS |
| Sixteen-token greedy generation | PASS |
| 30 repeated sixteen-token generations | PASS, 30/30 |
| Deterministic decoded output hash | PASS |

The 30-run output SHA-256 was identical for every repetition:

`6a1a52943e857dfc38e89c84e0202ebc692c9b18976b6a2876421b20315407d2`

For repetitions 2-30, mean generation time was `0.618889 s`, with a range of `0.608903-0.627416 s`. These figures are qualification observations, not formal performance results.

## Scope and decision

The NPU is now qualified to execute this bounded, static Qwen3-0.6B symmetric-INT4 workload. This supersedes the earlier broad statement that Qwen3-0.6B could not compile on the NPU; the precise result is that the asymmetric CPU/iGPU IR cannot compile, while the NPU-specific symmetric IR can.

This does not yet qualify longer prompt shapes, production speculative decoding, NPU energy efficiency, or cross-runtime RTX+NPU performance. Those require a separate controlled qualification matrix.

## Same-artifact device comparison

The same symmetric INT4 artifact and prompt were subsequently run 30 times on each explicitly selected device. The first repetition was treated as cold and excluded from the timing summary below.

| Device | Successful runs | Unique output hashes | Mean steady 16-token time | Range |
|---|---:|---:|---:|---:|
| CPU | 30/30 | 1 | 0.213392 s | 0.202070-0.246122 s |
| GPU.0 | 30/30 | 2 | 0.295835 s | 0.282211-0.369433 s |
| NPU | 30/30 | 1 | 0.618889 s | 0.608903-0.627416 s |

CPU and NPU produced the same hash in every repetition. GPU.0 matched that hash in 29/30 runs; repetition 2 selected a different greedy continuation (`the user is asking` rather than `I need`) at an apparent numerical decision boundary. This is a correctness/stability observation that must be retained. These short fixed-shape timings are qualification observations rather than a formal benchmark, but they show that the NPU is approximately 2.9x slower than the CPU for this particular 16-token test.

## Evidence

- `env/npu-lab-pip-freeze.txt`
- `logs/npu-export-qwen3-0.6b-int4-sym.txt` (failed console-encoding attempt)
- `logs/npu-export-qwen3-0.6b-int4-sym-v2.txt`
- `logs/check_npu_qwen_prefer_plugin.txt`
- `logs/check_npu_qwen_16tokens.txt`
- `logs/check_npu_qwen_30x16.txt`
- `logs/check_npu_qwen_forced_plugin.txt`
- `logs/check_sym_qwen_cpu_30x16_v2.txt`
- `logs/check_sym_qwen_gpu0_30x16_v2.txt`
- `scripts/check_npu_qwen.py`
