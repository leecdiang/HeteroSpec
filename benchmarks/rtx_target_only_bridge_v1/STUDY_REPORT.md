# RTX matched-configuration target-only bridge

**SUPPORTED_ON_EXPOSED_COHORT**. All **171/171** fresh formal runs passed independent raw verification. Engineering: 12; additional diagnostic generations: 0; failed attempts: 0; retries: 0; formal restarts: 0.

This study is based on PR #54 at `16aeada781c475c9641e09c90e93fb0a0e136c34` and is stacked on `codex/manuscript-intervention-reconstruction-v010`. The pre-formal implementation/protocol freeze is `564398820b747674e6ba1bc131e6738e5fda1459`. PR #53/#54, all inherited evidence, and the manuscript are unchanged.

## Question and execution

Does ordinary draft-free target-only U2 reproduce native intervention N1 under matched current RTX settings, and how does its agreement differ from N0? The retrospective lead was recomputed: historical U2=N0 51/57; U2=N1 57/57. Historical U2 actually used 12 threads. The present comparison uses 24 generation and 24 batch threads, including explicit supported draft settings on N paths. This is an exposed cohort, not a discovery on unseen tasks or a thread-causality experiment.

All 19 prescribed HumanEval tasks ran in three conditions and three fresh-process repetitions. Condition orders were N0/N1/U2, N1/U2/N0, U2/N0/N1. One GPU queue, no warmup, no process/KV reuse; the OS file cache was not flushed. Exact argv, effective settings and input bindings are retained per run.

N0 uses the existing qualified native UB2 prefill/draft, k=2 and UB2→UB2 sham. N1 preserves the same first-pending sample/accept and handoff while changing target continuation to UB1. U2 is the released ordinary CLI with global UB2, its own initialization/prefill/continuation, and no draft model, transplant, proposal tape or supplied answer. Target-only caller grouping was observed rather than changed to force agreement.

Hardware: RTX 5070 Ti Laptop GPU, 12,227 MiB, UUID `GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd`; driver 616.92; Windows 11 build 26300; Python 3.11.9. Target Qwen3-8B-Q8_0 and draft Qwen3-0.6B-Q8_0 hashes match the specified assets. Runtime b10839 is pinned to `0cae43063cf15170e91a2ff4d034da0ecef4a1b2`. All 54 released runtime files and the prior native frontend match their hashes; post-execution readback passes all 80 asset bindings. Raw logs confirm CUDA0 target 37/37 layers and N draft 29/29, 24-thread numerical pools, ctx=4096, batch=2048, F16 KV and FA off. HTTP housekeeping uses 23 threads and is separate.

Twelve local engineering runs passed independent capture/input/config/handoff checks on /15, /25, /18 and /31. Unchanged instrumentation reuses its prior qualified 120-array/30-sham evidence; that larger campaign was not rerun. Seven meaningful negative verifier tests passed. U2=N1 and N0=N1 were never qualification gates.

## Fresh results

| Pair | Full arrays | EOS/limit reason | Full stop boundary | Joint equality | All three equal task units |
|---|---:|---:|---:|---:|---:|
| U2/N1 | 57/57 | 57/57 | 57/57 | 57/57 | 19/19 |
| U2/N0 | 51/57 | 57/57 | 54/57 | 51/57 | 17/19 |
| N0/N1 | 51/57 | 57/57 | 54/57 | 51/57 | 17/19 |

N0, N1 and U2 each have 19/19 stable tasks across all three repetitions. Tasks are the scientific units; the 57 pairs are repeated observations, not independent samples. Full arrays include the terminal EOG ID, or all 128 committed IDs at the cap. The frozen endpoint field records EOS/limit reason. A supplementary strict stop boundary compares (committed length, reason, terminal token ID), so /15's differing lengths are explicitly visible as three unequal boundaries. BOUNDARY_COMPARISONS.json reparses all 171 raw records for this clarification; the frozen primary reason metric, numerical execution and outcomes remain unchanged.

