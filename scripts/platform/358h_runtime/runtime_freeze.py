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
    "benchmarks/358h_runtime/runtime_protocol_v0_2.json",
    "benchmarks/358h_runtime/RUNTIME_ARCHITECTURE_v0_2.md",
    "benchmarks/358h_runtime/V01_TO_V02_TRANSITION.md",
    "scripts/platform/358h_runtime/runtime_types.py",
    "scripts/platform/358h_runtime/runtime_target.py",
    "scripts/platform/358h_runtime/runtime_draft.py",
    "scripts/platform/358h_runtime/runtime_shared_draft.py",
    "scripts/platform/358h_runtime/runtime_factory.py",
    "scripts/platform/358h_runtime/runtime_process_v02.py",
    "scripts/platform/358h_runtime/runtime_session_v02.py",
    "scripts/platform/358h_runtime/runtime_workers_v02.py",
    "scripts/platform/358h_runtime/runtime_r0_v02.py",
    "scripts/platform/358h_runtime/runtime_legacy_target_v02.py",
    "scripts/platform/358h_runtime/runtime_legacy_draft_v02.py",
    "scripts/platform/358h_runtime/runtime_process_unit_tests_v02.py",
    "scripts/platform/358h_runtime/runtime_runner.py",
    "scripts/platform/358h_runtime/runtime_policy.py",
    "scripts/platform/358h_runtime/runtime_logic_unit_tests.py",
    "scripts/platform/358h_runtime/probe_openvino_state.py",
    "scripts/platform/358h_runtime/runtime_state_tests.py",
    "scripts/platform/358h_runtime/plan_runtime_qualification.py",
    "scripts/platform/358h_runtime/run_runtime_qualification.py",
    "scripts/platform/358h_runtime/freeze_runtime_registry.py",
    "scripts/platform/358h_runtime/run_runtime_campaign.py",
    "scripts/platform/358h_runtime/analyze_runtime_campaign.py",
    "scripts/platform/358h_runtime/runtime_freeze.py",
    "scripts/platform/358h_runtime/create_runtime_freeze.py",
    "scripts/platform/358h_runtime/validate_runtime_scaffold.py",
]

MODEL_ARTIFACT_SHA256 = {
    "models/gguf/Qwen3-8B-Q8_0.gguf": "408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6",
    "models/gguf/Qwen3-0.6B-Q8_0.gguf": "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031",
    "models/openvino/qwen3-0.6b-6130ef-int4-sym-g128/openvino_model.xml": "fc8ad94dbecfc0c45cf3db4f0624344d2bea2cdd6997e0b45ca52d4f7baa1103",
    "models/openvino/qwen3-0.6b-6130ef-int4-sym-g128/openvino_model.bin": "2e129cffb1a7239007a3df27e0f3f7bb12f65a40e5c9b1e24a250d952da47837",
}

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
    if tracked_tree_dirty():
        raise RuntimeError("tracked source changed after runtime freeze")
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

    actual_artifacts = {rel: sha256(ROOT / rel) for rel in MODEL_ARTIFACT_SHA256}
    if actual_artifacts != MODEL_ARTIFACT_SHA256:
        raise RuntimeError("frozen model artifact hash differs from closed binding")
    if manifest.get("model_artifacts") != actual_artifacts:
        raise RuntimeError("frozen model/runtime artifacts changed after runtime freeze")
    r0 = manifest.get("r0", {})
    for key in ("capability", "process_isolation", "state_tests", "status"):
        recorded = Path(r0.get(key, ""))
        if not recorded.is_file() or sha256(recorded) != r0.get(f"{key}_sha256"):
            raise RuntimeError(f"final R0 artifact changed after freeze: {key}")
    if "session_log" in r0 and sha256(Path(r0["session_log"])) != r0.get("session_log_sha256"):
        raise RuntimeError("final R0 session log changed after freeze")
    status = json.loads(Path(r0["status"]).read_text(encoding="utf-8"))
    if status.get("source_commit") != manifest["source_commit"] or status.get("status") != "R0_V02_PASS":
        raise RuntimeError("final R0 does not match frozen source")
    return manifest


__all__ = [
    "ROOT",
    "FROZEN_RELATIVE_FILES",
    "PACKAGE_NAMES",
    "DATASET_REL",
    "DATASET_SHA256",
    "MODEL_ARTIFACT_SHA256",
    "sha256",
    "git_head",
    "tracked_tree_dirty",
    "package_versions",
    "frozen_file_hashes",
    "verify_freeze_manifest",
]
