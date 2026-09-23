#!/usr/bin/env python3
"""Formal R2 paired runtime campaign for 358H.

Conditions come only from a frozen qualification registry.  The driver never
selects paths from observed performance.  Model load/compile and non-formal
warm-up occur before formal_data_started; the primary per-request timing starts
after target prompt prefill and includes every runtime-specific draft cost.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import openvino as ov
import psutil

from runtime_draft import LegacyGenAIReplayDraft, OptimumDraftEngine
from runtime_runner import run_speculative, run_target_only
from runtime_shared_draft import SharedOptimumPersistentDraft, SharedOptimumReplayDraft
from runtime_target import LlamaAPI, RuntimeTargetPool
from runtime_types import first_divergence

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATASET = ROOT / "datasets" / "humaneval" / "HumanEval.jsonl.gz"
DATASET_SHA256 = "b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef"
FULL = [3, 10, 19, 20, 28, 32, 44, 47, 48, 50, 54, 57, 62, 64, 68, 70, 89, 90, 101, 104, 105, 106, 107, 111, 119, 123, 126, 128, 129, 162]
WARMUP = 0
OUTPUT_CAP = 128
SEED = 20260925
CPU_AFFINITY = list(range(12))
ALL_AFFINITY = list(range(os.cpu_count() or 16))


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def load_tasks() -> dict[int, dict]:
    if sha256(DATASET) != DATASET_SHA256:
        raise RuntimeError("HumanEval dataset hash mismatch")
    out = {}
    with gzip.open(DATASET, "rt", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            out[int(row["task_id"].split("/")[-1])] = row
    return out


def prompt_for(row: dict) -> str:
    return (
        "Complete the following Python function. Return only the completed Python code, "
        "without Markdown fences.\n\n" + row["prompt"]
    )


def formatted_prompt(prompt: str) -> str:
    return (
        f"<|im_start|>user\n{prompt}<|im_end|>\n"
        f"<|im_start|>assistant\n<think>\n\n</think>\n\n"
    )


def parse_path(name: str) -> dict[str, Any]:
    if name == "TARGET_UB1":
        return {"name": name, "kind": "TARGET", "device": None, "ubatch": 1}
    ubatch = 2 if name.endswith("_UB2") else 1
    device = "NPU" if "_NPU_" in name else "CPU"
    if name.startswith("LEGACY_"):
        kind = "LEGACY"
    elif name.startswith("OPTIMUM_REPLAY_"):
        kind = "OPTIMUM_REPLAY"
    elif name.startswith("PERSIST_"):
        kind = "PERSIST"
    else:
        raise ValueError(f"unsupported frozen path {name}")
    return {"name": name, "kind": kind, "device": device, "ubatch": ubatch}


def set_affinity(path_name: str) -> list[int]:
    chosen = CPU_AFFINITY if "_CPU_" in path_name else ALL_AFFINITY
    try:
        os.sched_setaffinity(0, chosen)
    except AttributeError:
        psutil.Process().cpu_affinity(chosen)
    return chosen


def assert_host_gate() -> None:
    battery = psutil.sensors_battery()
    if battery is None or battery.power_plugged is not True:
        raise RuntimeError("AC power must be positively online")
    if (os.environ.get("SESSIONNAME") or "").upper().startswith("RDP"):
        raise RuntimeError("RDP session is forbidden")


def create_adapters(specs: dict[str, dict[str, Any]]):
    """Create minimum resident draft engines needed by the frozen condition set."""
    adapters: dict[str, Any] = {}

    # One legacy LLMPipeline per device can serve both target UB1/UB2 because
    # draft semantics are independent of the target physical microbatch.
    legacy_by_device = {}
    for device in ("CPU", "NPU"):
        names = [n for n, s in specs.items() if s["kind"] == "LEGACY" and s["device"] == device]
        if names:
            legacy = LegacyGenAIReplayDraft(device, 1)
            legacy_by_device[device] = legacy
            for name in names:
                adapters[name] = legacy

    # Replay and persistent policies share the same compiled Optimum engine per
    # device. They are never used concurrently; each observation finishes/resets
    # before another policy touches the engine.
    engines = {}
    for device in ("CPU", "NPU"):
        names = [
            n for n, s in specs.items()
            if s["device"] == device and s["kind"] in ("OPTIMUM_REPLAY", "PERSIST")
        ]
        if not names:
            continue
        engine = OptimumDraftEngine(device)
        engines[device] = engine
        for name in names:
            spec = specs[name]
            if spec["kind"] == "OPTIMUM_REPLAY":
                adapters[name] = SharedOptimumReplayDraft(engine, spec["ubatch"])
            else:
                adapters[name] = SharedOptimumPersistentDraft(engine, spec["ubatch"])
    return adapters, engines, legacy_by_device


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    assert_host_gate()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    if registry.get("status") != "FROZEN_FOR_R2":
        raise RuntimeError("qualification registry is not frozen for R2")
    if registry.get("selection_uses_performance_timing") is not False:
        raise RuntimeError("registry does not prove timing-independent path selection")
    conditions = list(registry.get("formal_conditions", []))
    if not conditions or conditions[0] != "TARGET_UB1" or len(conditions) != len(set(conditions)):
        raise RuntimeError(f"invalid formal condition set: {conditions}")

    specs = {name: parse_path(name) for name in conditions}
    tasks = load_tasks()
    args.output_dir.mkdir(parents=True, exist_ok=False)

    # All heavy initialization happens before formal_data_started.
    api = LlamaAPI()
    targets = RuntimeTargetPool(api)
    adapters, engines, legacy = create_adapters(specs)

    init = {
        "schema": "heterospec.358h.runtime.r2_session.v0",
        "registry": str(args.registry),
        "registry_sha256": sha256(args.registry),
        "conditions": conditions,
        "python": sys.version,
        "platform": platform.platform(),
        "openvino": ov.get_version(),
        "target_bindings": {"UB1": targets[1].binding_record(), "UB2": targets[2].binding_record()},
        "draft_paths": {
            name: None if specs[name]["kind"] == "TARGET" else adapters[name].capabilities.__dict__
            for name in conditions
        },
        "accounting_boundary": "post target-prompt-prefill; runtime-specific draft begin/checkpoint/propose/reconcile/finish all included",
        "energy": "NOT_CLAIMED",
    }
    write_json(args.output_dir / "session.json", init)

    schedule = []
    for task_id in FULL:
        for rep in range(3):
            order = list(conditions)
            random.Random(SEED + task_id * 1009 + rep).shuffle(order)
            schedule.append({"task_id": task_id, "repetition": rep, "conditions": order})
    write_json(args.output_dir / "schedule.json", schedule)

    # Mandatory non-formal warm-up on HumanEval/0 only.
    warm_prompt = prompt_for(tasks[WARMUP])
    warm_pt = targets[1].tokenize(formatted_prompt(warm_prompt), True)
    warm = []
    for name in conditions:
        spec = specs[name]
        set_affinity(name)
        if spec["kind"] == "TARGET":
            r = run_target_only(targets[1], warm_pt, 8)
        else:
            r = run_speculative(targets[spec["ubatch"]], adapters[name], warm_pt, 8)
        warm.append({"path": name, "tokens": r["tokens"], "claim_status": "NON_FORMAL / INVALID_FOR_CLAIMS"})
    write_json(args.output_dir / "warmup.json", warm)

    status = {
        "schema": "heterospec.358h.runtime.r2_status.v0",
        "formal": True,
        "formal_data_started": True,
        "formal_data_started_at_utc": utc(),
        "registry_sha256": sha256(args.registry),
        "dataset_sha256": DATASET_SHA256,
        "conditions": conditions,
        "expected_observations": len(FULL) * 3 * len(conditions),
        "completed_observations": 0,
        "complete": False,
    }
    write_json(args.output_dir / "R2_STATUS.json", status)

    rows = []
    raw_path = args.output_dir / "observations.jsonl"
    for unit in schedule:
        task_id = unit["task_id"]
        rep = unit["repetition"]
        prompt = prompt_for(tasks[task_id])
        pt = targets[1].tokenize(formatted_prompt(prompt), True)
        for name in unit["conditions"]:
            spec = specs[name]
            affinity = set_affinity(name)
            started = utc()
            if spec["kind"] == "TARGET":
                r = run_target_only(targets[1], pt, OUTPUT_CAP)
            else:
                r = run_speculative(targets[spec["ubatch"]], adapters[name], pt, OUTPUT_CAP)
            row = {
                "schema": "heterospec.358h.runtime.r2_observation.v0",
                "formal": True,
                "task_id": f"HumanEval/{task_id}",
                "repetition": rep,
                "path": name,
                "started_at_utc": started,
                "ended_at_utc": utc(),
                "prompt_token_count": len(pt),
                "generated_token_ids": r["tokens"],
                "output_token_count": len(r["tokens"]),
                "timing": r["timing"],
                "rounds": r["rounds"],
                "proposed": r["proposed"],
                "accepted": r["accepted"],
                "committed": r["committed"],
                "process_affinity": affinity,
                "target_binding": targets[spec["ubatch"]].binding_record(),
                "draft_capabilities": r.get("draft_capabilities"),
                "exact_vs_reference": None,
                "first_divergence": None,
                "errors": [],
                "warnings": [],
            }
            rows.append(row)
            with raw_path.open("a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                f.flush()
                os.fsync(f.fileno())
            status["completed_observations"] += 1
            status["last_observation"] = {"task_id": task_id, "repetition": rep, "path": name}
            write_json(args.output_dir / "R2_STATUS.json", status)

    refs = {
        (r["task_id"], r["repetition"]): r["generated_token_ids"]
        for r in rows if r["path"] == "TARGET_UB1"
    }
    if len(refs) != 90:
        raise RuntimeError(f"expected 90 target references, got {len(refs)}")

    exact_counts = {}
    for row in rows:
        ref = refs[(row["task_id"], row["repetition"])]
        row["exact_vs_reference"] = row["generated_token_ids"] == ref
        row["first_divergence"] = first_divergence(ref, row["generated_token_ids"])
    for name in conditions:
        subset = [r for r in rows if r["path"] == name]
        exact = sum(bool(r["exact_vs_reference"]) for r in subset)
        exact_counts[name] = {
            "exact": exact,
            "total": len(subset),
            "performance_admissible": exact == len(subset) == 90,
        }

    write_json(args.output_dir / "observations.resolved.json", rows)
    status["complete"] = True
    status["completed_at_utc"] = utc()
    status["exact_counts"] = exact_counts
    write_json(args.output_dir / "R2_STATUS.json", status)
    print(json.dumps(exact_counts, indent=2))
    return 0 if all(x["performance_admissible"] for x in exact_counts.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
