#!/usr/bin/env python3
"""Build the frozen R2 path registry from R1 exactness outcomes only.

This script deliberately never reads R1 timing fields. Formal condition selection
is therefore a pure function of feasibility/exactness and the predeclared scope.
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


def is_qualified(table: dict[str, dict], name: str) -> bool:
    row = table.get(name)
    return bool(row and row.get("status") == "QUALIFIED")


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
        small_ok = is_qualified(small, name)
        full_ok = is_qualified(full, name)
        registry[name] = {
            "small_gate": "PASS" if small_ok else "FAIL_OR_MISSING",
            "full_gate": "PASS" if full_ok else "FAIL_OR_MISSING",
            "status": "QUALIFIED" if small_ok and full_ok else "BLOCKED",
            "formal_performance_allowed": bool(small_ok and full_ok),
        }

    # Formal scope is fixed here and depends only on exactness/feasibility.
    # UB2 is evaluated on the NPU branch because the state-interface diagnosis is
    # the runtime study's primary intervention target. CPU persistent UB1 remains
    # a negative/control path for the 'draft cost alone may not suffice' question.
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

    if registry.get("PERSIST_NPU_UB2", {}).get("status") == "QUALIFIED":
        formal.append("PERSIST_NPU_UB2")
        ub2_rule = "PERSIST_NPU_UB2 promoted"
    elif registry.get("LEGACY_NPU_UB2", {}).get("status") == "QUALIFIED":
        formal.append("LEGACY_NPU_UB2")
        ub2_rule = "persistent NPU UB2 unavailable/blocked; qualified legacy NPU UB2 target-path fallback promoted"
    else:
        ub2_rule = "no NPU UB2 path qualified; no UB2 formal timing"

    out = {
        "schema": "heterospec.358h.runtime.qualification_registry.v0",
        "status": "FROZEN_FOR_R2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_uses_performance_timing": False,
        "registry": registry,
        "formal_conditions": formal,
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
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"formal_conditions": formal, "ub2": ub2_rule}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
