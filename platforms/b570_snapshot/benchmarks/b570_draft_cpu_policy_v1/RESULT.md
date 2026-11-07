# B570 draft CPU parallelism: exact-reference controlled result

**NO_ESTABLISHED_PRACTICAL_PANEL_BENEFIT**

One factor changed: draft context CPU thread parameters8 ->1. Target stays8; runtime DLLs, GPU kernels, weights, q1 prefill, QB layout, sampling and state protocol are unchanged. See SOURCE_AUDIT.md for the source and OpenMP build evidence. A disposable ggml pool object is not proof that OS worker threads are recreated; no persistent-threadpool variant was run.

Preregistered before GPU execution in `8c0d082debf279c8c23bccb12088fcee19ff37e8`, with qualification and estimator committed before timing in `e126060f85de0c42d9846c780fc5c158e5ccbb32`. Scientific parent is PR134 `51febaddcf49bb18565e568cf964a6e5c78876c9`.

## Reference and measurement

All four fixed inputs pass. **346 candidate target/draft full-logit vectors match the original PR134 QB files byte for byte**, including rejected verification rows. Complete IDs/EOG/length/terminal/stop and speculative cycle traces remain identical. No replacement reference or inherited performance PASS.

Four qualification requests precede four independent timing processes. Each timing process runs four registered warmups and16 measured requests: **16 warmups and64 measured requests**. Every measured endpoint/state trace passes. BASE_A and BASE_B are identical QB threads8 implementations. DRAFT1 is the candidate; R is target-only8 with draft weights resident.

| Input | DRAFT1 service reduction vs dual-BASE | DRAFT1 / R service | BASE_A / BASE_B imbalance |
|---|---:|---:|---:|
| HumanEval/38 | +0.003% | 2.5971 | -0.111% |
| HumanEval/65 | -1.022% | 2.6819 | +0.004% |
| HumanEval/115 | +0.042% | 2.6330 | -0.793% |
| HumanEval/127 | -0.625% | 2.6209 | -0.067% |

Equal-input geometric-mean DRAFT1/dual-BASE service ratio: **1.00399350**; reduction **-0.3993%**.
Request-only ratio: **1.00401272**.
DRAFT1/target-only service ratio: **2.63305634**.
Largest input-aggregate A/A imbalance: **0.7931%**; registered practical screen: **2.0000%**.
Per-session panel ratios: `[0.9988026049601184, 1.0071420418756973, 1.0105671746425091, 0.9995120215150611]`.

Primary analysis uses paired service ratios, equal input weighting and all16 blocks. No outlier removal or stopping for significance. Four fixed exposed inputs, one model pair/machine/date: descriptive finite-panel estimates, no population confidence interval or equivalence claim.

## Locating costs

Registered synchronized host phase fields give descriptive arithmetic means:

- Baseline draft prefill: **9.287213s**; DRAFT1 draft prefill: **9.306119s**, reduction **-0.204%**.
- DRAFT1 total draft prefill/decode: **12.462260s**.
- Baseline target verification: **0.939463s**; DRAFT1 target verification: **0.950916s**.

The intervention changes CPU backend parallelism policy, not the mathematical/GPU mapping. A performance effect can support that policy as a contributor in this environment; it cannot isolate OS thread creation, OpenMP runtime internals, CPU/GPU contention or a physical GPU bottleneck by itself. The scope of thread count1 is draft CPU computation, not a native-process thread cap.

Subsequent source inspection found that GET_ROWS/SET_ROWS already request one task and the graph planner clamps worker count to the maximum task count. Changing the context parameter therefore need not change actual worker count in the embedding-only CPU subgraph. The experiment tests a parameter policy; it does not establish that fewer workers actually ran. This weakens the original overhead hypothesis and is retained alongside the negative measurement.

**Disposition:** Do not promote draft CPU1 as a performance improvement; retain the original policy and this negative controlled result.

## Full cost boundary

Primary service includes fresh context creation/graph reservation, prefills, generation, host logits/sampling, state updates, synchronization and context destruction. Shared model load is separately recorded. No node observer or raw-vector writes in timed requests; comparisons/file output follow the timer. Request-only and phase costs remain secondary.

Token-by-token prefill remains unchanged. Warmup uses the old16-token prompt; it is separately recorded and checked. Driver cache coldness, all-shape cache residency and background-machine exclusivity are not established. This is post-registered-warmup fresh-context service, not cold boot or a proven production software ceiling.

## Paper implication

This study refines PR134's software baseline through an explicit one-factor counterfactual. Preserve PR134's original evidence and the current result separately. Neither numerical admission nor reduced thread count alone is a speedup claim. Draft economics must still be assessed against contemporary R, not historical timings. Do not infer a hardware accelerator opportunity from the expensive draft phase alone.

## Evidence

Candidate346 raw vectors remain locally archived with full hashes and sizes. Compact archive includes all native result/progress/geometry JSON, logs and receipts. This is local full-byte recheck, not external raw-data certification.

Conservative whole-parent charge: **1316.0326372s**; preserved prior1817.8040152s; all-history **3133.8366524s**. No actor, RTL, CPU8 expansion or merge.
