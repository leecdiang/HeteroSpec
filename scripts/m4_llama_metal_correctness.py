#!/usr/bin/env python3
"""Strict baseline-versus-draft correctness gate for llama.cpp Metal."""

import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from m4_mlx_smoke import first_divergence, memory_gate, memory_snapshot


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "datasets" / "Spec-Bench" / "data" / "spec_bench" / "question.jsonl"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(tokens):
    return hashlib.sha256(",".join(map(str, tokens)).encode()).hexdigest()


def tokenize(model, text):
    result = subprocess.run(
        ["llama-tokenize", "--model", str(model), "--stdin", "--ids"],
        input=text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return json.loads(result.stdout.strip())


def run_cli(target, prompt, max_tokens, draft=None, k=2):
    command = [
        "llama-cli", "--model", str(target), "--device", "MTL0",
        "--n-gpu-layers", "all", "--file", str(prompt), "--n-predict", str(max_tokens),
        "--temp", "0", "--top-k", "0", "--top-p", "1", "--min-p", "0",
        "--seed", "123", "--single-turn", "--simple-io", "--no-display-prompt",
        "--no-warmup", "--no-perf", "--chat-template-kwargs", '{"enable_thinking":false}',
    ]
    if draft:
        command += [
            "--spec-type", "draft-simple", "--model-draft", str(draft),
            "--spec-draft-device", "MTL0", "--spec-draft-ngl", "all",
            "--spec-draft-n-max", str(k), "--spec-draft-n-min", "0",
        ]
    started_ns = time.time_ns()
    started = time.perf_counter()
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    ended = time.perf_counter()
    prompt_text = Path(prompt).read_text(encoding="utf-8")
    prefix = f"> {prompt_text}\n"
    if prefix not in result.stdout or "\n\n[ Prompt:" not in result.stdout:
        raise RuntimeError("Could not isolate completion from llama-cli output")
    completion_text = result.stdout.split(prefix, 1)[1].rsplit("\n\n[ Prompt:", 1)[0]
    return {
        "wall_started_unix_ns": started_ns,
        "wall_ended_unix_ns": time.time_ns(),
        "completion_ms": (ended - started) * 1000,
        "output_text": result.stdout,
        "completion_text": completion_text,
        "stderr_tail": result.stderr[-2000:],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--question-ids", default="395,469")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--k", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    ids = [int(value) for value in args.question_ids.split(",")]
    rows = {json.loads(line)["question_id"]: json.loads(line) for line in args.dataset.read_text().splitlines()}
    record = {
        "schema": "heterospec.m4_llama_metal_correctness.v1",
        "started": now(), "target": str(args.target), "draft": str(args.draft),
        "tokenizer": "embedded_in_target_gguf", "question_ids": ids, "k": args.k,
        "max_tokens": args.max_tokens, "temperature": 0, "memory_before": memory_snapshot(), "runs": [],
    }
    process_started = time.perf_counter()
    for question_id in ids:
        question = rows[question_id]
        # llama-cli applies the chat template embedded in the target GGUF.
        prompt_text = question["turns"][0]
        prompt_path = args.output.parent / f"llama_q{question_id}_prompt.txt"
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt_text, encoding="utf-8")
        baseline = run_cli(args.target, prompt_path, args.max_tokens)
        speculative = run_cli(args.target, prompt_path, args.max_tokens, args.draft, args.k)
        # Canonicalize the pure completion through the tokenizer embedded in the
        # target GGUF, without crossing the prompt/completion BPE boundary.
        baseline_tokens = tokenize(args.target, baseline["completion_text"])
        speculative_tokens = tokenize(args.target, speculative["completion_text"])
        record["runs"].append({
            "question_id": question_id,
            "baseline": {**baseline, "tokens": baseline_tokens, "token_sha256": digest(baseline_tokens)},
            "speculative": {**speculative, "tokens": speculative_tokens, "token_sha256": digest(speculative_tokens)},
            "exact_match": baseline_tokens == speculative_tokens,
            "first_divergent_token": first_divergence(baseline_tokens, speculative_tokens),
        })
    record["memory_after"] = memory_snapshot()
    record["memory_gate"] = memory_gate(record["memory_before"], record["memory_after"], time.perf_counter() - process_started)
    record["status"] = "PASS" if all(item["exact_match"] for item in record["runs"]) else "FAIL_CORRECTNESS"
    record["ended"] = now()
    args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({"status": record["status"], "memory_gate": record["memory_gate"], "runs": [
        {"question_id": item["question_id"], "exact_match": item["exact_match"], "first_divergent_token": item["first_divergent_token"]} for item in record["runs"]
    ]}, indent=2))


if __name__ == "__main__":
    main()
