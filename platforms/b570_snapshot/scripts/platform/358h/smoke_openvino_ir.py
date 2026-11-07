#!/usr/bin/env python3
"""Bounded, non-timed OpenVINO GenAI IR smoke for one physical device."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import traceback
from datetime import datetime, timezone
from pathlib import Path

import openvino as ov
import openvino_genai as ov_genai
import numpy as np


PHYSICAL_DEVICES = {"CPU", "GPU", "NPU"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--max-prompt-len", type=int, default=128)
    parser.add_argument("--prompt-tokens", type=int)
    parser.add_argument("--prefill-hint", choices=["STATIC", "DYNAMIC"], default="STATIC")
    args = parser.parse_args()
    if args.device not in PHYSICAL_DEVICES:
        parser.error("device must be exactly CPU, GPU, or NPU")

    core = ov.Core()
    files_before = [item for item in args.model_dir.rglob("*") if item.is_file()]
    pipeline_config: dict[str, object]
    if args.device == "NPU":
        pipeline_config = {
            "MAX_PROMPT_LEN": args.max_prompt_len,
            "MIN_RESPONSE_LEN": 4,
            "PREFILL_HINT": args.prefill_hint,
            "GENERATE_HINT": "FAST_COMPILE",
        }
        if args.cache_dir:
            args.cache_dir.mkdir(parents=True, exist_ok=True)
            pipeline_config["CACHE_DIR"] = str(args.cache_dir.resolve())
    else:
        pipeline_config = {"PERFORMANCE_HINT": "LATENCY"}

    payload = {
        "schema": "heterospec.358h.openvino_ir_smoke.v1",
        "formal_measurement": False,
        "performance_metrics_recorded": False,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_dir": str(args.model_dir.resolve()),
        "model_files": [
            {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(files_before)
        ],
        "requested_device": args.device,
        "available_devices": list(core.available_devices),
        "pipeline_config": pipeline_config,
        "openvino": ov.get_version(),
        "openvino_genai": getattr(ov_genai, "__version__", "unknown"),
        "python": platform.python_version(),
        "status": "FAIL",
        "actual_execution_devices": None,
        "actual_execution_devices_status": "LLMPipeline does not expose its internal compiled models; strict evidence is recorded separately through lower-level OpenVINO qualification.",
    }
    try:
        pipe = ov_genai.LLMPipeline(str(args.model_dir), args.device, pipeline_config)
        tokenizer = pipe.get_tokenizer()
        prompt = "Hello"
        if args.prompt_tokens:
            base = "Heterogeneous computing requires reproducible device qualification. "
            encoded = tokenizer.encode(base * (args.prompt_tokens // 4 + 32), add_special_tokens=False)
            ids = np.asarray(encoded.input_ids.data, dtype=np.int64).reshape(-1)[: args.prompt_tokens].reshape(1, -1)
            mask = np.ones_like(ids, dtype=np.int64)
            tokenized = ov_genai.TokenizedInputs(ov.Tensor(ids), ov.Tensor(mask))
        else:
            tokenized = tokenizer.encode(prompt, add_special_tokens=False)
        config = ov_genai.GenerationConfig()
        config.do_sample = False
        config.max_new_tokens = 4
        config.min_new_tokens = 4
        config.ignore_eos = True
        result = pipe.generate(tokenized, config)
        token_ids = [int(value) for value in result.tokens[0]]
        input_ids = [int(value) for value in tokenized.input_ids.data[0]]
        payload.update(
            status="PASS_BOUNDED_GENERATION",
            prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            input_token_ids=input_ids,
            input_token_ids_sha256=hashlib.sha256(
                json.dumps(input_ids, separators=(",", ":")).encode("ascii")
            ).hexdigest(),
            input_token_count=int(tokenized.input_ids.data.shape[1]),
            generated_token_ids=token_ids,
            generated_token_ids_sha256=hashlib.sha256(
                json.dumps(token_ids, separators=(",", ":")).encode("ascii")
            ).hexdigest(),
            output_structurally_valid=bool(token_ids) and len(token_ids) <= 4,
        )
    except Exception as exc:
        payload.update(error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc())

    if args.cache_dir and args.cache_dir.exists():
        payload["generated_cache_files"] = [
            {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(item for item in args.cache_dir.rglob("*") if item.is_file())
        ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "requested_device": args.device,
        "status": payload["status"],
        "generated_token_ids": payload.get("generated_token_ids"),
        "cache_files": len(payload.get("generated_cache_files", [])),
    }, indent=2))
    return 0 if payload["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
