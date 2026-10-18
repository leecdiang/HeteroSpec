# PR113 S0 — real native integration completed; GPU stages unstarted

S0 is completed as CPU/source engineering. Original design0fba42fe8732527ca99ceb9c9ee67e93b18e9d80 and its six files are unchanged. PR104 remains sealed at f997262d6b0accb126a1217c9356745cc8bbf708 and PR110 at dae5aea9f9009a686196dd89981c0ae9699ae612/SOFTWARE_FIRST. No old sessions, operator experiments or390-cell model were repeated. Main, PR102, historical values, B570, release and automation are unchanged.

## Actual implementation and evidence

Recovered the complete authenticated PR104 native source and reverified72 complete Q/K/V/mask snapshots in their existing read-only authenticated restoration. No PR11064-key/two-channel crop is used. All15 original family×arm runtime routes, both original binaries,21 numerical DLLs,6 models and original driver/runtime pins passed byte hashes. Large immutable weights/DLLs are referenced, not copied or committed. Full modified native source, three compiled executables, actual commands and CPU raw records are in RAW_S0.zip.

The isolated native server and operator host compile with the inherited Zig/CMake toolchain. Concrete GGML builders implement MQ/PQ/QB/QH_C/QH_D. PQ uses real per-query chains, QB a fourth-axis batch view, QH r=h*q+j and a real compact-versus-dense mask distinction. Permuted Q explicitly packs, contiguous Q only reshapes when legal, dense masks execute REPEAT, K/V remain the original objects, and ordinary output restoration is a real dependency. Diagnostic canonical stage copies do not become hidden clean-timing dependencies. Native request QH dispatch is restricted by the original target mask3 and q>1; q1 retains the original common chain. Original draft/k3/sampler/precision/shader code is unchanged. Original PQ/QB request branches remain in place. A concrete active/layout field rejects inappropriate cached-graph reuse.

Actor glue includes a real CPU-only server entry that calls the same server_schema::eval_llama_cmpl_schema as actual HTTP completions, before common/backend initialization. It consumes the real admitted JSON bytes and native getenv selectors. The transport passes that same immutable bytes object. Commands distinguish effective draft-free k0 from C k3. Original R keeps its original binary; rebuilt shadow and M/C routes are explicitly enumerated with actual binary SHA in RUNTIME_MANIFEST.json, not assumed from one old executable. Future loaded model/output-capacity/full-reference qualification remains separate.

## Actual tests

- 18 supplied helper methods and6 actual transport/sanitizer tests passed;8 independent raw-auditor methods passed, including complete-census/no-fake-PASS negatives, exact ULP, completion timing, missing modules and endpoint validity.
- Built1680 real native GGML graphs:72 full descriptors plus96 source-derived shape descriptors, each×5 layouts×diagnostic-stage outputs on/off. The finite superset covers3 family head/GQA configurations, D64/128, q1..4, permuted/compact Q and source-derived padded KV extents256/512/768/1024 under original ctx1024. Superset shapes have no invented native payload or new long-context evidence.
- 144 actual full-snapshot QH storage-graph cases checked4,177,920 native Q/mask word addresses and1,228,800 synthetic AV sentinel output-restoration words using an independent storage-only interpreter over the actual constructed GGML nodes. It executes no attention arithmetic and provides no numerical-equivalence certificate.
- q1 graph fingerprints agree across all five layouts. Ten malformed native descriptor/geometry cases and two malformed native request cases are rejected. Actual native allow_reuse rejects changed layout, changed active role and changed ubatch; native target/draft prefill/continuation and invalid-role guards pass. Full loaded-model cache lifecycle is still a future S2 check.
- 43 real native parser request bodies passed, covering all3 families×7 future request arms×counts/diagnostic plus QH_D selector. All1009 planned S1 command/wire slots roundtrip. These are CPU parser cases, not model requests.

The complete node registry lists every executable and metadata node, source edge, op parameters, shape, stride and expected output. S0 support entries are deliberately null. The next actual CUDA census must query every node, and the independent audit compares all1680 graph fingerprints before accepting the fixed QH_C-then-QH_D rule. Passing necessary shape conditions or a caller boolean is not full support.

## Four distinct qualification states

| Evidence | Current actual state |
|---|---|
|Native graph/serializer/source integration|CPU checks and compilation PASS|
|Actual CUDA support|NOT_QUERIED|
|Actual CUDA execution/placement|NOT_EXECUTED|
|Numerical own-path/PQ-QB/QH/repeatability|NOT_EXECUTED in this new study|
|Full natural-request R/shadow/M/C qualification|NOT_EXECUTED|
|Cost gain or faster QH|NOT_MEASURED|

The code for direct CUDA-only operator allocation, complete support and buffer-device checks, before/after full input readback, actual loaded-module/PID receipts, bounded ordinary output and diagnostic stages has compiled. The source-named model placement hook is diagnostic-only after scheduler completion and inactive in paid counts mode. None has yet been exercised on CUDA. S0 CPU tests do not upgrade any of these states. The optional query/head lowering has no predeclared positive or hardware result.

