# HeteroSpec-PC Gate 0 report

## Result

**GATE 0 = PASS WITH TELEMETRY LIMITATION**

CUDA and explicit OpenVINO CPU/iGPU/NPU runtime gates passed. NVIDIA power logging works. Intel Unified Telemetry records CPU/package power plus GPU/NPU activity, but this OEM/driver combination did not emit independent Intel GPU or NPU power domains.

## NVIDIA

| Check | Result |
|---|---|
| RTX detected | PASS |
| PyTorch CUDA | PASS |
| RTX model name | NVIDIA GeForce RTX 5070 Ti Laptop GPU |
| VRAM | 11.91 GiB (12 GB class; 12,227 MiB reported by `nvidia-smi`) |
| CUDA runtime | 12.8 |
| PyTorch | 2.11.0+cu128 |
| Compute capability | 12.0 |
| Driver | 616.56 |
| NVML power telemetry | PASS WITH LOGGER WORKAROUND |

The final NVIDIA idle file contains 30 complete 1 Hz rows. Power was 18.5–20.6 W in the accepted capture. Under Hybrid mode, persistent NVML handles intermittently became invalid, so the logger now reinitializes the handle per sample. Seven rows used an explicitly marked `nvidia-smi` fallback for an invalid field; both interfaces use the NVIDIA management stack. No silent data substitution is performed.

## Intel

| Check | Result |
|---|---|
| OpenVINO CPU | PASS |
| OpenVINO GPU.0 | PASS |
| OpenVINO NPU | PASS |
| Explicit CPU toy-model compile/inference | PASS |
| Explicit GPU.0 toy-model compile/inference | PASS |
| Explicit NPU toy-model compile/inference | PASS |
| Intel telemetry | PARTIAL |

- CPU full device name: Intel(R) Core(TM) Ultra 9 275HX
- GPU.0 full device name: Intel(R) Graphics (iGPU)
- NPU full device name: Intel(R) AI Boost
- OpenVINO also exposes GPU.1 as NVIDIA GeForce RTX 5070 Ti Laptop GPU; Intel experiments must explicitly use GPU.0.
- Available Intel power domains: CPU package (`PKG-PWR`)
- Available non-power counters: CPU utilization/frequency, Intel GPU utilization/frequency, NPU NOC/DMA activity
- Unavailable: separate Intel GPU power and NPU power; temperature/throttling counters were not emitted

Formal experiments must compile to `CPU`, `GPU.0`, or `NPU` explicitly. `AUTO`, `MULTI`, and `AUTO:GPU,CPU` are prohibited for single-device claims.

## Platform

| Item | Recorded state |
|---|---|
| Windows | Windows 11 Home China, 25H2, build 26200.9168 |
| Laptop | ASUS ROG Strix G16 G615LR_G615LR |
| BIOS | G615LR.338 (2026-06-04) |
| Windows power mode | Balanced; accepted by user for this experiment |
| OEM performance mode | G-Helper Balanced, mode 0 |
| MUX/GPU mode | Hybrid; G-Helper GPUMux=1, both GPUs started and runtime-visible |
| AC | Plugged in; battery 99% at inventory time |
| RAM | 47.4 GiB reported (48 GB installed class) |
| D: free space | 593.4 GB |
| Page file | System managed, `C:\pagefile.sys` |
| Display | Internal BOE NE160QDM-NZC, 240 Hz; no connected external monitor detected |

## Background-state note

- Windows Update service was running, but no active update worker process was detected.
- NVIDIA Overlay had five processes and should be closed before formal Phase 1 measurements.
- OneDrive, Steam and Discord were not detected.
- Windows Defender service was already stopped before this work; this task did not disable or modify Windows security settings.

## Frozen software

- Python 3.11.9 x64
- Target environment: `.venv-target`
- Intel environment: `.venv-intel`
- Hugging Face cache: `hf-cache`
- Intel Graphics driver: 32.0.101.8991
- Intel NPU driver: 32.0.100.5540
- NVIDIA driver: 616.56

Gate 0 stops here. No LLM, Spec-Bench, speculative decoding benchmark, CUDA Toolkit, TensorRT-LLM, affinity tuning, undervolting, overclocking, or TGP modification was performed.
