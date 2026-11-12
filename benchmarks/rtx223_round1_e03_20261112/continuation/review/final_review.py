"""Independent e02 identity/raw ledger audit. No models, CUDA or GPU calls."""
from pathlib import Path
import ast
import datetime
import hashlib
import json
import sqlite3
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def main():
    out = HERE / "FINAL_INDEPENDENT_REVIEW.json"
    need(not out.exists(), "fresh independent final receipt required")
    result = {"schema": "heterospec.e02.independent-final-review.v1", "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "models": 0, "GPU_kernel_launches": 0, "native_GPU_program_invoked": False, "producer_verifier_imported_for_raw_audit": False, "old_41_tests_rerun": False}
    parent = read(ROOT / "continuation/PARENT_BINDING.json")
    archive = ROOT.parent / "HeteroSpec_RTX221_Round1_20261112_v2.zip"
    need(sha(archive) == parent["original_delivery_zip_sha256"], "parent archive changed")
    with zipfile.ZipFile(archive) as z:
        manifest_raw = z.read("delivery/DELIVERY_MANIFEST.json")
        need(hashlib.sha256(manifest_raw).hexdigest() == parent["parent_manifest_sha256"], "parent manifest identity")
        manifest = json.loads(manifest_raw)
        members = manifest["files"]
        need(len(members) == 165, "parent file count")
        for item in members:
            p = ROOT / item["path"]
            original = Path(parent["parent_source"]) / item["path"]
            need(p.stat().st_size == item["bytes"] and sha(p) == item["sha256"], "copied parent changed: " + item["path"])
            need(original.stat().st_size == item["bytes"] and sha(original) == item["sha256"], "old e01 source changed: " + item["path"])
    result["parent_preservation"] = {"original_and_copied_files_independently_rehashed": len(members), "archive_sha256": sha(archive), "parent_manifest_sha256": parent["parent_manifest_sha256"], "old_epoch_unchanged": True}
    safety = read(HERE / "safety-independent-v1/RECEIPT.json")
    need(safety["pass"] and all(r["tests"] == 18 and r["returncode"] == 0 for r in safety["test_runs"]), "independent safety tests")
    for path, h in safety["source_sha256"].items():
        need(sha(ROOT / path) == h, "reviewed safety source changed")
    raw_ledgers = []
    keys = ("model_requests", "target_draft_rows", "native_gpu_seconds", "kernel_launches", "capture_bytes")
    for mode in ("normal", "optimized"):
        base = HERE / "safety-independent-v1/raw" / mode
        paths = sorted(base.glob("*/ledger.sqlite"))
        need(len(paths) == 18, "all CPU OS ledgers retained")
        for path in paths:
            db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
            family = db.execute("SELECT id,parent,stop_reason FROM family").fetchone()
            need(family[0].startswith("CPU-TEST-"), "real budget family touched by OS fixture")
            charged = json.loads(family[1])
            rows = db.execute("SELECT id,status,reserved,actual,pid,creation,reason FROM attempts").fetchall()
            attempts = []
            for attempt, status, rtext, atext, pid, creation, reason in rows:
                reserved, actual = json.loads(rtext), json.loads(atext) if atext else {}
                for key in keys:
                    charged[key] += max(reserved[key], actual.get(key) or 0)
                if status == "COMPLETE":
                    need(all(actual.get(key) is not None for key in keys), "unknown COMPLETE survived")
                else:
                    need(family[2] is not None, "failure did not stop family")
                if status == "OVERRUN":
                    need(actual["kernel_launches"] == 1, "synthetic observed overrun lost")
                    need(charged["kernel_launches"] == 1, "synthetic overrun not charged")
                attempts.append({"id": attempt, "status": status, "reserved": reserved, "actual": actual, "pid": pid, "creation": creation, "reason": reason})
            db.close()
            raw_ledgers.append({"path": str(path.relative_to(HERE)), "sha256": sha(path), "fixture_family": family[0], "charged": charged, "stop_reason": family[2], "attempts": attempts})
    (HERE / "OS_RAW_LEDGER_AUDIT.json").write_text(json.dumps({"scope": "synthetic own CPU test families, never study GPU usage", "ledgers": raw_ledgers, "producer_ledger_code_imported": False}, indent=2), encoding="utf8")
    result["windows_safety"] = {"independent_test_receipt": "safety-independent-v1/RECEIPT.json", "test_counts": [18, 18], "raw_ledgers_read_independently": len(raw_ledgers), "raw_ledger_audit_sha256": sha(HERE / "OS_RAW_LEDGER_AUDIT.json"), "actual_GPU_lock_used": False, "scope": "Own CPU-TEST mutex/file/Job/deadline mechanisms; original-thread clearance remains separate"}
    gate_source = (ROOT / "continuation/safety/windows_runner.py").read_text(encoding="utf8")
    tree = ast.parse(gate_source)
    need(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)), "safety guard removable by -O")
    gate_values = [node.value.value for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CURRENT_NATIVE_GATE" for t in node.targets) and isinstance(node.value, ast.Constant)]
    need(gate_values == ["BLOCKED_ORIGINAL_THREADS_UNVERIFIED"], "current native gate unexpectedly released")
    frontend = ROOT / "continuation/frontend"
    recipe = read(frontend / "HOOK_SOURCE_v5.json")
    source = frontend / "hooked_frontend_v5"
    for name, h in recipe["files"].items():
        need(sha(source / name) == h, "frontend source recipe mismatch: " + name)
    build_path = frontend / "hooked-build-v4/BUILD.json"
    build = read(build_path)
    need(build["status"] == "COMPILED_LINKED_NOT_NATIVE_QUALIFIED", "frontend build status")
    for name, h in build["source_hashes"].items():
        need(sha(source / name) == h, "compiled frontend source mismatch")
    for path, h in build["linked_input_identities_before_and_after"].items():
        need(sha(path) == h, "linked input changed")
    selftests = read(frontend / "hooked-build-v4/HOST_SELFTEST.json")
    need(selftests["build_receipt_sha256"] == sha(build_path), "host selftest build changed")
    for item in selftests["records"]:
        core = item["core"]
        need(item["returncode"] == 0 and item["passed"], "host selftest failed")
        need(sha(item["argv"][0]) == item["exe_sha256"] == build["builds"][core]["exe_sha256"], "host selftest executable identity")
        log = frontend / "hooked-build-v4" / (core + "-selftest.log")
        need(sha(log) == item["log_sha256"], "host selftest log changed")
        need(read(log) == item["result"], "host selftest raw result")
        need(item["result"]["models"] == 0 and item["result"]["CUDA_calls"] == 0 and item["result"]["backend_initializations"] == 0, "host selftest scope")
    worker = (source / "worker.cpp").read_text(encoding="utf8")
    need(worker.index('if(life=="fresh"){target=nullptr;draft=nullptr;}fresh.draft.reset()') < worker.index("transaction.complete=true"), "fresh owner UAF fix missing")
    entry = (source / "entry.cpp").read_text(encoding="utf8")
    actual_main = entry[entry.index("int main("):]
    need(actual_main.index('std::string(argv[1])=="--selftest"') < actual_main.index("llama_backend_init"), "selftest is not before backend initialization")
    result["frontend"] = {"source_members": len(recipe["files"]), "build_sha256": sha(build_path), "host_selftests": 2, "linked_inputs_independently_rehashed": len(build["linked_input_identities_before_and_after"]), "fresh_transaction_UAF_fix_source_checked": True, "native_model_state_or_cost_qualification": "NOT_RUN", "source_recipe_status_is_prebuild_metadata": True}
    native = ROOT / "continuation/native"
    status = read(native / "STATUS.json")
    for name, h in status["receipt_files"].items():
        need(sha(native / name) == h, "native preparation receipt mismatch: " + name)
    matrix = read(native / "NATIVE_MATRIX.json")
    need(matrix["cells"] == 66 and len(matrix["records"]) == 66, "native matrix size")
    need({row["native_result"] for row in matrix["records"]} == {"NOT_RUN"}, "native results misclassified")
    obuild = read(native / "operator-v3/build-v1/BUILD.json")
    need(obuild["returncode"] == 0 and obuild["execution_enabled"] is False, "operator execution enabled or build failed")
    need("-DHS_NATIVE_EXECUTION_ENABLED=0" in obuild["command"], "operator compile gate missing")
    need(sha(native / "operator-v3/build-v1/operator_probe.exe") == obuild["executable_sha256"], "operator binary identity")
    for name, h in obuild["source_sha256"].items():
        need(sha(native / "operator-v3" / name) == h, "operator compiled source mismatch")
    op = (native / "operator-v3/native/operator_probe.cu").read_text(encoding="utf8")
    need(op.rindex('result["kernel_launch_attempts"]=counts.attempted') > op.index("catch(const std::exception"), "failed launch accounting not retained")
    need('capture_bytes_known?json(capture_bytes):json(nullptr)' in op and "attempted_capture_paths" in op, "failed capture bytes claim false zero")
    backend = read(native / "backend-build-v1/BUILD.json")
    need(backend.get("returncode", backend.get("code")) == 0, "patched MMVQ compile failed")
    result["native_preparation"] = {"operator_build_sha256": sha(native / "operator-v3/build-v1/BUILD.json"), "operator_binary_execution": "DISABLED_NOT_INVOKED", "failed_launch_and_capture_byte_paths_reviewed": True, "MMVQ_compile": "PASS_TRANSLATION_UNIT_ONLY", "new_numerical_DLL_link_load": "NOT_RUN", "full_model_kernel_limit": "NOT_IMPLEMENTED", "native_qualification_cells": 66, "native_results": "ALL_NOT_RUN", "current_actual_q8_capture": "NOT_RUN", "A_B_C_bytes_and_timing": "NOT_RUN"}
    dedup = read(ROOT / "continuation/dedup/DEDUP_RESULT.json")
    need(dedup["verdict"] == "INCONCLUSIVE" and dedup["process_inventory"]["host_scope_verified"] is False, "dedup overclaim")
    need(all(t["current_terminal_evidence"] is False for t in dedup["local_app_catalog"]["candidate_threads"]), "catalog mistaken for execution evidence")
    for ledger in dedup["legacy_ledgers"]:
        need(sha(ledger["path"]) == ledger["expected_sha256"], "legacy ledger changed")
    need(sha(dedup["parent_epoch_ledger"]["path"]) == dedup["parent_epoch_ledger"]["sha256"], "parent e01 ledger changed")
    result["dedup_and_legacy"] = {"dedup_receipt_sha256": sha(ROOT / "continuation/dedup/DEDUP_RESULT.json"), "original_thread_terminal_evidence": "UNAVAILABLE", "host_process_inventory": "RESTRICTED_NAMESPACE_ONLY", "legacy_and_parent_ledgers_rehashed": 4, "native_gate": "BLOCKED"}
    result["findings_recheck"] = {"S1": "Current native gate hard-blocks receipt self-sealing; future authority protocol still required", "S2": "Deadline checked after exit query and before accepting completion; new regression passes", "S3": "COMPLETE unknown actuals becomes durable COUNTER_INVALID; new regression passes", "S4": "Observed overrun persisted/charged; synthetic overrun raw ledger independently checked", "S5": "Preassignment own-child cleanup regression passes with OS birth/absence evidence", "F1": "Fresh raw owner pointers cleared before destruction; final compiled source bound", "N1": "Failure raw output paths measured after catch; unknown bytes represented as null/lower-bound"}
    result["gate_table"] = {"parent_preservation": "PASS_165_FILES", "Win32_CPU_containment": "PASS_18_EACH_MODE", "frontend_compile_link_host_selftest": "PASS_PREPARATION_ONLY", "dedup_clearance": "BLOCKED", "full_model_graph_quantizer_kernel_budget": "BLOCKED_NOT_IMPLEMENTED", "actual_q8_full_output_state_qualification": "NOT_RUN", "real_bonus_seed_L4_correction_continuation": "NOT_RUN", "paired_C_over_packed_improvement": "NOT_RUN", "complete_service_cost_net_benefit": "NOT_RUN", "round2": "DO_NOT_START"}
    result["decision"] = "INCONCLUSIVE"
    result["review_verdict"] = "NEW_PREPARATION_PASSED_REVIEW_WITH_NATIVE_GATES_CLOSED"
    out.write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps({"decision": result["decision"], "review_verdict": result["review_verdict"], "parent_files": 165, "raw_OS_ledgers": len(raw_ledgers), "native_cells": 66, "gate_table": result["gate_table"]}, indent=2))


if __name__ == "__main__":
    main()
