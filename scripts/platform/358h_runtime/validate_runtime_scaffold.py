#!/usr/bin/env python3
"""Hardware-independent preflight validator for the prospective 358H runtime study."""
from __future__ import annotations

import json
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
    if protocol.get("formal_performance_stage") != "R2":
        failures.append("protocol does not declare R2 as formal performance stage")
    if protocol.get("energy") not in ("OUT_OF_SCOPE", "NOT_CLAIMED"):
        failures.append("protocol unexpectedly enables energy")

    unit = subprocess.run(
        [sys.executable, str(HERE / "runtime_logic_unit_tests.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if unit.returncode != 0:
        failures.append("runtime_logic_unit_tests.py failed:\n" + unit.stdout + unit.stderr)

    result = {
        "base": BASE,
        "head": git("rev-parse", "HEAD"),
        "changed_files": len(changed),
        "allowed_prefixes": list(ALLOWED_PREFIXES),
        "escaped_files": escaped,
        "logic_unit_tests_returncode": unit.returncode,
        "pass": not failures,
        "failures": failures,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
