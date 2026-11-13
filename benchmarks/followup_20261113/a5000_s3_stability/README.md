# A5000 S3 stability and held-out workload follow-up

Status: **H COMPLETE; R1/R2 PENDING**. The user authorized both panels and subsequently removed computation/panel time limits; the 468-request / 149,760-row ceilings remain. The original native deployment is restored, successor launch/checker/scratch wiring is implemented, and H has passed qualification and completed all registered requests. See [execution contract](EXECUTION.md), [H results and raw evidence](RESULTS_H_20261114/README.md), and [current handover](HANDOVER_ZH.md). Historical STATE, journals, baselines and paper remain unchanged. The design below records the original plan; execution amendments in EXECUTION.md supersede its former approval and wall-limit language.

## Question and decision
Does the S3 independent-scalar-group advantage over a backend scalar loop recur on later dates? Separately, does it appear on a prospectively selected short-prompt workload? This is a confirmation of a compatibility-preserving deployment increment, not a search for 5% and not a LOCAL or speculative-decoding experiment.

Primary replication panel R: the original 12 S3 roots, on **two new dates separated by at least 24 hours**, same A5000 UUID. Dates are arranged before execution and not selected from favorable timing.
Secondary panel H: 12 new roots, run in a separate named session; its results never replace R. The user authorized H independently of the sign of R. It ran first and is reported as a prospectively selected new workload, with later development exposure unknown for every root.

## Frozen numerical and timing contract
Reuse the exact Qwen3-32B-Q4_K_M GGUF and original S3 numerical binaries/dependencies where available. Target-only greedy k=0, no draft, WHOLE/SIMPLE, context 1024, microbatch/output reserve 32, two native CPU threads, F16 KV, CUDA graphs off, flash off, cap128, original prompt rendering. No CPU/GPU offload or placement changes. B = shared activation quantization followed by backend scalar loop (a=1); C = independent scalar groups. G is omitted because C/B is the unresolved question.

The primary clock is the **same native reset-inclusive resident request interval**: reset/planning/prefill/decode/owned output/final synchronization included; load/context construction, heavy capture and terminal export excluded. Record worker wall/load and end-to-end campaign wall separately. Do not replace this with GPU-event time or a new server clock. Keep full prompt and emitted-token counts, prefill/decode subintervals and output/state checks.

If original qualified artifacts cannot be restored exactly, report a **rebuilt-deployment replication**, not an identical-binary repeat. Requalify that deployment before timing. A changed driver/toolkit is logged and prevents attributing a difference solely to date.

## Panel sizes and order
R: 12 roots × 2 new dates × 2 rounds × 2 arms = **96 measured requests**. Every arm is a fresh process with one same-root warmup, reset, and one measured request, matching S3: another **96 warmups**, 96 fresh formal workers.
H: 12 new roots × 1 session × 2 rounds × 2 arms = **48 measured + 48 warmups**, 48 fresh formal workers.

For each root and date, round 1 uses BC or CB from a fixed schedule, round 2 reverses it. Half of each domain has each order. Interleave domains and randomize root order with a recorded fixed seed, independent of outputs/times. Keep the two arms of each pair adjacent. A fresh process per arm retains the historical load/reset boundary. A common warmup is charged, not assumed free.

The supplied CPU schedule generator validates counts and emits order only. It is **not a native runner** and cannot start CUDA.

## Qualification without regenerating hundreds of GB
Before first timing each root: two independent pristine R runs, then B-heavy + B-clean and C-heavy + C-clean bridge runs (6 requests/root, four processes). Compare the requested complete vocabulary vectors, active F16 KV in logical order and logical/pending/termination state at the same registered checkpoints as the S3 reader. R repetition must agree before comparing candidates. Existing S3 EOG/cap/reset fixtures remain evidence for unchanged code; if the frontend changes, re-run affected fixtures with a revised request budget, not silently reuse their certificate.

On the second replication date, recheck two fixed sentinel roots (one code, one math): R, repeated R, B-heavy+clean, C-heavy+clean = 12 requests. All clean timed requests compare complete emitted sequence, trajectory/work metadata, final vocabulary vector and final active KV against the per-root independent R oracle **after the timer**. R/H qualification is not a new all-input proof.

Use bounded streaming comparisons / one-root-at-a-time scratch rather than exporting every tensor for every timed request. Retain all scalar timings, input tokens, configuration, output vectors, comparison results and failures; retain full new raw trajectories for fixed sentinel roots and any mismatch if space permits. Record exactly which raw states were retained. Do not claim full archived tensor replay when only streaming equality records remain. No existing dataset or archive may be deleted. Any temporary-file disposal policy for new captures must be included in execution approval; this design does not delete files.

## Request and resource envelope
R: 72 first-date qualification + 12 second-date sentinel + 192 formal/warm = **276 planned requests**; request ceiling **292**, counting failed starts. H: 72 qualification + 96 formal/warm = **168 planned**; ceiling **176**. Combined planned **444**, maximum **468**; no borrowed old quota.

All inputs have 1–192 prompt tokens and cap128; conservative reservation <=320 rows/request: R ceiling **93,440 rows**, H **56,320**, combined **149,760**. Actual native input/output rows are reported separately. Formal workers 96+48; qualification workers56+48 (each B/C qualification worker runs both heavy and clean), so **248 planned worker starts**, with any failure/replacement charged to request ceilings.

