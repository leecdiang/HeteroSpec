#!/usr/bin/env python3
"""Collect direct llama.cpp k=2 draft timing statistics on the frozen 12Q set."""

import argparse
import json
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
    selection = json.loads((ROOT / "benchmarks/root_cause_12q/selection.json").read_text())
    wanted = set(selection["question_ids"])
    rows = {}
    for line in (ROOT / "datasets/Spec-Bench/data/spec_bench/question.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["question_id"] in wanted:
            rows[row["question_id"]] = row
    record = {
        "schema": "heterospec.m4_llama_k2_decomposition.v1",
        "started": datetime.now(timezone.utc).isoformat(),
        "target": str(args.target), "draft": str(args.draft), "runs": [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for index, question_id in enumerate(selection["question_ids"], 1):
        prompt = rows[question_id]["turns"][0]
        prompt_path = args.output.parent / f"llama_decomp_q{question_id}.txt"
        prompt_path.write_text(prompt, encoding="utf-8")
        metrics = run_cli(args.target, args.draft, prompt_path, 64, "k2")
        metrics["canonical_output_tokens"] = len(tokenize(args.target, metrics["completion_text"]))
        record["runs"].append({"question_id": question_id, "category": rows[question_id].get("category"), "metrics": metrics})
        args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"[{index}/12] q={question_id} draft_ms={metrics.get('spec_impl_duration_ms', {}).get('draft_generate')} decode_ms={metrics['decode_ms']}", flush=True)
    record["status"] = "PASS"
    record["ended"] = datetime.now(timezone.utc).isoformat()
    args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
