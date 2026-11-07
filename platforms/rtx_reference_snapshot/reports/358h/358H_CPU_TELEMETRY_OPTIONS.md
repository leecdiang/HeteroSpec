# 358H CPU telemetry options and qualification decision

Status: **WINDOWS ENERGY METER / DIRECT PDH SELECTED FOR CPU-PACKAGE ENERGY**

This is a pre-formal engineering qualification. None of the timings or power traces below are formal Phase-1 results.

## Candidate audit

| Candidate | Physical boundary | Sampling / timestamps | Privilege and deployment | Observer risk | Decision |
|---|---|---|---|---|---|
| Intel Unified Telemetry / SocWatch | Package and component domains, including NPU where exposed | 100 ms configuration; UT clock mapped to QPC by adjacent ITT calibration | Administrator/elevated collector | Material on this platform: CPU failed at 5.4915% with no ITT and 3.0236% with minimal metrics | Retain failed evidence; reject for CPU timing/energy admission |
| Windows Energy Meter through direct PDH API | Hardware-backed `RAPL_Package0_PKG` package power | 1000 ms; QPC midpoint around each `PdhCollectQueryData` call | No new driver or reboot | Low: short-window 10 OFF + 10 ON absolute median change 0.2004% | Selected for CPU-package energy, subject to representative-window confirmation |
| Existing PowerShell `Get-Counter` wrapper | Same package RAPL provider | 1000 ms, host timestamp | No new driver | PowerShell process/runtime is avoidable overhead and gives weaker timestamp control | Replaced by direct PDH implementation |
| Intel PCM | Package RAPL/MSR | Tool dependent | Windows MSR driver, administrator rights, driver signing/test-signing and often reboot | Potentially low after qualification, but deployment changes the machine | Not installed tonight; reject as unnecessarily invasive when direct PDH is available |
| PresentMon service/SDK | GPU-board/device metrics where supported | Service/SDK dependent | Installed service, but no qualified CPU package path | B570 records show CPU power unsupported; boundary is not the requested CPU package | Reject for CPU energy |
| Windows `Power Meter` counters | Platform-dependent | PDH | None | Observed counters are identically zero on this machine | Reject: no physical response |
| Energy Estimation Engine / task energy models | Modelled process/application energy | ETW/model-specific | Provider access | Not a direct hardware package boundary | Reject for hardware energy claims |
| TDP, utilization, or vendor percentages | No measured energy boundary | N/A | None | Not a measurement | Prohibited as energy evidence |

## Selected implementation

`scripts/platform/358h/sample_windows_energy_meter.py` uses the Windows PDH API directly. It samples `\Energy Meter(RAPL_Package0_PKG)\Power` once per second, records the QPC midpoint and collection-call duration, and converts the provider's milliwatt power reading to watts. The raw `Energy` counter is retained only for investigation; it is not treated as joules until its scale and accumulation semantics are independently established.

The admitted physical claim is **CPU package power/energy over an exact host-QPC workload window**. It is not wall energy, system energy, isolated CPU-core energy, or an NPU domain. Package and component domains must never be added.

The frozen overhead statistic remains the absolute percent change between telemetry-ON and telemetry-OFF medians, with randomized/interleaved seed 570 and an unchanged 1% acceptance limit. The first complete direct-PDH qualification used 10 OFF and 10 ON observations and passed at 0.2004%. A second, separately seeded qualification uses a Phase-1-like 2048-token context and 128-token output so the sensor window matches the intended study duration class. Bootstrap intervals, variance, collector CPU time, and order/thermal trends are descriptive diagnostics and do not replace the frozen median gate.

## Core isolation decision

The machine exposes 16 logical/physical cores with no SMT: logical CPUs 0–3 have the higher efficiency-class value, 4–15 the lower value, and 12–15 form a separate last-level-cache group. A scientifically clean isolation option would pin the workload to 0–11 and the collector to 12–15 for both OFF and ON comparisons.

That option changes the CPU under test by withholding four cores. It is therefore not adopted merely to improve an overhead number. If the unpinned representative qualification passes and the collector remains at negligible CPU use, the formal CPU latency track stays unpinned and telemetry OFF, while the conditional energy track uses the already-qualified direct-PDH collector. Isolation is reserved for diagnosis or for a separately preregistered energy-only track; an unpinned OFF result may never be compared with a pinned ON result.

## Cross-platform comparability

The measurement discipline is shared with prior M4 and B570 work: frozen sensor boundary, explicit sampling cadence, exact workload boundary, observer-overhead qualification, and no inference from TDP. The physical boundaries are not identical. M4 used private IOReport/SMC component telemetry and a 2% overhead limit; B570 used PresentMon GPU-card power at 100 ms and a 1% limit; 358H direct PDH exposes CPU-package RAPL at 1000 ms. Cross-platform energy values therefore require boundary-qualified labeling and must not be presented as if they were the same sensor.

## Sources

- Intel PCM official repository and Windows installation notes: `https://github.com/intel/pcm` and `doc/WINDOWS_HOWTO.md`.
- Microsoft Performance Counters API: `https://learn.microsoft.com/windows/win32/perfctrs/using-performance-counters`.
- Local raw evidence: `runs/358h/qualification_ac_20260918/telemetry_overhead_v3_100ms_noitt/`, `telemetry_overhead_v4_100ms_minimal/`, `telemetry_overhead_v5_windows_rapl/`, and `telemetry_overhead_v6_phase1like/`.

