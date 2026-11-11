#!/usr/bin/env python3
"""Run and record the frozen 358H OpenVINO conversion command."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    args = parser.parse_args()

    command = [
        str(Path(sys.executable).with_name("optimum-cli.exe")),
        "export",
        "openvino",
        "--model",
        str(args.source.resolve()),
        "--task",
        "text-generation-with-past",
        "--weight-format",
        "int4",
        "--sym",
        "--group-size",
        "128",
        "--ratio",
        "1.0",
        str(args.output_dir.resolve()),
    ]
    started = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace")
    payload = {
        "schema": "heterospec.358h.openvino_export_attempt.v1",
        "formal_measurement": False,
        "started_at_utc": started,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_repository": "Qwen/Qwen3-0.6B",
        "source_revision": "6130ef31402718485ca4d80a6234f70d9a4cf362",
        "source_role": "reconstructed_runtime_source_STRONGLY_SUPPORTED",
        "command": command,
        "conversion": {
            "task": "text-generation-with-past",
            "weight_format": "INT4",
            "symmetric": True,
            "group_size": 128,
            "ratio": 1.0,
            "calibration": "data-free",
            "export_shape_policy": "Optimum dynamic IR; OpenVINO GenAI NPU pipeline performs documented static-shape preparation",
        },
        "packages": {
            name: version(name)
            for name in [
                "openvino",
                "openvino-genai",
                "openvino-tokenizers",
                "optimum",
                "optimum-intel",
                "optimum-onnx",
                "transformers",
                "nncf",
                "torch",
                "onnx",
            ]
        },
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    args.record.parent.mkdir(parents=True, exist_ok=True)
    args.record.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"returncode": completed.returncode, "record": str(args.record)}, indent=2))
    if completed.returncode:
        print(completed.stdout[-4000:])
        print(completed.stderr[-4000:], file=sys.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
