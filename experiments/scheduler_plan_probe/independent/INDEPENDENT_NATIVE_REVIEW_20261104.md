# Independent review of the native scheduler dry-veto probe

## Decision

The reviewed implementation is acceptable as **default-off diagnostic infrastructure that always refuses execution while armed**. It is not an enabled fast path, a complete backend prepare interface, an allocation/read lease, a request-level transaction, or a certificate for numerical equivalence. No path was found that converts a matching descriptor into permission to execute while the probe is armed.

This review made no changes to the implementation files or repository. Tests ran on the cloud CPU, with no model or GPU execution.

## Exact reviewed implementation

- `stage.py`: `2edceabefa079d756cc58323e3c43c2cadd745aa402b96b08e617889b7b4d2bc`
- Staged `ggml/src/ggml-backend.cpp`: `bbff3f0856f30b805f8077592d16fc34dbd139a1aa1103588a5a48ce26c68342`
- `hs_plan_probe.h`: `58529b413b893d889b9e1c510dda3816aedcf140842e24b9996ebbc24c175f51`
- `hs_plan_probe.inc`: `9f133424b99dd61369768c28bf1bfe0fb045872f17bcb027066f8e715c7952b3`
- Tested `libggml-base.so.0.23.0`: `13c76b6e7d979f511ef79d86e09bceafdf9fa462d795ab13170e54f50b15a4bc`

The remaining exact library and independent test-source hashes are in `independent_results.json`. Hashes bind this review to specific artifacts; they are not proof certificates.

## Code findings and corrections

1. **Execution boundary.** Armed unallocated schedulers fail before implicit allocation. Armed allocated schedulers compare the diagnostic snapshot and unconditionally return failure before entering `compute_splits`. Matching and unsupported snapshots both remain vetoes. Reset does not silently disarm the probe. Explicit disarm restores the existing scheduler path.
2. **Wrong caller graph.** The first implementation could allocate graph A, capture unrelated graph B alongside A's splits, and report a match. An independent native test reproduced this. The final implementation binds the actual allocation graph, rejects the mismatch, and invalidates that binding on reset and public split operations.
3. **Snapshot coverage.** The review identified missing split graph UID/use counts and transfer source-backend mappings. The final snapshot includes those fields, graph order and active hash entries, source/view closure, tensor metadata, allocated transfer mappings, ring slots/events, and relevant pointer identities. Snapshot comparisons are exact field comparisons, not only hashes.
4. **Lifetime and TOCTOU.** Owner/instance/epoch/caller checks precede deeper comparison; scheduler identity allocation saturates rather than reusing IDs. These checks are useful diagnostics but are not leases. The header requires external serialization and live graph/tensor/buffer objects. Concurrent mutation/free remains outside the API contract. Tensor contents, opaque backend state and hidden resource lifetimes are not certified.
5. **Callbacks and allocation.** No scheduler evaluation callback or backend virtual metadata getter is invoked during snapshot inspection. Snapshot allocation failures are caught and do not grant execution. The scheduler retains its POD allocation lifecycle, with separate ownership of the nontrivial snapshot object.
6. **Synchronous wrapper.** An armed call through the synchronous scheduler wrapper still invokes backend synchronization after the asynchronous entry returns failure. The guarantee is no new split input-copy or graph submission through `compute_splits`, not no backend call or wait whatsoever. The independent test explicitly confirms this distinction.

## Independent native CPU results

`run_independent.py` compiled and ran both independent tests against the exact fully ASan/UBSan-instrumented libraries above, with the test executables also instrumented.

- A matching snapshot remained vetoed, and the output sentinel was unchanged.
- Operator metadata and graph-use-count changes were detected.
- An oversized caller graph count, a cycle, and an unrelated caller graph were rejected.
- Evaluation callbacks were not invoked while armed.
- Reset preserved the veto and did not fall through to automatic allocation/execution.
- Changing tensor data did not change metadata matching, explicitly demonstrating that matching does not certify data or numerical correctness.
- The synchronous wrapper still called synchronization after the veto.
- The ordinary unarmed scheduler reproduced the existing callback-stop counterexample: it returned success after only the first node executed, leaving the final output unchanged. This does not occur through the armed path; it demonstrates why the diagnostic cannot authorize ordinary callback execution.

The implementation's separate native test was also rerun independently: **60 checks passed**, exercising **3 scheduler splits and 3 transfers**. Its fixture uses two real CPU compute backends with test-only isolated buffer-domain tags to force splits. It is not a heterogeneous-device or CUDA-transfer test.

Instrumentation flags were independently checked for `ggml-backend.cpp`, `ggml.c`, and `ggml-cpu.cpp` in the fresh build's compile commands. LeakSanitizer initially failed in the ptrace environment. The successful runs used `ASAN_OPTIONS=detect_leaks=0`; **leak detection was not validated**. The initial failure must not be represented as a complete sanitizer pass.

## Remaining boundaries

- Native context mutation, `memory_update`, metadata application and some allocation work occur before this scheduler boundary. The probe does not make the whole request atomic or restore those changes.
- Zero-tail/padding invariants, exact KV write sets, reader exclusion, asynchronous recovery and atomic output publication remain unimplemented here.
- Backend-internal CUDA allocation, quantization, padding writes, PDL/fusion/graph-capture dispatch and numerical qualifications remain unknown. The unconditional missing-lease/hidden-prepare blockers are appropriate; no matching snapshot may be upgraded to execution authorization.
- Pointer equality is not allocation-generation identity, and copied metadata is not immutable live runtime state. Reuse eligibility is not established.
- Persistent-write markers are conservative diagnostic flags, not a complete physical write-frame proof.
- Per-split copying of shared graph auxiliary tables can cost substantial time and memory. No warm-hit cost or performance improvement was established.

The safe next step is to use this probe to gather structural facts and negative cases while keeping the production gate closed. Enabling execution would require additional ownership, completion, backend preparation and numerical evidence, not merely changing the veto's return value.
