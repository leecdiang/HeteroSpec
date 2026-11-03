# B570 Llama Q8 native result

The combined repair preserves the frozen stock Vulkan reference on all 24 prospectively selected unseen inputs. Independent reconstruction passes all 288 qualification requests, 23,718 saved full-vocabulary vectors and 14,555 committed candidate vectors. All 864 warmups and 864 measurements complete with reference-equal outputs. QB reduces complete speculative service time by 4.945% relative to the paired PQ controls, passing the predeclared 2.942% A/A screen in all six periods. The speculative C_QB path is nevertheless 62.879% slower than stock R under the admitted GPU-target / CPU-draft placement. These are distinct findings.

Raw publication and fresh remote reconstruction are recorded separately in delivery receipts; completion of local native work is not by itself a remote-delivery claim.

## Contract and reference

This is the independent B570 companion execution of PR161, based on `98b9e57f1412ad885bf479cf0d9bbf40c5511cb7`. RTX PR160 is untouched. The exact original Llama target and draft Q8 weights are retained, with hashes in `MODEL_HASHES.json`. Zero-forward admission selected target GPU layers999 / draft CPU layers0 after the all-GPU reference failed the declared memory reserve. The selection preceded scientific forwards and was not retuned for speed or answers.

The immutable stock numerical reference is `oracle-01`, built from upstream `0cae43063cf15170e91a2ff4d034da0ecef4a1b2` with an observation bridge. The final candidate is `candidate-combined-02`, epoch `combined-epoch-03`, frozen at source commit `5d1272dcb2e53b73e3e72db4c403361fbef7d6c4`. The original reference is never replaced by candidate R. Hardware is an Arc B570 with driver32.0.101.9150 and i5-13400;8 threads, k3, cap128, ctx1024, F16 KV and flash attention off are fixed.

R uses the frozen stock UB1 path. M_PQ/M_QB are ordinary greedy generation with the scoped candidate layout and target context microbatch capacity4. C_PQ/C_QB additionally execute draft and verification transactions. Thus M/R and C/R are complete-path comparisons, including their different prefill behavior. Pure layout cost is the paired C_QB versus C_PQ comparison. CPU draft placement is a disclosed capacity choice, not a controlled hardware-only CUDA/Vulkan comparison.

## Native mechanisms and controls

The original54 Llama requests and5916 vectors were authenticated and reconstructed before new development. The old B570 Q6 partition/MUL evidence remains a separate numerical contract:8 post-consumer alias captures are excluded, and no Q6 result substitutes for this Q8 qualification. Old Qwen q2/q4, key256/512 records were recovered separately.

The36-request natural B570 baseline reproduces local failures. Actual local cycles, states and dispatches identify two independent factors:

1. Before RoPE, q1 Q8 projection uses F32 activations while q4 selects Q8_1 activation quantization. Producer-safe real Q/K/V operands reproduce all15 original own paths. A declared intervention and a structural scoped GGML_PREC_F32 dispatch policy reproduce the concatenated scalar projections. The final binary also passes21 real-operand projection calls covering q1/2/3/4. There is no hidden environment switch or serial projection fallback.
2. Projection repair alone preserves development endpoints but leaves99 committed vectors different, beginning at output29 on the long input. At actual cycle8/base765, scalar rows use physical key extent768 before the final1024 row, whereas the original batch uses1024 throughout. Visible V, QK and probability prefixes agree bitwise. Eleven own-path and crossed-extent AV calls exchange the results. Actual Vulkan dispatch changes from the noncontiguous to contiguous matvec path; the claim is an extent/contiguity/dispatch factor, not an unchanged-pipeline loop-length explanation. Maximal adjacent equal-prefix attention groups, with graph-reuse invalidation, repair it structurally. The observed boundary remains a3+1 batch split on Vulkan0 in all32 layers.

Sixteen real attention-chain replays cover q1..4, PQ/QB and keys768/1024, with64 stage comparisons. Five final same-state requests preserve natural trajectories and live source state; all20 q1/q4 full-vector rows match. Controlled layer0 attention/post-FFN traces and exact group concatenation agree. The final binary passes12 unchanged historical Qwen requests and914 saved vectors/descriptors under the original auditor.

