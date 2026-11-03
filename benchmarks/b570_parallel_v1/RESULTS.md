# B570 reference-compatible parallel execution

On the original B570, the local and whole-graph schemes produced the scalar reference's full-vocabulary bytes at every one of the 93 primary common-state coordinates. Two per-query attention cells lacked a completed execution. The archive identifies both requested states and their failed attempts. Each coordinate starts from the same serialized physical KV state and consumes the same known tokens for every arm.

| Deployment | Physical boundaries | S1 | PQ-ext | QB-local | WB-cut | Native FAST |
|---|---|---:|---:|---:|---:|---:|
| Qwen3-8B, C1024, both models resident | 256, 512, 768 | 33/33 | 31/33 | 33/33 | 33/33 | 3/33 |
| Qwen3-8B, C4096, only target resident | 1024, 1536, 2048, 3072 | 44/44 | 44/44 | 44/44 | 44/44 | 4/44 |
| SmolLM2-1.7B, C4096, both models resident | 256, 2048 | 16/16 | 16/16 | 16/16 | 16/16 | 0/16 |

Cells count exact matches relative to all registered coordinates. The two missing PQ-ext executions are C1024, q32 at heads 480 and 752. All 91 observed PQ-ext cells matched. Qwen covers q1/2/4/8/16/32. Smol covers q2/8/16/32. All measured FAST multi-row cells diverged. The unscoped FAST build matched the untouched numerical DLL's native wide output at both sampled widths in each deployment. The UB1 S1 cost configuration passed its own 93/93 comparison.

## Arithmetic and execution

The Qwen target has head dimension 128 and 32 Q heads sharing eight KV heads. SmolLM2-1.7B has head dimension 64 and 32:32 MHA. Its initial grouped implementation preserved all greedy tokens on the four pilot coordinates while changing all 80 logit vectors. The layer-zero Q tensors matched. The scalar path selected the permuted p021 QK kernel, while the grouped path selected a generic matvec. Row zero alone differed at 4519 of 8192 QK elements. Extending the p021 kernel across query workgroups restored its scalar reduction. QK, probabilities and AV then matched for all eight traced rows, as did their full-vocabulary outputs. The separate SmolLM2-135M probe with dim64 and 9:3 GQA passed both width-eight coordinates for all four compatible arms. The larger Smol model also matched all four intact exposed input controls.

The scoped dense Q8 path retains F32 activations and dispatches column tiles across grid Y. On the q16 Qwen attention projection the actual Vulkan dispatch was `mul_mat_vec_q8_0_f32_f32` with dimensions 2048 × 2 × 1. The shared scalar rule, complete Vulkan tensor strides, allocator-derived extent sequence and graph reuse signature determine where attention may batch.

| Qwen q16 trace | QB target calls | WB target calls | QB / WB FFN widths | QB / WB actual dispatches |
|---|---|---|---|---|
| C1024, head 240, inside one extent | 16 | 16 | 16 / 16 | 760 / 760 |
| C1024, head 248, crossing 256 | 16 | 8+8 | 16 / 8+8 | 1048 / 1520 |
| C4096 target-only, head 2032, inside one extent | 16 | 16 | 16 / 16 | 760 / 760 |
| C4096 target-only, head 2040, crossing 2048 | 16 | 8+8 | 16 / 8+8 | 1048 / 1520 |

Each crossing paired the same original state and known work. In the first crossing, QB spent 1.771 ms on mask copies and 0.159 ms on concatenation according to device timestamps. At the 2048 crossing these figures were 1.659 ms and 0.157 ms. WB incurred neither operation on these two traces. The timestamp-labeled library reproduced the formal vectors. Service and fixed-work estimates use separate executions without tracing.

In the sequential reuse probe, the head-252 crossing used one width-eight graph in QB and widths four plus four in WB. Both rebuilt at head 260 and reused the previous graph at heads 268 and 276. All 32 output vectors matched the scalar replay.

## Resource and regression boundaries

The initial Vulkan budget check used unsigned subtraction. Usage above the driver's budget can wrap the apparent free memory above total device memory. Early long-context admissions therefore do not certify the stipulated reserve. Their processes, output and cost remain in the evidence. The corrected worker rejects free memory above total as well as free memory below 128 MiB. Both-model Qwen C2048 and C4096 failed zero-forward capacity. The separate C4096 deployment loads only the target, offloads every target layer, and has its own independently frozen original numerical reference. C1024 ordinary requests retain both GPU models. Allocation-block and device-local-only probes also failed the dual-context Qwen k1 gate.

The original Qwen P1 fixtures retained all 384 reference vectors. The new candidate matched them again, including the ordinary q32 prefill cases with residual widths 9, 22 and 23. The k1 worker stopped at zero-forward admission. Both original Llama controls matched PR163. CodeContests/valid/108 reproduced 246 vectors and 35 cycles with grouping at head 765. GSM8K/test/496 reproduced 302 vectors and 43 cycles without a group transition.

The clean paired service and fixed-work measurements are pending.

