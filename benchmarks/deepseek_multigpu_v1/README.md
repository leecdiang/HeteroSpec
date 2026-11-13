# DeepSeek models and reference constrained inference on eight A5000 GPUs

**Terms:** TP means tensor parallelism; PP means pipeline parallelism; KV means key/value cache; BF16 is bfloat16; F16 is IEEE float16; F32 is IEEE float32; GQA means grouped-query attention; MLA means multi-head latent attention; MoE means mixture of experts; FA2 means FlashAttention 2; SM denotes NVIDIA streaming-multiprocessor architecture; P2P means GPU peer-to-peer access.

**Status: source research, implementation plan and CPU-only preflight. No GPU run, new speedup, native adapter or numerical qualification is claimed by this PR.**

目标是在单机 8×RTX A5000 上，把 HeteroSpec 的参考约束执行方法推进到主流多卡框架与更大的模型，而不是把八个单卡副本称为单请求多卡加速。DeepInfer 本身不支持 A5000；这不阻止采用 vLLM、SGLang 等主流框架开展规模扩展。

## Decision

1. **Primary engineering route:** vLLM, BF16 `DeepSeek-R1-Distill-Qwen-14B` for two-GPU qualification, then `DeepSeek-R1-Distill-Qwen-32B` at TP4 and TP8. These are dense Qwen-family distilled models, not the full DeepSeek MoE. Fit and execution remain conditional on checkpoint, runtime and per-rank measurements.
2. **Independent mainstream comparator/fallback:** SGLang on the same model and hardware allocation. Do not implement both adapters simultaneously before the first route's numerical and collective gates are resolved.
3. **Architecture extension:** DeepSeek-V2-Lite is a separate MLA/MoE experiment after the dense path works. A distill result does not establish MLA/MoE or DeepInfer support.
4. **Official DeepInfer:** retain a concrete port map, but do not launch its default checkpoint on this host. The pinned release supports SM100/Ascend 950 and DeepSeek-V4.1-Flash. SM86 and this memory budget fail independent requirements.

The engineering target is **more than 5% resident end-to-end latency reduction against a same-speculation strong baseline**. It must generalize across a representative supported domain in mainstream frameworks, not only a selected condition. It is a hypothesis, not a promised result or a condition for retaining data.

The central research question is the incremental benefit over the mainstream engine's **own optimized reference-compatible batched path**. vLLM and DeepInfer already have batch-invariant modes. Reimplementing an existing invariant kernel or beating an intentionally weak column loop would not establish a new contribution.

## Read and run

[中文详细摘要](ZH_SUMMARY.md) · [反例与相关工作核查](COUNTEREXAMPLES.md)

- [Portable method and representative validation](PORTABLE_METHOD.md): broader >5% objective, candidate mechanisms and independent multi-scenario confirmation.
- [Feasibility and framework choice](FEASIBILITY.md): hardware, models, memory, topology and source pins.
- [Integration design](INTEGRATION.md): exact reference, vLLM seams, distributed commit/rollback, native DeepInfer map and implementation milestones.
- [Experiment protocol](PROTOCOL.md): staged 2→4→8 GPU study, strong controls, full cost, failures and stopping rules.
- [Source manifest](SOURCES.json): immutable code references and limits.
- [Current status](STATUS.json): machine-readable separation of researched, implemented and unrun work.
- [Validation record](VALIDATION.json): CPU tests, design checks and exact file hashes.

From the repository root, with Python 3.11 or newer and no extra packages:

```sh
python -B -m unittest discover -s benchmarks/deepseek_multigpu_v1/tooling -p 'test_*.py' -v
python -O -B -m unittest discover -s benchmarks/deepseek_multigpu_v1/tooling -p 'test_*.py' -v
python -B benchmarks/deepseek_multigpu_v1/tooling/preflight.py benchmarks/deepseek_multigpu_v1/tooling/examples/qwen32b_tp8.json
```

The last command intentionally reports missing hardware evidence and exits nonzero. The examples contain **planning assumptions**, not fabricated server observations. `estimated_possible`, if later obtained with real measurements, is still not runtime admission or numerical qualification. The tool does not install software, download checkpoints, contact a server, execute a model or authorize a run. See [tooling documentation](tooling/README.md).

## What changes and what does not

This is a new directory on a new branch based on `main` at `cfc9edf4582bb3c02885c9171a2ab2635bf19588`. It does not stack on, edit, merge or reinterpret #216, #217 or #218. Their model bytes, scalar references, experimental records, request ceilings and pending work remain separate. Source observations from those PRs explain reuse boundaries; their timings are not measurements of vLLM, SGLang, DeepInfer or eight-GPU inference.

The CPU tool is a memory/capability planner, not a mock implementation presented as a backend. A source-only review cannot certify hardware support, rank safety, bitwise equality, throughput, energy or a speedup. The next deliverable is an unchanged-engine TP2 smoke and a saved engine-native reference, followed by a minimal instrumented adapter. This PR deliberately does not publish a speculative speedup estimate.
