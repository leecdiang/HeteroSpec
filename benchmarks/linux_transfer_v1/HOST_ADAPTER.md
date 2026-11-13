# Native adapter map and execution latitude

## Exact scientific sources

- Integrated main base: `cfc9edf4582bb3c02885c9171a2ab2635bf19588`.
- RTX source kit: PR195 `873d16712fbf3bc04f54e9b3753515c5dbebb60f`, SHA/size in `pins.json`.
- The kit has `native/cores/loop4`, `native/cores/packed`, `native/frontend`, and
  `samples/R1-Qwen-JOB.json`, `samples/R1-Smol-JOB.json`, `samples/R2-INPUTS.json`.
- Each original file is authenticated by `SOURCE_ASSET_MANIFEST.json`; CUDA source
  is present in the core trees. **Inspect the actual CUDA delta and generated
  instantiation rules** before assuming that rebuilding reproduces the old DLL's
  recipe. The old DLL hash does not establish which Linux compile options to use.
- `benchmarks/tpds_phase1_v1/host_rtx.py` explains final v2 source normalization;
  `benchmarks/rtx_phase_plan_v1/host.py` documents earlier source derivation.
- Pristine reference upstream `0cae43063cf15170e91a2ff4d034da0ecef4a1b2` stays
  independent from both candidate cores. The Linux driver is an explicitly new
  observation/dispatch frontend, not an assertion of Windows executable identity.

## Source/build steps still requiring actual host execution

The authoring environment could inspect repository text but could not materialize
the private binary ZIP or fetch a complete upstream tree, and has no CUDA toolkit.
Therefore these scripts are tested with bounded fixtures, not already qualified
native source. Do not manufacture a successful build receipt from their tests.

`sources.py` authenticates the complete kit, stages two cores and changes known
OS inventory/bootstrap/profiler glue. It preserves all arithmetic/caller code;
unknown Windows calls are listed in PORT.json. Inspect their real uses, implement
native POSIX equivalents in a new epoch, and update the source lock after review.
Do not fake Windows functions to return success. `profiler.inc` remains preserved
as historical input but is not compiled: profile=true raises a real error.

Check final core `llama-ext.h` and custom exports for platform-specific attributes.
Replacing `__declspec` export decoration with ELF visibility is a portability edit;
changing reductions, activation quantization, physical cache extent, output masks
or reference producer arithmetic is not. Track these categories separately.

`build.py` builds every numerical target through CMake (GGML_CUDA/CPU on) rather
than using portable_rtx.py's CUDA-off/static-host-plus-DLL route. Both candidates
must share identical backend source/options; the sole intended core factor is
projection lowering. Preserve legal graph reuse. Record real NVCC host compiler,
architecture, CUDA libraries and flags; never inherit Blackwell-only architecture
flags onto Ampere or silently add fast-math. Incompatible installed tools can be
handled in an approved user-space toolchain, not by changing company drivers.

The static source-link setup is deliberate. Confirm actual backend registration,
thread-local scope/counter identity, CPU buffer allocation and model-layer placement
in the built binary. No silent CPU inference fallback. All CUDA kernels/base/CPU
modules are rebuilt; driver/toolkit libraries are observed system dependencies.

## Reference and qualification adapter

1. Supply exact GGUFs by the SHA256 pins; preserve template and token IDs.
2. `reference.cpp` understands job `inputs` and `cases/forced` records, writes full
   requested frontiers and seq0 state captures, and never calls candidate code.
3. Align candidate configuration defaults with the frozen Linux reference contract
   (threads, n_ctx/n_batch, output reservation, kv types, producer and stopping).
   Freeze R before candidate outputs. Different output-reservation declarations
   must be explicitly qualified, not quietly normalized by changing R.
4. Map captured paths into `compare.py` manifests. Raw serialized equality is a
   conservative first check; use established active-state extraction only after
   documenting the serialization ABI, layer/position mapping and pending boundary.
5. For free output checks candidate `receipt.json` uses `ids`, `endpoint`,
   `service_seconds`, cycles and producer/pending/termination traces; the independent
   driver uses `ids`, `service_s`, pending position and terminal kind. Compare the
   actual token/EOG/cap contract, not JSON object identity or only a text hash.
6. Reuse the independent `trace_from_row` adapter from the reviewed decisive study
   to reconstruct accepted prefixes/rollback/frontier, retaining its real evidence.
   If paths/imports are Windows-specific, adapt them; don't turn missing traces
   into `trace_valid=true`. The new analyzer consumes checked normalized records.
7. Native output counters and module observations are required before clean timing.
   `freeze.py` binds submitted proofs; it is not an automatic scientific reviewer.

Use original exposed boundary witness and a finite geometry/control set first.
Smol remains its own R family. A shared CUDA rule migration is not proof that Vulkan
was ported; company NVIDIA tests are CUDA-only in this protocol.

## Models/primers and CHECKED schema

Create private `models.json` with target_model, draft_model, both `_sha256` fields
and threads. Sourcekit R2 inputs already include16 Qwen roots. Primers are two
separate exposed inputs, e.g. the historical GSM roots; recover their original
native token records from the pinned prior source/sample metadata. No need for a
new large KV download: a small authenticated input file suffices. If not available,
predeclare two already exposed development inputs before outputs; record that
primer policy is a new Linux deployment choice. Never use test roots as primers.

`jobs.py` emits jobs accepted by the reviewed entry. In a new host version check
that a null draft really creates no draft model/context and validate source fields.
Confirmation `CHECKED` records contain id, job_sha256, COMPLETE status,
native_checks_passed, eighteen requests with root/service_s/reference_id/
reference_compatible/trace_valid, and actual_host_clocks. Every flag must refer to
an executed independent check. Receipt paths/hashes belong in the compact evidence.
Missing checks close inference; all existing records remain.

## Freedom without drifting the experiment

Autonomously repair normal compilation, include/ABI paths, library registration,
formatting, module-map resolution, source-archive layout and safe resource handling.
Keep numbered epochs, before/after diffs, failure receipts and required requalification.
A failed helper or compiler is not a scientific failure. Do not stop after discovery,
CPU tests or staging when a normal authorized engineering fix is available.

Don't replace reference/code/model identity, ignore failed vectors, change a frozen
arm/sample/timing window, reset someone else's GPU, lower safety limits or rent
compute. Use separate versions after a freeze. If company authorization or necessary
source access is genuinely absent, report the exact blocker while completing the
non-GPU branch. No self-declared bypasses of native evidence requirements.
