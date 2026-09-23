#!/usr/bin/env python3
"""R0-only OpenVINO/Optimum state capability probe.

This script is NON-FORMAL.  It is intentionally descriptive: it inventories the
frozen draft IR, attempts explicit device compilation, and reports whether the
frontend exposes explicit past-key-value tensors or OpenVINO VariableState.
It must not be used as a latency benchmark.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import openvino as ov

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LEGACY_DIR = ROOT / "scripts" / "platform" / "358h"
if str(LEGACY_DIR) not in sys.path:
    sys.path.insert(0, str(LEGACY_DIR))

from phase3_heterogeneous_runner import DRAFT_IR, EXPECTED  # noqa: E402


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def port_record(port) -> dict[str, Any]:
    try:
        names = sorted(port.names)
    except Exception:
        names = []
    try:
        any_name = port.any_name
    except Exception:
        any_name = names[0] if names else "<unnamed>"
    try:
        pshape = str(port.partial_shape)
    except Exception:
        pshape = "<unknown>"
    try:
        et = str(port.element_type)
    except Exception:
        et = "<unknown>"
    return {"any_name": any_name, "names": names, "partial_shape": pshape, "element_type": et}


def variable_state_record(state) -> dict[str, Any]:
    rec: dict[str, Any] = {}
    try:
        rec["name"] = state.name
    except Exception:
        try:
            rec["name"] = state.get_name()
        except Exception:
            rec["name"] = "<unknown>"
    try:
        tensor = state.state
    except Exception:
        try:
            tensor = state.get_state()
        except Exception as exc:
            rec["state_read_error"] = repr(exc)
            return rec
    try:
        rec["shape"] = list(tensor.shape)
    except Exception:
        rec["shape"] = None
    try:
        rec["element_type"] = str(tensor.element_type)
    except Exception:
        rec["element_type"] = None
    try:
        rec["byte_size"] = int(tensor.byte_size)
    except Exception:
        rec["byte_size"] = None
    return rec


def raw_openvino_probe(device: str) -> dict[str, Any]:
    core = ov.Core()
    xml = DRAFT_IR / "openvino_model.xml"
    model = core.read_model(str(xml))
    rec: dict[str, Any] = {
        "device": device,
        "model_inputs": [port_record(x) for x in model.inputs],
        "model_outputs": [port_record(x) for x in model.outputs],
        "compile_status": "NOT_ATTEMPTED",
    }
    kv_inputs = [x for x in rec["model_inputs"] if "past" in x["any_name"].lower() or "key_values" in x["any_name"].lower()]
    kv_outputs = [x for x in rec["model_outputs"] if "present" in x["any_name"].lower() or "key_values" in x["any_name"].lower()]
    rec["explicit_kv_input_count"] = len(kv_inputs)
    rec["explicit_kv_output_count"] = len(kv_outputs)
    try:
        compiled = core.compile_model(model, device, {"PERFORMANCE_HINT": "LATENCY"})
        request = compiled.create_infer_request()
        rec["compile_status"] = "PASS"
        try:
            actual = compiled.get_property("EXECUTION_DEVICES")
            rec["execution_devices"] = list(actual) if not isinstance(actual, str) else [actual]
        except Exception as exc:
            rec["execution_devices_error"] = repr(exc)
        try:
            states = request.query_state()
            rec["variable_state_count"] = len(states)
            rec["variable_states"] = [variable_state_record(x) for x in states]
        except Exception as exc:
            rec["variable_state_query_error"] = repr(exc)
    except Exception as exc:
        rec["compile_status"] = "FAIL"
        rec["compile_error"] = repr(exc)
    return rec


def optimum_probe(device: str) -> dict[str, Any]:
    rec: dict[str, Any] = {"device": device, "load_status": "NOT_ATTEMPTED"}
    try:
        from optimum.intel.openvino import OVModelForCausalLM
        import optimum.intel

        rec["optimum_intel_version"] = getattr(optimum.intel, "__version__", "unknown")
        kwargs: dict[str, Any] = {"device": device, "compile": True}
        model = OVModelForCausalLM.from_pretrained(str(DRAFT_IR), **kwargs)
        model.compile()
        rec["load_status"] = "PASS"
        rec["stateful"] = bool(getattr(model, "stateful", False))
        rec["use_cache"] = bool(getattr(model, "use_cache", False))
        rec["input_names"] = list(getattr(model, "input_names", []))
        rec["output_names"] = list(getattr(model, "output_names", []))
        rec["key_value_input_names"] = list(getattr(model, "key_value_input_names", []))
        rec["key_value_output_names"] = list(getattr(model, "key_value_output_names", []))
        request = getattr(model, "request", None)
        if request is not None:
            try:
                compiled = request.get_compiled_model()
                actual = compiled.get_property("EXECUTION_DEVICES")
                rec["execution_devices"] = list(actual) if not isinstance(actual, str) else [actual]
            except Exception as exc:
                rec["execution_devices_error"] = repr(exc)
            try:
                states = request.query_state()
                rec["variable_state_count"] = len(states)
                rec["variable_states"] = [variable_state_record(x) for x in states]
            except Exception as exc:
                rec["variable_state_query_error"] = repr(exc)
    except Exception as exc:
        rec["load_status"] = "FAIL"
        rec["load_error"] = repr(exc)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--devices", nargs="+", choices=["CPU", "NPU"], default=["CPU", "NPU"])
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    for path, expected in EXPECTED.items():
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(f"frozen artifact hash mismatch: {path}: {actual} != {expected}")

    core = ov.Core()
    report: dict[str, Any] = {
        "schema": "heterospec.358h.runtime.r0_state_capability.v0",
        "formal": False,
        "claim_status": "NON_FORMAL / INVALID_FOR_PERFORMANCE_CLAIMS",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "openvino": ov.get_version(),
        "available_devices": core.available_devices,
        "draft_ir": str(DRAFT_IR),
        "raw_openvino": {},
        "optimum": {},
        "interpretation": {
            "explicit_pkv": "preferred if the frontend exposes past/present KV tensors that can be retained without full-prefix replay",
            "variable_state": "potentially usable only if snapshot/restore/reconcile can be proven exact and all transfer cost is charged",
            "genai_chat": "not sufficient by itself because the public chat API does not establish arbitrary partial rollback/reconcile semantics",
        },
    }
    for device in args.devices:
        report["raw_openvino"][device] = raw_openvino_probe(device)
        report["optimum"][device] = optimum_probe(device)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "devices": args.devices}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
