#!/usr/bin/env python3
"""R1 correctness qualification for prospective 358H runtime paths.

All timings produced here are QUALIFICATION_ONLY and invalid for headline
performance claims. The only promotion signal is exact token equality against
the shared TARGET_UB1 reference.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil

from runtime_factory import create_draft_adapters, parse_path
from runtime_freeze import verify_freeze_manifest
from runtime_runner import run_speculative, run_target_only
from runtime_target import LlamaAPI, RuntimeTargetPool
from runtime_types import first_divergence

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATASET = ROOT / "datasets" / "humaneval" / "HumanEval.jsonl.gz"
DATASET_SHA256 = "b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef"
SMALL = [3, 10, 19, 20, 106, 129]
FULL = [3, 10, 19, 20, 28, 32, 44, 47, 48, 50, 54, 57, 62, 64, 68, 70, 89, 90, 101, 104, 105, 106, 107, 111, 119, 123, 126, 128, 129, 162]
WARMUP = 0
OUTPUT_CAP = 128

ALLOWED_PATHS = {
    "TARGET_UB2",
    "LEGACY_CPU_UB1",
    "LEGACY_NPU_UB1",
    "LEGACY_NPU_UB2",
    "OPTIMUM_REPLAY_CPU_UB1",
    "OPTIMUM_REPLAY_NPU_UB1",
    "PERSIST_CPU_UB1",
    "PERSIST_NPU_UB1",
    "PERSIST_NPU_UB2",
}


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


def assert_host_gate() -> None:
    battery = psutil.sensors_battery()
    if battery is None or battery.power_plugged is not True:
        raise RuntimeError("AC power must be positively online")
    if (os.environ.get("SESSIONNAME") or "").upper().startswith("RDP"):
        raise RuntimeError("RDP session is forbidden")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["small", "full"], required=True)
    ap.add_argument("--paths", nargs="+", required=True, help="R0-feasible candidate paths only")
    ap.add_argument("--freeze-manifest", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    bad = sorted(set(args.paths) - ALLOWED_PATHS)
    if bad:
        raise ValueError(f"unknown or out-of-scope v0.1 candidate paths: {bad}")
    if len(args.paths) != len(set(args.paths)):
        raise ValueError("duplicate path names")
    assert_host_gate()
    freeze = verify_freeze_manifest(args.freeze_manifest)

    tasks = load_tasks()
    task_ids = SMALL if args.stage == "small" else FULL
    expected_pairs = len(task_ids) * 3
    seed = 20260923 if args.stage == "small" else 20260924
    args.output_dir.mkdir(parents=True, exist_ok=False)

    api = LlamaAPI()
    targets = RuntimeTargetPool(api)
    specs = {"TARGET_UB1": parse_path("TARGET_UB1")}
    specs.update({name: parse_path(name) for name in args.paths})

    try:
        drafts, optimum_engines, legacy_engines = create_draft_adapters(specs)
    except Exception as exc:
        write_json(args.output_dir / "path_initialization.json", {
            "status": "FAIL",
            "error": repr(exc),
            "requested_paths": args.paths,
        })
        raise

    init_records = {}
    for name, spec in specs.items():
        init_records[name] = {
            "status": "PASS",
            "target_ubatch": spec["ubatch"],
            "draft_device": spec["device"],
            "draft_capabilities": None if spec["kind"] == "TARGET" else drafts[name].capabilities.__dict__,
        }
    init_records["_engine_topology"] = {
        "optimum_compiled_engines": sorted(optimum_engines),
        "legacy_genai_engines": sorted(legacy_engines),
        "rule": "at most one physical draft engine per frontend/device in this process",
    }
    write_json(args.output_dir / "path_initialization.json", init_records)

    conditions = list(specs)
    schedule = []
    for task_id in task_ids:
        for rep in range(3):
            order = list(conditions)
            random.Random(seed + task_id * 1009 + rep).shuffle(order)
            schedule.append({"task_id": task_id, "repetition": rep, "conditions": order})
    write_json(args.output_dir / "schedule.json", schedule)

    status = {
        "schema": "heterospec.358h.runtime.r1_status.v2",
        "formal": False,
        "claim_status": "QUALIFICATION_ONLY / TIMINGS INVALID_FOR_HEADLINE_CLAIMS",
        "stage": args.stage,
        "created_at_utc": utc(),
        "candidate_paths": args.paths,
        "expected_pairs_per_path": expected_pairs,
        "completed_observations": 0,
        "complete": False,
        "dataset_sha256": DATASET_SHA256,
        "output_cap": OUTPUT_CAP,
        "k": 2,
        "promotion_rule": "all pairs exact against TARGET_UB1; any mismatch blocks that complete path",
        "timing_used_for_promotion": False,
        "freeze_manifest": str(args.freeze_manifest),
        "freeze_manifest_sha256": sha256(args.freeze_manifest),
        "freeze_source_commit": freeze["source_commit"],
    }
    write_json(args.output_dir / "R1_STATUS.json", status)

    warm_prompt = prompt_for(tasks[WARMUP])
    warm_pt = targets[1].tokenize(formatted_prompt(warm_prompt), True)
    warm = []
    for name in conditions:
        spec = specs[name]
        tgt = targets[spec["ubatch"]]
        if spec["kind"] == "TARGET":
            result = run_target_only(tgt, warm_pt, 8)
        else:
            result = run_speculative(tgt, drafts[name], warm_pt, 8)
        warm.append({"path": name, "tokens": result["tokens"], "claim_status": "NON_FORMAL / INVALID_FOR_CLAIMS"})
    write_json(args.output_dir / "warmup.json", warm)

    rows = []
    raw_path = args.output_dir / "observations.jsonl"
    for unit in schedule:
        task_id = unit["task_id"]
        rep = unit["repetition"]
        prompt = prompt_for(tasks[task_id])
        pt = targets[1].tokenize(formatted_prompt(prompt), True)
        for name in unit["conditions"]:
            spec = specs[name]
            tgt = targets[spec["ubatch"]]
            started = utc()
            if spec["kind"] == "TARGET":
                r = run_target_only(tgt, pt, OUTPUT_CAP)
            else:
                r = run_speculative(tgt, drafts[name], pt, OUTPUT_CAP)
            row = {
                "schema": "heterospec.358h.runtime.r1_observation.v2",
                "formal": False,
                "claim_status": "QUALIFICATION_ONLY / TIMINGS INVALID_FOR_HEADLINE_CLAIMS",
                "stage": args.stage,
                "task_id": f"HumanEval/{task_id}",
                "repetition": rep,
                "path": name,
                "started_at_utc": started,
                "ended_at_utc": utc(),
                "prompt_token_count": len(pt),
                "generated_token_ids": r["tokens"],
                "output_token_count": len(r["tokens"]),
                "timing_diagnostic_only": r["timing"],
                "rounds": r["rounds"],
                "proposed": r["proposed"],
                "accepted": r["accepted"],
                "target_binding": tgt.binding_record(),
                "draft_capabilities": r.get("draft_capabilities"),
                "exact_vs_reference": None,
                "first_divergence": None,
            }
            rows.append(row)
            with raw_path.open("a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                f.flush()
                os.fsync(f.fileno())
            status["completed_observations"] += 1
            status["last_observation"] = {"task_id": task_id, "repetition": rep, "path": name}
            write_json(args.output_dir / "R1_STATUS.json", status)

    refs = {
        (r["task_id"], r["repetition"]): r["generated_token_ids"]
        for r in rows if r["path"] == "TARGET_UB1"
    }
    if len(refs) != expected_pairs:
        raise RuntimeError(f"expected {expected_pairs} TARGET_UB1 references, got {len(refs)}")

    exact_summary = {}
    for row in rows:
        ref = refs[(row["task_id"], row["repetition"])]
        row["exact_vs_reference"] = row["generated_token_ids"] == ref
        row["first_divergence"] = first_divergence(ref, row["generated_token_ids"])
    for name in conditions:
        subset = [r for r in rows if r["path"] == name]
        exact = sum(bool(r["exact_vs_reference"]) for r in subset)
        exact_summary[name] = {
            "exact_pairs": exact,
            "total_pairs": len(subset),
            "status": "QUALIFIED" if exact == len(subset) == expected_pairs else "BLOCKED",
            "performance_promotion_allowed": bool(name != "TARGET_UB1" and exact == len(subset) == expected_pairs),
        }

    write_json(args.output_dir / "observations.resolved.json", rows)
    write_json(args.output_dir / "qualification_summary.json", exact_summary)
    status["complete"] = True
    status["completed_at_utc"] = utc()
    status["qualification"] = exact_summary
    write_json(args.output_dir / "R1_STATUS.json", status)
    print(json.dumps(exact_summary, indent=2))
    return 0 if all(v["status"] == "QUALIFIED" for v in exact_summary.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
