#!/usr/bin/env python3
"""CPU-only RTX scope-transfer design, record audit and finite-panel analysis.

No command imports a native controller, downloads weights, compiles a worker or
executes a model. The record envelope documented in RECORD_SCHEMA.md is a new
host-adapter contract; the existing rtx_bridge worker does not emit it yet.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import sys

STUDY = "rtx_scope_transfer_v1"
REPO = Path(__file__).resolve().parents[3]
DESIGN = REPO / "benchmarks" / STUDY
BASE = "9149b6f5f5a4dcde1b6124c654dc0ba1241ca509"
PANEL_COMMIT = "79f6e6d687f87465219a7557bc4c8306e9b13149"
PANEL_SOURCE = "benchmarks/rtx_jsa_closeout_v1/revision_a/INPUT_MANIFEST.json"
PANEL_SHA = "5087de106148cf8497a3753f4075f59f76c8eeab88792869b86b9e12cd0f3ce3"
MODEL_SHA = "7fe5ad4dfff880b9da0394c1448eb6c3fb5cd733769e20319cf1fac1a9dc986d"
COUNTEREXAMPLE_SHA = "2bca6cbbf02cbaeaf5750899bfb5fc72742289a3d03519a50e98c2f8ad92cbdb"
FAMILIES = ("Qwen", "SmolLM2")
ARMS = ("R", "M_GS", "M_PQ", "M_QB", "C_GS", "C_PQ", "C_QB")
SCOPES = ("GS", "PQ", "QB")
SOURCE_VARIANTS = {"Qwen": "original", "SmolLM2": "metadata4", "Llama": "metadata4"}
SOURCE_ZIPS = {"original": "62086688fc095be2654ae25aad2c7780c94db8617db5a6a9f71504f49897bf7e",
               "metadata4": "36be0d738ad5d29579b75825f68337003eb127405cc5418abc566cb07718a4d8"}
SEED = "rtx-scope-transfer-20261027-v1"
LOCAL_TZ = timezone(timedelta(hours=8), "Asia/Shanghai")
END_KEYS = ("ids", "eog", "length", "terminal_id", "stop_reason")
SPEC_KEYS = ("study_id", "slot_id", "unit_id", "stage", "family", "input_id",
             "prompt_ids_sha256", "date_slot", "session_slot", "block_id", "arm",
             "scope", "layout_selector", "scoped_target", "target_ub", "target_outputs",
             "draft_enabled", "k", "lifecycle", "observer", "producer", "reference_id")
FAILURES = {"REFERENCE_MISMATCH", "COMPLETE_COUNTEREXAMPLE", "OBSERVER_INTERFERENCE",
            "GEOMETRY_NOT_ADMITTED", "RESTORE_SHAM_FAILED", "NUMERICAL_FAILURE"}
RECORD_STATUSES = {"COMPLETE", "TECHNICAL_FAILURE", "BUDGET_EXHAUSTED",
                   "NOT_RUN_DEPENDENCY", "NOT_RUN_DATE_UNAVAILABLE", *FAILURES}


class ContractError(ValueError):
    pass


def need(ok, message):
    if not ok:
        raise ContractError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def hash_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    def reject(value):
        raise ContractError("nonfinite JSON extension: " + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=reject)


def read(path):
    return strict_json(Path(path).read_bytes())


def lines(path):
    return [strict_json(line) for line in Path(path).read_bytes().splitlines() if line.strip()]


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")


def save_lines(path, rows):
    Path(path).write_bytes(b"".join(canonical(r) + b"\n" for r in rows))


def is_hash(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def utc(value):
    need(isinstance(value, str), "UTC timestamp required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    need(result.tzinfo is not None and result.utcoffset() == timedelta(0), "explicit UTC timestamp required")
    return result


def local_date(value):
    return utc(value).astimezone(LOCAL_TZ).date().isoformat()


def ordered(values, *parts):
    return sorted(values, key=lambda x: (digest((SEED + "|" + "|".join(map(str, parts)) + "|" + str(x)).encode()), str(x)))


def arm_spec(arm):
    need(arm in ARMS, "unknown arm")
    scope = "R" if arm == "R" else arm[-2:]
    return {"arm": arm, "scope": scope, "layout_selector": {"R": 1, "GS": 2, "PQ": 1, "QB": 0}[scope],
            "scoped_target": arm != "R", "target_ub": 1 if arm == "R" else 4,
            "target_outputs": 1 if arm == "R" else 4,
            "draft_enabled": arm.startswith("C_"), "k": 3 if arm.startswith("C_") else 0}


def extract_inputs(manifest_path, contract_path):
    need(hash_file(manifest_path) == PANEL_SHA, "PR144 input manifest SHA256 differs")
    need(hash_file(contract_path) == MODEL_SHA, "PR144 model contract SHA256 differs")
    source, models = read(manifest_path), read(contract_path)
    panel = {"schema": 1, "study_id": STUDY, "source_commit": PANEL_COMMIT,
             "source_path": PANEL_SOURCE, "source_sha256": PANEL_SHA,
             "exposure": "EXPOSED_IN_PR144; independent of original repair panel; not blind now",
             "prompt_hash_encoding": "SHA256 of compact UTF-8 JSON integer array, no trailing LF",
             "families": {}, "llama_diagnostic": [], "llama_unrun_confirmation_reserve": []}
    pins = {"schema": 1, "source_commit": PANEL_COMMIT, "source_sha256": MODEL_SHA, "families": {}}
    for family in (*FAMILIES, "Llama"):
        inputs = source["panel"][family]
        need(len(inputs) == 12 and len({x["id"] for x in inputs}) == 12, "fixed panel size/identity differs")
        contract = models["families"][family]
        pins["families"][family] = {
            "source_variant": SOURCE_VARIANTS[family], "source_zip_sha256": SOURCE_ZIPS[SOURCE_VARIANTS[family]],
            "models": {role: {k: v[k] for k in ("sha256", "bytes")} for role, v in contract["models"].items()},
            **{k: contract[k] for k in ("vocabulary_sha256", "vocabulary_tokens", "eog", "template_sha256",
                                       "draft_template_sha256", "tokenizer_metadata", "architecture_shapes")}}
        selected = []
        for index, item in enumerate(inputs):
            ids = item["prompt_ids"]
            need(ids and all(type(i) is int and 0 <= i < contract["vocabulary_tokens"] for i in ids), "invalid prompt IDs")
            need(len(ids) == item["prompt_token_count"] and item["cap"] == 128, "prompt count/cap differs")
            need(len(ids) + 128 + 3 <= 1024, "prompt + cap + speculative reserve exceeds context")
            row = {"family": family, "source_index": index, "id": item["id"], "prompt_ids": ids,
                   "prompt_ids_sha256": digest(canonical(ids)), "prompt_tokens": len(ids), "cap": 128,
                   "dataset_snapshot": item["snapshot"], "stratum": item["stratum"], "domain": item["domain_group"],
                   "source_entry_sha256": digest(canonical(item)), "selection_hash": item["selection_hash"],
                   "historical_token_ids_sha256": item.get("token_ids_sha256"),
                   "reference_id": f"pr144/{family}/{index:02d}/{item['id']}"}
            selected.append(row)
        if family in FAMILIES:
            panel["families"][family] = selected
        else:
            for index, role in ((8, "known_failure"), (6, "long_pass_control"), (3, "short_pass_control")):
                panel["llama_diagnostic"].append({**selected[index], "role": role})
            panel["llama_unrun_confirmation_reserve"] = [selected[i] for i in (9, 10, 11)]
    need([(x["id"], x["prompt_tokens"]) for x in panel["llama_diagnostic"]] ==
         [("CodeContests/valid/108", 737), ("CodeContests/valid/43", 443), ("GSM8K/test/496", 77)], "Llama diagnostic selection differs")
    return panel, pins


def schedules(panel):
    slots, diagnostic = [], []
    def add(dest, family, item, arm, stage, unit, block, order, date=None, session=None, observer="off", producer="NATIVE", **extra):
        spec = arm_spec(arm)
        dest.append({"schema": 1, "study_id": STUDY, "slot_id": f"{unit}/{stage}/{block}/{arm}/{observer}",
                     "unit_id": unit, "unit_order": order, "position_in_unit": sum(r["unit_id"] == unit for r in dest),
                     "stage": stage, "family": family, "input_id": item["id"], "source_index": item["source_index"],
                     "prompt_ids_sha256": item["prompt_ids_sha256"], "reference_id": item["reference_id"],
                     "date_slot": date, "session_slot": session, "block_id": f"{unit}/{stage}/{block}",
                     **spec, "producer": producer, "lifecycle": "fresh" if stage.startswith("diagnostic") else "resident",
                     "observer": observer, "expected_status": "PENDING", **extra})
    for family_index, family in enumerate(FAMILIES):
        base = ordered(ARMS, "latin-base", family)
        for item in panel["families"][family]:
            i = item["source_index"]
            for arm in base[i % 7:] + base[:i % 7]:
                add(slots, family, item, arm, "qualification", f"qualification/{family}", f"heavy-{i:02d}", family_index, observer="heavy")
        for i in (0, 11):
            item = panel["families"][family][i]
            for arm in base[i % 7:] + base[:i % 7]:
                add(slots, family, item, arm, "qualification", f"qualification/{family}", f"off-{i:02d}", family_index)
    for day in range(3):
        family_order = FAMILIES if day % 2 == 0 else FAMILIES[::-1]
        for session in range(2):
            s = day * 2 + session
            for fi, family in enumerate(family_order):
                base = ordered(ARMS, "latin-base", family)
                unit, order = f"formal/d{day}/s{session}/{family}", 2 + day * 4 + session * 2 + fi
                warm = panel["families"][family][0]
                r = (s + 12) % 7
                for arm in base[r:] + base[:r]:
                    add(slots, family, warm, arm, "warmup", unit, "warm-00", order, day, session)
                for i in ordered(range(12), "input-order", family, s):
                    item, r = panel["families"][family][i], (s + i) % 7
                    for arm in base[r:] + base[:r]:
                        add(slots, family, item, arm, "formal", unit, f"input-{i:02d}", order, day, session)
    for stage, producers, arms in (("diagnostic_A1", ("NATIVE",), ("R", "C_PQ", "C_QB")),
                                    ("diagnostic_A2", ("P1", "P4_NATIVE"), ("M_PQ", "C_PQ", "C_QB"))):
        for item in panel["llama_diagnostic"]:
            for producer in producers:
                for observer in ("off", "heavy"):
                    for arm in arms:
                        add(diagnostic, "Llama", item, arm, stage, stage + "/Llama",
                            f"i{item['source_index']:02d}-{producer}-{observer}", 0,
                            observer=observer, producer=producer,
                            diagnostic_only=True, consumer="C1" if arm == "M_PQ" else arm,
                            expected_role=item["role"])
    need(Counter(x["stage"] for x in slots) == {"qualification": 196, "formal": 1008, "warmup": 84}, "schedule budget differs")
    need(Counter(x["stage"] for x in diagnostic) == {"diagnostic_A1": 18, "diagnostic_A2": 36}, "diagnostic budget differs")
    need(len({x["slot_id"] for x in slots + diagnostic}) == len(slots + diagnostic), "duplicate slot identity")
    return slots, diagnostic


def prepare(manifest, contract, design):
    panel, pins = extract_inputs(manifest, contract)
    slots, diagnostic = schedules(panel)
    design = Path(design)
    save(design / "PANEL.json", panel)
    save(design / "MODEL_PINS.json", pins)
    save_lines(design / "SLOTS.jsonl", slots)
    save_lines(design / "DIAGNOSTIC_SLOTS.jsonl", diagnostic)
    return check_plan(design)


def check_plan(design):
    design = Path(design)
    panel, pins, plan = read(design / "PANEL.json"), read(design / "MODEL_PINS.json"), read(design / "PLAN.json")
    need(panel["source_sha256"] == PANEL_SHA and pins["source_sha256"] == MODEL_SHA, "source pin drift")
    need(plan["base_commit"] == BASE and plan["date_timezone"] == "Asia/Shanghai", "base/date contract drift")
    need(plan["date_first_session_gap_hours_minimum"] == 20, "date spacing drift")
    for family, items in panel["families"].items():
        need(family in FAMILIES and len(items) == 12, "family/panel size drift")
        for item in items:
            need(digest(canonical(item["prompt_ids"])) == item["prompt_ids_sha256"] and len(item["prompt_ids"]) == item["prompt_tokens"], "prompt hash/count drift")
    expected, diag = schedules(panel)
    need(lines(design / "SLOTS.jsonl") == expected, "schedule is not exact deterministic reconstruction")
    need(lines(design / "DIAGNOSTIC_SLOTS.jsonl") == diag, "diagnostic schedule drift")
    counts = Counter(x["stage"] for x in expected)
    return {"status": "PLAN_VALID", "execution_status": "NOT_RUN", "native_status": "NATIVE_EXTENSION_REQUIRED", "new_native_executions": 0,
            "factorial_slots": dict(counts), "diagnostic_slots": len(diag), "dates": 3,
            "date_timezone": "Asia/Shanghai", "planned_family_session_workers": 12,
            "native_worker_implemented": False, "native_compiled": False, "native_qualified": False}


def endpoint(value, model, cap=128):
    need(all(k in value for k in END_KEYS), "incomplete endpoint")
    ids, flags = value["ids"], value["eog"]
    need(isinstance(ids, list) and 0 < len(ids) <= cap and all(type(v) is int and 0 <= v < model["vocabulary_tokens"] for v in ids), "bad output IDs")
    need(isinstance(flags, list) and len(flags) == len(ids) and all(type(v) is bool for v in flags), "bad EOG flags")
    need(flags == [i in model["eog"] for i in ids], "EOG classification differs")
    need(type(value["length"]) is int and value["length"] == len(ids) and value["terminal_id"] == ids[-1], "length/terminal mismatch")
    need(not any(flags[:-1]), "output continued after EOG")
    need(value["stop_reason"] == ("EOG" if flags[-1] else "CAP"), "stop reason differs")
    need(flags[-1] or len(ids) == cap, "truncated endpoint is not a full request")
    return {k: value[k] for k in END_KEYS}


def validate_cycles(record, item, model):
    """Recompute existing bridge transaction fields; all verification rows remain."""
    cycles = record["cycles"]
    if not record["draft_enabled"]:
        need(cycles == [], "target-only arm unexpectedly drafts")
        need(record["draft_calls"] == 0 and record["draft_final_kv"] is None, "target-only draft state/calls")
        return
    out, k, base = [record["endpoint"]["ids"][0]], record["k"], item["prompt_tokens"]
    done = out[-1] in model["eog"] or len(out) == item["cap"]
    pending = out[0]
    need(isinstance(cycles, list), "cycles required")
    for index, c in enumerate(cycles):
        need(not done and c["cycle"] == index and c["base"] == base and c["seed"] == pending, "cycle/pending/base differs")
        p, decisions = c["proposals"], c["decisions"]
        need(len(p) == k and len(decisions) == k + 1 and c["caller_rows"] == k + 1, "missing proposed or unexamined verification rows")
        need(all(type(v) is int and 0 <= v < model["vocabulary_tokens"] for v in p + decisions), "invalid decision IDs")
        accepted, rejected, kind = 0, False, None
        for j in range(k):
            if done:
                break
            if p[j] == decisions[j]:
                accepted += 1
                token, kind = p[j], "accepted"
            else:
                token, kind, rejected = decisions[j], "correction", True
                pending = token
            out.append(token)
            done = token in model["eog"] or len(out) == item["cap"]
            if rejected:
                break
        if accepted == k and not done:
            pending, kind = decisions[k], "bonus"
            out.append(pending)
            done = pending in model["eog"] or len(out) == item["cap"]
        keep = base + 1 + accepted
        expected = {"accepted": accepted, "rejected": rejected, "commit_kind": kind,
                    "output_length": len(out), "pending_after": None if done else pending,
                    "done": done, "keep": keep}
        need(all(c.get(key) == value for key, value in expected.items()), "transaction conservation/commit mismatch")
        for role in ("target", "draft"):
            need(c[role + "_before"] == {"min": 0, "max": base - 1}, "precycle KV bound differs")
            need(c[role + "_after"] == {"min": 0, "max": keep - 1}, "trim/rollback bound differs")
        base = keep
    need(done and out == record["endpoint"]["ids"], "cycles do not reconstruct complete endpoint")
    for role in ("target", "draft"):
        need(record[role + "_final_kv"] == {"min": 0, "max": base - 1}, "final KV bound differs")


def payload(bundle, pin):
    need(isinstance(pin, dict) and is_hash(pin.get("sha256")) and type(pin.get("bytes")) is int, "payload pin incomplete")
    path = Path(pin["path"])
    need(not path.is_absolute() and ".." not in path.parts, "payload path must stay inside bundle")
    resolved = (bundle / path).resolve()
    need(resolved.is_relative_to(bundle.resolve()), "payload escapes bundle")
    need(resolved.is_file() and resolved.stat().st_size == pin["bytes"] and hash_file(resolved) == pin["sha256"], "payload missing/hash mismatch: " + str(path))
    return resolved


def dates_ok(receipts, calendar_dates, families=FAMILIES):
    need(len(calendar_dates) == 3 and len(set(calendar_dates)) == 3 and sorted(calendar_dates) == calendar_dates, "three increasing local dates required")
    formal = [x for x in receipts if x["unit_id"].startswith("formal/")]
    need(len(formal) == 6 * len(families), "six selected sessions per included family required")
    times = {}
    for r in formal:
        day, session = r["date_slot"], r["session_slot"]
        need(type(day) is int and day in range(3) and type(session) is int and session in range(2), "date/session slot differs")
        start, end = utc(r["process_start_utc"]), utc(r["process_end_utc"])
        need(start < end and local_date(r["process_start_utc"]) == calendar_dates[day] == local_date(r["process_end_utc"]), "worker crosses/mislabels Asia/Shanghai date")
        key = (day, session, r["family"])
        need(key not in times, "duplicate family/session date receipt")
        times[key] = start
    for day in (1, 2):
        for family in families:
            need(times[(day, 0, family)] - times[(day - 1, 0, family)] >= timedelta(hours=20), "family adjacent-date first sessions are less than 20 hours apart")
        need(min(times[(day, 0, f)] for f in families) - min(times[(day - 1, 0, f)] for f in families) >= timedelta(hours=20), "adjacent-date first sessions less than 20 hours apart")
    expected_order = []
    for day in range(3):
        for session in range(2):
            for family in (FAMILIES if day % 2 == 0 else FAMILIES[::-1]):
                if family in families:
                    expected_order.append((day, session, family))
    need(sorted(times, key=times.get) == expected_order, "frozen family/session order differs")
    return True


def identity_errors(binding, plan, design, models):
    errors = []
    try:
        need(binding["schema"] == 1 and binding["study_id"] == STUDY and binding["is_synthetic"] is False and binding["status"] == "FROZEN_BEFORE_FIRST_NATIVE_REQUEST", "missing, unbound or synthetic execution binding")
        for key, name in (("plan_sha256", "PLAN.json"), ("panel_sha256", "PANEL.json"), ("schedule_sha256", "SLOTS.jsonl")):
            need(binding[key] == hash_file(design / name), "execution binding differs: " + key)
        need(binding["date_timezone"] == "Asia/Shanghai", "execution timezone differs")
        utc(binding["frozen_utc"])
        need(all(type(binding["resource_caps"][k]) is int and binding["resource_caps"][k] > 0
                 for k in ("worker_timeout_seconds", "total_owned_seconds", "payload_bytes", "minimum_free_bytes")), "host resource caps must be bound before native execution")
        need(isinstance(binding["calendar_dates"], list) and len(binding["calendar_dates"]) == 3, "host must freeze three local dates before first formal request")
        for family in FAMILIES:
            b, m = binding["families"][family], models["families"][family]
            for key in ("source_variant", "source_zip_sha256", "models", "vocabulary_sha256", "template_sha256"):
                need(b[key] == m[key], "family identity differs: " + family + "/" + key)
            for key in ("executable_sha256", "core_sha256", "worker_source_sha256", "build_receipt_sha256"):
                need(is_hash(b[key]), "unbound build field: " + family + "/" + key)
            need(isinstance(b["numerical_modules"], dict) and len(b["numerical_modules"]) == 21 and all(is_hash(v) for v in b["numerical_modules"].values()), "exact 21-library manifest required")
            need({"ggml-base.dll", "ggml-cuda.dll", "cublas64_12.dll", "cublasLt64_12.dll", "cudart64_12.dll"} <= set(b["numerical_modules"]), "required loaded numerical modules missing")
            need(b["context"] == plan["context"], "runtime contract differs")
            need(all(isinstance(b[key], str) and b[key] for key in ("host_id", "device_id", "driver")), "host/device/driver identity missing")
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(str(exc))
    return errors


def local_geometry(record):
    """Read observed query tensors, including the pinned metadata4 name alias.

    llama-graph.cpp names the same q view twice: hs_attn_query_batch followed
    by jsa_llama_query_batch. Its actual metadata survives as kq's second input.
    No dimensions, strides, layers or device values are synthesized here.
    """
    prefix = "hs_attn_query_batch-" if record["scope"] == "QB" else "hs_attention_q-"
    result = [g for g in record["geometry"] if g["name"].startswith(prefix)]
    identity = record.get("identity", {})
    if (record["scope"] == "QB" and record["family"] == "SmolLM2"
            and identity.get("source_variant") == "metadata4"
            and identity.get("source_zip_sha256") == SOURCE_ZIPS["metadata4"]):
        for node in record["geometry"]:
            name = node["name"]
            sources = node.get("sources", [])
            if (name.startswith("kq-") and name[3:].isdigit()
                    and node.get("op") == "MUL_MAT" and len(sources) == 2
                    and sources[1].get("name") == "jsa_llama_query_batch-" + name[3:]):
                result.append(sources[1])
    return result


def audit(design, bundle):
    """Fail closed. Missing/failed slots stay in denominators, never imputed."""
    design, bundle = Path(design), Path(bundle)
    check_plan(design)
    plan, panel, models = read(design / "PLAN.json"), read(design / "PANEL.json"), read(design / "MODEL_PINS.json")
    slots = lines(design / "SLOTS.jsonl")
    expected = {r["slot_id"]: r for r in slots}
    rows = lines(bundle / "REQUESTS.jsonl") if (bundle / "REQUESTS.jsonl").is_file() else []
    result = {"schema": 1, "study_id": STUDY, "status": "INCOMPLETE_OR_UNQUALIFIED", "qualified_performance": None,
              "planned": dict(Counter(x["stage"] for x in slots)), "records_received": len(rows),
              "new_executions_by_this_auditor": 0, "failures": [], "families": {f: {"eligible": False, "errors": []} for f in FAMILIES},
              "missing_slot_ids": [], "selected_record_count": 0, "is_synthetic": any(r.get("is_synthetic") is True for r in rows)}
    received = {r.get("slot_id") for r in rows}
    result["missing_slot_ids"] = sorted(set(expected) - received)
    required = ("EXECUTION_IDENTITY.json", "REFERENCES.json", "ATTEMPTS.json", "REQUESTS.jsonl")
    missing = [name for name in required if not (bundle / name).is_file()]
    if missing:
        result["failures"].append("missing bundle files: " + ", ".join(missing))
        return result, []
    binding, references, attempts = read(bundle / required[0]), read(bundle / required[1]), read(bundle / required[2])
    result["failures"].extend(identity_errors(binding, plan, design, models))
    if result["is_synthetic"]:
        result["failures"].append("synthetic fixtures are not native evidence")
    if result["failures"]:
        return result, []
    by_attempt = defaultdict(list)
    seen = set()
    for r in rows:
        key = (r.get("slot_id"), r.get("attempt_id"))
        if r.get("slot_id") not in expected or key in seen:
            result["failures"].append("unknown/duplicate slot-attempt: " + str(key))
        seen.add(key)
        by_attempt[r.get("attempt_id")].append(r)
    if result["failures"]:
        return result, []
    units = defaultdict(list)
    for s in slots:
        units[s["unit_id"]].append(s)
    receipts = defaultdict(list)
    try:
        need(isinstance(attempts, list), "ATTEMPTS must be a list")
        need(len({a["attempt_id"] for a in attempts}) == len(attempts), "duplicate attempt ID")
        for a in attempts:
            need(a["unit_id"] in units, "unplanned execution unit")
            need(a["status"] in {"COMPLETE", "TECHNICAL_FAILURE", *FAILURES, "BUDGET_EXHAUSTED"}, "invalid process disposition")
            need(utc(a["process_end_utc"]) > utc(a["process_start_utc"]), "invalid owned process interval")
            need((utc(a["process_end_utc"]) - utc(a["process_start_utc"])).total_seconds() <= binding["resource_caps"]["worker_timeout_seconds"], "owned worker time ceiling exceeded")
            for r in by_attempt[a["attempt_id"]]:
                need(expected[r["slot_id"]]["unit_id"] == a["unit_id"] and r["status"] in RECORD_STATUSES, "record/attempt unit or status differs")
                need(type(r["started"]) is bool, "started disposition required")
                if r["status"].startswith("NOT_RUN"):
                    need(r["started"] is False and r.get("reason") and r.get("failure_id"), "NOT_RUN requires cause; no inferred measurement")
            receipts[a["unit_id"]].append(a)
        need(set(by_attempt) <= {a["attempt_id"] for a in attempts}, "records without owned-process receipt")
        retries = sum(a["attempt_index"] == 1 for a in attempts)
        need(retries <= 2, "technical session retry budget exceeded")
        started = sum(r.get("started") is True for r in rows)
        need(started <= 1288 + 182, "request budget including technical reserve exceeded")
        need(sum((utc(a["process_end_utc"]) - utc(a["process_start_utc"])).total_seconds() for a in attempts) <= binding["resource_caps"]["total_owned_seconds"], "total owned time ceiling exceeded")
    except (KeyError, TypeError, ValueError) as exc:
        result["failures"].append(str(exc))
        return result, []
    selected, selected_receipts = [], []
    items = {(f, x["id"]): x for f, v in panel["families"].items() for x in v}
    for unit, planned in units.items():
        family = planned[0]["family"]
        error = result["families"][family]["errors"]
        try:
            candidates = sorted(receipts[unit], key=lambda a: a["attempt_index"])
            need([a["attempt_index"] for a in candidates] in ([0], [0, 1]), "missing/invalid unit attempts: " + unit)
            if len(candidates) == 2:
                need(unit.startswith("formal/") and candidates[0]["status"] == "TECHNICAL_FAILURE", "only technical formal-session failure permits retry")
                need(not any(r["status"] in FAILURES for r in by_attempt[candidates[0]["attempt_id"]]), "numerical failure cannot be retried")
                need(utc(candidates[0]["process_end_utc"]) <= utc(candidates[1]["process_start_utc"]), "attempts overlap")
                need(local_date(candidates[0]["process_start_utc"]) == local_date(candidates[1]["process_start_utc"]), "technical retry changes study date")
            a = candidates[-1]
            need(a["status"] == "COMPLETE" and a["family"] == family and a["cleanup_verified"] is True, "unit not complete/cleaned: " + unit)
            need(a["date_slot"] == planned[0]["date_slot"] and a["session_slot"] == planned[0]["session_slot"], "receipt date/session slot differs")
            current = by_attempt[a["attempt_id"]]
            need([r["slot_id"] for r in current] == [s["slot_id"] for s in planned], "missing/reordered unit slots: " + unit)
            need(utc(binding["frozen_utc"]) < utc(a["process_start_utc"]), "execution precedes freeze")
            previous = utc(a["process_start_utc"])
            for r, s in zip(current, planned):
                need(r["schema"] == 1 and r["is_synthetic"] is False and r["started"] is True and r["status"] == "COMPLETE", "noncomplete or synthetic request")
                need(all(r.get(k) == s[k] for k in SPEC_KEYS), "request differs from frozen slot: " + s["slot_id"])
                need(r["identity"] == binding["families"][family], "actual execution/module/model identity differs")
                need(r["pid"] == a["pid"] and r["process_start_utc"] == a["process_start_utc"], "request process identity differs")
                start, end = utc(r["request_start_utc"]), utc(r["request_end_utc"])
                need(previous <= start < end <= utc(a["process_end_utc"]), "request time/order outside process")
                previous = end
                if s["date_slot"] is not None:
                    need(r["date_timezone"] == "Asia/Shanghai" and r["actual_date"] == local_date(r["request_start_utc"]) == local_date(r["request_end_utc"]) == binding["calendar_dates"][s["date_slot"]], "actual local date differs")
                item, model = items[(family, s["input_id"])], models["families"][family]
                got = endpoint(r["endpoint"], model, item["cap"])
                ref = references["endpoints"][s["reference_id"]]
                need(ref["source_commit"] == PANEL_COMMIT and ref["source_kind"] == "PR144_HISTORICAL_R", "historical reference provenance differs")
                original = read(payload(bundle, ref["raw_payload"]))
                # Adapter stores a preserved original R record plus an explicit
                # JSON key path; it cannot silently replace the old R with new R.
                for key in ref["endpoint_key_path"]:
                    original = original[key]
                normalized = {"ids": original["ids"], "eog": original.get("eog", original.get("eog_flags")),
                              **{k: original[k] for k in ("length", "terminal_id", "stop_reason")}}
                need(endpoint(ref["endpoint"], model) == endpoint(normalized, model) == got, "fixed historical R endpoint mismatch")
                need(isinstance(r["service_seconds"], (int, float)) and not isinstance(r["service_seconds"], bool) and math.isfinite(r["service_seconds"]) and r["service_seconds"] > 0, "invalid service duration")
                need(r["service_timer_definition"] == plan["service_timer_definition"], "service clock definition differs")
                need(r["observed_scope"] == s["scope"] and r["context_scope_fixed"] is True and r["context"] == {**plan["context"], "target_ub": s["target_ub"], "target_outputs": s["target_outputs"]}, "scope/context binding differs")
                need(r["prompt_tokens"] == item["prompt_tokens"] and r["prompt_ids_sha256"] == item["prompt_ids_sha256"], "actual native prompt differs")
                native = read(payload(bundle, r["raw_native_record"]))
                for key in ("identity", "endpoint", "cycles", "target_final_kv", "draft_final_kv", "draft_calls", "service_seconds", "observed_scope", "context", "physical_widths", "geometry", "prompt_tokens", "prompt_ids_sha256", "context_scope_fixed"):
                    need(native[key] == r[key], "adapter differs from retained native record: " + key)
                validate_cycles(r, item, model)
                if s["observer"] == "heavy":
                    need(r["physical_widths"] and all(type(w) is int and w > 0 for w in r["physical_widths"]), "physical width evidence absent")
                    if s["scope"] in ("GS", "R"):
                        need(set(r["physical_widths"]) == {1}, "GS/R physical target width is not one")
                    elif s["draft_enabled"]:
                        need(4 in r["physical_widths"] or len(r["cycles"]) == 0, "local verifier lacks batched physical width")
                    if s["scope"] in ("PQ", "QB"):
                        geometry = local_geometry(r)
                        layers = {int(g["name"].rsplit("-", 1)[1]) for g in geometry}
                        shapes = model["architecture_shapes"]["target"]
                        count = next(v for k, v in shapes.items() if k.endswith(".block_count"))
                        heads = next(v for k, v in shapes.items() if k.endswith(".attention.head_count"))
                        need(layers == set(range(count)), "local geometry lacks family-specific target layers")
                        need(all(g["ne"][1] == 1 and g["ne"][2] == heads and len(g["nb"]) == 4 and all(type(v) is int and v > 0 for v in g["nb"]) and "5070" in g["device"] for g in geometry), "actual local tensor geometry/placement differs")
                        if s["scope"] == "PQ":
                            need(all(g["ne"][3] == 1 for g in geometry), "PQ attention query axis differs")
                        elif r["cycles"]:
                            need(any(g["ne"][3] == 4 for g in geometry), "QB has no observed four-row attention batch")
                    need(r["raw_vectors"], "complete heavy vector inventory missing")
                    names = set()
                    for v in r["raw_vectors"]:
                        need(v["name"] not in names and v["dtype"] == "float32" and v["bytes"] == 4 * model["vocabulary_tokens"], "bad full-vocabulary vector inventory")
                        names.add(v["name"])
                        payload(bundle, v)
                    required_vectors = {"target/initial.f32"}
                    if s["draft_enabled"]:
                        required_vectors |= {f"draft/proposal-{c['cycle']}-{j}.f32" for c in r["cycles"] for j in range(3)}
                        required_vectors |= {f"target/verify-{c['cycle']}-{j}.f32" for c in r["cycles"] for j in range(4)}
                    else:
                        required_vectors |= {f"target/ordinary-{j}.f32" for j in range(1, got["length"])}
                    need(names == required_vectors, "missing/extra decision vectors including unexamined rows")
            selected.extend(current)
            selected_receipts.append(a)
        except (KeyError, IndexError, TypeError, ValueError, OSError) as exc:
            error.append(unit + ": " + str(exc))
    for family in FAMILIES:
        try:
            dates_ok([a for a in selected_receipts if a["unit_id"].startswith("formal/") and a["family"] == family], binding["calendar_dates"], (family,))
        except (KeyError, TypeError, ValueError) as exc:
            result["families"][family]["errors"].append(str(exc))
    try:
        # Global timing/cleanup applies to all attempts, including a failed
        # family. Numerical failure in one family need not disqualify the other.
        ordered_receipts = sorted(attempts, key=lambda a: utc(a["process_start_utc"]))
        need(all(a["cleanup_verified"] is True for a in ordered_receipts), "unreconciled worker cleanup")
        need(all(utc(a["process_end_utc"]) <= utc(b["process_start_utc"]) for a, b in zip(ordered_receipts, ordered_receipts[1:])), "owned workers overlap")
        need(len({(a["pid"], a["process_start_utc"]) for a in selected_receipts}) == len(selected_receipts), "sessions did not independently reload processes")
        formal_receipts = [a for a in selected_receipts if a["unit_id"].startswith("formal/")]
        if len(formal_receipts) == 12:
            dates_ok(formal_receipts, binding["calendar_dates"])
    except (KeyError, TypeError, ValueError) as exc:
        result["failures"].append(str(exc))
    for family in FAMILIES:
        state = result["families"][family]
        own = [r for r in selected if r["family"] == family]
        state["selected_counts"] = dict(Counter(r["stage"] for r in own))
        state["logical_work_equal"] = None
        try:
            need(state["selected_counts"] == {"qualification": 98, "warmup": 42, "formal": 504}, "full fixed-panel qualification/formal denominator incomplete")
            grouped = defaultdict(dict)
            for r in own:
                grouped[(r["stage"], r["date_slot"], r["session_slot"], r["input_id"], r["observer"])][r["arm"]] = r
            work_equal = True
            for key, g in grouped.items():
                for prefix in ("M", "C"):
                    if prefix + "_PQ" in g and prefix + "_QB" in g:
                        for field in ("cycles", "target_final_kv", "draft_final_kv"):
                            need(g[prefix + "_PQ"][field] == g[prefix + "_QB"][field], "PQ/QB natural canonical state differs")
                if key[0] == "qualification" and key[-1] == "heavy":
                    for prefix in ("M", "C"):
                        pq, qb = g[prefix + "_PQ"], g[prefix + "_QB"]
                        for field in ("cycles", "target_final_kv", "draft_final_kv"):
                            need(pq[field] == qb[field], "PQ/QB full canonical state differs")
                        vec = lambda r: {v["name"]: (v["bytes"], v["sha256"]) for v in r["raw_vectors"]}
                        need(vec(pq) == vec(qb), "PQ/QB complete decision vectors differ")
                if all(a in g for a in ("C_GS", "C_PQ", "C_QB")):
                    work_equal &= g["C_GS"]["cycles"] == g["C_PQ"]["cycles"] == g["C_QB"]["cycles"]
            for item in (panel["families"][family][0], panel["families"][family][11]):
                on = grouped[("qualification", None, None, item["id"], "heavy")]
                off = grouped[("qualification", None, None, item["id"], "off")]
                need(all(on[a]["cycles"] == off[a]["cycles"] and on[a]["target_final_kv"] == off[a]["target_final_kv"] and on[a]["draft_final_kv"] == off[a]["draft_final_kv"] for a in ARMS), "observer sentinel changes state/trajectory")
            qual_end = max(utc(a["process_end_utc"]) for a in selected_receipts if a["family"] == family and a["unit_id"].startswith("qualification/"))
            first_formal = min(utc(a["process_start_utc"]) for a in selected_receipts if a["family"] == family and a["unit_id"].startswith("formal/"))
            need(qual_end < first_formal, "formal timing started before family qualification ended")
            state["logical_work_equal"] = work_equal
            state["interpretation"] = "matched observed logical work" if work_equal else "complete-request joint path effect; execution-cost-only attribution not supported"
            state["eligible"] = not state["errors"] and not result["failures"]
        except (KeyError, TypeError, ValueError) as exc:
            state["errors"].append(str(exc))
    result["selected_record_count"] = len(selected)
    result["calendar_dates"] = binding["calendar_dates"]
    result["selected_attempts"] = [a["attempt_id"] for a in selected_receipts]
    result["status"] = "CPU_AUDIT_COMPLETE" if any(s["eligible"] for s in result["families"].values()) else "INCOMPLETE_OR_UNQUALIFIED"
    result["qualified_performance"] = {f: s["eligible"] for f, s in result["families"].items()} if result["status"] == "CPU_AUDIT_COMPLETE" else None
    return result, selected


def finite_panel_estimates(rows, family, calendar_dates):
    """Arithmetic only; caller must gate eligibility. Never request-bootstrap."""
    cells = defaultdict(dict)
    for r in rows:
        if r["family"] == family and r["stage"] == "formal":
            key = (r["date_slot"], r["session_slot"], r["input_id"])
            need(r["arm"] not in cells[key], "duplicate contrast arm")
            cells[key][r["arm"]] = r["service_seconds"]
    need(len(cells) == 72 and all(set(c) == set(ARMS) for c in cells.values()), "complete 12x2x3 seven-arm panel required")
    effects = []
    for (d, s, task), v in sorted(cells.items()):
        need(all(math.isfinite(x) and x > 0 for x in v.values()), "positive finite service times required")
        z = {"D_" + l: math.log(v["M_" + l]) - math.log(v["C_" + l]) for l in SCOPES}
        z["I_QB_vs_GS"] = z["D_QB"] - z["D_GS"]
        z.update({"C_QB_over_C_PQ": math.log(v["C_QB"]) - math.log(v["C_PQ"]),
                  "M_QB_over_M_PQ": math.log(v["M_QB"]) - math.log(v["M_PQ"])})
        z.update({"R_over_C_" + l: math.log(v["R"]) - math.log(v["C_" + l]) for l in SCOPES})
        effects.append({"date_slot": d, "session_slot": s, "input_id": task, "log_effects": z})
    names = list(effects[0]["log_effects"])
    sessions, dates, summaries = [], [], []
    for d in range(3):
        for s in range(2):
            current = [e for e in effects if e["date_slot"] == d and e["session_slot"] == s]
            need(len(current) == 12 and len({x["input_id"] for x in current}) == 12, "session task set incomplete")
            sessions.append({"date_slot": d, "date": calendar_dates[d], "session_slot": s,
                             "log_effects": {n: math.fsum(e["log_effects"][n] for e in current) / 12 for n in names}})
        current = [e for e in sessions if e["date_slot"] == d]
        dates.append({"date_slot": d, "date": calendar_dates[d],
                      "log_effects": {n: math.fsum(e["log_effects"][n] for e in current) / 2 for n in names},
                      "within_date_session1_minus_session0": {n: current[1]["log_effects"][n] - current[0]["log_effects"][n] for n in names}})
    for name in names:
        values = [d["log_effects"][name] for d in dates]
        avg = math.fsum(values) / 3
        result = {"contrast": name, "mean_log_effect": avg, "ratio": math.exp(avg),
                  "date_log_effects": values, "date_ratios": list(map(math.exp, values)),
                  "all_three_dates_positive": all(v > 0 for v in values),
                  "all_three_dates_negative": all(v < 0 for v in values),
                  "date_log_range": [min(values), max(values)],
                  "adjacent_date_log_changes": [values[1] - values[0], values[2] - values[1]]}
        if name == "I_QB_vs_GS":
            # Student t, df=2 has an analytic CDF. Bonferroni two primary family
            # contrasts => 97.5% two-sided intervals, solely weak sensitivity.
            y = 2 * (1 - .025 / 2) - 1
            critical = math.sqrt(2) * y / math.sqrt(1 - y * y)
            width = critical * statistics.stdev(values) / math.sqrt(3)
            result["weak_date_sensitivity"] = {"degrees_of_freedom": 2, "confidence_level": .975,
                "critical_value": critical, "log_interval": [avg - width, avg + width],
                "ratio_interval": [math.exp(avg - width), math.exp(avg + width)],
                "interpretation": "Bonferroni for two primary family contrasts under independent approximately normal date means; three dates cannot provide robust population inference."}
        summaries.append(result)
    return {"family": family, "independent_dates": 3, "sessions": sessions, "dates": dates,
            "input_session_effects": effects, "summary": summaries,
            "scope": "fixed exposed 12-input panel on one host; no request bootstrap; no population power guarantee"}


def analyze(design, bundle):
    report, selected = audit(design, bundle)
    results = {"study_id": STUDY, "audit": report, "qualified_performance": None,
               "new_native_executions": 0, "results": {}}
    for family, state in report["families"].items():
        results["results"][family] = finite_panel_estimates(selected, family, report["calendar_dates"]) if state["eligible"] else None
    if any(v is not None for v in results["results"].values()):
        results["qualified_performance"] = results["results"]
    return results


def known_counterexample(path):
    need(hash_file(path) == COUNTEREXAMPLE_SHA, "counterexample source differs")
    entries = [r for r in read(path) if r.get("stage") == "E1" and r.get("family") == "Llama"]
    need({r["arm"] for r in entries} == {"PQ", "QB"} and len(entries) == 2, "known Llama arm set differs")
    first = entries[0]
    for r in entries:
        need(r["task_id"] == "CodeContests/valid/108" and r["prompt_tokens"] == 737, "counterexample input differs")
        a, b = r["reference_output"]["ids"], r["observed_output"]["ids"]
        diff = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        need(diff == r["first_different_output_index_zero_based"] == 81, "first endpoint divergence differs")
        need(a[81] == 16 and b[81] == 15, "failure tokens differ")
    need(entries[0]["observed_output"] == entries[1]["observed_output"], "saved PQ/QB endpoints differ")
    return {"status": "HISTORICAL_ENDPOINT_COUNTEREXAMPLE_RECONSTRUCTED", "new_native_executions": 0,
            "source_commit": PANEL_COMMIT, "source_sha256": COUNTEREXAMPLE_SHA,
            "family": "Llama", "input_id": first["task_id"], "prompt_tokens": 737,
            "first_endpoint_divergence_zero_based": 81, "R_token": 16, "PQ_QB_token": 15,
            "PQ_QB_saved_endpoints_equal": True, "raw_decision_vector_equality_revalidated": False,
            "operator_location": None,
            "missing_for_full_A0": ["observer.jsonl", "logits.f32", "complete response/cycle traces with source hashes"],
            "interpretation": "These saved endpoint summaries do not locate the earliest logit or operator divergence."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare", help="extract exact pinned IDs/models and deterministic slots; CPU only")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--model-contract", type=Path, required=True)
    p.add_argument("--design", type=Path, default=DESIGN)
    p = sub.add_parser("check-plan", help="reconstruct and verify existing CPU design")
    p.add_argument("--design", type=Path, default=DESIGN)
    for command in ("audit", "analyze"):
        p = sub.add_parser(command, help="read retained host records; never execute a worker")
        p.add_argument("--design", type=Path, default=DESIGN)
        p.add_argument("--bundle", type=Path, required=True)
        p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("inspect-known-counterexample", help="CPU endpoint reconstruction only; raw A0 vectors remain required")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(args.manifest, args.model_contract, args.design)
    elif args.command == "check-plan":
        result = check_plan(args.design)
    elif args.command == "inspect-known-counterexample":
        result = known_counterexample(args.source)
        save(args.out, result)
    else:
        result = analyze(args.design, args.bundle) if args.command == "analyze" else audit(args.design, args.bundle)[0]
        save(args.out, result)
    print(json.dumps({k: result[k] for k in ("status", "execution_status", "native_status", "study_id", "new_native_executions", "qualified_performance") if k in result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ContractError, KeyError, TypeError, ValueError, OSError) as exc:
        print("CPU_CONTRACT_FAILURE: " + str(exc), file=sys.stderr)
        sys.exit(2)
