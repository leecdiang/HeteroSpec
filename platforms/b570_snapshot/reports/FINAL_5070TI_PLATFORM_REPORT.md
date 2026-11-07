# HeteroSpec-PC: Final RTX 5070 Ti Platform Report

**Platform status: PRIMARY PLATFORM = CLOSED**  
**Closure date: 2026-09-07**

## Executive conclusion

On this Windows 11 consumer AI PC, under the tested Qwen3 model sizes and traditional draft-target speculative decoding, neither heterogeneous CPU drafting nor mature same-GPU assisted generation produced a stable practical win. The custom CPU→RTX path is dominated in both performance and measured component energy. Native RTX→RTX integration removes much of the orchestration penalty, but the formal power run is still slower and consumes more RTX energy per output token. Scaling the target from 8B to 14B improves the draft/target latency ratio, yet does not cross break-even; the 12 GB VRAM capacity boundary appears first.

This is a bounded platform characterization, not the universal claim that heterogeneous speculation is useless.

## 1. Platform

| Component | Frozen configuration |
|---|---|
| OS | Windows 11 Home China 25H2, build 26200.9168 |
| CPU | Intel Core Ultra 9 275HX |
| RAM | 48 GB class (47.4 GiB reported) |
| iGPU | Intel Graphics, driver 32.0.101.8991 |
| NPU | Intel AI Boost, driver 32.0.100.5540, about 13 TOPS |
| dGPU | NVIDIA GeForce RTX 5070 Ti Laptop, 12 GB class |
| NVIDIA driver / CUDA | 616.56 / PyTorch CUDA 12.8 |
| OpenVINO | 2026.3.1 |
| Power / graphics | AC, Balanced accepted by user, OEM Balanced, Hybrid MUX |

Gate 0 passed with telemetry limitation: NVIDIA board power and Intel CPU package power are available; independent Intel iGPU/NPU power domains are unavailable and are not estimated.

## 2. Draft-device characterization

The fair three-device comparison uses the same NPU-compatible symmetric INT4 Qwen3-0.6B artifact, 32 greedy output tokens, two warm-ups and five measurements per cell.

| Device | Input 32 | Input 64 | Input 128 | Decision |
|---|---:|---:|---:|---|
| CPU | 95.67 tok/s | 94.41 tok/s | 93.08 tok/s | Fastest; primary draft |
| Intel GPU.0 | 67.27 tok/s | 66.44 tok/s | 64.82 tok/s | Slower and numerically less stable |
| NPU | 31.46 tok/s | 31.46 tok/s | 31.45 tok/s | Qualified, about 3x slower than CPU |

The NPU-legal static model has a 128-token maximum prompt, so a fair three-device 512/2048/8192 matrix cannot be produced without changing the artifact and invalidating comparability. A separate CPU/iGPU long-context matrix exists for the asymmetric CPU/iGPU artifact:

| Device | 512 TPOT | 2048 TPOT | 8192 TPOT |
|---|---:|---:|---:|
| CPU | 17.75 ms | 21.01 ms | 33.34 ms |
| GPU.0 | 13.32 ms | 16.00 ms | 21.21 ms |

Thus iGPU can outperform CPU for longer batched/persistent generation on a different artifact, while CPU remains fastest for the short, same-artifact proposal workload actually used to select the speculative draft device. The protocol distinction is retained rather than forcing a misleading unified table.

## 3. Main 60-question pilot

| k | Geomean speedup | Acceptance | Faster | Exact |
|---:|---:|---:|---:|---:|
| 1 | 0.51x | 67.2% | 0/60 | 60/60 |
| 2 | 0.46x | 56.3% | 0/60 | 60/60 |
| 4 | 0.35x | 40.7% | 1/60 | 60/60 |
| 6 | 0.30x | 31.5% | 0/60 | 60/60 |
| 8 | 0.25x | 25.4% | 1/60 | 60/60 |

Increasing `k` lowered acceptance and worsened performance. The 420-question holdout was therefore never opened.

## 4. Root cause

| Configuration | Geomean speedup | Faster | Exact | Draft | Verify/decode | Residual |
|---|---:|---:|---:|---:|---:|---:|
| RTX baseline | 1.000x | — | reference | — | 57.75 s | — |
| CPU→RTX custom | 0.733x | 1/12 | 12/12 | 17.45 s | 61.82 s | 5.95 s |
| RTX→RTX custom | 0.611x | 0/12 | 12/12 | 23.66 s | 71.07 s | 6.19 s |
| RTX→RTX native diagnostic | 1.015x | 5/12 | 12/12 | integrated | integrated | integrated |

Cross-device transfer is not the sole cause: placing both models on RTX under the same custom harness is worse because of contention. Repeated draft prefill, verification, Python/KV bookkeeping and cross-runtime scheduling all contribute. Mature native integration removes most custom overhead, but the small diagnostic was only approximately break-even.

