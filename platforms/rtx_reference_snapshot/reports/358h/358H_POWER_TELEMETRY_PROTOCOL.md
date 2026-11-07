# 358H CPU-draft versus NPU-draft power protocol

Status: **SEPARATED TRACKS FROZEN / CPU PACKAGE QUALIFIED / NPU ENERGY NOT ADMISSIBLE**

The scientific comparison is CPU draft versus NPU draft using the same frozen OpenVINO model semantics. The primary latency/break-even track runs with telemetry OFF. A separate CPU-package energy track uses the Windows Energy Meter `RAPL_Package0_PKG` counter through a direct PDH sampler. Intel Unified Telemetry remains qualification evidence but is not admitted for formal CPU or NPU energy in this campaign.

The B570 study's measurement discipline is reused: an exact host-clock workload boundary, at least five seconds of telemetry coverage before and after that boundary, linear interpolation at both boundaries, trapezoidal integration, an idle-load-idle sensor sanity test, and a randomized 10-OFF/10-ON overhead qualification with an absolute median overhead limit of one percent.

The B570 sensor boundary is not reused. B570 measured board-level `GPU Card Power`; 358H reports Package and NPU domains separately when Unified Telemetry exposes them. Package, NPU, PP0/core, PP1/graphics, and DRAM readings may overlap and must never be added together. Every result must name its sensor, unit, sampling cadence, missing-sample count, and integration boundary.

Any admitted CPU-package energy collection fails closed if any of these conditions is false:

- external power is positively online before and after the run;
- the battery is not discharging;
- the frozen Windows power scheme is unchanged;
- the requested device is exactly CPU or NPU and its independent binding evidence passed;
- Package power/energy is present and its units and scale pass idle-load-idle qualification;
- workload process affinity is exactly logical CPUs 0–11 and collector affinity is exactly 12–15;
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

No trace produced during telemetry qualification is formal Phase-1 data. NPU-domain energy is not admitted and must not be inferred from package RAPL.

## Preserved failed attempt

The first overhead qualification used Unified Telemetry's stock `pwr-low.json`, whose `samplingInterval` is 1 ms. CPU median inner-loop duration changed from 1,983.9834 ms with telemetry OFF to 3,001.0712 ms with telemetry ON: 51.2649% absolute overhead. It therefore failed the preregistered 1% gate and was stopped before NPU overhead testing. The raw evidence remains under `runs/358h/qualification_ac_20260918/telemetry_overhead/`.

The neutral corrective action is a frozen official-format power configuration at the already established B570 cadence of 100 ms. It changes only `samplingInterval`; the official low-config metric list is unchanged. The 1% acceptance threshold is unchanged, and the full randomized 10-OFF/10-ON gate must be repeated for both CPU and NPU under `telemetry_overhead_v2_100ms/`.

The 100 ms attempt showed that collecting OpenVINO's very dense built-in ITT stream still materially perturbs the CPU path. It was stopped and preserved under `telemetry_overhead_v2_100ms/`. Formal workload traces therefore do not enable the ITT collector. Exact host QPC boundaries are mapped into the Unified Telemetry clock by short adjacent calibration traces that do enable one user marker; before/after calibration spread and drift must be no more than 5 ms. The actual formal power collectors are `socwatch` for CPU and `socwatch,level-zero,xpu-os` for NPU. Their observer overhead is qualified separately under `telemetry_overhead_v3_100ms_noitt/` without changing the 1% gate.

## Final no-ITT 100 ms overhead qualification

The randomized/interleaved seed-570 qualification completed 10 telemetry-OFF and 10 telemetry-ON observations for both devices. These are qualification-only runs and are not formal performance data.

| Device | OFF median | ON median | Absolute change | 1% gate |
|---|---:|---:|---:|---|
| CPU | 1,891.5408 ms | 1,995.41385 ms | 5.4915% | FAIL |
| NPU | 1,354.96095 ms | 1,364.4205 ms | 0.6981% | PASS |

