#!/usr/bin/env python3
"""Non-formal end-to-end dry run for the frozen 358H Phase-1 machinery."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import openvino as ov
import openvino_genai as genai
import psutil

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "models/openvino/qwen3-0.6b-6130ef-int4-sym-g128"
PREREG = ROOT / "benchmarks/358h_threshold_validation/preregistration_v1.json"
GATE = ROOT / "runs/358h/qualification/phase0_gate.json"
EVIDENCE = {
    "CPU": ROOT / "runs/358h/qualification_ac_20260918/environment_cpu.json",
    "NPU": ROOT / "runs/358h/qualification_ac_20260918/npu_cache_binding_ctx8192.json",
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


def power_scheme() -> tuple[str, bool]:
    completed = subprocess.run(["powercfg", "/GETACTIVESCHEME"], capture_output=True, check=True)
    raw = completed.stdout
    text = raw.decode("utf-8", errors="replace")
    return text.strip(), b"381b4222-f694-41f0-9685-ff5bb260df2e" in raw.lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--expect-formal-ready", choices=["yes", "no"], required=True)
    args = parser.parse_args()
    out = args.output_directory.resolve()
    out.mkdir(parents=True, exist_ok=False)
    prereg = json.loads(PREREG.read_text(encoding="utf-8-sig"))
    gate = json.loads(GATE.read_text(encoding="utf-8-sig"))
    expected = prereg["models"]["draft_runtime"]
    checks: dict[str, bool] = {
        "preregistration_parses": prereg["schema"].endswith("preregistration.v1"),
        "phase0_gate_parses": gate.get("schema_version") >= 5,
        "ir_xml_hash": digest(MODEL / "openvino_model.xml") == expected["xml_sha256"],
        "ir_bin_hash": digest(MODEL / "openvino_model.bin") == expected["bin_sha256"],
    }
    battery = psutil.sensors_battery()
    power_scheme_text, balanced = power_scheme()
    checks["external_power"] = battery is not None and battery.power_plugged is True
    checks["balanced_scheme"] = balanced

    core = ov.Core()
    tokenizer = genai.Tokenizer(MODEL)
    prompt = tokenizer.encode("HeteroSpec non-formal dry run.", add_special_tokens=False)
    config = genai.GenerationConfig()
    config.do_sample = False
    config.max_new_tokens = 4
    config.min_new_tokens = 4
    config.ignore_eos = True
    config.apply_chat_template = False
    device_records = {}
    for device in ("CPU", "NPU"):
        checks[f"{device.lower()}_available"] = device in core.available_devices
        binding = json.loads(EVIDENCE[device].read_text(encoding="utf-8-sig"))
        checks[f"{device.lower()}_binding_evidence"] = (
            (device == "CPU" and binding["devices"]["CPU"]["model_probe"]["execution_devices"] == ["CPU"])
            or (device == "NPU" and binding.get("actual_execution_devices", "").upper() == "NPU")
        )
        properties = {"PERFORMANCE_HINT": "LATENCY"}
        if device == "NPU":
            properties = {
                "MAX_PROMPT_LEN": 8192,
                "MIN_RESPONSE_LEN": 128,
                "PREFILL_HINT": "DYNAMIC",
                "GENERATE_HINT": "FAST_COMPILE",
                "CACHE_DIR": str((ROOT / "runs/358h/qualification_ac_20260918/npu_cache_ctx8192").resolve()),
            }
        pipe = genai.LLMPipeline(str(MODEL), device, properties)
        result = pipe.generate(prompt, config)
        tokens = [int(value) for value in result.tokens[0]]
        checks[f"{device.lower()}_functional_smoke"] = len(tokens) == 4
        device_record = {
            "schema": "heterospec.358h.preformal_device_smoke.v1",
            "formal_measurement": False,
            "performance_claim_prohibited": True,
            "requested_device": device,
            "binding_evidence": str(EVIDENCE[device].relative_to(ROOT)),
            "generated_token_count": len(tokens),
            "generated_token_ids_sha256": hashlib.sha256(json.dumps(tokens).encode()).hexdigest(),
            "completed_at": now(),
        }
        path = out / f"{device.lower()}-smoke.json"
        path.write_text(json.dumps(device_record, indent=2) + "\n", encoding="utf-8")
        device_records[device] = path

    readiness = subprocess.run(
        [sys.executable, str(ROOT / "scripts/platform/358h/run_phase1_draft_characterization.py"), "--check"],
        text=True,
        capture_output=True,
    )
    expected_code = 0 if args.expect_formal_ready == "yes" else 2
    checks["formal_runner_fail_closed_state"] = readiness.returncode == expected_code
    go = json.loads((ROOT / "runs/358h/dry_run/phase2_gate_go.json").read_text(encoding="utf-8"))
    no_go = json.loads((ROOT / "runs/358h/dry_run/phase2_gate_nogo.json").read_text(encoding="utf-8"))
    checks["phase2_gate_positive_fixture"] = go["overall_classification"] == "GO"
    checks["phase2_gate_negative_fixture"] = no_go["overall_classification"] == "NO-GO"

    artifacts = []
    for path in [*device_records.values(), PREREG, GATE]:
        artifacts.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": digest(path)})
    manifest = {
        "schema": "heterospec.358h.preformal_dry_run.v1",
        "formal_measurement": False,
        "performance_claim_prohibited": True,
        "started_and_completed_on_ac": checks["external_power"],
        "completed_at": now(),
        "python": platform.python_version(),
        "openvino": ov.get_version(),
        "checks": checks,
        "qualification_pass": all(checks.values()),
        "formal_runner_check": {"expected": args.expect_formal_ready, "returncode": readiness.returncode, "stdout": readiness.stdout.strip(), "stderr": readiness.stderr.strip()},
        "failure_recovery": "Incomplete session directories remain non-formal and immutable; restart with a new session ID after resolving the recorded failed check. Never append to or overwrite a completed formal session.",
        "artifacts": artifacts,
    }
    path = out / "dry_run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0 if manifest["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

