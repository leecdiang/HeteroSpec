# M4 prospective runtime profitability-control study v0.1

Status: **DESIGN FROZEN BEFORE NEW TIMING; implementation and provenance gates pending.**

This is a new prospective software study on `runtime/m4-profitability-control-v0.1`. The closed M4 hardware results remain read-only. Energy is **NOT_CLAIMED**. A negative, inadmissible, or blocked result remains a valid outcome.

## Question and data

Can a one-way realized-cost guard choose whether to continue the existing Metal fixed-`k=2` speculative path or fall back permanently to target-only for unseen prompts, with strict direct generated-token ID equality and lower held-out latency regret?

The local dataset byte hashes are in `WORKLOAD_INVENTORY.json`. Historical raw records, derived tables, selections, and local ignored M4 files were scanned without using performance values to select tasks. IDs with any historical M4 execution or exposed outcome are ineligible. A SHA-256 rank of `20260924|<family>|<task_id>` selects, within each of HumanEval and Spec-Bench, 8 untouched qualification, 20 untouched calibration, and 30 untouched held-out tasks. The two families are prospective strata and are **never** passed to the online policy. The held-out total is 60. Exact IDs and prompt hashes are in the split JSON files. Qualification tasks never enter calibration or formal estimation.

HumanEval prompts use the historical code-completion instruction plus canonical task prompt. Spec-Bench uses `turns[0]` as in the historical M4 runner. Both are one user chat message using the installed Qwen template with thinking disabled. A common 128-token cap is fixed for this new study; this is the historical HumanEval cap and is declared here before any new timing. Target and draft are the historical Qwen3 8B/0.6B Q8_0 pair with hashes in the protocol JSON. Both run on Metal `MTL0`; `k=2`, draft-simple, greedy target sampling, and one-way fallback are fixed. The source/environment manifest must capture every remaining build setting before any formal run.

## Conditions and correctness

The only online conditions are `TARGET_ONLY`, `ALWAYS_SPEC_K2`, and `GUARD_K2`. The offline oracle is `min(T_target,T_always_spec)` **after** both are measured. Direct generated-token ID sequences for both speculative conditions must equal the paired target-only sequence for the same task and repetition. One mismatch makes that condition performance-inadmissible. Full output, including EOS where generated, is compared. Mismatch location, IDs, round, policy state, and KV position are retained.

No task ID, family label, prompt whitelist, historical winner, future token, final length, held-out result, or current-request target-only latency may enter the guard. The initial seed token and every fully charged speculative verification round contribute committed progress `C` only when their generated IDs are actually committed. At `E` completed verification rounds, and after every later round if still speculative, compute `R_spec = all elapsed charged generation and control cost / C`. If `C=0` at a decision, fall back. Otherwise continue iff `R_spec <= (1-m) * R_target_ref`; fallback is permanent. A request ending before `E` has no decision. The cost clock starts at the historical post-prefill generation boundary and includes initialization, draft, target verification, accept/correction/bonus, memory reconciliation, synchronization, guard calculation, copies, and transition. Model load, first compilation, and shared prompt prefill are outside all conditions identically.

`R_target_ref` is the median across calibration prompts of each prompt's median target-only post-prefill latency across three repetitions divided by its median generated-token count. Nonpositive counts invalidate calibration rather than being silently discarded. The nine policy candidates are the Cartesian grid `E={2,4,8}` and `m={0,0.05,0.10}` in `POLICY_CANDIDATES.json`. No candidate may be added after calibration starts.

## Calibration and freeze

Run three repetitions on each of the 40 calibration tasks for target-only, always-spec, and all nine guard candidates. Reject candidates with any direct token-ID mismatch. For each task and condition take the median latency; define calibration oracle as the lesser target/always-spec median. Select the candidate with lowest geometric mean across tasks of `T_guard/T_oracle`. Exact ties break by lower measured mean guard-compute overhead, smaller `E`, larger margin, then lexicographic ID. Freeze the selected candidate, target reference, raw-data and script hashes, source/build, model/environment, IDs, and explicit `heldout_data_seen=false` before qualification. Calibration timings are development data only.

An R0 feasibility phase may test API, state/KV fallback, exact token plumbing, timestamps, cost accounting, and durable JSONL. R0 timing is non-formal and cannot tune the policy. Required state-machine tests cover full accept, both rejection positions, correction/bonus, EOS/cap/reset, repeated rejection, early and late fallback, no switch-back, `C=0`, and charge of guard/transition work. Any implementation repair affecting calibration timing reruns calibration. Policy-semantic changes require a new protocol version.

After policy freeze, the 16 reserved qualification tasks get three paired repetitions. Require 48/48 direct token-ID exact pairs for **each** speculative condition. Timings are diagnostic. The formal runner then requires a clean committed tree, matching source/script/model/data/environment/policy hashes, qualification PASS, and this protocol version. It writes `FORMAL_DATA_STARTED` before any held-out observation.

## Formal schedule and analysis

Each of 60 held-out tasks gets three repetitions of all three conditions; condition order is shuffled within task×repetition with seed 20260924. Record every observation as append-only JSONL with flush and `fsync`, full token IDs, timing, decision trace, proposed/accepted/committed counts, fallback round, guard compute/transition cost, power/thermal metadata, and status. Interruption or invalidation retains the whole attempt and requires a new complete attempt under the same freeze; there is no selective rerun. A correctness mismatch is reported and makes performance for that condition inadmissible.

Per task and condition, take the median of its three latencies. Primary speedup is the prompt geometric mean of `T_target/T_guard`; also report `T_target/T_always_spec`. Use 10,000 prompt-level bootstrap resamples, seed 20260924, percentile 95% CI; repetitions are not independent bootstrap units. After measurement, report geometric-mean oracle regret `T_guard/min(T_target,T_always_spec)` with the same CI method, median and p90 additive regret, fallback fraction and round distribution, token fractions, acceptance, committed tokens/round, guard compute and transition cost, total control overhead, and both prospective strata. Retain every prompt, including unfavorable strata and failed attempts.

The paper and historical M4 records are untouched. No result is merged to `main` without an explicit user request.
