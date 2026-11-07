#!/usr/bin/env python3
"""Tiny deterministic source-vs-GGUF semantic diagnostic (never a benchmark)."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


PROMPTS = [
    "The capital of France is",
    "2 + 2 =",
    "def add(a, b):\n    return",
    "The quick brown fox",
    "你好，我是",
    "Reason carefully: 17 * 23 =",
]


def digest_ids(ids: list[int]) -> str:
    return hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode("ascii")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--gguf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.source, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.source,
        local_files_only=True,
        dtype="auto",
        device_map="cpu",
    )
    model.eval()
    source_results: dict[str, list[int]] = {}
    with torch.inference_mode():
        for prompt in PROMPTS:
            encoded = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
            input_length = int(encoded["input_ids"].shape[1])
            generated = model.generate(
                **encoded,
                do_sample=False,
                max_new_tokens=8,
                min_new_tokens=8,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=None,
            )
            source_results[prompt] = [int(item) for item in generated[0, input_length:].tolist()]
    del model
    gc.collect()

    import openvino_genai as ov_genai

    pipeline = ov_genai.LLMPipeline(str(args.gguf), "CPU", PERFORMANCE_HINT="LATENCY")
    gguf_tokenizer = pipeline.get_tokenizer()
    config = ov_genai.GenerationConfig()
    config.do_sample = False
    config.max_new_tokens = 8
    config.min_new_tokens = 8
    config.ignore_eos = True
    checks = []
    for prompt in PROMPTS:
        encoded = gguf_tokenizer.encode(prompt, add_special_tokens=False)
        result = pipeline.generate(encoded, config)
        gguf_ids = [int(item) for item in result.tokens[0]]
        source_ids = source_results[prompt]
        prefix = 0
        for left, right in zip(source_ids, gguf_ids):
            if left != right:
                break
            prefix += 1
        checks.append(
            {
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "source_token_ids": source_ids,
                "gguf_token_ids": gguf_ids,
                "first_token_match": bool(source_ids and gguf_ids and source_ids[0] == gguf_ids[0]),
                "matching_prefix_tokens": prefix,
                "full_eight_token_match": source_ids == gguf_ids,
                "source_ids_sha256": digest_ids(source_ids),
                "gguf_ids_sha256": digest_ids(gguf_ids),
            }
        )

    first_token_matches = sum(item["first_token_match"] for item in checks)
    full_matches = sum(item["full_eight_token_match"] for item in checks)
    payload = {
        "schema": "heterospec.358h.source_gguf_functional_equivalence.v1",
        "formal_measurement": False,
        "performance_metrics_recorded": False,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "decoding": {
            "deterministic_greedy": True,
            "new_tokens": 8,
            "eos_ignored_for_fixed_length": True,
        },
        "prompt_count": len(PROMPTS),
        "first_token_matches": first_token_matches,
        "full_eight_token_matches": full_matches,
        "checks": checks,
        "interpretation": "Diagnostic only. Q8_0 and BF16/FP32 arithmetic need not be numerically identical.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "prompt_count": len(PROMPTS),
        "first_token_matches": first_token_matches,
        "full_eight_token_matches": full_matches,
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
