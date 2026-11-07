# Prospective CPU8 closure protocol

Status: DESIGN_ONLY. No existing acceptance criterion is waived. This is a new task/campaign with a new UUID; the exhausted PR119 campaign stays closed. A fresh allowance is not a reset of its historical ledger.

## 1. Scope and traceability

Start from pinned PR119 `aa7d64b5e4c198699a2f1fcc52c8ff2e31103fa7`. Create new implementation/results directories under `benchmarks/b570_cpu8_closeout_v6/`. Record new campaign origin before its first preparation process. Copy and hash required source; never overwrite old evidence. Retain original acceptance predicates and the qualified native supervisor. Changes are limited to verifier-role separation, delivery tool binding, prospective budget admission, and their integration/tests.

Before execution, write a traceability table mapping every inherited mandatory gate to its new artifact and source hash. Prior results are historical evidence only. Rerun required native gates in the new deployment; use impact-directed regression for unchanged non-mandatory tests. No new 3-hour soak, full 19-case/57-slot suite, or GPU workload is required by this CPU8 protocol. Do not label this subset ENGINEERING_READY.

## 2. Two verifier roles

`live`: original run root, canonical filesystem identity checked, current process and storage admission unconditionally enforced, deployed source/freeze/tool/native evidence all verified. No relocation flag may weaken these checks.

`reconstruct`: read-only recomputation at either original or restored root. Returns RECONSTRUCTION_ONLY plus explicit table/hash comparison results. It cannot produce a live admission token or CPU8_INTEGRATION_PASS. Historical at-seal budget snapshots remain historical fields.

Portable `role_guard` is not sufficient against filesystem aliases; retain native reparse/hardlink/root identity protections. Portable `final_gate` accepts derived booleans solely as internal composition results: never load these booleans from CLI or receipt JSON. The production auditor must call the original raw/native/freeze/current-resource validators itself. If that composition is absent, this proposal is not integrated.

## 3. Bind actual delivery operations

Freeze an intent before each download and restore invocation. Retain the actual tool request and all responses, provider call identifiers, execution session identifiers, terminal exit/output, and their capture index. The capture supervisor records the index outside candidate-owned receipt generation; retain raw provider exports alongside any normalized records. This establishes auditable consistency, not independent external certification. A receipt writer must not be able to fabricate both transcript and trusted index unnoticed.

For downloads, bind the actual repository URL/ref to an immutable commit and blob ID, actual returned encoded payload to decoded chunk bytes, chunk ordering/membership to the archive digest, and archive bytes to the restored manifest. Validate both SHA256 and Git blob identity. A local file with the right digest or a transport-name string alone is insufficient. `bind_download` only implements the content check; the platform must supply and validate the provider-operation binding.

For restore, bind the actual frozen interpreter/argv/workdir/environment, isolated import flags, unmodified driver hash, original session through final terminal response, OS process identity/closure, and actual output report bytes. Compare report bytes with the frozen expected recomputation. No `exit_code: 0` or `isolated_import: true` self-declaration suffices. Reuse the existing watchdog tool-binding implementation. If provider exports are unavailable, report DELIVERY_PENDING; do not fabricate provenance or rerun formal cases to hide the gap. Remove secrets from archival material without dropping identity fields needed for verification.

Required targeted negatives: relocation on original root and copied root cannot emit live PASS; forged exit/isolated fields; wrong command/session/terminal exit; missing poll completion; changed downloaded payload/blob/commit binding; fabricated capture index from candidate path; absent native result; missing eighth case. Include one real download and real isolated restore positive path before final source freeze. These are engineering checks, not formal CPU8 slots.

## 4. Protected cumulative budget

Retain inherited limits: 21,600 cumulative process-lifetime seconds, 21,600 wall seconds, 3,000 starts, storage/link/copy accounting and minimum free-space constraints. Record actual known process lifetimes and conservative charges for uncovered intervals; UNKNOWN never means zero. Keep the full-task OS ledger UNKNOWN unless independently resolved.

| Stage | Protected lifetime for later stages | Protected wall for later stages |
|---|---:|---:|
| Development, deployment and final review | 7,200 s | 3,600 s |
| Frozen formal CPU8 acceptance | 3,600 s | 1,800 s |
| Delivery and closure | 0 | 0 |

Thus development plus its next operation must fit within 14,400 charged lifetime seconds, leaving 3,600 for acceptance and 3,600 for delivery. These are reservations, not proof the work fits. Estimate all eight formal cases and actual remote delivery before freeze; increase their reservations prospectively if their conservative bounds exceed these defaults, reducing development room. Never reduce a reservation merely to admit development. Reserve sufficient process starts, storage/export bytes and cleanup headroom using the inherited guards as well.

