#!/usr/bin/env python3
"""Bounded M4 baseline/speculative smoke test with exact-token comparison."""

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import mlx.core as mx
from mlx_lm import load, stream_generate


def swap_usage():
    text = subprocess.check_output(["sysctl", "vm.swapusage"], text=True).strip()
    return text


def digest(tokens):
    payload = ",".join(map(str, tokens)).encode()
    return hashlib.sha256(payload).hexdigest()


def first_divergence(left, right):
    for index, pair in enumerate(zip(left, right)):
        if pair[0] != pair[1]:
            return index
    return None if len(left) == len(right) else min(len(left), len(right))


def run(model, tokenizer, messages, max_tokens, draft=None, k=4):
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
    )
    mx.reset_peak_memory()
    wall_started_ns = time.time_ns()
    started = time.perf_counter()
    first = None
    first_wall_ns = None
    tokens, from_draft = [], []
    last_response = None
    for response in stream_generate(
        model,
        tokenizer,
        prompt,
        max_tokens=max_tokens,
        draft_model=draft,
        num_draft_tokens=k,
    ):
        last_response = response
        if first is None:
            first = time.perf_counter()
            first_wall_ns = time.time_ns()
        tokens.append(int(response.token))
        from_draft.append(bool(response.from_draft))
    ended = time.perf_counter()
    wall_ended_ns = time.time_ns()
    return {
        "wall_started_unix_ns": wall_started_ns,
        "first_token_unix_ns": first_wall_ns,
        "wall_ended_unix_ns": wall_ended_ns,
        "tokens": tokens,
        "token_sha256": digest(tokens),
        "output_tokens": len(tokens),
        "ttft_ms": (first - started) * 1000 if first else None,
        "completion_ms": (ended - started) * 1000,
        "end_to_end_tokens_per_second": len(tokens) / (ended - started),
        "generation_tokens_per_second": last_response.generation_tps if last_response else None,
        "prompt_tokens": last_response.prompt_tokens if last_response else None,
        "prompt_tokens_per_second": last_response.prompt_tps if last_response else None,
        "accepted_draft_tokens": sum(from_draft),
        "accepted_output_fraction": sum(from_draft) / len(tokens) if tokens else 0,
        "from_draft": from_draft,
        "mlx_peak_memory_gib": mx.get_peak_memory() / 1024**3,
    }


def main():
    parser = argparse.ArgumentParser()
    model_root = Path(os.environ.get("HETEROSPEC_MODEL_ROOT", Path.home() / ".cache/heterospec/models"))
    parser.add_argument("--target", default=str(model_root / "Qwen3-8B-4bit"))
    parser.add_argument("--draft", default=str(model_root / "Qwen3-0.6B-4bit"))
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--question-id", type=int, default=469)
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--warmup-tokens", type=int, default=4)
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.dataset:
        rows = (json.loads(line) for line in args.dataset.read_text().splitlines())
        question = next(row for row in rows if row["question_id"] == args.question_id)
        messages = [{"role": "user", "content": question["turns"][0]}]
        prompt_source = {"dataset": str(args.dataset), "question_id": args.question_id}
    else:
        messages = [{"role": "user", "content": "Explain in two sentences why the sky appears blue."}]
        prompt_source = {"dataset": None, "question_id": None, "fallback": "embedded canary"}

    record = {
        "started": datetime.now(timezone.utc).isoformat(),
        "target": args.target,
        "draft": args.draft,
        "temperature": 0,
        "batch_size": 1,
        "k": args.k,
        "prompt_source": prompt_source,
        "swap_before": swap_usage(),
    }
    target, tokenizer = load(args.target)
    warmup = [{"role": "user", "content": "Reply with OK."}]
    run(target, tokenizer, warmup, args.warmup_tokens)
    record["baseline"] = run(target, tokenizer, messages, args.max_tokens)
    if args.baseline_only:
        record["speculative"] = None
        record["exact_match"] = None
        record["first_divergent_token"] = None
        record["swap_after"] = swap_usage()
        record["status"] = "PASS"
        record["ended"] = datetime.now(timezone.utc).isoformat()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(json.dumps({k: record[k] for k in ("status", "swap_before", "swap_after")}, indent=2))
        return
    draft, draft_tokenizer = load(args.draft)
    if draft_tokenizer.vocab_size != tokenizer.vocab_size:
        raise RuntimeError("Draft and target tokenizer vocabularies differ")
    run(target, tokenizer, warmup, args.warmup_tokens, draft, args.k)
    record["speculative"] = run(target, tokenizer, messages, args.max_tokens, draft, args.k)
    left, right = record["baseline"]["tokens"], record["speculative"]["tokens"]
    record["exact_match"] = left == right
    record["first_divergent_token"] = first_divergence(left, right)
    record["swap_after"] = swap_usage()
    record["status"] = "PASS" if record["exact_match"] else "FAIL_CORRECTNESS"
    record["ended"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({k: record[k] for k in ("status", "exact_match", "first_divergent_token", "swap_before", "swap_after")}, indent=2))


if __name__ == "__main__":
    main()
