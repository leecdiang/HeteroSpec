#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

FROZEN_RELATIVE_FILES = [
    "benchmarks/358h_runtime/runtime_protocol_v0.json",
    "scripts/platform/358h_runtime/runtime_types.py",
    "scripts/platform/358h_runtime/runtime_target.py",
    "scripts/platform/358h_runtime/runtime_draft.py",
    "scripts/platform/358h_runtime/runtime_shared_draft.py",
    "scripts/platform/358h_runtime/runtime_factory.py",
    "scripts/platform/358h_runtime/runtime_runner.py",
    "scripts/platform/358h_runtime/probe_openvino_state.py",
    "scripts/platform/358h_runtime/runtime_state_tests.py",
    "scripts/platform/358h_runtime/run_runtime_qualification.py",
    "scripts/platform/358h_runtime/freeze_runtime_registry.py",
    "scripts/platform/358h_runtime/run_runtime_campaign.py",
    "scripts/platform/358h_runtime/analyze_runtime_campaign.py",
    "scripts/platform/358h_runtime/runtime_freeze.py",
    "scripts/platform/358h_runtime/create_runtime_freeze.py",
]

PACKAGE_NAMES = [
    "openvino",
    "openvino-genai",
    "optimum-intel",
    "transformers",
    "torch",
    "nncf",
    "numpy",
    "psutil",
]

DATASET_REL = "datasets/humaneval/HumanEval.jsonl.gz"
DATASET_SHA256 = "b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def tracked_tree_dirty() -> bool:
    text = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True
    )
    return bool(text.strip())


def package_versions() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for name in PACKAGE_NAMES:
        try:
            out[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            out[name] = None
    return out


def frozen_file_hashes() -> dict[str, str]:
    out = {}
    for rel in FROZEN_RELATIVE_FILES:
        path = ROOT / rel
        if not path.is_file():
            raise RuntimeError(f"freeze input missing: {rel}")
        out[rel] = sha256(path)
    return out


def verify_freeze_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("status") != "FROZEN_FOR_R1_R2":
        raise RuntimeError("runtime freeze manifest is not FROZEN_FOR_R1_R2")
    if manifest.get("source_commit") != git_head():
        raise RuntimeError(
            f"git HEAD changed after runtime freeze: {git_head()} != {manifest.get('source_commit')}"
        )
    expected_files = manifest.get("frozen_files", {})
    actual_files = frozen_file_hashes()
    if expected_files != actual_files:
        changed = sorted(
            rel for rel in set(expected_files) | set(actual_files)
            if expected_files.get(rel) != actual_files.get(rel)
        )
        raise RuntimeError(f"runtime source/protocol changed after freeze: {changed}")
    if manifest.get("python") != sys.version:
        raise RuntimeError("Python version changed after runtime freeze")
    current_packages = package_versions()
    if manifest.get("packages") != current_packages:
        changed = sorted(
            name for name in set(manifest.get("packages", {})) | set(current_packages)
            if manifest.get("packages", {}).get(name) != current_packages.get(name)
        )
        raise RuntimeError(f"runtime package versions changed after freeze: {changed}")
    dataset = ROOT / DATASET_REL
    if sha256(dataset) != DATASET_SHA256 or manifest.get("dataset_sha256") != DATASET_SHA256:
        raise RuntimeError("HumanEval dataset changed after runtime freeze")

    # Reuse the closed campaign's authoritative model/artifact hash list.
    legacy_dir = ROOT / "scripts" / "platform" / "358h"
    if str(legacy_dir) not in sys.path:
        sys.path.insert(0, str(legacy_dir))
    from phase3_heterogeneous_runner import EXPECTED  # noqa: E402

    actual_artifacts = {str(p.relative_to(ROOT)): sha256(p) for p in EXPECTED}
    if manifest.get("model_artifacts") != actual_artifacts:
        raise RuntimeError("frozen model/runtime artifacts changed after runtime freeze")
    return manifest


__all__ = [
    "ROOT",
    "FROZEN_RELATIVE_FILES",
    "PACKAGE_NAMES",
    "DATASET_REL",
    "DATASET_SHA256",
    "sha256",
    "git_head",
    "tracked_tree_dirty",
    "package_versions",
    "frozen_file_hashes",
    "verify_freeze_manifest",
]
