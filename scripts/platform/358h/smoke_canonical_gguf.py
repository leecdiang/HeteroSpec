#!/usr/bin/env python3
"""Run a bounded, non-timed OpenVINO GenAI GGUF device smoke test."""

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


PHYSICAL_DEVICES = {"CPU", "GPU", "NPU"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.device not in PHYSICAL_DEVICES:
        parser.error("device must be exactly CPU, GPU, or NPU; meta-devices are forbidden")

    core = ov.Core()
    payload = {
        "schema": "heterospec.358h.canonical_gguf_smoke.v1",
        "formal_measurement": False,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": str(args.model.resolve()),
        "model_sha256": hashlib.sha256(args.model.read_bytes()).hexdigest(),
        "requested_device": args.device,
        "available_devices": list(core.available_devices),
        "openvino": ov.get_version(),
        "openvino_genai": getattr(ov_genai, "__version__", "unknown"),
        "python": platform.python_version(),
        "status": "FAIL",
        "actual_execution_devices": None,
        "actual_execution_devices_status": (
            "UNAVAILABLE_FROM_LLMPipeline_GGUF_PYTHON_API; explicit physical plugin request alone "
            "does not satisfy the independent EXECUTION_DEVICES evidence gate"
        ),
    }
    try:
        pipe = ov_genai.LLMPipeline(str(args.model), args.device, PERFORMANCE_HINT="LATENCY")
        config = ov_genai.GenerationConfig()
        config.max_new_tokens = 4
        config.min_new_tokens = 4
        config.do_sample = False
        result = pipe.generate("Hello", config)
        if isinstance(result, str):
            payload.update(
                status="PASS_BOUNDED_GENERATION",
                output_text_sha256=hashlib.sha256(result.encode("utf-8")).hexdigest(),
                output_text_bytes=len(result.encode("utf-8")),
            )
        else:
            token_ids = [int(value) for value in result.tokens[0]]
            payload.update(
                status="PASS_BOUNDED_GENERATION",
                generated_token_ids=token_ids,
                generated_token_ids_sha256=hashlib.sha256(
                    ",".join(map(str, token_ids)).encode("ascii")
                ).hexdigest(),
            )
    except Exception as exc:
        payload.update(
            error_type=type(exc).__name__,
            error=str(exc),
            traceback=traceback.format_exc(),
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("requested_device", "status", "actual_execution_devices")}, indent=2))
    return 0 if payload["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
