# B570: actively transfer the shared rules to the Qwen counterexamples

Read `PLAN.md`, `B570.json`, and `src/reference_batching/README.md` in this PR. Continue autonomously through ordinary engineering fixes and native execution in a fresh worktree/output root. The purpose is to repair the known Qwen producer–consumer failures with the same structural method used for Llama.

## What to deliver

The old PR163 Qwen adapter calls only the layout setter; `reference_q8` and `prefix_extent` stay off. Replace that compatibility-only coverage with real rule selection, actual triggers and a repaired original failing path.

1. Restore PR163's final candidate source (`5d1272dcb2e53b73e3e72db4c403361fbef7d6c4`, results at `10a70566ce01ab707dbdcc57d8270c1434088f07`). Stage a new tree with `src/reference_batching/integrate_llama_cpp.py --backend vulkan --source <restored-final-source> --out <fresh-candidate-source>` and compile the pinned Vulkan path.
2. Connect native extraction to the shared planner: actual tensor/head structure, weight/input types, scalar and batch activation quantization/dispatch, cache occupancy and per-row physical extent. Select the F32-activation batch path from those conditions when required. Apply the effective policy to the relevant producer and consumer calls and bind it to graph reuse. Preserve the existing native shape guards unless implementing and testing a supported extension.
3. Replay these exact PR152 fixtures against the unchanged original R and exact P1 construction:
   - `MATH500/test/prealgebra/1865.json`;
   - `MATH500/test/prealgebra/1804.json`;
   - `GSM8K/train/1184`.
   Keep their original prompts, cap, k, models and numerical contract. For the two MATH inputs, repair **P1+PQ/QB**; P4T+PQ/QB already passed and cannot substitute for that result. Use GSM1184 to check the producer condition, since its P4T natural C1 also diverges.
   Retain Qwen's original all-GPU target/draft placement, 8 threads, F16 KV and k1 verification; do not copy Llama's CPU-draft placement. The integrated confirmation/cost path may use a uniformly selected, reference-preserving native prefill policy fixed before outputs; never route between P1/P4T according to an input or its result.
4. Record the expected structural action before each diagnostic and the actual native action afterward. Show whether precision preservation, prefix splitting or another structurally justified condition fired. Enabling switches without a trigger is not a mechanism transfer. If the old failure remains, localize the first relevant same-state/operand divergence and implement the smallest reusable rule indicated by it. Do not automatically transplant the CUDA head-normalization placement hypothesis to Vulkan.
5. Use a focused factor reversal or replay to establish that the new condition accounts for the repaired Qwen failure. Recheck the known Llama boundary counterexample and one ordinary control after the common source changes. Reuse the old Llama evidence; do not restart its full audit or 24-input/864-measurement campaign.
6. Freeze the shared implementation and mapping, then qualify eight natural unseen Qwen3-8B inputs selected with the exact tokenizer and existing exposure index. Include boundary-near and ordinary lengths where the natural pool permits. Run genuine greedy R/M_PQ/M_QB/C_PQ/C_QB, preserving full committed vectors and matched transaction checks. No model-name routing, default-off success, changed P1/R, quantization substitution or hand-edited prompts.
7. Run one fixed cost panel: default three sessions × eight inputs × five arms, plus immediate same-arm warmups. Compare M_QB/M_PQ and C_QB/C_PQ within the same new runtime, report M_QB/C_QB and paths/R, retain placement and input contract, and report reference preparation/loading separately. For phase explanations, use a separate small diagnostic subset with prefill/decode/verification/repair clocks; keep the formal measurements clean.

If the historical executable has hard-coded input lists, add only an input/recording adapter around the same numerical call sequence and pinned libraries. Preserve the original executable and compare retained fixture vectors first. Report this adapter honestly; do not freeze a different numerical R for convenience.

## Completion

Deliver a result PR containing the shared/native implementation, compact structural-trigger table, all three retained-case outcomes, small frozen confirmation and complete fixed cost results. A negative timing result is complete evidence. If a specific operator remains unsupported, preserve its minimal counterexample and implementation requirement instead of starting unrelated models or an endless fresh-panel search.

Do not merge the manuscript or submit it externally. No additional platform is part of this work.

**一句话执行 prompt：** 继续本 PR 的 `benchmarks/reference_batching_transfer_20261103/B570_PROMPT.md`：让共享结构规则真正启用并修复原 Qwen P1 反例，保留原 R 和输入，按实际机制自主补齐实现，再完成小型未见确认与一次固定成本面板，提交结果 PR。
