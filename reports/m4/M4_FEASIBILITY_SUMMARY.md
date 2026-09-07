# M4 Feasibility Summary

## Decision

**M4 PLATFORM = HALTED AT M1 EXACT-TOKEN GATE**

The reboot resolved the two operational blockers: the 8B/0.6B pair repeatedly
ran with swap fixed at zero, and Silemetry supplied valid no-sudo component
power through IOReport. The original question-395 canary again matched exactly.
However, frozen question 469 diverged deterministically at output token 24 for
`k=2,4,6`, including a fresh-process `k=2` reproduction. The 12Q performance
pilot therefore stopped after its first 4 of 144 planned blocks. No speed or
energy result is promoted.

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
Qwen3-8B target = SAFE FOR BOUNDED 64-TOKEN PROTOCOL
Qwen3-8B + 0.6B = SAFE FOR BOUNDED 64-TOKEN PROTOCOL
```

After reboot, two paired canaries and the first pilot block retained swap at
0 MiB with normal memory pressure. This does not qualify larger contexts or
models.

### Correctness

```text
BASELINE = PASS
SPECULATIVE = PASS
EXACT MATCH = FAIL (FROZEN QUESTION 469)
```

### Telemetry

```text
POWER TELEMETRY = PASS WITH PRIVATE-API LIMITATION
```

Silemetry TelemetryCore returned CPU/GPU/ANE/DRAM/package power without sudo.
It relies on private IOReport/AppleSMC interfaces, so captures are suitable for
this fixed machine/build but not presented as a stable cross-version API.

## Bounded next-phase recommendation

Do not resume the 12Q performance run under the current exact-token protocol.
The bounded result is a correctness failure of native speculation with the
selected 4-bit target, traced to a target-logit near tie that changes under the
batched verification shape. A future, separately approved diagnostic could
test a higher-precision target or independent runtime, but it must not be
merged with this stopped condition.

Do not enter 60Q, 420Q, a 14B run, ANE development or a custom speculative-runtime rewrite without a separate decision.
