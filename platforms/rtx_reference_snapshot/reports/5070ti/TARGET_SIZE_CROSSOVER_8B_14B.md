# Target-Size Crossover: Qwen3-8B vs Qwen3-14B

## Decision

**STOP the traditional draft-model speculation branch on the current 12 GB Windows platform.** The 14B target is substantially slower than 8B and improves the theoretical draft/target cost ratio, but the tested mature CPU-assisted path remains slower on every diagnostic question and fails exact-output equality on 4/12 questions. A 20B target and the 420-question holdout are not justified.

## Frozen feasibility protocol

- Model family: Qwen3
- Targets: 8B and 14B
- Target linear weights: bitsandbytes NF4 with double quantization
- Quantized linear compute: FP32
- Non-quantized layers: BF16
- Attention: eager
- Prompt/output: 128 / 256 tokens
- Repetitions: 3
- CUDA allocation limit: 85% of physical VRAM
- No CPU offload or silent fallback

The BF16 non-quantized-layer protocol was used for both sizes because the prior all-FP32 14B load could not fit. At an 85% allocation cap, it failed before allocation while requesting 10.71 GiB. At 91%, it reached approximately 75% of model loading, allocated 10.49 GiB, then safely failed while requesting another 340 MiB; NVML peaked at 11,550.1 MB.

## Baseline crossover

| Target | Median TTFT | Median decode | Sustained throughput | 256-token end-to-end | CUDA peak | NVML peak |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3-8B | 229.48 ms | 60.16 ms/token | 16.62 tok/s | 16.44 tok/s | 5.905 GiB | 6694.1 MB |
| Qwen3-14B | 423.87 ms | 88.69 ms/token | 11.27 tok/s | 11.11 tok/s | 9.678 GiB | 10646.1 MB |

The 14B target has 1.474x the steady-state token latency of the 8B target. Using the qualified short-burst OpenVINO CPU draft observation of 10.78 ms/token, the simple screening ratio is:

- 8B: `r = 10.78 / 60.16 = 0.179`
- 14B: `r = 10.78 / 88.69 = 0.122`

This confirms that target scaling moves the cost ratio in the desired direction. It does not include verification, scheduling, repeated draft prefill, or KV-management costs.

## 14B assisted diagnostic

RTX-resident 14B plus RTX-resident 0.6B was not attempted because the target alone used 9.68 GiB of CUDA allocation and approximately 10.65 GB by NVML. The assistant was therefore placed on CPU and Transformers native assisted generation was used as the integrated control path (`k=1`, 64-token cap, the same length-selected 12-question diagnostic set).

| Metric | Result |
|---|---:|
| Exact output equality | 8/12 |
| Geometric mean speedup | 0.718x |
| Median speedup | 0.717x |
| Aggregate-time ratio | 0.708x |
| Questions faster than baseline | 0/12 |
| CUDA peak | 9.884 GiB |
| NVML peak | 10734.1 MB |

The result is marked **FAIL_CORRECTNESS**, not PASS. Shape-dependent numerical behavior in the BF16/batched assisted verification path changed tokens on four questions. Timings are retained as diagnostic evidence but cannot be promoted to a correctness-qualified speculative benchmark.

## Interpretation

The 14B target establishes a real size crossover in raw target cost, but not an end-to-end speculative decoding crossover. The consumer GPU is caught between two constraints:

1. All-FP32 14B does not fit safely.
2. The memory-feasible BF16 mixed path permits the baseline but introduces exactness failures under batched assisted verification, while CPU assistance still adds more latency than it saves.

The negative 14B result does not prove that every optimized heterogeneous implementation must fail. A stateful OpenVINO draft integration with persistent KV cache could be a separate systems project. It does show that the currently available native/custom paths do not cross break-even, so expanding to 420 questions or a 20B target would add risk and cost without resolving the blocking mechanisms.

## Evidence

- `logs\phase6-qwen3-8b-bf16-anchor-20260906.json`
- `logs\phase6-qwen3-14b-bf16-feasibility-20260906.json`
- `logs\phase6-qwen3-14b-canary-20260906.json`
- `logs\phase6-qwen3-14b-canary91-20260906.json`
- `logs\phase6-qwen3-14b-native-cpu-assist-12q-20260906.json`
- `env\qwen3-14b-manifest.json`

