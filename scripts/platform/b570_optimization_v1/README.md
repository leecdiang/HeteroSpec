# CPU guards and host integration

These tools do **not** launch inference or certify an unreviewed native implementation. B570's execution agent must restore #82, implement the resident driver/controller, collect actual receipts, independently inspect the bound native evidence, and freeze it before forward/confirmation as the protocol requires. Fixtures are explicitly synthetic, not experiment records.

From the repository root (Python 3.11+, standard library only):

```powershell
python -m unittest discover -s scripts/platform/b570_optimization_v1 -p 'test_*.py' -v
python scripts/platform/b570_optimization_v1/plan.py plan --output local/b570-opt/static-plan.json
python scripts/platform/b570_optimization_v1/plan.py assets --input local/b570-opt/asset-paths.json --output local/b570-opt/asset-check.json
python scripts/platform/b570_optimization_v1/plan.py host --input local/b570-opt/HOST_FACTS.json --output local/b570-opt/host-check.json
python scripts/platform/b570_optimization_v1/plan.py select --input local/b570-opt/discovery.json --output local/b570-opt/selection.json
python scripts/platform/b570_optimization_v1/plan.py confirm --input local/b570-opt/confirmation.json --selection local/b570-opt/selection.json --output local/b570-opt/decision.json
```

`asset-paths.json` maps ASSETS keys to real full GGUF paths. Full hashing is intentionally run on B570 before inference, not on the active RTX machine. A passing asset check does not verify runtime vocabulary.

HOST_FACTS fields and evidence roles are defined by `host_check` and exercised by the synthetic fixture tests. `evidence` is an array of `{role,path,bytes,sha256}`; paths are relative to the receipt directory. Required files include actual native source, binary, numeric module manifest, load log, vocab dump, memory trace, boundary/capture/reset log. The checker confirms bindings and declared invariants; the execution agent must review source/logs, not manufacture true flags. Attach full local asset-check receipts, restore receipts, actual remote-freeze receipts and independent review in the result archive.

Discovery input: `discovery_tasks` (six of each domain), all `records`, candidate table with `candidate_id`, `matched_arm` (`M_native_greedy`/`M_vulkan_batched_repair`), `gate_status` and `peak_bytes`; bound `evidence` plus `independent_native_review_status=PASS`. Unsupported/failed/incomplete candidates remain in the table. Every tested candidate needs its own gate receipt and full records in the published archive. Records have session (discovery repeat0/1), round0, arm, task_id, status, whole_request_seconds, cap128, committed_ids, runtime_eog_flags, length, terminal_id, stop_reason (`EOG`/`CAP`), prompt_ids_sha256. Stock UB128 must be complete and stable; optional ordinary settings need the same full-panel qualification to be eligible, and every excluded setting remains reported. No output slicing occurs.

Both discovery and confirmation CLI checks require hash-bound evidence roles `native_gate_receipts`, `request_ledger`, `remote_freeze_receipt`, `asset_checks`, `history_audit`, `raw_records`. Confirmation input additionally binds `candidate_id`, `ordinary_ub`, full `historical_and_rtx_reserved_ids`, `history_audit_status=ACTUAL_FULL_HISTORY_AUDITED`, `f0b_remote_status=ACTUAL_GIT_BLOBS_VERIFIED`, 24 confirmation_tasks and the full 768 paid matrix. The checked-in BASE_EXCLUSIONS minimum is always enforced, even if the caller omits it; extend it with full host history. A passing calculation is conditional on independently verified implementation, real source/asset provenance and pre-forward remote seals. These text flags alone do not prove their chronology: publish the ledger, Git receipts and native logs.

Integrate `native_memory_budget.h` into the **same resident worker process**. It requires a real Vulkan physical-device handle and the advertised VK_EXT_memory_budget extension. Log PID, exact device/heap mapping, timestamps, budget and usage with loader/source hashes at load and throughout engineering. The header reports device-local heaps; B570 must independently establish those are its dedicated heaps, and absence of shared spill. A separate process has a different usage scope. No local Vulkan SDK compilation was performed for this design PR.

The execution agent's controller must add START/COMPLETE ledger, strict budgets, hash/freeze validation, real inference, independent archive restoration, and final PR delivery. Until those are implemented and exercised on B570 this directory is **a validated planning/analysis toolkit, not an already running experiment**.
