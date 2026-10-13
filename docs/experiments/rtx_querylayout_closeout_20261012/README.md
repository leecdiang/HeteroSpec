# RTX method closeout — prospective design

**Design status only; zero new GPU execution by this PR.** The operator replay and cost numbers are UNKNOWN until a separate result PR exists.

Base: independently audited RTX PR #94 (`f8f3572f8f55041337a7352cc676783f9f4e1cb3`) stacked on completed PR #91. Keep all parent science and existing JSA manuscript unchanged.

**Question:** Can a phase-scoped query-as-batch attention layout explain numerical reference recovery at actual QK/softmax/AV kernels, and be cheaper than independently qualified per-query attention or target-global serialization, while preserving projection/FFN batching?

Read order: [PROTOCOL.md](PROTOCOL.md) (normative hypothesis, arms, metrics, evidence and caps) → [EXECUTION_PROMPT.md](EXECUTION_PROMPT.md) (host Work authorization).

Results must be labelled separately: (1) operator numerical correspondence, (2) complete fixed-reference output qualification, (3) matched same-reference repair cost, and (4) incremental draft value. A source-level transformation, matching tokens, and lower graph counts are **not substitutes** for each other.

The platform owner may execute by saying: **“完成 RTX query-layout 机制闭环设计 PR；严格执行 EXECUTION_PROMPT.md，提交新的 Draft 结果 PR。”**

After authenticating the design head, Work must run the real pinned host study; do not create speculative metrics or edit main. Any inability is a `BLOCKED_NOT_RUN` result with concrete receipts.
