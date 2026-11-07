#!/usr/bin/env python3
"""Frozen-k confirmatory validation for M4 llama.cpp Metal."""

import argparse
import hashlib
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

from m4_llama_metal_12q import (
    integrate_energy, run_cli, save, start_telemetry, stop_telemetry, tokenize,
)
from m4_mlx_smoke import first_divergence, memory_snapshot


ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--selection", type=Path, default=ROOT / "benchmarks/m4_confirmatory_24q/selection.json")
    parser.add_argument("--dataset", type=Path, default=ROOT / "datasets/Spec-Bench/data/spec_bench/question.jsonl")
    parser.add_argument("--telemetry-probe", type=Path, default=ROOT / "work/m4/silemetry_csv_probe")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--telemetry-output", type=Path, required=True)
    args = parser.parse_args()

    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    ids = selection["question_ids"]
    if len(ids) != 24 or not selection.get("selection_frozen_before_generation"):
        raise RuntimeError("Confirmatory selection must contain 24 pre-frozen IDs")
    prior = set(selection["excluded_prior_m4_ids"])
    if prior.intersection(ids):
        raise RuntimeError("Confirmatory IDs overlap prior M4 diagnostics")
    wanted = set(ids)
    rows = {}
    for line in args.dataset.read_text().splitlines():
        row = json.loads(line)
        if row["question_id"] in wanted:
            rows[row["question_id"]] = row
    if rows.keys() != wanted:
        raise RuntimeError(f"Missing IDs: {sorted(wanted - rows.keys())}")
    group_by_id = {
        qid: group for group, group_ids in selection["question_ids_by_group"].items() for qid in group_ids
    }

    rng = random.Random(selection["seed"])
    schedule = []
    for repetition in range(1, 4):
        rep_ids = ids.copy()
        rng.shuffle(rep_ids)
        for question_id in rep_ids:
            order = ["baseline", "k2"]
            rng.shuffle(order)
            schedule.append({"question_id": question_id, "repetition": repetition, "order": order})

    record = {
        "schema": "heterospec.m4_llama_confirmatory_24q.v1",
        "started": now(), "status": "STARTED", "target": str(args.target), "draft": str(args.draft),
        "selection": selection, "k": 2, "temperature": 0, "batch_size": 1,
        "max_tokens": 64, "repetitions": 3, "schedule": schedule,
        "telemetry_csv": str(args.telemetry_output), "memory_before": memory_snapshot(), "runs": [],
    }
    save(record, args.output)
    telemetry, stream = start_telemetry(args.telemetry_probe, args.telemetry_output)
    completed = 0
    try:
        for block in schedule:
            question_id = block["question_id"]
            repetition = block["repetition"]
            prompt_path = args.output.parent / f"confirmatory_q{question_id}.txt"
            prompt_path.write_text(rows[question_id]["turns"][0], encoding="utf-8")
            pair = []
            for order_index, condition in enumerate(block["order"]):
                metrics = run_cli(args.target, args.draft, prompt_path, 64, condition)
                tokens = tokenize(args.target, metrics["completion_text"])
                item = {
                    "question_id": question_id, "group": group_by_id[question_id],
                    "category": rows[question_id].get("category"), "repetition": repetition,
                    "order_index": order_index, "condition": condition, "tokens": tokens,
                    "token_sha256": hashlib.sha256(",".join(map(str, tokens)).encode()).hexdigest(),
                    "metrics": metrics,
                }
                record["runs"].append(item)
                pair.append(item)
                completed += 1
                save(record, args.output)
                print(f"[{completed}/144] rep={repetition} q={question_id} {condition} {metrics['decode_ms']:.2f}ms memory={metrics['memory_gate']['status']}", flush=True)
            baseline = next(item for item in pair if item["condition"] == "baseline")
            speculative = next(item for item in pair if item["condition"] == "k2")
            speculative["exact_match"] = speculative["tokens"] == baseline["tokens"]
            speculative["first_divergent_token"] = first_divergence(baseline["tokens"], speculative["tokens"])
            speculative["paired_speedup"] = baseline["metrics"]["decode_ms"] / speculative["metrics"]["decode_ms"]
            save(record, args.output)
            if not speculative["exact_match"]:
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
        output_tokens = metrics["output_tokens_runtime"]
        if metrics["energy"]["status"] == "PASS":
            metrics["energy_per_output_token"] = {
                key.replace("_energy_j", "_j_per_token"): value / output_tokens
                for key, value in metrics["energy"].items() if key.endswith("_energy_j")
            }
    record["memory_after"] = memory_snapshot()
    record["ended"] = now()
    save(record, args.output)
    print(json.dumps({"status": record["status"], "runs": len(record["runs"])}, indent=2))
    return 0 if record["status"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