Removing ITT reduced a representative trace from tens of megabytes of OpenVINO events to roughly 29 KiB of SocWatch data, but SocWatch still materially perturbs the short CPU generation loop. The threshold was not relaxed. Phase 0 therefore remains blocked for a joint CPU/NPU formal telemetry protocol. The raw evidence and machine-readable decisions are under `runs/358h/qualification_ac_20260918/telemetry_overhead_v3_100ms_noitt/{cpu,npu}/`.

A subsequent engineering attempt may reduce the SocWatch metric set to only the scientifically required domains and must repeat the same frozen 10-OFF/10-ON gate. Any such retry is a new, versioned qualification configuration; it does not replace or erase this failure. Other defensible alternatives are a qualified lower-overhead hardware/external energy source or separate timing and energy studies under a preregistered protocol amendment. Formal data remain prohibited until one path passes without weakening the 1% rule.

That versioned minimal-metric retry was subsequently completed under `telemetry_overhead_v4_100ms_minimal/`. CPU collected only `pkg-pwr`; NPU collected only `pkg-pwr,npu-pwr`; cadence, seed, workload, repetition count, and the 1% gate were unchanged.

| Device | OFF median | ON median | Absolute change | 1% gate |
|---|---:|---:|---:|---|
| CPU minimal | 999.20145 ms | 1,029.4135 ms | 3.0236% | FAIL |
| NPU minimal | 1,353.15305 ms | 1,383.41515 ms | 2.2364% | FAIL |

Metric pruning reduced CPU perturbation but did not make it admissible. The NPU result also demonstrates run-to-run sensitivity: the earlier superset configuration passed at 0.6981%, while this separately randomized qualification failed at 2.2364%. The project therefore does not cherry-pick the passing NPU attempt. A lower-overhead measurement mechanism or a scientifically preregistered isolation strategy must be qualified before formal telemetry is allowed.

## Final direct-PDH and isolation qualification

The direct PDH sampler is `scripts/platform/358h/sample_windows_energy_meter.py`. It samples package power at 1000 ms and timestamps every query at the QPC midpoint. Raw Energy-counter values are investigation-only; formal joules are obtained by exact-window interpolation and trapezoidal integration of the qualified watt stream.

| Qualification | Workload | OFF median | ON median | Absolute change | 1% gate |
|---|---|---:|---:|---:|---|
| v5 direct PDH | short 20×4-token loop, unpinned | 1009.96135 ms | 1011.98580 ms | 0.200448% | PASS |
| v6 representative | 2048-token context, 128 output, unpinned | 1871.65955 ms | 1902.73340 ms | 1.660230% | FAIL |
| v7 representative isolated | same 2048/128 semantics; workload 0–11, collector 12–15 | 1878.60930 ms | 1876.30945 ms | 0.122423% | PASS |

The v7 collector used at most 0.015625 process CPU seconds per 15-second trace, at most 0.1042% of one CPU over wall time; the maximum PDH collection call was 0.7512 ms. The descriptive bootstrap 95% interval for signed overhead was −1.968% to 1.220%; it does not replace the preregistered absolute-median gate. First-half versus second-half median duration changed by −0.0123%, and the index/duration rank correlation was −0.0737.

Because isolation changes the compute set, the exact CPU affinity 0–11 is frozen for all formal CPU runs, including telemetry OFF latency. The collector uses 12–15 only in the energy track. An unpinned OFF result is never compared with a pinned ON result.

Final policy:

- **Track L (primary):** CPU and NPU latency/break-even, telemetry OFF. CPU process affinity 0–11 is frozen; NPU uses the system default host affinity.
- **Track E (conditional):** CPU package power/energy only, direct PDH at 1000 ms, workload 0–11, collector 12–15. These results are reported independently and do not replace Track-L timing.
- **NPU energy:** `ENERGY-NOT-ADMISSIBLE / NOT REPORTED`.
- **Symmetric CPU/NPU energy comparison:** prohibited in this campaign.

