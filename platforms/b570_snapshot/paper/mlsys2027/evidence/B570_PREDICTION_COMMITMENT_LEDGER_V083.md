# B570 Prediction Commitment Ledger — v0.8.3

## 1. Scope

Existing-record reconstruction only; zero new inference. The reserved set contains 24 prompts, three repetitions each, and 72 complete generated-token-ID predictions. Exposure wording: no known B570 exposure in audited retained records.

## 2. Commitment identity

- Prediction file SHA-256: `0201ccd1f67492510d34be567aa83f1c38d3bd1f162a970c05d3cea9d3957826`.
- Prediction freeze Git provenance marker: `c99aaf2082ffff46741bef6f69dd96b4654d4c08`.
- Hypothesis freeze Git provenance marker: `313069ce5ac10d4d31849f515c912cad29ac7360`; hypothesis content SHA-256: `0fb6eba1fc57595dd9c4487c30ff8c5b9a0929a7714511a1278b01be4615aefe`.

A content digest identifies bytes. A Git commit binds those bytes to repository history; the recorded times support ordering. None alone proves wall-clock publication to the world.

## 3. Chronology

| Event | Recorded UTC time | Provenance source |
|---|---|---|
| discovery completed | 2026-09-29T10:34:20.875359Z | `DISCOVERY_ANALYSIS.json:finished_utc` |
| H1 hypothesis freeze | 2026-09-29T10:35:04.415251Z | `hypothesis_freeze.json:created_utc` |
| H1 freeze Git commit | 2026-09-29T10:35:25Z | `Git committer date (repository metadata)` |
| reserved inference checkpoint | 2026-09-29T10:35:41.547306Z | `artifacts/b570_mechanism_v08/raw/reserved_predictions/checkpoint.json:start_utc` |
| first reserved inference | 2026-09-29T10:35:41.602565Z | `artifacts/b570_mechanism_v08/raw/reserved_predictions/executions.json:start_utc` |
| last reserved inference completed | 2026-09-29T11:03:46.759317Z | `artifacts/b570_mechanism_v08/raw/reserved_predictions/executions.json:end_utc` |
| prediction file completed | 2026-09-29T11:03:46.794920Z | `RESERVED_PREDICTIONS.json:created_utc` |
| prediction checkpoint Git commit | 2026-09-29T11:04:57Z | `Git committer date (repository metadata)` |
| prediction checkpoint push | UNKNOWN | `Outcome stage records a push gate; no independent push timestamp` |
| live outcome checkpoint | 2026-09-29T11:05:18.111184Z | `artifacts/b570_mechanism_v08/raw/reserved_outcomes/checkpoint.json:start_utc` |
| first live serialized outcome | 2026-09-29T11:05:18.166783Z | `artifacts/b570_mechanism_v08/raw/reserved_outcomes/executions.json:start_utc` |

## 4. Endpoint rule

Complete generated-token IDs only; prompt IDs excluded. At most 128 committed IDs; an earlier terminal EOG is included. Equality compares the entire sequence including length. First divergence uses zero-based indexing; if one sequence ends first, the absent token is null.

## 5. Reserved result summary

- Frozen UB1 predictor → live serialized complete equality: **72/72**.
- UB128 reference trajectory → live serialized equality: **60/72**.
- Prompt mismatch/no-mismatch classification: **24/24**.
- Divergent repetition-pair first-divergence agreement: **12/12**, across **4** prompts.

## 6. 24-prompt compact table

Full digests are in the CSV and JSON ledgers; this table shows their first 12 hex characters.

