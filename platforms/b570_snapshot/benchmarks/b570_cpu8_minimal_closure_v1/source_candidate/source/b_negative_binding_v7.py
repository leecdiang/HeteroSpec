"""B-only verifier for three *fixed* expected failures; never relaxes success restore.

Requires frozen B task contract, real provider export/capture, Job identities,
and independent outer cleanup evidence. This is source-only and NOT native-tested.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from operation_roles_v7 import operation, rel
from delivery_binding_v6 import capture, utc, request_check


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


def native_child_binding(start, created, op, original, operation_sha, task_uuid):
    # Native command and parent identity are evidence separate from the shell
    # provider request, which request_check authenticates.
    need(type(start.get("pid")) is int and type(created.get("pid")) is int
         and type(start.get("created_filetime")) is str
         and type(created.get("created_filetime")) is str,
         "B guard and child native identity type")
    need(type(op.get("argv")) is list and op["argv"]
         and all(type(x) is str for x in op["argv"]), "B child argv type")
    need(op["argv"] == created.get("argv")
         and created.get("command") == subprocess.list2cmdline(op["argv"])
         and created.get("parent_pid") == start["pid"]
         and int(created["created_filetime"]) >= int(start["created_filetime"])
         and created.get("image") == op["argv"][0],
         "B native child argv/parent identity")
    need(start.get("intent_sha256") == operation_sha
         and op.get("task_uuid") == task_uuid
         and Path(op["root"]).resolve() == Path(original).resolve(),
         "B guard operation identity binding")
    return True


def outside_owner_binding(witness, start, created, operation_sha, terminal, job_members):
    terminal_sha = hashlib.sha256(
        json.dumps(terminal, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    need(witness.get("owner_pid") == start["pid"]
         and witness.get("owner_created_filetime") == start["created_filetime"]
         and witness.get("guard_parent_pid") == start.get("parent_pid")
         and type(start.get("parent_pid")) is int and start["parent_pid"] > 0
         and witness.get("guard_command_sha256") == start["command_sha256"]
         and witness.get("guard_operation_sha256") == operation_sha
         and witness.get("root_pid") == created["pid"]
         and witness.get("root_created_filetime") == created["created_filetime"]
         and witness.get("provider_terminal_sha256") == terminal_sha,
         "B outside owner/guard/child/provider identities disagree")
    outside_pid = witness.get("external_owner_pid")
    outside_created = witness.get("external_owner_created_filetime")
    need(type(outside_pid) is int and outside_pid > 0
         and type(outside_created) is str and outside_created.isdecimal()
         and int(outside_created) > 0,
         "B independent outside owner identity absent")
    need(type(job_members) is set
         and all(type(pid) is int and pid > 0 and type(created_ft) is str
                 and created_ft.isdecimal() and int(created_ft) > 0
                 for pid, created_ft in job_members),
         "B actual Job identities required")
    need(outside_pid not in ({start["pid"], created["pid"]} |
                            {pid for pid, _ in job_members})
         and (outside_pid, outside_created) not in job_members
         and witness.get("external_owner_job_member") is False,
         "B outside owner cannot be guard, child or Job member")
    return terminal_sha


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
         and row["provider_exit_code"] != 0 and type(row.get("provider_is_error")) is bool,
         "B frozen role/negative terminal")
    sources = {"B02": "FIXTURE_NATIVE", "B03": "GUARD_MONOTONIC",
               "B04": "EXTERNAL_NATIVE_OWNER"}
    need(row.get("detector_source") == sources[role], "B frozen detector origin")
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
    created = exactly(native, "OP_CREATED_SUSPENDED")
    need(type(start.get("at_ns")) is int and type(created.get("at_ns")) is int
         and start["at_ns"] < created["at_ns"], "B real owner startup")
    operation_sha = sha(root / "tools" / (operation_id + ".operation.json"))
    original = request_check(root, operation_id, intent, initial, start, operation_sha)
    # Exact workload argv, native command line and parent relationship are
    # authenticated separately from the outer PowerShell/guard request.
    native_child_binding(start, created, op, original, operation_sha, campaign["task_uuid"])
    # The external owner must authenticate its own bytes after execution.
    # A prospective frozen contract cannot know the future witness SHA256.
    outside = Path(campaign["external_root"]).resolve()
    need(outside != original and outside not in original.parents and original not in outside.parents,
         "B outer capture distinct from candidate")
    witness_path = outside / "native-exits" / (operation_id + ".json")
    need(witness_path.is_file() and not witness_path.is_symlink()
         and not witness_path.is_junction() and witness_path.stat().st_nlink == 1,
         "B external cleanup record")
    witness = load(witness_path)
    need(witness.get("frozen_contract_sha256") == sha(root / "B_NEGATIVE_CONTRACT.json"),
         "B outside witness prospective contract identity")
    need(witness.get("operation_id") == operation_id
         and witness.get("job_empty") is True
         and witness.get("all_owned_handles_closed") is True,
         "B observed outside cleanup")
    known = {(x["pid"], x["created_filetime"]) for x in native
             if x.get("event") in ("MEMBER_IDENTITY", "OP_CREATED_SUSPENDED")}
    identities = witness.get("member_exits")
    need(type(identities) is list and identities, "B external full member exits")
    exited = {(x["pid"], x["created_filetime"]) for x in identities
              if int(x["exit_filetime"]) > int(x["created_filetime"])}
    need(known and known.issubset(exited) and len(exited) == len(identities),
         "B incomplete/duplicate native descendant exits")
    need(type(witness.get("job_total_starts")) is int
         and witness["job_total_starts"] == len(exited),
         "B external job total starts and exits disagree")
    terminal_sha = outside_owner_binding(witness, start, created,
                                         operation_sha, terminal, exited)
    need(witness.get("owner_exit_filetime") and witness.get("owner_created_filetime")
         and int(witness["owner_exit_filetime"]) > int(witness["owner_created_filetime"]),
         "B owner OS exit unknown")
    need(type(witness.get("cleanup_elapsed_ms")) is int
         and 0 <= witness["cleanup_elapsed_ms"] <= op["cleanup_seconds"] * 1000,
         "B cleanup exceeded bound")
    need(witness.get("capture_source") == "EXTERNAL_NATIVE_OWNER"
         and witness.get("task_uuid") == campaign["task_uuid"],
         "B independent owner record absent")
    if role == "B02":
        # A fixed, reviewed native fixture must record the rejected CreateProcess
        # OS result. The ordinary guard cannot infer error 1816 from Job census.
        fixture_path = rel(root, "operations/" + operation_id + "/FIXTURE_NATIVE_EVENTS.jsonl")
        native_attempts = rows(fixture_path)
        detector = exactly(native_attempts, "JOB_CAP_DENIED")
        reporter = (detector.get("writer_pid"), detector.get("writer_created_filetime"))
        need(detector.get("native_error") == os_code and reporter in exited
             and type(detector.get("at_ns")) is int
             and start["at_ns"] < detector["at_ns"], "B02 actual native refused create")
        need(witness.get("fixture_native_sha256") == sha(fixture_path)
             and witness.get("termination_reason") == "JOB_CAP_DENIED",
             "B02 fixture byte capture and negative reason")
    elif role == "B03":
        detector = exactly(native, "OPERATION_DEADLINE")
        failed = exactly(native, "OPERATION_FAILURE")
        need(detector.get("source") == "GUARD_MONOTONIC_CHECK"
             and type(detector.get("at_ns")) is int
             and type(detector.get("deadline_ns")) is int
             and type(detector.get("observed_ns")) is int
             and type(detector.get("rescue_fired")) is bool
             and (detector["observed_ns"] > detector["deadline_ns"]
                  or detector["rescue_fired"] is True)
             and start["at_ns"] < detector["at_ns"] <= failed["at_ns"]
             and "OPERATION_DEADLINE" in failed.get("error", ""),
             "B03 actual monotonic deadline detector")
        need(witness.get("termination_reason") == "OPERATION_DEADLINE",
             "B03 independent timeout cause missing")
    else:
        # Abrupt owner death means it CANNOT be the author of its own successful
        # cleanup event. Only an external native owner may attest this detector.
        outside_events = witness.get("independent_events")
        need(type(outside_events) is list, "B04 outside events missing")
        detector = exactly(outside_events, "OWNER_ABORT_CLEANUP")
        need(detector.get("source") == "EXTERNAL_NATIVE_OWNER"
             and witness.get("owner_exit_class") == "ABNORMAL"
             and not any(x.get("event") == "GUARD_END" for x in native),
             "B04 external abnormal-owner cleanup not proven")
    return {
        "status": "B_EXPECTED_FAILURE_EVIDENCE_CONSISTENT",
        "role": role, "operation_id": operation_id,
        "provider_exit_code": terminal["exit_code"],
        "detector": expected_detector, "detector_source": sources[role],
        "external_witness_sha256": sha(witness_path),
        "guard_pid": start["pid"], "guard_created_filetime": start["created_filetime"],
        "provider_terminal_sha256": terminal_sha,
        "known_members": len(known), "externally_reported_exits": len(exited),
        "scope": "Evidence consistency only; B actual hard cap/provenance needs native approval",
    }
