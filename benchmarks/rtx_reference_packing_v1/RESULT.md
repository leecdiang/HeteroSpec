# PR110 — executed bounded CPU study: SOFTWARE_FIRST

H0–H3 are completed. The declared F32 AV primitive, finite resource scheduler and independent numerical/trace checker were implemented and executed.23 H1 CPU tests passed. All390 prospective formal cells passed; zero failed cells, missing cells, retries or outcome-driven scan expansion. Additional GPU/model/standalone-operator starts=0. PR110 remains Draft. Original design documents at324dbb7ccd07d5a5fc787fc56cc6f07ff18725f9 remain unchanged.

## Prior RTX experiment is closed

PR104 completed E2 sessions0–5, including the cross-date final session, and all72 E1 contexts. Its final pushed head is f997262d6b0accb126a1217c9356745cc8bbf708. E2 scientific F0 is49b992b2ed1cabd05fad6e234cad2d3418c2b65a; transport supplement e06dc8df53622eddd3f9306addbeaf428cdb3548; exact-interpreter restoration registration c51354bb19061ed3863cb457068dc727aa46d8ab; prospective E1 F0 fea46ef7ffa0f553b6aa5c9f1a26f6296f1cd1ca. Restoring the exact original signed launcher passed the unchanged original identities; no frozen gate was bypassed and no started scientific request was retried.

| Native cost | Complete PR104 | Added in this resumption |
|---|---:|---:|
| Model workers |396 (324 E2 +72 E1)|126 (54 E2 +72 E1)|
| Requests including warmups |1836 (1620+216)|486 (270+216)|
| Standalone operator processes/starts |432|432|
| Logical model caller invocations |245946|74216|
| Native model/replay owned seconds |6023.1775825|1874.141706|

Model-worker plus operator processes total828, with558 new. Caller counters are not hardware kernel launches; physical micrographs total431718/rows569646 and are not kernel counters either. Global auxiliary OS/compiler/control starts were not comprehensively captured. E1 configure/build command wall127.016612 seconds and native-header compile/test1.493158 seconds are separate engineering costs.

E2 request/block/output-contract/workload/heavy-observer failures=0; E1 request/operator/output-contract/workload failures=0; no final missing scientific coordinates. Original Phase0 routing failure ccfbc2e, authenticated pre-start transport EOF, export path-length/control failures, cancellation and interpreter-drift stop remain in PR104's immutable archive; successful exact recovery did not erase them. Full serial-R endpoint qualification passes. All216 C_PQ/C_QB acceptance/rollback/workload-counter pairs agree; this is not a complete trace-identity claim.

| Family | M T_PQ/T_QB (six-session interval) | C T_PQ/T_QB (six-session interval) |
|---|---|---|
|Qwen|1.020563 [1.013023,1.026553]|1.031614 [1.025393,1.037926]|
|SmolLM2|1.027767 [1.021010,1.035017]|1.065803 [1.063387,1.068399]|
|Llama|1.015593 [1.009627,1.021622]|1.029114 [1.020126,1.039149]|

The1.02 practical threshold is unchanged. Llama M is weak/no practical difference; Qwen M's practical uncertainty crosses the threshold.9 of72 task aggregates regress; all432 task/session contrasts remain. Estimation uses six sessions, never request bootstrap or fast-subset selection. Small fixed exposed panels and six clusters limit inference.

E1 observer equality, MQ own-path and per-arm repeatability passed72/72. PQ/QB bitwise equality holds72/72 at QK/softmax/AV, max error/ULP=0. MQ/PQ and MQ/QB agree only for18 q1 negative controls;54 q>1 cases first diverge at QK. Maximum finite absolute errors are QK0.078582763671875, softmax0.0009172558784484863 and AV0.010433197021484375. Actual layers0/mid/last and both phases broaden finite geometry evidence; tensor key extent256 includes padding and visible keys only reach109/130/127 by family. Kernel/reduction-tree identity, universal equivalence, long-context and cross-platform claims remain unsupported.

PR104 authenticated remote E2/E1/control bytes were restored to a fresh directory:19,922 inventoried members verified and11 analysis outputs separately recomputed byte-equal. This was an actual separate-interpreter CPU reconstruction on this host, not an external audit. The narrow fixed-panel claim that QB can lower local-repair cost while preserving recorded speculative workload/endpoint economics is supported, especially all three C paths. It does not establish universal or hardware-level acceleration. PR104's own RESULT and raw archive remain on its original branch; PR102 was not edited.

## H0 and H1: scope and actual implementation

H0.md separates request timing/source-known graph organization from unknown CUDA launch, cache/DRAM, utilization and state costs. Fixed numerical partitions, batch-invariant parallelism, ragged packing and KV multicast are strong software mechanisms; none is reserved exclusively for the candidate. No new GPU profiling was used to infer kernel shares. Source-specific primary links and boundaries are in H0.md.

The deployed RTX reduction DAG remains UNKNOWN. This study uses DECLARED_ARCHITECTURE_REFERENCE: F16 V is exactly converted to F32; each product rounds RN-even to F32; each ascending-key addition rounds separately; gradual underflow and signed zero are specified; nonfinite inputs and overflow reject with retained failure rather than a substitute input. No FMA, reassociation, online softmax, zero skipping or changed acceptance decisions. fp32.py implements integer arithmetic; checker.py independently rounds exact Fractions and never imports fp32.py/model.py.

H1's23 tests cover RN ties, subnormals, signed zeros, invalid/overflow domains,3006 adjacent random/edge pairs checked independently for ADD and MUL, association and fused-versus-separate counterexamples, input immutability, q1/q4 parity, candidate overhead, bandwidth/banks/queues/writeback, rejected spill/staging, owner/epoch isolation, missing/stale/duplicate events and corrupt payload/use counts. The single engineering revision followed source review before formal starts; initial untested sources remain. No failed test run or second revision occurred.

