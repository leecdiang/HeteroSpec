# PR174 author-requested review

Pinned result: `aa7ff4e64752be3de0d7974febbce453ae3a96c0` (2026-11-04).
Decision: preserve the completed population-panel result; no AUTO retuning or timing repeats. Permit only the bounded schedule-distinguishing challenge in PLAN.md, with a zero-GPU stop.

## What was checked

Read the result, native serving loop, held-out runner, fitting and selection code, analysis, timing/accounting semantics, common-cohort selection, freeze and published root/geometry records. Independently recomputed all96 published root-level ratios (32 roots x3 contrasts), their10000-draw joint root bootstrap, both fixed-policy geometric ratios, and all32 dense-append schedules. The three registered aggregate ratios and all six family-adjusted interval endpoints match exactly in this reconstruction. This is report-level reconstruction, not a reread of512 raw timings, all raw vectors,7.76GB archive download or independent GPU replication.

## Findings

- Native completion is supported by the submitted execution and reconstruction records:32 held-out roots,512 formal/512 warmups,160 heavy-reference comparisons, separate aligned controls. No blocking contradiction was found in the inspected sources; this is not approval to auto-merge.
- Service geometric means: QB3.007363726s; WB-cut3.002246032s; WB-rechunk3.003072665s; AUTO3.021309640s. AUTO/WB-cut is1.006349782:0.635% slower at the point estimate. Baseline/AUTO family interval is[0.974812905,1.012617483]. No useful AUTO benefit, no equivalence proof, no basis for attributing the small difference entirely to lookup overhead.
- The twelve calibration roots have zero crossings. All selection bins therefore inherit the same WB-cut policy. This is a valid frozen fallback result, not a successful adaptive policy or proof that every possible adaptive strategy is useless.
- New CPU coverage finding: four of32 roots trigger a local physical cut, but31/32 have IDENTICAL ordered WB-cut and WB-rechunk caller sequences. Only root98981480-7f89-4ecf-b87c-ea1419e244df (input00e60d6a-1b9e-4caf-a41c-2851b8829d96), H205, append84, differs: [32,19,13,20] vs[32,19,32,1]. Both have four calls. Whole-panel total calls: QB44; WB-cut48; WB-rechunk48. Append lengths span9..121, median24.5. These are descriptor reconstructions; formal.py checks actual calls against the plans.
- The full saved leaf pool has573/6423 crossed paths and623/9888 crossed QB calls. The32/64-token floor-LCP scenarios are output-free hypothetical policies, not another engine benchmark. Do not infer root prevalence directly from path-weighted prevalence.
- The complete-service timer deliberately charges file-backed snapshot read and cache-map construction/import. Mean import is cumulative from request receipt; the published append interval is cumulative too. This is not a production cache throughput study, and neither a disk bottleneck nor isolated kernel cost is identified by those totals.
- The recorded calibration campaign is2038.781179s, including failed/superseded epochs and coordination wait within that window. It is not an estimate of the irreducible fitting cost of the small selector. No positive measured saving exists to amortize it.

## Manuscript implications

The reference-compatible arithmetic and prior controlled packing results remain valid within their original deployments. This study adds preserved-reference prefix replay and an application boundary; it does not newly measure packed-versus-unpacked benefit. Keep operator packing, local attention grouping, caller chunking and policy selection as distinct claims. Do not use vector/archive volume as novelty, switch the headline to better cache latency, or relabel an AUTO null as a universal failure of parallel execution.

The strongest remaining uncertainty is the active new WB-rechunk comparison, not whether the completed representative panel deserves more repetitions. A small conditional natural challenge can settle that uncertainty but cannot rescue the representative average. If the simple caller wins, simplify the runtime choice and focus the paper on the shared arithmetic transformation. B570 may provide a different backend mapping; it must not be used to hide RTX nulls or to pool incompatible service lifecycles.

## Sources

All relative source paths below refer to the pinned result commit:
- benchmarks/rtx_prefix_reuse_v1/execution/RESULTS.md
- .../worker_service.cpp; formal.py; common_fit.py; common_panel.py; common_manifest.py; analyze.py; details.py
- .../evidence/analysis.json (blob8b5496e3b4bb9771eb8a2cc4edbce546654c35b0)
- .../evidence/common-panel.json (blobd91fe8376e1cf6141a3e356d2023b0ab473693da)
- .../evidence/SENSITIVITY_REPORT.json; SOURCE_POLICY_FREEZE.json
- benchmarks/tpds_prefix_reuse_v1/study.py; selector.py

The author-review environment ran only CPU calculations and16 synthetic selection tests. No new model execution, manuscript change or B570 mutation occurred.
