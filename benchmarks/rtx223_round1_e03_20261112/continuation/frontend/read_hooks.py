"""Offline reader for v3 native evidence hooks; not a native admission gate.

Expected row IDs, stage geometries and KV dimensions must come from an
independent frozen reference contract, never from the candidate's receipt.
"""
from __future__ import annotations
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from admission import AdmissionError, NativeStateSpec, read_artifact, read_native_state, validate_full_vector


def need(ok, message):
    if not ok:
        raise AdmissionError("HOOK_EVIDENCE", message)


def read_evidence(root, receipt, expected):
    """Return bytes and parsed active hashes after checking an external contract.

    expected = {cycles:int, vocab:{target:int,draft:int}, state_specs:{role:NativeStateSpec},
      requested_rows:{role:[{call,caller_row,position,caller_rows,all_outputs,phase}]},
      states:{role:{stage_name:{geometry:<full expected geometry dict>,metadata_sha256:str}}}}
    """
    root = Path(root).resolve(strict=True)
    need(set(expected) == {"cycles", "vocab", "state_specs", "requested_rows", "states"}, "independent full evidence contract required")
    need(type(expected["cycles"]) is int and expected["cycles"] >= 0, "external reference cycle count required")
    need(set(expected["vocab"]) == {"target", "draft"}, "both model vocabularies must be frozen")
    need(set(expected["requested_rows"]) == {"target", "draft"}, "both requested-row sets required")
    need(set(expected["states"]) == {"target", "draft"}, "both target/draft stage sets required")
    result = {"vectors": {}, "states": {}, "native_admission": False, "scope": "OFFLINE_BYTES_AND_FROZEN_STAGE_CONTRACT_ONLY"}
    for role in ("target", "draft"):
        rows = receipt["requested_vector_captures"][role]
        wanted = expected["requested_rows"][role]
        keys = ("call", "caller_row", "position", "caller_rows", "all_outputs", "phase")
        key = lambda row: tuple(row[k] for k in keys)
        need(len({key(r) for r in rows}) == len(rows), "duplicate requested row")
        need([key(r) for r in rows] == [key(r) for r in wanted], "complete external requested row contract mismatch")
        owner = receipt["output_owner"][role + "_owner"]
        generation = receipt["output_owner"][role + "_generation"]
        need(receipt["output_owner"][role + "_invalid"] is False, "owner invalidated")
        result["vectors"][role] = []
        for row in rows:
            need(row["owner_id"] == owner and row["generation"] == generation and row["owned_copy"] is True, "vector ownership mismatch")
            need(row["vocab"] == expected["vocab"][role], "vocabulary cannot be shrunk by candidate")
            artifact = {"path": role + "/" + row["path"], "bytes": row["bytes"], "sha256": row["sha256"]}
            raw = read_artifact(root, artifact)
            validate_full_vector(raw, expected["vocab"][role])
            result["vectors"][role].append(raw)
        states = receipt["native_state_captures"][role]
        frozen_states = expected["states"][role]
        need(len({s["stage"] for s in states}) == len(states), "duplicate native stage")
        need({s["stage"] for s in states} == set(frozen_states), "missing/extra externally requested native state stage")
        need("initial" in frozen_states and "terminal" in frozen_states, "initial/terminal stage contract required")
        for cycle in range(expected["cycles"]):
            need("untrimmed-"+str(cycle) in frozen_states and "commit-"+str(cycle) in frozen_states, "every externally frozen cycle requires untrimmed and committed native state")
        result["states"][role] = {}
        for stage in states:
            name = stage["stage"]
            need(stage["schema"] == "heterospec.native-state-stage.v2" and stage["role"] == role, "state schema/role")
            need(stage["owner_id"] == owner and stage["generation"] == generation and stage["owner_invalid"] is False, "state owner mismatch")
            need(stage["capture_only_not_clean_guard"] is True and stage["independent_active_KV_parse_required"] is True, "capture must not impersonate clean guard")
            need(stage["geometry"] == frozen_states[name]["geometry"], "native geometry differs from external reference")
            need(stage["geometry"]["physical_head"] is not None, "head equality not established by native append guard")
            relative = role + "/state/" + name
            metadata = json.loads(read_artifact(root, {
                "path": relative + "/metadata.json",
                "bytes": (root / relative / "metadata.json").stat().st_size,
                "sha256": frozen_states[name]["metadata_sha256"]}))
            need(metadata == stage, "state sidecar and request record disagree")
            raw = read_artifact(root, {"path": relative + "/sequence.bin", "bytes": stage["sequence_bytes"], "sha256": stage["sequence_sha256"]})
            parsed = read_native_state(raw, frozen_states[name]["geometry"]["active_positions"], expected["state_specs"][role])
            result["states"][role][name] = {"geometry": stage["geometry"], "parsed": parsed}
    return result


def compare_evidence(a, b):
    need(a["vectors"].keys() == b["vectors"].keys(), "model role set changed")
    for role in a["vectors"]:
        need(a["vectors"][role] == b["vectors"][role], "complete requested vector byte mismatch: " + role)
        need(a["states"][role].keys() == b["states"][role].keys(), "native stage set changed")
        for name in a["states"][role]:
            x, y = a["states"][role][name], b["states"][role][name]
            need(x["geometry"] == y["geometry"], "native geometry mismatch")
            need(x["parsed"]["active_sha256"] == y["parsed"]["active_sha256"], "native active KV mismatch")
    return {"equal": True, "scope": "EXTERNALLY_FROZEN_EVIDENCE_ONLY", "native_admission": False}
