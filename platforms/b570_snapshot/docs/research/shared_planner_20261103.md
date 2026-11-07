# Shared planner implementation review — 2026-11-03

## Result

The shared C++ planner and the two native source adapters are implemented and
CPU checked. This is an implementation candidate, not a new GPU result. It
replaces the duplicated physical-prefix calculations and grouping loops, while
retaining the existing backend admission checks and attention views.

The adapter also includes layout, prefix policy, activation precision and
head-normalization placement in graph reuse identity. The historical B570 code
checked the extent vector but did not include the independently mutable Q8
precision switch in that comparison. Fresh contexts in the historical workers
can prevent this from affecting their measurements; the new check is needed
when reusing a runtime across policies. No native stale-graph failure is claimed
to have been reproduced here.

## Source findings

1. Both prefix patches implement the same physical calculation. Under a dense,
   contiguous, single-stream append, row `i` needs
   `min(capacity, max(padding, ceil((head+i+1)/padding)*padding))`, with scalar
   padding `max(n_pad,256)` in the pinned llama.cpp source. The implementation
   derives this from cache occupancy and physical slots, not the output token
   index. The shared code widens arithmetic before rounding and rejects
   inconsistent occupancy/capacity states.

2. The maximal adjacent equal-extent grouping rule is already present on both
   platforms. Extracting it into one header removes duplicate implementations;
   it does not create a new scientific result. The new interface permits
   additional arithmetic/dispatch requirements. The present native graph call
   supplies extents only, so automatic extraction of those additional
   requirements remains unimplemented.

3. B570's Q8 projection repair is independently scoped. It uses the actual Q8_0
   weight type, F32 activation type and explicit F32 precision request to retain
   the existing F32 batch path. The old Qwen adapter sets only the layout; both
   new feature switches default to false. Those Qwen results establish
   compatibility of the old path, not activation of the new method.

4. B570's graph adapter still admits d128, 32/8 heads, q2–q4 and physical extents
   256–1024. The CUDA Q/K head-normalization scheduler rule still identifies
   tensor roles through `Qcur_normed-`/`Kcur_normed-` and q<=4. These are concrete
   remaining obstacles to an automatically extracted, general execution rule.
   They are retained in this candidate; widening assertions alone would not
   establish support.

## Verification actually performed

- C++17 compilation with GCC 13.3.0, `-O2 -Wall -Wextra -Werror`.
- Physical extents matched an independent scalar allocation loop over padding
  boundaries, capacity tails and batch widths; overflow and unsupported states
  were exercised.
- Contiguous group counts matched an exhaustive partition search for arbitrary
  short sequences of extent/arithmetic/dispatch requirements.
- Same-shape identity tests changed precision, layout, prefix policy,
  head-normalization placement and implementation version.
- The source adapter's generated cache method was compiled and executed.
- Both source transforms were applied to actual pinned upstream KV/graph
  declarations plus the saved native graph and the respective prefix patches.
  For CUDA, the existing head-normalization scheduler patch was also applied.
  The original input trees were byte checked as unchanged. These fixtures are
  source-transform checks, not complete restored source capsules or full native
  CUDA/Vulkan builds.
- A separate agent reviewed the shared header and adapter and found no blocking
  numerical issue; its main qualification is recorded above: arithmetic and
  dispatch extraction is still an extension point.

No model requests, new latency measurements, changed references or GPU
qualification occurred. Native qualification must identify the new candidate
binary, not reuse the old PR162/163 qualification label.

## Next informative native test

Use the existing Llama boundary and the two fixed-reference B570 Qwen failures
`MATH500/test/prealgebra/1865.json` and `MATH500/test/prealgebra/1804.json`.
For those Qwen inputs, P1→PQ/QB failed and P4T→PQ/QB already passed. The new test
must activate and record the structural policies under the failing P1 cases,
and retain the original reference and producer/consumer comparisons. A P4T-only
pass would not demonstrate repair of those counterexamples. Diagnose any
remaining first differing operation; do not widen the model list before the
rule can explain this transfer.

## Evidence locations

- [RTX prefix patch](https://github.com/leecdiang/HeteroSpec/blob/e11d2b75d82422409ba2b701aa38c59f36acc50b/benchmarks/rtx_llama_repair_v1/host_execution/prefix_extent.py)
- [RTX combined source builder](https://github.com/leecdiang/HeteroSpec/blob/e11d2b75d82422409ba2b701aa38c59f36acc50b/benchmarks/rtx_llama_repair_v1/host_execution/build_combined.py)
- [RTX head-normalization scheduler hook](https://github.com/leecdiang/HeteroSpec/blob/e11d2b75d82422409ba2b701aa38c59f36acc50b/scripts/experiments/rtx_reference_repair_v1/repair_offload.hpp)
- [Vulkan prefix patch](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/scripts/experiments/b570_llama_execution_v1/prefix_extent.py)
- [Vulkan Q8 activation repair](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/scripts/experiments/b570_llama_execution_v1/reference_q8.py)
- [Vulkan Qwen adapter](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/scripts/experiments/b570_llama_execution_v1/prepare_qwen_adapter.py)
- [Vulkan shape admission](https://github.com/leecdiang/HeteroSpec/blob/10a70566ce01ab707dbdcc57d8270c1434088f07/scripts/experiments/b570_llama_companion_v1/source.py)
- [Scalar allocator](https://github.com/ggml-org/llama.cpp/blob/0cae43063cf15170e91a2ff4d034da0ecef4a1b2/src/llama-kv-cache.cpp)
