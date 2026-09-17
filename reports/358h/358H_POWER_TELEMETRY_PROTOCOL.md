# 358H CPU-draft versus NPU-draft power protocol

Status: **IMPLEMENTED, QUALIFICATION PENDING ADMINISTRATOR TRACE**

The scientific comparison is CPU draft versus NPU draft using the same frozen OpenVINO model semantics. Intel Unified Telemetry is the primary collector. Windows Energy Meter RAPL counters are retained only as a slower, independent diagnostic cross-check.

The B570 study's measurement discipline is reused: an exact host-clock workload boundary, at least five seconds of telemetry coverage before and after that boundary, linear interpolation at both boundaries, trapezoidal integration, an idle-load-idle sensor sanity test, and a randomized 10-OFF/10-ON overhead qualification with an absolute median overhead limit of one percent.

The B570 sensor boundary is not reused. B570 measured board-level `GPU Card Power`; 358H reports Package and NPU domains separately when Unified Telemetry exposes them. Package, NPU, PP0/core, PP1/graphics, and DRAM readings may overlap and must never be added together. Every result must name its sensor, unit, sampling cadence, missing-sample count, and integration boundary.

Formal collection fails closed if any of these conditions is false:

- external power is positively online before and after the run;
- the battery is not discharging;
- the frozen Windows power scheme is unchanged;
- the requested device is exactly CPU or NPU and its independent binding evidence passed;
- Package power/energy is present and its units and scale pass idle-load-idle qualification;
- the NPU-specific domain is present for an NPU-domain claim;
- timestamps are monotonic and the workload interval is fully covered;
- telemetry overhead passed the preregistered one-percent gate;
- model, IR, runtime, driver, preregistration, and repository hashes match the frozen manifest.

Charging state is recorded. Package/component energy can remain admissible when AC is online and the battery is not discharging, but wall/system-energy claims are out of scope because no qualified wall-power boundary exists.

Scripts:

- `scripts/platform/358h/run_unified_telemetry.ps1`: fail-closed primary collection and artifact hashing.
- `scripts/platform/358h/analyze_ut_trace.py`: Package/NPU metric-name discovery gate.
- `scripts/platform/358h/collect_windows_rapl.ps1`: secondary RAPL diagnostic stream.
- `scripts/platform/358h/integrate_power_telemetry.py`: exact-boundary trapezoidal integration.
- `scripts/platform/358h/power_preflight.ps1`: AC, administrator, tool, and model hash gates.

No trace produced during telemetry qualification is formal Phase-1 data.

## Preserved failed attempt

The first overhead qualification used Unified Telemetry's stock `pwr-low.json`, whose `samplingInterval` is 1 ms. CPU median inner-loop duration changed from 1,983.9834 ms with telemetry OFF to 3,001.0712 ms with telemetry ON: 51.2649% absolute overhead. It therefore failed the preregistered 1% gate and was stopped before NPU overhead testing. The raw evidence remains under `runs/358h/qualification_ac_20260918/telemetry_overhead/`.

The neutral corrective action is a frozen official-format power configuration at the already established B570 cadence of 100 ms. It changes only `samplingInterval`; the official low-config metric list is unchanged. The 1% acceptance threshold is unchanged, and the full randomized 10-OFF/10-ON gate must be repeated for both CPU and NPU under `telemetry_overhead_v2_100ms/`.

The 100 ms attempt showed that collecting OpenVINO's very dense built-in ITT stream still materially perturbs the CPU path. It was stopped and preserved under `telemetry_overhead_v2_100ms/`. Formal workload traces therefore do not enable the ITT collector. Exact host QPC boundaries are mapped into the Unified Telemetry clock by short adjacent calibration traces that do enable one user marker; before/after calibration spread and drift must be no more than 5 ms. The actual formal power collectors are `socwatch` for CPU and `socwatch,level-zero,xpu-os` for NPU. Their observer overhead is qualified separately under `telemetry_overhead_v3_100ms_noitt/` without changing the 1% gate.
