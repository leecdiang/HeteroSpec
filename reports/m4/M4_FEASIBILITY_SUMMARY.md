# M4 Feasibility Summary

## Decision

**M4 PLATFORM = READY FOR 12Q PILOT**, conditional on a fresh zero-swap memory requalification and one privileged `powermetrics` qualification capture.

The M4 MacBook Air is suitable as HeteroSpec's architecture-control platform: native MLX speculation exists, target/draft KV caches persist, Metal execution works, the specified 8B/0.6B pair coexists, and the bounded `k=4` canary produced 64/64 exact target tokens. A one-prompt warm diagnostic showed useful speedup, so a later 12Q native control has research value. It is not ready to start that pilot in the current desktop session because swap grew during both target-only and paired canaries, and component-power fields remain unqualified without administrator authorization.

## Required status

### Repository

```text
CLONE = PASS
BRANCH = macos/m4-feasibility
```

### Runtime

```text
MLX = PASS
MPS = PARTIAL
llama.cpp Metal = PASS
```

MLX/Metal and a native speculative canary were tested. MPS executed an on-device tensor operation and its installed Transformers source supports assisted generation, but Qwen3 assisted generation was not model-tested. llama.cpp detected the M4 Metal device and exposed speculative/cache controls; no GGUF generation was run.

### Memory

```text
Qwen3-8B target = UNSAFE
Qwen3-8B + 0.6B = UNSAFE
```

Both configurations fit and ran, but the formal no-swap-growth rule failed in the current active desktop state. Reclassification to SAFE requires a fresh zero-swap rerun.

### Correctness

```text
BASELINE = PASS
SPECULATIVE = PASS
EXACT MATCH = PASS
```

### Telemetry

```text
POWER TELEMETRY = PARTIAL
```

The OS advertises CPU/GPU/ANE/thermal samplers at 1 s resolution, but actual `powermetrics` sampling requires root and non-interactive sudo was unavailable.

## Bounded next-phase recommendation

After the two preconditions pass, run only the existing 12 root-cause prompts:

- M0: Qwen3-8B target-only.
- M1: Qwen3-8B + Qwen3-0.6B native MLX-LM speculation.
- Fixed `k=2,4,6`, three repetitions per configuration; dynamic scheduling is omitted because installed MLX-LM exposes fixed `num_draft_tokens`, not a dynamic scheduler.
- Preserve exact-token gating, 1-second raw/aggregated telemetry, swap/pressure/thermal state and within-M4 relative speedup.

Do not enter 60Q, 420Q, a 14B run, ANE development or a custom speculative-runtime rewrite without a separate decision.
