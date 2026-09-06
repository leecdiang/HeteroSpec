# M4 Telemetry Feasibility

## Feasibility verdict

One-hertz system/process/memory/thermal logging is feasible. Reliable per-domain power must be qualified on the actual M4/macOS build; the experiment must not promise separate CPU, GPU or ANE watts before `powermetrics` exposes and validates those fields.

| Source | Candidate signals | 1 Hz | Privilege | Role / limitation |
|---|---|---:|---|---|
| `powermetrics` | CPU/GPU/SoC energy or power, frequency, residency, thermal data depending on hardware/OS sampler | Yes, if supported | Usually `sudo` for full sampling | Primary power candidate; run an idle and workload qualification and preserve raw output. Available domains vary. |
| `vm_stat`, `memory_pressure`, `sysctl`, process RSS | pages, pressure, physical memory, process memory | Yes | No | Primary memory/swap context; not model allocator memory. |
| `pmset` | AC/battery and selected thermal/power state | Yes/periodic | Mostly no | Platform-state metadata, not component watts. |
| `ioreg` | Registry/power-state properties | Technically | Some fields restricted | Discovery/sanity only; keys are not a stable research power API. |
| MLX memory APIs | Active/cache/peak allocator bytes | Per run | No | Runtime memory attribution; not total unified memory or energy. |
| Instruments / Metal System Trace | GPU command and kernel timeline | Trace session | Developer tools, permissions | Root-cause profiling only; too intrusive for the primary formal logger. |
| Activity Monitor | Human sanity check | Not a stable experiment API | No | Do not scrape for formal data. |

## Qualification procedure

Capture 30 seconds idle and a short warmed generation at 1 Hz. Store raw `powermetrics` output, command/help text, exit status, sudo requirement and parser coverage. Validate counter units and monotonicity; energy counters may be differenced into 1-second bins, while instantaneous power is retained as reported. Separately sample memory pressure, swap and process RSS. Measure baseline throughput once with and once without logging; if median perturbation exceeds 2%, use power as a separately labeled run or lower-cost sampler.

Report only observed domains. If only aggregate SoC/package energy is stable, publish that and state that CPU/GPU/ANE attribution is unavailable. Never infer ANE power by subtraction, and never add overlapping domains as “whole-machine power.” Battery discharge rate is not a substitute for component power.

## Thermal controls

The MacBook Air is fanless, so thermal history is a first-order covariate. Record ambient notes, AC/battery state, Low Power Mode, start/end thermal pressure, warm-up policy and run order. Randomize or counterbalance baseline/spec conditions, enforce cooldown to the same thermal state, and invalidate runs that enter serious/critical thermal pressure.

