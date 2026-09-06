# M4 Runtime Options

## Recommendation

Use **MLX/MLX-LM as the primary feasibility runtime, conditional on an exact-token correctness gate**. Use **llama.cpp Metal as the fallback/independent implementation check** if MLX-LM exactness fails. Keep **Transformers + MPS as a compatibility control**, not the primary performance path.

| Runtime | Apple GPU / unified memory | Native draft speculation | KV/cache path | Python integration | Measurement fit | Decision |
|---|---|---|---|---|---|---|
| MLX-LM | Native MLX CPU/GPU arrays share unified memory | Yes: `draft_model` and controllable draft-token count | Target and draft prompt caches are maintained by native generation | Strong | Per-token stream records timing and whether a token came from draft; MLX exposes allocator peak | Primary, correctness-gated |
| Transformers + MPS | PyTorch MPS; unified memory underneath | Yes through `assistant_model`; constant/dynamic assistant schedules exist | Integrated Transformers generation cache | Strong | Familiar schema, but unsupported MPS ops can fail or fall back | Compatibility control only; CPU fallback must be disabled for formal data |
| llama.cpp Metal | Mature Metal backend and GGUF ecosystem | Yes: draft model, max/min draft tokens and explicit draft device options | Native context/cache management | CLI-first; bindings add another layer | Good CLI counters, harder token-level schema integration | Fallback and independent validation |

MLX-LM's current CLI/Python implementation supports greedy generation, batch-1 streaming, a separate draft model, a fixed number of draft tokens and target/draft prompt caches. Its stream records generation timing and draft provenance. MLX itself allows CPU and GPU operations over unified-memory arrays without an explicit device copy, and exposes peak allocator memory. See the official [MLX-LM generation implementation](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/generate.py), [server implementation](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/server.py), [server options](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/SERVER.md), [MLX unified-memory documentation](https://ml-explore.github.io/mlx/build/html/usage/unified_memory.html), and [`get_peak_memory`](https://ml-explore.github.io/mlx/build/html/python/_autosummary/mlx.core.get_peak_memory.html).

The recommendation is conditional because open MLX-LM reports describe greedy speculative divergence for current Qwen3 combinations and cache-trimming limitations. These are not proof that this exact pair will fail on M4, but they make token-by-token qualification mandatory: [issue 1423](https://github.com/ml-explore/mlx-lm/issues/1423), [issue 1470](https://github.com/ml-explore/mlx-lm/issues/1470), and [issue 1446](https://github.com/ml-explore/mlx-lm/issues/1446).

Transformers officially supports assisted decoding with `assistant_model`, greedy mode, and fixed or dynamic assistant-token schedules; it does not support batched assisted inputs. MPS is supported on Apple Silicon, but missing operations can trigger an optional CPU fallback. Formal runs must fail rather than enable that fallback. See [assisted decoding](https://huggingface.co/docs/transformers/assisted_decoding), [generation configuration](https://huggingface.co/docs/transformers/main_classes/text_generation), and [Apple Silicon/MPS](https://huggingface.co/docs/transformers/v5.7.0/en/perf_train_special).

llama.cpp exposes fixed speculative controls and an explicit draft device in its official [speculative decoding guide](https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md). Its GGUF quantization is a valid architecture-specific practical configuration, not a bit-exact counterpart of Windows NF4/OpenVINO INT4.

## Version policy

Do not freeze a version from a Windows host. On the M4, install the latest stable mutually compatible MLX and MLX-LM releases, record exact versions and commits/model revisions, run the two-prompt canary, and only then freeze `requirements/macos-mlx-lock.txt`. Nightly builds are excluded from formal results.

## Neural Engine

MLX's documented device choices are CPU and GPU; it is not a direct ANE execution route. Core ML could make ANE work a future conversion project, but autoregressive dynamic shapes, mutable KV state, operator placement and dispatch would need separate qualification. ANE is therefore out of the first M4 phase and no ANE power or performance claim is authorized.

