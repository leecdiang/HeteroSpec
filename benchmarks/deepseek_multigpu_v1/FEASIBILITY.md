# Feasibility and framework choice

**Terms:** TP means tensor parallelism; PP means pipeline parallelism; KV means key/value cache; BF16 is bfloat16; F16 is IEEE float16; F32 is IEEE float32; GQA means grouped-query attention; MLA means multi-head latent attention; MoE means mixture of experts; FA2 means FlashAttention 2; SM denotes NVIDIA streaming-multiprocessor architecture; P2P means GPU peer-to-peer access.

## Scope and evidence

The requested machine is one host with eight RTX A5000 GPUs. The second eight-GPU host and inter-node networking are out of scope. We have not inspected this server during this task. Nominal hardware specifications and source support are not an inventory of its free memory, topology, installed bridges, drivers or availability.

Pins used for the decision:

- HeteroSpec main: `cfc9edf4582bb3c02885c9171a2ab2635bf19588`.
- Official DeepInfer: `a679bb86ce36e883a98a97733492b686e5b9a08e`.
- vLLM: `75be5c3919b6a82fa1885c0d0a2250adba477413`.
- HeteroSpec Q32: `41ef4ca6bbc382c02fb97ebea874651fbf9fd4ac`; strong G/B/C implementation: `f419a89d54f4ec93b4c9c328b4ea9f416ae3c989`.

These are inspected source snapshots, not a tested installation lock. Record exact compiler, PyTorch, Triton, CUDA, driver, NCCL, attention backend and wheel/build provenance before execution. A moving branch, a model marketing name or a package version alone is insufficient.

## Why native DeepInfer is not the A5000 starting point

