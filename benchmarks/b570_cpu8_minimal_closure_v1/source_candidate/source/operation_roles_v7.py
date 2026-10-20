"""Fail-closed prospective operation-role lookup, distinct from native gate paths.

A is independently source-reviewed. B/C look up actual operations in one pinned
OPERATION_ROLE_MAP.json. Historical operation IDs are never accepted as new PASS.
"""
import hashlib
import json
import re
import copy
from pathlib import Path

SCHEMA = "B570_TASK_OPERATION_ROLES_V1"
IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
F0_SENTINEL = "__F0_SHA256__"
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


def formal_template(root, role="C-formal-watchdog"):
    """One immutable C source template; its bytes are in F0, no F0 hash yet."""
    root = Path(root).resolve()
    doc = role_map(root, "C")
    need(role in doc["roles"], "formal role missing")
    mapping = doc["roles"][role]
    need(mapping.get("phase") == "C" and mapping.get("kind") == "formal_cpu8"
         and mapping.get("post_freeze_template") is True
         and "sha256" not in mapping, "formal role must pin only pre-F0 template")
    opid = mapping["operation_id"]
    path = rel(root, "tools/" + opid + ".operation.template.json")
    need(path.is_file() and mapping.get("template_sha256") == digest(path),
         "formal template exact frozen bytes")
    template = load(path)
    need(template.get("id") == opid and template.get("task_uuid") == doc["task_uuid"]
         and template.get("stage") == "C", "formal template task identity")
    argv = template.get("argv")
    need(type(argv) is list and argv.count("--freeze-sha256") == 1
         and all(type(x) is str for x in argv), "formal template argument inventory")
    pos = argv.index("--freeze-sha256")
    need(pos + 1 < len(argv) and argv[pos+1] == F0_SENTINEL
         and argv.count(F0_SENTINEL) == 1, "formal template F0 placeholder")
    return opid, path, template


def render_formal_operation(root):
    """Deterministic post-F0 bytes. No mutation of the frozen template/map."""
    root = Path(root).resolve()
    opid, path, template = formal_template(root)
    freeze_path = rel(root, "CAPABILITY_FREEZE.json")
    need(freeze_path.is_file(), "F0 must exist before runtime rendering")
    frozen = load(freeze_path)
    pinned = frozen.get("files", {})
    runtime_rel = "tools/" + opid + ".operation.json"
    template_rel = path.relative_to(root).as_posix()
    need(runtime_rel not in pinned, "F0 hash cycle: runtime operation frozen")
    need(pinned.get(template_rel) == digest(path)
         and pinned.get("OPERATION_ROLE_MAP.json") == digest(root/"OPERATION_ROLE_MAP.json"),
         "F0 has not pinned role map and source operation template")
    actual = copy.deepcopy(template)
    pos = actual["argv"].index("--freeze-sha256")
    actual["argv"][pos+1] = digest(freeze_path)
    text_bytes = (json.dumps(actual, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    return opid, rel(root, runtime_rel), actual, text_bytes


def materialize_formal_operation(root):
    """Explicit post-freeze native-controller step; never invoked during F0."""
    root = Path(root).resolve()
    campaign = load(rel(root, "CAMPAIGN.json"))
    need(root == Path(campaign["original_root"]).resolve(), "no restored-root execution")
    opid, dest, _, serialized = render_formal_operation(root)
    with dest.open("xb") as stream:
        stream.write(serialized)
        stream.flush()
        import os
        os.fsync(stream.fileno())
    return {"operation_id": opid, "operation_sha256": digest(dest),
            "freeze_sha256": digest(root/"CAPABILITY_FREEZE.json"),
            "status": "POST_F0_OPERATION_MATERIALIZED_NOT_ADMITTED"}


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
    if mapping.get("kind") == "formal_cpu8":
        need(phase == "C" and role == "C-formal-watchdog",
             "unexpected post-F0 dynamic operation role")
        tid, expected_path, expected, serialized = render_formal_operation(root)
        need(tid == opid and expected_path == path and path.is_file()
             and path.read_bytes() == serialized,
             "formal runtime operation not exactly derived from F0 template")
        op = expected
    else:
        need(path.is_file() and mapping.get("sha256") == digest(path)
             and "template_sha256" not in mapping,
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
    for key in required:
        need(key in paths and isinstance(paths[key], str), "missing native gate role")
    need(len(set(paths[k] for k in required)) == len(required), "native gate alias")
    for key in required:
        p = rel(root, paths[key])
        need(p.parent != root and p.exists(), "native gate artifact absent")
    return {key: rel(root, paths[key]) for key in required}
