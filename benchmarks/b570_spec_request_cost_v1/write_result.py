from pathlib import Path
import json
r=Path(__file__).parent
a=json.loads((r/"ANALYSIS.json").read_text())
rows="\n".join(f'| {x["session"]} | {" / ".join(x["order"])} | {x["seconds"]["PQ_A"]:.6f} | {x["seconds"]["PQ_B"]:.6f} | {x["seconds"]["QB"]:.6f} | {100*(1-x["QB_over_dual_PQ"]):+.3f}% |' for x in a["rows"])
text=f"""# B570 real speculative request: balanced cost pilot

Decision: **{a["decision"]}**. All9 timed requests match the qualified reference's complete native endpoint and10-cycle state trace. All3 independent processes exited0 with normal cleanup, complete capture and no deadline kill.

| Process | Order | PQ_A seconds | PQ_B seconds | QB seconds | QB reduction vs dual-PQ |
|---|---|---:|---:|---:|---:|
{rows}

Equal-weight dual-PQ mean: {a["mean_dual_PQ_seconds"]:.9f}s.
QB mean: {a["mean_QB_seconds"]:.9f}s.
Mean reduction: {a["mean_gain_seconds"]:.9f}s ({100*(1-a["ratio_of_means"]):+.4f}%).
Largest within-process A/A absolute difference: {a["largest_AA_difference_seconds"]:.9f}s.
Predeclared screening threshold: {a["predeclared_screen_seconds"]:.9f}s.

The screen requires QB to beat BOTH identical PQ implementations in all3 processes, plus mean reduction greater than max(2% dual-PQ baseline, largest A/A difference). This is a pragmatic descriptive screen, not a statistical significance test. No confidence interval or workload-general benefit is claimed from3 processes, one input, one date.

Process0's first PQ_A request takes15.01s while its identical PQ_B takes9.89s. This large A/A discrepancy drives the apparent aggregate reduction; it is preserved, not excluded after observing results. First-use/cache effects or unrelated system interference are hypotheses, not established causes. Processes1/2 individually show only about0.26%/0.33% reduction against dual-PQ. A future study must prospectively distinguish first-use from steady-state and balance process-level first-use exposure; rotation alone across these3 processes did not resolve this anomaly.

## Execution and cost boundary

The preceding bridge in `../b570_spec_request_bridge_v1` qualified actual speculative q2/key256/GQA32:8 execution on all36 target layers. It reproduced16 historical target-only complete logits vectors and all31 PQ/QB full-logit pairs byte for byte, including rejected verification rows. These checks preceded cost collection.

This study uses the exact qualified private runtime and models: Qwen3-8B-Q8_0 target and Qwen3-0.6B-Q8_0 draft. HumanEval/42 exposed input124IDs,16-token cap, one natural proposal per cycle, deterministic greedy sampling. Each request performs10 verification cycles,6 accepted proposals and4 rejections; no actor or RTL runs. PQ_A and PQ_B use the same PQ implementation. Three process sessions rotate each arm through each position once; not all6 permutations.

Timing starts after fresh contexts are created and ends after completion synchronization. It includes target and draft token-by-token prefill, proposal generation, verification, full-logit host copies/finite checks, greedy sampling, acceptance/correction/bonus, KV trimming and cycle-record construction. It excludes model loading, context creation, result comparisons and disk output. Models remain loaded across the three requests within a process. No observer or raw-logit file write occurs in a timed request.

Every timed request checks full output IDs/EOG/length/terminal/stop and complete cycle trace against the qualified reference after the timer. Timed requests do not recapture every full logits vector; that stronger check belongs to the preceding qualification. This is a bounded standalone runtime bridge with known host overhead, not yet the full production serving path or an optimized software ceiling. It is also not a comparison of speculative decoding against target-only latency.

## Accounting and evidence

The user explicitly authorized continuing beyond the previous remaining-budget barrier. Historical charge285.6803089s and previous failures are preserved unchanged. A new180s operational envelope was prospectively registered for this study.

New conservative whole-parent charge: {a["ledger"]["new_study_charged_seconds"]:.7f}s.
Combined historical charge: {a["ledger"]["all_history_cumulative_seconds"]:.7f}s.
Parent time includes setup/load/cleanup and is not GPU kernel active time. Old unused allowance is not relabeled or reset.

`COMPACT_EVIDENCE.zip` contains all native result/progress records, stderr/stdout and receipts, including the qualified reference. `BUILD_MANIFEST.json` pins executable/runtime/model/source inputs. `ANALYSIS.json` and `analyze.py` reproduce the table and decision from raw records. Full-logit raw files and hashes remain in the bridge evidence.

## Scientific implication and next experiment

The runtime bridge now establishes semantic feasibility for this request. Cost evidence must be interpreted independently of that success. A small or noisy request difference is insufficient to infer useful hardware opportunity or an end-to-end speedup.

The next useful study is a separately preregistered multi-input, longer-output request panel with repeated process sessions and paired identical-implementation controls, retaining exact native outputs before timing. Include target-only requests and report load/context/prefill/decode/host/transfer boundaries separately before claiming speculative benefit. Freeze the input panel before inspecting results; do not select prompts for favorable acceptance. Broaden actual query/key geometry only after exact-reference admission. Do not spend further runs repeatedly chasing this exposed prompt's favorable timing.

This delivery does not expand CPU8, start actor/RTL or merge a PR.
"""
(r/"RESULT.md").write_text(text,encoding="utf-8")
print(text)
