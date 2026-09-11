# Arc B570 Energy Telemetry Qualification

**Decision: GO for later formal B570 board-energy measurement, provided the existing disconnected-ToDesk protocol is enforced.** This qualification did not run HumanEval, V2, speculative decoding, or any paper experiment. All numerical load results below are instrumentation smoke evidence only.

## 1. Provenance and installed environment

- Repository branch: `windows/b570-backend-control`
- Preregistration/provenance base: `59185f24793eb2b852be0821295d13c44ad97636`
- OS: Windows 11 Pro 25H2, build `26200`
- GPU: `Intel(R) Arc(TM) B570 Graphics`, PCI device `8086:e20c`, PNP identity `PCI\VEN_8086&DEV_E20C&SUBSYS_21111EF7&REV_00\6&B335EA9&0&00080008`
- B570 driver: `32.0.101.8993`, newer than the required `32.0.101.6793` floor. No driver update was performed.
- Intel Graphics Software: `26.26.2459.3`
- Intel PresentMon product/service/API DLL/SDK loader: `2.5.1.0`
- PresentMon API reported at runtime: `3.3.0`
- Official installation: Intel Corporation `Intel(R) PresentMon`, obtained from the GameTechDev/PresentMon `v2.5.1` release. The retained, ignored source archive has SHA-256 `d307a637ce51e728b89c0d05c86aa92506230addb9357f3117c976f436afbb56`.
- Service: `PresentMonSharedService`, Running, Automatic, `C:\Program Files\Intel\PresentMonSharedService\PresentMonService.exe`
- Service API: `C:\Program Files\Intel\PresentMonSharedService\PresentMonAPI2.dll`
- SDK: `C:\Program Files\Intel\PresentMon\SDK`
- Level Zero loader/SDK: official `1.32.0`, loader `C:\Windows\System32\ze_loader.dll`, headers and import library under `C:\Program Files\LevelZeroSDK\1.32.0`.

The collector uses the service dynamic-query API directly. It does not launch the GUI, overlay, or a frame-event capture. It selects the adapter whose introspected name contains `B570`, polls with PID `0`, and never registers a presenter.

## 2. PresentMon metric introspection

| Metric | Result | Unit / treatment |
|---|---:|---|
| `PM_METRIC_GPU_CARD_POWER` | SUPPORTED | W; mandatory primary metric |
| GPU Power | SUPPORTED | W; retained as a separate diagnostic, never added to Card Power |
| GPU Frequency | SUPPORTED | MHz |
| GPU Effective Frequency | UNSUPPORTED | blank CSV field |
| GPU Utilization | SUPPORTED | % |
| Render/Compute Utilization | SUPPORTED | % |
| GPU Memory Used | SUPPORTED | converted from bytes to MiB in CSV |
| GPU Memory Frequency | SUPPORTED | MHz |
| GPU Memory Effective Frequency | SUPPORTED | MHz |
| GPU Temperature | SUPPORTED | C |
| GPU Power Percent | SUPPORTED | % |
| CPU Power | UNSUPPORTED | blank CSV field |
| CPU Frequency | SUPPORTED | introspected only; not included in the authoritative board-energy query |
| CPU Utilization | SUPPORTED | introspected only; not included in the authoritative board-energy query |

The authoritative energy boundary is **Intel Arc B570 graphics-adapter board power**, as exposed by `PM_METRIC_GPU_CARD_POWER`. `GPU Card Power + GPU Power` is prohibited because these are not independent additive domains. CPU power is unavailable and no result is described as whole-system energy.

## 3. Collector definition

The minimal official-API implementation is in `scripts/platform/b570/presentmon_telemetry/`.

- Telemetry poll period: fixed at `100 ms` (10 Hz).
- Dynamic-query history window: `1000 ms`, matching the official sample default and ensuring that the latest hardware point is available despite scheduler jitter.
- Card Power statistic: `PM_STAT_NEWEST_POINT`, not a one-second rolling mean. This preserves the sensor point at each poll and avoids smoothing workload boundaries.
- Other supported diagnostic metrics: `PM_STAT_AVG` over the query window.
- CSV timestamps: UTC plus QPC tick and sample index.
- Metadata: service API version, adapter name/id, B570 driver/PNP identity, period, query window/stat, availability, units, UTC bounds, QPC bounds/frequency, PID `0`, and `presenter_required=false`.
- Unsupported fields are blank; they are not replaced by zero.

An early connected-development capture used a 100 ms statistic window and revealed empty-window zeros. It is retained under `work/b570/telemetry_qualification/` and is excluded. The official sample's 1000 ms history window plus `PM_STAT_NEWEST_POINT` removed this API-window artifact without changing the 100 ms sensor polling period.

## 4. Disconnected-ToDesk sanity qualification

Authoritative qualification raw directory:

`work/b570/telemetry-qualification-20260912-022438/`

The exact profile was 20 s idle, a non-formal Qwen3-8B `llama-bench` Vulkan0 PP512 × 100 workload, then 20 s idle. Workload QPC duration was `36.3350216 s`. This was not HumanEval and is not admissible as a paper performance result.

ToDesk's local log recorded the remote-session close at `2026-09-12 02:23:40 +08:00`. The telemetry process ran `02:24:43.835`–`02:26:00.282`, and the complete qualification ended at `02:27:18.911`; there was no reconnect event in that interval. Thus the final capture was genuinely unattended and disconnected.

