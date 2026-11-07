# Qwen3-8B RTX Target Baseline

## Status

**PASS** — the formal target-only baseline completed 30/30 measured runs without a black screen, bugcheck, CUDA error, or NVML read error.

This report covers only the RTX target-model baseline. It is not a speculative-decoding result and does not include draft-device or end-to-end speedup claims.

## Frozen configuration

- Session: `p2-RTX-20260905T223147`
- Time: 2026-09-05 22:31:47–22:41:50 (Asia/Shanghai)
- Model: Qwen3-8B, revision `b968826d9c46dd6066d109eabc6255188de91218`
- Quantization: bitsandbytes NF4, BF16 compute, double quantization
- Device: NVIDIA GeForce RTX 5070 Ti Laptop GPU
- Attention backend: explicitly forced PyTorch SDPA cuDNN
- Context lengths: 512, 2048, 8192 tokens
- Requested output lengths: 128 and 256 tokens
- Warm-up: 3 per configuration
- Measured repetitions: 5 per configuration
- GPU tuning: G-Helper core and memory offsets both verified as 0 before launch
- Memory-clock verification: observed maximum 14001 MHz (default)
- Intel Unified Telemetry: deliberately not loaded during this RTX-only stability run

## Results

| Input tokens | Output tokens | Runs | Mean completion (s) | Mean tok/s | SD tok/s | CV | Peak PyTorch allocation (GiB) | Mean tagged GPU power (W) | Peak GPU power (W) | Peak temp (°C) | Peak NVML VRAM (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 512 | 128 | 5 | 5.205 | 24.60 | 0.35 | 1.42% | 5.887 | 87.2 | 98.3 | 66 | 6544.1 |
| 512 | 256 | 5 | 9.778 | 26.18 | 0.22 | 0.84% | 5.887 | 90.4 | 101.4 | 73 | 6554.1 |
| 2048 | 128 | 5 | 5.439 | 23.53 | 0.08 | 0.36% | 6.218 | 100.4 | 133.5 | 81 | 7046.1 |
| 2048 | 256 | 5 | 10.506 | 24.38 | 0.67 | 2.76% | 6.218 | 96.1 | 133.6 | 81 | 7058.1 |
| 8192 | 128 | 5 | 7.593 | 16.86 | 0.07 | 0.43% | 7.620 | 117.9 | 141.5 | 84 | 8862.1 |
| 8192 | 256 | 5 | 12.435 | 20.59 | 0.09 | 0.42% | 7.620 | 112.1 | 141.2 | 85 | 8874.1 |

Power means above use only NVML samples tagged to measured runs; warm-up and between-run idle samples are excluded. They are GPU-board telemetry, not whole-system power.

## Integrity checks

- Session manifest: `valid: true`
- Result directories found: 30/30
- Requested output-token count satisfied: 30/30
- Deterministic token hash within every configuration: PASS (one unique hash per five repetitions)
- NVML samples: 587 total, 250 tagged to measured runs
- NVML read errors: 0
- Whole-session maxima: 141.6 W, 86 °C, 8874.1 MB VRAM, 100% GPU utilization
- Previous incomplete/invalid B0 directories are not included; membership is defined exclusively by this session manifest's run list.

## Stability finding

The earlier HYPERVISOR_ERROR incidents are not reproduced under the same 8192-token context class after forcing the cuDNN SDPA backend. The formal run stayed below 8.9 GB NVML VRAM, whereas the unstable automatic-attention path approached the 12 GB limit. This is strong operational evidence that the forced cuDNN path is a safe baseline configuration, but it does not by itself prove the Windows hypervisor's root cause.

## Artifacts

- Session manifest: `logs\phase2-target-20260905T223147.json`
- NVML trace: `telemetry\qwen_target_nvml_20260905T223147.csv`
- Per-run data: `runs\2026-09-05\qwen3\B0\RTX\...`
- Crash investigation: `reports\PHASE2_HYPERVISOR_INCIDENT.md`

## Decision

The Qwen3-8B RTX target baseline is qualified for subsequent controlled experiments with `sdpa_backend=cudnn`. Automatic SDPA backend selection remains prohibited for context lengths of 4096 tokens or greater on this machine until the platform crash is independently resolved.
