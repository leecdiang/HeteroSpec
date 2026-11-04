# Independent adversarial review: qualified committed-state execution

Review date: 2026-11-04. This review covers the conditional design and Python abstraction identified below. It neither approves a native optimized path nor supplies a kernel certificate. No native runtime source was edited, no native runtime was executed for this review, and no GPU or user hardware was used.

## Verdict

The revised proposal is coherent as a **conditional design**. No counterexample was found within its stated independent-layer storage, exact-kernel, bounded-write, exclusive-owner, and sound-completion assumptions. The review found concrete omitted obligations and model guard weaknesses; the final design/model incorporates the corrections listed below. This is not a universal proof or a performance result. Production qualification remains closed until the native obligations are discharged.

## Exact reviewed artifacts

Paths below are relative to the parent runtime-qualification directory. SHA256 identifies the precise reviewed bytes; it does not establish their semantics.

- `RUNTIME_QUALIFICATION_AND_COMMITTED_STATE_20261104.md`: `e0b88b081fecb901d573561159cb9096fa94a8994cfc220ceb3789db67c7ed0d`
- `check_transaction_model.py`: `bf70caf1f72c6e1fd16ee504d3e6dc1f776d9dfbc0cbe66fd82c304980508ecb`
- `source_manifest.json`: `3137dd15ff3f55d2f6ce6e1ae6eda6b718e16b2e34cdd43c7a880f4c015515d1`

The final normalized design was compared with the previously reviewed working artifact. Its publication/provenance/path changes do not change the conditional protocol. The final S3 table wording now explicitly requires full reader exclusion or generation-isolated storage plus linearizable publication, consistent with the already reviewed full protocol. All 12 source-file digests in the final source manifest were independently checked against the inspected staged source. This review did not independently rerun archive acquisition, repository publication, native compilation, or prior native validation.

## Findings incorporated in the final revision

1. **Complete preflight is stronger than truthy split flags.** An earlier Python guard admitted empty and incomplete split manifests. The final model checks exact named-stage coverage/order. Independent regression tests now reject empty, short, reordered, and duplicated manifests without numerical-state mutation. Native preparation must additionally account for backend-internal allocations, quantization, padding writes, transfers, fusions, route selection, and captured execution.
2. **Pointer publication does not isolate in-place KV.** A reader holding an old immutable descriptor still references mutable padded KV bytes. The review reproduces contamination by a future-slot infinity before descriptor publication. The final document requires reader exclusion for the whole transaction, including prior device readers until completion, or generation-isolated storage. The Python model still performs separate metadata assignments; it explicitly assumes no observers rather than claiming to implement linearizable publication.
3. **CPU execution settings are part of the reference.** `src/llama-context.cpp:2505–2522` chooses batch thread count and threadpool when `batched` is true. A scalar-shaped node within a multi-token graph is not automatically executing under scalar-reference settings. The revised design requires freezing or qualifying these settings.
4. **Scheduler success is not necessarily full-node completion.** In `ggml/src/ggml-backend.cpp:1802–1848`, an evaluation callback can stop remaining nodes while the scheduler eventually returns success. The revised first domain rejects unmodeled callbacks and requires completed-manifest coverage.
5. **Fallback is a separate state transition.** Ordinary native decode can mutate metadata, fail after earlier ubatches, or leave dirty free bytes. A prelaunch rejection is a stutter only before fallback. The final design requires an invariant-preserving transactional reference fallback or revocation of fast-path eligibility until restoration.
6. **Layer aliases invalidate the schedule argument.** An earlier model admitted shared layer storage. The final model rejects K-layer, V-layer, and K/V aliases, taint, and dirty free tails. The independent suite verifies current alias rejection without mutation. A separately named unsafe fixture deliberately skips admission and reproduces divergence; it is not the current candidate.
7. **Transposed-V cleanup needs disjoint ranges.** An abstract transposed layout test confirms exact per-dimension clearing restores the old state, while clearing the enclosing interval corrupts committed prefix elements. This is address-layout reasoning, not execution of a native F16/CUDA memset.

