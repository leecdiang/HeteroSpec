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

- **Native host extractor/binding: NOT_IMPLEMENTED.** The backend must expose the
  actual selected kernel/reduction and bind the gate in the same native module.
  The provided C++ callback interface is not that hardware-specific extractor.
- **Real llama.cpp adapter for Python StateOwner: NOT_IMPLEMENTED.** It must restore
  the separately maintained initial logits and pending-token semantics, not only
  call llama_state_seq_set_data. The tests use an explicit mock native adapter.
- **Full PR171 source staging: NOT_RUN.** Complete restored llama.cpp source is in
  host/release assets, not the main repository. The source tests use pinned-anchor
  fixtures and do not stand in for a complete source-tree test.
- **Full llama.cpp compilation, CUDA/Vulkan execution and new bitwise replay:
  NOT_RUN.** CPU header compilation and graph-source transformation are distinct.
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

`reference_batching.hpp` is copied **unchanged** from PR166 commit
`abd36bea639bf814159ad68ab015bc983c5338b1`, Git blob
`a0baff824a1b54fb3867845372939b9a97c11115`. It retains existing physical extent and
projection policies. No historical implementation, evidence or manuscript is
rewritten, and no experimental PR is merged. The new gate does not claim that
its old `ActivationPath` equality proves numerical equality.

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

Do not use the output for model execution until the native binding, complete
checkpoint adapter and actual backend builds have been implemented and audited.
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
rollback and scalar retry belong to StateOwner and the future native adapter.

## Stage gates before any new performance experiment

1. Obtain the pinned full source capsule; run the stager and complete native builds.
2. Implement actual dispatch extraction and same-module binding, including runtime
   identity and separately qualified tiled fallback. Do not populate the registry
   with synthetic test receipts or broad unseen shapes.
3. Implement a real full capsule adapter with initial logits/pending/positions;
   inject failures before append, after allocation, during decode and during import.
4. Reuse stored operands for exact qualification and preserve all failures.
5. Only then register a bounded hardware study with unchanged scalar reference,
   equally optimized WB-rechunk and complete costs. No unbounded sweep is implied.
