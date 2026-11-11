#!/usr/bin/env python3
"""Run the preregistered M4 HumanEval workload-conditioned study."""

import argparse
import gzip
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from m4_llama_metal_12q import (
    integrate_energy, run_cli, save, start_telemetry, stop_telemetry, tokenize,
)
from m4_mlx_smoke import first_divergence, memory_snapshot


ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def load_problems(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return {row["task_id"]: row for row in map(json.loads, stream)}


def condition_args(condition):
    if condition == "baseline":
        return "baseline", []
    if condition == "fixed_k2":
        return "k2", []
    if condition == "k2_pmin_0.8":
        return "k2", ["--spec-draft-p-min", "0.8"]
    if condition == "k2_pmin_0.9":
        return "k2", ["--spec-draft-p-min", "0.9"]
    raise ValueError(condition)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument(
        "--preregistration", type=Path,
        default=ROOT / "benchmarks/m4_code_conditioned_30q/preregistration.json",
    )
    parser.add_argument(
        "--dataset", type=Path,
        default=ROOT / "datasets/human-eval/data/HumanEval.jsonl.gz",
    )
    parser.add_argument("--telemetry-probe", type=Path, default=ROOT / "work/m4/silemetry_csv_probe")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--telemetry-output", type=Path, required=True)
    args = parser.parse_args()

    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    ids = prereg["dataset"]["task_ids"]
    if len(ids) != 30 or not prereg["dataset"]["selection_frozen_before_prompt_download"]:
        raise RuntimeError("Expected 30 task IDs frozen before prompt download")
    problems = load_problems(args.dataset)
    missing = set(ids) - set(problems)
    if missing:
        raise RuntimeError(f"Missing HumanEval tasks: {sorted(missing)}")

    conditions = ["baseline", "fixed_k2", "k2_pmin_0.8", "k2_pmin_0.9"]
    rng = random.Random(20260909)
    schedule = []
    for repetition in range(1, 4):
        rep_ids = ids.copy()
        rng.shuffle(rep_ids)
        for task_id in rep_ids:
            order = conditions.copy()
            rng.shuffle(order)
            schedule.append({"task_id": task_id, "repetition": repetition, "order": order})

    dataset_sha = hashlib.sha256(args.dataset.read_bytes()).hexdigest()
    record = {
        "schema": "heterospec.m4_humaneval_code_conditioned.v1",
        "started": now(), "status": "STARTED", "preregistration": prereg,
        "dataset": str(args.dataset), "dataset_sha256": dataset_sha,
        "human_eval_git_commit": "6d43fb980f9fee3c892a914eda09951f772ad10d",
        "target": str(args.target), "draft": str(args.draft),
        "conditions": conditions, "schedule": schedule, "runs": [],
        "telemetry_csv": str(args.telemetry_output), "memory_before": memory_snapshot(),
    }
    save(record, args.output)
    telemetry, stream = start_telemetry(args.telemetry_probe, args.telemetry_output)
    completed = 0
    total = len(schedule) * len(conditions)
    try:
        for block in schedule:
            task_id = block["task_id"]
            prompt = prereg["fixed_runtime"]["prompt_template"].replace(
                "{humaneval_prompt}", problems[task_id]["prompt"]
            )
            prompt_path = args.output.parent / f"humaneval_{task_id.replace('/', '_')}.txt"
            prompt_path.write_text(prompt, encoding="utf-8")
            pair = []
            for order_index, condition in enumerate(block["order"]):
                run_condition, extra_args = condition_args(condition)
                metrics = run_cli(args.target, args.draft, prompt_path, 128, run_condition, extra_args)
                tokens = tokenize(args.target, metrics["completion_text"])
                item = {
                    "task_id": task_id, "repetition": block["repetition"],
                    "order_index": order_index, "condition": condition,
                    "tokens": tokens,
                    "token_sha256": hashlib.sha256(",".join(map(str, tokens)).encode()).hexdigest(),
                    "metrics": metrics,
                }
                record["runs"].append(item)
                pair.append(item)
                completed += 1
                save(record, args.output)
                print(
                    f"[{completed}/{total}] rep={block['repetition']} {task_id} {condition} "
                    f"decode={metrics['decode_ms']:.2f}ms memory={metrics['memory_gate']['status']}",
                    flush=True,
                )
            baseline = next(item for item in pair if item["condition"] == "baseline")
            for item in pair:
                item["exact_match"] = item["tokens"] == baseline["tokens"]
                item["first_divergent_token"] = first_divergence(baseline["tokens"], item["tokens"])
                if item["condition"] != "baseline":
                    item["paired_speedup"] = baseline["metrics"]["decode_ms"] / item["metrics"]["decode_ms"]
            save(record, args.output)
            if not all(item["exact_match"] for item in pair):
                record["status"] = "ABORTED_CORRECTNESS"
                break
        else:
            record["status"] = "PASS"
    finally:
        stop_telemetry(telemetry, stream)

    for item in record["runs"]:
        metrics = item["metrics"]
        metrics["energy"] = integrate_energy(
            args.telemetry_output, metrics["decode_start_unix_ns"], metrics["decode_end_unix_ns"]
        )
        if metrics["energy"]["status"] == "PASS":
            count = metrics["output_tokens_runtime"]
            metrics["energy_per_output_token"] = {
                key.replace("_energy_j", "_j_per_token"): value / count
                for key, value in metrics["energy"].items() if key.endswith("_energy_j")
            }
    record["memory_after"] = memory_snapshot()
    record["ended"] = now()
    save(record, args.output)
    print(json.dumps({"status": record["status"], "runs": len(record["runs"])}, indent=2))
    return 0 if record["status"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
