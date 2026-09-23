#!/usr/bin/env python3
"""Derive R1 correctness-qualification groups from R0 feasibility only.

This planner deliberately consumes no timing fields. It converts the descriptive
R0 capability/state outputs into process-separated candidate groups so later
qualification does not depend on manual path selection or observed speed.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def exact_optimum_binding(cap: dict[str, Any], device: str) -> bool:
    row = cap.get("optimum", {}).get(device, {})
    return row.get("load_status") == "PASS" and row.get("execution_devices") == [device]


def device_available(cap: dict[str, Any], device: str) -> bool:
    return device in set(cap.get("available_devices", []))


def persistent_pass(state: dict[str, Any], device: str) -> bool:
    return bool(state.get("draft", {}).get(device, {}).get("pass"))


def target_ub2_pass(state: dict[str, Any]) -> bool:
    return bool(state.get("target", {}).get("UB2", {}).get("pass"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--r0-capability", type=Path, required=True)
    ap.add_argument("--r0-state-tests", type=Path, required=True)
    ap.add_argument("--r0-process-isolation", type=Path, required=True)
    ap.add_argument("--r0-status", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    cap = json.loads(args.r0_capability.read_text(encoding="utf-8"))
    state = json.loads(args.r0_state_tests.read_text(encoding="utf-8"))
    process = json.loads(args.r0_process_isolation.read_text(encoding="utf-8"))
    status = json.loads(args.r0_status.read_text(encoding="utf-8"))
    if cap.get("formal") is not False or state.get("formal") is not False:
        raise RuntimeError("planner inputs must be explicitly non-formal R0 artifacts")
    if (status.get("status") != "R0_V02_PASS" or status.get("formal_data_seen") is not False
            or status.get("process_checks_pass") is not True
            or process.get("multi_worker", {}).get("status") != "PASS"):
        raise RuntimeError("planner requires passing v0.2 process-isolated R0 evidence")

    groups: dict[str, list[str]] = {}
    reasons: dict[str, Any] = {}

    cpu: list[str] = []
    if device_available(cap, "CPU") and state.get("draft", {}).get("legacy_cpu", {}).get("status") == "AVAILABLE_R0":
        cpu.append("LEGACY_CPU_UB1")
        reasons["LEGACY_CPU_UB1"] = "CPU available; frozen legacy constructor revalidates binding"
    if exact_optimum_binding(cap, "CPU") and state.get("draft", {}).get("CPU", {}).get("replay_repeat_exact") is True:
        cpu.append("OPTIMUM_REPLAY_CPU_UB1")
        reasons["OPTIMUM_REPLAY_CPU_UB1"] = "R0 Optimum execution_devices == ['CPU']"
        if persistent_pass(state, "CPU"):
            cpu.append("PERSIST_CPU_UB1")
            reasons["PERSIST_CPU_UB1"] = "R0 CPU forced persistent/reconcile state test passed"
        else:
            reasons["PERSIST_CPU_UB1"] = "BLOCKED_FROM_R1: R0 CPU persistent state test unavailable/failed"
    else:
        reasons["OPTIMUM_REPLAY_CPU_UB1"] = "BLOCKED_FROM_R1: exact Optimum CPU binding unavailable"
        reasons["PERSIST_CPU_UB1"] = "BLOCKED_FROM_R1: same-frontend Optimum CPU control unavailable"
    if cpu:
        groups["cpu_ub1"] = cpu

    npu_legacy: list[str] = []
    npu_present = device_available(cap, "NPU")
    if npu_present and state.get("draft", {}).get("legacy_npu", {}).get("status") == "AVAILABLE_R0":
        npu_legacy.append("LEGACY_NPU_UB1")
        reasons["LEGACY_NPU_UB1"] = "NPU available; frozen GenAI constructor revalidates closed static-profile binding"
        if target_ub2_pass(state):
            npu_legacy.extend(["TARGET_UB2", "LEGACY_NPU_UB2"])
            reasons["TARGET_UB2"] = "R0 target UB2 forced state test passed"
            reasons["LEGACY_NPU_UB2"] = "predeclared NPU target-path fallback candidate; TARGET_UB2 R0 gate passed"
        else:
            reasons["TARGET_UB2"] = "BLOCKED_FROM_R1: R0 target UB2 state test failed/unavailable"
            reasons["LEGACY_NPU_UB2"] = "BLOCKED_FROM_R1: TARGET_UB2 R0 gate failed"
    else:
        reasons["LEGACY_NPU_UB1"] = "BLOCKED_FROM_R1: NPU not listed by OpenVINO Core"
        reasons["TARGET_UB2"] = "not scheduled in NPU group because NPU target-path study cannot be formed"
        reasons["LEGACY_NPU_UB2"] = "BLOCKED_FROM_R1: NPU unavailable"
    if npu_legacy:
        groups["npu_legacy_target"] = npu_legacy

    npu_state: list[str] = []
    if npu_present and exact_optimum_binding(cap, "NPU"):
        npu_state.append("OPTIMUM_REPLAY_NPU_UB1")
        reasons["OPTIMUM_REPLAY_NPU_UB1"] = "R0 Optimum execution_devices == ['NPU']"
        if persistent_pass(state, "NPU"):
            npu_state.append("PERSIST_NPU_UB1")
            reasons["PERSIST_NPU_UB1"] = "R0 NPU forced persistent/reconcile state test passed"
            if target_ub2_pass(state):
                npu_state.append("PERSIST_NPU_UB2")
                reasons["PERSIST_NPU_UB2"] = "R0 NPU persistence and target UB2 gates both passed"
            else:
                reasons["PERSIST_NPU_UB2"] = "BLOCKED_FROM_R1: TARGET_UB2 R0 gate failed"
        else:
            reasons["PERSIST_NPU_UB1"] = "BLOCKED_FROM_R1: R0 NPU persistent state test unavailable/failed"
            reasons["PERSIST_NPU_UB2"] = "BLOCKED_FROM_R1: NPU persistence unavailable/failed"
    else:
        reasons["OPTIMUM_REPLAY_NPU_UB1"] = "BLOCKED_FROM_R1: exact Optimum NPU binding unavailable"
        reasons["PERSIST_NPU_UB1"] = "BLOCKED_FROM_R1: same-frontend Optimum NPU control unavailable"
        reasons["PERSIST_NPU_UB2"] = "BLOCKED_FROM_R1: same-frontend Optimum NPU control unavailable"
    if npu_state:
        groups["npu_state"] = npu_state

    all_paths = [path for group in groups.values() for path in group]
    if len(all_paths) != len(set(all_paths)):
        raise AssertionError(f"planner emitted duplicate paths across process groups: {all_paths}")

    out = {
        "schema": "heterospec.358h.runtime.r1_plan.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "formal": False,
        "selection_uses_timing": False,
        "inputs": {
            "r0_capability": str(args.r0_capability),
            "r0_state_tests": str(args.r0_state_tests),
            "r0_process_isolation": str(args.r0_process_isolation),
            "r0_status": str(args.r0_status),
            "source_commit": status["source_commit"],
        },
        "groups": groups,
        "path_reasons": reasons,
        "rules": [
            "R1 candidate membership is a pure function of R0 feasibility/binding/state outcomes",
            "do not manually add candidates after inspecting R0 or R1 timing",
            "small-gate survivors alone may proceed to the corresponding full gate",
            "TARGET_UB1 is automatically supplied by the R1 driver and is not repeated in groups"
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"groups": groups, "selection_uses_timing": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
