#!/usr/bin/env python3
"""R1 token-exact qualification through the v0.2 process-isolated session."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path

import psutil

from runtime_factory import parse_path
from runtime_freeze import verify_freeze_manifest
from runtime_process_v02 import apply_affinity, assert_no_duplicate_omp
from runtime_session_v02 import RuntimeProcessSession, draft_groups, prepare_legacy_npu_cache
from runtime_types import first_divergence

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATASET = ROOT / "datasets/humaneval/HumanEval.jsonl.gz"
DATASET_SHA256 = "b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef"
SMALL = [3, 10, 19, 20, 106, 129]
FULL = [3, 10, 19, 20, 28, 32, 44, 47, 48, 50, 54, 57, 62, 64, 68, 70,
        89, 90, 101, 104, 105, 106, 107, 111, 119, 123, 126, 128, 129, 162]
OUTPUT_CAP = 128
ALLOWED_PATHS = {"TARGET_UB2", "LEGACY_CPU_UB1", "LEGACY_NPU_UB1", "LEGACY_NPU_UB2",
                 "OPTIMUM_REPLAY_CPU_UB1", "OPTIMUM_REPLAY_NPU_UB1", "PERSIST_CPU_UB1",
                 "PERSIST_NPU_UB1", "PERSIST_NPU_UB2"}


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, obj) -> None:
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


def formatted_prompt(row: dict) -> str:
    prompt = "Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n" + row["prompt"]
    return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


def assert_host_gate() -> None:
    battery = psutil.sensors_battery()
    if battery is None or battery.power_plugged is not True:
        raise RuntimeError("AC power must be positively online")
    if (os.environ.get("SESSIONNAME") or "").upper().startswith("RDP"):
        raise RuntimeError("RDP session is forbidden")
    assert_no_duplicate_omp()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["small", "full"], required=True)
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--group", required=True)
    ap.add_argument("--paths", nargs="+", help="full stage: small-gate survivors only")
    ap.add_argument("--small-summary", type=Path, help="required for full: prior small-gate summary")
    ap.add_argument("--freeze-manifest", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    if plan.get("selection_uses_timing") is not False:
        raise RuntimeError("R1 plan does not prove timing-independent selection")
    planned = plan.get("groups", {}).get(args.group)
    if not planned:
        raise RuntimeError(f"group absent from R0-derived plan: {args.group}")
    if args.stage == "small":
        if args.paths is not None:
            raise RuntimeError("small gate must use the complete R0-planned group")
        args.paths = planned
    else:
        if not args.small_summary:
            raise RuntimeError("full gate requires completed small-gate evidence")
        small = json.loads(args.small_summary.read_text(encoding="utf-8"))
        small_status = json.loads((args.small_summary.parent / "R1_STATUS.json").read_text(encoding="utf-8"))
        if (small_status.get("stage") != "small" or small_status.get("complete") is not True
                or small_status.get("group") != args.group
                or small_status.get("plan_sha256") != sha256(args.plan)):
            raise RuntimeError("small-gate provenance differs from this R0 group")
        survivors = [p for p in planned if small.get(p, {}).get("status") == "QUALIFIED"
                     and small[p].get("exact_pairs") == small[p].get("total_pairs") == 18]
        if not survivors:
            raise RuntimeError("no exact small-gate survivors")
        if args.paths is not None and args.paths != survivors:
            raise RuntimeError("full gate paths must equal all exact small-gate survivors")
        args.paths = survivors
    if len(args.paths) != len(set(args.paths)) or set(args.paths) - ALLOWED_PATHS:
        raise ValueError("duplicate or out-of-scope candidate path")
    assert_host_gate()
    freeze = verify_freeze_manifest(args.freeze_manifest)
    if plan.get("inputs", {}).get("source_commit") != freeze["source_commit"]:
        raise RuntimeError("R0 plan source differs from frozen source")
    tasks = load_tasks()
    task_ids = SMALL if args.stage == "small" else FULL
    expected = len(task_ids) * 3
    seed = 20260923 if args.stage == "small" else 20260924
    args.output_dir.mkdir(parents=True, exist_ok=False)
    if any(p.startswith("LEGACY_NPU_") for p in args.paths):
        cache_record = prepare_legacy_npu_cache(args.output_dir)
        write_json(args.output_dir / "legacy_npu_cache.json", cache_record)
    mask = sorted(psutil.Process().cpu_affinity())
    apply_affinity(mask)
    groups = draft_groups(args.paths)
    session = RuntimeProcessSession(mask, tuple(groups))
    status = {"schema": "heterospec.358h.runtime.r1_status.v0.2", "formal": False,
              "claim_status": "QUALIFICATION_ONLY / TIMINGS_INVALID_FOR_HEADLINE_CLAIMS",
              "stage": args.stage, "created_at_utc": utc(), "candidate_paths": args.paths,
              "plan": str(args.plan), "plan_sha256": sha256(args.plan), "group": args.group,
              "expected_pairs_per_path": expected, "completed_observations": 0,
              "complete": False, "dataset_sha256": DATASET_SHA256, "output_cap": OUTPUT_CAP,
              "k": 2, "timing_used_for_promotion": False,
              "freeze_manifest": str(args.freeze_manifest),
              "freeze_manifest_sha256": sha256(args.freeze_manifest),
              "freeze_source_commit": freeze["source_commit"],
              "source_commit": freeze["source_commit"], "session_affinity_mask": mask,
              "ac_power_online": True, "process_start_method": session.start_method}
    write_json(args.output_dir / "R1_STATUS.json", status)
    rows = []
    conditions = ["TARGET_UB1", *args.paths]
    schedule = []
    for task_id in task_ids:
        for rep in range(3):
            order = list(conditions)
            random.Random(seed + task_id * 1009 + rep).shuffle(order)
            schedule.append({"task_id": task_id, "repetition": rep, "conditions": order})
    write_json(args.output_dir / "schedule.json", schedule)
    try:
        init = session.initialize(args.paths)
        info = init["process_info"]
        if not info["target"]["target_import_clean"] or any(
                not d["draft_import_clean"] for d in info["drafts"].values()):
            raise RuntimeError("backend import boundary violated")
        if info["target"]["affinity"] != mask or any(
                d["affinity"] != mask for d in info["drafts"].values()):
            raise RuntimeError("worker affinity mismatch")
        write_json(args.output_dir / "path_initialization.json", init)
        warm = []
        for name in conditions:
            outcome = session.run(name, formatted_prompt(tasks[0]), 8, f"warmup-{name}")
            warm.append({"path": name, "tokens": outcome["result"]["tokens"],
                         "claim_status": "NON_FORMAL / INVALID_FOR_CLAIMS"})
        write_json(args.output_dir / "warmup.json", warm)
        for unit in schedule:
            task_id, rep = unit["task_id"], unit["repetition"]
            formatted = formatted_prompt(tasks[task_id])
            for name in unit["conditions"]:
                observation_id = f"{args.stage}-HumanEval-{task_id}-rep-{rep}-{name}"
                started = utc()
                outcome = session.run(name, formatted, OUTPUT_CAP, observation_id)
                r = outcome["result"]
                spec = parse_path(name)
                row = {"schema": "heterospec.358h.runtime.r1_observation.v0.2",
                       "formal": False, "claim_status": "QUALIFICATION_ONLY",
                       "stage": args.stage, "task_id": f"HumanEval/{task_id}",
                       "repetition": rep, "path": name, "observation_id": observation_id,
                       "started_at_utc": started, "ended_at_utc": utc(),
                       "prompt_token_count": outcome["prompt_tokens"],
                       "generated_token_ids": r["tokens"], "output_token_count": len(r["tokens"]),
                       "timing_diagnostic_only": r["timing_v02"],
                       "harness_roundtrip_ns": outcome["harness_roundtrip_ns"],
                       "rounds": r["rounds"], "proposed": r["proposed"],
                       "accepted": r["accepted"], "target_binding": init["target_init"]["bindings"][f"UB{spec['ubatch']}"],
                       "draft_capabilities": r.get("draft_capabilities"),
                       "target_worker_pid": session.target.pid,
                       "draft_worker_pid": None if spec["kind"] == "TARGET" else session.drafts[
                           ("legacy" if spec["kind"] == "LEGACY" else "optimum") + "_" + spec["device"].lower()].pid,
                       "exact_vs_reference": None, "first_divergence": None}
                rows.append(row)
                with (args.output_dir / "observations.jsonl").open("a", encoding="utf-8", newline="\n") as f:
                    f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                    f.flush(); os.fsync(f.fileno())
                status["completed_observations"] += 1
                status["last_observation"] = observation_id
                write_json(args.output_dir / "R1_STATUS.json", status)
        refs = {(r["task_id"], r["repetition"]): r["generated_token_ids"]
                for r in rows if r["path"] == "TARGET_UB1"}
        if len(refs) != expected:
            raise RuntimeError(f"expected {expected} contemporary target references, got {len(refs)}")
        summary = {}
        for row in rows:
            ref = refs[(row["task_id"], row["repetition"])]
            row["exact_vs_reference"] = row["generated_token_ids"] == ref
            row["first_divergence"] = first_divergence(ref, row["generated_token_ids"])
        for name in conditions:
            subset = [r for r in rows if r["path"] == name]
            exact = sum(r["exact_vs_reference"] for r in subset)
            summary[name] = {"exact_pairs": exact, "total_pairs": len(subset),
                             "status": "QUALIFIED" if exact == len(subset) == expected else "BLOCKED",
                             "performance_promotion_allowed": name != "TARGET_UB1" and exact == len(subset) == expected}
        write_json(args.output_dir / "observations.resolved.json", rows)
        write_json(args.output_dir / "qualification_summary.json", summary)
        status.update(complete=True, completed_at_utc=utc(), qualification=summary)
        write_json(args.output_dir / "R1_STATUS.json", status)
        print(json.dumps(summary, indent=2))
        return 0 if all(x["status"] == "QUALIFIED" for x in summary.values()) else 2
    except Exception as exc:
        status["error"] = repr(exc)
        write_json(args.output_dir / "R1_STATUS.json", status)
        raise
    finally:
        write_json(args.output_dir / "process_shutdown.json", session.close())


if __name__ == "__main__":
    raise SystemExit(main())