The final document also captures source-level hazards examined during the coordinated review: `memory_update`/metadata application precede graph execution; later CPU/GPU splits can fail after earlier work; CUDA errors can terminate rather than throw; MMVQ has internal scratch/quantization/padding operations; PDL weakens a simplistic same-stream ordering argument; and graph/capture reuse needs independent allocation/qualification binding. Their presence in the document does not implement the necessary checks.

## Executed checks on the final model

Results are reproducible with the two scripts and JSON files in this directory. Both scripts require the exact model digest above.

- **Supplied baseline:** 54 successful schedule/full-state comparisons, 648 injected abort positions, 648 guard rejections, and 5 deliberate counterexamples.
- **Independent scalar toy:** 500 sampled cases using Python binary64 scalar inputs selected from signed zeros, finite values, subnormals, infinities, and NaN. The toy's original attention is a masked sum of V; both schedules use the same projection function. Inputs here are abstract scalars, not valid native token IDs. This is not special-value coverage of real attention.
- **Independent stronger attention toy:** 200 cases with integer inputs in [-4, 4], using Python binary64 padded QK, softmax, and PV. This separate suite does not establish all-value equivalence or model HeteroSpec's attention kernels, reductions, layouts, or rounding.
- **Continuation:** 18 injected aborts followed by a fresh-binding append match the old-state reference continuation.
- **Premise probes:** deterministic observation between the Python publication assignments sees mixed metadata; an old descriptor sees tentative padded KV; a separate future-K infinity counterexample shows that masking does not remove all physical K dependencies.

The observer probes intentionally violate the toy model's no-observer premise. They demonstrate why native reader exclusion is required, not a counterexample to a theorem that explicitly assumes exclusion. The unsafe alias fixture likewise deliberately violates the independent-storage premise. Current rejection is never misreported as an admitted numerical mismatch.

## What remains unestablished

- Every changed projection must have a real relation bound to actual deployed arithmetic, including quantization, reductions, casts, tails, and compiler lowering. Reusing the same Python `project` function imports this premise; it does not prove it.
- Every native write frame, buffer lifetime, physical anti-dependency, internal operation, and prepared/replayed route must be enforced rather than asserted by caller metadata.
- Host and device readers must obey the owner protocol. Completion must cover all submitted work, including partial submission and output copies. Recovery must finish clearing before reuse; unknown faults cannot yield Clean.
- The complete exposed output/KV/metadata/sampler contract must refine the chosen scalar schedule. Equality against that schedule does not imply equality with arbitrary cold-prefill/chunking recipes.
- The accepted-prefix speculative extension, imports, deletion/shift, shared prefixes, additional devices, and unsupported callbacks remain outside the first theorem unless separately qualified.
- Native correctness, graph-replay correctness, fault recovery, applicability, and net end-to-end benefit require separate authorized experiments. The zero-tail and ghost checks do not establish a hot-path cost bound.

The supplied model is deliberately small and finite. Its full-array equality assertions are verification observations, not a proposed runtime implementation. Atomicity, asynchronous completion, certificates, CUDA semantics, and native API encapsulation remain assumptions. Keeping these boundaries explicit avoids presenting the model as evidence it cannot supply.

## Prior-work boundary

[Vosti](https://arxiv.org/html/2609.38981v1) already composes engine/KV invariants with relational kernel contracts; its paper states trusted compiler/interface assumptions and unchecked input-dependent finiteness for attention. [Taming Bitwise Behavior](https://arxiv.org/html/2609.11356v1) covers equivalence-based tuning, including a supplied reference. The revised proposal appropriately avoids claiming that general composition as new. Its potential distinction is retrofitting a fixed legacy deployment trajectory with transactional execution and a useful compatible path. This review did not reproduce either external artifact.
