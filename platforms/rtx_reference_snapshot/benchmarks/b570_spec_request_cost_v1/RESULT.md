# B570 real speculative request: balanced cost pilot

Decision: **NO_ESTABLISHED_PRACTICAL_REQUEST_GAIN**. All9 timed requests match the qualified reference's complete native endpoint and10-cycle state trace. All3 independent processes exited0 with normal cleanup, complete capture and no deadline kill.

| Process | Order | PQ_A seconds | PQ_B seconds | QB seconds | QB reduction vs dual-PQ |
|---|---|---:|---:|---:|---:|
| 0 | PQ_A / PQ_B / QB | 15.010835 | 9.887352 | 10.045003 | +19.311% |
| 1 | PQ_B / QB / PQ_A | 9.881487 | 9.903571 | 9.866445 | +0.264% |
| 2 | QB / PQ_A / PQ_B | 9.891373 | 9.866477 | 9.846754 | +0.326% |

Equal-weight dual-PQ mean: 10.740182500s.
QB mean: 9.919400767s.
Mean reduction: 0.820781733s (+7.6422%).
Largest within-process A/A absolute difference: 5.123482800s.
Predeclared screening threshold: 5.123482800s.

The screen requires QB to beat BOTH identical PQ implementations in all3 processes, plus mean reduction greater than max(2% dual-PQ baseline, largest A/A difference). This is a pragmatic descriptive screen, not a statistical significance test. No confidence interval or workload-general benefit is claimed from3 processes, one input, one date.

Process0's first PQ_A request takes15.01s while its identical PQ_B takes9.89s. This large A/A discrepancy drives the apparent aggregate reduction; it is preserved, not excluded after observing results. First-use/cache effects or unrelated system interference are hypotheses, not established causes. Processes1/2 individually show only about0.26%/0.33% reduction against dual-PQ. A future study must prospectively distinguish first-use from steady-state and balance process-level first-use exposure; rotation alone across these3 processes did not resolve this anomaly.

## Execution and cost boundary

The preceding bridge in `../b570_spec_request_bridge_v1` qualified actual speculative q2/key256/GQA32:8 execution on all36 target layers. It reproduced16 historical target-only complete logits vectors and all31 PQ/QB full-logit pairs byte for byte, including rejected verification rows. These checks preceded cost collection.

This study uses the exact qualified private runtime and models: Qwen3-8B-Q8_0 target and Qwen3-0.6B-Q8_0 draft. HumanEval/42 exposed input124IDs,16-token cap, one natural proposal per cycle, deterministic greedy sampling. Each request performs10 verification cycles,6 accepted proposals and4 rejections; no actor or RTL runs. PQ_A and PQ_B use the same PQ implementation. Three process sessions rotate each arm through each position once; not all6 permutations.

Timing starts after fresh contexts are created and ends after completion synchronization. It includes target and draft token-by-token prefill, proposal generation, verification, full-logit host copies/finite checks, greedy sampling, acceptance/correction/bonus, KV trimming and cycle-record construction. It excludes model loading, context creation, result comparisons and disk output. Models remain loaded across the three requests within a process. No observer or raw-logit file write occurs in a timed request.

Every timed request checks full output IDs/EOG/length/terminal/stop and complete cycle trace against the qualified reference after the timer. Timed requests do not recapture every full logits vector; that stronger check belongs to the preceding qualification. This is a bounded standalone runtime bridge with known host overhead, not yet the full production serving path or an optimized software ceiling. It is also not a comparison of speculative decoding against target-only latency.

## Accounting and evidence

The user explicitly authorized continuing beyond the previous remaining-budget barrier. Historical charge285.6803089s and previous failures are preserved unchanged. A new180s operational envelope was prospectively registered for this study.

New conservative whole-parent charge: 115.5320486s.
Combined historical charge: 401.2123575s.
Parent time includes setup/load/cleanup and is not GPU kernel active time. Old unused allowance is not relabeled or reset.

`COMPACT_EVIDENCE.zip` contains all native result/progress records, stderr/stdout and receipts, including the qualified reference. `BUILD_MANIFEST.json` pins executable/runtime/model/source inputs. `ANALYSIS.json` and `analyze.py` reproduce the table and decision from raw records. Full-logit raw files and hashes remain in the bridge evidence.

## Scientific implication and next experiment

The runtime bridge now establishes semantic feasibility for this request. Cost evidence must be interpreted independently of that success. A small or noisy request difference is insufficient to infer useful hardware opportunity or an end-to-end speedup.

The next useful study is a separately preregistered multi-input, longer-output request panel with repeated process sessions and paired identical-implementation controls, retaining exact native outputs before timing. Include target-only requests and report load/context/prefill/decode/host/transfer boundaries separately before claiming speculative benefit. Freeze the input panel before inspecting results; do not select prompts for favorable acceptance. Broaden actual query/key geometry only after exact-reference admission. Do not spend further runs repeatedly chasing this exposed prompt's favorable timing.

This delivery does not expand CPU8, start actor/RTL or merge a PR.