Changed N0/N1 tasks: HumanEval/25, HumanEval/15. Both changed tasks agree with U2 in all three repetitions (6/6 observations). The other 17 tasks are output no-ops. Predicting N1=N0 achieves 17/19 tasks and 51/57 observations, compared with U2's 19/19 and 57/57. These finite exposed-case differences do not establish a general predictive method. COMPARISONS.json gives every length, zero-based first divergence and endpoint; unequal-length difference count is positional substitutions over the common length plus the absolute length difference, divided by max length for its fraction.

| Case | N0 / N1 / U2 lengths | First N0/N1 divergence | Old UB1 reference relationship |
|---|---|---|---|
| /15 | 25 / 28 / 28 | index 15: 9147 → 4199 | U2=N1 restores reference; N0 differs |
| /25 | 75 / 75 / 75 | index 4: 1406 → 271 | N0 matches reference; U2=N1 moves away |
| /18 | 69 / 69 / 69 | none | all three still differ from reference |

There are no new U2/N1 mismatches or instabilities. Fresh N0 and N1 each match their pinned historical counterpart in 57/57 arrays/endpoints. Fresh U2 at 24 threads matches historical U2 at 12 threads in 57/57; this is an observational bridge. Old-reference agreement remains 51/57 for each current condition. Reproduction fidelity does not erase /25's failed restoration objective.

The runtime logs contain zero committed IDs beyond the contract endpoint. The traces additionally retain 60 uncommitted target samples beyond the committed prefix in 60 native records; full sampled lists, decisions and tails remain inspectable and are excluded from equality. No raw tail was silently discarded.

## Diagnosis and decision

Existing formal captures suffice for the bounded exploratory /15, /25, /18, /31 selection; no extra generations were needed. For these cases, N0/N1 first-pending source KV and full pending logits are byte-equal. At /15 and /25, the first divergent target decision flips the top candidate while the native caller still contains three tokens. Captured continuation occupied tokens are [1,2] for N0 and [1] for N1; U2 post-first-commit batch dumps have length 1 despite UB2 capacity. U2 graph tensors and live KV/logits are unobserved. These observations are consistent with a caller/occupied-shape numerical explanation, but do not uniquely prove causation or equal later prefix state. DIAGNOSTICS.md preserves exact scores and alignment limits.

Ordinary U2 is sufficient to reproduce N1 on this matched exposed cohort. This weakens the novelty of the complex RTX P/R predictor for that objective. The result is consistent with ordinary deterministic greedy re-execution using the shared numerical backend; it does not rule out that simple explanation or establish an equivalence theorem. **Stop pursuing a new-method novelty claim or more 57/57 checks through this route.** A later study would need a concrete useful decision and a frozen construction rule tested against ordinary target-only and the no-op baseline on new tasks/configurations. No demonstrated utility here justifies launching that study now.

No speedup, energy benefit, actual VRAM reduction, functional accuracy, reference restoration in general, bitwise state equality or cross-platform generality is claimed.

## Evidence and limits

The independent CPU verifier imports no controller/capture/comparison helper, reparses all 171 selected raw records, verifies 1,596 per-run file bindings, recomputes all tables and reparses 114 restored historical native logs. A separate settings audit covers 183 engineering/formal records and 122 handoffs. Hashes establish supplied content consistency, not independent authentication of omitted weights/runtime binaries, physical execution or absolute time. Opaque sampler state and live U2 internals remain unavailable.

Compact arrays, task tables, protocol/input/asset/freeze bindings and reports are reviewable directly in Git. Full raw evidence uses Git-backed CAS parts under `artifacts/rtx_target_only_bridge_v1`. REPRODUCIBILITY.md gives restoration commands. Final archive/readback/delivery receipts are later Git objects, outside the archive snapshot they describe; see their exact coverage before claiming delivery complete.
