# Verification Amortization Framework

## Purpose

This note defines the audited cost vocabulary for the completed M4, RTX 5070 Ti Laptop/CUDA, Arc B570/Vulkan, and Core Ultra X7 358H studies. The central rule is to keep three concepts separate:

1. **realized end-to-end round cost**;
2. **target-forward microbenchmark batching opportunity**;
3. **correctness admissibility**.

A fast microbenchmark is not automatically a usable optimization path, and a target-forward PP2/PP1 ratio is not automatically the complete target-side cost of a speculative round.

## 1. Realized speculative-round accounting

For a speculative round, let:

- `T_b`: matched target-only baseline cost per committed output token;
- `T_d(real)`: realized draft-subsystem cost through the actual runtime state interface;
- `T_target,round(real)`: complete realized target-side work for the round, including proposal verification and any correction/bonus target work that lies inside the runtime's round semantics;
- `T_x`: residual transfer, synchronization, scheduling, orchestration, bookkeeping, or other cost not already included;
- `C`: **all committed output tokens per speculative round**, including correction/bonus behavior.

Then, at one consistent aggregation level,

`speedup = T_b * C / [T_d(real) + T_target,round(real) + T_x]`.

Normalize by `T_b`:

- `D_real = T_d(real) / T_b`
- `R_target = T_target,round(real) / T_b`
- `X = T_x / T_b`

so

`speedup = C / [D_real + R_target + X]`

and break-even is

`C > D_real + R_target + X`.

This is an accounting identity when every term is measured under the same boundary. It is not a claim that every platform exposes every term separately.

## 2. Target-forward microbenchmark proxy

For target context/depth `n`, proposal width `k`, and execution path `e`, define

`V_k^micro(n,e) = T_target_forward(k,n,e) / T_target_decode(1,n)`.

This measures whether the backend can evaluate a width-`k` causal block for near the cost of one target decode. It is a **mechanism proxy**, not an end-to-end decomposition.

Tracked values:

| Platform/backend | Context/depth | Path | Workload correctness status | `V_2^micro` |
|---|---:|---|---|---:|
| M4 / Metal | 512 | synchronized causal batch | exact in tested surrounding gate | 1.022 |
| M4 / Metal | 2,048 | synchronized causal batch | exact in tested surrounding gate | 1.076 |
| M4 / Metal | 8,192 | synchronized causal batch | exact in tested surrounding gate | 1.032 |
| RTX 5070 Ti Laptop / CUDA | 0 | batched `ubatch=2` | correctness-blocked on frozen HumanEval replication | 1.009 |
| RTX 5070 Ti Laptop / CUDA | 256 | batched `ubatch=2` | correctness-blocked | 0.983 |
| RTX 5070 Ti Laptop / CUDA | 0 | serialized `ubatch=1` | exact control | 2.431 |
| RTX 5070 Ti Laptop / CUDA | 256 | serialized `ubatch=1` | exact control | 2.137 |
| Arc B570 / Vulkan | 512 | serialized `ubatch=1` | **not globally exact** on HumanEval30 | 1.983 |
| Arc B570 / Vulkan | 2,048 | serialized `ubatch=1` | **not globally exact** on HumanEval30 | 1.992 |

Paper-facing B570 terminology is `V2_serialized`, not `V2_exact`.

### Why `V_k^micro` is not `R_target`

The microbenchmark normally measures a target-forward block. A realized speculative round may additionally require target correction/bonus decode, initial-target behavior, rollback/state actions, or other target work. Therefore:

- use `V_k^micro` to diagnose batching opportunity;
- use `R_target` for complete end-to-end round accounting when it is measured;
- never silently substitute one for the other.

## 3. Correctness filtering

Correctness is a gate on optimization claims, not a timing adjustment.

1. Freeze model/runtime/workload/greedy settings.
2. Compare generated target-model token IDs under the frozen normalization.
3. A path that fails the workload-level token-exact contract is excluded from correctness-admissible performance claims.
4. Serialization is not synonymous with exactness; B570 demonstrates this directly.
5. HumanEval token equality is not functional pass@k.

On RTX/CUDA, the cheap batched path is physically real but fails the exactness gate; the tested exact control has much larger `V_2^micro`. On B570, even the serialized candidate remains only 60/90 exact pairs, so there is no globally admissible optimization result.

## 4. 358H: direct realized accounting

358H provides the cleanest measured realization because the formal runner records draft time, complete target-verification time, residual, and committed progress `C`.

Using campaign arithmetic totals:

| Path | `C` | `D_real` | `R_target` | `X` | Aggregate ratio `C/(D+R+X)` |
|---|---:|---:|---:|---:|---:|
| CPU draft | 2.4631 | 0.4304 | 2.9767 | 0.00124 | 0.7227 |
| NPU draft | 2.4584 | 4.1251 | 2.9435 | 0.00130 | 0.3477 |

These are ratio-of-aggregate-cost identities. They are not expected to equal the preregistered prompt-level geometric-mean headline speedups (0.734x and 0.352x), because the estimands differ.

The NPU path directly demonstrates why isolated draft throughput is not `T_d(real)`: each OpenVINO proposal call runs `LLMPipeline.generate` on the entire committed prefix, so replay/reconstruction plus proposal dominates the realized NPU draft interval.

## 5. Committed progress versus acceptance

Acceptance changes profitability only through the work it ultimately helps commit.

- 358H directly measures `C`: 2.4631 CPU and 2.4584 NPU.
- Historical M4/RTX `accepted_per_round` counts accepted **draft** tokens/round and is not `C`.
- M4 HumanEval permits a boundary-affected reconstructed effective progress `output_tokens_runtime / verification_rounds`: approximately 2.826 fixed-k2, 2.676 at p_min=.8, and 2.606 at p_min=.9.
- Because initial/final effects vary, those M4 values remain diagnostic and are not promoted to the same evidentiary status as 358H's direct round traces.

This also shows why a higher acceptance rate does not necessarily imply larger realized committed progress under a different proposal policy.

## 6. Platform interpretation

- **M4:** cheap exact width-two target-forward batching creates an opportunity; profitability is workload-conditioned. Representative 24Q remains negative while preregistered HumanEval fixed-k2 is positive.
- **RTX 5070 Ti Laptop:** a cheap raw batched target-forward path exists, but the frozen token-exact gate excludes it. The tested exact serialized control is decisively negative.
- **B570:** serialization raises target-forward cost and still does not establish universal token exactness; all fallback timing/energy remains diagnostic.
- **358H CPU:** exact but target-side work dominates.
- **358H NPU:** exact but full-prefix replay+proposal dominates the realized draft subsystem.

## 7. What this framework does not claim

- It does not identify unified memory as the cause of the M4 result.
- It does not claim CUDA or Vulkan is generally numerically incorrect.
- It does not claim NPUs are intrinsically unsuitable for speculative decoding.
- It does not equate isolated accelerator tok/s or TOPS with realized draft cost.
- It does not force unmeasured replay/rollback/transfer terms into platforms that did not expose them.
- It does not use B570 diagnostic performance as an admissible optimization result.
- It does not compare prompt-bootstrap CIs as if they captured full session/thermal/runtime-state uncertainty.

Primary evidence remains the frozen platform reports, preregistrations, scripts, and archived results referenced by `paper/mlsys2027/PAPER_FRAMEWORK_HANDOFF.md`.
