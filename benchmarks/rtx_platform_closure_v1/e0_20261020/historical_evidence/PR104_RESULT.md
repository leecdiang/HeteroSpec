# PR104 — complete E2 and bounded native E1 results

E2 completed all six original sessions. E1 terminal state: **COMPLETED_MATRIX**. A completed matrix counts attempted coordinates, not a guarantee that every geometry was observed or admitted. All old failures, cancellation and stopped-state receipts remain immutable. No main, PR102, historical empirical values, release or B570 execution was changed. PR104 remains Draft.

## Execution and costs

| Phase | Native workers | Requests (warmups included) | Warmups | Standalone operator starts | Native owned seconds |
|---|---:|---:|---:|---:|---:|
| E2 | 324 | 1620 | 324 | 0 | 4968.994058 |
| E1 | 72 | 216 | 72 | 432 | 1054.183524 |

This resumption added54 E2 workers/270 requests and 72 E1 workers/216 requests/432 standalone replay starts. E2 logical model caller invocations=206076; E1=39870. These caller counters and physical micrograph counters are not hardware kernel launches. Global auxiliary OS/compiler process starts were not comprehensively captured and remain NOT_GLOBALLY_CAPTURED.

E1 compilation/configuration command wall seconds=127.016612; actual native-header CPU compile/test seconds=1.493158. These are engineering costs, separate from combined native model/replay lifetime; no model/operator probe was inserted.

E2 request failures=0, failed blocks=0, output mismatches=0, invalid contracts=0, workload errors=0, heavy-observer flags=0. E1 request failures=0, operator failures=0, invalid output contracts=0, workload errors=0.

The whole E2 ceiling remained324 workers/1,620 requests/43,200 native seconds. E1 remained72 contexts/216 requests including warmups/432 standalone replay starts/21,600 combined native seconds. Unused ceilings cannot be transferred. All failed/started/unstarted coordinates are retained in ledgers and context tables; none is retried.

## E2 PQ/QB cost confirmation

Ratio=T_PQ/T_QB. The original inclusive resident request timer runs in counts mode; it is not isolated kernel/operator time. Equal task weights within each session and equal weights over six sessions; intervals use the original six-session bootstrap. No request-level bootstrap, latency trimming, task pruning or sample expansion.

| Family | Path | Geometric speed ratio | Approx. six-session interval | QB latency reduction | 1.02 interpretation |
|---|---|---:|---|---:|---|
| Qwen | M | 1.020563 | [1.013023, 1.026553] | 2.015% | practical point evidence; interval crosses1.02 |
| Qwen | C | 1.031614 | [1.025393, 1.037926] | 3.064% | practical point evidence |
| SmolLM2 | M | 1.027767 | [1.021010, 1.035017] | 2.702% | practical point evidence |
| SmolLM2 | C | 1.065803 | [1.063387, 1.068399] | 6.174% | practical point evidence |
| Llama | M | 1.015593 | [1.009627, 1.021622] | 1.535% | weak/no practical difference; interval crosses1.02 |
| Llama | C | 1.029114 | [1.020126, 1.039149] | 2.829% | practical point evidence |

All session log contrasts and all task/session ratios are in E2_SESSION_CONTRASTS.csv and E2_TASK_CONTRASTS.csv. E2_TASK_SUMMARY.csv retains all72 family/path/task contrasts; 9 have a six-session point ratio below1. No task-level significance test is claimed. E2_SESSION_TABLE.csv gives the six actual starts/completions and lifetime accounting. All1,620 raw request latencies remain in the complete E2 archive and paid-request table; nonpositive/nonfinite latency count=0. No posthoc outlier threshold removes data.

Recorded C_PQ/C_QB acceptance/rollback and logical-workload counters/histograms agree in 216/216 task/session pairs. Full original serial-R endpoint qualification passes across the six sessions. Counter agreement does not establish identical complete control traces, physical kernel schedules or reduction trees.

## E1 geometry and numerical correspondence

The fixed matrix is three families × target layers0/floor(L/2)/L-1 × prefill/continuation × q1..4. GGUF block counts are Qwen36, SmolLM224, Llama32. Longest inherited P2 prompts with lexical-ID ties select GSM8K/test/443, with105/126/123 input IDs respectively. q2/4 use minimum observed key extent128; q1/3 use0. Input choices were frozen before E1 forwards.

Context qualification states: `{'PASS': 72}`. E1_CONTEXTS.csv includes every coordinate, observed key extent, visible mask keys, observer equality, own-path and within-arm repeatability. PASS means admission, not that every pair is numerically equal. q1 is an ordinary-decoding negative control.

| Pair | Operator | Bitwise-equal admitted contexts | Maximum finite absolute error | Maximum finite ULP |
|---|---|---:|---:|---:|
| MQ/PQ | AV | 18/72 | 0.010433197021484375 | 1953885696 |
| MQ/PQ | QK | 18/72 | 0.078582763671875 | 2017357824 |
| MQ/PQ | softmax | 18/72 | 0.0009172558784484863 | 96633 |
| MQ/QB | AV | 18/72 | 0.010433197021484375 | 1953885696 |
| MQ/QB | QK | 18/72 | 0.078582763671875 | 2017357824 |
| MQ/QB | softmax | 18/72 | 0.0009172558784484863 | 96633 |
| PQ/QB | AV | 72/72 | 0.0 | 0 |
| PQ/QB | QK | 72/72 | 0.0 | 0 |
| PQ/QB | softmax | 72/72 | 0.0 | 0 |

