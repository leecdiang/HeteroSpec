#!/usr/bin/env python3
"""Freeze an outcome-blind M4 calibration, qualification, and held-out plan."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "benchmarks/m4_runtime"
SEED = 20260924
ALGORITHM = (
    "For each family, SHA256('20260924|<family>|<task_id>'), sort ascending; "
    "first 8 qualification, next 20 calibration, next 30 held-out. "
    "All remaining eligible tasks remain unused."
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(name, data):
    (BASE / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main():
    inventory_path = BASE / "WORKLOAD_INVENTORY.json"
    inventory_bytes = inventory_path.read_bytes()
    inventory = json.loads(inventory_bytes)
    now = datetime.now(timezone.utc).isoformat()
    splits = {"QUALIFICATION": [], "CALIBRATION": [], "HELDOUT": []}
    for family in ("Spec-Bench", "HumanEval"):
        eligible = [
            row for row in inventory["candidates"]
            if row["workload_family"] == family and row["eligible_for_heldout"]
            and row["eligible_for_calibration"]
        ]
        eligible.sort(key=lambda row: digest(f"{SEED}|{family}|{row['task_id']}".encode()))
        if len(eligible) < 58:
            raise SystemExit(f"DESIGN_BLOCKED: {family} has fewer than 58 eligible tasks")
        for key, part in (
            ("QUALIFICATION", eligible[:8]),
            ("CALIBRATION", eligible[8:28]),
            ("HELDOUT", eligible[28:58]),
        ):
            splits[key].extend({
                "workload_family": row["workload_family"],
                "stratum": row["stratum"],
                "task_id": row["task_id"],
                "prompt_hash": row["prompt_hash"],
            } for row in part)
    ids = [f"{x['workload_family']}|{x['task_id']}" for rows in splits.values() for x in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit("Split overlap")
    for key, rows in splits.items():
        write(f"{key}_SPLIT.json", {
            "schema": f"heterospec.m4_runtime.{key.lower()}_split.v0.1",
            "created_utc": now,
            "source_commit": inventory["source_commit"],
            "inventory_sha256": digest(inventory_bytes),
            "dataset_sha256": inventory["datasets"],
            "seed": SEED,
            "algorithm": ALGORITHM,
            "formal_heldout_data_seen": False,
            "tasks": rows,
        })
    print({key: len(rows) for key, rows in splits.items()})


if __name__ == "__main__":
    main()
