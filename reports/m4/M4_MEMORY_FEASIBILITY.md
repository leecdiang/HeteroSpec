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

## Measured smoke values

| Run | Prompt tokens | MLX peak | Swap before | Swap after | Formal memory gate |
|---|---:|---:|---:|---:|---|
| 8B target-only, ID 291 | 400 | 4.718 GiB | 1,751.75 MiB | 1,780.44 MiB | FAIL: +28.69 MiB |
| 8B + 0.6B, ID 395, k=4 | 21 | 4.742 GiB | 1,487.81 MiB | 1,751.75 MiB | FAIL: +263.94 MiB |

The machine began the overall audit at zero swap, but model download/loading and the active desktop session caused macOS to allocate swap before the formal canaries. Memory pressure still reported about 49--50% free, and no runtime OOM occurred. This proves the pair can coexist and execute, but it does not satisfy the stricter no-swap-growth benchmark gate.

**Qwen3-8B target = UNSAFE for formal benchmark in the current session.**

**Qwen3-8B + 0.6B = UNSAFE for formal benchmark in the current session.**

This is an operational classification, not evidence that 24 GB is intrinsically insufficient. A future 12Q pilot may requalify after rebooting/closing memory-heavy applications, returning swap to zero, and confirming zero growth across repeated warm runs. MLX peak allocation is not total unified-memory use and remains labeled separately.

## Unified-memory interpretation

Unified memory can reduce physical device-to-device copies and model-coexistence friction. It does not eliminate kernel dispatch, synchronization, KV bookkeeping, cache trimming, Metal scheduling or contention when target and draft share the GPU. It therefore removes one architectural penalty without guaranteeing speculative speedup.

Qwen3-14B is estimate-only in this phase and was not downloaded or run.
