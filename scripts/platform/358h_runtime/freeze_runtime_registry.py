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


def load_summaries(paths: list[Path], expected_stage: str) -> tuple[dict[str, dict], list[dict], str, str]:
    merged: dict[str, dict] = {}
    provenance = []
    freeze_sha: str | None = None
    freeze_commit: str | None = None
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        status_path = path.parent / "R1_STATUS.json"
        status = json.loads(status_path.read_text(encoding="utf-8"))
        if status.get("stage") != expected_stage or not status.get("complete"):
            raise RuntimeError(f"{path}: expected complete R1 {expected_stage} status")
        if status.get("timing_used_for_promotion") is not False:
            raise RuntimeError(f"{path}: R1 does not prove timing-independent qualification")
        this_freeze = status.get("freeze_manifest_sha256")
        this_commit = status.get("freeze_source_commit")
        if not this_freeze or not this_commit:
            raise RuntimeError(f"{path}: R1 status lacks freeze provenance")
        if freeze_sha is None:
            freeze_sha, freeze_commit = this_freeze, this_commit
        elif this_freeze != freeze_sha or this_commit != freeze_commit:
            raise RuntimeError(f"{path}: R1 results were produced from different source/environment freezes")
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
            "freeze_manifest_sha256": this_freeze,
            "freeze_source_commit": this_commit,
        })
    assert freeze_sha is not None and freeze_commit is not None
    return merged, provenance, freeze_sha, freeze_commit


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

    if not reasons:
        reasons.append("PASS")
    return ok, reasons


def qualified(registry: dict[str, Any], name: str) -> bool:
    return registry.get(name, {}).get("status") == "QUALIFIED"


