# M4 Unified-Memory Feasibility

## Method

These are planning estimates, not measurements on an M4. Local Qwen3 configs give BF16 KV bytes/token as `2 × layers × KV heads × head_dim × 2 bytes`: 144 KiB for 8B, 160 KiB for 14B, and 112 KiB for 0.6B. Native speculation keeps target and draft caches, so the pair is budgeted together. Four-bit weight ranges include quantization metadata; runtime buffers and macOS use remain separate.

| Pair / context | 4-bit weights (estimate) | Pair BF16 KV | Runtime/buffer allowance | Assessment on 24 GB |
|---|---:|---:|---:|---|
| 8B + 0.6B, 2k | 5.0--6.0 GiB | 0.50 GiB | 2--4 GiB | Comfortable |
| 8B + 0.6B, 8k | 5.0--6.0 GiB | 2.00 GiB | 2--4 GiB | Feasible with substantial system headroom |
| 14B + 0.6B, 2k | 8.0--9.5 GiB | 0.53 GiB | 3--5 GiB | Feasible canary, not automatically safe |
| 14B + 0.6B, 8k | 8.0--9.5 GiB | 2.13 GiB | 3--5 GiB | Tight after macOS/apps; feasibility-only |

For the required 12-question run with a 64-token output cap, 8B+0.6B 4-bit should be the only initial pair. Keep at least 6 GiB visibly available for macOS and transient allocations, close memory-heavy applications, and reject any run that creates sustained swap growth or yellow/red memory pressure. “24 GB unified” is not a 24 GB model budget.

The 14B pair is allowed only after the 8B protocol is complete and only as a separate load/one-prompt canary. It is not part of the minimum matrix. No 20B model is authorized.

## What unified memory changes

Unified memory can remove an explicit CPU-to-discrete-GPU payload copy and makes model coexistence more flexible. It does **not** remove command submission, producer/consumer synchronization, cache coherency or residency costs, KV bookkeeping, target verification, kernel launch overhead, or contention when draft and target use the same GPU. It may therefore improve the Windows cross-memory component without guaranteeing speculative speedup.

## Qualification measurements

Record MLX active/peak allocator bytes before load, after both models load, after warm-up and after each run; also record `vm_stat`, `memory_pressure`, process RSS and swap usage. The formal pass condition is no increasing swap during the timed region and normal/green memory pressure. Allocator peak is not total unified-memory use and must be labeled separately.

