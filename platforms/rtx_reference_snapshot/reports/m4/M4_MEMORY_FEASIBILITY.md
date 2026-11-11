# M4 Unified-Memory Feasibility

## Planning estimate

The selected MLX artifacts are native group-size-64 4-bit models. The verified files are 4,607,835,174 bytes for the target and 335,450,584 bytes for the draft.

For BF16 KV, bytes per token are estimated as `2 × layers × KV heads × head_dim × 2 bytes`: 144 KiB/token for Qwen3-8B and 112 KiB/token for Qwen3-0.6B.

| Pair / context | Pair KV estimate | Weights | Runtime/buffer allowance | 24 GB assessment before load |
|---|---:|---:|---:|---|
| 8B + 0.6B, 2k | 0.50 GiB | about 4.7--5.1 GiB | 2--4 GiB | Safe with substantial OS headroom |
| 8B + 0.6B, 8k | 2.00 GiB | about 4.7--5.1 GiB | 2--4 GiB | Feasible, but must gate on swap/pressure |
| 14B + 0.6B, 2k | about 0.53 GiB | about 8--9.5 GiB | 3--5 GiB | Estimate only; not authorized for this run |
| 14B + 0.6B, 8k | about 2.13 GiB | about 8--9.5 GiB | 3--5 GiB | Tight enough to require a separate future gate |

Initial measured state was zero allocated swap and 48% system-wide memory free. The selected short/medium smoke prompts and 64-token cap are far below the 2k row, so the estimate clears the load gate for Qwen3-8B + 0.6B. A passing run still requires no sustained swap growth and normal memory pressure.

## Pre-reboot measured smoke values

| Run | Prompt tokens | MLX peak | Swap before | Swap after | Formal memory gate |
|---|---:|---:|---:|---:|---|
| 8B target-only, ID 291 | 400 | 4.718 GiB | 1,751.75 MiB | 1,780.44 MiB | FAIL: +28.69 MiB |
| 8B + 0.6B, ID 395, k=4 | 21 | 4.742 GiB | 1,487.81 MiB | 1,751.75 MiB | FAIL: +263.94 MiB |

The machine began the overall audit at zero swap, but model download/loading and the active desktop session caused macOS to allocate swap before the formal canaries. Memory pressure still reported about 49--50% free, and no runtime OOM occurred. This proves the pair can coexist and execute, but it does not satisfy the stricter no-swap-growth benchmark gate.

**Qwen3-8B target = UNSAFE for formal benchmark in the current session.**

**Qwen3-8B + 0.6B = UNSAFE for formal benchmark in the current session.**

This is an operational classification, not evidence that 24 GB is intrinsically insufficient. MLX peak allocation is not total unified-memory use and remains labeled separately.

## Unified-memory interpretation

Unified memory can reduce physical device-to-device copies and model-coexistence friction. It does not eliminate kernel dispatch, synchronization, KV bookkeeping, cache trimming, Metal scheduling or contention when target and draft share the GPU. It therefore removes one architectural penalty without guaranteeing speculative speedup.

Qwen3-14B is estimate-only in this phase and was not downloaded or run.

## Post-reboot requalification

After a clean reboot, swap was 0 MiB with zero swap-ins and swap-outs, system
memory pressure reported 91% free, AC power was connected and Low Power Mode
was disabled. Two complete paired question-395 runs and the first four-block
question-469 pilot block retained normal memory pressure (85--86% free after
the paired runs).

**Qwen3-8B target = SAFE for the bounded 64-token M1/M2 protocol.**

**Qwen3-8B + 0.6B = SAFE for the bounded 64-token M1/M2 protocol.**

This replaces the earlier session-specific UNSAFE classification. The M2 run
was stopped for correctness, not memory, so this does not qualify larger
contexts, 14B, or any expanded benchmark.

## Composite memory gate

Swap is not an exhaustion-only signal on macOS and is not used as a binary
gate. Each run records pressure, swap and virtual-memory counter deltas before
and after execution; longer runs must additionally check throughput over time.

| Status | Criteria |
|---|---|
| PASS | Model loads and generates; memory pressure remains normal; no material swap growth, throttling, page-thrashing or sustained throughput decline; system remains responsive. |
| WARN | Stable or slowly growing swap is present, but pressure remains normal and there is no throttling, thrashing, sustained throughput decline or responsiveness issue. Continue only with the warning recorded. |
| FAIL | Pressure reaches a constrained state, pages throttle/thrash, swap grows rapidly and persistently, throughput decays materially over time, or an OOM/system-responsiveness failure occurs. |

The BF16 target-only 4-token smoke loaded and generated successfully, but added
about 995 MiB of swap and temporarily reduced reported free memory to 21%.
Without a paired-draft stability run this is **WARN**, not a binary proof of
infeasibility. The planned BF16 + 0.6B draft experiment remains deferred because
the observed headroom is narrow; the 8-bit precision-rescue target is the next
controlled configuration.

The 8-bit MLX target-only smoke passed the composite memory gate with no swap
growth and 59% free memory after execution. The later llama.cpp Metal Q8_0
target-plus-draft correctness checks completed without throttling. Their
per-run classifications were WARN for `k=2` (+8.87 MiB swap) and `k=4`
(+41.00 MiB), then PASS for `k=6` (zero swap growth). These short deltas are
not evidence of sustained growth; a longer performance run must still check
pressure and throughput over time.