Inputs are24 qualified native operand subviews from PR104 E1, one per3 families ×2 phases ×q1..4, selected in layer0/mid/last priority using only provenance, MQ own-path, MQ repeatability and observer equality. All first qualified selections happened to be layer0; middle/late inputs are not claimed for PR110. Full registry/readback/shape/stride/GQA/boundary provenance is in NATIVE_COVERAGE.json. Caller positions can exceed physical q and are not invented into a one-to-one token mapping. Crop is head0/KVhead0, first2 channels and first64 keys, all physical queries; native softmax P is not renormalized. This is actual operand data under reference B, not full native AV replay or restored deployed arithmetic.2 additional explicitly SYNTHETIC inputs (q1/q4,K64,C2,seed20261015) remain separate. Missing groups=0.

## H2: actual finite event comparison

CPU_F0.json binds actual source, inputs, resources, accounting, runtime and grid. It was committed/pushed at76bffe0d2a87327cb3f8792042e45a70271e6a7f; authenticated remote F0 bytes matched SHA d27c64c0605917633395917077b0c0a03cd09eff3837ef8891fdf8e245045375 before the first formal start. All frozen source/runtime hashes passed the driver gate.26 workloads ×3 declared abstract regimes ×5 mappings=390 attempts/78 workload-resource points. This is a deterministic complete panel, not a random sample or a significance test.

All five names explicitly alias the same legal concrete policy: B0_FIXED_SHARED, B1_PACKED_MULTICAST, A_CONTEXT, A_SUPPLY and C_JOINT. Both proposed capabilities already belong to B1 and cannot legitimately be denied to B0 here. The comparison is a bounded consistency/parity test, not independent implementations proving identical hardware or exhaustive ragged schedule-set equivalence. All output, cycle, traffic, peak-state, waits and decompressed trace data agree across five mappings at every point. B1/candidate cycle ratios=1.000 throughout; regressions relative to B1=0, incremental benefit=0. No causal ablation benefit is inferred from aliases.

| Abstract regime | Points | B1 total cycles range | Peak charged buffer bytes | Maximum queue occupancy |
|---|---:|---:|---:|---:|
|Wide|26|385–450|140–296|8|
|Supply limited|26|513–1281|140–284|2|
|Bank conflict|26|577–1025|140–296|4|

State is charged in the same512B budget:64B global control,20B/output context,12B/resident or in-flight operand. Finite compute/context read/write/output ports, bank read/FILL sharing, broadcast deliveries, credits/queues and reservations produce real waits. Output STORE/COMMIT has finite cost. The one-context/one-key critical-path lower bound is4 cycles and is met; larger policy optimality is unproved. A finite extra-issue-latency negative test makes C_JOINT slower while preserving output; tighter ports/banks obey checked bounds. Wait counters overlap per blocked opportunity and must not be summed as wall-time fractions. Supply bytes are F32 words at the declared operand-store/local-buffer boundary, not RTX DRAM measurements. Exact per-cell counters, hashes and traces are retained.

## H3: evidence acceptance, costs and conclusion

Scientific raw data/source/inputs/traces were pushed at901661bf02c2d07c79430f6817c1a9500a81b128. RAW_CPU.zip is6,673,700 bytes, SHA a56bb48615c9305bbdcd600e7437f065f602cb7e817770d81d9c24492c18f119. Actual authenticated readback plus fresh extraction verified1638 members. A new interpreter executed restored recheck.py against all390 saved traces, recomputing exact-rational outputs and resource/dependency checks without rescheduling any cell. All390 passed. AUTHENTICATED_ARCHIVE_RESTORE.json is final acceptance; earlier intermediate receipts stay unchanged.

9 recorded research child jobs through independent CPU recheck consumed30.8208854 child wall seconds; peak observed RSS57,999,360 bytes. Failed research jobs=0. The successful download driver also started2 serial gh control children, whose combined additional lifetime is bounded above by its3.2712649-second parent lifetime; ordinary Git/metadata/UI/control processes are not globally enumerated. Recorded research plus this conservative nested-child bound is34.0921503 seconds, far below14400. Final BUDGET_ACCOUNTING.json records derived bytes across research/download/restore/delivery directories; actual output remains below2GiB, one heavy job at a time, formal attempts390/1024. Metadata sealing/copying is not additional functional or architecture search.

One first post-scientific archive readback failed with `transform: short source buffer`; its22-byte partial artifact and stderr are retained. Re-fetching the same immutable archive with explicit identity encoding succeeded. This is a retained control/transport failure, not a repeated formal cell. No scientific failures, incomplete coordinates, unreported input rejection or selected successful subset.

Decision: **SOFTWARE_FIRST**. No new capability over the strong baseline was identified or modeled; the deliberately same-capability panel confirms parity and independent contract/resource checks. The model does not justify new hardware, PPA, energy, RTX end-to-end speedup or broader numerical equivalence. It is one AV primitive with64-key/two-channel native subviews, one rectangular scheduling policy, three synthetic resource regimes and no RTX clock/cache/DRAM calibration. CPU execution seconds are not chip latency. No B570 task was restarted or required to pass.

The next minimal evidence would be a concrete mechanism unavailable to a legal B1 mapping, its actual software bottleneck and numerical contract, followed by a newly approved bounded validation/F0. None is executed here. Existing RTX PQ/QB repair evidence can inform a narrow claim/evidence table; no new hardware contribution or paper result is inserted, and PR102/main/release/arXiv/Zenodo remain unchanged.
