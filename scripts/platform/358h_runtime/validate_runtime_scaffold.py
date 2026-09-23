#!/usr/bin/env python3
"""Hardware-independent preflight validator for the prospective 358H runtime study."""
from __future__ import annotations

import json
import ast
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = "b80bdbc67f6e19829245ad732390cd6aef941675"
ALLOWED_PREFIXES = ("benchmarks/358h_runtime/", "scripts/platform/358h_runtime/")
REQUIRED = [
    ROOT / "benchmarks" / "358h_runtime" / "runtime_protocol_v0.json",
    ROOT / "benchmarks" / "358h_runtime" / "RUNTIME_ARCHITECTURE.md",
    ROOT / "benchmarks" / "358h_runtime" / "WORK_HANDOFF.md",
    ROOT / "benchmarks" / "358h_runtime" / "R0_API_DECISION_TABLE.md",
    ROOT / "benchmarks" / "358h_runtime" / "runtime_protocol_v0_2.json",
    ROOT / "benchmarks" / "358h_runtime" / "RUNTIME_ARCHITECTURE_v0_2.md",
    ROOT / "benchmarks" / "358h_runtime" / "V01_TO_V02_TRANSITION.md",
]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    failures: list[str] = []
    changed = [x for x in git("diff", "--name-only", f"{BASE}...HEAD").splitlines() if x]
    escaped = [p for p in changed if not p.startswith(ALLOWED_PREFIXES)]
    if escaped:
        failures.append(f"changes escaped runtime-study prefixes: {escaped}")

    for path in REQUIRED:
        if not path.is_file():
            failures.append(f"missing required file: {path.relative_to(ROOT)}")

    protocol = json.loads(REQUIRED[0].read_text(encoding="utf-8"))
    r2 = protocol.get("stages", {}).get("R2", {})
    if r2.get("claim_status") != "FORMAL_PROSPECTIVE_RUNTIME_STUDY":
        failures.append("protocol does not declare R2 as the formal prospective runtime study")
    if protocol.get("fixed_semantics", {}).get("energy") != "NOT_CLAIMED":
        failures.append("protocol unexpectedly enables an energy claim")
    if protocol.get("formal_data_seen") is not False:
        failures.append("preexecution protocol says formal data has already been seen")
    if protocol.get("created_from_main") != BASE:
        failures.append("protocol base commit differs from scaffold validator base")

    v02 = json.loads(REQUIRED[4].read_text(encoding="utf-8"))
    gates = v02.get("stage_gates", {})
    if (v02.get("formal_data_seen") is not False
            or v02.get("status") != "READY_FOR_FREEZE_R1_R2_SOURCE"
            or gates != {"r0_reviewed": True, "r1_authorized": True, "r2_authorized": False}
            or v02.get("r0_v02", {}).get("stop_after_r0") is not False):
        failures.append("v0.2 protocol stage gates are not ready for freeze/R1-only")

    # Spawn re-imports entrypoint modules in every child. A top-level backend
    # import in any neutral module would recreate the v0.1 OpenMP collision.
    neutral = ("runtime_r0_v02.py", "runtime_process_v02.py", "runtime_session_v02.py",
               "runtime_workers_v02.py", "runtime_factory.py", "runtime_freeze.py",
               "create_runtime_freeze.py", "run_runtime_qualification.py", "run_runtime_campaign.py",
               "plan_runtime_qualification.py", "freeze_runtime_registry.py")
    forbidden = ("runtime_target", "runtime_draft", "runtime_shared_draft", "openvino", "openvino_genai", "optimum", "phase3_heterogeneous_runner")
    for filename in neutral:
        tree = ast.parse((HERE / filename).read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(name.startswith(forbidden) for name in names):
                failures.append(f"top-level backend import in {filename}: {names}")

    from runtime_freeze import FROZEN_RELATIVE_FILES
    unfrozen = sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in HERE.glob("*.py")
                      if str(p.relative_to(ROOT)).replace("\\", "/") not in FROZEN_RELATIVE_FILES)
    if unfrozen:
        failures.append(f"runtime Python files omitted from source freeze: {unfrozen}")
    neutral_import = subprocess.run([sys.executable, "-B", "-c",
        "import sys, run_runtime_qualification, run_runtime_campaign; "
        "assert not any(n.startswith(('openvino', 'optimum', 'runtime_target', 'runtime_draft', 'runtime_shared_draft')) for n in sys.modules)"],
        cwd=HERE, text=True, capture_output=True)
    if neutral_import.returncode:
        failures.append("R1/R2 parent import graph loads inference backend: " + neutral_import.stderr)

    unit = subprocess.run(
        [sys.executable, str(HERE / "runtime_logic_unit_tests.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if unit.returncode != 0:
        failures.append("runtime_logic_unit_tests.py failed:\n" + unit.stdout + unit.stderr)
    process_unit = subprocess.run(
        [sys.executable, str(HERE / "runtime_process_unit_tests_v02.py")],
        cwd=ROOT, text=True, capture_output=True,
    )
    if process_unit.returncode != 0:
        failures.append("runtime_process_unit_tests_v02.py failed:\n" + process_unit.stdout + process_unit.stderr)

    result = {
        "base": BASE,
        "head": git("rev-parse", "HEAD"),
        "changed_files": len(changed),
        "allowed_prefixes": list(ALLOWED_PREFIXES),
        "escaped_files": escaped,
        "logic_unit_tests_returncode": unit.returncode,
        "process_unit_tests_returncode": process_unit.returncode,
        "pass": not failures,
        "failures": failures,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
