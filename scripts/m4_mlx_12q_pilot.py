#!/usr/bin/env python3
"""Bounded 12-question MLX native-speculation pilot for Apple Silicon."""

import argparse
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from mlx_lm import load

from m4_mlx_smoke import run


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IDS = ROOT / "benchmarks" / "root_cause_12q" / "selection.json"
DEFAULT_DATASET = ROOT / "datasets" / "Spec-Bench" / "data" / "spec_bench" / "question.jsonl"


def now():
    return datetime.now(timezone.utc).isoformat()


def swap_snapshot():
    text = subprocess.check_output(["sysctl", "vm.swapusage"], text=True).strip()
    match = re.search(r"used = ([0-9.]+)M", text)
    if not match:
        raise RuntimeError(f"Cannot parse swap usage: {text}")
    return {"raw": text, "used_mib": float(match.group(1))}


def save(record, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(record, indent=2), encoding="utf-8")
    temporary.replace(output)


def main():
    parser = argparse.ArgumentParser()
    model_root = Path(os.environ.get("HETEROSPEC_MODEL_ROOT", Path.home() / ".cache/heterospec/models"))
    parser.add_argument("--target", default=str(model_root / "Qwen3-8B-4bit"))
    parser.add_argument("--draft", default=str(model_root / "Qwen3-0.6B-4bit"))
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--selection", type=Path, default=DEFAULT_IDS)
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--warmup-tokens", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    selection = json.loads(args.selection.read_text())
    question_ids = selection["question_ids"]
    if len(question_ids) != 12:
        raise RuntimeError(f"The bounded pilot requires exactly 12 frozen IDs, got {len(question_ids)}")
    wanted = set(question_ids)
    questions = {}
    for line in args.dataset.read_text().splitlines():
        row = json.loads(line)
        if row["question_id"] in wanted:
            questions[row["question_id"]] = row
    missing = wanted - questions.keys()
    if missing:
        raise RuntimeError(f"Dataset is missing frozen IDs: {sorted(missing)}")

    conditions = [
        {"name": "baseline", "k": None},
        {"name": "k2", "k": 2},
        {"name": "k4", "k": 4},
        {"name": "k6", "k": 6},
    ]
    record = {
        "schema": "heterospec.m4_mlx_12q_pilot.v1",
        "started": now(),
        "status": "STARTED",
        "target": args.target,
        "draft": args.draft,
        "temperature": 0,
        "batch_size": 1,
        "max_tokens": args.max_tokens,
        "repetitions": args.repetitions,
        "question_ids": question_ids,
        "selection": selection,
        "order": "four-condition cyclic Latin rotation by question index plus repetition",
        "swap_before": swap_snapshot(),
        "runs": [],
    }
    if record["swap_before"]["used_mib"] != 0:
        raise RuntimeError("Pilot refuses to start with non-zero swap")
    save(record, args.output)

    target, tokenizer = load(args.target)
    draft, draft_tokenizer = load(args.draft)
    if draft_tokenizer.vocab_size != tokenizer.vocab_size:
        raise RuntimeError("Draft and target tokenizer vocabularies differ")
    warmup = [{"role": "user", "content": "Reply with OK."}]
    run(target, tokenizer, warmup, args.warmup_tokens)
    for k in (2, 4, 6):
        run(target, tokenizer, warmup, args.warmup_tokens, draft, k)

    total = len(question_ids) * args.repetitions * len(conditions)
    completed = 0
    for repetition in range(args.repetitions):
        for question_index, question_id in enumerate(question_ids):
            row = questions[question_id]
            messages = [{"role": "user", "content": row["turns"][0]}]
            rotation = (question_index + repetition) % len(conditions)
            ordered = conditions[rotation:] + conditions[:rotation]
            block = []
            for order_index, condition in enumerate(ordered):
                if condition["k"] is None:
                    metrics = run(target, tokenizer, messages, args.max_tokens)
                else:
                    metrics = run(
                        target,
                        tokenizer,
                        messages,
                        args.max_tokens,
                        draft,
                        condition["k"],
                    )
                item = {
                    "question_id": question_id,
                    "category": row.get("category"),
                    "repetition": repetition + 1,
                    "order_index": order_index,
                    "condition": condition["name"],
                    "k": condition["k"],
                    "metrics": metrics,
                    "swap_after": swap_snapshot(),
                }
                record["runs"].append(item)
                block.append(item)
                completed += 1
                save(record, args.output)
                print(
                    f"[{completed}/{total}] q={question_id} rep={repetition + 1} "
                    f"condition={condition['name']} rate={metrics['end_to_end_tokens_per_second']:.2f} tok/s "
                    f"swap={item['swap_after']['used_mib']:.2f} MiB",
                    flush=True,
                )
                if item["swap_after"]["used_mib"] != 0:
                    record["status"] = "ABORTED_SWAP_GROWTH"
                    record["ended"] = now()
                    save(record, args.output)
                    return 2

            baseline = next(item for item in block if item["condition"] == "baseline")
            reference = baseline["metrics"]["tokens"]
            for item in block:
                item["exact_match"] = item["metrics"]["tokens"] == reference
            if not all(item["exact_match"] for item in block):
                record["status"] = "ABORTED_CORRECTNESS"
                record["ended"] = now()
                save(record, args.output)
                return 3
            save(record, args.output)

    record["swap_after"] = swap_snapshot()
    record["status"] = "PASS"
    record["ended"] = now()
    save(record, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
