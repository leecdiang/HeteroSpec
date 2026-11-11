#!/usr/bin/env python3
"""Import the GenAI-produced NPU cache payload and verify strict NPU binding."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openvino as ov


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-blob", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = args.cache_blob.read_bytes()
    header_end = raw.find(b"\n") + 1
    header_text = raw[:header_end].decode("utf-8")
    match = re.search(r'header_size_alignment="(\d+)"', header_text)
    if not match:
        raise SystemExit("OpenVINO cache header does not declare header_size_alignment")
    payload_offset = int(match.group(1))
    core = ov.Core()
    compiled = core.import_model(
        raw[payload_offset:],
        "NPU",
        {"WEIGHTS_PATH": str(args.weights.resolve())},
    )
    execution_devices = compiled.get_property("EXECUTION_DEVICES")
    infer_request = compiled.create_infer_request()
    outputs = infer_request.infer(
        {
            "input_ids": np.array([[9707]], dtype=np.int64),
            "attention_mask": np.array([[1]], dtype=np.int64),
            "position_ids": np.array([[0]], dtype=np.int64),
            "beam_idx": np.array([0], dtype=np.int32),
        }
    )
    logits = next(iter(outputs.values()))
    top_token_id = int(np.argmax(logits[0, -1]))
    payload = {
        "schema": "heterospec.358h.npu_cache_binding.v1",
        "formal_measurement": False,
        "performance_metrics_recorded": False,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_device": "NPU",
        "available_devices": list(core.available_devices),
        "cache_blob": {
            "path": str(args.cache_blob.resolve()),
            "bytes": args.cache_blob.stat().st_size,
            "sha256": sha256(args.cache_blob),
            "wrapper_header": header_text.strip(),
            "compiled_payload_offset": payload_offset,
            "compiled_payload_sha256": hashlib.sha256(raw[payload_offset:]).hexdigest(),
        },
        "weights": {
            "path": str(args.weights.resolve()),
            "bytes": args.weights.stat().st_size,
            "sha256": sha256(args.weights),
        },
        "actual_execution_devices": execution_devices,
        "actual_execution_devices_match_request": str(execution_devices).upper() == "NPU",
        "loaded_from_cache": compiled.get_property("LOADED_FROM_CACHE"),
        "inputs": [
            {"name": item.any_name, "shape": str(item.partial_shape), "type": str(item.element_type)}
            for item in compiled.inputs
        ],
        "outputs": [
            {"name": item.any_name, "shape": str(item.partial_shape), "type": str(item.element_type)}
            for item in compiled.outputs
        ],
        "bounded_single_step_inference": "PASS",
        "top_token_id": top_token_id,
        "qualification_pass": str(execution_devices).upper() == "NPU" and top_token_id == 220,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "actual_execution_devices": execution_devices,
        "bounded_single_step_inference": "PASS",
        "top_token_id": top_token_id,
        "qualification_pass": payload["qualification_pass"],
    }, indent=2))
    return 0 if payload["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
