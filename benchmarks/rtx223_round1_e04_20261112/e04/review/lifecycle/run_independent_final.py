"""New lifecycle CPU tests and independent SQLite recheck; never native work."""
from pathlib import Path
import ast
import datetime
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "e04/budget/lifecycle_budget.py"
OUT = HERE / "final-independent-v1"
EXPECTED_SOURCE = "4c0aeabf01cf530d9ad0ce20ddc7db7848b0a3c572a858bfece8e1a885d837a4"
EXPECTED_TEST = "1754aaaf1017d930cf1fd19a7dcf4d1e99bff4f853e106a595a85acb4bccc1be"


def need(ok, text):
    if not ok:
        raise ValueError(text)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def audit_sqlite(path):
    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    try:
        app_id = db.execute("PRAGMA application_id").fetchone()[0]
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if app_id != 0x48534D4B:
            return {"path": str(path.relative_to(OUT)), "sha256": sha(path), "kind": "OWN_FOREIGN_DB_NEGATIVE_FIXTURE", "application_id": app_id, "tables": sorted(tables)}
        family = db.execute("SELECT id,ceiling,parent,inherited,stop_reason FROM family").fetchone()
        need(family[0].startswith("CPU-MOCK-") and family[1] == 4096, "nonmock budget family in independent CPU fixture")
        leases = db.execute("SELECT id,epoch,plan_hash,reserved,status,emitted,reason FROM leases ORDER BY rowid").fetchall()
        charged = family[3] + sum(max(row[3], row[5]) for row in leases)
        if any(row[4] == "OVERRUN" for row in leases):
            need(family[4] is not None, "overrun failed to stop family")
            need(any(row[5] == 4097 for row in leases), "above-family-cap observation lost")
            need(charged >= 4097, "observed 4097 not charged")
        for row in leases:
            need(type(row[3]) is int and row[3] >= 0 and type(row[5]) is int and row[5] >= 0, "invalid raw mock integer")
            if row[4] == "COMPLETE":
                need(row[5] <= row[3], "complete mock exceeded bound")
        return {"path": str(path.relative_to(OUT)), "sha256": sha(path), "kind": "CPU_MOCK_ONLY_NOT_GPU_QUOTA", "family": family[0], "ceiling": family[1], "inherited_mock": family[3], "stop_reason": family[4], "independently_recomputed_charged": charged, "leases": [dict(zip(("id", "epoch", "plan_hash", "reserved", "status", "observed_mock_emissions", "reason"), row)) for row in leases], "poststats": [json.loads(r[0]) for r in db.execute("SELECT payload FROM observations")]}
    finally:
        db.close()