The [pinned README](https://github.com/deepseek-ai/DeepInfer/blob/a679bb86ce36e883a98a97733492b686e5b9a08e/README.md) lists SM100 and Ascend 950, Linux, Python 3.12, GCC ≥13 and CUDA 13 for NVIDIA. A5000 is Ampere SM86. Its architecture is not made compatible by installing CUDA 13 or changing a build flag. The release's optimized FlashMLA, DeepGEMM, DeepEP and custom kernels must each have an appropriate replacement or port; replacing only a GEMM import is insufficient.

Only DeepSeek-V4.1-Flash is advertised by this release. The default checkpoint is V4.1-Flash-1017, not a small R1 distilled checkpoint. The [official V4.1 family card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) reports 552B backbone parameters and another 196B Engram parameters. Its backbone scale alone is beyond this GPU-resident budget: even an ideal 552-billion-parameter 4-bit payload is 276 GB = 257.045 GiB, before scales, padding, state, workspaces or additional components. This is a lower-bound calculation, not a supported quantization recipe or a measurement of that checkpoint's resident bytes.

Likewise, 671B main weights for full V3/R1 at ideal 4 bits require 335.5 GB = 312.459 GiB. Including an additional 14B MTP module gives 342.5 GB = 318.978 GiB. The total nominal capacity is 192 GiB, separated across eight devices. Active MoE parameters reduce arithmetic, not the need to store or fetch inactive experts. CPU offload or very-low-bit approximations would introduce a different system, quality and transfer regime; they are not the default scientific route.

DeepInfer already implements DSpark/confidence-scheduled verification, bounded SWA replay, asynchronous scheduling, deterministic sampling and batch-invariant inference. Its published throughput is on SM100 scale-up configurations, including 64 devices for decode. None of those numbers predicts A5000 performance.

## Candidate matrix

| Route | Role | Why investigate | What is not established |
|---|---|---|---|
| vLLM + R1-Distill-Qwen-14B BF16, TP2 | First multi-GPU reference and adapter | Mainstream engine; dense GQA; Ampere invariant matrix path exists | Distilled checkpoint and full speculative state qualification on this server |
| vLLM + R1-Distill-Qwen-32B BF16, TP4/8 | Main scale expansion | Meaningful model-parallel workload; 8 KV heads admit these partitions | Fixed collective semantics and actual memory/performance |
| SGLang + same dense checkpoints | Mainstream control and fallback | Independent implementation and serving baseline | No transfer of vLLM or HeteroSpec numerical qualification |
| DeepSeek-V2-Lite BF16 | Later MLA/MoE extension | 16B total / 2.4B active is a tractable family member | MLA cache, routing and expert-dispatch contract |
| DeepInfer + V4.1-Flash | Future architecture port | Direct production-framework transfer | Unsupported SM86 and insufficient GPU-resident memory |
| Existing Hetero CUDA + layer partition | Diagnostic fallback | Whole local matmuls may retain existing recipes | Not a vLLM/DeepInfer port; layer partition alone need not reduce single-request latency |

The dense route is chosen for engineering tractability, not because it is known to produce positive results. R1-Distill-Qwen belongs to the DeepSeek release family but uses Qwen architecture. Report that distinction in every result title.

## Memory arithmetic

For a dense GQA checkpoint with evenly sharded weights, a useful first estimate is:

`rank_bytes = sharded_weight_bytes + replicated_weights + quantization_metadata + KV + workspace + communication + graph_pool + allocator_reserve + draft_state`.

Actual modules are not all sharded evenly. Embeddings/output heads, alignment, buffers and runtime replication must be counted from the selected loader. Use the largest rank, not the node average. Treat free memory observed before load as an input and measure peak reserved and allocated memory after complete warmup, during verification, rollback and graph capture.

For an uncompressed GQA cache with equally divided KV heads:

`KV_rank = 2 × layers × allocated_tokens × concurrent_sequences × (KV_heads / TP) × head_dim × bytes_per_element`.

Allocated tokens include input plus output allowance, speculative lookahead, block rounding and prefix ownership; do not substitute prompt length. This formula does not describe MLA or compressed/sparse/sliding-window state. KV replication or unequal partitions require explicit accounting. FP32 KV doubles the BF16/F16 values below.

The following are **ideal tensor-payload planning estimates**, with 4096 allocated tokens, batch 1, two-byte KV, no draft model and evenly divided 8 KV heads. Official model-index observations give 29,540,067,328 tensor bytes for 14B and 65,527,752,704 for 32B. The Hub API reports revisions `1df8507178afcc1bef68cd8c393f61a886323761` and `711ad2ea6aa40cfca18895e8aca02ab92df1a746`, respectively. These metadata observations do not verify downloaded weights, loader replication or resident memory; all tensor hashes/dtypes and the selected revision must be read back before admission. See SOURCES.json for the distinction between pinned and moving-source reads.

| Model label | TP | Ideal payload GiB/rank | KV GiB/rank | Subtotal GiB/rank |
|---|---:|---:|---:|---:|
| 14B, 48 layers, head dim 128 | 2 | 13.756 | 0.375 | 14.131 |
| 32B, 64 layers, head dim 128 | 4 | 15.257 | 0.250 | 15.507 |
| 32B, 64 layers, head dim 128 | 8 | 7.628 | 0.125 | 7.753 |

These subtotals exclude every remaining term above and are not fit certificates. At concurrency 8, the 32B TP4 KV term alone becomes 2 GiB per rank. A framework may reserve much more memory for its page pool. Freeze `max_model_len`, maximum sequence count, GPU-memory-utilization policy and graph sizes before running; report both the configured reservation and measured utilization. Start with 1024 allocated tokens for the smoke and 4096 for the planned panel, not the checkpoint's maximum context.

## Topology is a correctness and performance input

Record GPU UUIDs and stable rank mapping, `nvidia-smi -L`, selected device properties, `nvidia-smi topo -m`, actual P2P access matrix, bridge status, PCIe link widths/speeds under load, CPU NUMA placement and host-memory capacity. A nominally eight-card machine is not an eight-way NVLink fabric. Do not change ACS/IOMMU/security or network settings to manufacture P2P access.

The pinned vLLM [batch-invariance documentation](https://github.com/vllm-project/vllm/blob/75be5c3919b6a82fa1885c0d0a2250adba477413/docs/features/batch_invariance.md) supports compute capability ≥8.0 and explains fixed-order custom all-reduce. However, [custom_all_reduce.py](https://github.com/vllm-project/vllm/blob/75be5c3919b6a82fa1885c0d0a2250adba477413/vllm/distributed/device_communicators/custom_all_reduce.py) disables its path for more than two GPUs without full connectivity. Its supported topology and message conditions must actually hold. A warning followed by NCCL fallback is not proof of equivalent arithmetic.

Consequently, `VLLM_BATCH_INVARIANT=1` is necessary infrastructure to investigate, not an eight-A5000 numerical certificate. TP2 is the first gate. TP4/8 may need a CUDA fixed-order collective implementation or a topology-qualified alternative. All-gather plus explicit rank-order summation is an auditable candidate, but costs extra memory and communication and must run in both reference and candidate. Its performance must be compared with the strongest native engine, not hidden.

## What should be learned before custom kernels

1. Can the unchanged pinned runtime load and generate on the actual hardware at the selected TP and BF16 configuration?
2. Are repeated scalar references and native multi-query verification identical at complete logits and active state under the fixed deployment?
3. Does native invariant batching already solve the reference constraint without HeteroSpec intervention?
4. Where is time actually spent: matrix kernels, attention, communication, scheduler, graph replay, draft work or cache transitions?

If the native path is already invariant and fast, the useful research result may be a smaller integration, an improved phase/state interface, or a negative result. Do not add a slower artificial reference to create a favorable speedup.

## SGLang and optional DeepSeek architecture path

At SGLang `219b7e7a688363bac9ef09eacf80e44eef9efe4b`, the speculative-decoding documentation offers NGRAM, STANDALONE, EAGLE and MTP routes. NGRAM is CUDA-only, excludes attention data parallelism above one, and disables overlap scheduling/mixed chunked prefill. UNO requires FA3 and TP=PP=1, so it is not the eight-A5000 route. The pinned installation documentation requires CUDA 13 and identifies 0.5.19 as the last CUDA 12 lane. An older installed driver may therefore favor vLLM, whose inspected default binary documentation uses CUDA 12.9. Verify actual builds rather than assuming either latest package works. SGLang comparisons must disclose their scheduler differences.

DeepSeek-V2-Lite has 16B total parameters, 2.4B active, 27 layers, 16 attention heads, 64 routed experts, two shared experts and six selected routed experts per token. Its MLA cache and MoE dispatch are separate contracts. Its advertised 32k context is not an instruction to allocate the larger positional limit in the configuration. Official DeepSeek-V3 `inference/model.py` illustrates BF16/FP8 linears, tensor/expert partitioning and naive/absorbed MLA caches, but is not a ready-made HeteroSpec or complete serving adapter.
