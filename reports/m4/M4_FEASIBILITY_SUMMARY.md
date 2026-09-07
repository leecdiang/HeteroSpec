# M4 Feasibility Summary

## Decision

**M4 MLX PATH = HALTED; LLAMA.CPP METAL `k=2` = POSITIVE SIGNAL**

The reboot resolved the two operational blockers: the 8B/0.6B pair repeatedly
ran with normal memory pressure, and Silemetry supplied valid no-sudo component
power through IOReport. The original question-395 canary again matched exactly.
However, frozen question 469 diverged deterministically at output token 24 for
`k=2,4,6`, including a fresh-process `k=2` reproduction. The 12Q performance
pilot therefore stopped after its first 4 of 144 planned blocks. An 8-bit MLX
target still diverged on questions 395 and 469. In contrast, the independent
llama.cpp Metal Q8_0 target/draft pair matched exactly on both questions for
`k=2,4,6`. The subsequent 12Q decision matrix passed all 48 exact comparisons;
`k=2` delivered 1.350x geometric-mean decode speedup, was faster on 11/12
questions and improved paired package energy by 1.162x.

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

MLX/Metal and a native speculative canary were tested. MPS executed an on-device tensor operation and its installed Transformers source supports assisted generation, but Qwen3 assisted generation was not model-tested. llama.cpp detected the M4 Metal device, loaded official Q8_0 GGUF target/draft artifacts and passed the bounded two-question exactness gate for `k=2,4,6`.

### Memory

```text
Qwen3-8B target = SAFE FOR BOUNDED 64-TOKEN PROTOCOL
Qwen3-8B + 0.6B = SAFE FOR BOUNDED 64-TOKEN PROTOCOL
```

After reboot, two paired canaries and the first pilot block retained normal
memory pressure. Memory is qualified with a composite PASS/WARN/FAIL gate,
not a `swap == 0` rule. This does not qualify larger contexts or models.

### Correctness

```text
BASELINE = PASS
SPECULATIVE = PASS
MLX EXACT MATCH = FAIL
LLAMA.CPP Q8_0 EXACT MATCH = PASS (12/12, k=2/4/6)
LLAMA.CPP k=2 PERFORMANCE = PASS (1.350x decode, 11/12 faster)
LLAMA.CPP k=2 ENERGY = PASS (1.162x paired package-energy improvement)
```

### Telemetry

```text
POWER TELEMETRY = PASS WITH PRIVATE-API LIMITATION
```

Silemetry TelemetryCore returned CPU/GPU/ANE/DRAM/package power without sudo.
It relies on private IOReport/AppleSMC interfaces, so captures are suitable for
this fixed machine/build but not presented as a stable cross-version API.

## Bounded next-phase recommendation

Do not resume performance work on MLX. The llama.cpp Metal 12Q matrix provides
a strong architecture-control positive signal for `k=2`; `k=4` was near
break-even and `k=6` was negative. A bounded `k=2` replication is justified if
tighter noise estimates are required, while expansion to 60Q remains a
separate decision.

Do not enter 60Q, 420Q, a 14B run, ANE development or a custom speculative-runtime rewrite without a separate decision.
