#!/usr/bin/env python3
"""Compare target-only decode with an idle draft model resident on Metal."""

import argparse
import json
import random
import statistics
from datetime import datetime, timezone
from pathlib import Path

from m4_llama_metal_12q import run_cli


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=5)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    prompt = "Explain why the sky appears blue in three concise sentences."
    prompt_path = args.output.parent / "llama_residency_prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    order = ["target_only", "draft_resident"] * args.repetitions
    random.Random(20260903).shuffle(order)
    record = {
        "schema": "heterospec.m4_llama_draft_residency_control.v1",
        "started": datetime.now(timezone.utc).isoformat(), "order": order, "runs": [],
    }
    for index, condition in enumerate(order, 1):
        extra = None
        if condition == "draft_resident":
            extra = [
                "--spec-type", "none", "--model-draft", str(args.draft),
                "--spec-draft-device", "MTL0", "--spec-draft-ngl", "all",
            ]
        metrics = run_cli(args.target, args.draft, prompt_path, 64, "baseline", extra)
        record["runs"].append({"condition": condition, "metrics": metrics})
        args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"[{index}/{len(order)}] {condition} decode_ms={metrics['decode_ms']:.2f}", flush=True)
    medians = {
        condition: statistics.median(
            run["metrics"]["decode_ms"] for run in record["runs"] if run["condition"] == condition
        ) for condition in ["target_only", "draft_resident"]
    }
    record["medians_ms"] = medians
    record["resident_overhead_ratio"] = medians["draft_resident"] / medians["target_only"] - 1
    record["status"] = "PASS"
    record["ended"] = datetime.now(timezone.utc).isoformat()
    args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({"medians_ms": medians, "resident_overhead_ratio": record["resident_overhead_ratio"]}, indent=2))


if __name__ == "__main__":
    main()
