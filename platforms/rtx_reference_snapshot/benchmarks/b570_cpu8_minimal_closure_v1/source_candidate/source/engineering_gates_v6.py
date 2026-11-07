"""Prospective C engineering evidence; old A regression IDs are never promoted."""
import hashlib
import json
import re
from pathlib import Path
from operation_roles_v7 import operation, rel


def need(v, reason):
    if not v:
        raise ValueError(reason)


def load(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(root):
    root = Path(root).resolve()
    campaign = load(root / "CAMPAIGN.json")
    binding = load(rel(root, "ENGINEERING_GATE_BINDING.json"))
    need(binding.get("schema") == "B570_C_ENGINEERING_BINDING_V2"
         and binding.get("task_uuid") == campaign.get("task_uuid")
         and campaign.get("task_uuid"), "wrong C engineering task")
    # C's native compiler/load proof is a fresh operation, never 'compile-v6-2'.
    operation_id, op = operation(root, "C-compiled-identity", "C", "native_build_or_load")
    from delivery_binding_v6 import invocation
    result = invocation(root, operation_id, op["argv"],
                        rel(root, "operations/" + operation_id + "/stdout.log"))
    need(result["status"] == "ACTUAL_PROVIDER_RESTORE_BOUND",
         "current native tool chain not bound")
    build_path = rel(root, binding["build_record"])
    build = load(build_path)
    source = rel(root, "legacy/repo/benchmarks/b570_supervision_fix_v2/host/LauncherCapture.cs")
    dll = rel(root, binding["compiled_dll"])
    need(build.get("source_sha256") == sha(source)
         and build.get("dll_sha256") == sha(dll)
         and build.get("candidate_task_uuid") == campaign["task_uuid"],
         "compiled/source/current task identity")
    need(build.get("provenance") in ("CURRENT_NATIVE_BUILD", "B_NATIVE_LOAD_VALIDATED"),
         "historical build alone cannot qualify")
    if build["provenance"] == "B_NATIVE_LOAD_VALIDATED":
        b_file = rel(root, binding["b_entry_proof"])
        proof = load(b_file)
        need(proof.get("status") == "ENTRY_ADMITTED"
             and proof.get("dll_sha256") == build["dll_sha256"]
             and proof.get("source_sha256") == build["source_sha256"]
             and sha(b_file) == binding["b_entry_proof_sha256"],
             "pinned B native proof drift")
        # Its real provider/OS provenance is authenticated separately by C's admission.
    else:
        event_path = rel(root, binding["compiler_os_events"])
        data = event_path.read_bytes()
        need(data.endswith(bytes([10])), "partial native compiler journal")
        events = [json.loads(x) for x in data.splitlines()]
        need(build.get("compiler") in events and build.get("exit") in events,
             "native compiler begin/exit absent")
        need(build["exit"].get("exit_code") == 0
             and int(build["exit"]["exit_filetime"]) >
             int(build["compiler"]["created_filetime"]), "native compiler closure")
    return {
        "status": "C_ENGINEERING_NATIVE_IDENTITY_BOUND",
        "compiled_mode": build["provenance"],
        "source_sha256": build["source_sha256"],
        "dll_sha256": build["dll_sha256"],
        "native_operation": operation_id,
        "actual_tool": result,
        "scope": "C native prerequisite only; no A reviewer PID; no formal CPU8 performance",
    }
