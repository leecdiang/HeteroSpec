#!/usr/bin/env python3
"""Measure the k=2 synthetic-acceptance crossover in llama.cpp Metal."""

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from m4_llama_metal_12q import run_cli


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    prompt = "Explain why the sky appears blue in three concise sentences."
    args.output.parent.mkdir(parents=True, exist_ok=True)
    prompt_path = args.output.parent / "llama_synthetic_prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    conditions = ["baseline", "p20", "p40", "p60", "p80", "p100"] * args.repetitions
    random.Random(20260903).shuffle(conditions)
    record = {
        "schema": "heterospec.m4_llama_synthetic_crossover.v1",
        "started": datetime.now(timezone.utc).isoformat(), "order_seed": 20260903,
        "k": 2, "repetitions": args.repetitions, "order": conditions, "runs": [],
    }
    for index, condition in enumerate(conditions, 1):
        if condition == "baseline":
            metrics = run_cli(args.target, args.draft, prompt_path, 64, "baseline")
            requested = None
        else:
            requested = int(condition[1:]) / 100
            rates = f"{requested},{requested}"
            metrics = run_cli(
                args.target, args.draft, prompt_path, 64, "k2",
                ["--spec-synth-rates", rates],
            )
        record["runs"].append({"condition": condition, "requested_rate": requested, "metrics": metrics})
        args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"[{index}/{len(conditions)}] {condition} decode_ms={metrics['decode_ms']:.2f} observed={metrics.get('acceptance_rate')}", flush=True)
    record["status"] = "PASS"
    record["ended"] = datetime.now(timezone.utc).isoformat()
    args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
