# PR178 implementation candidate: explicit contracts and state transactions

Snapshot: 2026-11-04. This extends the roadmap, not the scientific claim.

## What is implemented

1. A C++17 deployment/dispatch contract and an explicit qualification registry.
   Registry lookup binds device, model, reference, build, runtime, exact geometry,
   types, residency and complete quantization/accumulation/reduction/rounding/
   dispatch descriptors. A matching descriptor is **not** an equivalence proof.
   Evidence labels distinguish empirical replay, structural assumptions and
   bit-semantics claims. The registry trusts the supplied evidence record; it
   does not independently validate a theorem or authenticate an artifact.
   Empirical replay is not admitted by default. The caller must explicitly opt
   into this finite-evidence operating mode, without upgrading its guarantee.
2. Checked independent-group packing geometry: groups of four columns, unchanged
   K, bounded q, contiguous complete coverage and an old-path tail. There is no
   newly invented wide GEMM, shader or performance result.
3. A native-module-owned binding API and graph gate. The gate requires actual
   host-provided dispatch/residency extraction. Missing binding is rejected.
   Keeping the old <=4-column tiled lowering requires a separate qualification;
   it is never mislabeled as the original scalar fallback.
4. A source stager for the exact PR171 packed graph and shared prefix extractor.
   It preserves the source tree, checks unique anchors and writes a fresh output.
   It calls the gate in the actual packed branch and preserves unsupported prefix
   failure rather than silently discarding status while the binding is active.
   A graph rejection is late relative to KV slot allocation: the caller must
   abort and restore the complete checkpoint, not continue scalar in that context.
5. Python single-owner full-state transactions: immutable KV bytes, independent
   initial logits, tokens, positions, pending tokens and deployment/recipe identity;
   taint before any native export/execute; explicit successful decode and full-state
   verification; restoration with complete readback; failure remains tainted.
   Policy restoration, graph rebuild and suffix trimming cannot clear taint.
6. Conservative exact-recipe checkpoint cache. Digests are lookup indices only;
   complete metadata and bytes are compared. No cross-recipe compatibility is
   inferred and no production hit-rate or scheduling claim is made.

## What is deliberately not implemented or not verified

- **Hardware dispatch/residency extractor and GPU qualification: NOT_IMPLEMENTED.**
  Real native module binding and context preflight are implemented and tested on
  Linux CPU. They do not reveal the final CUDA kernel or prove its arithmetic.
- **Python-to-native adapter: NOT_IMPLEMENTED.** The Python state owner remains a
  mock-adapter protocol test. A separate, real C++ `NativeCheckpointOwner` now
  owns a llama context, serializes/restores its memory, and maintains independent
  logits, pending tokens, positions and provenance. It is not a Python ABI.
- **Complete restored source staging and full CPU llama build: PASS** in the
  separate `NATIVE_VALIDATION.json` receipt. The source ZIP SHA256 is
  `b1926827029e0bb8e219861901f2ca3538b330a44f9c6093b5267157dbfcd1ac`.
- **CUDA/Vulkan execution, Windows builds and new reference-relative GPU replay:
  NOT_RUN.** Synthetic CPU model tests establish transactional behavior only.
- **Windows DLL/CRT callback ABI: NOT_RUN.** TLS storage is defined in one exported
  native module, avoiding header-local copies. Linux shared-library/host binding
  and thread isolation were tested. Windows still needs matching compiler/CRT,
  proper exported APIs, callback lifetime discipline and an actual host test.
- No automatic extraction of arbitrary floating-point semantics, proof checking,
  cross-hardware equivalence, arbitrary q/quantization/layout support, partial
  state recovery, multistream, concurrent serving or GPU speed claim.

The stager only protects the existing packed branch (inside its old type and
4<q<=32 guard) and active-scope prefix extraction. Other dtype/q/operator paths
can bypass this branch. Whole-request admission is still a required host task;
this is NOT a fail-closed contract for every runtime operation.

The stager is a candidate integration artifact. It is intentionally fail-closed:
without the still-required native binding, the optimized packed branch rejects.
It must not replace a working production binary until native integration and
qualification are complete. The frozen original scalar binary remains the host
fallback; no unsafe automatic switch is added inside a modified graph.

## Code relationship to existing work

`reference_batching.hpp` is copied unchanged from the verified PR171 source kit,
SHA256 `746cce0b2ef4f1aa5504ff3921a6676f3158e0325f6dca035f81829b1ae8261c`.
Unlike the older PR166 helper, it retains scalar head placement through q=32.
The stager pins and preserves the source's own shared header. It does not merge
or edit historical experimental branches. `ActivationPath` equality still is
not proof of floating-point equivalence.

