"""Independent Windows-only budget accounting. No CUDA loading or GPU execution.

Admission never infers liveness from a historic PR or an empty process list.
All critical checks use explicit exceptions, also under python -O.
"""
from __future__ import annotations

import hashlib
import datetime
import json
import math
import sqlite3
from pathlib import Path


class ResourceRefusal(RuntimeError):
    pass


KEYS = ("model_requests", "target_draft_rows", "native_gpu_seconds", "kernel_launches", "capture_bytes")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ResourceRefusal(message)


def admit_live(plan, receipt, legacy_bindings):
    """Caller must provide a fresh original-thread and actual device receipt."""
    require(plan.get("profile") == "windows-native-single-rtx5070ti", "Wrong platform profile")
    require(plan.get("gpu_admission") == "READY", "Frozen plan blocks GPU admission")
    require(receipt.get("original_thread_status") == "VERIFIED_IDLE_OR_COMPLETED", "Original thread unverified or active")
    require(bool(receipt.get("original_thread_id")) and bool(receipt.get("thread_evidence")), "Missing original-thread evidence")
    observed = receipt.get("observed_utc")
    require(isinstance(observed, str), "Missing admission observation timestamp")
    try:
        stamp = datetime.datetime.fromisoformat(observed)
    except ValueError as exc:
        raise ResourceRefusal("Invalid observation timestamp") from exc
    require(stamp.tzinfo is not None, "Observation timestamp needs timezone")
    age = (datetime.datetime.now(datetime.timezone.utc) - stamp).total_seconds()
    require(0 <= age <= 60, "Admission observation expired or future-dated")
    require(receipt.get("device_uuid") == plan["device"]["uuid"], "Wrong actual GPU UUID")
    require(receipt.get("visible_device_uuids") == [plan["device"]["uuid"]], "Not a bound single-device map")
    require(receipt.get("physical_index") == plan["device"]["physical_index"], "Wrong physical device")
    require(receipt.get("foreign_compute_pids") == [], "Other compute tasks or unknown process inventory")
    require(receipt.get("legacy_lock_present") is False, "Legacy lock occupied or unknown")
    require(receipt.get("source_build_model_modules_verified") is True, "Source/build/model/modules not verified")
    purpose = receipt.get("purpose")
    require(purpose in ("qualification", "performance"), "Unknown native admission purpose")
    if purpose == "performance":
        require(receipt.get("native_qualification_passed") is True, "Native qualification missing")
    else:
        require(receipt.get("qualification_plan_frozen") is True and receipt.get("independent_reference_available") is True, "Qualification prerequisites missing")
    for binding in legacy_bindings:
        require(sha256(binding["path"]) == binding["sha256"], "Legacy artifact changed: " + binding["path"])
    return {"status": "ADMITTED", "device_uuid": receipt["device_uuid"]}


class Ledger:
    """Reserve resources before work. Failed/reserved work remains charged."""
    def __init__(self, path, plan):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.plan = plan
        self.plan_hash = hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.db = sqlite3.connect(self.path)
        self.db.execute("CREATE TABLE IF NOT EXISTS epoch (epoch TEXT PRIMARY KEY, plan_sha256 TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY, stage TEXT NOT NULL, status TEXT NOT NULL, reserved TEXT NOT NULL, actual TEXT, outcome TEXT)")
        rows = self.db.execute("SELECT epoch,plan_sha256 FROM epoch").fetchall()
        if rows:
            if rows != [(plan["epoch"], self.plan_hash)]:
                self.db.close()
                raise ResourceRefusal("Ledger belongs to another epoch or plan")
        else:
            self.db.execute("INSERT INTO epoch VALUES (?,?)", (plan["epoch"], self.plan_hash))
            self.db.commit()

    def totals(self):
        total = {k: 0 for k in KEYS}
        for raw, observed in self.db.execute("SELECT reserved,actual FROM attempts"):
            reserved, actual = json.loads(raw), json.loads(observed) if observed else {}
            for k, v in reserved.items():
                total[k] += max(v, actual.get(k, 0))
        return total

    def reserve(self, attempt_id, stage, amounts, admission):
        require(self.plan.get("gpu_admission") == "READY", "Frozen plan blocks GPU admission")
        require(admission.get("status") == "ADMITTED", "GPU admission blocked")
        require(admission.get("device_uuid") == self.plan["device"]["uuid"], "Admission device mismatch")
        require(set(amounts) == set(KEYS), "Resource reservation must be complete")
        for k, v in amounts.items():
            require(type(v) in (int, float) and math.isfinite(v) and v >= 0, "Invalid amount: " + k)
            if k != "native_gpu_seconds":
                require(type(v) is int, "Noninteger resource: " + k)
        require(stage in self.plan["request_allocations"], "Unknown stage")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            require(self.db.execute("SELECT COUNT(*) FROM attempts WHERE status='OVERRUN'").fetchone()[0] == 0, "Epoch stopped after resource overrun")
            require(self.db.execute("SELECT COUNT(*) FROM attempts WHERE id=?", (attempt_id,)).fetchone()[0] == 0, "Duplicate attempt; no retry")
            total = self.totals()
            for k in KEYS:
                require(total[k] + amounts[k] <= self.plan["maximums"][k], "Epoch cap exceeded: " + k)
            stage_totals = {"model_requests": 0, "target_draft_rows": 0}
            for (raw,) in self.db.execute("SELECT reserved FROM attempts WHERE stage=?", (stage,)):
                for k in stage_totals:
                    stage_totals[k] += json.loads(raw)[k]
            for k in stage_totals:
                require(stage_totals[k] + amounts[k] <= self.plan["request_allocations"][stage][k], "Stage cap exceeded: " + k)
            self.db.execute("INSERT INTO attempts VALUES (?,?,?, ?,NULL,NULL)", (attempt_id, stage, "RESERVED", json.dumps(amounts, sort_keys=True)))

    def finish(self, attempt_id, actual, outcome):
        require(outcome in ("COMPLETE", "FAILED", "TIMEOUT"), "Invalid terminal outcome")
        require(set(actual) == set(KEYS), "Actual accounting must be complete")
        row = self.db.execute("SELECT reserved,status FROM attempts WHERE id=?", (attempt_id,)).fetchone()
        require(row is not None and row[1] == "RESERVED", "Unknown or already finalized attempt")
        reserved = json.loads(row[0])
        for k in KEYS:
            require(type(actual[k]) in (int, float) and math.isfinite(actual[k]) and actual[k] >= 0, "Actual usage invalid: " + k)
            if k != "native_gpu_seconds":
                require(type(actual[k]) is int, "Noninteger actual resource: " + k)
        overrun = any(actual[k] > reserved[k] for k in KEYS)
        status = "OVERRUN" if overrun else outcome
        with self.db:
            self.db.execute("UPDATE attempts SET status=?,actual=?,outcome=? WHERE id=?", (status, json.dumps(actual, sort_keys=True), outcome, attempt_id))
        require(not overrun, "Actual usage exceeds reservation; overrun persisted and charged")

    def snapshot(self):
        attempts = [dict(zip(("id", "stage", "status", "reserved", "actual", "outcome"), row)) for row in self.db.execute("SELECT * FROM attempts ORDER BY id")]
        return {"epoch": self.plan["epoch"], "plan_sha256": self.plan_hash, "reserved": self.totals(), "attempts": attempts, "refunds": 0, "automatic_retry": False}

    def close(self):
        self.db.close()
