# RTX active rechunk conditional result

Eight frozen, previously unexposed natural roots completed the single bounded PR176 study. This conditional cohort does not replace PR174’s representative AUTO null result. All original numerical arithmetic, scalar R, cache granularity and natural physical offsets were retained. No AUTO training or original-panel extension occurred.

The output-free census contains 6,423 paths / 2,596 roots: 298 paths (260 roots with any such path) have unequal WB ordered schedules; 192 paths (173 roots) have unequal call counts. Excluding the original 44 roots and engineering exposures left 2,552 root representatives, of which 130 qualify. One hash-ranked path per root was chosen before conditioning; the fixed seed selected eight. The exclusion inventory contains 45 roots including one outside the eligible leaf pool. Tile fragmentation totals describe caller geometry, not measured GPU occupancy.

The pre-output freeze was published in commit `372bd5c35ad46f98d61801ad6f726ac98b2361dc` on PR177. The actual PR176 base is `6987317a4a4d4495fa9f1543bf922d978e13d4f8`. No selected outputs existed at publication.

## Numerical qualification and scope

All 32 original-repeat/candidate-heavy comparisons matched every committed full-vocabulary byte and final state. All 144 candidate requests matched original output tokens, pending token, position, actual dense physical head and the complete ordered `(head,width)` CPU plan. Heavy and observer-off qualification both passed; formal measurements use observer-off. Fourteen exposed-synthetic engineering requests also passed original/old/new executor controls. No numerical retry, replacement root, failed native request or discarded performance observation occurred.

The same PR171 packed numerical core serves all three arms. Configuration: Qwen3-8B Q8_0, F16 KV, C4096, non-flash, all-GPU target-only, q32, greedy cap128/native EOG, exact-token file-backed snapshots. Every measured request reads its snapshot and performs index construction/reset/lookup/import. Each measurement has an immediate same-arm warmup; the two sessions load independent model/context instances and rotate all six fixed arm permutations.

## Paired outcomes

Ratios are numerator / denominator; a ratio above one favors the denominator. Absolute differences are numerator minus denominator seconds; positive means the numerator is slower. Equal root/session weights; geometric ratios and arithmetic paired time differences are computed directly per pair. These are descriptive eight-root conditional results, with no 3% screen, significance-based repetition, or population-average claim.

| Comparison | Phase | Geometric ratio | Mean paired difference (s) | Session 0 ratio | Session 1 ratio |
|---|---|---:|---:|---:|---:|
| WB-rechunk / QB | lookup_import_ready_s | 0.979622 | -0.010439 | 0.975039 | 0.984227 |
| WB-rechunk / QB | append_execution_s | 0.960486 | -0.028796 | 0.953151 | 0.967878 |
| WB-rechunk / QB | continuation_s | 1.005962 | +0.015223 | 1.018781 | 0.993305 |
| WB-rechunk / QB | service_s | 0.994379 | -0.024012 | 1.003141 | 0.985693 |
| WB-cut / QB | lookup_import_ready_s | 0.998845 | -0.001507 | 0.982495 | 1.015468 |
| WB-cut / QB | append_execution_s | 1.022445 | -0.004440 | 0.986282 | 1.059933 |
| WB-cut / QB | continuation_s | 0.990885 | -0.022641 | 1.021216 | 0.961454 |
| WB-cut / QB | service_s | 0.989765 | -0.028587 | 1.008004 | 0.971857 |
| WB-cut / WB-rechunk | lookup_import_ready_s | 1.019623 | +0.008933 | 1.007646 | 1.031741 |
| WB-cut / WB-rechunk | append_execution_s | 1.064508 | +0.024356 | 1.034760 | 1.095111 |
| WB-cut / WB-rechunk | continuation_s | 0.985012 | -0.037864 | 1.002390 | 0.967935 |
| WB-cut / WB-rechunk | service_s | 0.995360 | -0.004575 | 1.004848 | 0.985963 |

## Every root and both session directions

Primary QB versus WB-rechunk comparison; all three pairings and every absolute phase time are in `evidence/ANALYSIS.json`. Root indices refer to the frozen selection, never a post-result ordering.

