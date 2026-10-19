"""Fail-closed prospective operation-role lookup, distinct from native gate paths.

A is independently source-reviewed. B/C look up actual operations in one pinned
OPERATION_ROLE_MAP.json. Historical operation IDs are never accepted as new PASS.
"""
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "B570_TASK_OPERATION_ROLES_V1"
IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\\Z")
HISTORICAL = {
    "037-final-review", "036-final-regressions", "026-budget-negatives",
    "025-bridge-negatives", "021-build-launcher-windows-path",
    "compile-v6-2", "038-final-startup", "probe-download-01",
    "030-isolated-probe-recompute",
}


def need(value, reason):
    if not value:
        raise ValueError(reason)


def load(path):
    return json.loads(Path(path).read_bytes())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(root, name):
    need(isinstance(name, str) and name and "\\" not in name, "role relative path")
    p = Path(name)
    need(not p.is_absolute() and ".." not in p.parts and ":" not in name, "role path escape")
    current = root
    for part in p.parts:
        current = current / part
        need(not current.is_symlink() and not current.is_junction(), "role path alias")
    return current


def role_map(root, phase):
    root = Path(root).resolve()
    need(phase in ("B", "C"), "native task phase")
    campaign = load(root / "CAMPAIGN.json")
    uid = campaign.get("task_uuid")
    need(isinstance(uid, str) and uid, "current native task UUID")
    doc = load(rel(root, "OPERATION_ROLE_MAP.json"))
    need(doc.get("schema") == SCHEMA and doc.get("task_uuid") == uid
         and doc.get("phase") == phase, "role map current task identity")
    roles = doc.get("roles")
    need(isinstance(roles, dict) and roles, "role inventory")
    ids = []
    for key, row in roles.items():
        need(IDENT.fullmatch(key) is not None and isinstance(row, dict), "role entry")
        op = row.get("operation_id")
        need(row.get("phase") == phase and isinstance(op, str)
             and IDENT.fullmatch(op) is not None and op not in HISTORICAL,
             "role phase/current operation id")
        ids.append(op)
    need(len(set(ids)) == len(ids), "duplicate operation ids")
    return doc


def operation(root, role, phase, expected_kind=None):
    root = Path(root).resolve()
    doc = role_map(root, phase)
    need(role in doc["roles"], "unregistered role")
    mapping = doc["roles"][role]
    if expected_kind is not None:
        need(mapping.get("kind") == expected_kind, "wrong operation kind")
    opid = mapping["operation_id"]
    filename = "tools/" + opid + ".operation.json"
    path = rel(root, filename)
    need(path.is_file() and mapping.get("sha256") == digest(path),
         "operation exact bytes not frozen")
    op = load(path)
    need(op.get("id") == opid and op.get("task_uuid") == doc["task_uuid"]
         and op.get("stage") == phase, "operation belongs to another task/stage")
    return opid, op


def native_gate_paths(root, required=("healthy", "freeze", "stall", "stall_harness")):
    """Reuse the original NATIVE_GATE_PATHS.json; do not create a second gate map."""
    root = Path(root).resolve()
    paths = load(rel(root, "NATIVE_GATE_PATHS.json"))
    task = load(rel(root, "CAMPAIGN.json"))
    need(paths.get("schema") == "B570_NATIVE_GATE_PATHS_V2"
         and paths.get("task_uuid") == task.get("task_uuid"), "native map current UUID")
    need(len(set(paths[k] for k in required)) == len(required), "native gate alias")
    for key in required:
        need(key in paths and isinstance(paths[key], str), "missing native gate role")
        p = rel(root, paths[key])
        need(p.parent != root and p.exists(), "native gate artifact absent")
    return {key: rel(root, paths[key]) for key in required}