Before every operation, use integer-ceiling charges and a conservative next-operation envelope including children, polling, cancellation and cleanup. `reserve()` is a pre-admission arithmetic helper, not a running watchdog. The native adapter must enforce cumulative consumption during the operation and terminate within the admitted envelope while preserving later-stage reserves. If no enforceable bound exists, do not admit that operation. Stage transitions never reset origin or charges.

Do not repeat the known 240-second review timeout blindly. Set review scope and timeout from observed previous duration, available charged headroom and enforceable process limits. Review the entire deployed live/delivery composition at exact hashes. One repair cycle may be attempted only if its complete regression/review/cleanup envelope fits. A timed-out, partial or stale review is not clean. If development cannot finish, stop early with PATCH_READY_FOR_REVIEW or ENGINEERING_BLOCKED and an actionable artifact, preserving the reserved budget; do not spend it on endless reviews.

## 5. Freeze, execute exactly eight cases once

Freeze source inventory, native adapter, helper imports, gate artifacts, final scoped clean review, intents, case order and budget bounds. Dynamic/unhashed imports invalidate the freeze. Adapt hard-coded old gate filenames transparently in the new implementation and record the mapping; never fabricate old artifacts. No mutable code edits after freeze.

| Order | Case | Required terminal result | Trigger |
|---|---|---|---|
| 1 | normal_single | NORMAL_COMPLETE | normal |
| 2 | normal_transition | TRANSITIONS_COMPLETE | eight pairs / sixteen unique slots |
| 3 | terminal_pending_completion | SEALED_WRITE_REJECTED | SEALED_WRITE_DURING_CLOSE |
| 4 | frozen_input | SEALED_WRITE_REJECTED | WRITE_FROZEN_INPUT |
| 5 | late_closed_slot_write | SEALED_WRITE_REJECTED | WRITE_CLOSED_SLOT_A |
| 6 | resource_read_failure | RESOURCE_READ_REJECTED | FAIL_RESOURCE_READ |
| 7 | directory_read_timeout | COVERAGE_GAP_REJECTED | STALL_DIRECTORY_READ |
| 8 | journal_write_failure | JOURNAL_FAILURE_REJECTED | FAIL_JOURNAL_WRITE |

Expected faults qualify only when the frozen intended detector and original raw audit predicates pass, including actual process identities, cleanup, handles and job closure. An unrelated early error is not a successful negative test. Record started/completed/qualified independently. Stop on unexpected formal failure or resource/coverage failure, retain the partial campaign, and do not retry that scientific/formal coordinate under a renamed slot. Engineering tests before freeze are separately labeled and retained.

## 6. Delivery and states

After eight qualified cases, preserve immutable case artifacts and report CPU8_CASES_PASS_DELIVERY_PENDING until actual remote restore, byte recomputation and tool binding complete. Delivery may continue within the same open campaign and reserved budget without rerunning cases. If the UUID is permanently closed, any later delivery audit uses a new delivery-only task, references immutable original case evidence and does not claim a resumed live campaign; its reconstruction cannot retroactively change the original live verdict.

CPU8_INTEGRATION_PASS requires current live checks, all eight original native predicates, exact deployed clean review/freeze and bound delivery evidence. Do not emit F0 before the original required predicates are satisfied. Report ENGINEERING_BLOCKED before formal start, FORMAL_FAILED/PARTIAL when appropriate, or delivery pending distinctly; never collapse eight qualified cases into 0/8 because upload is pending.

Final report: source/executable mapping (UNKNOWN if unresolved), exact eight-case table, failures and exclusions, actual calls and process coverage, charged and observed budgets, current-versus-at-seal resource checks, remote archive identity/restoration receipts, remaining unknowns. Keep Draft, no automatic merge, no GPU/model/actor/RTL. CPU8 PASS only opens a separate research-design decision.

## 7. Permitted implementation discretion

The Windows operator may adjust paths, tool adapters, archive chunk size, reasonable timeouts and ordering of pre-freeze engineering checks within the same contracts and reserves. Record decisions and freeze them before formal execution. A small packaging or transport issue may be repaired during delivery without modifying frozen execution evidence; changed analysis code requires a distinct versioned audit, never silently replacing the original. Changes to expected results, safety gates, formal coordinates, or resource ceilings require a new explicit protocol, not an improvised exception.
