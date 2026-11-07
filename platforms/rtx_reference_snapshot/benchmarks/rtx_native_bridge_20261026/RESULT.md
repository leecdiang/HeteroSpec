# RTX native reproduction and matched deployment bridge

**Completed finite campaign:** native recovery/rebuild/replay and all 936 registered formal requests (864 measurements + 72 warmups). No formal technical retry, missing slot, outlier deletion or adaptive extension.

The common new runtime uses the twelve exposed Qwen3 inputs and one RTX 5070 Ti Laptop, with k1/k3 × resident/fresh × PQ_A/PQ_B/QB. All 204 v2 qualification requests pass full endpoint/state/vector and 36-layer layout/placement checks. All outputs also match the historical E2 R endpoints. This is a new service driver, not a claim that its timer or implementation is the historical HTTP E2 contract.

| k | Lifecycle | QB / dual PQ | Reduction | Simultaneous 95% family interval | Largest input A/A | Practical gain established |
|---|---|---:|---:|---|---:|---|
| 1 | resident | 0.986617 | 1.338% | [0.965043, 1.006956] | 7.343% | NO |
| 3 | resident | 0.937404 | 6.260% | [0.922603, 0.949354] | 4.125% | YES |
| 1 | fresh | 0.973534 | 2.647% | [0.955904, 0.996512] | 4.699% | NO |
| 3 | fresh | 0.946409 | 5.359% | [0.940517, 0.953312] | 4.388% | YES |

Each primary cell has a Bonferroni-adjusted 98.75% percentile interval, giving nominal 95% family coverage for four registered cells. The paired bootstrap clusters six process sessions and preserves all four cells together. Inputs are fixed, previously exposed examples, not independent runtime sessions.

Established requires upper CI<0.98, point reduction exceeding max(2%,input-aggregate A/A), and improvement in every session. Failure to establish this does not prove zero effect or equivalence. No timing-based input subset is selected.

Within this new stack, the secondary k contrasts favor a larger QB layout effect at k3 in both lifecycles. Individual lifecycle contrasts include unity. The interaction is exploratory; these measurements do not identify CUDA Graph causality or decompose the old E2-versus-service difference.

## Absolute service cost

| k | Lifecycle | Mean dual PQ (s) | Mean QB (s) | Mean QB−PQ (ms) | Reversed blocks |
|---|---|---:|---:|---:|---:|
| 1 | resident | 1.646575 | 1.631283 | -15.292 | 30/72 |
| 3 | resident | 1.358022 | 1.272156 | -85.866 | 9/72 |
| 1 | fresh | 1.690768 | 1.655382 | -35.386 | 28/72 |
| 3 | fresh | 1.371483 | 1.307389 | -64.093 | 8/72 |

The primary ratio is the exponential of equal session/input mean log paired ratios. Absolute seconds/differences above are arithmetic block means and need not produce the identical ratio.

## Paired factor contrasts

These are ratios of QB/PQ layout ratios, not absolute service-time speedups. Intervals are pointwise 95% and secondary/exploratory.

| Contrast | Ratio of layout ratios | Pointwise 95% interval |
|---|---:|---|
| k3_over_k1_resident | 0.950119 | [0.941942, 0.962733] |
| k3_over_k1_fresh | 0.972137 | [0.956121, 0.983815] |
| fresh_over_resident_k1 | 0.986740 | [0.959322, 1.016663] |
| fresh_over_resident_k3 | 1.009607 | [0.994990, 1.024132] |
| interaction | 1.023175 | [1.004200, 1.041466] |

## Native evidence and limits

- Recovered 3542 original and 3537 metadata4 indexed files; both source archives and all 21 numerical DLLs checked. Full core/frontend rebuild completed from a new source/build directory. External CUDA/BLAS numerical DLLs were retained, not rebuilt. Rebuilt executable hashes differ from historical binaries and are separately identified.
- Real E1 q3/layer0/GSM8K443 fixture: twelve replay processes, original and rebuilt × MQ/PQ/QB × two repeats. QK/softmax/AV match authenticated own-arm outputs; MQ own-path and PQ/QB byte identity pass.
- Six historical/rebuilt HTTP requests (R/PQ/QB for each build) match the archived R endpoint. Full input bytes/IDs, state, stop conditions, commands and raw responses are packaged.
- Engineering pilot 25 requests. Initial qualification 135 native requests then Windows aggregate-file replacement failure;69 pending slots remain NOT_RUN. All v1 records remain local. v2 changes recording only, has a new executable identity, and independently reruns all 204 qualification requests. No formal observations are mixed across builds.
- Additional hsc backend counters/callback/full-logit writes are disabled for clean timing; common driver phase timers and state bookkeeping remain included. Counter pilot showed an unresolved approximately 2.9% difference; no counter time was subtracted. Identical inherited backend logging remains enabled. Actual CUDA capture/instantiate/replay/eager/fallback counts are not completely measured, so no Graph causal mechanism is claimed.
- Six sessions ran on one date. Session, leave-one-session, first 3/last 3 and pointwise t sensitivities plus every input regression remain in ANALYSIS.json. Date-level robustness is unidentifiable. Power/thermal admission is checked per session; continuous thermal/clock/energy traces are absent.
- Both weights stay loaded. Resident PQ/QB context pairs remain available throughout each process; fresh contexts are created/reserved/destroyed inside the timer. All cells share the same request implementation, and every request clears/recreates KV state. No prompt prefix reuse.
- Bulk raw tensors/build products/interrupted attempt are local and SHA256 indexed. The compact native fixtures and complete formal result records are in Git and freshly extracted/verified; this does not imply remote delivery of all bulk raw tensors or a third-party audit.
- Historical M3/C3 label-to-implementation mapping remains unresolved. No B570 run, manuscript rewrite, PR merge, publication or extension of the separate PR142 long-input scope.

## Review and reproduction

[Frozen plan](registration/FREEZE.json) · [Full analysis](results/ANALYSIS.json) · [936 timing rows](results/TIMING.csv) · [288 paired blocks](results/BLOCKS.csv) · [Independent raw audit](results/INDEPENDENT_AUDIT.json) · [Raw access](results/RAW_ACCESS.json) · [Request accounting](results/ACCOUNTING.json) · [Native fixtures](results/NATIVE_FIXTURES.zip) · [Native records](results/NATIVE_RECORDS.zip)

Reproduction and timer details: [runtime guide](../../scripts/native_reproduction/rtx_bridge/README.md). Execution freeze commit: `30ad53be0f3e281a2731b05fb2b13a51a00e1bb6`.
