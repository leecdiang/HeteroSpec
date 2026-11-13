# Integration design

**Terms:** TP means tensor parallelism; PP means pipeline parallelism; KV means key/value cache; BF16 is bfloat16; F16 is IEEE float16; F32 is IEEE float32; GQA means grouped-query attention; MLA means multi-head latent attention; MoE means mixture of experts; FA2 means FlashAttention 2; SM denotes NVIDIA streaming-multiprocessor architecture; P2P means GPU peer-to-peer access.

## The transferable method

HeteroSpec groups known queries only when their physical cache requirements and arithmetic recipes can coexist without changing the chosen reference. Its existing Q4_K/Q6_K weight-quantization CUDA recipes are not a universal matrix-multiplication format. Their scalar-dot reductions, Q8_1 block-quantized activation bytes and cache layout are specific to the pinned llama.cpp build.

In the [existing strong control](https://github.com/leecdiang/HeteroSpec/blob/f419a89d54f4ec93b4c9c328b4ea9f416ae3c989/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/execution_v1/build_backend.py), B quantizes all columns once, then invokes the unchanged scalar-dot kernel per column. C groups independent channels while retaining scalar-column arithmetic. B is allowed to share preparation; requiring it to repeat every quantization would weaken the comparator. Its guards require local same-device operands, Q4_K/Q6_K × F32, bounded widths and specific layouts. These guards do not establish vLLM BF16, tensor parallelism or paged-KV support.

The current [query-layout kit](https://github.com/leecdiang/HeteroSpec/blob/cfc9edf4582bb3c02885c9171a2ab2635bf19588/src/query_layout/README.md) also explicitly excludes arbitrary fused attention and concurrent multi-sequence use. Its process-wide layout setter must not be reused as a request-scoped distributed interface.

## Reference policy before optimization

Maintain three visibly different references/comparators:

- **R_native(p):** an unmodified pinned mainstream engine deployment at fixed TP degree p, topology, rank order, precision, graph policy and scheduler settings. Save repeated scalar decode references with ordinary prompt prefill. Establish repeatability before making any numerical claim.
- **R_invariant(p):** the engine's supported invariant mode with its selected kernels and collectives, qualified separately. If a new CUDA ordered collective is needed, call the reference **R_ordered(p)** and record that semantic change before candidate development. It is not bitwise equivalence to stock NCCL or to R_native.
- **R_legacy:** the existing HeteroSpec GGUF/Q4 reference. It remains unchanged and does not qualify either new reference.

Choose and freeze the study's reference after source/support investigation and before collecting performance outcomes. The aim is to preserve a useful deployment reference, preferably the existing invariant mode, not invent a deliberately slow scalar implementation. Report the latency cost of invariant/ordered mode versus R_native as part of the result. If R_native cannot be repeated and the user requires preservation of that exact deployment, that lane is blocked; a separately labelled reference does not silently satisfy it.

Use a distinct R for each TP degree. Changing p, sharding, rank order or collectives can change floating-point accumulation. The candidate must equal its own frozen R(p), not a reference regenerated after observing a mismatch. Cross-degree output and task-quality comparisons are additional evidence, not a substitute for within-degree equality.

For every declared observation boundary compare complete finite logits and canonical active state, not only argmax IDs. If only decode continuation from a fixed prefill state is qualified, state that scope. To claim complete request equivalence, prefill, chunking, graph capture, acceptance, correction/bonus and final state must also pass.

## vLLM source map and first patches

All paths in this section refer to [vLLM 75be5c39](https://github.com/vllm-project/vllm/tree/75be5c3919b6a82fa1885c0d0a2250adba477413). The inspected `gpu_worker.py` selects `v1/worker/gpu/model_runner.py` for normal non-multimodal execution; no old `VLLM_USE_V2_MODEL_RUNNER` switch appears in this pinned envs file. Native `ngram` maps to `NgramGPUSpeculator`. These source checks identify the selected integration path, not a completed runtime test. Do not patch an obsolete EAGLE path from an older tutorial.

| Seam | Pinned path | Proposed change and acceptance condition |
|---|---|---|
| Native BF16 arithmetic | `vllm/model_executor/determinism/batch_invariant.py` | Reuse and instrument the existing Ampere persistent Triton path before inventing a new projection kernel. Record tile/reduction policy and prove actual operand correspondence. |
| Collective selection | `vllm/distributed/device_communicators/cuda_communicator.py`, `custom_all_reduce.py` | Log actual custom/NCCL/fused paths. Add an explicit opt-in ordered CUDA fallback only if needed and qualified. No silent policy switches by message size. |
| Target model | `vllm/model_executor/models/qwen2.py` | Instrument projection, norm/rotary and layer output boundaries without changing the model or tokenizer. |
| Query and position construction | `vllm/v1/worker/gpu/input_batch.py` | Build request-local plan metadata beside query starts, positions, slots and sampled/draft token combination. Preserve existing ownership and post-update semantics. |
| Verification execution | `vllm/v1/worker/gpu/model_runner.py` | Carry immutable plan and epoch through forward execution; collect physical dispatch and rank receipts. Reject unsupported descriptors before scheduling kernels. |
| Attention | `vllm/v1/attention/backends/flash_attn.py` | Derive legality from actual block tables, lengths, masks, positions and KV dtype. In invariant mode retain its scheduling/split constraints. No application of dense-cache formulas to paged state. |
| Proposer lifecycle | `vllm/v1/worker/gpu/spec_decode/speculator.py`, `speculator_config.py`, `ngram/` | Start with the native n-gram proposer. Preserve its lifecycle; a proposer plugin alone is not HeteroSpec. |
| Verification and sampling | `vllm/v1/worker/gpu/spec_decode/rejection_sampler.py` | Keep the native semantics initially. Verify logits segment ownership, accepted prefix, correction/bonus and EOS accounting. |

On SM86, the pinned invariant implementation replaces relevant cuBLAS operations with persistent Triton operations because Ampere cuBLASLt is not made invariant simply by selecting a workspace option. This is a useful foundation, but it does not prove invariance of every speculative path, backend, state transition or TP collective.

Start with BF16 weights/activations, BF16 KV explicitly chosen and recorded (F16 would be a separately qualified configuration), FA2 where supported by the selected path, eager target execution, fixed prefill policy, greedy decoding, one live request and no prefix sharing. No FP8 substitution. Each later feature is a separate qualification: graphs, concurrency, chunked prefill, prefix caching, learned drafting and MLA/MoE.

## Fixed-order collective option

The current communicator's floating-point `all_reduce_batch_invariant` fallback is ROCm-only. The helper all-gathers rank contributions, sums them in ascending rank order in FP32 and casts once. A small CUDA routing change is conceptually possible, but changing only one `if` is not sufficient engineering validation.

Required implementation work:

1. Register an explicit collective policy and version in the run configuration and graph key. Choose one policy for all eligible floating reductions; do not mix custom and fallback arithmetic by tensor size without proving equality.
2. Audit row-parallel linear, embedding/vocabulary reductions, sequence-parallel reduce-scatter, fused all-reduce/norm, symmetric-memory paths and compile transformations. Disable unsupported alternate paths, with a visible capability failure rather than an unobserved fallback.
3. Validate contiguous and supported strided inputs, BF16/F16/F32, zero/odd/aligned sizes, chunk boundaries and rank counts 2/4/8. Prove output ownership and no input alias corruption. Explicitly define rounding and overflow/NaN handling.
4. Reuse bounded buffers where legal; count all-gather bytes, temporary memory, allocations and synchronization. Capture support is separate. A benchmark that excludes the fallback's extra communication cannot claim a full-request gain.
5. Run the same policy in the saved reference and every exactness arm. Compare stock native serving separately so a costly reference choice is visible.

Fixing an NCCL algorithm/protocol environment variable alone is not a proof of fixed reduction order across shapes, implementations or capture modes. An ordered fallback may lose badly on PCIe; that is a valid result and a reason to prefer a topology-supported native path or stop expansion.

## Request-scoped plan contract

The adapter should introduce a typed immutable `VerificationPlan`, not a mutable global layout flag. Required contents:

- engine/model/kernel/collective policy identities and per-rank shard mapping;
- request ID plus generation/epoch, phase, token positions and logical output owner;
- canonical incoming active-state digest, allocated slot/block ownership, valid lengths and visible prefix;
- query order and any reversible row/channel mapping;
- group-specific mask, position, extent, cache dtype/layout, kernel recipe and dispatch constraints;
- lookahead capacity, graph/capture identity and a proposed post-state, distinct from committed state.

A group is legal only if every row's scalar-visible keys, mask and arithmetic contract remain unchanged. Logical length alone does not prove equal physical page access. Query reordering must preserve causal position/masks and restore output order before sampling. Cache writes must follow logical token ownership, not temporary execution order.

Do not export raw allocator padding as scientific state. Canonical state export includes every active K/V element in logical layer/head/token order, plus positions, valid lengths, block ownership, frontier logits and any engine state needed to reproduce continuation. Compare canonical bytes and retain layout metadata separately. Unused slots must never become visible after rollback or request reuse.

## Distributed execution and failure semantics

All ranks enter collectives in the same order with matching operation IDs, shapes, dtypes and group membership. The coordinator broadcasts a plan digest and monotonically increasing epoch; each rank validates its local shard and state before work begins. A rank must not locally skip a collective because its group is empty. Empty participation is represented by an agreed schedule, not divergent control flow.

Treat speculative execution as prepare → verify → commit/rollback at a common logical boundary:

1. Reserve bounded lookahead slots and retain the committed prefix.
2. Execute every rank's prepared plan and produce verification receipts.
3. Decide accepted-prefix length once using the canonical target logits/sampling policy.
4. Broadcast accepted length, correction/bonus and stop reason; apply the same logical transition everywhere.
5. Publish completion only after all rank state receipts agree.

This is an application protocol, not fault-tolerant distributed consensus. A dead rank or timed-out collective aborts the entire worker group and invalidates the in-flight request. Restart from a saved committed state or a fresh model process. Do not claim transparent recovery or reuse potentially inconsistent KV. Preserve failure receipts and cost; avoid forcibly resetting a GPU used by another job.

Qualification cases include no acceptance, interior rejection, all accepted plus bonus, pending correction, EOG at each position, output cap at each position, page boundary, near capacity, cancellation before/after verify, worker exit, stale epoch, duplicated completion, rank-order mismatch and two request lifecycles reusing slots. Shared-prefix refcounts and copy-on-write are future gates, not implicit support.

## Native DeepInfer port map

At [a679bb86](https://github.com/deepseek-ai/DeepInfer/tree/a679bb86ce36e883a98a97733492b686e5b9a08e), relevant components are:

- `csrc/engine/input_metadata/prepare_tensor_input_v4.cpp`, `sequence.hpp`, `scheduler.hpp`, `mtp_varlen.hpp`, `process_output.hpp`: query construction, scheduler and variable-length verification ownership.
- `deepinfer/model_executor/input_metadata/` and `models/mtp/dflash.py`: model-side speculative metadata and DSpark-related execution.
- `deepinfer/model_executor/models/v4_modules/`: MLA/indexed attention, compression, SWA, cross-layer/YOCO, MoE and Engram components.
- `deepinfer/worker/model_runner.py`, `cuda_graph_runner.py`, `dflash_cuda_graph_runner.py`, `cache_engine.py`: execution, graph and state management.
- `deepinfer/model_executor/parallel_utils/`: distributed collective and buffer policies.

A real port must implement SM86 alternatives for every required kernel, memory format and communication primitive; support a fitting model; map compressed/SWA/MLA state and bounded replay; and qualify native DSpark plus invariant execution as strong baselines. The README explicitly says a complete service still needs a KV cache system, disaggregation and replica load balancing. Its offline implementation must not be described as a drop-in complete server. These tasks are much broader than wrapping HeteroSpec's current query view.

## Milestones and stop conditions

1. **E0: reproducible mainstream load.** Pinned source/build, actual host manifest, model/tokenizer hashes, unchanged-engine TP2 output and complete memory accounting.
2. **E1: saved reference and mismatch map.** Repeated scalar versus native q=4/q=8 on identical inputs/state; first differing operator located. Preserve all failures.
3. **E2: one useful operation.** Implement only a source-justified grouping opportunity, with G/B/native/group controls and full-vector equality. If native batched execution already wins and is invariant, retain it.
4. **E3: complete request adapter.** State transaction and greedy endpoint gates at TP2, then TP4, then TP8. Each topology receives its own reference.
5. **E4: clean cost and serving controls.** Complete the frozen protocol, deliver source and replayable results. Negative or no-increment results remain publishable evidence.

No stage is complete in this PR. An equality failure blocks that candidate's timing, not all continued diagnosis. A memory/driver/topology failure selects a documented smaller supported configuration or mainstream fallback; it must not be concealed by changing model, quantization or reference mid-panel.
