# Historical arithmetic-path evidence: focused V3 review

## Outcome

The historical replay supports the intended evidence bridge: retaining four-column arithmetic while moving multiple groups into an outer channel dimension restored the sampled scalar operator outputs, whereas directly increasing native width did not. This is an operator compatibility result on a specified RTX/Q8 cohort. It does not identify a universal four-column numerical limit or decompose the S3 service gain.

## Sources directly read

All project paths below use commit `371223b696bb805030c29f04e39eb17b57fb2ebb` under `benchmarks/rtx_operator_frontier_v1/execution/`:

- [Original report](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/RESULTS.md), README, host.py, witness.py, driver.cpp, replay.inc, collect.py, results.py and the preceding PLAN.
- [Operand descriptors and per-route complete-output digests](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/evidence/operands.json.gz).
- [Kernel activity records](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/evidence/operator-activities.json.gz).
- [First divergence checks](https://github.com/leecdiang/HeteroSpec/blob/371223b696bb805030c29f04e39eb17b57fb2ebb/benchmarks/rtx_operator_frontier_v1/execution/evidence/first-divergence.json) and bindings.json.
- [Frozen upstream CUDA arithmetic source](https://github.com/ggml-org/llama.cpp/blob/0cae43063cf15170e91a2ff4d034da0ecef4a1b2/ggml/src/ggml-cuda/mmvq.cu), plus mmvq.cuh. Converting these upstream LF files to Windows CRLF reproduces the report's source digests exactly. The binding therefore supports reading this exact source, rather than a modern unrelated implementation.
- Current V2 method, results and supplemental contract sections.

The local `pr171_operands.json`, `pr171_activities.json` and `pr171_compact_summary.json` support direct inspection and CPU recomputation. The first two are decompressed public records. No native inference, weight upload or raw-tensor replay was performed. No private archive was downloaded. The public bindings contain historical machine paths, so their full contents were not copied into the deliverable.

## Exact cohort and comparison

Device: NVIDIA GeForce RTX 5070 Ti Laptop GPU, CUDA backend. Models: Qwen3-0.6B-Q8_0 and Qwen3-8B-Q8_0. Each contributes eight captured descriptors: layer-zero Q, K, V and attention-output projections; FFN gate, up and down; vocabulary projection. The 0.6B vocabulary projection uses tied `token_embd.weight`; 8B uses `output.weight`. These are 16 model/operator pairs, not 16 independent workloads or all layers.

The capture uses real GGUF weights and model-generated F32 activations from a deterministic 32-token fixture, `113 + (i * 173) % 2309`. Width experiments use the appropriate leading columns of each captured activation. Scalar replay applies one-column matmuls to the same operands and joins the columns; native uses one two-dimensional matmul; packed uses one broadcast matmul on `[K,4,q/4]`, then reshapes to the original column order. `replay.inc` copies and compares the complete operator-output buffer. The public records retain its digest for each route. All 16 width-32 native outputs match their own captured live outputs. Live scalar input and first-Q output checks are separately available for both models; later-layer replays use captured operands, not independently recaptured scalar-model activations.

## Compact supplemental table

| Width | Native dispatch observed in 8B traces | Native/scalar complete-output match | Four-column outer grouping/scalar match |
|---:|---|---:|---:|
| 2 | Row-Q8_1; MMVQ, block 32 × 4 | 16/16 | — |
| 4 | Row-Q8_1; MMVQ, block 32 × 4 | 16/16 | — |
| 8 | Row-Q8_1; MMVQ, block 32 × 2 | 0/16 | 16/16 |
| 16 | MMQ-Q8_1; MMQ; optional stream-K fixup | 0/16 | 16/16 |
| 32 | MMQ-Q8_1; MMQ; optional stream-K fixup | 0/16 | 16/16 |

Caption essentials: equality covers the complete sampled operator output against same-operand scalar replay across eight descriptors in each of two Qwen3 models. Dispatch traces cover the eight 8B descriptors. A dash means packed execution was not instantiated at width 2 or 4. Stream-K fixup appears for seven of eight traced descriptors at widths 16 and 32; the vocabulary projection has no fixup. Packed widths 8, 16 and 32 all retain the row-Q8_1 quantizer and four-column MMVQ with block 32 × 4. Counts describe captured descriptors, not statistical workload samples.

Native widths four and eight use the same row-Q8_1 kernel name, so their disagreement cannot be summarized as a quantizer switch. The frozen source selects four reduction warps for widths 1–4 and two for widths 5–8; its K-loop partition and shared-memory partial-sum accumulation depend on that count. The corresponding blocks are observed in the 8B traces. Internal temporary quantized bytes were not captured separately, so the evidence supports changed arithmetic organization, not an isolated attribution of every differing bit to one reduction instruction.

## Suggested main-text bridge (about 90 words)

Captured Q8 operations show why the inner numerical path must remain separate from outer scheduling. Across eight operator classes in each of Qwen3-0.6B and Qwen3-8B on RTX, native widths two and four match same-operand scalar replay, whereas widths eight, sixteen and thirty-two differ. Retaining four-column operations inside an outer group dimension restores the complete sampled outputs at all three wider widths. The 8B traces use the same activation quantizer at widths four and eight but change reduction warps; larger widths select MMQ. Thus increasing native width can change arithmetic even without a quantizer change.

Place after the arithmetic-group construction or before the performance results; replace a generic warning about shape preservation rather than duplicate the explanation. The more precise finite-cohort and dispatch scope belongs in the supplemental table.

## What to exclude from the new main argument

- The historical 23-to-2 kernel comparison uses eight separately quantized four-column matmuls plus seven joins versus one packed matmul. It combines quantization, launching and concatenation changes. It is not a scheduling-only comparison against shared-quantization backend-loop4, and does not explain S3's 1.51%.
- Historical natural-service percentages are unnecessary for the mechanism bridge. They use a different RTX contract and obsolete graph comparator.
- The C1024 versus C1536 retained-witness discrepancy does not invalidate own-path replay, but those final rows must not be pooled or described as one shared reference.

## Remaining review limits

The complete-output equality counts were independently recomputed from public per-route digests and checked against the comparison code. Full raw output bytes for all 16 descriptors, proprietary original model assets and the GPU execution were not independently regenerated. The source/trace agreement is strong bounded mechanism evidence; universal equivalence across all native inputs, devices, shapes or future dispatchers remains outside this study.
