#!/usr/bin/env python3
"""Freeze the prospective runtime implementation after final R0 qualification.

Generate this manifest only after R0 capability/state work is complete and any
API-compatibility repairs have been committed. R1 and R2 reject a changed source
tree or Python package environment.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from runtime_freeze import (
    DATASET_REL,
    DATASET_SHA256,
    MODEL_ARTIFACT_SHA256,
    ROOT,
    frozen_file_hashes,
    git_head,
    package_versions,
    sha256,
    tracked_tree_dirty,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--r0-capability", type=Path, required=True)
    ap.add_argument("--r0-state-tests", type=Path, required=True)
    ap.add_argument("--r0-process-isolation", type=Path, required=True)
    ap.add_argument("--r0-status", type=Path, required=True)
    ap.add_argument("--r0-session-log", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    if tracked_tree_dirty():
        raise RuntimeError(
            "tracked working tree is dirty; commit final R0/API compatibility repairs before freezing"
        )
    if args.output.exists():
        raise RuntimeError(f"refusing to overwrite existing freeze manifest: {args.output}")

    r0_cap = json.loads(args.r0_capability.read_text(encoding="utf-8"))
    r0_state = json.loads(args.r0_state_tests.read_text(encoding="utf-8"))
    r0_process = json.loads(args.r0_process_isolation.read_text(encoding="utf-8"))
    r0_status = json.loads(args.r0_status.read_text(encoding="utf-8"))
    if r0_cap.get("formal") is not False or r0_state.get("formal") is not False:
        raise RuntimeError("R0 provenance inputs must be explicitly non-formal")
    if (r0_status.get("status") != "R0_V02_PASS" or r0_status.get("source_commit") != git_head()
            or r0_status.get("source_dirty_tracked") is not False
            or r0_status.get("ac_power_online") is not True
            or r0_status.get("formal") is not False
            or r0_status.get("formal_data_seen") is not False
            or not r0_status.get("process_checks_pass")
            or not r0_status.get("target_state_pass")
            or r0_process.get("multi_worker", {}).get("status") != "PASS"):
        raise RuntimeError("final R0 provenance is not a clean exact-HEAD AC-online R0_V02_PASS")

    dataset = ROOT / DATASET_REL
    if sha256(dataset) != DATASET_SHA256:
        raise RuntimeError("HumanEval dataset hash mismatch before freeze")

    artifacts = {rel: sha256(ROOT / rel) for rel in MODEL_ARTIFACT_SHA256}
    if artifacts != MODEL_ARTIFACT_SHA256:
        raise RuntimeError("closed model artifact hash mismatch before freeze")

    pip_freeze = subprocess.check_output(
        [sys.executable, "-m", "pip", "freeze"], text=True
    ).splitlines()

    manifest = {
        "schema": "heterospec.358h.runtime.freeze_manifest.v0.2",
        "status": "FROZEN_FOR_R1_R2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": git_head(),
        "tracked_tree_clean_at_freeze": True,
        "frozen_files": frozen_file_hashes(),
        "python": sys.version,
        "packages": package_versions(),
        "pip_freeze": pip_freeze,
        "dataset_sha256": DATASET_SHA256,
        "model_artifacts": artifacts,
        "r0": {
            "capability": str(args.r0_capability.resolve()),
            "capability_sha256": sha256(args.r0_capability),
            "state_tests": str(args.r0_state_tests.resolve()),
            "state_tests_sha256": sha256(args.r0_state_tests),
            "process_isolation": str(args.r0_process_isolation.resolve()),
            "process_isolation_sha256": sha256(args.r0_process_isolation),
            "status": str(args.r0_status.resolve()),
            "status_sha256": sha256(args.r0_status),
        },
        "rules": [
            "R1 and R2 must verify this manifest before inference",
            "any frozen source/protocol/package/artifact change invalidates prior R1 qualification",
            "untracked result files do not change the source freeze",
            "do not commit or change HEAD between freeze, R1, registry freeze, and R2",
        ],
    }
    if args.r0_session_log:
        manifest["r0"]["session_log"] = str(args.r0_session_log.resolve())
        manifest["r0"]["session_log_sha256"] = sha256(args.r0_session_log)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": manifest["status"],
        "source_commit": manifest["source_commit"],
        "frozen_file_count": len(manifest["frozen_files"]),
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
