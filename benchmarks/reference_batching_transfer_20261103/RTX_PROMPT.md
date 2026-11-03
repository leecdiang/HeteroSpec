# RTX: implement shared requirements and test predictive Qwen transfer

Read `PLAN.md`, `RTX.json`, and `src/reference_batching/README.md` in this PR. Continue autonomously through ordinary engineering fixes and execution. Use a fresh worktree and output root; retain the previous RTX results and original references.

## What to deliver

Complete a real shared-runtime integration and demonstrate that its rules are selected from Qwen3-8B/14B graph and backend structure. The previous combined-policy regressions are not enough: show that the actual prefix boundary and normalization placement rules fire, and that their predicted actions preserve the original reference.

1. Restore the final repaired source used by PR162 `e11d2b75d82422409ba2b701aa38c59f36acc50b` using its source binding. Stage a new tree with `src/reference_batching/integrate_llama_cpp.py --backend cuda --source <restored-final-source> --out <fresh-candidate-source>`. Compile against the pinned existing toolchain/libraries. Fix ordinary source-anchor/ABI/build integration problems in the new candidate without touching the historical tree.
2. Finish the native requirement extractor and call sites. Read actual Q/K normalization roles, head/tensor structure, scalar-reference backend preference, cache occupancy and physical extents. Feed actual structural requirements into the shared planner and cache identity. Do not leave arithmetic/dispatch IDs at defaults or leave the projection/placement helper unused while calling the result an automatic policy.
3. Before each focused diagnostic, write its expected grouping or placement action. Include an actual Qwen boundary split and a nearby non-boundary case for each family, plus the original Qwen14B failures repaired by PR159. Query-width and head differences must come from the graphs. Log actual native selected actions and graph-reuse identity; a compiled rule that never fires counts as enabled compatibility only.
4. Use the existing same-state/operand tooling if a structural expectation fails. Retain the original R, model bytes, numerical paths and failed examples. Repair the shared rule from the actual divergence; no model-name, prompt, output-position or answer exceptions. Recheck the old Llama boundary counterexample and one non-boundary control once after integration.
5. Freeze the implementation, then select four natural unseen inputs per Qwen family. Use the existing exact tokenizer and exposure index, with both boundary-near and ordinary lengths. No padding, truncation, answer-based selection or replacing a failed confirmation input. Qualify natural R/M_PQ/M_QB/C_PQ/C_QB using the established complete-vector and transaction checks.
6. Run one fixed complete cost panel: default three sessions × eight inputs × five arms, with immediate same-arm warmups. Measure M_QB/M_PQ, C_QB/C_PQ, M_QB/C_QB and each path/R. Keep the original immutable numerical R. All M/C contrasts use this same new runtime. Record loading/reference preparation separately. If needed, collect phase clocks on a separate small diagnostic subset, never in the formal timing path.

The whole path is allowed to have a neutral cost result. Stop after the fixed timing panel; do not extend it to make QB pass a threshold. Do not rerun the old Llama24-input/864-measurement panel or revive full delivery audits as a research milestone.

## Result table

For each family, report: extracted structural conditions; expected and observed groups/actions; original counterexamples repaired; unchanged-R full-vector result; genuinely unseen confirmation; M_QB/M_PQ; C_QB/C_PQ; M_QB/C_QB. Separate active mechanism transfer from no-trigger compatibility. Include an unsupported case only when it teaches a specific missing structural condition.

Open a result PR against this work branch with the implementation changes and concise evidence/commands. Preserve old records and identify new candidate code/runtime hashes. Do not merge the manuscript or submit it externally.

**一句话执行 prompt：** 继续本 PR 的 `benchmarks/reference_batching_transfer_20261103/RTX_PROMPT.md`：把共享 planner 接入真实图／后端需求提取，预测并验证 Qwen8B/14B 的边界与归一化放置迁移，保留原 R，自行修复工程问题，完成小型未见确认和一次固定完整成本面板后交付结果 PR。
