# Cross-Platform Mechanism

## Status and scope

This note is a living mechanism synthesis for the closed M4, RTX 5070 Ti Laptop, Arc B570, and Core Ultra X7 358H studies. It must be read together with `paper/mlsys2027/PAPER_FRAMEWORK_HANDOFF.md` and `paper/notes/VERIFICATION_AMORTIZATION_FRAMEWORK.md`.

The central audit rule is to keep three quantities separate:

1. **correctness admissibility** of an execution path;
2. **target-forward batching opportunity**, measured by `V_k^micro`;
3. **complete realized speculative-round cost**, including `T_d(real)`, complete target-side `R_target`, residual `X`, and committed progress `C`.

A cheap `V_k^micro` is not automatically a correctness-admissible path, and it is not automatically the complete target-side cost of an end-to-end speculative round.

## Joint result

The completed studies expose four regimes under the frozen configurations:

- **profitable + exact:** M4 / llama.cpp Metal on the separately preregistered HumanEval code-conditioned fixed-k2 workload;
- **exact but unprofitable:** M4 representative 24Q, RTX serialized HumanEval controls, and 358H CPU/NPU;
- **physically fast but correctness-inadmissible:** RTX CUDA batched `ubatch=2` and the B570 fast Vulkan path;
- **state-interface bound:** 358H NPU, where the draft device is competitive in isolated throughput but the actual OpenVINO adapter reconstructs the full committed prefix on every proposal call.

The cross-platform lesson is therefore not “high acceptance is insufficient” by itself. The stronger systems observation is that **the execution path available after correctness filtering and the realized state interface determine which physical batching/draft opportunities remain usable end to end**.

## Accounting vocabulary

For realized speculative-round accounting:

```text
speedup = T_b * C /
          [T_d(real) + T_target,round(real) + T_x]

        = C / [D_real + R_target + X]
```

where `C` is all committed output tokens per speculative round. Historical M4/RTX fields named `accepted_per_round` count accepted **draft** tokens and are not the same metric.

Separately, for a target-forward microbenchmark:

```text
V_k^micro(n,e) = T_target_forward(k,n,e) / T_target_decode(1,n)
```

`V_k^micro` diagnoses target batching efficiency on path `e`; it does not include every correction/bonus/state action of a realized round unless the measurement boundary explicitly proves that it does.

## Evidence chain

### M4 / llama.cpp Metal

1. The final llama.cpp Q8_0 correctness path is distinct from earlier MLX-LM precision paths that failed strict exactness.
2. The tested llama.cpp Metal `k=2/4/6` correctness cells were exact.
3. At `k=2`, synchronized target-forward `V_2^micro` measured approximately **1.022–1.076** across tested prefix lengths. This demonstrates a physically cheap width-two target-forward opportunity; it is not a full realized `R_target` measurement.
4. Keeping an idle draft resident added only about 0.65% to the bounded target-only control, arguing against simple model residency as the main loss in that control.
5. The frozen representative Spec-Bench 24Q confirmation is negative: **0.842x [0.809, 0.877]**, 72/72 exact, 1/24 prompts faster, with worse package J/token.
6. The separately preregistered HumanEval30 fixed-k2 study is positive: **1.387x [1.351, 1.422]**, 30/30 prompts faster, 90/90 exact, mean acceptance about 90.1%.
7. Fixed-k2 HumanEval package-efficiency ratio is 1.013x [0.990, 1.034], so the primary energy result is **neutral within uncertainty**, not a statistically robust energy win.

Safe mechanism interpretation: an exact cheap width-two target-forward path exists in the tested Metal runtime, and one separately preregistered code-conditioned workload realizes a profitable regime while the representative 24Q workload does not. The repository does not directly measure a common cross-platform `C` for historical M4 runs, so do not turn “code predictability supplies enough committed work” into a causal claim. Unified memory is compatible with the observed implementation but is not isolated from Metal kernels, scheduling, state handling, or other runtime effects.

### RTX 5070 Ti Laptop / llama.cpp CUDA

