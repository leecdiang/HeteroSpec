# Required manifests before B/C/D execution

This operational checklist implements the frozen master protocol. No B/C/D task has been selected or executed by this tranche. An absence of a local output is not evidence of clean historical exposure.

## B: recipe and unused-task panel

Freeze a new manifest, commit and record its SHA before either reference or candidate generation. Include:

- The post-A recipe decision, source/build hashes, exact command/environment templates, original wrapper and inclusive EOG/cap rules. The scalar reference uses scalar target decode/prefill; speculation is compared in cost to its separately qualified target-only control with the same target scope and prefill. Do not count scalar reference generation as free or use its outputs to route the candidate.
- Dataset file SHA256 and task-ID namespace. Record every task's raw/formatted prompt SHA256 and formatting-source hash. Downloaded prompts alone are not inspected generated outputs.
- An exposure ledger with task ID, `EXECUTED_OR_INSPECTED`, `AVAILABLE_ONLY`, or `UNKNOWN`, supporting manifest/output paths and hashes, and source coverage. Search the manuscript inputs, earlier platform experiments, PR #55/#56/#58/#59 artifacts and local histories. Unknown histories are excluded.
- Eligible tasks ranked by SHA256 of UTF-8 `(task_id + "HeteroSpec-RTX-Phase2-B-v1")`, with task ID as the deterministic tie-breaker. Select the first24 in each eligible HumanEval/MBPP namespace. Keep the entire ranked eligible list and excluded reasons. Fewer eligible tasks require an explicit pre-output protocol amendment or an unsupported evaluation.
- Exact condition, repetition, task order and excluded warmup counts. Use four cyclic condition rotations; retain every full output and timing, even when a candidate drifts. No retuning on B under the same unused-task label.
- Code extraction/tests are out of scope until a separate functional-evaluation contract is frozen; array agreement does not establish code correctness.

## C: width/length bridge and boundary panel

Freeze the first8 qualified B tasks in its deterministic hash order and all twelve cap/width configurations before any boundary outputs. Caps are128/256/512; `(k, UB)` is `(1,2),(3,4),(5,6),(7,8)`. Freeze exact commands and actual graph-shape coverage for each width before the formal panel. The scalar reference remains scalar; a matched target control uses the candidate's target geometry and must independently agree with that reference. Preserve repeated scalar baselines as paid requests.

The Stage A attention constraint does not establish invariance of projections/FFN beyond UB4. Verify that the existing one-KV-stream graph view remains supported; do not silently bypass shape guards. Every failed configuration keeps its complete outputs and diagnostic timings, with no qualified speed claim. Any extension is selected by the predeclared width/cap order and B task hash order, limited to at most two pairs, and committed before its model runs. Natural prefix alignment is required for actual-state crossing; forced donor prefixes are a separate unsupported question.

## D: persistent order and resource panel

Freeze the first24 qualified B tasks and two permutations before inference. Generate each permutation by sorting SHA256 of UTF-8 `(task_id + "HeteroSpec-RTX-Phase2-D-v1-cycleN")`, where N is1 or2, then task ID. Keep one uncached resident service for each of the two modes in each cycle. This produces96 measured requests and4 excluded warmups. Keep full outputs, phase reset observations, request duration trends and resource metadata outside request timers. Single-slot correctness is not a multi-slot throughput result.

## Records and failure policy

Each manifest binds protocol, source commit, runner/config/prompt/dataset/build/model/runtime identities and a complete planned request matrix. A complete matrix audit precedes analysis. Distinguish recipe failure, reference failure and implementation failure. Keep incomplete attempts and zero-model preparation errors. A failing request is not automatically repeated with different code or a convenient replacement task. Follow-up repairs require a new frozen identity and retain the original failure as evidence.