The existing main `src/query_layout/contract.py` is unchanged. State lineage is
an additional module rather than a change to the old graph-key API. Existing
`state_recipe` concepts are not presented as new.

## Running the checks

From the repository root:

```sh
python scripts/reference_contract/validate.py --output /tmp/hs-contract-validation.json
```

This compiles the C++ gate into a Linux shared library, links the host test,
executes protocol/packing checks and runs Python tests. It downloads no model,
performs zero GPU requests and writes a receipt that distinguishes every
unexecuted native stage. Run it again after any edits; the committed receipt
records file hashes and commands, not a CI success claim.

To stage an already restored PR171 source candidate:

```sh
python scripts/reference_contract/stage.py --source /path/to/restored-packed-source --out /path/to/fresh-candidate
```

For reproducible native CPU validation of the authorized source kit, run:

```sh
python scripts/reference_contract/validate_native.py --source /path/to/candidate --work /tmp/fresh-native-validation --output /tmp/native-validation.json
```

This requires CMake, Ninja and g++, builds CPU only, generates a seeded tiny
Llama GGUF, quantizes it to Q8_0, and tests the actual runtime. No model download
is needed. It applies isolated observer portability and experimental graph
assertion hardening patches after staging. Do not treat these CPU tests as
qualification to deploy the optimized GPU branch.
A unique anchor is a drift detector, not a cryptographic source identity check.
The receipt records before/after hashes so the host can bind it to its pinned
source manifest and reject an unexpected source before native execution.

## Trust and ownership boundaries

All registry/evidence/checkpoint objects are trusted in-process configuration.
They are not an untrusted network protocol and carry no authorization signatures.
A malicious caller can fabricate a receipt; this library does not claim to stop
that. A correct host must get receipts from its separate qualified verifier.

The owner assumes one serialized native context. Callbacks must not mutate a
context outside the owner or mutate the registry during use. Reentrant public
state operations are rejected. Native asynchronous work must be synchronized by
the adapter before export, verification or import completion. An `execute`
callback must return exactly True; false/non-success return codes fail.

`execute_operator` is explicitly **stateless with respect to KV**. It checks
that position, prefix, recipe and deployment do not change. Stateful append,
rollback and scalar retry belong to the state owners and the host verifier.

## Stage gates before any new performance experiment

1. Reproduce the verified CPU source build, then build the target GPU backends.
2. Implement actual dispatch extraction and same-module binding, including runtime
   identity and separately qualified tiled fallback. Do not populate the registry
   with synthetic test receipts or broad unseen shapes.
3. Extend the tested C++ capsule owner to the deployment host and inject native
   import failures; retain independent initial logits/pending/positions.
4. Reuse stored operands for exact qualification and preserve all failures.
5. Only then register a bounded hardware study with unchanged scalar reference,
   equally optimized WB-rechunk and complete costs. No unbounded sweep is implied.

## Native integration and recovery scope

`native_guard.hpp` installs both binding and execution scope in the actual
runtime module for one synchronous decode. It unwinds them before the owner
reconstructs a checkpoint. Runtime preflight reads real context/model fields:
only dense non-SWA Llama/Qwen3, one sequence, causal attention, no flash/MoE,
contiguous append positions, q<=32 and all output rows are accepted. Nested
active scopes are refused. The existing optimized attention assertions are
converted into catchable exceptions only while bound; generic ggml assertions,
allocation failures that abort, signals and device failures are not recoverable
C++ exceptions. This is not a universal crash-recovery system.

Graph reuse is conservatively disabled whenever the old graph or current call
is bound. This prevents a previously authorized graph bypassing a new binding.
The guard is for the existing dense-attention input, not arbitrary architectures.

The source's full state serializer actually writes model identity and memory,
not logits. The owner therefore retains logits separately and never reads stale
native logits after import. Restore builds a fresh context, checks exact state
round-trip plus positions, then swaps it in. A failed restore remains tainted.
It preserves the last verified capsule rather than mutating a failed context
in place. The successful late-rejection test invokes the real Q8 packed-branch
gate after slot allocation and then verifies continuation against an uninterrupted
CPU control. Test-only permission to retain old tiles exercises graph invalidation;
it is not a production qualification and is never installed by default.

Still required before performance claims: actual selected-kernel/residency
extraction at a trustworthy scheduler boundary, frozen original-reference host
fallback, Qwen/GPU full-vector replay and continuation tests, import-failure
injection, Windows ABI tests, concurrency isolation and service-level costs.

Final cloud evidence: 40 Python tests, 643 C++ protocol checks (also UBSan),
47 real Q8 CPU context/guard/checkpoint checks, and the existing native
state test executable reporting all eight cases passed. An independent review
recompiled the native test against the final library and reproduced 47/47.
No CI run, GPU result or acceptance-probability improvement is inferred.
