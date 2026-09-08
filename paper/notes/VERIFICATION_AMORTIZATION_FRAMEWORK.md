# Verification Amortization Framework

## Purpose

This note defines one cost vocabulary for the completed M4 and Windows studies. It separates an algorithm's nominal batching opportunity from the execution path that remains admissible after correctness is enforced.

## Exact verification amortization factor

For target context depth `n` and proposal width `k`, define

`V_k(n) = T_target_verify(k, n) / T_target_decode(1, n)`.

`V_k` is the **exact verification amortization factor** only when the measured verification path passes the study's output-equivalence gate. Values near one mean that a `k`-token causal block can be checked for approximately the cost of one autoregressive target step. Values near `k` mean that verification is effectively serialized.

Define the correctness-constrained factor

`V_k^exact(n) = min V_k(n, e)` over execution paths `e` that pass the frozen correctness gate.

This definition prevents a fast but output-divergent kernel path from being counted as usable amortization. If no tested path is exact, `V_k^exact` is unavailable, not the minimum timing observed.

The tracked kernel-level proxies are:

| Platform/backend | Context | Path | Correctness status | `V_2` |
|---|---:|---|---|---:|
| M4 llama.cpp/Metal | 512 | synchronized causal batch | exact in the surrounding llama.cpp gate | 1.022 |
| M4 llama.cpp/Metal | 2,048 | synchronized causal batch | exact in the surrounding llama.cpp gate | 1.076 |
| M4 llama.cpp/Metal | 8,192 | synchronized causal batch | exact in the surrounding llama.cpp gate | 1.032 |
| Windows llama.cpp/CUDA | 0 | batched `ubatch=2` | correctness-blocked on the frozen HumanEval replication | 1.009 |
| Windows llama.cpp/CUDA | 256 | batched `ubatch=2` | correctness-blocked on the frozen HumanEval replication | 0.983 |
| Windows llama.cpp/CUDA | 0 | serialized `ubatch=1` | exact control | 2.431 |
| Windows llama.cpp/CUDA | 256 | serialized `ubatch=1` | exact control | 2.137 |

These ratios are target-forward microbenchmarks, not end-to-end decompositions. The M4 table uses prefix lengths 512/2,048/8,192; the Windows table uses depths 0/256, so rows should not be treated as matched hardware measurements.

## Unified round cost model

For one speculative round, let:

- `T_b`: baseline target time per output token;
- `T_d(k)`: time to produce `k` draft candidates, including any repeated draft prefill;
- `T_v(k,e)`: target verification time on execution path `e`;
- `T_x(e)`: transfer, synchronization, scheduling, Python/KV bookkeeping, correction, and other residual cost;
- `C`: output tokens committed by the round under the actual acceptance sequence.

Then

`T_spec/token = [T_d(k) + T_v(k,e) + T_x(e)] / C`

and

`speedup = T_b * C / [T_d(k) + V_k(e) * T_b + T_x(e)]`.

The break-even condition is

`C > T_d(k)/T_b + V_k(e) + T_x(e)/T_b`.

This equation explains why acceptance rate by itself is insufficient. Acceptance changes `C`, but profitability also requires small normalized draft cost, a low **correctness-admissible** `V_k`, and a small residual. Repository fields named `accepted_per_round` count accepted draft tokens as parsed from llama.cpp and are not silently substituted for `C`; a correction/bonus token and end effects depend on the runtime. End-to-end observed speedup remains authoritative.

## Correctness-constrained execution path

The admissible path is selected in this order:

1. Freeze model files, prompt set, greedy settings, proposal width, and runtime/build.
2. Compare paired baseline and speculative output token IDs.
3. Exclude a failing execution path from performance claims, even if it is faster.
4. Measure the cheapest tested exact alternative and report its `V_k^exact`.
5. Evaluate end-to-end cost and energy without mixing sensor boundaries.

On Windows, step 3 excludes batched `ubatch=2`; `ubatch=1` restores exactness but raises `V_2^exact` above two. On M4, the tested llama.cpp/Metal path retains exact output while keeping `V_2` near one. This is the central cross-platform constraint.

## What the framework does not claim

- A kernel-level `V_k` does not determine speedup without draft, residual, and realized commit behavior.
- Token equality does not establish HumanEval functional correctness.
- The data do not isolate unified memory, GPU architecture, a particular CUDA kernel, or quantization as a single cause.
- The Windows numerical capture identifies a batch-shape-dependent argmax flip on one stable case; it does not prove a universal CUDA failure.

Primary sources within the repository are `reports/m4/M4_SPECULATION_MECHANISM_DIAGNOSIS.md`, `reports/5070ti/WINDOWS_VERIFICATION_MECHANISM_CONTROLS.md`, and `reports/5070ti/CUDA_DIVERGENCE_NUMERICAL_DIAGNOSIS.md`.
