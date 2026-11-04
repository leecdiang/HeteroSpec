# Native scheduler plan inspection and fail-closed dry veto

This is a **diagnostic subsystem**, not the proposed cheap transaction fast path. It adds a real pre-copy/pre-submission boundary to the frozen scheduler and validates an immutable metadata snapshot against the current allocated plan. It has no mode that grants execution. An exact match returns `MATCH_DRY_VETO`, and an armed scheduler always returns `GGML_STATUS_FAILED`.

No changes are made to llama decode, attention ordering, KV storage, reference arithmetic, graph reuse, or CUDA capture. No production qualification is created. Ordinary scheduler execution remains unchanged until a caller explicitly arms the diagnostic gate; an explicit disarm restores the ordinary path.

## Why the requested full fast path is not implementable at this boundary

The actual frozen sources show `llama_context::decode` calls `memory_update(false)` and prepares/applies memory metadata before graph allocation and scheduler compute. The current graph puts future query KV writes before earlier attention. A scheduler hook cannot undo these effects or establish exact per-query `write KV -> attention read -> next write` ordering. Prefix extents alone do not restore the zero/free/padding bytes that attention can read.

The scheduler exposes all assigned splits and transfer tensors after allocation, but does not expose a closed backend launch/resource plan. The CUDA MMVQ path still allocates pool scratch, quantizes and can clear padding during execution. CUDA capture, fusion, PDL and error/abort paths add further obligations. This code therefore **does not** advertise a full all-backend prepare, bounded rollback, zero-tail owner, atomic output publication, reader lease, or immutable resource generation.

The useful subset implemented here is an actual all-scheduler-split census and a reliably closed diagnostic boundary, with native tests showing it refuses a stale/unsupported plan before the first split's input copy or graph submission. It is useful for future plan extraction and graph-reuse falsification without pretending those missing mechanisms exist.

## API and immutable evidence

`hs_sched_plan_capture(sched, graph)` requires a successfully allocated nonempty graph and the exact original graph bound by that allocation. It deep-copies checked descriptor fields rather than retaining only graph pointers or digests:

- Caller and every split's ordered nodes, split boundaries/backends and actual input/copy tensor mapping.
- Tensor types, dimensions, strides, operation and all operation parameters, sources, views/offsets, flags, data/buffer identity and buffer usage/context/size.
- Graph UID, evaluation order, visited hash entries and use counts, plus gradient-table identities.
- Scheduler identity/epoch, current/next copy ring indices, events, eval callback identity, and backend/device/context/compute-entry identities.

There are no scheduler eval callbacks or backend virtual metadata getter calls in extraction. Source/view cycles, capacity violations, empty plans and malformed/missing transfer bindings are rejected. All C API allocation/inspection exceptions become null/error/rejection. Snapshot instances are opaque and immutable; arming makes its own copy, allowing the caller to free the original. Scheduler instance IDs saturate rather than wrap; reset invalidates the allocation graph/epoch but **does not silently disarm** the gate. The next compute then refuses before automatic reallocation.

A structural match is not numerical equivalence. Content-only input changes intentionally still match, and are tested. Opaque backend/extra contents, thread settings, allocation lifetime, arbitrary data/padding bytes, backend internal preparation and completion are not certified. Backend pointers are identities, not allocation-generation leases. Every snapshot carries `NO_READER_LEASE` and `HIDDEN_BACKEND_PREPARE` blockers. Callbacks, parallel copy rings and potential persistent-write/view-alias nodes receive additional conservative blockers.

The caller MUST serialize all access to the scheduler, graphs, tensors and buffers, and keep them alive during capture/compare/compute. The tool does not prevent raw-pointer mutation or C++ data races. Matching metadata cannot authorize graph reuse. No optimized execution is permitted even on a matching graph, so there is no check-then-launch escape.

## Exact side-effect boundary

The gate is inside `ggml_backend_sched_graph_compute_async`, immediately before `compute_splits`, after existing allocation if the scheduler was already allocated. An armed unallocated scheduler refuses before automatic allocation. The accepted guarantee is **no new copy or backend graph submission from this call's split execution**.

It is not “no backend call ever”: the synchronous wrapper still calls `ggml_backend_sched_synchronize` after an error, preserving legacy semantics. Previously submitted work can complete or fail there. Allocation/clear, graph construction, callbacks outside this boundary and earlier llama memory updates are not rolled back. There is no CUDA-fatal-error recovery claim.

## Actual native CPU tests

The reproducible test uses two real CPU compute backends with test-only distinct buffer domains. This prevents the scheduler from collapsing them into one split and creates three real splits with three real transfer tensors. It is not a heterogeneous-device or GPU test. A test-executable symbol interposition counts the real exported tensor-copy calls, and a test backend wrapper counts real compute submissions. No production counter hook is added.

60 checks pass in the normal harness and UBSan-instrumented harness:

- Capture before allocation and wrong-graph capture refuse.
- An immutable copied plan survives freeing its original capture handle.
- Exact-match dry veto, operation/stride/source/data-address/dimension/flags/view-offset/buffer-usage/UID mutations refuse with no copy or compute submission.
- Content-only data changes remain metadata matches but still cannot execute.
- Eval callbacks are marked unsupported and never called under the gate.
- Malformed node count and cyclic descriptors refuse.
- Reset keeps the arm latched and refuses before reallocation.
- Explicit disarm executes the original three-split graph, performs the expected transfers and produces all16 expected output values.

The initial simple two-CPU setup collapsed to a single split; it was replaced rather than reported as multi-split evidence. An initial sentinel fixture overwrote a reused input allocation; marking fixture inputs as retained outputs corrected the test ownership. These are test corrections, not runtime numerical fixes.

The regular full native CPU libraries are built from staged real sources. The initial UBSan run instruments only the test harness. A subsequent fresh build instruments all three ggml libraries and the harness with AddressSanitizer and UBSan; all60 checks pass. LeakSanitizer cannot operate under this environment's ptrace, so its original failed log is preserved and the same sanitized executable is rerun with ASAN_OPTIONS=detect_leaks=0. Leak detection is explicitly not tested. VALIDATION.json pins the final instrumented libraries. Independent review is recorded separately once final binaries are checked. GPU execution, Windows ABI and whole-model continuation are not tested here.

## Reproduce

From the repository, first run `cd experiments/scheduler_plan_probe`. The supplied source must match the frozen scheduler pin. Use a new work directory. After the build, independent checks run with `python independent/run_independent.py --source /fresh/work/source --lib /fresh/work/build/bin`. For the fully sanitized build also pass `--sanitize address-undefined` and set `ASAN_OPTIONS=detect_leaks=0`. No GPU or model is required.

    python validate.py --source /path/to/authorized/staged/source --work /fresh/work

For whole-library sanitizers in this ptrace environment:

    ASAN_OPTIONS=detect_leaks=0 python validate.py --sanitize-native --source /path/to/authorized/staged/source --work /fresh/sanitized

Requires CMake, Ninja, a C/C++ toolchain and the already authorized native source kit/staged tree. No downloads, GPU or user computer are used. `stage.py` requires the exact frozen scheduler SHA256 `5a9094517d11dcafe43c51af97bfe3d6afe75d73096be4b899bae7025b1edd31` and a new output directory. The receipt pins the stager, probe, test sources and built libraries. A matching digest is identity evidence only.

Extraction copies metadata and currently can scan shared hash/use-count tables once per split, giving an O(splits * hash capacity) component. It is intentionally disabled by default and is not described as low overhead. No throughput result is claimed. A future compact plan can deduplicate immutable tables only after preserving complete validation, owned-resource leases and all hidden-backend obligations.