| Segment | Card Power median | Card Power mean | GPU utilization median | GPU frequency median |
|---|---:|---:|---:|---:|
| pre-idle | 35.585 W | 35.611 W | 13.625% | 400 MHz |
| workload | 161.987 W | 141.795 W | 98.837% | 2750 MHz |
| post-idle | 35.707 W | 36.090 W | 13.538% | 400 MHz |

Card Power rose by about 4.55× from the pre-idle median, utilization approached 99%, frequency rose from 400 to 2750 MHz, and both power and frequency returned toward the pre-idle state afterward. Adapter identity remained B570, not UHD 730. Response is physically coherent; no particular watt value is treated as a platform specification.

The smoke interval integrated to `5158.823 J`, mean `141.979 W`, median observed `161.940 W`, and peak observed `168.959 W`. These values only validate the pipeline.

## 5. Sampling stability

- Samples: `764`
- QPC timestamps strictly monotonic: PASS
- Actual interval median: `100.193 ms`
- p95: `100.732 ms`
- maximum: `101.420 ms`
- estimated missing samples: `0`
- Card Power zero samples: `0 / 764`
- unexplained reset/discontinuity: none observed

**Sampling stability: PASS. The final frozen rate is 100 ms.**

## 6. Exact synchronization and energy integration

`run_unattended.ps1` now optionally starts the collector before the pre-idle interval, keeps it alive through the post-idle interval, and records:

- run ID;
- workload start/end UTC;
- workload start/end QPC;
- QPC frequency;
- workload exit status;
- telemetry process start/end UTC and QPC;
- telemetry exit status and file paths.

The collector is stopped by a local stop file; it does not depend on ToDesk. Future formal runs must retain at least 5 s of telemetry lead and tail, while integration uses only the exact workload QPC interval.

`integrate_energy.py` linearly interpolates power at the two QPC boundaries and applies trapezoidal integration to the enclosed Card Power points:

`E_board = integral GPUCardPower(t) dt`, with `W × s = J`.

It emits board energy J, duration, mean/median/peak board power, optional output-token count, and J/output-token. Synthetic tests passed for a constant 10 W trace (`10 J`) and a linear 0→20 W ramp (`20 J`). The term is **B570 board energy** or **GPU board energy**, never whole-system energy.

## 7. Telemetry overhead

The frozen schedule used seed `570`, randomized/interleaved 10 OFF and 10 ON process-level observations. Each observation was the same non-formal Qwen3-0.6B Vulkan0 PP1024 `llama-bench` workload with 20 internal repetitions. The comparison metric was `llama-bench avg_ns`, isolating the repeated GPU operation from model-load time.

| Statistic | OFF | ON at 100 ms |
|---|---:|---:|
| median | 90.6717725 ms | 89.8922525 ms |
| CV across observations | 0.503% | 0.415% |

- ON/OFF ratio: `0.99140284`
- point change: `-0.8597%`
- deterministic 10,000-resample bootstrap ratio CI95: `[0.98709, 0.99484]`

The negative direction must not be interpreted as a speed benefit. Its absolute point change is below the preregistered 1.0% limit and cross-observation CV is low. **TELEMETRY_OVERHEAD = PASS.**

## 8. Level Zero Sysman cross-check

The bounded official Sysman probe enumerated both Intel devices. B570 mapped independently to device ID `0xe20c` and exposed two power-domain handles plus GPU, memory, and another frequency domain.

- B570 power-domain enumeration: SUPPORTED
- `zesPowerGetEnergyCounter()` on both B570 domains: UNSUPPORTED (`ZE_RESULT_ERROR_UNSUPPORTED_FEATURE`, `0x78000003`)
- `zesPowerGetUsage()`: unavailable in this runtime path (`0x78000001`)
- `zesFrequencyGetState()`: SUPPORTED; observed GPU 400 MHz when idle, memory 19000 MHz

The UHD 730 energy counter worked, but it is not the B570 and is irrelevant to the B570 energy boundary. Because B570 Sysman energy is unsupported, a PresentMon-vs-Sysman joule comparison is **NOT AVAILABLE**. Per protocol this does not fail the primary PresentMon gate.

## 9. Formal-use policy and final gate

All mandatory conditions pass:

1. official Intel/GameTechDev PresentMon 2.5.1 service/API;
2. exact Arc B570 identity;
3. Card Power available;
4. PID 0 independent telemetry without presenter;
5. no zero/broken stream in the authoritative run;
6. stable 100 ms timestamp stream with no missing samples;
7. coherent idle→load→idle response;
8. unattended disconnected-ToDesk logging;
9. exact QPC workload-window synchronization;
10. telemetry overhead within 1.0%;
11. validated trapezoidal energy integration.

**FORMAL BOARD-ENERGY READINESS: GO.** Formal timing/power intervals must still run unattended with ToDesk disconnected. The frozen primary source is PresentMon 2.5.1 `PM_METRIC_GPU_CARD_POWER` at 100 ms, Card Power `PM_STAT_NEWEST_POINT`; formal energy is the trapezoidal integral over exact workload QPC bounds. Raw qualification logs remain under `work/` and are not paper artifacts.

## 10. Official references

- Intel PresentMon product page: <https://game.intel.com/us/intel-presentmon/>
- Official GameTechDev/PresentMon releases: <https://github.com/GameTechDev/PresentMon/releases>
- Official PresentMon API header: <https://github.com/GameTechDev/PresentMon/blob/main/IntelPresentMon/PresentMonAPI2/PresentMonAPI.h>
- Official service/SDK deployment notes: <https://github.com/GameTechDev/PresentMon/blob/main/README-Service.md>
- Official Level Zero Sysman API header: <https://github.com/oneapi-src/level-zero/blob/master/include/level_zero/zes_api.h>
