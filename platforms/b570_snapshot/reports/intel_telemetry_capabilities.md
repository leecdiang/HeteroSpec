# Intel Unified Telemetry capability report

Captured: 2026-09-03 22:44:18–22:45:00 +08:00  
Tool: Intel Unified Telemetry 0.2.0-beta1.1  
Command: `ut.exe -t 30 --config-level low --enable socwatch,emon,level-zero,xpu-os`

The elevated capture configured all four requested collectors and exited successfully. Raw EMON, SoCWatch, Intel GPU, NPU, and XPU-OS files are retained under `telemetry\intel_idle_30s` together with the converted 408,450-event JSON trace.

| Counter/domain | Status | Unit | Observed behavior | 1 s aggregation |
|---|---|---:|---|---|
| CPU package power (`PKG-PWR`) | Available | mW | 8,920 samples over 31.76 s; non-zero data present | Yes; average within 1 s bins, then display as W to 0.1 W |
| CPU utilization (`cpu_load`, `cpu_utilization_%`) | Available | % | High-rate per-core data, approximately 2 ms median spacing | Yes |
| CPU operating frequency (`cpu_op_freq`) | Available | GHz | High-rate per-core data, approximately 2 ms median spacing | Yes |
| Intel GPU utilization (`GPU.GpuBusy`, XPU-OS 3D utilization) | Available with timestamp warning | % | Level Zero data present; Intel driver warning says metric timestamps may be inaccurate | Yes for value summaries; do not claim precise cross-source alignment |
| Intel GPU frequency | Available with timestamp warning | MHz | `AvgGpuCoreFrequencyMHz` and `CoreFrequencyMHz` present | Yes |
| Intel GPU power / VCCGT | Unavailable in trace | W/mW | Requested by the supplied low power config, but no corresponding event was emitted | No |
| Intel GPU temperature | Unavailable in trace | °C | Not emitted at low config on this OEM platform | No |
| Intel GPU throttling reason | Unavailable in trace | flag | Not emitted at low config on this OEM platform | No |
| NPU NOC/DMA activity | Available | raw counter | 58 samples over 31.47 s; about 1.07 s median spacing; idle values were zero | Already approximately 1 s |
| NPU power | Unavailable in trace | W/mW | Requested by the supplied low power config, but no corresponding event was emitted | No |
| NPU frequency / P-state | Unavailable in trace | MHz/state | Not emitted in this capture | No |
| NPU temperature / throttling | Unavailable in trace | °C/flag | Not emitted in this capture | No |

## Interpretation rules

- Package, GPU, NPU, core and other power domains must remain separate. They must not be summed and presented as whole-system power.
- Formal processing should use 1-second bins. Power presentation may be rounded to 0.1 W only after aggregation.
- The Intel GPU values are usable, but the known Level Zero timestamp-unit warning prevents strong claims about sub-second alignment against EMON or SoCWatch.
- Gate 0 therefore records Intel telemetry as **PARTIAL**: CPU/package power is usable, while Intel GPU/NPU independent power domains are unavailable on this capture.