| Root index (H / append) | Phase | S0 rechunk/QB | S1 rechunk/QB | Paired geometric ratio | Mean difference (s) |
|---|---|---:|---:|---:|---:|
| 0 (68 / 405) | append_execution_s | 1.014135 | 1.007077 | 1.010600 | +0.019370 |
| 1 (233 / 48) | append_execution_s | 1.061963 | 0.924288 | 0.990737 | -0.002489 |
| 2 (254 / 52) | append_execution_s | 1.116592 | 1.198720 | 1.156927 | +0.037913 |
| 3 (237 / 49) | append_execution_s | 1.048317 | 0.745670 | 0.884137 | -0.036484 |
| 4 (218 / 90) | append_execution_s | 0.699917 | 1.007016 | 0.839540 | -0.086157 |
| 5 (263 / 521) | append_execution_s | 0.938025 | 0.955736 | 0.946839 | -0.134377 |
| 6 (238 / 34) | append_execution_s | 1.005267 | 0.962302 | 0.983550 | -0.003064 |
| 7 (754 / 41) | append_execution_s | 0.818764 | 0.999411 | 0.904590 | -0.025080 |
| 0 (68 / 405) | service_s | 1.032778 | 1.064626 | 1.048581 | +0.228115 |
| 1 (233 / 48) | service_s | 1.006595 | 0.954165 | 0.980030 | -0.068259 |
| 2 (254 / 52) | service_s | 1.032315 | 1.037405 | 1.034857 | +0.114076 |
| 3 (237 / 49) | service_s | 0.981815 | 1.081500 | 1.030453 | +0.095757 |
| 4 (218 / 90) | service_s | 1.042331 | 0.889015 | 0.962625 | -0.124442 |
| 5 (263 / 521) | service_s | 0.920697 | 0.969954 | 0.945005 | -0.312550 |
| 6 (238 / 34) | service_s | 1.046899 | 0.950655 | 0.997617 | -0.007174 |
| 7 (754 / 41) | service_s | 0.968645 | 0.953796 | 0.961192 | -0.117616 |

The synchronized phases are disjoint: receipt through import-ready; import-ready through final append completion including planning/graph work; append completion through committed response. Their sums equal full service per request. Diagnostic receipt/final-state serialization follows the service boundary; it remains in host wall. Heavy-vector dumping is retained in qualification continuation/service and separately logged. No cumulative geometric means are subtracted.

## Complete cost and retained failures

Exactly 160 scientific requests: 16 original R, 48 heavy/off qualification, 48 immediate warmups and 48 formal measurements. Including 14 engineering requests, 174 were reserved and 174 completed, below the 200 all-stage cap. Zero new calibration/AUTO training requests. Native process wall including all setup, snapshots and evidence I/O: 812.672000 s; recorded service sum: 632.161825 s; recorded model-load sum: 50.948193 s. Per-process context setup (where the inherited worker supports it), snapshot production, observer I/O and host wall are in `evidence/COSTS.json`. These overlapping totals must not be added together.

Original R was not edited to introduce new setup clocks: its context setup remains in host wall. New candidate context initialization is separately logged. The source build receipts and all native logs/manifests are in the raw archive. One CPU command was initially launched from the repository root, producing missing-module/missing-file errors; it started no native request. The same 16 CPU tests passed from the correct directory. A transient pre-study Git fetch connection failure likewise started no request. These operational failures are retained in `evidence/OPERATIONS.json`.

PR174 remains unchanged: AUTO 3.02130964 s versus WB-cut 3.00224603 s (0.635% slower), all three baseline/AUTO intervals cross one. Its 2,026 reserved / 1,957 completed / 69 uncompleted reserved requests and 2,038.781179 s calibration host cost remain inherited costs, not erased or charged again as this challenge’s calibration.

## Decision and stop

WB-rechunk beats QB on the conditioned append point estimate: rechunk/QB = 0.960486 (3.951% less append time), with the same direction in both loaded sessions (0.953151 and 0.967878). Complete service is 0.994379 (0.562% lower) overall, but its direction reverses across sessions (1.003141 and 0.985693); this is not a stable service-benefit claim. The mean paired differences are -28.796 ms append and -24.012 ms service. WB-cut/rechunk is 1.064508 for append and 0.995360 for service, again separating caller mechanics from whole-service behavior.

For natural requests where restarting full-width chunks changes the schedule, prefer the simple WB-rechunk caller where appropriate and retain reduction-preserving arithmetic as the shared contribution. These data do not support a QB advantage over that caller. WB-rechunk does not beat every individual root, and neither a service win nor a population win is established by this small conditioned panel. All root/session reversals remain in the tables and raw records. PR174’s AUTO no-benefit conclusion stays intact; there is no rescue campaign.

RTX GPU work stops after this single study. No B570/PR175 operation, submitted arXiv edit, merge or rented GPU was performed. Portable raw-byte verification and prepare-only replay are delivery checks, not additional model requests. See `REPRODUCE.md` for artifact links and reconstruction.