| Task | Pred=Live | Ref=Live | Live length r1/r2/r3 | Pred/live digest r1 | First divergence |
|---|---:|---:|---|---|---:|
| HumanEval/58 | 3/3 | 3/3 | 128/128/128 | `cc12b5e1b600/cc12b5e1b600` | — |
| HumanEval/156 | 3/3 | 3/3 | 128/128/128 | `b8060d33b72c/b8060d33b72c` | — |
| HumanEval/134 | 3/3 | 0/3 | 128/128/128 | `fc12c8453de5/fc12c8453de5` | 88 |
| HumanEval/42 | 3/3 | 0/3 | 128/128/128 | `c737973a39a6/c737973a39a6` | 73 |
| HumanEval/122 | 3/3 | 3/3 | 128/128/128 | `ed3172303704/ed3172303704` | — |
| HumanEval/114 | 3/3 | 3/3 | 128/128/128 | `16037f527b2f/16037f527b2f` | — |
| HumanEval/93 | 3/3 | 3/3 | 128/128/128 | `4b69a84d3675/4b69a84d3675` | — |
| HumanEval/115 | 3/3 | 3/3 | 128/128/128 | `43fbb9bd3da9/43fbb9bd3da9` | — |
| HumanEval/151 | 3/3 | 3/3 | 128/128/128 | `f371e4f2b94e/f371e4f2b94e` | — |
| HumanEval/63 | 3/3 | 3/3 | 128/128/128 | `b3141572ec95/b3141572ec95` | — |
| HumanEval/125 | 3/3 | 3/3 | 128/128/128 | `689af3f02f2d/689af3f02f2d` | — |
| HumanEval/133 | 3/3 | 3/3 | 128/128/128 | `c1ed3bf83bde/c1ed3bf83bde` | — |
| HumanEval/43 | 3/3 | 3/3 | 128/128/128 | `2e3776c7ff02/2e3776c7ff02` | — |
| HumanEval/139 | 3/3 | 3/3 | 128/128/128 | `23a77663974d/23a77663974d` | — |
| HumanEval/77 | 3/3 | 3/3 | 128/128/128 | `dea569b38784/dea569b38784` | — |
| HumanEval/35 | 3/3 | 3/3 | 128/128/128 | `93498855fe64/93498855fe64` | — |
| HumanEval/27 | 3/3 | 3/3 | 128/128/128 | `f0f161a1b9e3/f0f161a1b9e3` | — |
| HumanEval/34 | 3/3 | 3/3 | 128/128/128 | `813cb3180ab5/813cb3180ab5` | — |
| HumanEval/145 | 3/3 | 0/3 | 128/128/128 | `31246ffe07b9/31246ffe07b9` | 103 |
| HumanEval/82 | 3/3 | 3/3 | 128/128/128 | `a356c9235624/a356c9235624` | — |
| HumanEval/154 | 3/3 | 3/3 | 128/128/128 | `0743671d064c/0743671d064c` | — |
| HumanEval/78 | 3/3 | 3/3 | 128/128/128 | `a685f47dbab9/a685f47dbab9` | — |
| HumanEval/96 | 3/3 | 3/3 | 128/128/128 | `3824c19fc287/3824c19fc287` | — |
| HumanEval/138 | 3/3 | 0/3 | 128/128/128 | `9e54992a7160/9e54992a7160` | 93 |

## 7. Divergent prompts

All three repetitions agree within each listed prompt for both predictor and live sequences.

| Task | Repetition agreement | First divergence (zero-based) | Reference token | Predicted/live token |
|---|---|---:|---:|---:|
| HumanEval/134 | 3/3 stable | 88 | 914 | 1946 |
| HumanEval/42 | 3/3 stable | 73 | 432 | 1817 |
| HumanEval/145 | 3/3 stable | 103 | 1184 | 686 |
| HumanEval/138 | 3/3 stable | 93 | 14374 | 9064 |

## 8. Interpretation boundary

The target-only UB1 predictor reproduces the tested serialized trajectory. Live draft computation is not required to generate that tested trajectory. The records do not establish a unique numerical root cause, a specific Vulkan kernel, a general B570 law, universal UB1 correctness, an RTX mechanism, or cross-backend transfer.
