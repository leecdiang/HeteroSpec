# Resident cost gate on the original RTX19 cohort

Prerequisite: the fixed attention prototype matches all four original diagnostic/control references. This gate is frozen after that exposed engineering check, before the 19-task service outcomes below. It is not an unexposed holdout.

Run the exact19 original RTX HumanEval prompts, in their original source order, cap128 with inclusive native EOG. Same assets, FA off, ctx4096, batch2048, threads24, single slot, greedy seed123, no prompt reuse, f16 cache. The same private compiled server and unchanged released CUDA DLLs run all three conditions:

1. Target-only global UB1, attention patch off.
2. Full native draft k2/global UB1, attention patch off (existing serialization baseline).
3. Full native draft k2/global UB2, single-query attention patch on, other operations batched.

Each condition gets three fresh resident sessions, with one excluded cap32 warmup and all19 requests:171 measured requests +9 warmups. Rotate condition order target/serial/candidate; serial/candidate/target; candidate/target/serial, and rotate task order by repetition. GPU conditions execute sequentially. Close only owned processes. Maximum six additional qualification requests are reserved if a server transport issue requires diagnosis; no automatic failed-model retry or outcome-based exclusions. If target-only service does not match the original immutable CLI R arrays, stop the experiment; do not redefine the reference.

Primary output gate: every complete candidate ID array and endpoint must match its paired fresh target reference; native service stop_type limit/eos is mapped explicitly to the CLI inclusive-EOG contract. Compare candidate versus existing serialization on the same reference. Keep every failed task and its time, but do not report a workload-wide admissible speedup for a failing condition.

Primary cost: full uncached HTTP request elapsed time in a resident single-slot server; includes prompt evaluation, drafting, target verification, correction/bonus, state cleanup and response. Model loading and teardown are excluded for all conditions. Secondary cost: native predicted_ms generation timer, separately labeled. Report median of three condition latencies per task then geometric mean of paired target/candidate ratios, and per-task ranges. Three repetitions are a stability/screening study, not a confidence interval, energy, throughput, training-novelty or universal-losslessness claim. No task-dependent routing or recorded proposal/reference input is passed to the candidate.

No instrumented state forks or metadata callbacks run during cost measurement. The source still synchronizes target and draft decoding through the same existing frontend wrapper in all conditions; thus results apply to this shared private frontend, not automatically the released deployment binary. Source/hardware/asset bindings and all raw request/response bytes are retained.