1. The matched HumanEval replication's default batched `ubatch=2` path fails the hard token-exact gate on a stable frozen case.
2. HumanEval/106 reproduces the same first divergence in 3/3 independent processes at the same captured output position: baseline and serialized execution choose token 2790; batched execution chooses 2629.
3. At the shared prefix, `score(2790)-score(2629)` changes from **+0.080948** in baseline/serialized execution to **-0.126457** in batched execution. This supports a batch-shape-dependent numerical argmax flip; it does not identify a particular CUDA kernel or establish a universal CUDA defect.
4. The physically cheap batched target-forward path has `V_2^micro≈1.009` at depth 0 and `≈0.983` at depth 256.
5. The tested exact serialized `ubatch=1` control has `V_2^micro≈2.431` and `≈2.137` at the same depths.
6. Under serialized exact controls, HumanEval CPU→RTX reaches only **0.404x [0.390, 0.418]** and RTX→RTX only **0.650x [0.629, 0.673]**, despite >91% weighted acceptance and 90/90 exact pairs each.
7. Same-GPU placement recovers a substantial fraction of the heterogeneous loss, so CPU↔GPU transfer/synchronization is material, but remaining below 1.0 shows it is not the sole cause. Earlier custom/native controls likewise show that runtime integration and state reuse change realized cost.

Safe mechanism interpretation: the frozen CUDA stack exposes a physically cheap batched target-forward path, but the strict token-equivalence contract excludes that path. The tested correctness-admissible control is much more expensive at the target-forward level and remains end-to-end negative once draft/runtime costs are included. `V_2^micro` is mechanism evidence, not a claim that complete `R_target` equals 2.14–2.43.

### Arc B570 / llama.cpp Vulkan

1. Formal preregistration v2 stops after the six-prompt correctness gate fails; no formal V2/performance claim is rescued from that run.
2. A later explicitly diagnostic HumanEval30 extension records **45/90 exact pairs** for the fast path.
3. The single frozen serialized `n_ubatch=1` fallback improves exactness but remains non-universal: **60/90 exact pairs, 20/30 wholly exact prompts**.
4. The serialized target-forward proxy is `V_2^micro≈1.983` at context 512 and `≈1.992` at 2048.
5. Overall serialized performance remains diagnostic: **0.3087x [0.2927, 0.3246]**, 0/30 prompts faster. Arc-board efficiency ratio is **0.3023x [0.2846, 0.3202]** within the board-only sensor boundary.

Safe mechanism interpretation: **serialization is an execution property, not an exactness guarantee**. Historical result objects/report fields may retain the name `V2_exact` for provenance, but paper-facing terminology is serialized `V_2^micro` / `V2_serialized`. No tested B570 path supports a correctness-admissible optimization result.

### Core Ultra X7 358H / Vulkan target + OpenVINO draft

1. CPU and NPU paths use the same frozen Qwen3-0.6B OpenVINO draft semantics and a shared explicit Vulkan0 Qwen3-8B target.
2. Both pass the frozen Stage-A gate (18/18 exact) and full HumanEval30 token-equivalence comparison (90/90 exact per draft device).
3. Acceptance remains high at 75.31% CPU and 75.13% NPU, with directly measured committed progress **C=2.463** and **C=2.458** output tokens/round.
4. Nevertheless, post-prefill decode speedup is **0.734x [0.693, 0.771]** CPU and **0.352x [0.333, 0.369]** NPU; neither is faster on any of the 30 prompts.
5. CPU speculative time is 12.63% replay+proposal, 87.34% complete measured target-side work, and about 0.04% residual.
6. NPU speculative time is 58.35% replay+proposal, 41.63% target-side work, and about 0.02% residual.
7. Runner inspection shows every OpenVINO proposal call passes the **entire committed prefix** to `LLMPipeline.generate`; replay/reconstruction plus proposal is therefore genuinely inside realized `T_d(real)`.
8. The target runner's timed verification region includes proposal evaluation, invalid-candidate KV rollback when needed, and correction/bonus target decode. 358H therefore provides the cleanest direct realization of complete `R_target` among the four campaigns.

Using ratio-of-total-times accounting:

