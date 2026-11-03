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

The scoped dense Q8 path retains F32 activations and dispatches column tiles across grid Y. On the q16 Qwen attention projection the actual Vulkan dispatch was `mul_mat_vec_q8_0_f32_f32` with dimensions 2048 × 2 × 1. At q32 it was 2048 × 4 × 1. On the latter crossing, QB kept the full 32-row outer computation in one graph and WB issued 16 rows at head 2032 and 16 at head 2048. The shared scalar rule, complete Vulkan tensor strides, allocator-derived extent sequence and graph reuse signature determine where attention may batch.

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

## Blind qualification

The implementation freeze preceded selection of twelve code and mathematics inputs, with two inputs per domain and length band. Prompt lengths ranged from 90 to 688 tokens. Each of the four compatible arms matched the original reference at all 1331 committed output positions. FAST matched eleven greedy sequences and zero full-vector sequences. The four-arm panel uses six balanced sessions with adjacent arms and a fresh context per request.

## Complete natural service

All 288 formal service measurements and their 288 immediate warmups completed on the first attempt. Seconds below are equal-input geometric means. The intervals resample the twelve inputs while retaining all six sessions within each input.

| Arm | Geometric mean service, s | Arm / QB time | Input-bootstrap 95% interval | Blocks where QB was faster |
|---|---:|---:|---|---:|
| S1, UB1 | 15.394 | 2.12179 | 1.89950–2.33161 | 72/72 |
| PQ-ext | 10.723 | 1.47796 | 1.37948–1.56543 | 72/72 |
| QB-local | 7.255 | 1 | — | — |
| WB-cut | 7.258 | 1.00029 | 0.99967–1.00120 | 33/72 |

Fresh natural prefill starts at zero and its 32-row chunks align with the 256-cell physical allocation boundary. QB and WB made identical numbers of whole-target calls in all 72 blocks. WB was faster in 39 of those blocks. At 90 input tokens the separate QB/WB prefill diagnostics took 0.833/0.836 s. At 688 tokens they took 6.903/6.908 s across 22 calls each. The natural data give no measurable local-grouping advantage over the strong whole-graph caller. Native FAST took 0.71690 times QB service in twelve matched reference slots and failed numerical qualification on every input.

Loading both resident models took a mean 5.14–5.15 s per process across arms. Mean host-owned time for a process containing setup, immediate warmup, measurement and cleanup was 43.545 s for S1, 32.429 s for PQ, 23.848 s for QB and 23.827 s for WB. The old polling experiment yielded 33 formal observations across its 60 slots. Twenty-four dual-context slots failed admission and three ordinary measurements exhausted the device reserve. Among matched pairs, polling-on / polling-off service was 1.047 for R (6 pairs), 1.033 for M_PQ (6) and 1.037 for M_QB (3). The raw on/off query durations and incomplete pairs remain in the archive.

## Fixed work across physical boundaries

All 1395 registered timed cells returned. Each interval starts after state restoration and ends after synchronized execution and all required greedy reads. The table gives geometric means of paired WB time divided by QB time. Values above one favor QB. The inside column includes the scalar controls where registered. The per-width columns contain crossing observations only.

| Deployment | Inside | Crossing | q2 | q4 | q8 | q16 | q32 | Crossing blocks favoring QB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen C1024, both weights resident | 1.0000 | 1.1154 | 1.2169 | 1.3138 | 1.1933 | 0.9547 | 0.9478 | 26/45 |
| Qwen target-only C4096 | 1.0024 | 1.0610 | 1.1298 | 1.1333 | 1.0765 | 0.9900 | 0.9855 | 37/60 |
| SmolLM2-1.7B C4096 | 0.9974 | 1.1163 | 1.2350 | — | 1.2641 | 1.0830 | 0.9183 | 18/24 |

At q32 WB cut the full query into two 16-row graphs and had lower geometric mean latency on all three deployments. The dispatch reduction did not cover the local path's additional work at this width. At q2 and q8 the local path had lower geometric mean latency on all three. In the crossing cells, the eligible PQ/QB ratios were 1.374, 1.266 and 1.338 respectively. The S1/QB ratios were 2.246, 1.583 and 2.355. Missing numerical qualifications are excluded from those comparisons. The raw table retains their timings.

The within-coordinate ratio of crossing WB/QB to inside WB/QB was 1.1154, 1.0606 and 1.1192 across the three deployments. A predictor stratified by width and crossing status had median absolute log-ratio error 0.0276 on the 24 held-out Smol B2048 observations. Qwen C1024 predictions tested on the 120 multi-row observations in the separate target-only C4096 deployment had error 0.0260. This second comparison changes both capacity and residency and cannot isolate a context effect.

The independent audit reconstructed 465 observed or missing numerical cells and 1395 fixed timings from the native records, checked 80 serialized checkpoint files, and verified 4077 unique comparison-vector objects. There were 684 supervised native processes with 17214.82 charged process-seconds including failures, admission and diagnostics. These are process wall-clock intervals. GPU-active duration was measured separately in sampled dispatch traces.

## Relevance to TPDS

The systems question here is how much concurrency a runtime retains while reproducing a specific deployed scalar reference. WB-cut provides a direct comparator because it respects the same physical allocator and numerical contract. The hardware evidence identifies the operations that still run wide, the extra dispatches from splitting the entire graph and the mask copies and concatenations paid by local grouping.

Related systems already address deterministic inference through batch-invariant kernels, schedule control, verification and rollback, and formal reasoning about engine state and kernels. The present comparison contributes an empirical test of local compatibility against whole-target cutting, including a head-geometry counterexample localized to a real dispatch. Its numerical evidence covers the reported geometries and workloads. [Thinking Machines](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/), [LLM-42](https://arxiv.org/abs/2601.17768), [CoRun](https://arxiv.org/abs/2608.14376), [Vosti](https://arxiv.org/abs/2609.38981).

The performance contribution is bounded by query width and alignment. The strong whole-graph baseline accounts for the observed natural service improvement relative to scalar execution on this panel. Local grouping adds measured value at selected crossings, and loses to whole-graph cuts at the widest registered query. In the separate RTX pilot the same shared header was used with a different speculative deployment and a WB/QB service ratio of 1.0104 across eight blocks. The two studies provide a transfer of the rule and its comparison method. Their different workloads preclude a pooled speed estimate. [RTX execution results](https://github.com/leecdiang/HeteroSpec/blob/9c79594f679ea4aad1956d8a385fdf6a7352d892/benchmarks/tpds_parallel/RESULTS.md)

