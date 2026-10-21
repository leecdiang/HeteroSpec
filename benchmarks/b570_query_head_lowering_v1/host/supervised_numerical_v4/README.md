# B570 targeted numerical v4 — CPU qualified, GPU unstarted

Review base: `02ac1d7313cb9d29617cda122c4c7556c7f2289e`.
New run: `b570-supervised-numerical-v4-20261016-01`.
Independent output root: `C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/host_outputs/supervised_numerical_v4/b570-supervised-numerical-v4-20261016-01`.

The task completed real supervisor changes and CPU fault tests, not a GPU restart. Old S1, diagnostics, v2 and v3 remain byte-preserved history. v3 remains 117 started /116 admitted (1 census +115 numerical) /1 invalid /44 unstarted. No old output qualifies a new v4 sample. QH_C stays primary. [POLICY.md](POLICY.md) is the exact stop/monitoring/numerical policy.

## Directory diagnosis and actual CPU evidence

v3 workers.usage repeatedly enumerates all files under both source/output roots, then re-enumerates the run tree, then stats its file list again for export reserve. Frozen files and current growing files are therefore repeatedly read. Actual bytes and the additional raw-export reserve are intentionally separate charges, not an accidental claim of twice the physical storage; the repeated metadata work is avoidable. Full module/output audits are separate and remain mandatory.

The unchanged v3 valid directory reads have max duration578ms at indices0..29,531ms at30..59,781ms at60..89 and844ms at90..115; max initial completion812/672/922/985ms. These bands show growth plus OS/cache variance, not a monotonic fitted law. Failed index116 has an890ms discarded read and no valid initial completion by1016ms; it stays invalid. Neither its observations nor old v2's undecomposed1.032s are reclassified.

Pure CPU tree:160 directories, each50 files under two leaf directories;8,000 files,262,144,000 real bytes. Old-style two-pass scanning of1,000/2,000/4,000/8,000 files measured141/297/578/1094ms maxima across three measurements per size. At8,000 files all three measurements exceeded1 second (1078/1078/1094ms). These are CPU filesystem measurements, not GPU timings.

In the actual new supervisor path on that tree, eight admitted live directory reads took at most16ms while a writer appended2MiB. Full prelaunch inventory took922ms, outside native coverage but inside engineering cost. The same resource and directory streams still use the original strict integer1e9ns rule. Two ReadDirectoryChangesW threads protect the sealed baseline; any sealed change, notification loss/overflow/API error or watcher gap invalidates it. Runtime scanning is limited to the active slot with a full32MiB/256-file reservation. The next slot rebuilds its complete baseline; full post-exit output scans are retained. There is no claim that arbitrary scheduling will always fit1s: any future miss stops.

Final fresh suite:27 CPU tests pass, including real child/monitor/auditor processes,8,000-file late-tree concurrent writes, growing/new sealed-file invalidation, active-byte/file-count caps, pre-spawn budget rejection, exact threshold±1ns, slow reads, waiting-GO identity delay, post-exit hash delay, bad module hash, absent/truncated output, monitor death, timeout/crash/fast exit, poll/read exit races and unchanged old failure classification. Notification parser overflow/malformed negatives invoke the actual parser deterministically; no claim is made of forcing a genuine kernel queue overflow. All five preparation attempts are retained: the first23-test and second24-test suites passed; the third26-test suite found a CPU analyzer import-name collision; the fourth26-test suite passes after renaming the independent tool; the final27-test suite also covers preservation of lifecycle evidence after a watcher cleanup error. A separate CPU metadata executable consumes all69 actual serialized wires, emits80 census +68 numerical descriptors, and checks the actual census/execution graph identity and independent address/GQA/mask semantics. It does not execute a graph or load a GPU library.

CPU preparation has111 actual supervised CPU child PIDs,222 monitor/audit CPU worker processes, and four additional CPU metadata processes; five test-suite controllers/build tools and offline/freezing/delivery tools are separate. Suite wall sum123.953s. The final positive complete-slot CPU maximum is2.484s. BUDGET.json recounts actual non-null PIDs; a pre-spawn rejection is not a child process. Early attempt02's lifecycle-row count is preserved and explicitly corrected in this recount. No claim these totals enumerate every system/compiler process. Build command times and all source snapshots are retained under preparation/. The successful offline review used9.8s approximately; its earlier1.17s CPU directory-argument error is retained in the budget record.

