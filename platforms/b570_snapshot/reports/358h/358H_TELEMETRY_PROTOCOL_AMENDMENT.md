# 358H pre-formal telemetry protocol amendment

Status: **FROZEN BEFORE FORMAL DATA**

No formal Phase-1 observation existed when this amendment was selected. The one-percent threshold is unchanged.

The repository audit shows that energy is conditional on a valid sensor boundary, while latency supplies the primary draft-cost term to the break-even analysis. The original single in-band telemetry design is therefore replaced by two non-substitutable tracks:

1. **Track L — primary latency/break-even.** CPU and NPU run with telemetry OFF. CPU is pinned to logical CPUs 0–11; NPU uses default host affinity. Track L supplies `T_d(2)` and makes no energy claim.
2. **Track E — CPU-package energy only.** The same CPU model/runtime/generation semantics and the same workload affinity 0–11 are used. The direct PDH collector is pinned to 12–15 and samples `RAPL_Package0_PKG` power at 1000 ms. Track-E timing must not replace Track-L timing.

The CPU-package path passed a representative 10 OFF + 10 ON qualification at 0.122423% absolute median overhead under the frozen isolation configuration. The unpinned representative attempt failed at 1.660230% and remains part of the record.

NPU energy is not admissible. The latest minimal SocWatch qualification failed at 2.2364%, and CPU package RAPL does not measure an isolated NPU domain. No symmetric CPU/NPU energy comparison will be made.

Raw evidence:

- `runs/358h/qualification_ac_20260918/telemetry_overhead_v6_phase1like/`
- `runs/358h/qualification_ac_20260918/telemetry_overhead_v7_phase1like_isolated/`

This amendment changes measurement architecture, not the acceptance threshold, model, device binding, contexts, prompts, repetition count, or formal performance result.