## 5. Target-size crossover and capacity boundary

| Target | Decode | Throughput | Draft/target r | Assisted speedup | CUDA peak | NVML peak | Exact |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-8B | 60.16 ms/token | 16.62 tok/s | 0.179 | 0.733x custom | 5.905 GiB target | 6.694 GB target | 12/12 diagnostic |
| Qwen3-14B | 88.69 ms/token | 11.27 tok/s | 0.122 | 0.718x native CPU-assisted | 9.884 GiB assisted | 10.734 GB assisted | 8/12 |

Target latency rose 47.4%, but CPU assistance remained slower. The 14B assisted timing is diagnostic only because four outputs diverged. All-FP32 nonquantized layers did not fit safely; RTX 14B plus RTX draft and 20B were not attempted.

## 6. Empirical break-even

The 60Q question-level model freezes measured draft, acceptance and residual behavior, and scales target verification with target autoregressive latency. With 2,000 question-level bootstrap resamples, no `k=1/2/4` curve crosses 1.0 in 30–600 ms/token.

| k | Predicted at 600 ms/token | Asymptotic upper bound |
|---:|---:|---:|
| 1 | 0.622x | 0.668x |
| 2 | 0.579x | 0.624x |
| 4 | 0.448x | 0.484x |

For the current custom verifier, verification alone is already more expensive per committed token than baseline decode. There is therefore no finite target-size-only break-even under this empirical scaling. This does not apply to a future persistent, tightly integrated implementation.

## 7. Formal component power and energy

The final measurement uses the frozen 12-question set, 64-token cap, one measurement per question/turn, in-process 1 Hz NVML and Intel Unified Telemetry `PKG-PWR`. All native outputs were exact.

| Configuration | Mean tok/s | RTX avg W | RTX J/token | CPU package avg W | CPU package J/token |
|---|---:|---:|---:|---:|---:|
| RTX baseline | 20.30 | 106.3 | 5.25 | 39.3 | 1.99 |
| CPU→RTX custom k=1 | 11.80 | 90.8 | 8.25 | 57.7 | 5.15 |
| RTX→RTX native k=1 | 18.64 | 96.1 | 5.29 | 27.3 | 1.50 |

The formal native paired result is 0.899x geomean, median 0.877x, range 0.798–1.096x, with 2/12 questions faster and 12/12 exact. Native assistance lowers instantaneous RTX power by about 4.6% relative to its paired baseline measurement, but the longer completion time removes the benefit: RTX energy is slightly higher (5.29 vs 4.79 J/token within that native run). It therefore provides neither a stable performance win nor an RTX-energy win.

CPU→RTX custom is clearly dominated: lower RTX watts do not compensate for substantially longer execution, while CPU package power and both component energy/token values increase. Intel and NVIDIA domains are reported separately and never summed as whole-system energy.

## 8. Answers to the platform questions

1. **Fastest proposal device:** CPU on the fair same-artifact short-proposal matrix.
2. **Why it does not accelerate RTX:** its cost is not free; repeated prefill, verification and orchestration exceed saved target decoding.
3. **Transfer or integration:** not transfer alone. Same-GPU custom is worse; native integration recovers much of the loss, proving KV/scheduling integration matters.
4. **Why 14B still does not crossover:** target cost rises, but verification scaling, CPU assistance and correctness-sensitive batched behavior still dominate.
5. **Break-even latency:** none finite for the measured custom harness under empirical proportional verification scaling; the k=1 asymptote is about 0.668x.
6. **Compute versus capacity:** capacity boundary appears first. The safe 14B target already occupies about 9.7 GiB CUDA / 10.65 GB NVML on a 12 GB GPU.

## 9. Final stop rule

The RTX 5070 Ti platform will not run the 420 holdout, 20B targets, RTX 14B+draft co-residency, additional `k`, or new speculative algorithms. The remaining research direction—if pursued—is a separate cross-generation platform characterization, not an extension of this run.

> **PRIMARY PLATFORM = CLOSED**

## Artifacts

- `analysis/all_runs.csv`, `analysis/all_rounds.csv`, `analysis/all_power_1s.csv`
- `analysis/paper_power_8b_custom_12q_runs.csv`
- `analysis/paper_power_8b_native_12q_runs.csv`
- `analysis/paper_power_summary.csv`
- `analysis/break_even_curve.csv`, `analysis/break_even_thresholds.csv`
- `reports/figures/figure1_pilot_speedup_vs_k.*`
- `reports/figures/figure2_root_cause_decomposition.*`
- `reports/figures/figure3_target_size_crossover.*`
- `reports/figures/figure4_vram_capacity_boundary.*`
- `reports/figures/figure5_power_energy.*`
- `reports/figures/figure6_empirical_break_even_curve.*`
- `reports/figures/figure7_draft_device_characterization.*`
