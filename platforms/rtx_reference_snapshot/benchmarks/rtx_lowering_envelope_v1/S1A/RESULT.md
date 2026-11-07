# PR113 S1A: actual complete CUDA support census

Executed once on 2026-10-15, under explicit human approval bound in `../registration/S1A_AUTHOR_APPROVAL.json`. Original reviewed protocol and the S1 F0 are unchanged. Actual native support predicates admit **QH_C** by the predetermined C-then-D rule. This is support qualification only.

|Layout|Fully supported / registered graphs|Supported / queried nodes|Executable node queries|
|---|---:|---:|---:|
|MQ|336 / 336|2184 / 2184|1848|
|PQ|336 / 336|8232 / 8232|5880|
|QB|336 / 336|3318 / 3318|1848|
|QH_C|336 / 336|3372 / 3372|1650|
|QH_D|336 / 336|3624 / 3624|1902|

All 1680 actual graph records matched the frozen native CPU node identities, shapes, strides, source edges, operation parameters and metadata classification. All 20,730 node support queries returned true; no unsupported node is omitted. Each layout covers all 72 full snapshot descriptors and the 96 finite source-derived shape descriptors, with stage outputs both disabled and enabled. Registry shapes do not constitute numerical tests at larger contexts. Node query counts are graph-construction counts, not measured kernel launches or latency estimates. Actual placement remains null, since no graph was allocated or executed by this census.

## Starts, admission and environment

Exactly one readiness query and one native census host, PID27920; controller PID33332. Controller began 2026-10-15T11:44:24.488260Z and ended 11:44:40.884091Z. Native owned lifetime including exit/audit handling was 1.607550600s against the 240s ceiling; readiness query 0.058216400s. Graph computes0, model requests0, warmups0. No failed or missing support slot, no scientific retry, and no other scientific stage started. Historical S0's four engineering failures and transport failure remain unchanged and are not erased by this success.

The single pre-start observation matched RTX5070 Ti Laptop, driver616.92,12227MiB nvidia-smi total, used0MiB, utilization0%,41C,AC1. CUDA initialization independently printed12199MiB and capability12.0; preserve both tools' reported totals rather than treating their differing definitions as interchangeable. The frozen admission policy specifically uses nvidia-smi total. Power scheme GUID was registered metadata but not checked by the admission function. No periodic GPU monitoring or continuous-residency evidence was collected.

All7528 F0 file identities passed before the query. Six actually loaded pinned numerical libraries (ggml-cuda,ggml-base,cudart,cublas,cublasLt,libomp) passed exact runtime-directory/SHA checks. The21-library manifest was not a claim that every library must load. Complete actual loaded-module paths and post-exit hashes, including Windows/driver and existing Windhawk injection modules, are retained in MODULE_AUDIT. Non-numerical injected/system modules are observations, not a claim that every loaded module was prospectively pinned. No library/driver/toolkit installation, injection change, or runtime substitution was made.

F0: commit69192c49ad2d5cb36a3ad87721f82b13c926dbec; SHA256 `f6c1890917fe4e8aba21c55f89199d21d30d7c6988b28309e99720b7e94fecae`. Selection exact-byte SHA256 `1f672d562428b4e8f31e16c1239e43c7349504414134ac3884d6a13d37cbec6b`. The historical F0 readback receipt's NOT_GRANTED describes its earlier registration time; the new explicit approval is a separate receipt.

## Evidence and limits

RAW_S1A.zip contains all support/controller raw, the global immutable before-start receipt, complete expected node registry, F0/approval, admitted full descriptor plan, loaded-module hash audit, source provenance and CPU reconstruction code. RAW_MANIFEST binds every member. The complete modified native source/binaries remain in the authenticated S0 archive at d4bf7770e43ed5487c0ce4bbda36f648209b6da1, bound again by this F0. Original full snapshots/model/library bytes remain sealed read-only. No crop, fabricated tensor, arithmetic simulator or five-name alias was used. Authentication and fresh-restore receipts supplement this immutable raw archive after its commit.

Backend support: PASS on this finite registry. Executed CUDA placement, input lifetime/mutation controls, QK/softmax/AV numerical correspondence, full natural-request endpoints, and complete costs: **NOT_EXECUTED / NOT_MEASURED**. PROFILE_UNAVAILABLE_PLACEMENT_ONLY remains unchanged; no kernel-time, DRAM, occupancy, energy, reduction-tree, QH-speed or hardware-benefit claim follows. There is no replacement or expansion of PR104/PR110, main, papers, B570 or automation.

## Exact next gate

Stop after authenticating complete census and fixed selection. The proposed next scope is only the full-tensor numerical substage: the predeclared720 `kind=numeric` slots,72 contexts×5 layouts×2 fresh repeats, one complete graph computation per host, zero warmups and zero model requests. The executor calls this authorization `S1B_EXACT_SLOTS`; this does **not** authorize the protocol's timing/profiling S1B. `NEXT_NUMERICAL_PROPOSAL.json` contains the exact original ordered IDs, unchanged F0 and caps. Original MQ/PQ/QB controls, q1, repeatability, finite outputs, placement and immutable inputs must qualify; all finite q>1 differences remain results and cannot change QH_C. No automatic start without separate author approval. S2/S3 remain unprepared and unapproved.

S1 budget consumed:1/1009 native hosts,0/2808 computes,0/288 warmups,1.607550600/7200 owned native seconds. Stage remainder is an upper ceiling, not authorization. All new raw/restoration/delivery bytes are charged to S1's separate4GiB bound, with actual accounting in DELIVERY.json. Old S0 allocation is not reused.

## Sealing and fresh reconstruction completed

Data commit `b5e7b501138acbc7296cd02b25716169e66ea5b9` was pushed before readback. RAW_S1A.zip is1,817,572 bytes, SHA256 `1ca56d05a4811df1158021194af0a0aece46ce376d8024b04efe7b942cac49da`, containing35 members /77,240,047 uncompressed bytes. Actual authenticated identity-encoding downloads of archive, manifest, selection, full analysis and reconstruction script matched the committed local bytes. A new-directory restoration verified every member and recomputed the complete analysis byte-for-byte on CPU, including every node identity/support predicate and fixed selection. It started zero new GPU hosts, graph computations, model requests or device queries. AUTHENTICATED_RAW.json and FRESH_RESTORE.json record these facts.

One post-experiment transport failure is retained separately: the first `gh` raw response failed with `transform: short source buffer` and23 retained response bytes. A second transport implementation read the same immutable commit with authentication held only in memory and explicit identity encoding. This was not a new support attempt; support failures remain0, transport failures1. No response/source/failed attempt was replaced. The raw analysis's zero control-failure count describes the census/controller execution, before this subsequent readback failure.

The1.607550600s native-host interval is not a graph latency or an exclusive kernel time. Controller wall elapsed16.399829388s includes freeze hashing, readiness and raw audit; the0.058216400s readiness query is inside that wall interval, not an independent interval to add to it. Report both native and controller envelopes; even the conservative whole-controller bound is below the7200s stage ceiling. No positive execution-cost result follows from support census wall time.
