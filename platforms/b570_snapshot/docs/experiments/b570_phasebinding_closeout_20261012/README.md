# B570 phase-binding / physical work — prospective closeout

**Design only. No additional B570 requests are executed by this PR.** Base = audited B570 PR #93 head `57da177c3b63a714d6e6b5e5d7a7dc1f1393e662` over PR #92.

**Two-part purpose:** (1) test the concrete R_stock versus R_prod/M/C reference difference at two known GSM8K first-divergence boundaries, using prefill/continuation/state controls **only when isolatable**; (2) close the actual k1/UB1 physical verification work explanation using existing 1,200 native requests and a tiny additional instrumentation witness.

Keep two claims separate: original R_stock-qualified request ratios remain NULL; PR #93's R_prod=M_match=C_k1 post-hoc full-output-matched ratios (R_prod/C 0.719264, M/C 0.727927) are supported but cannot retroactively replace the registered stock reference. Continuous GPU residency and additive stage wall remain UNKNOWN.

Read [PROTOCOL.md](PROTOCOL.md) (normative) then [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md). No RTX query-batch port, no model/k/quantization search, no fourth family, no redoing existing 1,200 formal slots.

The platform owner may execute by saying: **“完成 B570 phase-binding 机制闭环设计 PR；严格执行 EXECUTION_PROMPT.md，提交新的 Draft 结果 PR。”**
