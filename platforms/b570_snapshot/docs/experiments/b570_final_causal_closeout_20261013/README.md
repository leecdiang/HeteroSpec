# B570 final causal closeout — design PR

**Design status only: no fresh GPU work has been run for this PR.**

**Immutable parent:** #99 (head c0e16aff9f3eeb0e677a52fcdc092068c096bf5d). History: #97 → #99; #92/#93 provide original reference failure, separate posthoc same-output loss, and physical k1/UB1 work evidence. Avoid mixing Q8/k2 historical campaigns with the new frozen Llama Q6 target and Q4 draft/k1 optional timing context.

### One last falsifiable experimental loop
1. **P1-A/B**: UB128 explicit caller D + frozen Prefill partition schedules to distinguish physical partition/caller observables.
2. **P1-C**: first divergent native operator and same-operand replay, explicitly checking upstream tensors before attributing effects to Attention.
3. **P0/P2**: complete retained-state restore admission, then controlled KV × initial FP32 Logits donor crosses **only if shams pass**; otherwise honestly mark NOT_ADMITTED.
4. **P3 OPTIONAL**: real completed Vulkan GPU timestamp timeline if feasible; never required for the main paper.

[PROTOCOL.md](PROTOCOL.md) is the only normative scientific definition; [EXPERIMENT_MATRIX.md](EXPERIMENT_MATRIX.md) is a quick arm/count table; [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) is the copy-paste B570 Work task entry.

**Upper bound:** 151 registered whole native requests, 49 extra/failed-start allowance, **200 all-new request starts maximum**, plus at most 8 zero-forward load probes and ≤72 GPU-only replay starts; ≤6 hours owned B570 GPU-process lifetime. Every slot, failed launch, and source revision must be accounted for. No new Qwen/Gemma family, RTX QB port, speculative tuning, positive-result search or 1,200-record repeat. Preserve old stock reference null ratios and separate posthoc negative paid ratios.

The Work platform owner can simply say: **“按照 B570 最终因果机制设计 PR 执行 PROTOCOL.md 与 EXECUTION_PROMPT.md，实机完成所有可准入实验，并创建独立 Draft 结果 PR。”**

The full-state cross and GPU timeline are conditional on genuine source/driver capability. **“完成全部” means completing/attempting admission gates and reporting blocked endpoints honestly, not fabricating their measurements.**