## New fixed numerical plan

|Group|q,K,Hkv|Modes|Independent runs|Calls|
|---|---|---|---:|---:|
|A|1,63,8;1,257,2|MQ,QH_C|2 each|8|
|B|2,63,8|MQ,PQ,QH_C,QH_D,REPEAT4|2 each|10|
|C|3,257,2|all five|2 each|10|
|D|4,63/257,8/2 (all four combinations)|all five|2 each|40|

First one full80-graph support census host, zero graph calls; then all8 groupA controls before B,C,D. Every numerical host makes exactly one graph call. PLAN.json and wires/ freeze every coordinate and its order.124 within-v4 cross-mode comparisons,34 independent repeat pairs, and ten separate descriptive q2 v3 anchor comparisons are expected. Missing/failed coordinates remain explicit. Native numerical host.cpp is byte-identical to v2/v3. Its fixture changes only one run-id literal; all numerical DLLs, builder, shaders, dtype, inherited QK/AV precision and logical input bytes remain unchanged. Q0 and independent PQ slabs, original masks, CONT/REPEAT and output restoration are retained. The CPU metadata adapter is a separate program and does not alter the numerical host.

New ceilings:69 experimental hosts,68 graph calls;138 CPU monitor/audit processes plus one controller and two controller watch threads per slot. Future controller engineering wall<=900s, complete slot<=180s, all v4 artifacts/preparation/build/tests plus export reserve<=1GiB. New allocation is69*10s +210s admission/snapshot/closeout contingency; it is not an old unused balance. Separate native lifetime and post-exit audit cost. Inherited RSS/RAM/disk/device checkpoints remain as specified by POLICY/F0. Zero model, extra probe, warmup, retry or expected crash. Any frozen identity, runtime/numerical-control, monitoring/audit/binding or budget error stops later slots. Finite q>1 cross-mode differences remain evidence and do not silently acquire a new equality/tolerance gate.

Exact planned raw input before/after + raw four-stage + normalized four-stage payload is60,149,008 bytes. Before final capsules, actual preparation was515,993,775 bytes, including the262MB stress fixture and all CPU failures. New allowance adds128MiB JSON/audit/journal evidence,64MiB packaging/preparation reserve, complete export reserve and64MiB concurrent active/export reservation:1,058,081,487 bytes total planning allowance against1,073,741,824 bytes. BUDGET.json contains exact per-slot bytes. Actual scans and conservative reservations, not this estimate alone, enforce the ceiling. The cap can stop a pathological long slot; completeness is never presumed.

## AV mechanism: fact, source explanation, unknown

OFFLINE_REVIEW.json rehashes all4,995 original v3 files and freshly restores the physical outputs of75 admitted q2/q3 hosts. Fifteen complete five-mode groups produce150 full mode-pair comparisons: QK and softmax are bitwise equal in every pair; each MQ-versus-other pair first differs at AV in all15 groups; all six non-MQ pairs have identical four stages. No failed/unstarted output is filled.

Frozen ggml-vulkan.cpp SHA256 is `04615c97998a76d2d0b15d2ebb93bf381eb3fb565492d7714d3fc9d1c333b98d`. Recorded actual AV tensors (including ne/nb, roots, source IDs, REPEAT and op parameters) are copied into OFFLINE_REVIEW.json, not inferred from mode names alone. For K=n,H=8,q>1:

|Mode|AV src0 V ne|AV src1 probability ne|V relation|Static dispatch|
|---|---|---|---|---|
|MQ|[n,128,Hkv,1]|[n,q,8,1]|same original V|matmat|
|PQ|[n,128,Hkv,1]|q parts [n,1,8,1]|same original V per part|matvec|
|QH_C/QH_D|[n,128,Hkv,1]|[n,1,8*q,1]|same original V|matvec|
|REPEAT4|[n,128,Hkv,q]|[n,1,8,q]|actual V REPEAT, K also REPEAT|matvec|

V's dimension01 strides are[2,2*n], probability's[4,4*n]. Full four-axis strides are retained per recorded tensor. MQ probability head stride is4*n*q; PQ/folded head stride4*n; REPEAT4 batch stride32*n. Ordinary GQA maps h//(8/Hkv); folded head r=h*q+j maps floor(r/(8*q/Hkv)) to that same V head; REPEAT4 selects the real copied V query batch. These mapping/address claims are independently checked against bytes, not taken from mutual numerical agreement.

