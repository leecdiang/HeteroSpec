# New host-adapter contract (schema1)

The original schema below is now produced by the 2026-10-28 host implementation.
Its build and execution status are tracked in [HOST_EXECUTION.md](HOST_EXECUTION.md)
and retained receipts. This does not retroactively change the original CPU review
into a review of native results.

**This format is a required extension, not the current rtx_bridge output.** Its native producer/adapter is `NATIVE_EXTENSION_REQUIRED`; the submitted study is `NOT_RUN`. `study.py audit/analyze` implement CPU validation of this envelope. Positive acceptance against real native payloads remains untested until the host implementation exists. The diagnostic stream is separate: the factorial auditor must not ingest its54 slots as performance observations.

## Bundle files and synthetic exclusion

The bundle contains `EXECUTION_IDENTITY.json`, `REFERENCES.json`, `ATTEMPTS.json`, `REQUESTS.jsonl` and original raw payloads. All paths inside payload pins are relative to the bundle, without `..` or external symlink escapes. Each payload pin is `{path, bytes, sha256}`; vector pins also have `name` and `dtype`. Missing bytes are a failure, not a reconstructed observation.

Every execution binding and started request has an explicit Boolean `is_synthetic`. The real auditor requires **exactly false**. Any true fixture marker, missing/native-unbound identity, missing source reference or missing request data prevents qualified performance. Synthetic fixtures in `test_cpu.py` exercise arithmetic and rejection only; they are not saved as experiment records. The public analyzer always re-audits the bundle and does not accept a caller-supplied `eligible=true` shortcut.

## Execution identity

Start from the committed template. The status must become `FROZEN_BEFORE_FIRST_NATIVE_REQUEST` before execution. Bind:

- Schema/study ID and exact PLAN/PANEL/SLOTS SHA256.
- `frozen_utc`, `date_timezone: Asia/Shanghai`, and three increasing actual local calendar dates.
- Positive resource caps: worker timeout, total owned seconds, payload bytes and minimum free bytes. Nulls are not admitted.
- Per family: exact source variant/archive, target/draft model `{sha256,bytes}`, vocabulary/template hash, executable/core/worker-source/build-receipt hashes, all21 numerical module names and hashes, host/device/driver identity and the full `PLAN.json` context contract.

Do not replace the historical21-module manifest with a list inferred from whatever DLLs happen to load. Actual loaded paths/hashes and source/build receipts must be retained. Their normalized identity is repeated in each request and in its raw native record. Source routing is fixed: Qwen-original; Smol/Llama-metadata4. A cohort cannot switch executables across arms.

## Historical references

`REFERENCES.json` has an `endpoints` object keyed by each `reference_id` in PANEL/SLOTS. Each entry contains:

- `source_commit` equal to the pinned PR144 commit; `source_kind: PR144_HISTORICAL_R`.
- `raw_payload`: the original historical R record's relative path, size and hash, linked to the already delivered source/shard inventory. Preserve that inventory and provenance; a newly generated R record is not a historical source.
- `endpoint_key_path`: a list of object keys leading from that original JSON to its endpoint object, such as `['output']` when appropriate. Inspect the actual source format; do not guess it.
- `endpoint`: complete `ids`, `eog`, `length`, `terminal_id`, `stop_reason`. The auditor re-reads the raw payload, accepts its original `eog_flags` spelling when present, and checks equality.

The requirement file does not invent missing R outputs. Bind and independently review these old endpoints before new native execution. Old numerical failures and raw reference bytes remain unchanged.

## Attempt receipts

`ATTEMPTS.json` is a list. Each owned process receipt has `attempt_id`, `unit_id`, `attempt_index`, `family`, `date_slot`, `session_slot`, `pid`, `process_start_utc`, `process_end_utc`, `status`, and `cleanup_verified`. Units match the schedule: `qualification/FAMILY` or `formal/dD/sS/FAMILY`. A new process and model load belongs to each formal family-session; PID reuse is permitted only with a different process-start identity.

Attempt0 is mandatory. Attempt1 is allowed only for a technical failed formal session, at most once per unit and twice overall. It restarts the whole91-slot session on the same local study date. Earlier rows, failures and explicit NOT_RUN causes remain in the bundle. Any numerical failure forbids technical retry. Qualification has no automatic retry. Receipt times must be ordered, bounded and nonoverlapping; all owned workers must have verified cleanup.

