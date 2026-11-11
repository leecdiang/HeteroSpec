"""Bounded, one-unit native execution after a committed host freeze.

No automatic retries or date changes. Native output is retained before the host
acknowledges each next request. The public study auditor remains the final gate.
"""
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import queue
import shutil
import socket
import subprocess
import threading
import time

import study as s
from qualify import qualification


def now():
    return datetime.now(timezone.utc)


def atomic(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    s.save(temp, data)
    temp.replace(path)


def pin(root, path, **fields):
    return {"path": path.resolve().relative_to(root.resolve()).as_posix(), "bytes": path.stat().st_size,
            "sha256": s.hash_file(path), **fields}


def current_gpu():
    text = subprocess.check_output(["nvidia-smi", "--query-gpu=uuid,driver_version,memory.used", "--format=csv,noheader,nounits"], text=True, timeout=30)
    rows = list(csv.reader(text.strip().splitlines()))
    s.need(len(rows) == 1, "ambiguous GPU")
    return tuple(v.strip() for v in rows[0])


def calendar_gate(slots, binding, attempts, instant):
    """Admission before process creation; all arguments permit CPU fixtures."""
    first = slots[0]
    day, session = first["date_slot"], first["session_slot"]
    if day is None:
        return
    dates = binding["calendar_dates"]
    s.need(s.local_date(instant.isoformat()) == dates[day], "not the frozen Shanghai date")
    midnight = datetime.fromisoformat(dates[day]).replace(tzinfo=s.LOCAL_TZ) + timedelta(days=1)
    s.need((midnight - instant).total_seconds() > binding["resource_caps"]["worker_timeout_seconds"], "insufficient local-date headroom for owned worker limit")
    formal = [a for a in attempts if a["unit_id"].startswith("formal/")]
    if day > 0 and session == 0:
        previous = [a for a in formal if a["date_slot"] == day - 1]
        own = [a for a in previous if a["family"] == first["family"]]
        s.need(previous and own, "previous date missing")
        s.need((instant - min(s.utc(a["process_start_utc"]) for a in own)).total_seconds() >= 20 * 3600, "family first-session gap below 20 hours")
        s.need((instant - min(s.utc(a["process_start_utc"]) for a in previous)).total_seconds() >= 20 * 3600, "daily first-session gap below 20 hours")


def validate_freeze(bundle):
    binding = s.read(bundle / "EXECUTION_IDENTITY.json")
    plan = s.read(s.DESIGN / "PLAN.json")
    models = s.read(s.DESIGN / "MODEL_PINS.json")
    s.need(not s.identity_errors(binding, plan, s.DESIGN, models), "invalid execution identity")
    dates = binding["calendar_dates"]
    s.need(len(dates) == 3 and dates == sorted(set(dates)) and all(datetime.fromisoformat(d).date().isoformat() == d for d in dates), "three distinct increasing dates required")
    provenance = s.read(bundle / "FREEZE_COMMIT.json")
    committed = subprocess.check_output(["git", "show", provenance["commit"] + ":" + provenance["identity_path"]], cwd=s.REPO)
    s.need(committed == (bundle / "EXECUTION_IDENTITY.json").read_bytes(), "execution identity must match committed freeze bytes")
    committed_refs = subprocess.check_output(["git", "show", provenance["commit"] + ":" + provenance["references_path"]], cwd=s.REPO)
    s.need(committed_refs == (bundle / "REFERENCES.json").read_bytes(), "historical reference binding changed after freeze")
    required_sources = {p.relative_to(s.REPO).as_posix() for p in Path(__file__).parent.iterdir()
                        if p.suffix in (".py", ".h", ".cpp")}
    required_sources |= {(s.DESIGN / name).relative_to(s.REPO).as_posix() for name in
                         ("PLAN.json", "PANEL.json", "MODEL_PINS.json", "SLOTS.jsonl", "DIAGNOSTIC_SLOTS.jsonl")}
    s.need(required_sources <= set(provenance["source_files"]), "incomplete source freeze")
    # Bind runner and scientific design to the same reviewed source snapshot.
    for path, digest in provenance["source_files"].items():
        s.need(s.hash_file(s.REPO / path) == digest, "source changed after freeze: " + path)
        content = subprocess.check_output(["git", "show", provenance["commit"] + ":" + path], cwd=s.REPO)
        s.need(s.digest(content) == digest, "source not present in freeze commit: " + path)
    return binding


def normalize(bundle, native_path, slot, receipt):
    raw = s.read(native_path)
    s.need(raw["slot"] == slot, "worker slot differs")
    row = {**slot, **{k: raw[k] for k in ("identity", "endpoint", "cycles", "target_final_kv", "draft_final_kv",
           "draft_calls", "service_seconds", "service_timer_definition", "observed_scope", "context", "physical_widths",
           "geometry", "prompt_tokens", "prompt_ids_sha256", "context_scope_fixed", "request_start_utc", "request_end_utc")},
           "is_synthetic": False, "started": True, "status": "COMPLETE", "attempt_id": receipt["attempt_id"],
           "pid": receipt["pid"], "process_start_utc": receipt["process_start_utc"],
           "date_timezone": "Asia/Shanghai", "actual_date": s.local_date(raw["request_start_utc"]),
           "raw_native_record": pin(bundle, native_path), "raw_vectors": []}
    folder = native_path.with_suffix("")
    if slot["observer"] == "heavy":
        row["raw_vectors"] = [pin(bundle, p, name=p.relative_to(folder).as_posix(), dtype="float32")
                              for p in sorted(folder.rglob("*.f32"))]
    return row


def run_unit(bundle, unit):
    bundle = bundle.resolve()
    lock = bundle / "HOST.lock"
    # A stale lock is evidence to reconcile, never implicit retry permission.
    with lock.open("x", encoding="utf-8") as f:
        json.dump({"pid": os.getpid(), "utc": now().isoformat(), "unit": unit}, f)
    try:
        return _run_unit(bundle, unit)
    finally:
        lock.unlink()


def _run_unit(bundle, unit):
    s.check_plan(s.DESIGN)
    binding = validate_freeze(bundle)
    local = s.read(bundle / "LOCAL_PATHS.json")
    attempts = s.read(bundle / "ATTEMPTS.json")
    all_rows = s.lines(bundle / "REQUESTS.jsonl")
    all_slots = s.lines(s.DESIGN / "SLOTS.jsonl")
    slots = [r for r in all_slots if r["unit_id"] == unit]
    s.need(slots, "unplanned unit")
    family = slots[0]["family"]
    s.need(not any(a["unit_id"] == unit for a in attempts), "unit already attempted; no automatic retry")
    s.need(all(a["cleanup_verified"] is True for a in attempts), "unreconciled owned worker")
    if unit.startswith("formal/"):
        qualification(s.DESIGN, bundle, family)
        ordered = list(dict.fromkeys(r["unit_id"] for r in all_slots if r["stage"] in ("warmup", "formal")))
        completed = {a["unit_id"] for a in attempts if a["status"] == "COMPLETE"}
        s.need(all(u in completed for u in ordered[:ordered.index(unit)]), "earlier formal unit incomplete")
    calendar_gate(slots, binding, attempts, now())
    caps = binding["resource_caps"]
    spent = sum((s.utc(a["process_end_utc"]) - s.utc(a["process_start_utc"])).total_seconds() for a in attempts)
    s.need(spent + caps["worker_timeout_seconds"] <= caps["total_owned_seconds"], "owned-time budget cannot admit whole unit")
    s.need(sum(r["started"] for r in all_rows) + len(slots) <= 1288, "primary request budget exhausted")
    identity = binding["families"][family]
    gpu_id, driver, used = current_gpu()
    s.need(gpu_id == identity["device_id"] and driver == identity["driver"] and socket.gethostname() == identity["host_id"], "host/device/driver changed")
    s.need(int(used) < 1024 and shutil.disk_usage(bundle).free >= caps["minimum_free_bytes"], "host resource admission failed")
    executable = Path(local[family]["executable"])
    s.need(s.hash_file(executable) == identity["executable_sha256"], "executable differs")
    build = executable.parent.parent
    s.need(s.hash_file(build / "BUILD.json") == identity["build_receipt_sha256"], "build receipt differs")
    s.need(s.hash_file(build / "core/src/libllama.a") == identity["core_sha256"], "core differs")
    s.need({p.name for p in executable.parent.glob("*.dll")} == set(identity["numerical_modules"]), "runtime DLL inventory changed")
    models = s.read(s.DESIGN / "MODEL_PINS.json")["families"][family]
    items = s.read(s.DESIGN / "PANEL.json")["families"][family]
    references = s.read(bundle / "REFERENCES.json")["endpoints"]
    for slot in slots:
        ref = references[slot["reference_id"]]
        s.payload(bundle, ref["raw_payload"])
        s.endpoint(ref["endpoint"], models)
    attempt_id = unit.replace("/", "-") + "-a0"
    root = bundle / "attempts" / attempt_id
    root.mkdir(parents=True, exist_ok=False)
    s.save(root / "SLOTS.json", slots)
    s.save(root / "PANEL.json", {"inputs": items})
    command = [str(executable), str(root / "native"), local[family]["target"], local[family]["draft"],
               str(root / "PANEL.json"), str(root / "SLOTS.json"), family,
               str(bundle / "EXECUTION_IDENTITY.json"), str(s.DESIGN / "PLAN.json")]
    receipt = {"attempt_id": attempt_id, "attempt_index": 0, "unit_id": unit, "family": family,
               "date_slot": slots[0]["date_slot"], "session_slot": slots[0]["session_slot"],
               "status": "STARTED", "cleanup_verified": False, "process_start_utc": now().isoformat(), "argv": command}
    atomic(root / "PROCESS.json", receipt)
    environment = {k: v for k, v in os.environ.items() if not k.startswith(("HS_", "LLAMA_ARG_", "GGML_", "CUDA_"))}
    events, rows, failure = queue.Queue(), [], None
    process = None
    start = time.monotonic()
    payload_bytes = sum(p.stat().st_size for p in bundle.rglob("*") if p.is_file())
    try:
        with (root / "stdout.log").open("x", encoding="utf-8") as log, (root / "stderr.log").open("xb") as err:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err,
                                       text=True, encoding="utf-8", env=environment,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            receipt["pid"] = process.pid
            atomic(root / "PROCESS.json", receipt)

            def consume():
                for line in process.stdout:
                    log.write(line); log.flush()
                    try:
                        events.put(s.strict_json(line))
                    except ValueError:
                        events.put({"event": "BAD_STDOUT"})
                events.put({"event": "EOF"})

            reader = threading.Thread(target=consume, daemon=True)
            reader.start()
            while True:
                s.need(time.monotonic() - start < caps["worker_timeout_seconds"], "worker time limit")
                s.need(shutil.disk_usage(bundle).free >= caps["minimum_free_bytes"], "disk headroom exhausted")
                s.need(payload_bytes <= caps["payload_bytes"], "payload budget exhausted")
                try:
                    event = events.get(timeout=1)
                except queue.Empty:
                    continue
                if event["event"] == "EOF":
                    break
                if event["event"] == "POOLS_READY":
                    native = s.read(root / "native/PROVISIONED.json")
                    s.need(native["requests"] == [] and native["pid"] == process.pid, "provision receipt differs")
                    s.need(native["memory_after_provisioning"]["free_bytes"] >= 256 * 1024**2, "resident pool headroom insufficient")
                    process.stdin.write("RUN\n"); process.stdin.flush()
                    continue
                s.need(event["event"] == "REQUEST_COMPLETED" and len(rows) < len(slots), "unexpected worker event")
                slot = slots[len(rows)]
                s.need(event["slot_id"] == slot["slot_id"], "worker order differs")
                native_path = root / "native" / (slot["slot_id"] + ".json")
                row = normalize(bundle, native_path, slot, receipt)
                rows.append(row)
                payload_bytes += row["raw_native_record"]["bytes"] + sum(v["bytes"] for v in row["raw_vectors"])
                try:
                    s.need(row["identity"] == identity, "native identity differs")
                    s.need(s.endpoint(row["endpoint"], models) == references[slot["reference_id"]]["endpoint"], "historical R endpoint mismatch")
                    s.validate_cycles(row, items[slot["source_index"]], models)
                    if slot["date_slot"] is not None:
                        s.need(row["actual_date"] == binding["calendar_dates"][slot["date_slot"]] == s.local_date(row["request_end_utc"]), "request crossed frozen date")
                except ValueError as exc:
                    row["status"] = "NUMERICAL_FAILURE"
                    row["reason"] = str(exc)
                    failure = "NUMERICAL_FAILURE"
                    raise
                s.save_lines(root / "REQUESTS.jsonl", rows)
                process.stdin.write("CONTINUE\n"); process.stdin.flush()
            code = process.wait(timeout=30)
            reader.join(timeout=5)
            native = s.read(root / "native/result.json")
            if "nonfinite logit" in native.get("error", ""):
                failure = "NUMERICAL_FAILURE"
            receipt["exit_code"] = code
            s.need(code == 0 and native["normal_cleanup_returned"] is True and len(rows) == len(slots), "native unit did not complete")
            receipt["status"] = "COMPLETE"
    except BaseException as exc:
        receipt["status"] = failure or "TECHNICAL_FAILURE"
        receipt["error"] = str(exc)
    finally:
        if process is not None and process.poll() is None:
            if process.stdin:
                try:
                    process.stdin.close()
                except OSError:
                    pass
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=30)
        receipt.update(process_end_utc=now().isoformat(), cleanup_verified=process is None or process.poll() is not None)
        active_file = root / "native/ACTIVE_SLOT.json"
        result_file = root / "native/result.json"
        if result_file.exists() and "nonfinite logit" in s.read(result_file).get("error", ""):
            receipt["status"] = "NUMERICAL_FAILURE"
        active = s.read(active_file)["slot_id"] if active_file.exists() else None
        # Preserve interrupted active work separately from requests never started.
        for slot in slots[len(rows):]:
            started = slot["slot_id"] == active
            rows.append({**slot, "is_synthetic": False, "attempt_id": attempt_id, "started": started,
                         "status": receipt["status"] if started else "NOT_RUN_DEPENDENCY",
                         "reason": receipt.get("error", "unit did not complete"), "failure_id": attempt_id})
        s.save_lines(root / "REQUESTS.jsonl", rows)
        atomic(root / "PROCESS.json", receipt)
        attempts.append(receipt)
        atomic(bundle / "ATTEMPTS.json", attempts)
        s.save_lines(bundle / "REQUESTS.jsonl", all_rows + rows)
    if receipt["status"] == "COMPLETE" and unit.startswith("qualification/"):
        try:
            result = qualification(s.DESIGN, bundle, family)
        except (ValueError, OSError, KeyError) as exc:
            result = {"status": "NOT_QUALIFIED", "family": family, "reason": str(exc), "qualified_performance": None}
        atomic(bundle / (family + "-QUALIFICATION.json"), result)
    print(json.dumps({k: receipt[k] for k in ("attempt_id", "status", "cleanup_verified")}, ensure_ascii=False))
    return 0 if receipt["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--unit", required=True)
    args = parser.parse_args()
    raise SystemExit(run_unit(args.bundle, args.unit))
