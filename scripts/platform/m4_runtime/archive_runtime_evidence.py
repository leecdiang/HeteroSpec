#!/usr/bin/env python3
"""Build a byte-addressed M4 archive without changing any frozen measurement file."""

import gzip
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "runs/m4/runtime_profitability_control_20260924"
BASE = ROOT / "benchmarks/m4_runtime"
OUT = ROOT / "artifacts/m4_runtime/runtime-profitability-control-20260925"
RUN_ID = "unattended-20260924t125921z"
ARCHIVE = OUT / "m4_runtime_complete_evidence.tar.gz"
RECOMPUTE = ROOT / "scripts/platform/m4_runtime/recompute_evidence_bundle.py"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_bytes(commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def data_from_file(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_bytes()


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build_payload():
    payload = {}

    def add(name, path):
        if name in payload:
            raise RuntimeError(f"Duplicate evidence path: {name}")
        payload[name] = data_from_file(path)

    stage_ids = {
        "calibration_baselines": RUN_ID + "-baseline",
        "calibration_candidates": RUN_ID + "-candidate",
        "qualification": RUN_ID + "-qualification",
        "formal": RUN_ID + "-formal",
    }
    for stage, attempt_id in stage_ids.items():
        directory = RUNS / stage / attempt_id
        for name in ("observations.jsonl", "manifest.json", "completion.json", "warmup.json", "runner_stderr.txt"):
            add(f"attempts/{stage}/{name}", directory / name)
    add("markers/FORMAL_DATA_STARTED", RUNS / "FORMAL_DATA_STARTED")
    add("markers/FORMAL_ATTEMPT_STARTED", RUNS / f"FORMAL_ATTEMPT_{RUN_ID}-formal_STARTED")
    add("build/manifest.json", RUNS / "build/manifest.json")
    add("build/m4-runtime-runner", RUNS / "build/m4-runtime-runner")
    add("pipeline/pipeline.log", RUNS / "pipeline" / RUN_ID / "pipeline.log")
    add("pipeline/status.json", RUNS / "pipeline" / RUN_ID / "status.json")
    add("pipeline/launcher.log", RUNS / "pipeline" / f"{RUN_ID}.launcher.log")
    add("freeze/CALIBRATION_FREEZE.json", BASE / "CALIBRATION_FREEZE.json")
    add("freeze/QUALIFICATION_REPORT.json", BASE / "QUALIFICATION_REPORT.json")
    add("analysis/FORMAL_ANALYSIS.json", BASE / "FORMAL_ANALYSIS.json")
    add("analysis/FORMAL_REPORT.md", BASE / "FORMAL_REPORT.md")
    add("analysis/analyze_runtime_study_provenance_recovery.py",
        ROOT / "scripts/platform/m4_runtime/analyze_runtime_study_provenance_recovery.py")
    add("tools/recompute_evidence_bundle.py", RECOMPUTE)
    add("tools/archive_runtime_evidence.py", Path(__file__))

    freeze = json.loads(payload["freeze/CALIBRATION_FREEZE.json"])
    for path, expected_sha in sorted(freeze["source_data_sha256"].items()):
        add(f"frozen_repo/{path}", ROOT / path)
        if sha(payload[f"frozen_repo/{path}"]) != expected_sha:
            raise RuntimeError(f"Frozen source differs from recorded digest: {path}")

    marker = json.loads(payload["markers/FORMAL_DATA_STARTED"])
    attempt_marker = json.loads(payload["markers/FORMAL_ATTEMPT_STARTED"])
    qualification = json.loads(payload["freeze/QUALIFICATION_REPORT.json"])
    formal_manifest = json.loads(payload["attempts/formal/manifest.json"])
    analysis = json.loads(payload["analysis/FORMAL_ANALYSIS.json"])
    pipeline_status = json.loads(payload["pipeline/status.json"])
    actual_sha = sha(payload["freeze/CALIBRATION_FREEZE.json"])
    wrong_sha = sha(payload["build/manifest.json"])
    if any(x["freeze_sha256"] != wrong_sha for x in (marker, attempt_marker, qualification, formal_manifest)):
        raise RuntimeError("The recorded freeze digest does not match the known defect")
    if actual_sha == wrong_sha or analysis["provenance_audit"]["actual_freeze_sha256"] != actual_sha:
        raise RuntimeError("The actual freeze digest failed recovery audit")
    if git_bytes(marker["head"], "benchmarks/m4_runtime/CALIBRATION_FREEZE.json") != payload["freeze/CALIBRATION_FREEZE.json"]:
        raise RuntimeError("Formal-start commit freeze differs from current original bytes")
    if git_bytes(marker["head"], "benchmarks/m4_runtime/QUALIFICATION_REPORT.json") != payload["freeze/QUALIFICATION_REPORT.json"]:
        raise RuntimeError("Formal-start commit qualification differs from current original bytes")
    if pipeline_status["stages"]["formal"]["status"] != "COMPLETE" or pipeline_status["status"] != "STOPPED":
        raise RuntimeError("Original pipeline status is not the documented analysis stop")

    closure = {
        "schema": "heterospec.m4_runtime.provenance_closure.v1",
        "classification": "METADATA_RECORDING_DEFECT_NOT_MEASUREMENT_MUTATION",
        "formal_start_commit": marker["head"],
        "actual_calibration_freeze_sha256": actual_sha,
        "erroneously_recorded_build_manifest_sha256": wrong_sha,
        "affected_fields": [
            "QUALIFICATION_REPORT.json:freeze_sha256",
            "FORMAL_DATA_STARTED:freeze_sha256",
            "FORMAL_ATTEMPT_STARTED:freeze_sha256",
            "formal/manifest.json:freeze_sha256",
        ],
        "cause": "frozen() returned the final artifact-loop path (build manifest) instead of the calibration-freeze path",
        "formal_start_freeze_git_blob_sha1": subprocess.check_output(
            ["git", "rev-parse", f"{marker['head']}:benchmarks/m4_runtime/CALIBRATION_FREEZE.json"],
            cwd=ROOT, text=True).strip(),
        "raw_observations_or_original_markers_modified": False,
        "measurement_timing_repeated_after_formal": False,
        "recovery_analysis_sha256": sha(payload["analysis/FORMAL_ANALYSIS.json"]),
    }
    payload["provenance/provenance_closure.json"] = json_bytes(closure)
    return payload


def create_archive(payload):
    entries = [{"path": name, "bytes": len(data), "sha256": sha(data)}
               for name, data in sorted(payload.items())]
    manifest = {
        "schema": "heterospec.m4_runtime.bundle_manifest.v1",
        "root": "m4-runtime-evidence",
        "attempt_id": RUN_ID,
        "entry_count": len(entries),
        "files": entries,
    }
    manifest_bytes = json_bytes(manifest)
    OUT.mkdir(parents=True, exist_ok=False)
    payload["bundle_manifest.json"] = manifest_bytes
    with ARCHIVE.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0, compresslevel=9) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for name, data in sorted(payload.items()):
                    info = tarfile.TarInfo("m4-runtime-evidence/" + name)
                    info.size = len(data)
                    info.mtime = 0
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    info.mode = 0o644
                    archive.addfile(info, io.BytesIO(data))
        raw.flush()
        os.fsync(raw.fileno())
    (OUT / "bundle_manifest.json").write_bytes(manifest_bytes)
    return manifest_bytes


def main():
    if OUT.exists():
        raise RuntimeError(f"Evidence destination already exists; refusing to replace it: {OUT}")
    payload = build_payload()
    manifest_bytes = create_archive(payload)
    digest = sha(ARCHIVE.read_bytes())
    result = subprocess.run([sys.executable, str(RECOMPUTE), str(ARCHIVE), "--expected-sha256", digest],
                            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(f"Archive extraction/recomputation failed:\n{result.stdout}{result.stderr}")
    recomputed = json.loads(result.stdout)
    descriptor = {
        "schema": "heterospec.m4_runtime.archive_descriptor.v1",
        "archive": ARCHIVE.name,
        "bytes": ARCHIVE.stat().st_size,
        "sha256": digest,
        "bundle_manifest_sha256": sha(manifest_bytes),
        "clean_extraction_validation": {
            "status": "PASS",
            "validated_payload_files": recomputed["verified_payload_files"],
            "size_or_sha256_failures": 0,
        },
        "independent_recomputation": recomputed,
    }
    (OUT / "archive_descriptor.json").write_bytes(json_bytes(descriptor))
    ARCHIVE.chmod(0o444)
    print(json.dumps(descriptor, indent=2))


if __name__ == "__main__":
    main()
