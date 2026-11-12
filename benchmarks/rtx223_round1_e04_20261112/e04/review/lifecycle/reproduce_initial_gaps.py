"""Own harmless CPU/SQLite fixtures only; never opens the canonical ledger."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "e04/budget/lifecycle_budget.py"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    out = HERE / "initial-gap-fixtures"
    out.mkdir(exist_ok=False)
    snapshot = out / "lifecycle_budget.reviewed.py"
    snapshot.write_bytes(SOURCE.read_bytes())
    name = "reviewed_lifecycle_fixture"
    spec = importlib.util.spec_from_file_location(name, snapshot)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    result = {"schema": "heterospec.e04.independent-initial-planner-gaps.v1", "source_sha256": digest(snapshot), "scope": "Own mock SQLite fixtures only; real canonical ledger never opened", "models": 0, "CUDA_calls": 0, "old_tests_rerun": False, "findings": []}
    sentinel = out / "harmless-original.sqlite"
    db = sqlite3.connect(sentinel)
    db.execute("CREATE TABLE sentinel(message TEXT)")
    db.execute("INSERT INTO sentinel VALUES('own fixture only')")
    db.commit(); db.close()
    before = digest(sentinel)
    alias = out / "CPU-MOCK-hardlink.sqlite"
    try:
        os.link(sentinel, alias)
        ledger = module.MockFamilyLedger(alias, "CPU-MOCK-alias", "own-parent", 0)
        ledger.close()
        db = sqlite3.connect(sentinel.as_uri() + "?mode=ro", uri=True)
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        db.close()
        result["findings"].append({"id": "M1", "hardlink_alias_accepted": True, "own_original_mutated": before != digest(sentinel), "original_tables_after": tables, "link_count": sentinel.stat().st_nlink, "not_the_real_canonical_ledger": True})
    except Exception as exc:
        result["findings"].append({"id": "M1", "hardlink_alias_accepted": False, "exception": type(exc).__name__ + ": " + str(exc), "own_original_mutated": before != digest(sentinel)})
    dbpath = out / "CPU-MOCK-pending.sqlite"
    ledger = module.MockFamilyLedger(dbpath, "CPU-MOCK-pending", "parent", 0)
    phases, certs = [], []
    for phase in module.REQUIRED_PHASES:
        n = module.Node("opaque", "mock:" + phase, "MOCK:" + phase, "a" * 64)
        phases.append(module.Phase(phase, (n,)))
        certs.append(module.Certificate(n.proof_id, phase, n.route, n.kind, 1 if phase == "target_verify" else 0, "a" * 64))
    policy = {actor: "b" * 64 for actor in module.REQUIRED_ACTORS}
    plan = module.Planner(module.MockProofRegistry(certs)).bind(tuple(phases), policy)
    ledger.reserve("unfinished", "e04", plan)
    ledger.mark_running("unfinished")
    ledger.close()
    reopened = module.MockFamilyLedger(dbpath, "CPU-MOCK-pending", "parent", 0)
    try:
        reopened.reserve("new-after-unclosed", "e05", plan)
        result["findings"].append({"id": "M2", "new_lease_after_unclosed_running_accepted": True, "snapshot": reopened.snapshot()})
    except Exception as exc:
        result["findings"].append({"id": "M2", "new_lease_after_unclosed_running_accepted": False, "exception": type(exc).__name__ + ": " + str(exc), "snapshot": reopened.snapshot()})
    reopened.close()
    try:
        bad_policy = {actor: "z" * 64 for actor in module.REQUIRED_ACTORS}
        module.Planner(module.MockProofRegistry(certs)).bind(tuple(phases), bad_policy)
        result["findings"].append({"id": "M3", "nonhex_policy_digest_accepted": True})
    except Exception as exc:
        result["findings"].append({"id": "M3", "nonhex_policy_digest_accepted": False, "exception": type(exc).__name__ + ": " + str(exc)})
    (out / "INITIAL_GAPS.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
