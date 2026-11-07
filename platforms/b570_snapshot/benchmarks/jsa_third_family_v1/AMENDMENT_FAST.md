# Prospective fast replication amendment

Design source: PR #83, immutable head `a8a52eafaf0a64ddd7b14c7472d1b4f2d7c19e62`.
This new execution study keeps PR #80/#82 read-only.

The author previously requested the fastest execution and removal of date-based
waiting. That preference continues for this study. Before any new forward, the
six dated repetitions are replaced with **two independent process sessions per
family, run consecutively**, with actual wall-clock dates retained. There is no
deliberate wait for another calendar date. Completion on one date is an aim,
not a reason to discard late or overnight slots.

The three fixed model pairs, new history-audited 12 MBPP + 12 GSM8K panel, six
conditions, four rounds per session, cap128, ctx1024/F16 KV, numerical DLLs,
full-offload and memory gates, target templates/shared pair IDs, greedy sampling,
scope/reset checks, fixed Llama M3/C3_K3 primary, k1/k2 secondary reporting,
capture-off formal requests and absence of formal retries remain in force.
Engineering and exposed/synthetic probes remain bounded by 640 requests.

The original family rotations, four condition rows and task-order hash strings
are used with session index 0 and 1 in place of date index. The primary R/M3/C3_K3
positions are balanced within each session. The original six-date overall
family/condition position balance is **not** achieved and is reported as a limit.
Cooling/admission remains the original idle120s + three 10s-spaced observations,
util<=5%, temp<=55C, range<=2C, AC required, at most600s per block.

New formal plan: `3 * 24 * 6 * 4 * 2 = 3456` requests, 144 planned warmups,
192 planned slots per family/condition. With the engineering cap, maximum full
requests is4240. Original owned-process upper budgets (8 engineering +24 formal
hours,32 total) and14-calendar-day outer guard remain; spare budget is not a
license to retry or add confirmations.

The frozen comparison-specific completeness gate now requires all192 slots of
each necessary condition and a complete stable R. Unrelated condition failures
do not erase an otherwise complete pair. No subset qualification, imputation,
majority reference, endpoint truncation, condition deletion or winner selection.
The old PR80 global-matrix gate is unchanged.

For each family/session/task/condition, aggregate four absolute resident HTTP
times by median. Average the24 paired task log ratios within each session, then
average the two session effects. Report descriptive point estimates, both
session effects, domain/task effects and regressions. **All six-date intervals,
Bonferroni date intervals and cross-date positive decisions are untested/null.**
No thousands-of-requests-as-independent-samples inference is substituted.

Asset, memory or implementation blocks retain planned missing slots and null
qualified comparisons for the affected family. Other families can proceed only
after the common input panel and their implementation are frozen and qualified.
Final F0A/F0B and authenticated remote readback are required before the respective
first forward and first formal request. This amendment is not a result.

## Native capacity resolution before any forward

The zero-forward actual loader logs show the unchanged PR80 runtime clamps
requested `--batch-size2048` to effective `n_batch1024` under `ctx1024`.
Keep the requested flag2048, context1024 and physical targetUB1/4,draftUB1;
do not override the native clamp or change the numerical stack. The effective
logical capacity for this new execution is therefore1024 in every condition
and family, resolving the unattainable literal effective2048 field in PR83.
All eligible prompts must be<=768 IDs, so no paid request exercises either
capacity ceiling above1024. This is a prospective feasibility amendment based
on zero-forward logs, not speed or output selection. Both requested and actual
values are reported; no old ctx4096 timing is pooled with this study.
