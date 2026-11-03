# Shared reference batching planner

This candidate extracts the physical-prefix planner used independently by
PR162 and PR163 into one C++17 implementation. It also adds the execution policy
to the native graph-reuse check. The implementation is CPU tested; the staged
CUDA and Vulkan sources still require their native build and model validation.

## Implemented

- `scalar_prefix_requirements` derives each row's physical extent from the real
  cache slot head, occupancy, capacity and scalar padding rule. It rejects
  sparse occupancy, sliding windows, multiple streams and inconsistent states.
- `partition_adjacent` makes maximal contiguous groups with equal physical
  extent and arithmetic/dispatch requirements. It preserves row order. Under
  this equality constraint, every requirement change forces a cut, so the
  resulting number of groups is minimal.
- `PolicyIdentity` distinguishes backend, layout, physical-prefix policy,
  activation precision, head-normalization placement policy and implementation
  version. The adapter checks it in addition to the existing native cache and
  tensor checks. Equal tensor shapes cannot conceal a changed precision policy.
- `projection_requirement` maps observed scalar/batch activation paths to an
  existing F32 batch path or an explicit unsupported result. Its inputs describe
  actual operations; it has no model-name or input-ID branch. This decision API
  is available for the next backend extractor. The source adapter below keeps
  the already qualified Vulkan Q8 implementation unchanged.

The native adapter actually calls the shared prefix extractor and group planner.
Its current graph call supplies the prefix extents; per-row arithmetic and
dispatch IDs use their default values. Extracting those IDs from the backend is
still an extension point, not a completed automatic policy pass.
It retains the original Q/K/V/mask views and backend admission guards. A rejected
prefix state retains the legacy generic path; it is not labelled reference
preserving by this module.

## Source lineage

| Component | Pinned source |
|---|---|
| CUDA prefix implementation | PR162 `e11d2b75d82422409ba2b701aa38c59f36acc50b`, `benchmarks/rtx_llama_repair_v1/host_execution/prefix_extent.py` |
| Vulkan prefix implementation | PR163 `10a70566ce01ab707dbdcc57d8270c1434088f07`, `scripts/experiments/b570_llama_execution_v1/prefix_extent.py` |
| Scalar cache allocation rule | llama.cpp `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`, `src/llama-kv-cache.cpp`, `llama_kv_cache::get_n_kv` |
| Vulkan precision implementation | PR163, `scripts/experiments/b570_llama_execution_v1/reference_q8.py` |

The source adapter accepts a restored final source tree with the original
prefix patch already applied. It checks all expected anchors before writing a
fresh candidate tree. It does not edit the frozen experiments.
The CUDA input must be the PR162 combined prefix/head-normalization source;
the adapter checks that the scalar head-normalization scheduler hook is present.

## API example

```cpp
#include "reference_batching.hpp"
using namespace hs_reference_batching;
DenseAppendState state{765, 4, 769, 769, 1024, 256, 1, true, false};
auto requirements = scalar_prefix_requirements(state);
auto groups = partition_adjacent(requirements.extents);
// extents: 768, 768, 768, 1024; groups: [0,3), [3,4).
```

The extent input is the physical append state after allocating the current
batch, not its logical position or a padded prompt length. The caller obtains
`padding` from the scalar allocator; the current native adapter uses its
`max(n_pad, 256)` rule.

## CPU verification

From the repository root:

```bash
g++ -std=c++17 -O2 -Wall -Wextra -Werror -Isrc/reference_batching \
  tests/reference_batching_test.cpp -o /tmp/reference_batching_test
/tmp/reference_batching_test
python3 -m unittest discover -s tests -p 'test_reference_batching*.py' -v
```

The C++ test compares allocation against an independent scalar loop across
padding boundaries and capacity tails, checks overflow/rejected states, and
compares group counts with exhaustive contiguous partitions. It also checks
equal-shape graph identities under changed precision/layout and projection-path
decisions. The Python checks compile the generated cache method and verify that
source drift is rejected before any candidate is written. They are not GPU
measurements or a full native llama.cpp build.

## Native integration

Restore each platform's final source capsule and reproduce its existing build
first. Then stage one fresh candidate:

```bash
python3 src/reference_batching/integrate_llama_cpp.py \
  --source /path/to/restored/final/source \
  --out /path/to/new/shared-planner-source --backend cuda
```

Use `--backend vulkan` for the B570 tree. Build the new directory using that
platform's existing compiler settings and numerical libraries. The adapter
writes `SHARED_PLANNER_SOURCE.json` with input/output hashes and the explicit
status `SOURCE_STAGED_NOT_GPU_QUALIFIED`.

For the Vulkan worker, enable the existing exported
`hs_b570_set_reference_q8(true)` and `hs_b570_set_prefix_extent(true)` around the
target phases being tested, alongside the layout setter. Reset all three
policies before the original R and draft calls. Preserve producer/consumer
selection and original references. The old Qwen adapter set only the layout;
using it unchanged tests compatibility, not activation of this candidate.

Start native validation with the existing Llama boundary case and the two
fixed-reference Qwen producer/consumer failures
`MATH500/test/prealgebra/1865.json` and `MATH500/test/prealgebra/1804.json` from PR152. In
those Qwen cases, P1 followed by PQ/QB failed while the P4T counterparts already
passed. Enabling the new method only under P4T would not establish repair of
the old failures. Record the actual policy and group/dispatch selections before
interpreting outcomes. A mismatch should lead to the first differing operation,
not changing the reference or replacing the failing input.

## Remaining research work

The B570 backend still has an explicit admitted tensor domain: head dimension
128, 32 query heads, 8 KV heads, q2–q4, physical extent 256–1024 in multiples of
256, non-flash causal attention and its other existing semantic guards. These
guards describe the current kernel implementation and are deliberately retained.
Cross-family activation must inspect actual graph shapes, Q/K normalization and
activation dispatch. A new shape requires a corresponding backend capability
implementation and native evidence; removing an assertion is not support.

The CUDA head-normalization placement repair still identifies Q/K normalization
through its existing tensor role names. Replacing that role identification with
an explicit graph-operation extractor, and demonstrating that the same enabled
rules handle the Qwen producer/consumer cases, are the next method-level tasks.
The shared planner makes this extension testable; it does not establish an
automatic, generally reference-preserving runtime by itself.
