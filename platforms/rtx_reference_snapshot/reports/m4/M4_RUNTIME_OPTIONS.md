# M4 Runtime Options

## Decision

**PRIMARY M4 RUNTIME: MLX-LM 0.31.3 on MLX 0.32.2**, correctness-gated. llama.cpp Metal 0.4.0 is the independent fallback. Transformers 5.16.1 + PyTorch MPS 2.14.0 is a compatibility control, not the formal runtime.

| Runtime | Apple GPU | Unified memory | Native speculative | KV reuse | Acceptance stats | Python integration | Recommended |
|---|---|---|---|---|---|---|---|
| MLX-LM 0.31.3 | PASS: default MLX device is GPU and Metal is available | Native MLX memory model | PASS: separate `draft_model` | PASS: persistent target + draft prompt caches, with cache trimming | PARTIAL: per-output `from_draft` exposes accepted draft tokens; no offered-token/round object | Strong | **Primary** |
| llama.cpp 0.4.0 | PASS: `MTL0: Apple M4` detected | Metal backend on Apple Silicon | PASS: draft-simple and other modes | PASS: target/draft KV types and prompt cache controls | PARTIAL: CLI performance/metrics, but integration requires parsing or bindings | CLI-first | Fallback / independent check |
| Transformers 5.16.1 + MPS | PASS: MPS built, available, and an operation executed on-device | PyTorch MPS allocation | Source/API support for `assistant_model` | Integrated generation cache | Limited public per-round telemetry | Strong | Compatibility control |

## Installed implementation audit

MLX-LM's generate and server CLIs expose `--draft-model` and `--num-draft-tokens`. The installed `speculative_generate_step`:

- defaults to greedy `argmax` when no sampler is provided;
- keeps separate target and draft prompt caches across proposal rounds;
- proposes exactly the fixed `num_draft_tokens` subject to the remaining output cap;
- trims both caches after rejection;
- yields each output token with a `from_draft` boolean;
- rejects non-trimmable target caches.

This is fixed-k native speculation. No dynamic speculation scheduler was found in the installed MLX-LM CLI or implementation. Exact offered tokens and per-round timings are not exposed by the high-level response and would require a small instrumentation patch; that is outside this feasibility phase.

Post-reboot expansion exposed a strict-correctness limitation. On frozen
question 469, the sequential target path selected token `14374` while the
batched speculative target verification selected token `16` at output index
24. The shared-prefix target logits show a near tie that becomes an exact BF16
tie in the batched shape. Thus “native speculative = available” remains true,
but “native speculative = exact under this quantized target” is false.

llama.cpp was installed externally through Homebrew, not vendored. Its CLI
exposes a draft model/device, draft KV types, min/max draft tokens, prompt-cache
reuse and metrics. The independent Metal control subsequently ran official
Qwen Q8_0 GGUF target/draft artifacts: frozen questions 395 and 469 matched the
baseline exactly for `k=2,4,6`. This makes llama.cpp the qualified correctness
control; performance remains unqualified until the bounded 12Q matrix runs.

Transformers source includes assisted generation, constant/heuristic schedules and assistant cache handling. Only an MPS tensor-operation gate was run; Qwen3 assisted generation on MPS was not model-tested, so it is PARTIAL rather than a formal-runtime pass.

## ANE audit

The Core ML compiler is installed, and `powermetrics` advertises an ANE sampler. MLX itself exposes CPU/GPU devices, not a direct ANE target. Converting Qwen3 autoregressive decode would require operator-placement, dynamic-shape and mutable-KV-cache qualification. **ANE = FUTURE WORK**; no implementation or performance claim is made.
