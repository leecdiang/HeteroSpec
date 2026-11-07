#!/usr/bin/env python3
"""CPU-only planning and evidence-structure checks. Never launches a model or GPU.

This tool generates exactly 152 PRIMARY coordinates. An unbound draft is not
execution-authorized. Native boundary export/import and the consumer extension
are specified in HOST_HANDOFF.md; they are not implemented by this Python file.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import pathlib
import sys
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
STUDY = "b570_producer_consumer_boundary_v1"
COMPLETE = {"COMPLETE_QUALIFIED", "COMPLETE_COUNTEREXAMPLE", "COMPLETE_NO_TRIGGER"}
FAILURE = {
    "RESTORE_SHAM_FAILED", "OBSERVER_INTERFERENCE", "GEOMETRY_NOT_ADMITTED",
    "REFERENCE_MISMATCH", "TECHNICAL_FAILURE", "BUDGET_EXHAUSTED",
}
NOT_RUN = {"NOT_RUN_DEPENDENCY", "NOT_RUN_DATE_UNAVAILABLE", "NOT_RUN_BUDGET"}
HEX = set("0123456789abcdef")
BUDGET = {"primary_model_requests": 152, "b0": 32, "b1": 120, "operator_replays": 0,
          "performance_measurements": 0, "maximum_active_gpu_workers": 1,
          "owned_seconds_cap": 10800, "payload_bytes_cap": 8589934592, "automatic_retry": False}

class ContractError(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise ContractError(message)

def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def sha_file(path):
    with pathlib.Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def is_hash(value):
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX

def is_int(value):
    return type(value) is int

def write_new(path, value):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def p4_schedule(length):
    result = [4] * (length // 4)
    tail = length % 4
    result += [2, 1] if tail == 3 else ([tail] if tail else [])
    require(sum(result) == length and set(result) <= {1, 2, 4}, "P4T schedule invalid")
    return result

def check_input(item, new):
    require(isinstance(item, dict), "input must be an object")
    require(isinstance(item.get("id"), str) and item["id"], "input id missing")
    ids = item.get("prompt_ids")
    require(isinstance(ids, list) and ids and all(is_int(t) and t >= 0 for t in ids),
            "prompt_ids must be nonnegative native integer IDs")
    require(item.get("cap") == (128 if new else 64), "new cap128 / control cap64 mismatch")
    require(len(ids) + item["cap"] + 2 < 512, "request extent must be <512")
    if new:
        require((64 <= len(ids) <= 192) or (256 <= len(ids) <= 352),
                "new input outside the frozen length bands")
        expected = "short" if len(ids) <= 192 else "long"
        require(item.get("stratum") == expected, "stratum/actual native length mismatch")
        require(isinstance(item.get("domain"), str) and item["domain"], "domain missing")
        source = item.get("source")
        require(isinstance(source, dict) and source.get("revision") and source.get("task_id"),
                "source revision/task_id missing")
        require(is_hash(item.get("template_sha256")), "template hash missing")
        require(is_hash(item.get("selection_hash")), "selection hash missing")
        require(item.get("exposure_status") == "UNSEEN_FOR_CURRENT_IMPLEMENTATION",
                "new-input exposure status must be explicitly frozen")
    return ids

def check_panel(panel, controls):
    require(panel.get("status") == "FROZEN_BEFORE_FORWARD", "panel is not frozen")
    require(panel.get("new_model_outputs_used_for_selection") is False,
            "selection may not use new model outputs")
    require(is_hash(panel.get("candidate_inventory_sha256")), "candidate inventory hash missing")
    require(is_hash(panel.get("exposure_audit_sha256")), "exposure audit hash missing")
    require(isinstance(panel.get("selection_rule"), str) and panel["selection_rule"], "selection rule missing")
    inputs = panel.get("inputs")
    require(isinstance(inputs, list) and len(inputs) == 8, "exactly eight new inputs required")
    for item in inputs:
        check_input(item, True)
    require(Counter(i["stratum"] for i in inputs) == {"short": 4, "long": 4}, "four inputs per band required")
    require(len({i["id"] for i in inputs}) == 8, "duplicate input IDs")
    require(len({digest(i["prompt_ids"]) for i in inputs}) == 8, "duplicate prompt token sequences")
    require(not ({i["id"] for i in inputs} & {i["id"] for i in controls}), "control selected as new input")
    return inputs

def check_runtime(runtime):
    require(runtime.get("status") == "BUILT_NOT_YET_B0_QUALIFIED", "runtime must identify the new build")
    require(runtime.get("native_extension_implemented") is True, "native extension is not implemented")
    for field in ("executable_sha256", "source_manifest_sha256", "numeric_modules_manifest_sha256"):
        require(is_hash(runtime.get(field)), field + " missing")
    require(runtime.get("upstream_commit") == "0cae43063cf15170e91a2ff4d034da0ecef4a1b2",
            "upstream changed")
    require(runtime.get("target_sha256") == "408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6",
            "target model changed")
    require(runtime.get("draft_sha256") == "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031",
            "draft model changed")
    require(runtime.get("threads") == 8 and runtime.get("kv_dtype") == "F16"
            and runtime.get("flash_attention") is False
            and runtime.get("placement") == "TARGET_AND_DRAFT_B570_VULKAN", "runtime contract changed")
    eog = runtime.get("eog_ids")
    require(isinstance(eog, list) and eog and all(is_int(x) and x >= 0 for x in eog), "native EOG IDs missing")
    require(is_int(runtime.get("vocabulary_size")) and runtime["vocabulary_size"] > max(eog), "vocabulary size missing")
    return runtime

def make_slots(controls, inputs=None):
    require(len(controls) == 2 and [i["id"] for i in controls] == ["HumanEval/38", "HumanEval/115"],
            "historical controls changed")
    for item in controls:
        check_input(item, False)
    bound = inputs is not None
    slots = []

    def add(stage, coordinate, item, index, producer, consumer, route, observer,
            donor=None, comparison=None, reference=None, producer_match=None, historical=None, extra_deps=()):
        ids = item["prompt_ids"] if item else None
        slot = {
            "schema": 1, "slot_id": f"{STUDY}/{coordinate}", "stage": stage,
            "cohort": "control" if stage == "B0" else "new_input",
            "input_index": index, "input_id": item["id"] if item else None,
            "prompt_ids_sha256": digest(ids) if ids else None,
            "prompt_tokens": len(ids) if ids else None,
            "cap": item["cap"] if item else 128,
            "producer": producer, "producer_layout": consumer if route == "natural_spec" else "PQ",
            "consumer": consumer, "route": route, "observer": observer,
            "k": 1 if consumer in {"PQ", "QB"} else 0,
            "target_ub": 1 if route == "strict_reference" else 4,
            "output_capacity": 1 if route == "strict_reference" else 4,
            "caller_lengths": None if ids is None else ([1] * len(ids) if producer == "P1" else p4_schedule(len(ids))),
            "donor_slot_id": donor, "compare_slot_id": comparison,
            "strict_reference_slot_id": reference, "producer_match_slot_id": producer_match,
            "historical_reference": historical, "requires_gate": [] if stage == "B0" else ["B0_QUALIFIED"],
            "depends_on": list(dict.fromkeys(x for x in (donor, comparison, reference, producer_match, *extra_deps) if x)),
            "performance_eligible": False, "result": None,
        }
        slots.append(slot)
        return slot["slot_id"]

    for index, item in enumerate(controls):
        prefix = f"B0/control{index}"
        c1_donors = {}
        for producer in ("P1", "P4T"):
            off = add("B0", f"{prefix}/{producer}/C1/natural/off", item, index, producer, "C1", "natural", "off",
                      historical={"qual_index": (0, 2)[index], "arm": "R"} if producer == "P1" else None)
            heavy = add("B0", f"{prefix}/{producer}/C1/natural/heavy", item, index, producer, "C1", "natural", "heavy",
                        comparison=off,
                        historical={"qual_index": (0, 2)[index], "arm": "R"} if producer == "P1" else None)
            c1_donors[producer] = heavy
            add("B0", f"{prefix}/{producer}/C1/resumed/off", item, index, producer, "C1", "resumed", "off",
                donor=heavy, comparison=heavy)
            add("B0", f"{prefix}/{producer}/C1/resumed/heavy", item, index, producer, "C1", "resumed", "heavy",
                donor=heavy, comparison=heavy)
        for consumer in ("PQ", "QB"):
            hist = {"qual_index": (0, 2)[index], "arm": consumer}
            off = add("B0", f"{prefix}/P1/{consumer}/natural/off", item, index, "P1", consumer, "natural_spec", "off",
                      historical=hist)
            heavy = add("B0", f"{prefix}/P1/{consumer}/natural/heavy", item, index, "P1", consumer, "natural_spec", "heavy",
                        comparison=off, producer_match=c1_donors["P1"], historical=hist)
            add("B0", f"{prefix}/P1/{consumer}/resumed/off", item, index, "P1", consumer, "resumed", "off",
                donor=heavy, comparison=heavy)
            add("B0", f"{prefix}/P1/{consumer}/resumed/heavy", item, index, "P1", consumer, "resumed", "heavy",
                donor=heavy, comparison=heavy)

    for index in range(8):
        item = inputs[index] if bound else None
        prefix = f"B1/input{index}"
        reference = add("B1", f"{prefix}/R/off", item, index, "P1", "C1", "strict_reference", "off")
        donors, shams = {}, {}
        for producer in ("P1", "P4T"):
            off = add("B1", f"{prefix}/{producer}/C1/natural/off", item, index, producer, "C1", "natural", "off",
                      reference=reference)
            heavy = add("B1", f"{prefix}/{producer}/C1/natural/heavy", item, index, producer, "C1", "natural", "heavy",
                        comparison=off, reference=reference)
            donors[producer] = heavy
            shams[producer] = add("B1", f"{prefix}/{producer}/C1/resumed/heavy", item, index, producer, "C1", "resumed", "heavy",
                                 donor=heavy, comparison=heavy, reference=reference)
        for producer in ("P1", "P4T"):
            for consumer in ("PQ", "QB"):
                off = add("B1", f"{prefix}/{producer}/{consumer}/resumed/off", item, index, producer, consumer, "resumed", "off",
                          donor=donors[producer], reference=reference, extra_deps=[shams[producer]])
                add("B1", f"{prefix}/{producer}/{consumer}/resumed/heavy", item, index, producer, consumer, "resumed", "heavy",
                    donor=donors[producer], comparison=off, reference=reference, extra_deps=[shams[producer]])
    require(len(slots) == 152, "internal primary count")
    require(Counter(s["stage"] for s in slots) == {"B0": 32, "B1": 120}, "internal stage counts")
    return slots

def build_plan(panel=None, runtime=None):
    control_doc = read(HERE / "CONTROL_INPUTS.json")
    controls = control_doc["inputs"]
    inputs = check_panel(panel, controls) if panel else None
    if panel:
        require(runtime is not None, "runtime identity required for a bound freeze")
        check_runtime(runtime)
    else:
        require(runtime is None, "cannot bind runtime without a real panel")
    slots = make_slots(controls, inputs)
    return {
        "schema": 1, "study_id": STUDY, "status": "FROZEN_BEFORE_FORWARD" if panel else "DRAFT_UNBOUND",
        "native_execution_count": 0, "native_extension_implemented": bool(panel),
        "execution_authorized": bool(panel),
        "base_commit": "9f03bead68462326497b03edb0d2d80f8f2fd4c3",
        "cpu_tool_sha256": sha_file(pathlib.Path(__file__)),
        "protocol_sha256": sha_file(HERE / "PROTOCOL.md"),
        "source_pins_sha256": sha_file(HERE / "SOURCE_PINS.json"),
        "controls_sha256": sha_file(HERE / "CONTROL_INPUTS.json"),
        "panel": panel, "runtime": runtime, "slots_sha256": digest(slots), "slots": slots,
        "budget": dict(BUDGET),
        "claim_scope": "BOUNDARY0_CLEAN_RECEIVER_CONTRACT; no natural P4T production-path claim",
    }

def validate_plan(plan):
    require(plan.get("schema") == 1 and plan.get("study_id") == STUDY, "unknown plan schema")
    bound = plan.get("status") == "FROZEN_BEFORE_FORWARD"
    require(bound or plan.get("status") == "DRAFT_UNBOUND", "unknown plan state")
    controls = read(HERE / "CONTROL_INPUTS.json")["inputs"]
    inputs = check_panel(plan["panel"], controls) if bound else None
    if bound:
        check_runtime(plan["runtime"])
    else:
        require(plan.get("panel") is None and plan.get("runtime") is None, "unbound plan contains fake bindings")
    require(plan.get("execution_authorized") is bound, "execution status mismatch")
    require(plan.get("cpu_tool_sha256") == sha_file(pathlib.Path(__file__)), "CPU tool changed after freeze")
    require(plan.get("protocol_sha256") == sha_file(HERE / "PROTOCOL.md"), "protocol changed after freeze")
    require(plan.get("source_pins_sha256") == sha_file(HERE / "SOURCE_PINS.json"), "source pin manifest changed")
    require(plan.get("controls_sha256") == sha_file(HERE / "CONTROL_INPUTS.json"), "control bytes changed")
    expected = make_slots(controls, inputs)
    require(plan.get("slots") == expected, "slot matrix/dependencies changed")
    require(plan.get("slots_sha256") == digest(expected), "slot digest mismatch")
    require(plan.get("budget") == BUDGET, "budget changed")
    return expected

def safe_payload(root, meta):
    require(isinstance(meta, dict) and is_hash(meta.get("sha256")), "payload identity missing")
    require(is_int(meta.get("bytes")) and meta["bytes"] > 0, "payload byte size invalid")
    rel = pathlib.PurePosixPath(meta.get("path", ""))
    require(str(rel) not in {"", "."} and not rel.is_absolute() and ".." not in rel.parts, "payload path escape")
    path = (root / pathlib.Path(*rel.parts)).resolve()
    require(path.is_relative_to(root.resolve()), "payload symlink escapes root")
    require(path.is_file() and path.stat().st_size == meta["bytes"], "missing/wrong-sized payload: " + str(rel))
    require(sha_file(path) == meta["sha256"], "payload hash mismatch: " + str(rel))

def time_value(value):
    require(isinstance(value, str), "UTC timestamp missing")
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "timestamp timezone missing")
    return parsed

def endpoint(record, slot, runtime):
    e = record.get("endpoint")
    require(isinstance(e, dict), "complete endpoint missing")
    ids, flags = e.get("ids"), e.get("eog")
    require(isinstance(ids, list) and 0 < len(ids) <= slot["cap"], "endpoint extent invalid")
    require(all(is_int(t) and 0 <= t < runtime["vocabulary_size"] for t in ids), "output token outside vocabulary")
    require(isinstance(flags, list) and len(flags) == len(ids) and all(type(x) is bool for x in flags), "EOG flags invalid")
    require(flags == [i in runtime["eog_ids"] for i in ids], "EOG authority mismatch")
    require(not any(flags[:-1]), "tokens committed after EOG")
    require(e.get("length") == len(ids) and e.get("terminal_id") == ids[-1], "endpoint metadata mismatch")
    reason = "EOG" if flags[-1] else "CAP"
    require(e.get("stop_reason") == reason and (reason == "EOG" or len(ids) == slot["cap"]), "stop contract mismatch")
    return e

def cycles(record, slot):
    data = record.get("cycles")
    require(isinstance(data, list), "cycle trace missing")
    if slot["k"] == 0:
        require(not data, "C1/R has speculative cycles")
        return
    output = record["endpoint"]
    ids, flags, cap = output["ids"], output["eog"], slot["cap"]
    require(isinstance(flags, list) and len(flags) == len(ids) and all(type(x) is bool for x in flags),
            "cycle endpoint EOG flags missing")
    reconstructed = [ids[0]]
    done = flags[0] or len(reconstructed) == cap
    last_keep = slot["prompt_tokens"]

    def commit_expected(token):
        position = len(reconstructed)
        require(position < len(ids) and ids[position] == token,
                "native k1 commitment does not match complete endpoint")
        reconstructed.append(token)
        return flags[position] or len(reconstructed) == cap

    for number, c in enumerate(data):
        require(not done, "cycle executed after cap/EOG termination")
        require(isinstance(c, dict) and c.get("cycle") == number, "cycle order mismatch")
        require(c.get("base") == last_keep, "cycle base does not equal previous keep")
        require(c.get("seed_id") == reconstructed[-1], "pending seed mismatch")
        require(is_int(c.get("proposal")) and isinstance(c.get("decisions"), list)
                and len(c["decisions"]) == 2 and all(is_int(x) for x in c["decisions"]),
                "k1 verification decisions missing")
        accepted = int(c["proposal"] == c["decisions"][0])
        require(is_int(c.get("accepted")) and c["accepted"] == accepted and c.get("q_caller") == 2,
                "acceptance/caller-width mismatch")
        keep = c["base"] + 1 + accepted
        require(c.get("keep") == keep, "rollback keep mismatch")
        # Match formal.cpp exactly: commit row0, then row1 iff accepted and
        # row0 did not reach cap/EOG. A terminal accepted row0 legally omits bonus.
        expected_commits = [c["decisions"][0]]
        done = commit_expected(c["decisions"][0])
        if accepted and not done:
            expected_commits.append(c["decisions"][1])
            done = commit_expected(c["decisions"][1])
        require(c.get("committed_ids") == expected_commits,
                "k1 committed IDs omit a required bonus or add a forbidden token")
        for key in ("target_kv_max", "draft_kv_max"):
            require(is_int(c.get(key)) and c[key] == keep - 1, "native post-trim " + key + " mismatch")
        if "batch_ids" in c:
            require(c["batch_ids"] == [c["seed_id"], c["proposal"]], "verification batch IDs mismatch")
        if "pending_after" in c:
            require(c["pending_after"] == (None if done else reconstructed[-1]), "post-cycle pending mismatch")
        if "done" in c:
            require(c["done"] is done, "post-cycle termination mismatch")
        last_keep = keep
    require(reconstructed == ids, "cycle trace does not reconstruct complete endpoint")
    require(done, "speculative trace ends before cap/EOG")

def vector_signature(record):
    return {key: {field: meta.get(field) for field in ("sha256", "bytes")}
            for key, meta in (record.get("vectors") or {}).items()}

def boundary_signature(record, field="boundary"):
    boundary = record.get(field)
    require(isinstance(boundary, dict), field + " state missing")
    result = {}
    for key in ("kv", "initial_logits"):
        meta = boundary.get(key)
        require(isinstance(meta, dict) and is_hash(meta.get("sha256"))
                and is_int(meta.get("bytes")) and meta["bytes"] > 0, "boundary payload identity missing")
        result[key] = {field: meta[field] for field in ("sha256", "bytes")}
    for key in ("kv_min", "kv_max", "sequence_id"):
        require(is_int(boundary.get(key)), "boundary position metadata missing")
        result[key] = boundary[key]
    return result

def compare_records(left, right, include_vectors):
    checks = {name: left.get(name) == right.get(name) for name in ("endpoint", "cycles")}
    if include_vectors:
        checks["vectors"] = vector_signature(left) == vector_signature(right)
    return checks

def load_records(path):
    records = []
    for number, line in enumerate(pathlib.Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if line.strip():
            value = json.loads(line)
            require(isinstance(value, dict), f"record line {number} is not an object")
            records.append(value)
    return records

def legacy_vector_path(key):
    if key == "target_initial":
        return pathlib.Path("target/initial.f32")
    parts = key.split("/")
    if parts[0] == "target_ordinary" and len(parts) == 2:
        return pathlib.Path("target") / ("ordinary-" + parts[1] + ".f32")
    if parts[0] == "target_verify" and len(parts) == 3:
        return pathlib.Path("target") / ("verify-" + parts[1] + "-" + parts[2] + ".f32")
    if parts[0] == "draft_proposal" and len(parts) == 2:
        return pathlib.Path("draft") / ("proposal-" + parts[1] + ".f32")
    raise ContractError("unknown logical vector key: " + key)

def audit_controls(plan, records, reference_root, payload_root):
    """Independently compare new NATURAL B0 records with delivered PR148 references.

    This compares numerical payloads/transactions, not context/binary identity:
    the P1 C1 target has UB4/output4 and is intentionally tested against strict R.
    """
    slots = validate_plan(plan)
    require(plan["status"] == "FROZEN_BEFORE_FORWARD" or not any(row.get("status") in COMPLETE for row in records),
            "new native control records cannot qualify under an unbound draft")
    by_id = {row.get("slot_id"): row for row in records}
    require(len(by_id) == len(records), "duplicate control/primary records")
    checks = []
    reference_files = {}
    for slot in slots:
        hist = slot["historical_reference"]
        if not hist:
            continue
        sid = slot["slot_id"]
        row = by_id.get(sid)
        if row is None or row.get("status") not in COMPLETE:
            checks.append({"slot_id": sid, "status": "PENDING", "passed": False})
            continue
        try:
            directory = reference_root / ("qual-" + str(hist["qual_index"]))
            reference_path = directory / "result.json"
            doc = read(reference_path)
            reference_files[str(reference_path)] = sha_file(reference_path)
            require(doc.get("status") == "QUALIFICATION_PASS", "legacy reference status invalid")
            arm_index = {"R": 0, "PQ": 1, "QB": 2}[hist["arm"]]
            old = doc["requests"][arm_index]
            require(old["input_id"] == slot["input_id"] and old["arm"] == hist["arm"], "legacy reference coordinate changed")
            expected_endpoint = {key: old[key] for key in ("ids", "eog", "length", "terminal_id", "stop_reason")}
            require(row.get("endpoint") == expected_endpoint, "historical endpoint differs")
            require(len(row.get("cycles", [])) == len(old["cycles"]), "historical cycle count differs")
            for current, previous in zip(row["cycles"], old["cycles"]):
                require(all(current.get(k) == v for k, v in previous.items()), "historical complete cycle state differs")
            for key in ("target_calls", "draft_calls"):
                require(row.get(key) == old[key], "historical " + key + " differs")
            vectors_checked = 0
            if slot["observer"] == "heavy":
                require(row.get("actual_signatures") == old["actual_signatures"], "historical actual descriptors differ")
                old_root = directory / ("qual-" + str(arm_index))
                vectors = row.get("vectors", {})
                mapped = {legacy_vector_path(key).as_posix(): meta for key, meta in vectors.items()}
                expected = {path.relative_to(old_root).as_posix(): path for path in old_root.rglob("*.f32")}
                require(set(mapped) == set(expected) and bool(expected), "historical complete vector inventory differs")
                for relative, meta in mapped.items():
                    safe_payload(payload_root, meta)
                    target = expected[relative]
                    require(meta["bytes"] == target.stat().st_size and meta["sha256"] == sha_file(target), "historical full vector bytes differ")
                    vectors_checked += 1
                actual_geometry = row.get("geometry_files", {})
                expected_geometry = {path.relative_to(old_root).as_posix(): path for path in (old_root / "target").glob("decode-*.json")}
                require(set(actual_geometry) == set(expected_geometry), "historical per-decode geometry inventory differs")
                for relative, meta in actual_geometry.items():
                    safe_payload(payload_root, meta)
                    require(read(payload_root / meta["path"]) == read(expected_geometry[relative]), "historical per-decode geometry differs")
            checks.append({"slot_id": sid, "status": "PASS", "passed": True,
                           "historical_arm": hist["arm"], "vectors_checked": vectors_checked})
        except (ContractError, OSError, KeyError, TypeError, ValueError) as exc:
            checks.append({"slot_id": sid, "status": "FAIL", "passed": False, "error": str(exc)})
    return {"schema": 1, "study_id": STUDY, "plan_sha256": digest(plan),
            "status": "PASS" if all(r["passed"] for r in checks) else "FAIL" if any(r["status"] == "FAIL" for r in checks) else "PENDING",
            "checks": checks, "legacy_reference_json_sha256": reference_files,
            "payloads_rehashed": True, "native_execution_performed": False,
            "scope": "new natural B0 numerical compatibility with delivered PR148 references; not historical binary/context identity"}

def audit_records(plan, records, payload_root=None, control_audit=None):
    slots = validate_plan(plan)
    by_slot = {s["slot_id"]: s for s in slots}
    control_checks = {r["slot_id"]: r for r in (control_audit or {}).get("checks", [])}
    if control_audit is not None:
        require(control_audit.get("plan_sha256") == digest(plan) and control_audit.get("payloads_rehashed") is True, "control audit is not for this plan/full payloads")
    seen, errors, outcomes, comparisons = {}, [], [], []
    restored_rehashed = []
    for row in records:
        try:
            sid = row.get("slot_id")
            require(sid in by_slot, "unknown slot")
            require(sid not in seen, "duplicate primary slot; retries need a separate amendment")
            seen[sid] = row
            require(row.get("attempt", 0) == 0, "automatic retry is not in this freeze")
            status = row.get("status")
            require(status in COMPLETE | FAILURE | NOT_RUN | {"STARTED"}, "unknown request status")
            if status in NOT_RUN:
                require(row.get("native_started") is False and bool(row.get("reason")), "NOT_RUN needs reason and no native start")
                continue
            require(row.get("native_started") is True, "native execution flag missing")
            require(plan["status"] == "FROZEN_BEFORE_FORWARD", "new native records cannot qualify under an unbound draft")
            if status in FAILURE | {"STARTED"}:
                require(bool(row.get("reason")), "failure/started record needs reason")
                continue
            slot = by_slot[sid]
            require(is_int(row.get("pid")) and row["pid"] > 0, "native PID missing")
            require(time_value(row.get("finished_utc")) >= time_value(row.get("started_utc")), "request time order invalid")
            require(row.get("runtime_sha256") == digest(plan["runtime"]), "runtime identity mismatch")
            require(row.get("prompt_ids_sha256") == slot["prompt_ids_sha256"], "prompt identity mismatch")
            endpoint(row, slot, plan["runtime"])
            cycles(row, slot)
            require(isinstance(row.get("checks"), dict), "checks missing")
            for key in ("module_identity", "device_placement", "actual_geometry"):
                require(row["checks"].get(key) is True, key + " failed or missing")
            require(row.get("performance_eligible") is False, "diagnostic time promoted to performance")
            if slot["route"] == "resumed":
                require(row["checks"].get("restore_roundtrip") is True, "restore roundtrip failed")
                require(row.get("extra_forward_calls_on_restore") == 0, "restore performed hidden forwards")
                restored = boundary_signature(row, "restored_boundary")
                require(restored["kv_min"] == 0 and restored["kv_max"] == slot["prompt_tokens"] - 1
                        and restored["sequence_id"] == 0, "restored boundary positions differ")
                require(restored["initial_logits"]["bytes"] == 4 * plan["runtime"]["vocabulary_size"],
                        "restored initial logits must contain the full FP32 vocabulary")
                require(payload_root is not None, "restored boundary qualification requires actual payload rehash")
                # A bool and the donor digest are insufficient: require both
                # actual post-import payload files and rehash their saved bytes.
                for key in ("kv", "initial_logits"):
                    safe_payload(payload_root, row["restored_boundary"][key])
            vectors = row.get("vectors")
            require(isinstance(vectors, dict), "vector inventory missing")
            if slot["observer"] == "heavy":
                expected_keys = {"target_initial"}
                if slot["k"] == 0:
                    expected_keys |= {"target_ordinary/" + str(i) for i in range(1, row["endpoint"]["length"])}
                else:
                    for i in range(len(row["cycles"])):
                        expected_keys |= {f"target_verify/{i}/0", f"target_verify/{i}/1", f"draft_proposal/{i}"}
                require(set(vectors) == expected_keys, "full requested vector row inventory differs")
                for meta in vectors.values():
                    require(isinstance(meta, dict) and is_hash(meta.get("sha256"))
                            and meta.get("bytes") == 4 * plan["runtime"]["vocabulary_size"], "FP32 full-vocabulary vector identity invalid")
            else:
                require(not vectors, "off request unexpectedly captured raw vectors")
            if slot["observer"] == "heavy" and slot["route"] in {"natural", "natural_spec"}:
                boundary = boundary_signature(row)
                require(boundary["kv_min"] == 0 and boundary["kv_max"] == slot["prompt_tokens"] - 1
                        and boundary["sequence_id"] == 0, "prefill boundary positions differ")
                require(boundary["initial_logits"] == vector_signature(row)["target_initial"],
                        "donor initial logits differ from the actually consumed target_initial vector")
                if payload_root is not None:
                    for key in ("kv", "initial_logits"):
                        safe_payload(payload_root, row["boundary"][key])
            if slot["route"] == "resumed" and slot["observer"] == "heavy":
                require(restored["initial_logits"] == vector_signature(row)["target_initial"],
                        "restored initial logits differ from the actually consumed target_initial vector")
            if payload_root:
                for meta in vectors.values():
                    safe_payload(payload_root, meta)
        except (ContractError, KeyError, TypeError, ValueError) as exc:
            errors.append({"slot_id": row.get("slot_id"), "error": str(exc)})

    complete = lambda sid: sid in seen and seen[sid].get("status") in COMPLETE and not any(e["slot_id"] == sid for e in errors)
    b0_slots = [s for s in slots if s["stage"] == "B0"]
    for slot in slots:
        sid = slot["slot_id"]
        if not complete(sid):
            continue
        row = seen[sid]
        for dep in slot["depends_on"]:
            if not complete(dep):
                errors.append({"slot_id": sid, "error": "dependency incomplete: " + dep})
            elif time_value(row["started_utc"]) < time_value(seen[dep]["finished_utc"]):
                errors.append({"slot_id": sid, "error": "dependency executed after dependent request: " + dep})
        compare = slot["compare_slot_id"]
        if compare and complete(compare):
            other = seen[compare]
            checks = compare_records(row, other, slot["observer"] == "heavy" and by_slot[compare]["observer"] == "heavy")
            comparisons.append({"slot_id": sid, "comparison": compare, "checks": checks})
            if not all(checks.values()):
                errors.append({"slot_id": sid, "error": "observer/own-path endpoint-cycle-vector sham failed"})
        donor = slot["donor_slot_id"]
        if donor and complete(donor):
            donor_signature = boundary_signature(seen[donor])
            if row.get("imported_boundary_sha256") != digest(donor_signature):
                errors.append({"slot_id": sid, "error": "imported donor identity mismatch"})
            if boundary_signature(row, "restored_boundary") != donor_signature:
                errors.append({"slot_id": sid, "error": "actual restored boundary bytes/positions differ from donor"})
            elif complete(sid):
                restored_rehashed.append(sid)
        match = slot["producer_match_slot_id"]
        if match and complete(match):
            if boundary_signature(row) != boundary_signature(seen[match]):
                errors.append({"slot_id": sid, "error": "consumer-specific producer bytes differ"})
        if slot["historical_reference"] and control_checks.get(sid, {}).get("passed") is not True:
            errors.append({"slot_id": sid, "error": "independent historical control audit missing/failed"})
        ref = slot["strict_reference_slot_id"]
        if ref and complete(ref):
            outcomes.append({"slot_id": sid, "strict_reference_equal": row["endpoint"] == seen[ref].get("endpoint"),
                             "producer_conditioned_endpoint_equal": row["endpoint"] == seen[donor].get("endpoint") if donor and complete(donor) else None,
                             "scope": plan["claim_scope"]})
    b0_bad = {e["slot_id"] for e in errors if e["slot_id"] in {s["slot_id"] for s in b0_slots}}
    b0_pass = all(complete(s["slot_id"]) for s in b0_slots) and not b0_bad
    b1_complete = [s for s in slots if s["stage"] == "B1" and complete(s["slot_id"])]
    if b1_complete and not b0_pass:
        errors.append({"slot_id": None, "error": "B1 executed without complete B0 qualification"})
    if b1_complete and b0_pass:
        gate_time = max(time_value(seen[s["slot_id"]]["finished_utc"]) for s in b0_slots)
        for slot in b1_complete:
            if time_value(seen[slot["slot_id"]]["started_utc"]) < gate_time:
                errors.append({"slot_id": slot["slot_id"], "error": "B1 started before the complete B0 gate"})
    layout_pairs = []
    for index in range(8):
        for producer in ("P1", "P4T"):
            pair = [s for s in slots if s["stage"] == "B1" and s["input_index"] == index
                    and s["producer"] == producer and s["consumer"] in {"PQ", "QB"}
                    and s["observer"] == "heavy"]
            if len(pair) == 2 and all(complete(s["slot_id"]) for s in pair):
                layout_pairs.append({"input_index": index, "producer": producer,
                    "slots": [s["slot_id"] for s in pair],
                    "checks": compare_records(seen[pair[0]["slot_id"]], seen[pair[1]["slot_id"]], True),
                    "scope": plan["claim_scope"]})
    counts = Counter(row.get("status") for row in seen.values())
    missing = [s["slot_id"] for s in slots if s["slot_id"] not in seen]
    failed = [sid for sid, row in seen.items() if row.get("status") in FAILURE]
    report = {
        "schema": 1, "study_id": STUDY, "plan_sha256": digest(plan),
        "validation_scope": "CPU structure, frozen coordinates, identity fields, endpoints, cycles and cross-record shams",
        "payloads_rehashed": payload_root is not None,
        "restored_boundaries_rehashed": restored_rehashed,
        "historical_control_scope": "independent audit-controls compares new natural B0 vectors, cycles and geometry to delivered PR148 references",
        "native_execution_performed_by_this_tool": False,
        "expected_primary_slots": 152, "recorded_slots": len(seen), "counts": dict(counts),
        "missing_slots": missing, "failed_slots": failed, "errors": errors,
        "b0_qualified": b0_pass, "comparisons": comparisons, "strict_reference_outcomes": outcomes,
        "pq_qb_comparisons": layout_pairs,
        "status": "INVALID" if errors else "PENDING" if missing or counts.get("STARTED") else "COMPLETE_ACCOUNTING",
    }
    return report

def verify_source(checkout):
    manifest = read(HERE / "SOURCE_PINS.json")
    checks = []
    for item in manifest["files"]:
        path = checkout / item["path"]
        actual = sha_file(path) if path.is_file() else None
        checks.append({"path": item["path"], "expected_sha256": item["sha256"],
                       "actual_sha256": actual, "passed": actual == item["sha256"]})
    return {"status": "PASS" if all(x["passed"] for x in checks) else "FAIL", "checks": checks,
            "native_execution_performed": False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("make-plan")
    make.add_argument("--panel", type=pathlib.Path)
    make.add_argument("--runtime", type=pathlib.Path)
    make.add_argument("--out", type=pathlib.Path, required=True)
    check = sub.add_parser("validate-plan")
    check.add_argument("plan", type=pathlib.Path)
    audit = sub.add_parser("validate-records")
    audit.add_argument("--plan", type=pathlib.Path, required=True)
    audit.add_argument("--records", type=pathlib.Path, required=True)
    audit.add_argument("--payload-root", type=pathlib.Path)
    audit.add_argument("--control-audit", type=pathlib.Path)
    audit.add_argument("--report", type=pathlib.Path, required=True)
    audit.add_argument("--require-complete", action="store_true")
    controls = sub.add_parser("audit-controls")
    controls.add_argument("--plan", type=pathlib.Path, required=True)
    controls.add_argument("--records", type=pathlib.Path, required=True)
    controls.add_argument("--reference-root", type=pathlib.Path, required=True)
    controls.add_argument("--payload-root", type=pathlib.Path, required=True)
    controls.add_argument("--out", type=pathlib.Path, required=True)
    source = sub.add_parser("verify-source")
    source.add_argument("--checkout", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "make-plan":
            require(bool(args.panel) == bool(args.runtime), "supply both real panel and runtime, or neither for an unbound draft")
            plan = build_plan(read(args.panel) if args.panel else None, read(args.runtime) if args.runtime else None)
            write_new(args.out, plan)
            print(json.dumps({"status": plan["status"], "primary_slots": 152, "native_executions": 0}))
        elif args.command == "validate-plan":
            plan = read(args.plan)
            validate_plan(plan)
            print(json.dumps({"status": "VALID", "binding": plan["status"], "primary_slots": 152, "native_executions": 0}))
        elif args.command == "verify-source":
            result = verify_source(args.checkout)
            print(json.dumps(result, indent=2))
            return 0 if result["status"] == "PASS" else 2
        elif args.command == "audit-controls":
            result = audit_controls(read(args.plan), load_records(args.records), args.reference_root, args.payload_root)
            write_new(args.out, result)
            print(json.dumps({"status": result["status"], "checks": len(result["checks"])}))
            return 0 if result["status"] == "PASS" else 2
        else:
            result = audit_records(read(args.plan), load_records(args.records), args.payload_root,
                                   read(args.control_audit) if args.control_audit else None)
            write_new(args.report, result)
            print(json.dumps({k: result[k] for k in ("status", "expected_primary_slots", "recorded_slots", "b0_qualified")}))
            return 2 if result["status"] == "INVALID" or (args.require_complete and result["status"] != "COMPLETE_ACCOUNTING") else 0
    except (ContractError, OSError, json.JSONDecodeError, KeyError) as exc:
        print("CONTRACT_ERROR: " + str(exc), file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

