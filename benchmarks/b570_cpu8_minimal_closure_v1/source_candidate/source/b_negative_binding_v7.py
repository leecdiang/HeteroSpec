"""B-only verifier for three *fixed* expected failures; never relaxes success restore.

Requires frozen B task contract, real provider export/capture, Job identities,
and independent outer cleanup evidence. This is source-only and NOT native-tested.
"""
import datetime
import hashlib
import json
import re
from pathlib import Path
from operation_roles_v7 import operation, rel
from delivery_binding_v6 import capture, utc


EXPECTED = {
    "B02": ("JOB_CAP_DENIED", 1816),
    "B03": ("OPERATION_DEADLINE", None),
    "B04": ("OWNER_ABORT_CLEANUP", None),
}


def need(v, message):
    if not v:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(path):
    data = Path(path).read_bytes()
    need(data.endswith(bytes([10])), "partial B native journal")
    events = [json.loads(row) for row in data.splitlines()]
    need(events and all(x.get("seq") == i + 1 for i, x in enumerate(events)),
         "B native journal sequence")
    return events


def exactly(events, name):
    found = [x for x in events if x.get("event") == name]
    need(len(found) == 1, "B native event " + name)
    return found[0]


def check(root, role):
    root = Path(root).resolve()
    need(role in EXPECTED, "no generic allowed-failure switch")
    campaign = load(root / "CAMPAIGN.json")
    contract = load(rel(root, "B_NEGATIVE_CONTRACT.json"))
    need(contract.get("schema") == "B570_B_NEGATIVES_V1"
         and contract.get("task_uuid") == campaign.get("task_uuid")
         and campaign.get("task_uuid") and contract.get("status") == "FROZEN",
         "native B contract must be prospective")
    need(set(contract["cases"]) == set(EXPECTED), "all three negative cases explicitly declared")
    row = contract["cases"][role]
    expected_detector, os_code = EXPECTED[role]
    need(row.get("detector") == expected_detector and type(row.get("provider_exit_code")) is int
         and row["provider_exit_code"] != 0, "B frozen role/negative terminal")
    operation_id, op = operation(root, role, "B", "entry_negative")
    need(row.get("operation_id") == operation_id, "B negative operation identity")
    initial = capture(root, operation_id, "initial")
    intent = load(rel(root, "tools/" + operation_id + ".intent.json"))
    need(initial["request"] == intent["request"]
         and intent["operation_sha256"] == sha(root / "tools" / (operation_id + ".operation.json")),
         "B negative prospective request")
    polls = sorted((root / "tools").glob(operation_id + ".poll*.json"),
                   key=lambda p: int(p.name.split(".poll")[1].split(".")[0]))
    need([p.name for p in polls] == [operation_id + ".poll" + str(i) + ".json"
                                  for i in range(1, len(polls) + 1)], "B poll inventory")
    events = [initial] + [capture(root, operation_id, p.name.split(".")[1]) for p in polls]
    session = initial["response"].get("session_id")
    previous = utc(intent["registered_utc"])
    for i, item in enumerate(events):
        need(previous <= utc(item["observed_utc"]), "B captured time order")
        previous = utc(item["observed_utc"])
        if i:
            need(type(session) is int and item["request"].get("session_id") == session,
                 "B poll session")
        response = item["response"]
        need(response.get("session_id", session) == session, "B changed response session")
        need(type(response.get("output")) is str, "B raw provider output")
        need(response.get("exit_code") is None or i == len(events) - 1,
             "B premature terminal")
    terminal = events[-1]["response"]
    need(type(terminal.get("exit_code")) is int
         and terminal["exit_code"] == row["provider_exit_code"]
         and terminal.get("isError") == row["provider_is_error"], "B exact expected terminal")
    native = rows(rel(root, "operations/" + operation_id + "/EVENTS.jsonl"))
    start = exactly(native, "GUARD_START")
    detection = exactly(native, expected_detector)
    need(start["at_ns"] < detection["at_ns"], "B detector timing")
    if os_code is not None:
        need(detection.get("native_error") == os_code, "B native cap rejection error")
    # Never trust the failing guard to certify its own successful cleanup.
    original = Path(campaign["original_root"]).resolve()
    outside = Path(campaign["external_root"]).resolve()
    need(outside != original and outside not in original.parents and original not in outside.parents,
         "B outer capture distinct from candidate")
    witness_path = outside / "native-exits" / (operation_id + ".json")
    need(witness_path.is_file() and not witness_path.is_symlink()
         and not witness_path.is_junction() and witness_path.stat().st_nlink == 1,
         "B external cleanup record")
    need(row.get("outer_witness_sha256") == sha(witness_path), "B witness frozen bytes")
    witness = load(witness_path)
    need(witness.get("operation_id") == operation_id
         and witness.get("job_empty") is True
         and witness.get("all_owned_handles_closed") is True, "B observed outside cleanup")
    known = {(x["pid"], x["created_filetime"]) for x in native
             if x.get("event") in ("MEMBER_IDENTITY", "OP_CREATED_SUSPENDED")}
    exited = {(x["pid"], x["created_filetime"]) for x in witness.get("member_exits", [])
              if int(x["exit_filetime"]) > int(x["created_filetime"])}
    need(known and known.issubset(exited), "B missing native descendant exits")
    need(witness.get("owner_exit_filetime") and witness.get("owner_created_filetime")
         and int(witness["owner_exit_filetime"]) > int(witness["owner_created_filetime"]),
         "B owner OS exit unknown")
    need(type(witness.get("cleanup_elapsed_ms")) is int
         and 0 <= witness["cleanup_elapsed_ms"] <= op["cleanup_seconds"] * 1000,
         "B cleanup exceeded bound")
    need(witness.get("capture_source") == "EXTERNAL_NATIVE_OWNER"
         and witness.get("task_uuid") == campaign["task_uuid"],
         "B independent owner record absent")
    if role == "B04":
        need(witness.get("owner_exit_class") == "ABNORMAL"
             and not any(x.get("event") == "GUARD_END" for x in native),
             "B04 must observe owner abnormal exit")
    return {
        "status": "B_EXPECTED_FAILURE_EVIDENCE_CONSISTENT",
        "role": role, "operation_id": operation_id,
        "provider_exit_code": terminal["exit_code"],
        "detector": expected_detector,
        "known_members": len(known), "externally_reported_exits": len(exited),
        "scope": "Evidence consistency only; B actual hard cap/provenance needs native approval",
    }