def main():
    OUT.mkdir(exist_ok=False)
    test_path = ROOT / "e04/budget/test_lifecycle_budget.py"
    need(sha(SOURCE) == EXPECTED_SOURCE and sha(test_path) == EXPECTED_TEST, "final planner source/test identity mismatch")
    (OUT / "lifecycle_budget.reviewed.py").write_bytes(SOURCE.read_bytes())
    tree = ast.parse(SOURCE.read_text(encoding="utf8"))
    need(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)), "critical guard removable by python -O")
    imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    need(not any(x and any(word in x.lower() for word in ("cuda", "ctypes", "pywin32", "cupy", "torch")) for x in imports), "planner imports native/GPU bridge")
    runs = []
    for flags, mode in (([], "normal"), (["-O"], "optimized")):
        argv = [sys.executable, "-B", *flags, "-m", "unittest", "discover", "-s", str(ROOT / "e04/budget"), "-p", "test_lifecycle_budget.py", "-v"]
        env = os.environ.copy()
        env["HS_E04_KEEP_ROOT"] = str(OUT / "raw" / mode)
        run = subprocess.run(argv, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        log = OUT / (mode + ".log")
        log.write_bytes(run.stdout)
        count = re.findall(rb"Ran (\d+) tests", run.stdout)
        runs.append({"mode": mode, "argv": argv, "exit_code": run.returncode, "tests": int(count[-1]) if count else None, "log_sha256": sha(log)})
    need(sha(SOURCE) == EXPECTED_SOURCE and sha(test_path) == EXPECTED_TEST, "source changed during independent test run")
    need(all(r["exit_code"] == 0 and r["tests"] == 26 for r in runs), "independent planner tests failed; raw retained")
    ledgers, alias_notes = [], []
    for mode in ("normal", "optimized"):
        raw_root = OUT / "raw" / mode
        need(len(list(raw_root.iterdir())) == 26, "not all independent test fixture directories retained")
        for db_path in sorted(raw_root.glob("*/*.sqlite")):
            # A deliberately retained hardlink/symlink negative fixture can be
            # plain text, not SQLite; inspect the header without invoking SQL.
            if db_path.read_bytes()[:16] != b"SQLite format 3\0":
                ledgers.append({"path": str(db_path.relative_to(OUT)), "kind": "PLAIN_SENTINEL_NOT_OPENED_AS_SQLITE", "bytes": db_path.stat().st_size, "sha256": sha(db_path)})
            else:
                ledgers.append(audit_sqlite(db_path))
        note = raw_root / "test_cpu_prefix_does_not_authorize_symlink_or_hardlink_alias/TEST_NOTES.json"
        notes = read(note)
        folder = note.parent
        alias_notes.append({"mode": mode, "notes": notes, "hardlink_fixture_file_retained": (folder / "CPU-MOCK-hardlink.sqlite").exists(), "note": "OS-refused fixture creation is not evidence that the corresponding runtime alias branch executed"})
    (OUT / "RAW_SQLITE_AUDIT.json").write_text(json.dumps({"scope": "Independent SQL/table arithmetic only; no producer snapshot/verifier imports", "databases_and_sentinels": ledgers, "alias_OS_scope": alias_notes}, indent=2), encoding="utf8")
    overrun = [row for item in ledgers for row in item.get("leases", []) if row["status"] == "OVERRUN"]
    need(len(overrun) == 2 and all(row["observed_mock_emissions"] == 4097 for row in overrun), "raw 4097 faults not present in both modes")
    native_preflight = ROOT / "e04/budget/NATIVE_PREFLIGHT.json"
    preflight = read(native_preflight)
    need(preflight["decision"] == "BLOCKED_BEFORE_NUMERICAL_DLL_LOAD" and preflight["complete_lifecycle_upper_bound"] is None and preflight["native_release"] is False and preflight["native_proof_registry_entries"] == 0, "native preflight overclaims authority or bound")
    registry_nodes = [node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PRODUCTION_PROOF_ALLOWLIST" for t in node.targets)]
    need(len(registry_nodes) == 1 and isinstance(registry_nodes[0].value, ast.Call) and isinstance(registry_nodes[0].value.args[0], ast.Dict) and not registry_nodes[0].value.args[0].keys, "production proof registry not empty")
    result = {"schema": "heterospec.e04.independent-lifecycle-planner-review.v1", "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "decision": "INCONCLUSIVE", "review_result": "PASS_CPU_MOCK_PLANNER_ONLY_NATIVE_REMAINS_BLOCKED", "source_sha256": EXPECTED_SOURCE, "test_sha256": EXPECTED_TEST, "runs": runs, "raw_SQL_audit_sha256": sha(OUT / "RAW_SQLITE_AUDIT.json"), "own_fixture_directories": 52, "actual_4097_faults_retained_each_mode": True, "no_unknown_upper_bound_promoted_to_zero": True, "native_preflight": preflight, "initial_findings": {"M1": "Resolved by dedicated root/alias guards and readonly mock format validation before writable open; actual OS alias-subcase scope remains explicit in raw notes", "M2": "Unclosed lease blocks new-epoch continuation; raw own mock ledger and regression retained", "M3": "Policy digest now hexadecimal SHA256 grammar; regression passes", "M4": "Out-of-reservation observed mock emissions4097 persist as OVERRUN, charge4097 and stop family; independently recomputed from SQLite"}, "conceptual_proof_obligations": "../PROOF_OBLIGATIONS.json", "native_full_lifecycle_4096_proof": "NOT_ESTABLISHED", "normal_numerical_DLL_loads": 0, "CUDA_calls": 0, "model_requests": 0, "GPU_kernel_launches": 0, "old_41_or_18_or_prior_counter_tests_rerun": False, "canonical_GPU_ledger_opened_or_modified": False, "scope_limits": ["The CPU mock simulator has synthetic certificates, not physical GPU coverage", "All required lifecycle names and arithmetic can be validated while the native proof registry is empty; this never releases a numerical DLL load", "Graph-node expansion in a CPU fixture does not observe a CUDA graph replay", "Opaque library/runtime upper bounds are trusted only in synthetic mock authority, not as native caller-provided proof", "Whole-model usability, actual initialization, allphysicalkernel coverage, numerical qualification and complete service timing remain NOT_RUN or unqualified", "Hardlink/symlink fixture creation denied by the OS must remain NOT_RUN for that subcase rather than be reported as executed protection"]}
    (OUT / "FINAL_REVIEW.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps({"review_result": result["review_result"], "tests": [r["tests"] for r in runs], "fixture_directories": 52, "SQL_items": len(ledgers), "overrun_rows": len(overrun), "native_proof_registry": 0, "native_upper_bound": None, "decision": result["decision"]}, indent=2))


if __name__ == "__main__":
    main()
