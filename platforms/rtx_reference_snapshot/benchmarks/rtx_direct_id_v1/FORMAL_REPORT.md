# RTX direct-ID qualification replication protocol v2

This **prospectively frozen direct-ID replication** completed all **270/270 executions**. The endpoint is exact equality of complete direct committed/generated token-ID arrays against the paired TARGET_REFERENCE. Qualification requires exactly 90/90 pairs; there is no partial threshold.

Historical scope: the historical serialized 90/90 count used parsed CLI output text followed by re-tokenization. It was **not a direct generated-ID certificate**. Known cheap batched verification and a captured CUDA numerical divergence informed this new design; it is not blinded discovery or a historically preregistered direct-ID result. No closed campaign is modified or reinterpreted here.

| Execution path | Exact pairs | Wholly exact prompts | Qualification | First divergence range |
| --- | --- | --- | --- | --- |
| RTX_BATCHED_K2 | 75/90 | 25/30 | BLOCKED | 17 through 114 (zero-based) |
| RTX_SERIALIZED_K2 | 90/90 | 30/30 | QUALIFIED | none |

Serialization restored qualification on this tested RTX path. These classifications are scoped to the tested CUDA execution paths, workload, models, runtime and frozen host. They do not establish a universal serialization guarantee, general CUDA nondeterminism, or semantic output failure.

Starting main: `483c4cbd6cd72ae1cdcdbba4534a62fc1786f885`. Frozen source HEAD: `a85b6295c8cb67c3f2d5de62791617253694c64b`. Formal execution/freeze commit: `34b7c1c23a7037742246ddff3c19e5d29d0b6189`. Runtime: original llama.cpp b10839, `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`, Clang 20.1.8 Windows x86_64, original CUDA 12.4 distribution. Host: Windows 11, RTX 5070 Ti Laptop 12 GB, driver **616.92** (historical driver: 616.56).

The original CLI uses an embedded server internally. The study retains that exact implementation. Native `process_token` debug events directly expose committed `result.tok` integers for ordinary and accepted speculative generation. Prompt IDs and unaccepted proposals are excluded; a generated terminal EOG ID is included. The source instrumentation patch is empty, and all original binaries remain unchanged. R0 checked the original six fixed sanity prompts plus the fixed operational regression task HumanEval/50 across three conditions against the original verbosity-4 output, then checked all three reset replays (45 qualified non-formal executions; 21 transcript pairs). Native logs are read through a lossless byte view, so incomplete UTF-8 fragments in draft or committed pieces cannot invalidate ASCII ID extraction. Auxiliary decoded pieces are checked as bytes, never re-tokenized. Its development attempts and review are preserved separately from formal evidence.

Target SHA-256: `408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6`. Draft SHA-256: `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`. Dataset SHA-256: `b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef`. The freeze and build manifests record each executable/DLL hash. The fixed three conditions differ in draft use and target n_ubatch (reference 1, batched 2, serialized 1); all use greedy output, seed 123, cap 128, context 4096, flash attention off and explicit full CUDA0 layer offload.

The 30 tasks and three repetitions were fixed before formal execution. Schedule seed **2026092801** randomized conditions within each task/repetition block. All records, arrays, sidecars, stdout/stderr and commands are retained. Every run passed contiguous direct-ID capture, output-budget, fresh-state and target/draft device/offload assertions. Frozen models, dataset, binaries and environment were checked before and after execution. **No parameter changed after formal data started.** No execution was selectively rerun and mismatches did not stop the run.

`FORMAL_ANALYSIS.json` reports all 180 pair comparisons, zero-based first divergences (including strict-prefix divergence), token values, sequence lengths, mismatch prompts, wholly exact prompts and repeat stability. Operational timing is preserved in raw logs only; no performance analysis, threshold search, subset promotion or alternate reference search was performed.

The independent checker recomputed all **180/180 comparisons** using a separate comparison implementation, recovered IDs independently from native commit logs, and verified 270 unique executions, task/repetition/condition membership, randomized order, frozen source bytes, commands, termination and real CUDA0/full-layer-offload evidence. Independent validation: **PASS**. It also rehashed the actual external model, dataset and runtime binary files on the execution host without invoking the GPU. The portable verifier validates retained file bytes and frozen external identity consistency without an RTX GPU; --asset-root additionally rehashes omitted external assets.

No MLSys manuscript, Figure 3, old figure data or historical evidence file changed. Cross-platform manuscript integration awaits review with the separate B570 direct-ID replication and belongs in a separate PR. This PR is draft and must not merge automatically.

Protocol history: v1 remains **INCOMPLETE_OPERATIONAL_FAILURE**, with 83 executions retained (82 valid), and has no qualification result. Its inference process exited 0 at the failed HumanEval/50 batched execution, but strict whole-log UTF-8 decoding failed on a partial draft-token fragment. V2 repaired only observational transport, preserved every v1 record, passed fresh instrument/byte regression checks, committed a new preregistration and freeze, and restarted the entire 270-execution schedule. No v1 execution is substituted as a v2 formal pair. All outcome counts in this report refer to completed protocol v2. The known v2 R0 development interruption during a chat session change is retained in the R0 evidence; v2 formal execution used durable file-backed background orchestration.

Batched first divergences are stable across all three repetitions of each mismatching task:

| Task | First divergent generated-token index (zero-based) | Mismatching repetitions |
| --- | --- | --- |
| HumanEval/64 | 114 | 3/3 |
| HumanEval/106 | 65 | 3/3 |
| HumanEval/119 | 17 | 3/3 |
| HumanEval/128 | 41 | 3/3 |
| HumanEval/129 | 21 | 3/3 |

All 30 prompts are repeat-stable within each of the three conditions. The serialized path has no mismatching prompt or divergence index.

Portable completed-v2 evidence archive SHA-256: `fc3676adae93c4f21bf6e29d9787d95d1e60d08c2d7223de30fc58c46c3e0822`. See `artifacts/rtx_direct_id_v2/archive_manifest.json` for the content-addressed filename. The archive contains the pre-address report snapshot; this detached address is recorded after compression.