Source lines10217..10268: split is excluded by batch shape; FWHT is excluded by the recorded default hint; the p021/noncontiguous variants are excluded by actual contiguous V. MQ's dst.ne1=q>1 and probability.ne2*ne3=8 prevent the matvec predicate even though q<=8. All other modes have dst.ne1=1 and take ggml_vk_mul_mat_vec_q_f16. In that function (9716..), F32 src1 selects the F32 probability path; K63/257 do not satisfy the >=1024 larger-workgroup condition (7960..8045). The generator733.. provides float arithmetic for these matvec variants; the shader has dot/fma and subgroup/shared-memory reduction variants.

Matmat (9366..) separately selects effective source format, staging and default accumulator variants. Selector7882.. chooses f16acc/f32acc based on default precision, fp16 and cooperative-accumulator availability. Shader generator472..552 and mul_mm_funcs605..642 show that a matmul variant with FLOAT_TYPE=float16_t converts B values into half shared storage even when its buffer B_TYPE is F32. The native historical device text reports fp16=1 and KHR_coopmat; this is old evidence, no fresh query. These source conditions explain why identical exposed F32 softmax buffers can undergo different internal arithmetic paths. They do not identify the exact selected SPIR-V specialization, flags, tile, accumulator or hardware reduction tree, which were not logged. No new trace/profile is authorized.

An independent CPU conditional calculation uses the existing GPU probability bytes and exact V16 values, applying FP64 fsum either directly or after F16 rounding of probability. At q2/K63/Hkv8 first element: MQ=-0.00011706352233886719; non-MQ=-0.00012361817061901093; direct fsum=-0.0001236124080605805; half-probability fsum=-0.00011730194091796875. Rounding alone does not reproduce MQ:1,983/2,048 rounded-to-F32 elements still differ; q3/K257/Hkv2 similarly3,038/3,072 differ. This bounds an explanation, not a shader emulator or replacement for frozen scalar FP64. FP64 error gaps are not evidence of natural-model accuracy improvement, and imply nothing about RTX Tensor Core internals.

AV_F0_PROPOSAL.json and av_proposal_inputs/ specify a separate, non-executable counterfactual: one3-description census +6 AV-only calls, three conditions with two processes each: MQ/original F32 probabilities; folded/original F32 probabilities; folded/probabilities rounded F16 then stored F32. V stays identical and AV precision default. This would separate operand rounding at fixed matvec geometry from the combined dispatch/reduction difference. No such host exists or starts here; executable/entry/SHA are explicitly null. Separate CPU implementation/review, exact executable F0 and author approval would be required. These seven proposed hosts are not part of the69-host v4 registration.

## Entry and stop position

Only after a separate human confirmation of the pushed exact F0:

```powershell
& 'C:/Users/DIANG/AppData/Local/Programs/Python/Python312/python.exe' 'C:/hs/b570-query-head-lowering/benchmarks/b570_query_head_lowering_v1/host/supervised_numerical_v4/execute.py' --author-approved-f0-sha <approved exact F0 SHA256>
```

F0.json is exclusive and never regenerated. execute.py checks every bound file, Python/runtime/numerical DLL/driver identity, environment, original inputs, references, analyzer, complete wires, old raw manifests and unused run directory, then uses OS process inventory without extra device probes. It records actual later authorization time. Any existing run root or drift stops without overwrite/restart. It runs only this69-host panel. reconstruct_v4.py is CPU-only post-run delivery; it cannot initialize a device or invent missing results.

Before any natural decoder request: this targeted panel must have complete valid lifecycle/resource/output evidence, eight common controls, all34 independent repeats and full stage/error reporting; unresolved finite MQ/AV differences must remain visible. Natural actor code must separately demonstrate equivalent Q0 allocation, mask/slab addressing and original KV ownership/copies with actual decoder data and unchanged arithmetic. Natural input exposure, mathematical acceptance criteria, complete decoder reference, request/stop/budget accounting and new executable F0 require a separate review/approval. Neither a numerical panel nor this AV source explanation opens S2/S3, actor, profiling or performance experiments. PR112 stays Draft; RTX, paper, main, release, automation and RTL are untouched.