## Measurement and monitoring contract

The native completed host timer includes real Q/mask packing, ordinary output recovery and explicit cudaDeviceSynchronize across the process device streams. Raw monotonic ns endpoints are retained for independent duration reconstruction. Build/allocation/transfer/readback and source/module hashing are outside clean windows; each evaluation's complete ordinary output is checked.1 numeric evaluation, or1 warmup+8 clean evaluations, or1 warmup+1 separate diagnostic evaluation are explicit. Standalone CUDA Graph capture is disabled equally by the inherited environment path to prevent unregistered capture evaluations; this operator mode does not claim production actor graph-management costs.

Nsight/CUPTI is not admitted: nsys/ncu were absent from PATH and inspected standard NVIDIA install locations, and no compatible native trace adapter was established. No installation/upgrade or device query was used to check this. Status PROFILE_UNAVAILABLE_PLACEMENT_ONLY; kernel names/durations, DRAM, occupancy, energy and proprietary reduction DAG remain UNKNOWN. Backend placement is a different evidence level from profiling, numerics and full endpoints.

Before-start append-only receipts, fixed one-shot census root, global census-start exclusion, native PID/module evidence and owned watchdog code are implemented. The S1A controller can execute only one support host after exact F0/readback/author confirmation, and cannot auto-launch the panel. Later panel execution requires a separately approved exact slot list and authenticated pre-output selection; failed/already-started coordinates cannot be replayed. Deadline polling is not periodic GPU sampling or continuous residency. Original R remains original runtime with truthful inherited checkpoint semantics; S2/S3 input/monitoring F0s are not supplied by this stage.

## Failures, costs and restoration

Four failed research jobs are retained: a watchdog race on a disappearing CMake scratch file; a native common_json stream-API compile error; a cache-test harness that changed Win32 environment without refreshing CRT getenv; and a UTF-8 source-retention helper initially read using GBK. Fixes stayed within two recorded bounded integration/control scopes. The initial failed8-file native delta was reconstructed and matched every original recorded SHA; exact bytes and intermediate failed candidates remain. A separate raw-readback HTTP404 occurred before its pending push had completed; its response/stderr remain in control_history. Re-fetch after push completion recovered the same immutable bytes. No scientific slot exists or was retried.

Through the completed fresh reconstruction, 21 prior research jobs used 321.865410 driver wall seconds; conservative whole-descendant lifetime charge 2152.713611/3600 seconds. Peak observed process commit was 701,747,200 bytes, not an RSS measurement. Windows Job Object active-process limits and lifetime×limit bounds include assigned compiler descendants; a failed sampling path reports unavailable counters rather than fabricated totals. One heavy research workflow at a time. The final metadata job's additional charge is in its EXIT receipt. Ordinary Git/transport/metadata processes are not globally enumerated.

Current generated artifact directories total 1,009,388,001 bytes; archive-plus-metadata delivery projected bound 1,042,433,722/1,073,741,824 bytes. PDB/object build products are retained locally but excluded from the compact raw archive. Original immutable payload storage is not newly generated output. Final local delivery checks the actual combined artifact bytes again.

RAW_S0.zip: 24,657,113 bytes, SHA256 `60fa03977d01b1b2da251d4c604b91643e12ca78a95ec848b90d64e30263c75b`. Authenticated remote raw data at d4bf7770e43ed5487c0ce4bbda36f648209b6da1 were restored to a new directory. All4205 members passed hashes, and the actual restored native executable reconstructed all1680 CPU graph node records exactly, with zero CUDA initialization/compute. This is actual fresh native CPU reconstruction, not an external audit or GPU replay. New control/restoration receipts supplement the immutable archive in Git.

## Exact next admission

Prospective actual S1 F0: commit69192c49ad2d5cb36a3ad87721f82b13c926dbec; SHA256 `f6c1890917fe4e8aba21c55f89199d21d30d7c6988b28309e99720b7e94fecae`. Its1,811,312 authenticated remote bytes match the local F0;7528 source/input/runtime/reference files are bound. The original design remains unchanged, and each later stage still requires its own exact authorization.

**Pending author confirmation only for S1A_SUPPORT_ONLY:**1 registered CUDA support host, zero graph computes, zero model requests, zero warmups;240s host/128MiB support raw subcaps, within the unchanged S1 total ceiling. One explicit pre-start GPU readiness query uses the frozen driver/name/VRAM, AC1, idle≤5%, temperature≤55C and headroom≥512MiB contract. A gate failure is retained and stops launch. Complete actual per-node census determines QH_C, otherwise QH_D, otherwise no admitted QH; no numerical/latency outcome enters that selection. Selection must be sealed/authenticated before any numerical output stage.

All1009 S1 hosts,2808 graph computes and288 warmups remain unstarted; S2/S3 are unstarted and unapproved. This S0 completion neither authorizes the full panel nor certifies full-request QH support. No new hardware, speedup, portability, accuracy or paper claim follows from CPU integration. The next useful evidence is actual backend support, followed only under new approval by numerical and full-request qualifications and complete costs.
