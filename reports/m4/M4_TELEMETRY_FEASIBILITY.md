# M4 Telemetry Feasibility

## Result

**POWER TELEMETRY = PASS WITH PRIVATE-API LIMITATION**

The Silemetry-mac TelemetryCore 0.1.0 (vendored macmon 0.8.0) was built and
called through its C ABI on this M4 without sudo. It samples private IOReport
energy counters and AppleSMC data directly; therefore this is a qualified local
research source, not a stable public macOS API guarantee.

The settled 30-second desktop-idle capture returned 30/30 samples. CPU, GPU,
ANE, DRAM and package power were valid throughout. Mean power was 0.39 W CPU,
0.34 W GPU, 0.58 W DRAM and 0.73 W package; ANE was a valid 0 W at idle. Package
is the Silemetry aggregate of CPU + GPU + ANE and excludes the separately
reported DRAM domain. One earlier 30-second capture was rejected as an idle
baseline because post-build background work raised mean CPU power to 4.42 W.

The timed question-395 rerun also produced valid phase-aligned samples. Its
short baseline/speculative phases averaged approximately 10.29/13.56 W GPU and
11.40/14.94 W package respectively. These are diagnostic short-window values;
no energy-efficiency claim is made because the phases lasted only 3--4 seconds.

A same-prompt logger-off control measured 17.48/20.58 tok/s for
baseline/speculative. The mean of two logger-on measurements was 17.32/20.54
tok/s, corresponding to approximately 0.95%/0.21% lower throughput and passing
the predeclared 2% logger-perturbation threshold. This small diagnostic does not
replace longer counterbalanced telemetry repetitions.

`powermetrics` on macOS 26.6.2 advertises `cpu_power`, `gpu_power`, `ane_power` and `thermal` samplers, supports 1,000 ms sampling, and can preserve machine-readable plist output. Actual sampling returns `powermetrics must be invoked as the superuser`. Non-interactive sudo is unavailable in this session, so the required 30-second idle capture was not fabricated or bypassed.

`powermetrics` remains a privileged fallback and was not needed for the local
power qualification. The lightweight CSV probe is built by
`scripts/setup/macos/build_silemetry_probe.sh`; raw captures remain ignored
under `work/m4/`.

| Source | Verified capability | Privilege | Interpretation |
|---|---|---|---|
| Silemetry TelemetryCore | CPU/GPU/ANE/DRAM/package power, CPU/GPU temperatures and frequency/utilization channels | None | Primary local source; private IOReport/AppleSMC API limitation. |
| `powermetrics` | CPU/GPU/ANE power and thermal sampler names; text/plist; 1 s interval | Root required | Optional cross-check; reported power is estimated and Apple warns against cross-device comparison. |
| `vm_stat` / `memory_pressure` / `sysctl vm.swapusage` | PASS | None | System memory, compression, pressure and swap; not model allocator memory. |
| MLX allocator | PASS | None | Active/peak runtime allocations; not total unified memory. |
| `pmset` / system profiler | PASS | None | AC/battery, Low Power Mode and battery state; not component watts. |

## Optional privileged cross-check

Run telemetry as a separate privileged process, never as `sudo python benchmark.py`:

```sh
sudo powermetrics --samplers cpu_power,gpu_power,ane_power,thermal \
  --sample-rate 1000 --sample-count 30 --format plist \
  --output-file telemetry/m4/powermetrics_idle_30s.plist
```

Retain the raw capture and aggregate into 1-second bins only after validating the actual plist keys and units. Report only domains present on this hardware/build. Do not split aggregate SoC power, infer ANE watts by subtraction, or sum overlapping domains as whole-machine power. Compare logger-on/off throughput before formal use and separate power runs if perturbation exceeds 2%.
