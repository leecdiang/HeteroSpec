# Native CPU capture → fresh replay → offline audit bridge

**Experimental, cloud CPU only, never a deployment gate.** This bridges real native captures into the unchanged offline auditor. It does not establish historical PR151 R equivalence, GPU qualification, resume correctness, or a production transaction fast path. All qualification outputs remain false.

## Exact scope

Two pinned synthetic, untrained tiny dense-Llama models (F32 weights or Q8_0 weights), two layers, 256 embedding dimensions, 128 synthetic token IDs, one sequence, F16 K/V, one thread, no flash attention. These GGUFs have vocabulary type NONE: there is **no real tokenizer or natural EOG qualification**. Synthetic stop positions are separate protocol cases. The same model is used for target and draft, not the production Qwen/Smol pairing.

The producer is one whole-prompt caller with only its last logits requested, then scalar continuation. Target n_ubatch is 1 and output capacity 4; draft n_ubatch is 1/2/4 and output capacity 1. Runtime rounds requested n_ctx 128 to observed n_ctx/n_ctx_seq 256 on this build; requested and observed values are separately recorded. The logical experiment remains bounded to at most 9 output IDs and 7 prompt IDs. PR151 scoped target ubatch4 and its resident-reset lifecycle are **not** recreated.

Three separate OS processes run candidate, forced-prefix reference, and autonomous free reference. The free process receives only prompt/cap/synthetic-stop configuration, never the candidate endpoint or forced-job tape. Each maximal forced path starts a fresh context. Their PID and exact input hashes are retained. Fresh contexts are not proof of historical resident equivalence or immunity to global allocator/cache effects.

`forced_reject_index >= 0` uses additional scalar oracle computation to select controlled proposal paths. These are labeled ORACLE_CONTROLLED_PROTOCOL_PROBE and their calls and costs are included. `-1` uses actual native draft proposals. Neither is a throughput or acceptance-rate benchmark. No draft prefill change is silently folded into a change in target producer geometry.

## What is captured

- Every full target F32 logit vector, including rejected verification tails.
- Every committed target boundary: explicit retained tokens/positions, raw native sequence serialization, canonical complete **active target K/V** bytes, the copied correct frontier logit vector, pending-for-next-loop and unmaterialized emitted suffix.
- Independent forced-prefix reference vectors and active K/V; autonomous free greedy endpoint and every vector.
- Actual decode caller widths/masks/positions, physical microbatch capacity and context geometry.

The sequence parser is deliberately narrow and byte-preserving. It verifies little-endian magic, sequence, stream, dense contiguous positions, two F16 K/V layers, row lengths and V transpose; it rejects unknown layouts and trailing/truncated data. Token IDs are **not present in raw state** and are established by the separately recorded native decode trace. Canonical order is token/layer/K-then-V/component. Each active token contributes 2048 bytes.

This is **not a resumable checkpoint**. Inactive padding, graph/allocator/backend hidden state, sampler state, and complete draft state are excluded. Copied frontier logits are explicit separate payloads; trimming KV does not reset native last-logit storage. No import/restore or reader-lease protocol is implemented.

## Build and reproduce

Use the exact unmodified candidate source from the source kit and the pinned cloud CPU library build. Model hashes and parser-related source pins are checked. The complete library and executable hashes, compiler command, implementation hashes, loaded regular module hashes, and host metadata are recorded. The three source pins bind parser-related files, not the entire transitive compilation provenance. `binding_complete` is the offline schema's recorded identity completeness flag, not cryptographic attestation or a full numerical deployment proof.

```
python build.py --source /path/to/candidate --library-dir /path/to/build/bin --output /fresh/build
python run_matrix.py --source /path/to/candidate --library-dir /path/to/build/bin --binary /fresh/build/bridge --models /path/to/stress-models --output /fresh/matrix
```

All output paths must be fresh. Every attempt, stdout/stderr, raw payload, input and receipt is retained. A failed process is not overwritten or relabeled successful. Full raw data are useful locally but should not be uploaded without checking size.

Metrics separate native decode wall time, sequence export time, payload writing, per-process wall time/peak RSS, unique content-addressed bytes and repeated logical audit reads. These include observation and protocol-oracle costs and do not estimate production latency. They do not measure disk traffic, GPU time, or uninstrumented execution cost.

## Prior failures retained

`run-v1` crashed after writing payloads because text lookup on the vocabulary-NONE synthetic model asserted. It is a failed attempt, not numerical evidence. The corrected implementation explicitly admits only the pinned synthetic ID namespace and performs no text lookup. An intermediate compile caught an invalid std::string-to-const-char* diagnostic call; this was fixed before build-v2. Initial `probe/` material preceded the final three-process design and is not qualification evidence.

