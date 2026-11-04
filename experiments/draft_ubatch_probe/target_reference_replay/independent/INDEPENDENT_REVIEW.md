# Independent audit of the target-reference evidence prototype

Verdict: no remaining blocker was found for the documented offline planning and recorded-byte/metadata consistency scope. This is not a review approval of an implemented native replay engine, GPU qualification, deployment equivalence, or a production fast path.

Reviewed auditor SHA256: `6fd522df4690e0ee718587dd306298addd2b076352e0e85df2264b95d75bf2d1`.
Reviewed design SHA256: `076be0d1a78bcd532c3820235d3f849e70ed37c13a270a7ce89c2b8908fa2b8c`.

## Executed independent checks

- The final 44 upstream artificial tests passed independently under `python3 -O`.
- A separate trace generator covered 408 artificial cases spanning both registered reference prompt recipes, six fixed/mixed rejection patterns, caps 1–17, and EOG/no-EOG contracts. There were 156 EOG terminations and 1188 speculative cycles across these traces. These are byte-fixture control-flow tests, not neural or GPU samples.
- Independently reconstructed query prefixes exactly included the initial prefix and all four actual verification prefixes, including rows after rejection. Every commit prefix matched the independently generated trace.
- Every required query had exactly one capture owner; each owner was a fresh-path leaf containing that query as an ancestor. Available-prefix sets matched independent ancestor closure, without relying on the planner's ownership assertion.
- 24 additional malformed-evidence mutations were rejected, including wrong reference tokens/positions/sequence/caller/freshness, masks, candidate row/output index, erased terminal pending, missing unexamined rows/jobs/observations, typed-value substitutions, teacher-forced free run, and an escaping payload path.
- Independent instrumentation of all successful blob reads matched the reported 5392 bytes and 98 calls for the selected rejection fixture. This is logical read accounting, not unique storage or OS I/O.

The final checks were run with optimization enabled; their conditions do not depend on removable assert statements.

## Concrete defects found and corrected

The historical version compared reference-job observation payloads while ignoring contradictory observation metadata. Setting a recorded prefix to `[15]`, positions to `[99]`, sequence to 9, caller widths to `[64]`, or fresh-context to false still returned `RECORDED_EVIDENCE_MATCH`. It also omitted output-mask and actual candidate caller/row coverage. The final schema checks those fields against reconstructed execution recipes.

The historical payload counter reported 2696 bytes while actually reading 6840 bytes in the selected fixture. Job observations and saved frontier reads were omitted. The final wrapper counts all successful reads; later single-owner capture also changes the amount read, so historical and final counts should not be presented as an I/O performance experiment.

Nested numeric/bool substitutions were initially accepted by ordinary Python equality, for example `[0,0,1]` as a Boolean mask, `[True]*3` as physical widths, float positions, and integer terminal-done. The final typed canonical JSON comparisons reject these substitutions. Such comparisons, query keys, and integrity digests rely on the stated cryptographic assumptions; logits and active-state payloads themselves are directly byte-compared.

Historical code, the executable reproducer, and its accepted-counterexample result are retained under historical/. Those historical accepted results document defects, not current admission.

## Prefix-path reuse: what is established and what is assumed

The planner covers all required prefixes with maximal paths and deterministic capture ownership. Assigning a shared ancestor to one path saves redundant host readout, not the forward replay of that ancestor in other fresh paths. Optional duplicate observations are validated rather than silently replacing the canonical one.

Equivalence to a separately fresh prefix replay is conditional on a native implementation executing the identical fixed prefix history: identical prompt producer, masks, positions, physical partition, context/output reservations, initialization and lifecycle. Each selected observation must complete synchronization and independent copying before the suffix can overwrite buffers. Every maximal path must start fresh and must never import candidate KV or trim/backtrack across branches. These runtime conditions were not executed or proven by this offline audit.

Skipping duplicate readout also removes automatic duplicate-prefix comparisons from other paths. Separately registered stability sentinels provide only their finite observed coverage. The artificial vector function used by these tests depends on the prefix by construction; it cannot prove that a hardware runtime has no history, observer, allocation, stream, or hidden-state dependence.

The fresh-context reference family is not automatically the old resident-reset R deployment. The historical-prefill recipe matches a caller shape, not the complete old lifecycle. The design now explicitly preserves this boundary.

## Resource cross-check

For prompt length 512, output cap 128, k=3, and the two stated no-EOG trajectories, independently reconstructed counts are:

- All accepted: 129 queried prefixes, 32 cycles, 74304 naive replay token evaluations, one maximal fresh path of 640 token evaluations.
- Reject at j0: 509 queried prefixes, 127 cycles, 293882 naive replay token evaluations, 127 maximal fresh paths totaling 73533 token evaluations.
- The separate autonomous scalar run needs another 639 token evaluations in either scenario.

The paired raw-vector and duplicated active-KV formulas agree with those trajectories. The nominal F16 per-token sizes, 144 KiB and 192 KiB, match the current official architecture dimensions for [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B/raw/main/config.json) and [SmolLM2-1.7B-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct/raw/main/config.json), checked on 2026-11-04. Actual GGUF metadata, cache dtype, padding, weights, workspace, allocation, and device admission still require separate binding and measurement.

These are neither wall-clock/FLOP estimates nor complete resource budgets. Context/model preparation, free and repeated runs, readout, metadata, failures and hidden state cost extra. Ideal chunk dedup assumes old committed chunks truly remain unchanged; all active bytes still have to be extracted and compared to detect corruption. Raw 4-byte vector retention is not Python process peak RAM. The final code removes retained per-row Python float tuples, but temporary tuples, raw buffers and JSON remain.

## Evidence and qualification limits

The final status remains `RECORDED_EVIDENCE_MATCH` with `gpu_qualification_established=false`. `binding_complete` is an input assertion, not an independently verified deployment attestation. Self-consistent metadata cannot establish producer truth, extractor correctness, canonical dtype/layout, real device/JIT binding, observation effects, context freshness, or hidden-state equivalence.

The prototype compares an externally trusted opaque fixed-length state format; it does not inspect arbitrary serializers or prove F16 layouts. Full reconstructable raw payloads, online full comparison with retained summaries, and hash-only evidence have different reproducibility strength and must stay distinct. No native/GPU implementation or runtime admission was added or validated in this review.

## Reproduction

```
python3 -O /path/to/auditor/test_replay_audit.py
python3 -O check_audit.py --audit-dir /path/to/auditor --output /tmp/fresh-independent-result.json
python3 -O historical/REPRODUCE.py
```

Use a fresh result path. The historical script intentionally prints accepted counterexamples for the bundled old auditor. All generated byte fixtures are artificial and local. The checker imports the supplied artificial test helper only for the deterministic vector function and payload packaging; its trace generation, coverage/ownership reconstruction, mutations, and resource recursion are separate.
