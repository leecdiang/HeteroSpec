# B570 E2: GQA admission repaired, reference boundary found in AV

Design: [PR130 at 7a209727](https://github.com/leecdiang/HeteroSpec/blob/7a209727f151f375c28653605f58252b6da77953/docs/research/heterospec_review_20261020/EXPERIMENT_PLAN.md), E0/E2. Execution 2026-10-20. Candidate based on PR129 `c541241ad62213a8d31006e539e4ce0623793040`, including the final observer correction; observer disabled here.

**The one scoped repair did not qualify the complete preregistered panel.** Execution stopped at key512/q2 when AV and final output differed from the newly registered same-DLL PQ reference. No performance or model request experiment followed. Do not deploy this candidate as a qualified backend.

## Actual changes

The previous PR128 allowance requires contiguous A and equal head extents. The real PR129 K is interleaved and V has capacity-strided rows, with Hq/Hkv=32/8. Both lifted QB operations fail that allowance.

The experimental patch adds only F16/F32, Hkv8/Hq32, q2/q4, d128, physical key256/512, capacity1024, with the exact recorded K/V stride patterns. It retains the old equal-head allowance. It also requires equal fourth extents before selecting the existing noncontiguous AV kernel, whose implementation asserts that equality; otherwise the existing copy-to-contiguous and broadcast matvec path is used. All 147 shader objects are unchanged. No KV REPEAT or QH substitution.

This guard prevents admission from routing a batch-broadcast operation into an incompatible shader. It does **not** preserve the numerical evaluation path automatically: PQ retains the old strided AV path, while lifted QB uses the packed matvec path.

## Fixed scientific inputs

q=1/2/4, Hq/Hkv=32/8, d128, single sequence, F16 K/V, F32 Q/mask, capacity1024. Key256 uses the recorded physical layout; key512 is the prospectively selected next aligned extent for visible length260. Causal masks use visible length124/260. Every value is deterministic synthetic data, not a captured model activation or natural speculative state.

Q is physically `[d,H,q]`, exposed as `[d,q,H]`; K backing is `[d,Hkv,capacity]`; V backing is `[capacity,d,Hkv]`. Query head h maps to KV head floor(h/4). Mask j hides keys after visible−q+j. Final layout is query-major, head-major, d-fast.

Reference `R_E2_PQ` is same-candidate-DLL explicit per-query attention, same original K/V objects and full backing bytes, QK F32 precision, inherited AV precision. It is an operator reference only, not historical B570 R or PR129's request reference. Qualification requires all stages to pass FP64 tolerance and all PQ/QB stage outputs to be byte-identical.

## Results

| Physical key | q | Support / placement | PQ–QB QK / softmax | PQ–QB AV / final |
|---|---:|---|---|---|
| 256 | 1 | Both supported, all B570 | byte-identical | byte-identical |
| 256 | 2 | Both supported, all B570 | byte-identical | byte-identical |
| 256 | 4 | Both supported, all B570 | byte-identical | byte-identical |
| 512 | 1 | Both supported, all B570 | byte-identical | byte-identical |
| 512 | 2 | Both supported, all B570 | byte-identical | **FAIL** |
| 512 | 4 | Not executed after failure | UNKNOWN | UNKNOWN |

Ten native descriptor controls passed: each QK/AV accepts the registered q2 descriptor and rejects q3, Hq16, altered capacity stride and F32 A. These are support queries; rejected descriptors were not executed.

Ten graphs completed. All returned stages passed the independently recomputed FP64 tolerance `abs_error <= 0.0002 + 0.002*abs(reference)`. Full backing storage readback before/after matched exactly for Q/K/V/mask. The first failing AV has **7,160 / 8,192 differing float32 elements**, max absolute PQ–QB difference **1.2223608791828156e-9**. At query0/head0/d0, PQ is `0x38d1e6f0`, QB is `0x38d1e6c0`. The same differences propagate unchanged into final output. QK and softmax each have **zero / 32,768** differing elements.

The small error does not relax the registered reference. No speedup is reported. Positive key256 observations are retained but cannot qualify the failed full panel or be selected retrospectively as request admission.

## Source localization and limits

Raw evidence localizes the first comparable divergence to AV: inputs and probabilities agree. Source dispatch predicts PQ uses `ggml_vk_mul_mat_vec_nc_f16_f32`, whereas batch-lifted QB uses existing F16 matvec after compacting V. The nc shader uses its own dot/accumulation and shared-memory reduction structure. A different evaluation path is a plausible explanation for the low-order difference, **not a measured instruction-level causal proof**. No new trace/counter run was performed.

The synthetic q1 control and exact operator checks do not establish a whole-model endpoint. There is no observed multi-query model graph, draft/accept/rollback run, natural KV-update cost or full request timing in this experiment.

## Accounting and termination

Native PID41828, exit2, normal backend cleanup, complete stdout/stderr, no deadline kill. Direct .NET process launch; no shell/REPL native child chain. Watchdog20s, internal18s, admission reserve15s. These are bounded process waits, not a newly certified Windows Job/CPU8 supervisor.

| Charge | Seconds |
|---|---:|
| Preserved previous cumulative | 246.8043431 |
| This complete parent wall, including entry/readback/reference/cleanup | 1.6062160 |
| New cumulative / cap | 248.4105591 / 300 |
| Remaining | **51.5894409** |

No reset, reclassified failure, new budget, model load, actor, RTL, CPU8 or merge. PR128/129 were already merged by the author's separate PR130 work; this run did not merge them. CPU8 remains 0/8 with no F0.

## Rechecking and reproduction

`analyze.py` is CPU-only. It independently regenerates FP64 stages from actual full input storage, reads every produced raw stage, checks all input readbacks and pair bytes, and verifies all179 pre-run manifest entries. Its successful completion confirms the archived **failure**, not a passing candidate.

`RAW_EVIDENCE.zip` contains all produced result files, including complete input backing stores, before/after copies, FP64 and GPU stage arrays. `SOURCE_SNAPSHOT.zip` preserves parent and candidate backend sources, graph header and relevant shader text. Source snapshots are diagnostic; unchanged linked shader object identities are in the build manifest. DLLs/executable and all original files remain in the local run root.

`RUN.ps1` is the historical one-shot launcher with a fixed prior ledger and absolute paths. Never rerun it to restart budget accounting. No CI or external independent certification is claimed.

## Decision

Per PR130 E2's one-scoped-repair stopping rule, close this attempt as a concrete GQA reference boundary and hold request execution. The next bounded hypothesis is preserving the existing nc AV evaluation while iterating query batches in host dispatch with broadcast K/V addresses, rather than substituting a different reduction. That would require a fresh candidate, prospective source review and the same full panel; it has not been implemented or executed here. Do not switch to REPEAT, relax byte equality, change the PQ reference, or present more QH timing as the solution.