def append_once(items: list[str], name: str) -> None:
    if name not in items:
        items.append(name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--small", nargs="+", type=Path, required=True, help="small-gate qualification_summary.json files")
    ap.add_argument("--full", nargs="+", type=Path, required=True, help="full-gate qualification_summary.json files")
    ap.add_argument("--r0-state-tests", type=Path, required=True)
    ap.add_argument("--r0-capability", type=Path, required=True)
    ap.add_argument("--r0-process-isolation", type=Path, required=True)
    ap.add_argument("--r0-status", type=Path, required=True)
    ap.add_argument("--freeze-manifest", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    r0_state = json.loads(args.r0_state_tests.read_text(encoding="utf-8"))
    r0_cap = json.loads(args.r0_capability.read_text(encoding="utf-8"))
    r0_status = json.loads(args.r0_status.read_text(encoding="utf-8"))
    r0_process = json.loads(args.r0_process_isolation.read_text(encoding="utf-8"))
    freeze = json.loads(args.freeze_manifest.read_text(encoding="utf-8"))
    if r0_state.get("formal") is not False or r0_cap.get("formal") is not False:
        raise RuntimeError("R0 inputs must be explicitly non-formal")
    if (r0_status.get("status") != "R0_V02_PASS" or r0_process.get("multi_worker", {}).get("status") != "PASS"
            or r0_status.get("source_commit") != freeze.get("source_commit")):
        raise RuntimeError("registry R0 provenance does not match passing final v0.2 R0")
    for key, path in (("capability", args.r0_capability), ("state_tests", args.r0_state_tests),
                      ("process_isolation", args.r0_process_isolation), ("status", args.r0_status)):
        if freeze.get("r0", {}).get(key + "_sha256") != sha256(path):
            raise RuntimeError(f"registry R0 {key} differs from source freeze")

    small, small_prov, small_freeze, small_commit = load_summaries(args.small, "small")
    full, full_prov, full_freeze, full_commit = load_summaries(args.full, "full")
    if small_freeze != full_freeze or small_commit != full_commit:
        raise RuntimeError("small/full R1 gates came from different source/environment freezes")
    if small_freeze != sha256(args.freeze_manifest) or small_commit != freeze["source_commit"]:
        raise RuntimeError("R1 source freeze differs from registry source freeze")

    names = sorted(set(small) | set(full))
    registry: dict[str, Any] = {}
    for name in names:
        small_ok = r1_qualified(small, name)
        full_ok = r1_qualified(full, name)
        feasibility_ok, feasibility_reasons = r0_gate(name, r0_state, r0_cap)
        path_ok = small_ok and full_ok and feasibility_ok
        registry[name] = {
            "r0_feasibility": "PASS" if feasibility_ok else "FAIL",
            "r0_notes": feasibility_reasons,
            "small_gate": "PASS" if small_ok else "FAIL_OR_MISSING",
            "full_gate": "PASS" if full_ok else "FAIL_OR_MISSING",
            "status": "QUALIFIED" if path_ok else "BLOCKED",
            "formal_performance_allowed": bool(path_ok),
        }

    # Minimal R2: only controls needed to identify a qualified intervention are
    # retained. A same-frontend replay condition has no formal value when the
    # corresponding persistent intervention is unavailable/blocked.
    formal = ["TARGET_UB1"]
    selection_reasons: dict[str, str] = {"TARGET_UB1": "shared system reference"}

    for device in ("CPU", "NPU"):
        persist = f"PERSIST_{device}_UB1"
        replay = f"OPTIMUM_REPLAY_{device}_UB1"
        legacy = f"LEGACY_{device}_UB1"
        if qualified(registry, persist):
            if not qualified(registry, replay):
                raise RuntimeError(
                    f"{persist} qualified without its same-frontend replay control {replay}; "
                    "state-reuse effect is not identifiable"
                )
            if qualified(registry, legacy):
                append_once(formal, legacy)
                selection_reasons[legacy] = "qualified contemporaneous bridge to closed replay mechanism"
            append_once(formal, replay)
            selection_reasons[replay] = f"same-frontend {device} replay control for persistent-state effect"
            append_once(formal, persist)
            selection_reasons[persist] = f"qualified {device} persistent-state intervention"

    target_ub2_ok = qualified(registry, "TARGET_UB2")
    persist_pair_ok = (
        target_ub2_ok
        and qualified(registry, "PERSIST_NPU_UB1")
        and qualified(registry, "PERSIST_NPU_UB2")
    )
    legacy_pair_ok = (
        target_ub2_ok
        and qualified(registry, "LEGACY_NPU_UB1")
        and qualified(registry, "LEGACY_NPU_UB2")
    )
    if persist_pair_ok:
        append_once(formal, "PERSIST_NPU_UB1")
        append_once(formal, "PERSIST_NPU_UB2")
        selection_reasons["PERSIST_NPU_UB2"] = "qualified same-policy NPU UB2 target-verification intervention"
        ub2_rule = "state-policy-matched PERSIST_NPU UB1/UB2 pair promoted"
    elif legacy_pair_ok:
        append_once(formal, "LEGACY_NPU_UB1")
        append_once(formal, "LEGACY_NPU_UB2")
        selection_reasons["LEGACY_NPU_UB1"] = selection_reasons.get(
            "LEGACY_NPU_UB1", "UB1 control for qualified legacy NPU UB2 target-path fallback"
        )
        selection_reasons["LEGACY_NPU_UB2"] = "qualified legacy NPU UB2 target-path fallback"
        ub2_rule = "persistent NPU UB2 unavailable/blocked; state-policy-matched LEGACY_NPU UB1/UB2 pair promoted"
    else:
        ub2_rule = "no correctness-qualified state-policy-matched NPU UB1/UB2 pair; no UB2 formal timing"

    identifiable_effects = {
        "state_reuse_cpu": ({"formal_paths": ["OPTIMUM_REPLAY_CPU_UB1", "PERSIST_CPU_UB1"],
                             "required_correctness_gates": []}
                            if qualified(registry, "OPTIMUM_REPLAY_CPU_UB1")
                            and qualified(registry, "PERSIST_CPU_UB1") else None),
        "state_reuse_npu": ({"formal_paths": ["OPTIMUM_REPLAY_NPU_UB1", "PERSIST_NPU_UB1"],
                             "required_correctness_gates": []}
                            if qualified(registry, "OPTIMUM_REPLAY_NPU_UB1")
                            and qualified(registry, "PERSIST_NPU_UB1") else None),
        "target_ub2": ({"formal_paths": ["PERSIST_NPU_UB1", "PERSIST_NPU_UB2"],
                        "required_correctness_gates": ["TARGET_UB2"]} if persist_pair_ok else
                       {"formal_paths": ["LEGACY_NPU_UB1", "LEGACY_NPU_UB2"],
                        "required_correctness_gates": ["TARGET_UB2"]} if legacy_pair_ok else None),
    }

    out = {
        "schema": "heterospec.358h.runtime.qualification_registry.v3",
        "status": "FROZEN_FOR_R2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_uses_performance_timing": False,
        "freeze_manifest_sha256": small_freeze,
        "freeze_source_commit": small_commit,
        "registry": registry,
        "formal_conditions": formal,
        "identifiable_effects": identifiable_effects,
        "formal_condition_reasons": selection_reasons,
        "formal_scope_rule": "retain only the target reference and controls required to identify qualified state/target interventions",
        "target_ub2_role": "correctness gate only; not a target-only performance condition",
        "ub2_selection_rule_result": ub2_rule,
        "r0": {
            "state_tests": str(args.r0_state_tests),
            "state_tests_sha256": sha256(args.r0_state_tests),
            "capability": str(args.r0_capability),
            "capability_sha256": sha256(args.r0_capability),
            "process_isolation": str(args.r0_process_isolation),
            "process_isolation_sha256": sha256(args.r0_process_isolation),
            "status": str(args.r0_status),
            "status_sha256": sha256(args.r0_status),
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
    print(json.dumps({
        "formal_conditions": formal,
        "formal_condition_reasons": selection_reasons,
        "ub2": ub2_rule,
        "freeze": small_freeze,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
