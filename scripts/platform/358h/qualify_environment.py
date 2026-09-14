#!/usr/bin/env python3
"""Capture a non-formal 358H/OpenVINO qualification record.

This script never uses AUTO, MULTI, or HETERO.  With --model-xml it also
queries and compiles the exact IR on every requested physical device.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FORBIDDEN_PREFIXES = ("AUTO", "MULTI", "HETERO")


def jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    return str(value)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_value(*args: str) -> str | None:
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def safe_property(core: Any, device: str, key: str) -> Any:
    try:
        return jsonable(core.get_property(device, key))
    except Exception as exc:  # device plugins expose different property sets
        return {"error": f"{type(exc).__name__}: {exc}"}


def safe_compiled_property(compiled: Any, key: str) -> Any:
    try:
        return jsonable(compiled.get_property(key))
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-xml", type=Path)
    parser.add_argument("--devices", nargs="+", default=["CPU", "GPU", "NPU"])
    args = parser.parse_args()

    bad = [d for d in args.devices if d.upper().startswith(FORBIDDEN_PREFIXES)]
    if bad:
        parser.error(f"meta-devices are forbidden for qualification: {bad}")

    try:
        import openvino as ov
    except ImportError as exc:
        raise SystemExit("OpenVINO is not installed; run setup_358h.ps1 first") from exc

    core = ov.Core()
    available = list(core.available_devices)
    report: dict[str, Any] = {
        "schema": "heterospec.358h.environment_qualification.v1",
        "formal_measurement": False,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": {
            "commit": git_value("rev-parse", "HEAD"),
            "branch": git_value("branch", "--show-current"),
            "dirty": bool(git_value("status", "--porcelain")),
        },
        "host": {
            "platform": platform.platform(),
            "python": sys.version,
            "machine": platform.machine(),
            "processor": platform.processor(),
            "windows_release": platform.release(),
            "windows_version": platform.version(),
            "ac_power_and_power_mode": "RECORD_MANUALLY_IN_QUALIFICATION_REPORT",
            "bios_and_driver_inventory": "CAPTURED_SEPARATELY_BY_WINDOWS_COMMANDS",
        },
        "runtime": {"openvino": jsonable(ov.get_version())},
        "requested_devices": args.devices,
        "available_devices": available,
        "devices": {},
        "qualification_pass": False,
        "failures": [],
    }

    model = None
    if args.model_xml:
        if not args.model_xml.is_file():
            parser.error(f"model XML not found: {args.model_xml}")
        model = core.read_model(args.model_xml)
        model_files = [args.model_xml]
        bin_path = args.model_xml.with_suffix(".bin")
        if bin_path.is_file():
            model_files.append(bin_path)
        report["model"] = {
            "xml": str(args.model_xml.resolve()),
            "files": [{"path": str(p.resolve()), "bytes": p.stat().st_size, "sha256": sha256(p)} for p in model_files],
        }

    for requested in args.devices:
        matches = [d for d in available if d == requested or d.startswith(f"{requested}.")]
        entry: dict[str, Any] = {"available_matches": matches, "properties": {}}
        if not matches:
            report["failures"].append(f"requested device unavailable: {requested}")
            report["devices"][requested] = entry
            continue
        exact = matches[0]
        for key in (
            "FULL_DEVICE_NAME", "DEVICE_ARCHITECTURE", "DEVICE_TYPE", "OPTIMIZATION_CAPABILITIES",
            "SUPPORTED_PROPERTIES", "EXECUTION_DEVICES", "NPU_DRIVER_VERSION", "NPU_COMPILER_VERSION",
        ):
            entry["properties"][key] = safe_property(core, exact, key)
        if model is not None:
            try:
                supported = core.query_model(model, exact)
                compiled = core.compile_model(model, exact, {"PERFORMANCE_HINT": "LATENCY"})
                execution_devices = safe_compiled_property(compiled, "EXECUTION_DEVICES")
                entry["model_probe"] = {
                    "query_supported_ops": len(supported),
                    "model_ops": len(model.get_ops()),
                    "compile": "PASS",
                    "execution_devices": execution_devices,
                }
                rendered = json.dumps(execution_devices).upper()
                if requested not in rendered:
                    report["failures"].append(
                        f"compiled {requested} model did not report {requested} in EXECUTION_DEVICES: {execution_devices}"
                    )
            except Exception as exc:
                entry["model_probe"] = {"compile": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
                report["failures"].append(f"model compile failed on {requested}: {exc}")
        report["devices"][requested] = entry

    report["qualification_pass"] = not report["failures"] and model is not None
    if model is None:
        report["failures"].append("device inventory only: rerun with --model-xml before qualification can pass")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "qualification_pass": report["qualification_pass"], "failures": report["failures"]}, indent=2))
    return 0 if report["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