| Path | `C` | `D_real` | `R_target` | `X` | `C/(D+R+X)` |
|---|---:|---:|---:|---:|---:|
| CPU draft | 2.4631 | 0.4304 | 2.9767 | 0.00124 | 0.7227 |
| NPU draft | 2.4584 | 4.1251 | 2.9435 | 0.00130 | 0.3477 |

These aggregate identities equal the corresponding aggregate baseline/speculative time ratios; they are not expected to equal the preregistered prompt-level geometric-mean headline speedups 0.734x / 0.352x.

Safe mechanism interpretation: isolated NPU throughput is not the realized draft-subsystem cost under the qualified adapter. The negative NPU result is a state-interface result under the current OpenVINO path, not evidence that NPU compute is intrinsically too slow or unsuitable for speculative decoding.

## Correctness-constrained mechanism map

| Regime / path | Cheap target-forward batching? | Passes frozen workload-level correctness? | End-to-end status | Mechanism use |
|---|---|---|---|---|
| M4 Metal k2 | Yes, `V_2^micro≈1.02–1.08` | Yes in tested final cells | HumanEval positive; 24Q negative | cheap exact batching opportunity + workload dependence |
| RTX CUDA batched ub2 | Yes, `≈0.98–1.01` | No on frozen replication | inadmissible | shows fastest physical path can be removed by correctness contract |
| RTX CUDA serialized ub1 | No, `≈2.14–2.43` | Yes in exact controls | negative | correctness-admissible control |
| B570 Vulkan fast | limited / context-dependent | No, 45/90 | diagnostic only | correctness-blocked |
| B570 serialized ub1 | `≈1.98–1.99` | No, 60/90 | diagnostic only | serialization does not guarantee exactness |
| 358H CPU | micro proxy not substituted for realized round cost | Yes, 90/90 | negative | complete target-side work dominates |
| 358H NPU | micro proxy not substituted for realized round cost | Yes, 90/90 | negative | realized full-prefix draft-state cost dominates |

This table is a mechanism map, not a hardware leaderboard. Context lengths, runtimes, kernels, quantization/execution, memory organization, and measurement boundaries differ.

## Claims safe for publication

- Under the study's strict greedy token-equivalence contract, correctness filtering can change which physically available verification path is admissible for a performance claim.
- A target-forward batching microbenchmark must not be silently substituted for complete realized target-side round cost.
- Isolated draft-device throughput can fail to predict realized draft-subsystem cost when the actual interface reconstructs state each round.
- The tested consumer systems occupy multiple regimes: profitable+exact, exact-but-negative, fast-but-inadmissible, and state-interface-bound.
- M4 profitability is workload-conditioned; the representative 24Q result remains negative.
- Transfer/synchronization is material on the RTX platform but does not solely explain its negative result.
- The cross-platform contrast changes multiple factors and cannot be attributed solely to unified memory, Metal, CUDA, Vulkan, OpenVINO, NPU hardware, or GPU architecture.

## Claims this note does not support

- “High acceptance is the new explanation of speculative-decoding performance.”
- “The accounting identity is a new speculative-decoding theory.”
- “M4 wins because of unified memory.”
- “CUDA is broken.”
- “Vulkan cannot preserve exactness.”
- “Serialized verification is exact by construction.”
- “NPU compute is too slow for speculative decoding.”
- “The 358H Phase-2 microbenchmark model predicted the final Phase-3 speedup.” Phase 2 was an eligibility/favorable-bound gate; Phase 3 measures realized costs omitted by the proxy.

## Preregistration deviation retained

The M4 HumanEval preregistration required a corrected synthetic ceiling after the primary and `p_min` conditions: conditional probabilities 0.6/0.7/0.8/0.9/0.95/1.0 mapped to unconditional llama.cpp rates `p,p^2`, five repetitions per level and baseline, 128 output tokens, and order seed 20260911. No tracked result artifact matches that design.

The existing `work/m4/llama_synthetic_crossover.json` predates the preregistration and uses different probabilities, rate mapping, repetition count, output length, and seed. It remains an earlier diagnostic only. The corrected ceiling is **not completed / unsupported by repository evidence** and must not be reconstructed from the exploratory run.
