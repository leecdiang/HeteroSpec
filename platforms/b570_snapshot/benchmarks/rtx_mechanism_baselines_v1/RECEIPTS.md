# Compact analysis contract

`analyze.py` accepts JSONL with one record per attempted **confirm or producer**
timed task. Reference, qualification, capability and profiling have separate
evidence tables. The RTX adapter and auditor must create these records from actual
raw outputs/ticks/metadata; do not hand-author scientific observations.

| Field | Meaning |
|---|---|
| task_id / attempt_id | Exact planned ID / unique actual attempt; no best-of-retry |
| plan_sha256 | Hash emitted by plan.py for the executed plan |
| layout | Actual PQ, QB or QH_C; QB_A/B both execute QB |
| graph_mode | Planned OFF/ON; actual validity is separately established |
| cost_view | resident_graph for confirm; integrated_q_update for producer |
| status | QUALIFIED, NUMERICAL_FAILURE, ENVIRONMENT_INVALID, EXECUTION_FAILED, MODE_UNVERIFIED |
| numerical_qualified | Genuine boolean after independent full-byte/device/completion checks |
| environment_qualified | Genuine boolean from the frozen environmental rule |
| mode_verified | Genuine boolean supported by mode evidence, not requested flag |
| session_id | Actual acquisition session identity |
| measured_us | All30 measured intervals, positive finite numbers, no trimming |
| host_sha256 | Consumed native executable identity |
| runtime_sha256 | Exact numerical module manifest identity |
| policy_sha256 | Common complete policy covering modes/arms, not per-arm telemetry |
| logical_input_sha256 | Canonical logical Q/K/V/mask/scale identity |
| physical_input_sha256 | Actual materialized input/stride manifest for this arm |
| reference_sha256 | Full ordinary byte-reference identity |
| mode_evidence_sha256 | Auditor's actual mode/signature/launch-evidence receipt |
| audit_sha256 | Full numerical/evidence receipt identity |
| failure_reason | Required if failed execution legitimately lacks a final hash |

Hashes are64 lowercase hex characters. Failed attempts may use null missing
hashes with a reason. Qualified observations require complete sample count, true
numerical qualification and verified mode; environment-ineligible observations
remain in coverage but are excluded from timing pairs. Do not assert ON if its
requested configuration fell back. Such a host has MODE_UNVERIFIED and is retained.

All modes and arms in one stage share executable/runtime/policy identities.
Logical/reference identities are fixed per case across modes/arms/blocks; physical
identity is fixed for each arm across modes/blocks. Producer compact/permuted arms
have the same logical values but different physical bytes/strides. Timed cases
must match the frozen plan; no q4 or new geometry silently masquerading as q2.

The compact checker cannot authenticate these hashes or compare raw graph
signatures. The separate auditor must check source/runtime freeze, exact inputs,
canonical references, every raw output occurrence, actual CUDA placement, completion,
graph mode, sampler counts and order. Retain warmups/capture work outside the
measured_us list, with all ticks and costs. A successful compact check alone is
not evidence that a GPU ran or a graph was captured.

Each case/block/mode needs all four eligible arms for paired summaries. Both
OFF and ON sub-blocks are needed for an ON/OFF contrast. Both value realizations
are needed for a geometry block. Missing or failed inputs never silently change
geometry weights. The helper reports every expected timed slot, including optional
UNSTARTED slots, with per-case and geometry statistics; it intentionally avoids
a grand average mixing q1, length boundaries, storage contrasts and producer work.

Bootstrap resamples whole acquisition blocks inside actual sessions, never inner
calls. Eight blocks/two sessions are conditional replication, not independent
days or a device population. Four-block or one-session results remain descriptive.
Factor ratios are ratios-of-ratios; their difference_us is a difference of mapping
time differences. They do not measure a named kernel or causal bandwidth effect.

The executor adds readable tables: CAPABILITY, NUMERICAL_COVERAGE, MODE_EVIDENCE,
HOST_COSTS (including mean/median/p95/max), MODE_CONTRASTS, MAPPING_CONTRASTS,
FACTOR_CONTRASTS, TRACE_SUMMARY, PRODUCER_TRANSACTIONS and FAILURES. A table can be
UNAVAILABLE/UNSTARTED with scope and reason. Keep valid independent outputs if a
later CPU report/retention step fails; fix exports from retained raw without GPU
reruns. Report actual telemetry limitations and raw location/restore status.

For graph replay amortization, report measured one-time capture/instantiate cost
and steady replay savings separately. If calculating a break-even invocation count,
use the matching mode pair and explicit formula; nonpositive steady savings have
no finite amortization point. This is a conditional estimate, not a measured
natural request benefit or hardware upper bound.