The later schema negative test found that unsigned JSON UINT64_MAX could wrap to signed -1 for `forced_reject_index`. Build-v2 incorrectly accepted it as the native-draft mode. Build-v3 checks unsigned bounds before conversion; this was a configuration-validation bug, not a GPU or target-arithmetic counterexample. The independent malformed-input attempt is retained.

## Final local result and evidence replay

The final 16-case matrix (two models × initial, rejection at 0/1/2, bonus, accepted termination, synthetic stop, native draft) completed 48 native processes. All 112 target vector uses and 40 committed target snapshots matched independently forced fresh paths. This corpus wrote 1,649,680 raw native payload bytes; per-case content-addressed bundles total 1,520,648 bytes. The offline auditor counted 3,216,384 repeated logical byte reads. Aggregate measured native-process wall time was 0.839 s, decode instrumentation 0.229 s, sequence export 0.00270 s, and offline audit 0.101 s, on this tiny synthetic CPU workload only. These single-run observations are not a statistical benchmark or a performance extrapolation.

The full lossless local content-addressed JSON archive contains 920 files and was restored byte-for-byte and re-audited. **That generated archive is not uploaded in this directory.** Its exact SHA256 and byte count are in LOCAL_ARCHIVE_MANIFEST.json; the roundtrip receipt describes a local verification, not remote artifact delivery. All shipped evidence is synthetic, and no user prompt or token data is included.

Generate a new complete corpus with the build/matrix commands above, then archive and replay it locally:

```
python archive_matrix.py --matrix /fresh/matrix --archive /fresh/matrix.json
python archive_matrix.py --archive /fresh/matrix.json --restore /fresh/restore
python -O recheck_archive.py --matrix /fresh/restore
```

A newly generated corpus will have new timestamps, paths, process IDs and timing observations, so its archive hash will differ. The shipped summaries and independent review establish what was observed locally; rerunning the commands is necessary to obtain fresh native payloads. Archive replay proves record consistency, not producer truth, numerical universality or GPU qualification.

Independent testing also found and fixed an evidence-retention bug: retrying the controller with an already existing output directory could change its old receipt to FAILED in the exception handler. The corrected controller only writes failure receipts into a directory created and owned by that invocation; preflight failures now get their own fresh receipt. The reviewer retained the before/after counterexample, and the final matrix was rerun with the corrected controller.

## Synthetic fixture prerequisites

The model generator and stress transformation are already in the parent directory's [reproduction instructions](../README.md), [make_stress_fixture.py](../make_stress_fixture.py), and [quantize_fixture.cpp](../quantize_fixture.cpp). Generate the original tiny Llama with the frozen source's `test-llama-archs -a llama -s178 -o <fresh directory>`, apply the five-norm stress transform, then quantize using that same CPU runtime. This bridge accepts only the two complete hashes in MODEL_PINS.json. No user prompt, token tape, model, or trained-model weights are included; all prompt IDs here are the literal synthetic `[1,2,3,4,5,6,7]` and all outputs derive from these fixtures.

The library admission is intentionally pinned to the archived cloud build. A rebuild under a different compiler, path, options or dependency version may have different hashes. Such a build is a **new experimental identity**, not permission to silently edit old receipts or claim old R. This package provides the executable build command and observed artifacts, but does not claim cross-toolchain bit-reproducible llama library builds. New source/model/runtime families need separately recorded pins and a fresh full validation dataset. The source kit SHA256 is b1926827029e0bb8e219861901f2ca3538b330a44f9c6093b5267157dbfcd1ac; no source-kit or library binary is copied into this directory.

The machine-readable boundary is also in SCOPE.json: `recovery=UNPROVEN` and `resume_authorized=false`.

## Independent review

The unchanged `independent/` bundle includes portable programs and exact historical counterexamples. The reviewer reproduced the final binary hash from an independent compile, reran 18 cases/54 processes (including longer cap9 rejection chains), and checked 178 complete vector uses and 58 committed snapshots. Separately, 34 required prefixes each ran in their own reference process; all 34 vectors and 10 requested KV payloads matched the maximal-path observations. Fixed-layout extraction passed 12 sentinel layouts and rejected 21 structural corruptions; native schema validation rejected all 31 malformed configurations. Twenty-five actual-evidence corruptions were rejected under Python `-O`, including K/V permutation, endian changes, terminal pending/frontier, producer masks and contaminated free/reference metadata. Output ownership and failed-preflight receipt preservation were independently rechecked after their fix. These are finite diagnostic tests, not universal arithmetic, lifecycle or GPU proofs.
