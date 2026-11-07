# Host-native implementation contract

## Reuse, do not build another supervision framework

RTX starts from `371223b696bb805030c29f04e39eb17b57fb2ebb` (PR171) and authenticates its source/build chain to PR168's original oracle. Read `benchmarks/rtx_operator_frontier_v1/execution/{README.md,RESULTS.md,driver.cpp,packed.patch}` and the inherited `benchmarks/tpds_parallel/` sources. Keep the packed change available to every fixed arm. Inspect the actual existing whole-target append loop: if it already rechunks after cuts, document that alias before allocating an additional arm.

B570 starts from `8ca17478c292275b3515a91b51d0e791a8fae256` (PR169). Reuse `benchmarks/b570_parallel_v1/{worker.cpp,wb_plan.py,binding.py,deployments.py,paths.py,host.py}`. The native worker's `natural()` currently advances its outer offset by the original chunk width; `chunk()` calls `partition()` and finishes all subparts of that chunk. Thus a new alignment-aware caller belongs above `chunk()`, not in the arithmetic shaders. `hs_parallel_groups()` already exposes dense physical prefix groups. Preserve the corrected signed/headroom interpretation (`free<=total` as well as the lower reserve) and the p021 d64 specialization. Qwen target-only is explicit, not an admission fallback mislabeled dual-model residency.

## Required small adapters

1. Native full-transcript tokenization/rendering exporter with exact byte/version hashes; root/message IDs remain metadata only and never influence layout.
2. Cache-prefix producer and restore/bind entry. Store token-level LCP, effective reuse length, actual physical head and complete necessary context state. Check restore shams and no mutation of the retained original snapshot. If only host serialization is implemented, call it snapshot-backed prefix replay and charge it; do not call it a zero-copy resident cache hit.
3. `QB`, `WB-cut`, `WB-rechunk` caller routes sharing arithmetic flags. `WB-rechunk` repeatedly queries the next admitted run for the *current* physical head. Preserve token order, native positions and output-selection rules. Never infer physical head solely from message length where holes or multiple sequences are possible.
4. AUTO selects one route before append from frozen calibrated structural bins. Bind the chosen route and arithmetic state to graph/cache identity. Log the choice outside the hot loop, and charge the lookup within service.
5. Native service qualification exports every committed vector with the same output-row flags as clean service. All-known-append-vector replay is a separate probe if it requests extra rows and changes output-projection shape. Capture only owned pre-reuse buffers. Clean timing computes ordinary outputs without heavy audit dumps; eligibility comes from source-identical service qualification and clean/observer controls.
6. Distinct timing fields: full cache-hit service, separately measured prefix build, model load, warmup, request lifetime and optional traced phases. Actual state import, context setup and synchronization must not disappear between wrappers and phase timers.
7. Read-only reconstruction validates the raw schedule, source identities, complete outcome arrays and timing boundaries. The provided CPU analyzer checks normalized records; it is not a substitute for a native raw parser.

## Admission invariants

Single causal dense stream; no sliding window or fragmented allocator; target-only residency known; supported actual tensor shapes/strides; q<=32; append+cap fits capacity; stable frozen scalar numerical libraries; no undeclared fallback; no concurrent owned GPU workload. Unsupported conditions produce a recorded failure, never silent scalar success counted as a parallel win.

Platform agents may implement these adapters, fix ordinary build/API issues and perform source-reviewed general repairs on development inputs. They must retain failure epochs and perform new qualifications after an arithmetic change. Never patch output IDs, particular tasks, token positions or observed margins to pass.

The bundled `study.py` is a geometry/selection/scheduling/statistics utility only. It does not compile a backend, prove ABI compatibility, provide a Windows Job wrapper or establish native correctness.
