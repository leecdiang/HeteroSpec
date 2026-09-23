#!/usr/bin/env python3
"""Build the frozen R2 path registry from R0 feasibility and R1 exactness only.

This script deliberately never reads R1 timing fields. Formal condition selection
is therefore a pure function of predeclared path scope, implementation feasibility
and correctness qualification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_summaries(paths: list[Path], expected_stage: str) -> tuple[dict[str, dict], list[dict]]:
    merged: dict[str, dict] = {}
    provenance = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        status_path = path.parent / "R1_STATUS.json"
        status = json.loads(status_path.read_text(encoding="utf-8"))
        if status.get("stage") != expected_stage or not status.get("complete"):
            raise RuntimeError(f"{path}: expected complete R1 {expected_stage} status")
        if status.get("timing_used_for_promotion") is not False:
            raise RuntimeError(f"{path}: R1 does not prove timing-independent qualification")
        for name, row in data.items():
            if name == "TARGET_UB1":
                continue
            if name in merged:
                raise RuntimeError(f"duplicate path across {expected_stage} summaries: {name}")
            merged[name] = row
        provenance.append({
            "summary": str(path),
            "summary_sha256": sha256(path),
            "status": str(status_path),
            "status_sha256": sha256(status_path),
        })
    return merged, provenance


def r1_qualified(table: dict[str, dict], name: str) -> bool:
    row = table.get(name)
    return bool(row and row.get("status") == "QUALIFIED")


def exact_device_binding(cap: dict[str, Any], device: str) -> tuple[bool, str]:
    row = cap.get("optimum", {}).get(device, {})
    if row.get("load_status") != "PASS":
        return False, f"Optimum {device} load_status={row.get('load_status', 'MISSING')}"
    actual = row.get("execution_devices")
    if actual != [device]:
        return False, f"Optimum {device} execution_devices={actual!r}"
    return True, "PASS"


def r0_gate(name: str, state: dict[str, Any], cap: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    ok = True

    ub2 = name.endswith("_UB2") or name == "TARGET_UB2"
    if ub2:
        target_ok = bool(state.get("target", {}).get("UB2", {}).get("pass"))
        if not target_ok:
            ok = False
            reasons.append("R0 TARGET_UB2 state test failed or missing")

    if name.startswith("OPTIMUM_REPLAY_") or name.startswith("PERSIST_"):
        device = "NPU" if "_NPU_" in name else "CPU"
        bind_ok, why = exact_device_binding(cap, device)
        if not bind_ok:
            ok = False
            reasons.append(why)

    if name.startswith("PERSIST_"):
        device = "NPU" if "_NPU_" in name else "CPU"
        state_ok = bool(state.get("draft", {}).get(device, {}).get("pass"))
        if not state_ok:
            ok = False
            reasons.append(f"R0 persistent {device} forced state test failed or unavailable")

    # Legacy replay binding is revalidated by the frozen LLMPipeline constructor
    # itself in R1/R2; the NPU path uses the closed cache-binding evidence.
    if not reasons:
        reasons.append("PASS")
    return ok, reasons


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--small", nargs="+", type=Path, required=True, help="small-gate qualification_summary.json files")
    ap.add_argument("--full", nargs="+", type=Path, required=True, help="full-gate qualification_summary.json files")
    ap.add_argument("--r0-state-tests", type=Path, required=True)
    ap.add_argument("--r0-capability", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    r0_state = json.loads(args.r0_state_tests.read_text(encoding="utf-8"))
    r0_cap = json.loads(args.r0_capability.read_text(encoding="utf-8"))
    if r0_state.get("formal") is not False or r0_cap.get("formal") is not False:
        raise RuntimeError("R0 inputs must be explicitly non-formal")

    small, small_prov = load_summaries(args.small, "small")
    full, full_prov = load_summaries(args.full, "full")
    names = sorted(set(small) | set(full))
    registry: dict[str, Any] = {}
    for name in names:
        small_ok = r1_qualified(small, name)
        full_ok = r1_qualified(full, name)
        feasibility_ok, feasibility_reasons = r0_gate(name, r0_state, r0_cap)
        qualified = small_ok and full_ok and feasibility_ok
        registry[name] = {
            "r0_feasibility": "PASS" if feasibility_ok else "FAIL",
            "r0_notes": feasibility_reasons,
            "small_gate": "PASS" if small_ok else "FAIL_OR_MISSING",
            "full_gate": "PASS" if full_ok else "FAIL_OR_MISSING",
            "status": "QUALIFIED" if qualified else "BLOCKED",
            "formal_performance_allowed": bool(qualified),
        }

    # Formal scope is fixed and depends only on feasibility/exactness. Keep the
    # UB1 controls needed to identify frontend and persistence effects whenever
    # they qualify. Missing paths are retained as blocked registry entries.
    formal = ["TARGET_UB1"]
    for name in [
        "LEGACY_CPU_UB1",
        "OPTIMUM_REPLAY_CPU_UB1",
        "PERSIST_CPU_UB1",
        "LEGACY_NPU_UB1",
        "OPTIMUM_REPLAY_NPU_UB1",
        "PERSIST_NPU_UB1",
    ]:
        if registry.get(name, {}).get("status") == "QUALIFIED":
            formal.append(name)

    # TARGET_UB2 is a correctness gate, not a formal target-only timing condition:
    # target-only decoding submits one token per llama_decode and therefore does
    # not exercise a two-token verification microbatch. The target-path effect is
    # estimated by comparing the same speculative state policy at UB1 vs UB2.
    target_ub2_ok = registry.get("TARGET_UB2", {}).get("status") == "QUALIFIED"
    persist_pair_ok = (
        target_ub2_ok
        and registry.get("PERSIST_NPU_UB1", {}).get("status") == "QUALIFIED"
        and registry.get("PERSIST_NPU_UB2", {}).get("status") == "QUALIFIED"
    )
    legacy_pair_ok = (
        target_ub2_ok
        and registry.get("LEGACY_NPU_UB1", {}).get("status") == "QUALIFIED"
        and registry.get("LEGACY_NPU_UB2", {}).get("status") == "QUALIFIED"
    )
    if persist_pair_ok:
        formal.append("PERSIST_NPU_UB2")
        ub2_rule = "state-policy-matched PERSIST_NPU UB1/UB2 pair promoted"
    elif legacy_pair_ok:
        formal.append("LEGACY_NPU_UB2")
        ub2_rule = "persistent NPU UB2 unavailable/blocked; state-policy-matched LEGACY_NPU UB1/UB2 pair promoted"
    else:
        ub2_rule = "no correctness-qualified state-policy-matched NPU UB1/UB2 pair; no UB2 formal timing"

    out = {
        "schema": "heterospec.358h.runtime.qualification_registry.v1",
        "status": "FROZEN_FOR_R2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_uses_performance_timing": False,
        "registry": registry,
        "formal_conditions": formal,
        "target_ub2_role": "correctness gate only; not a target-only performance condition",
        "ub2_selection_rule_result": ub2_rule,
        "r0": {
            "state_tests": str(args.r0_state_tests),
            "state_tests_sha256": sha256(args.r0_state_tests),
            "capability": str(args.r0_capability),
            "capability_sha256": sha256(args.r0_capability),
        },
        "r1_small": small_prov,
        "r1_full": full_prov,
        "interpretation": {
            "blocked": "diagnostic only; never timed for an admissible R2 speed claim",
            "missing": "not silently substituted by another device/frontend",
            "ub2": "must have R0 target state pass, R1 TARGET_UB2 exactness, and a jointly qualified same-policy NPU UB1/UB2 pair",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"formal_conditions": formal, "ub2": ub2_rule}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
