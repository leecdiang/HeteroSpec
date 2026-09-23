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
    if r0_cap.get("formal") is not False or r0_state.get("formal") is not False:
        raise RuntimeError("R0 provenance inputs must be explicitly non-formal")

    dataset = ROOT / DATASET_REL
    if sha256(dataset) != DATASET_SHA256:
        raise RuntimeError("HumanEval dataset hash mismatch before freeze")

    legacy_dir = ROOT / "scripts" / "platform" / "358h"
    if str(legacy_dir) not in sys.path:
        sys.path.insert(0, str(legacy_dir))
    from phase3_heterogeneous_runner import EXPECTED  # noqa: E402

    artifacts = {str(p.relative_to(ROOT)): sha256(p) for p in EXPECTED}
    for p, expected in EXPECTED.items():
        if artifacts[str(p.relative_to(ROOT))] != expected:
            raise RuntimeError(f"closed artifact hash mismatch before freeze: {p}")

    pip_freeze = subprocess.check_output(
        [sys.executable, "-m", "pip", "freeze"], text=True
    ).splitlines()

    manifest = {
        "schema": "heterospec.358h.runtime.freeze_manifest.v1",
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
            "capability": str(args.r0_capability),
            "capability_sha256": sha256(args.r0_capability),
            "state_tests": str(args.r0_state_tests),
            "state_tests_sha256": sha256(args.r0_state_tests),
        },
        "rules": [
            "R1 and R2 must verify this manifest before inference",
            "any frozen source/protocol/package/artifact change invalidates prior R1 qualification",
            "untracked result files do not change the source freeze",
            "do not commit or change HEAD between freeze, R1, registry freeze, and R2",
        ],
    }
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
