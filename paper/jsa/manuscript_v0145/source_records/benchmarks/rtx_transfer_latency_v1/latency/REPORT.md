# RTX fresh qualified matched latency v1

Result: **QUALIFIED**, with **90/90** new serialized/reference complete-ID equalities and **180/180** valid native timing intervals. Across 30 distinct prompts, the geometric mean of target/serialized prompt-median ratios is **0.645816x**, with 10,000 prompt-level bootstrap 95% CI **[0.629802, 0.659884]**. Serialized is slower for this measured generation boundary; ratios above 1 indicate a faster serialized path. 0/30 prompt medians favor serialized. All 180 runs are new, with no inherited v2 outcomes or timing observations.

Each task has three executions per condition, with the two conditions randomly ordered within task/repetition using seed 2026093001. Take the three-time median separately for each condition, divide target by serialized, then geometric-average the 30 ratios. Bootstrap resamples prompts, not repetitions, using seed 2026093002 and the frozen linear percentile rule. `PROMPT_MEDIANS.csv` provides full-precision absolute milliseconds and ratios; `REPORT.json` includes all 90 ID comparisons and the complete estimator result.

| Prompt | Target median ms | Serialized median ms | Target / serialized |
|---|---:|---:|---:|
| HumanEval/3 | 1033.0742 | 1613.0198 | 0.640460 |
| HumanEval/10 | 2837.0525 | 4071.2379 | 0.696853 |
| HumanEval/19 | 2739.3580 | 4178.3422 | 0.655609 |
| HumanEval/20 | 2852.5617 | 4107.5192 | 0.694473 |
| HumanEval/28 | 1128.4752 | 1783.2488 | 0.632820 |
| HumanEval/32 | 2939.6704 | 4180.7941 | 0.703137 |
| HumanEval/44 | 2738.9789 | 4161.8209 | 0.658120 |
| HumanEval/47 | 2670.4737 | 4059.4707 | 0.657838 |
| HumanEval/48 | 1446.1106 | 2144.1568 | 0.674443 |
| HumanEval/50 | 1179.6444 | 1758.1079 | 0.670974 |
| HumanEval/54 | 479.6713 | 838.3050 | 0.572192 |
| HumanEval/57 | 2734.1539 | 4093.6464 | 0.667902 |
| HumanEval/62 | 498.2627 | 806.3295 | 0.617939 |
| HumanEval/64 | 2807.8656 | 4000.2037 | 0.701931 |
| HumanEval/68 | 2197.3055 | 3301.9209 | 0.665463 |
| HumanEval/70 | 1286.6338 | 2088.7287 | 0.615989 |
| HumanEval/89 | 2458.5856 | 3697.5624 | 0.664921 |
| HumanEval/90 | 947.7475 | 1682.0591 | 0.563445 |
| HumanEval/101 | 295.2333 | 560.2718 | 0.526947 |
| HumanEval/104 | 1421.2895 | 2182.1307 | 0.651331 |
| HumanEval/105 | 2410.0023 | 3547.9300 | 0.679270 |
| HumanEval/106 | 1838.0470 | 2765.9707 | 0.664522 |
| HumanEval/107 | 1908.0848 | 2896.6412 | 0.658723 |
| HumanEval/111 | 1600.9905 | 2430.7307 | 0.658646 |
| HumanEval/119 | 2718.5650 | 4036.1256 | 0.673558 |
| HumanEval/123 | 1907.7502 | 2950.0084 | 0.646693 |
| HumanEval/126 | 843.6578 | 1319.3928 | 0.639429 |
| HumanEval/128 | 2044.0790 | 3434.0867 | 0.595232 |
| HumanEval/129 | 2875.7899 | 4490.6100 | 0.640401 |
| HumanEval/162 | 1208.5725 | 1934.7800 | 0.624656 |

The isolated b10839 build begins its native QPC interval after synchronized target and draft initial prefill, before per-request sampler creation/reset/seed and generation-state work. The interval covers draft inference, target verification, acceptance/correction/bonus, synchronization, state work, proposal and scheduling overhead through terminal committed ID, final synchronization, response/timing-log work and slot release. Model loading, initial prefill and process/model teardown are excluded. One-time model/context/speculative-engine allocation (including the persistent draft sampler) precedes prefill; per-request target sampler initialization and every draft sampler reset are inside the interval. These are instrumented CLI timings with native committed-ID and debug logging enabled, not uninstrumented deployment throughput. The final response/log overhead is conservatively included in both conditions. Native endpoint records are printed only after the measured end. A separately implemented chrono endpoint pair is checked on every run; both clocks share Windows' oscillator and are not independent physical clocks. The R0 conservative empty-hook probe used 10,000 samples, passed its frozen 10 microsecond / 1%-of-shortest-R0 threshold, and its raw record is retained.

This frontend/core was freshly built with Clang 21.1.0 and dynamically loads the original hashed CUDA backend DLLs. Exact build/source/patch, model, dataset, binary and DLL identities are retained. Changed frontend bytes have their own fresh direct-ID qualification; historical 90/90 does not qualify this build. Runtime uses Qwen3-8B Q8_0 / Qwen3-0.6B Q8_0, greedy k=2, seed 123, FA off, full CUDA0 offload, fresh contexts and inclusive EOG/128-ID endpoint. B's target and serialized conditions use this same timer executable. OS build 26300 differs from old v2 build 26200; historical driver-byte identity cannot be inferred from a version string.

Before B, the frozen rule required at least 120 seconds idle and three samples spaced 10 seconds apart, temperature <=55 C, utilization <=5%, temperature spread <=2 C, with a 600-second maximum. `THERMAL_PRECHECK.json` preserves the passing samples and asset rehash. Each run then has a fixed two-second idle and device snapshots before/after. Clocks were observed, not locked; these are measured laptop/Windows conditions. No energy result is estimated.

First B run: `2026-09-30T17:08:24.292824+00:00`. Last B run ended: `2026-09-30T17:44:32.149997+00:00`. Joint execution freeze: `dda3ec28535a1e178599ddfeda9ffc7b4124663b`; source freeze: `a4a72074746288d24dd9eb51223663f113bdd237`. A's failed candidate did not change B's tasks, conditions, timer, schedule, gates or estimator.

Independent verification: `verify_latency.py` imports neither the runner nor its aggregator. It reparses native IDs and timer endpoints, recomputes all 90 pairs, checks 180 intervals, recreates the randomized schedule, recomputes medians, geometric mean and prompt bootstrap, and validates identities/commands/offload/hash coverage. `INDEPENDENT_VALIDATION.json` and `OFFLINE_VALIDATION.json` record results. The separate B archive is content-addressed with a per-file digest manifest and frozen source, omitting weights/binaries/build products.
