# Evidence and analysis contract

Use simple machine-readable records and an independent analysis command. The
formats below specify meanings and minimum fields, not a required framework or
serializer. Add fields when necessary; keep a schema version. Null means unknown
or not observed and must have a reason. Do not substitute zero, an empty success
record, or a guessed timestamp. All identifiers must be unambiguous within a run.

## Before a formal block

Materialize RUN_SPEC.template.json into the run root. Fill actual source commit,
numerical modules, device/backend, lifecycle, input/reference manifest hashes,
matrix/ordering seed, cost views, counts, thresholds, resource estimates, analysis
version and exclusions. Record evidence cohort (historical/synthetic/new-natural),
reference kind (historical deployed/new deployed/abstract) and prior exposure.
Commit code first; hash actual bytes consumed. Retain the source/build diff from
PR118. No self-referential manifest or exact JSON whitespace convention is required.
Use a manifest of files and hash that manifest separately. If line-ending conversion
changes runtime bytes, bind the actual new bytes before a new formal block rather
than pretending they equal the old hash.

The planning template is deliberately not executable: null identities and empty
resolved matrices must be rejected by any future formal runner. Filling a template
does not fabricate authorization or prove qualification.

## Required output tables

| File | One row per | Minimum columns |
|---|---|---|
| CONTEXTS.csv | Logical input/geometry | context_id, cohort, exposure, family, layer, phase, q, d, Hq, Hkv, tensor_key_extent, visible_keys_min/max, positions/mask rule, shapes/strides/dtypes, source/reference hashes |
| CELLS.csv | Planned context/layout/lifecycle/block | cell_id, stage, context_id, layout, lifecycle, block, planned_order, status, reason, attempt_id, source_revision |
| ATTEMPTS.jsonl | Actual invocation/attempt | attempt_id, parent/cell, argv or exact command receipt, cwd, start/end clock, PID/creation identity if available, exit/timeout, source/runtime/input hashes, raw locations |
| QUALIFICATION.csv | Executed qualification cell | support status, actual device placement, input_before/after identity, completion, ordinary match, stage matches where observed, first mismatch/witness, repeat count, eligibility and reasons |
| TIMING_RAW.csv | Warmup or measured call | run/block/context/layout/host/call IDs, warmup flag, lifecycle, source cohort, cost view, raw clock ticks/frequency, phase boundaries, completion, output qualification, environment status, eligibility |
| TIMING_HOST.csv | Host/cost view | valid/raw/warmup counts, mean/median/p95/max, initialization/allocation/materialization/upload/readback costs, excluded validation cost or scope, memory bytes, missing reasons |
| CONTRASTS.csv | Matched context/block/pair/view | numerator/denominator identities, means, ratio, absolute difference, eligibility, both source revisions, missingness |
| COVERAGE.csv | Family/phase/q/cohort/etc. | planned/started/qualified/failed/unsupported/unstarted, pair coverage and scope |
| MODEL.csv | Workload/resource/policy | full geometry/ref kind, numerical DAG identity, compute/bytes/dependency bound, scheduler policy, storage/ports/queues/latencies, cycles, utilization, overhead, bound gap, calibration scope |

`TIMING_RAW` can use a normalized long-form phase table instead of very wide rows.
Record interval inclusion so `graph_compute` and synchronization are not double
counted. Keep warmups even though excluded from the estimate. Distinguish host
completed latency, CUDA-event duration, profiler activity and simulated cycles.

The validity dimensions are independent: a numerical observation can be valid while
its clean timing is invalid; a finite unequal candidate is a valid counterexample
while its preservation qualification is false. Never collapse both into one PASS.
Repeated-process qualification and repeated-input diversity are separate counts.

## Raw evidence and retention

Retain exact input/reference bytes needed to reproduce comparison (deduplicate
immutable CAS), ordinary output bytes for each distinct value plus occurrence
records, diagnostic witnesses, graph/placement metadata, raw timing records,
environment records, source/build/runtime identities, command stdout/stderr and
failure receipts. Full repeated identical arrays may share content-addressed blobs;
every occurrence still needs an explicit hash/size/identity record. Reconstruct
logical order independently from physical padding/strides.

On a mismatch, retain first index, expected/observed bit patterns, sizes, finite
status and available input/intermediate witnesses. A hash mismatch alone is not a
root cause. Error magnitudes/ULP are descriptive; include signed-zero treatment,
near-zero handling and nonfinite counts. Do not turn a tolerance into byte equality.

Follow CONTRIBUTING.md: **do not commit model weights, caches, credentials or raw
telemetry**. This new lane commits source, protocol, generated compact summaries,
manifests and reproducible analysis. Keep large/raw artifacts in an existing
author-approved evidence location; report the actual URI/path, access status,
hashes and retention limits. Do not invent a new external upload service or copy
all historical archives. If only local raw retention is possible, mark
`RAW_LOCAL_ONLY` and the paper reproducibility limitation; valid measured observations
can still be summarized. Remote byte restoration is a reproducibility tier, not a
reason to rerun GPU measurements or to claim a failed measurement passed.

## Analysis and consistency checks

Generate summaries from raw records, never hand-edit scientific CSVs. The analysis
command should detect duplicate/missing IDs, bad geometry, mismatched references,
source drift, unsupported/unplaced arms, invalid timer arithmetic, ineligible pairs,
and accidental pooling of development/confirmation or warmup/measured calls.
Use a small synthetic known-ratio case to check numerator/denominator direction and
weighting; include missing, failed and invalid controls. These CPU checks validate
analysis code, not GPU correctness or scientific results.

Recompute in a fresh directory/process from the retained manifest. Report which
bytes were actually restored, which outputs matched, and which artifacts remain
unavailable. A same-host fresh analysis is not an external audit. A protocol self-
review is not independent review. Do not require a third full raw copy to prove
the same claim; use hashes and selective restore within budget.

## RESULT.md and PR top description

Lead with actual outcome and the earliest unresolved scientific question. Include:

1. Exact source/runtime/reference/lifecycle; design defaults versus actual amendments.
2. D0 observed symptoms, decisive interventions, root cause or unresolved mitigation.
3. Per-stage planned/started/qualified/failed/unsupported/unstarted counts.
4. Numerical envelope and its scope; full geometry and true visible-key coverage.
5. Primary and secondary costs, all regressions, missingness, block sensitivity,
   observer/thermal limitations; no promotion of invalid timing to a speed sample.
6. Mechanism evidence versus inference; model calibration/ref assumptions and fair
   baseline/ideal comparisons if M1 ran.
7. Hardware decision YES/NO/INCONCLUSIVE and exactly what evidence would change it.
8. Runnable commands, generated tables, raw location/hash/restore status, actual
   time/resource costs, cleanup state and next bounded experiment.

Useful terminal labels include `CORE_COMPLETE`, `PARTIAL_QUALIFIED_COST`,
`NUMERICAL_ONLY`, `LIFECYCLE_BLOCKED`, `ENVIRONMENT_TIMING_BLOCKED`,
`NO_PRACTICAL_GAIN`, `HARDWARE_HEADROOM_UNESTABLISHED`, and `MODEL_ONLY`.
Labels are summaries, not substitutes for the tables. A partial but auditable
result is preferable to an all-or-nothing claim or another empty permission loop.
