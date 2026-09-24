#!/usr/bin/env python3
"""Hardware-independent checks that formal R2 cannot start without an effect."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from run_runtime_campaign import assert_r2_stage_gate


def expect_rejection(protocol: dict, registry: dict, message: str) -> None:
    try:
        assert_r2_stage_gate(protocol, registry)
    except RuntimeError as exc:
        assert str(exc) == message, str(exc)
    else:
        raise AssertionError(f"R2 gate accepted a case requiring {message}")


def main() -> None:
    authorized = {"stage_gates": {"r2_authorized": True}}
    closed = {"stage_gates": {"r2_authorized": False}}
    baseline_only = {"formal_conditions": ["TARGET_UB1"],
                     "registry": {"TARGET_UB1": {"status": "QUALIFIED"}},
                     "identifiable_effects": {"state_reuse_cpu": None, "target_ub2": None}}
    expect_rejection(closed, baseline_only, "R2_NOT_AUTHORIZED_PROTOCOL")
    expect_rejection(authorized, baseline_only,
                     "R2_NOT_ADMISSIBLE_NO_IDENTIFIABLE_INTERVENTION")
    pair = {"formal_conditions": ["TARGET_UB1", "OPTIMUM_REPLAY_CPU_UB1", "PERSIST_CPU_UB1"],
            "registry": {p: {"status": "QUALIFIED"} for p in
                         ("TARGET_UB1", "OPTIMUM_REPLAY_CPU_UB1", "PERSIST_CPU_UB1")},
            "identifiable_effects": {"state_reuse_cpu": {
                "formal_paths": ["OPTIMUM_REPLAY_CPU_UB1", "PERSIST_CPU_UB1"],
                "required_correctness_gates": []}}}
    assert_r2_stage_gate(authorized, pair)
    pair["identifiable_effects"] = {"unrecognized_pair": {
        "formal_paths": ["OPTIMUM_REPLAY_CPU_UB1", "PERSIST_CPU_UB1"],
        "required_correctness_gates": []}}
    expect_rejection(authorized, pair,
                     "R2_NOT_ADMISSIBLE_NO_IDENTIFIABLE_INTERVENTION")
    pair["identifiable_effects"] = {"state_reuse_cpu": {
        "formal_paths": ["OPTIMUM_REPLAY_CPU_UB1", "PERSIST_CPU_UB1"],
        "required_correctness_gates": []}}
    pair["registry"]["PERSIST_CPU_UB1"]["status"] = "BLOCKED"
    expect_rejection(authorized, pair,
                     "R2_NOT_ADMISSIBLE_NO_IDENTIFIABLE_INTERVENTION")
    target_pair = {"formal_conditions": ["TARGET_UB1", "LEGACY_NPU_UB1", "LEGACY_NPU_UB2"],
                   "registry": {p: {"status": "QUALIFIED"} for p in
                                ("TARGET_UB1", "LEGACY_NPU_UB1", "LEGACY_NPU_UB2")},
                   "identifiable_effects": {"target_ub2": {
                       "formal_paths": ["LEGACY_NPU_UB1", "LEGACY_NPU_UB2"],
                       "required_correctness_gates": ["TARGET_UB2"]}}}
    expect_rejection(authorized, target_pair,
                     "R2_NOT_ADMISSIBLE_NO_IDENTIFIABLE_INTERVENTION")
    target_pair["registry"]["TARGET_UB2"] = {"status": "QUALIFIED"}
    assert_r2_stage_gate(authorized, target_pair)

    # The actual entrypoint must refuse before it creates a formal output directory.
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        registry_path = root / "registry.json"
        registry_path.write_text(json.dumps(baseline_only), encoding="utf-8")
        output = root / "formal"
        command = [sys.executable, "-B", str(Path(__file__).with_name("run_runtime_campaign.py")),
                   "--registry", str(registry_path), "--freeze-manifest", str(root / "absent.json"),
                   "--output-dir", str(output)]
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode != 0
        assert "R2_NOT_AUTHORIZED_PROTOCOL" in result.stderr
        assert not output.exists(), "R2 guard created formal output"
    print("R2_GATE_V03_PASS")


if __name__ == "__main__":
    main()