The source record order within each attempt equals the frozen slot order. A completed unit contains every planned row; partial attempts are never merged. A family missing a qualified unit cannot produce the planned finite-panel estimate.

## Request envelope

Every row repeats the frozen slot's study/slot/unit/stage/family/input IDs, prompt-ID hash, reference ID, date/session/block, arm/scope/selector, scoped-target flag, target UB/output capacity, draft switch/k, lifecycle, observer and producer. It also contains:

- `schema:1`, `is_synthetic:false`, `attempt_id`, `started`, `status`, `pid`, `process_start_utc`, `request_start_utc`, `request_end_utc`.
- Formal/warmup rows: `date_timezone:Asia/Shanghai`, `actual_date` equal to the Shanghai date derived from both UTC request timestamps and the frozen calendar slot. Session processes must not cross local midnight.
- `identity`: exact per-family execution binding, observed from the executing binary/modules/model admission.
- `context`: every `PLAN.json` context field plus actual `target_ub` and `target_outputs` for this arm; `observed_scope`, `context_scope_fixed:true`, actual `prompt_tokens` and prompt hash.
- `endpoint`: full `ids`, Boolean `eog`, `length`, `terminal_id`, `stop_reason`. No continuation after EOG; CAP requires128 outputs. Do not replace false/unknown with missing or pass.
- `cycles`, `target_final_kv`, `draft_final_kv`, `draft_calls` with the semantics below.
- Positive finite `service_seconds` and the exact `service_timer_definition` from PLAN. Retain request-window, setup, teardown, model-load and provisioning clocks separately with their definitions; exclusive GPU time is null when no GPU timestamps exist. Only formal observer-off records enter performance estimates.
- `physical_widths`: actually observed target micrograph widths; `geometry`: actual target tensor metadata. Heavy qualification requires these; they are not filled from requested UB. Retain phase-specific full histograms/metadata in the raw record.
- `raw_native_record`: original native JSON pin; the auditor compares its identity, endpoint, state, context, geometry, widths, prompt identity and service time with the envelope.
- `raw_vectors`: heavy-only complete vector inventory, described below. Off records retain an empty inventory, not synthesized vectors.

NOT_RUN rows have `started:false`, a precise nonempty `reason` and `failure_id` identifying the blocking cause. They have no fabricated endpoint/time. A numerical mismatch retains its actual endpoint/raw evidence and a failure status. Such rows stay in the plan accounting but cannot qualify for timing. They are not removed to satisfy the exact completed-row validator.

## State and raw vectors

Target-only R/M has an empty cycle list, zero draft calls and null draft KV. For C, retain the existing bridge's cycle fields: `cycle`, `base`, `seed`, all three `proposals`, all four `decisions`, `caller_rows`, `accepted`, `rejected`, `commit_kind`, `output_length`, `pending_after`, `done`, `keep`, and before/after target/draft KV bounds. The auditor reconstructs the committed endpoint, rejection/bonus/terminal behavior and trim boundary. Unexamined verification rows cannot be omitted simply because they were not committed.

Heavy-vector canonical names match actual bridge captures: `target/initial.f32`, every `target/ordinary-N.f32` for a target-only continuation, and every `draft/proposal-CYCLE-J.f32` plus `target/verify-CYCLE-J.f32` for speculation. Each is full-vocabulary float32 with exactly `4*vocabulary_tokens` bytes. The actual file path may differ, but canonical names must be unique and the complete required inventory must match. The CPU audit hashes each retained file and compares PQ/QB name/size/hash inventories. A missing counterpart is not equality.

Actual geometry retains `name`, `ne`, `nb` and device text as in the inspected observer. The new observer must cover prefill/ordinary as needed for M as well as VERIFY for C. Local prefixes are `hs_attention_q-` for PQ and `hs_attn_query_batch-` for QB; all family target layers and correct head axis must be observed. PQ's query slot is one; QB must show the actual batched axis when verification occurs. GS/R target physical widths must be one. Requested geometry and a generic `correct:true` Boolean do not satisfy these checks.

For every input, the sentinel off/on trajectories and PQ/QB state/vector claims are audited separately from endpoint equality. GS/PQ/QB unequal natural cycles with equal endpoints retain complete-request interpretability but set `logical_work_equal:false` and prohibit pure execution-cost attribution. No result from this schema supplies a missing CUDA Graph event ledger, operator replay sham or cross-layout producer-state intervention.
