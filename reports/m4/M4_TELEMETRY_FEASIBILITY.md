# M4 Telemetry Feasibility

## Result

`powermetrics` on macOS 26.6.2 advertises `cpu_power`, `gpu_power`, `ane_power` and `thermal` samplers, supports 1,000 ms sampling, and can preserve machine-readable plist output. Actual sampling returns `powermetrics must be invoked as the superuser`. Non-interactive sudo is unavailable in this session, so the required 30-second idle capture was not fabricated or bypassed.

**POWER TELEMETRY = PARTIAL**: capability is present and the sampling design is viable, but observed field names, units and availability remain unqualified until the user runs the logger with administrator authorization.

| Source | Verified capability | Privilege | Interpretation |
|---|---|---|---|
| `powermetrics` | CPU/GPU/ANE power and thermal sampler names; text/plist; 1 s interval | Root required | Primary candidate; reported power is estimated and Apple warns against cross-device comparison. |
| `vm_stat` / `memory_pressure` / `sysctl vm.swapusage` | PASS | None | System memory, compression, pressure and swap; not model allocator memory. |
| MLX allocator | PASS | None | Active/peak runtime allocations; not total unified memory. |
| `pmset` / system profiler | PASS | None | AC/battery, Low Power Mode and battery state; not component watts. |

## Qualification command

Run telemetry as a separate privileged process, never as `sudo python benchmark.py`:

```sh
sudo powermetrics --samplers cpu_power,gpu_power,ane_power,thermal \
  --sample-rate 1000 --sample-count 30 --format plist \
  --output-file telemetry/m4/powermetrics_idle_30s.plist
```

Retain the raw capture and aggregate into 1-second bins only after validating the actual plist keys and units. Report only domains present on this hardware/build. Do not split aggregate SoC power, infer ANE watts by subtraction, or sum overlapping domains as whole-machine power. Compare logger-on/off throughput before formal use and separate power runs if perturbation exceeds 2%.