First bitwise-divergent operator, by admitted context/pair: `{'MQ/PQ': {'NONE': 18, 'QK': 54}, 'MQ/QB': {'NONE': 18, 'QK': 54}, 'PQ/QB': {'NONE': 72}}`. All detailed stage/ULP/nonfinite values are in E1_NUMERICAL.csv. Failed own-path/repeatability cases withhold qualified pair inference; their original tensor bytes remain archived.

| Family | Observed layers | (head dimension, query heads, KV heads, tensor key extent) | Unmasked visible-key range |
|---|---|---|---|
| Qwen | [0, 18, 35] | [(128, 32, 8, 256)] | 1–109 |
| SmolLM2 | [0, 12, 23] | [(64, 32, 32, 256)] | 1–130 |
| Llama | [0, 16, 31] | [(128, 32, 8, 256)] | 1–127 |

All captured Q/K/V dtypes are F32/F16/F16 with F32 masks; complete actual shapes/strides/GQA and masks are in each snapshot, not reconstructed by changing geometry.

## Freeze, recovery and raw evidence

Original PR98 baseline:3235d44c26edd92db33e574094c26af8e29d2452. Scientific E2 F0:49b992b2ed1cabd05fad6e234cad2d3418c2b65a. Transport supplement:e06dc8df53622eddd3f9306addbeaf428cdb3548. Exact-restoration registration:c51354bb19061ed3863cb457068dc727aa46d8ab. Prospective native E1 F0:fea46ef7ffa0f553b6aa5c9f1a26f6296f1cd1ca.

The original Phase0 routing failure ccfbc2e4c3ab3026a6bbec5caf4c98646781913c, pre-scientific authenticated transport EOF, CPU export path-length failure, user cancellation, interpreter-drift stop f784386 and recovery/control failures are retained. The drift stop was genuine before recovery; it is not the final execution state. The exact original d41bad… launcher was recovered from official bundle26.1011.11113, whose complete SHA-256 is81466ad85b7074e5694a3d45e8edae6387f09548cd2e8f144841951a329dd7c7. Original frozen files and original authenticated F0 passed without guard changes before untouched session5; no scientific retry or identity exception was introduced.

Complete E2 raw archive:26,237,013 bytes, SHA-256 ed3a87567b62c2610627783d43db00e187aef865aa7874d806428dd51d4a7227. All10,179 members passed fresh restoration and separate-interpreter CPU recomputation; authenticated remote archive bytes at75e01db7b2b471137b638a0d6c2e5bb61a23838f match. The export helper removes only a legacy non-scientific code-bundle flag, with no scientific field or estimate excluded.

Full E1 archive SHA-256=c71367c4c195a19105afe06993e29064cb499153b6a21a3984d2965730db1410, bytes=138345840, parts=3. E1_ARCHIVE_ASSEMBLY.json defines exact concatenation order and part hashes. RAW_ARCHIVE_MANIFEST_E1.json inventories retained members. Authenticated remote bytes from data commit c06e1991aa994b862cc50ed78a9c67184ccaf4a0 passed full fresh combined restoration and separate-interpreter CPU reconstruction, byte-equal across all analysis files. Models and numerical DLL bytes are excluded; immutable identities, actual native module receipts, complete private source and native executables are retained.

## Claim/evidence and limitations

The completed fixed-panel RTX evidence supports the narrow claim that QB can lower local-repair request cost while preserving the recorded speculative-decoding workload/endpoint economics. C-path gains are observed in all three families. Llama M remains below the practical threshold, and Qwen M practical uncertainty overlaps it. Per-task regressions remain part of the result. This is not a blanket per-task, new-input, multi-device or six-independent-dates claim.

E1 provides only finite observed geometry/operator correspondence under the frozen CUDA stack. Tensor extent includes masked padding and does not prove long unmasked contexts. One selected exposed prompt per family is not broad input generalization. Own-path/repeatability and capture-on/off endpoints do not identify the counts-mode kernel schedule or establish a universal numerical theorem. Physical-query token attribution inside a wider caller can remain UNKNOWN; full raw caller positions/ownership are preserved without inventing prefixes.

Before/after input identity is enforced by frozen driver assertions against retained immutable hashes; separate per-replay hash-dump files were not produced. Native worker PIDs and actual module receipts are retained; standalone replay executable/loader paths and fixed DLL hashes are bound, but a separate module enumeration/PID receipt was not added to the inherited replay executable. Kernel identity, reduction tree, hardware launch count, continuous thermal residency, DRAM/SM shares, energy, silicon area and cross-platform bitwise reference remain UNKNOWN or unmeasured.

Fresh-directory separate-interpreter CPU reconstruction on this host is not an external audit or a new GPU run. Original conversion/checkpoint lineage limits remain. PR102 and B570 results are not changed. PR110 may begin only after this actual E2/E1 closure, ended owned tasks and accepted new raw restoration.