Use one A5000, no concurrent study workers. Historical memory use reached ~19.87 GB on a 24 GB card, not a current allocation guarantee. Before any execution, inspect current free VRAM, other users and maintenance; do not evict unrelated jobs or alter clocks/power/security settings. Reuse existing cooperative lock and basic timeout, not a new host-wide control system. Require measured working-set headroom and sufficient free disk for the selected retention mode.

The original four-hour panel limits were explicitly cancelled by the user before execution. Native computation has no completion deadline. Storage remains bounded at **80 GiB new outputs**, with at least20 GiB free margin; the corrected phase-specific bound is 68.5244 GiB. Full original comparisons precede scoped disposal of new intermediate KV; see EXECUTION.md and STORAGE_BOUND.json. Resource or numerical failures still stop the affected work.

## Analysis and reporting
For R, compute each root/date mean log(C/B) over its two rounds; report each date's equal-root geometric ratio and all 12 root points. Primary combined R estimate equally weights roots and the two dates. Its 95% stratified paired-root bootstrap (20,000 draws, code/math separately, keeping dates and repeats together) is **conditional on these two dates**. Do not bootstrap two dates into a population-of-days confidence interval. Report date interaction descriptively and difference from historical S3; old S3 rows are not pooled into the confirmatory estimate.

H uses its own equal-root mean log ratio, own 95% interval with the same domain-cluster procedure, and distinct label "prospective held-out short-prompt panel." If claiming both R and H significant as one family, additionally report Holm-adjusted tests or simultaneous97.5% intervals; do not promote whichever is favorable. Primary R conclusion does not require H significance.

Provide root-level plots, paired order checks, phase totals and residuals; retain all unfavorable samples. No outlier trimming by observed performance, no optional stopping for significance, no target5% rule. Confidence interval crossing1 means inconclusive advantage, not equivalence; C slower is a valid result. An effect differing across dates is evidence about robustness, not a reason to discard a day. No population-wide or multi-GPU generalization.

## Held-out root selection
Before any new model output, select 6 code and 6 math from the original pinned source snapshots/formatting, excluding every known project root ID, exact normalized text and exact prompt-token match available in the public exposure inventory, including original12. Choose eligible 1–192 token inputs by SHA256("s3-holdout-20261113:"+canonical_id) ascending, no truncation and no output/acceptance/time screening. Record full chosen IDs/tokens and candidate exclusions in an input-only manifest. If the historical exposure inventory is incomplete, call them "prospectively selected new panel" and disclose known overlaps; never claim training-unseen. Missing source snapshot/insufficient candidates is a selection blocker, not permission to substitute a favorable dataset.

## Practical failure policy
Ordinary CPU preparation errors (paths, JSON formatting, packaging, known ABI compilation fixes) may be repaired and retried before native work; log a concise change. Do not create new approval gates for harmless file-format fixes.
During execution, pause for resource interference, thermal/power instability or ambiguous worker state. Resume only unstarted jobs after state is clear; do not kill unrelated jobs. A numeric mismatch halts that arm's performance claims and preserves evidence. Driver reset/hang or unknown live worker stops new starts. A failed timing pair may be rerun once as a **whole B/C pair**, only for a predefined infrastructure failure, with the first attempt retained and charged; no retries for unfavorable times. If budget cannot cover it, mark partial. Report partial data descriptively, not as completed registered panel.

## Implementation and execution status
The old execution_s3_v1/plan.py and run.py hard-code G/B/C,423 requests,12-root preparation and historical authority fields. **Do not invoke the old runner as this follow-up or edit its STATE.** Make a small successor adapter for B/C and named dates/cohorts using its existing model_job, clean reader and clock boundaries; copy no old authorization strings. Bind the actual launch command, root manifest, selected UUID, working-directory outputs and configured budgets in the execution handoff. Review that adapter and test schedule/parsing/failure handling on CPU before requesting execution.

The CPU adapter is extended by native.py, run_campaign.py, analyze.py and the saved-data independent replay.js. Seventeen CPU tests pass in ordinary and -O Python. Original model, ELFs, compiled dependency closure, S1 certificate and loaded modules have been checked on the host. H completed 168 successful logical requests plus two charged startup failures, with no numerical mismatch; all failures and repairs are retained. R1 is scheduled for Beijing 2026-11-14 03:00 at the earliest. R2 starts no earlier than completed R1 +24h+1s (and Beijing 2026-11-15 03:10). Both dates use the same frozen dated controller, same GPU and same journal. No R result is yet available.

## Sources
- [S3 report and exact scope](https://github.com/leecdiang/HeteroSpec/blob/ab695a766d055f7d3c6b1fed0720c579c749bcdb/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/RESULTS_S3_20261112/README.md)
- [Original plan](https://github.com/leecdiang/HeteroSpec/blob/ab695a766d055f7d3c6b1fed0720c579c749bcdb/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/execution_s3_v1/plan.py)
- [Original controller](https://github.com/leecdiang/HeteroSpec/blob/ab695a766d055f7d3c6b1fed0720c579c749bcdb/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/execution_s3_v1/run.py)
- [Original input-only selection](https://github.com/leecdiang/HeteroSpec/blob/ab695a766d055f7d3c6b1fed0720c579c749bcdb/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/execution_s3_v1/select_roots.py)
