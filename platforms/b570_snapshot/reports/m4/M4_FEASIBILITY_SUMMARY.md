# M4 Feasibility Summary

## Decision

**M4 PLATFORM = CLOSED — INITIAL SIGNAL NOT GENERALIZED**

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
questions and improved paired package energy by 1.162x. Mechanism follow-up
confirmed a profitable high-acceptance region but found session-sensitive
per-question magnitudes, so 1.350x is an initial signal rather than a replicated
effect-size estimate.

The final frozen-k validation used 24 previously unseen prompts with three
paired repetitions. All 72 pairs were exact, but prompt-level geometric-mean
speedup was 0.842x (95% prompt-bootstrap CI [0.809, 0.877]), only 1/24 prompts
was faster, and package-energy improvement was 0.678x. Even the highest
accepted-tokens/round tertile remained below break-even at 0.921x.

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
LLAMA.CPP k=2 DISCOVERY = INITIAL POSITIVE SIGNAL
LLAMA.CPP k=2 CONFIRMATORY PERFORMANCE = FAIL (0.842x, 1/24 faster)
LLAMA.CPP k=2 CONFIRMATORY ENERGY = FAIL (0.678x improvement ratio)
FINAL M4 DECISION = CLOSED — INITIAL SIGNAL NOT GENERALIZED
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
a strong initial architecture-control signal for `k=2`; `k=4` was near
break-even and `k=6` was negative. Synchronized microbenchmarks found
`V2=1.022--1.076`, idle draft residency added only 0.65%, and 12Q
acceptance/speedup correlation was 0.893. A bounded full `k=2` paired
replication was therefore run on 24 frozen unseen prompts; it failed to
generalize the positive performance and energy result.

The confirmatory stop rule has now fired. Do not run 60Q or attempt to rescue
the M4 result with another model, runtime, draft depth or algorithm. Preserve
the mechanism result—cheap `k=2` verification and strong acceptance dependence—
while reporting that an always-on profitable region did not generalize to the
frozen unseen sample.

Do not enter 60Q, 420Q, a 14B run, ANE development or a custom speculative-runtime rewrite without a separate decision.
