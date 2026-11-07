#!/usr/bin/env python3
"""Bounded paired reproducibility check for high/low-acceptance k=2 prompts."""

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from m4_llama_metal_12q import run_cli, tokenize


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ids = [438, 395]
    rows = {}
    for line in (ROOT / "datasets/Spec-Bench/data/spec_bench/question.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["question_id"] in ids:
            rows[row["question_id"]] = row
    schedule = [(qid, rep, condition) for qid in ids for rep in range(1, 4) for condition in ["baseline", "k2"]]
    random.Random(20260903).shuffle(schedule)
    record = {
        "schema": "heterospec.m4_llama_k2_repro_check.v1",
        "started": datetime.now(timezone.utc).isoformat(), "schedule": schedule, "runs": [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for index, (qid, rep, condition) in enumerate(schedule, 1):
        prompt_path = args.output.parent / f"llama_repro_q{qid}.txt"
        prompt_path.write_text(rows[qid]["turns"][0], encoding="utf-8")
        metrics = run_cli(args.target, args.draft, prompt_path, 64, condition)
        tokens = tokenize(args.target, metrics["completion_text"])
        record["runs"].append({"question_id": qid, "repetition": rep, "condition": condition, "tokens": tokens, "metrics": metrics})
        args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"[{index}/12] q={qid} rep={rep} {condition} {metrics['decode_ms']:.2f}ms", flush=True)
    for qid in ids:
        for rep in range(1, 4):
            pair = [r for r in record["runs"] if r["question_id"] == qid and r["repetition"] == rep]
            baseline = next(r for r in pair if r["condition"] == "baseline")
            spec = next(r for r in pair if r["condition"] == "k2")
            spec["exact_match"] = spec["tokens"] == baseline["tokens"]
            spec["speedup"] = baseline["metrics"]["decode_ms"] / spec["metrics"]["decode_ms"]
    record["status"] = "PASS" if all(r.get("exact_match", True) for r in record["runs"]) else "FAIL_CORRECTNESS"
    record["ended"] = datetime.now(timezone.utc).isoformat()
    args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