The final36-request development matrix passes3152 saved vectors and1920 committed candidate vectors. Prefix-off in the same binary restores the entire36-request/3152-vector projection-only trajectory, including the99 latent differences. Q8-off restores endpoint failures. A separate projection-off predecessor restores every original baseline trajectory and all3138 vectors. The original stock reference remains identical across384 development reference vectors. Numerical source changes and failed builds/admissions have distinct preserved epochs.

## Prospective unseen qualification

Freeze preceded panel selection at2026-11-02T15:08:25Z. The panel has24 natural inputs, six per code/math × short/long cell, with128–384 or512–768 native tokens and no padding or truncation. Cross-platform exclusions include reachable historical Git/local inputs, authenticated RTX159 metadata, and conservative exclusion of the complete pinned APPS/test and MATH/test pools used by ongoing RTX work. This is an independent Vulkan panel, not a jointly frozen cross-platform panel.

The48 original-reference and240 candidate requests all pass heavy/off controls, complete endpoints, transactions, candidate-R equality and full PQ/QB correspondence including rejected rows. The independent auditor also checks every committed candidate full vector against the stock scalar vector. It imports none of the primary audit, design or cycle functions. All23,718 saved vectors and14,555 committed candidate vectors pass. No confirmation input was replaced or recycled after a failure.

## Complete costs

All six Williams periods,24 inputs and six labels are retained. C_PQ_A/B are averaged arithmetically within each block before equally weighted log-ratio aggregation. R measurements use the original stock executable. Each pair loads the same exact models and executes a fresh-context warmup followed by a fresh-context measurement. Timing has no heavy observer, trace or probe.

| Ratio | Geometric mean | Interpretation |
|---|---:|---|
| C_QB / mean(C_PQ_A, C_PQ_B) |0.950548531|4.945% lower complete speculative service time|
| M_QB / C_QB |0.334254588|Ordinary scoped path costs33.425% of speculative QB|
| M_PQ / mean(C_PQ_A, C_PQ_B) |0.353302649|Ordinary scoped path costs35.330% of speculative PQ|
| C_QB / stock R |1.628786691|Speculative QB is62.879% slower than stock R|
| M_QB / stock R |0.544429425|Ordinary scoped QB is45.557% faster in this full-path comparison|
| C_PQ_A / C_PQ_B |1.001793750|Paired control ratio|

The practical threshold is max(2%, largest symmetric per-input aggregate A/A deviation)=2.9418325%. All six period layout ratios favor QB:0.946005141,0.951494000,0.949342846,0.952645422,0.948029479,0.955806567. The predeclared layout screen passes;2 of144 individual blocks nevertheless have slower QB and remain included. There is no request-level population confidence interval or perfect thermal/carryover-control claim.

| Cost window | Seconds |
|---|---:|
|864 warmup service windows|14,600.5637971|
|864 measured service windows|14,491.9098316|
|864 native model-loaded process pairs|34,405.6210000|
|Process remainder outside service windows|5,313.1473713|
|Host-owned time for the864 pairs|34,829.8570000|

The clean service clock includes context creation, prefill, draft, verification, KV reconciliation, synchronization and context teardown. The process remainder includes model loading/unloading and surrounding native work; it is not a separately measured model-load phase. Independent cost reconstruction exactly agrees with the primary cost report and verifies all1728 warmup/measured endpoints and transactions.

The final inference ledger reconciles2297 completed model requests,108 operator graph submissions,2520 reserved credits including failures/unstarted slots,47,854.915 host-owned seconds and46,061.496 native process seconds. Four failed native attempts and26 zero-request attempts remain included; no attempt is open. Build, preparation and transport failures remain separately archived and are not mislabeled as model execution. The ledger's elapsed windows do not represent all human/agent research wall time.

## Reproduction and limits

CPU protocol tests:60 passed. Actual patched native prefix-guard fixtures passed. Archive reconstruction and tamper tests:2 passed. These support the native evidence and do not substitute for it. See `RECONSTRUCTION.md` for independent qualification, timing and ledger reconstruction, and the release receipts for fresh remote verification scope. Model weights remain external pinned inputs.

This finite panel does not prove universal bitwise equivalence across models, devices, arbitrary cache states or future drivers. The measured gain concerns the declared scoped layout within this exact full request contract. The end-to-end speculative result remains slower than stock R on this admitted placement. No PR is automatically merged and no manuscript is changed.
