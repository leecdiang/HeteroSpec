# M4 Minimal Experiment Design

## Research role

Platform C is a **unified-memory, single-vendor integrated-runtime architecture control**, not a replacement for Platform A and not a third full benchmark platform.

## Staged matrix

| Gate | Work | Stop condition |
|---|---|---|
| M0 | Freeze system/runtime/model manifests; load Qwen3-8B and 0.6B 4-bit; 30 s idle telemetry; two-prompt baseline canary | Runtime error, fallback, swap growth, abnormal pressure/thermal state |
| M1 | Exact-token canary: baseline vs MLX-LM native speculation, fixed `k=2` | Any mismatch stops formal performance promotion |
| M2 | Existing 12 prompts: baseline plus fixed `k=2,4,6`; dynamic/default is optional and separate | Do not expand prompt count |
| M3 | Repeat only correctness-qualified conditions with qualified telemetry | Logger perturbation >2% or unavailable/ambiguous units requires limitation label |

Use Qwen3-8B target + Qwen3-0.6B draft, `temperature=0`, batch 1 and 64 generated tokens, matching the root-cause diagnostic. Use runtime-native 4-bit MLX models as an architecture-specific practical configuration. Warm models/caches before timing, counterbalance condition order, and separate model-load/prefill from decode.

Collect TTFT, completion time, output tok/s, TPOT, per-token ITL p50/p95, offered/accepted draft tokens, acceptance rate, accepted tokens/round, verification rounds, MLX active/peak memory, RSS, memory pressure, swap deltas, CPU/GPU utilization when reliable, thermal state and only qualified power/energy domains.

## Interpretation

- Native speculation >1.10x geometric-mean speedup, exact on 12/12 and without energy/memory regression: M4 justifies a later custom-path investigation.
- Approximately 1.00x: stop; supports a broader “limited headroom for local 8B draft-model speculation” result.
- Faster but non-exact: correctness failure, not a win.
- Exact but slower: valid negative architecture-control result.

No 60Q/420Q expansion, 14B matrix, ANE draft, custom speculative rewrite or cross-platform absolute tok/s comparison belongs to this phase.

