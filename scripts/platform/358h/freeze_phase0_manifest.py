#!/usr/bin/env python3
"""Freeze the complete non-performance 358H Phase-0 qualification manifest."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
Q = ROOT / "runs" / "358h" / "qualification"
SOURCE = ROOT / "models" / "src-6130ef"
IR = ROOT / "models" / "openvino" / "qwen3-0.6b-6130ef-int4-sym-g128"
GGUF = ROOT / "models" / "gguf" / "Qwen3-0.6B-Q8_0.gguf"


def load(name: str) -> dict:
    return json.loads((Q / name).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def files(root: Path) -> list[dict]:
    return [
        {
            "path": str(path.resolve()),
            "relative_path": str(path.relative_to(root)).replace("\\", "/"),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file() and ".cache" not in item.parts)
    ]


def main() -> int:
    equivalence = load("reconstructed_source_equivalence.json")
    low_level = load("environment_with_openvino_ir.json")
    smoke_cpu = load("openvino_ir_smoke_cpu.json")
    smoke_gpu = load("openvino_ir_smoke_gpu.json")
    smoke_npu = load("openvino_ir_smoke_npu.json")
    smoke_npu_8192 = load("openvino_ir_smoke_npu_ctx8192.json")
    npu_binding = load("npu_cache_binding.json")
    npu_binding_8192 = load("npu_cache_binding_ctx8192.json")
    export = load("openvino_export_attempt.json")
    overlay = load("canonical_chat_template_overlay.json")

    cpu_exec = low_level["devices"]["CPU"]["model_probe"]["execution_devices"]
    gpu_exec = low_level["devices"]["GPU"]["model_probe"]["execution_devices"]
    checks = {
        "canonical_gguf_hash": sha256(GGUF) == "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031",
        "reconstructed_source_immutable_and_hashed": sha256(SOURCE / "model.safetensors") == "f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b",
        "source_equivalence": equivalence["classification"] == "STRONGLY_SUPPORTED",
        "conversion_succeeded": export["returncode"] == 0,
        "canonical_chat_template_applied": overlay["after_matches_canonical"],
        "cpu_binding": any(str(item).upper().startswith("CPU") for item in cpu_exec),
        "gpu_binding": any(str(item).upper().startswith("GPU") for item in gpu_exec),
        "npu_binding": npu_binding["qualification_pass"] and npu_binding["actual_execution_devices"] == "NPU",
        "npu_8192_binding": npu_binding_8192["qualification_pass"] and npu_binding_8192["actual_execution_devices"] == "NPU",
        "cpu_smoke": smoke_cpu["status"] == "PASS_BOUNDED_GENERATION",
        "gpu_smoke": smoke_gpu["status"] == "PASS_BOUNDED_GENERATION",
        "npu_smoke": smoke_npu["status"] == "PASS_BOUNDED_GENERATION",
        "npu_8192_shape_smoke": smoke_npu_8192["status"] == "PASS_BOUNDED_GENERATION" and smoke_npu_8192["input_token_count"] == 8192,
        "no_formal_measurement": all(
            item.get("formal_measurement") is False
            for item in [equivalence, low_level, smoke_cpu, smoke_gpu, smoke_npu, smoke_npu_8192, npu_binding, npu_binding_8192, export, overlay]
        ),
    }
    payload = {
        "schema": "heterospec.358h.phase0_frozen_manifest.v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "formal_measurement": False,
        "historical_provenance": {
            "exact_upstream_revision_recovered": False,
            "limitation_handling": "reports/358h/358H_PROVENANCE_AMENDMENT.md",
            "canonical_gguf": {
                "repository": "Qwen/Qwen3-0.6B-GGUF",
                "revision": "23749fefcc72300e3a2ad315e1317431b06b590a",
                "file": str(GGUF.resolve()),
                "bytes": GGUF.stat().st_size,
                "sha256": sha256(GGUF),
            },
        },
        "reconstructed_source": {
            "repository": "Qwen/Qwen3-0.6B",
            "revision": "6130ef31402718485ca4d80a6234f70d9a4cf362",
            "classification": equivalence["classification"],
            "files": files(SOURCE),
        },
        "conversion": {
            "record": "runs/358h/qualification/openvino_export_attempt.json",
            "command": export["command"],
            "settings": export["conversion"],
            "packages": export["packages"],
            "canonical_chat_template_overlay": overlay,
        },
        "openvino_representation": {
            "directory": str(IR.resolve()),
            "files": files(IR),
            "common_ir_for_cpu_gpu_npu": True,
            "npu_runtime_shape_policy": {
                "pipeline": "OpenVINO GenAI documented NPU static/dynamic preparation",
                "bounded_static_smoke_max_prompt": 128,
                "formal_context_ceiling_qualified": 8192,
                "formal_context_ceiling_prefill_hint": "DYNAMIC",
                "prefill_chunk_default": 1024,
            },
        },
        "device_binding": {
            "CPU": {"requested": "CPU", "actual_execution_devices": cpu_exec, "smoke": smoke_cpu["status"]},
            "GPU": {"requested": "GPU", "actual_execution_devices": gpu_exec, "smoke": smoke_gpu["status"]},
            "NPU": {
                "requested": "NPU",
                "actual_execution_devices": npu_binding["actual_execution_devices"],
                "smoke": smoke_npu["status"],
                "context_8192_smoke": smoke_npu_8192["status"],
                "context_8192_binding": npu_binding_8192["actual_execution_devices"],
            },
            "meta_devices_forbidden": ["AUTO", "MULTI", "HETERO"],
        },
        "failed_attempts_preserved": [
            "runs/358h/qualification/canonical_gguf_smoke_npu.json",
            "runs/358h/qualification/environment_with_openvino_ir.json",
        ],
        "checks": checks,
        "qualification_pass": all(checks.values()),
        "phase1_formal_measurement_authorized": False,
        "phase1_authorization_condition": "Completed preregistration must be frozen and committed after this Phase-0 PASS.",
    }
    output = Q / "phase0_frozen_manifest.json"
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"qualification_pass": payload["qualification_pass"], "checks": checks, "output": str(output)}, indent=2))
    return 0 if payload["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
