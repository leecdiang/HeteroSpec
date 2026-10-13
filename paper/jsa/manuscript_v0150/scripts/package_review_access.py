#!/usr/bin/env python3
"""Package verified review sources locally; do not deposit or publish anything."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "output/review_access_stage"
ACCESS = ROOT / "review_access"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deliver(folder: Path, target: Path, kind: str) -> dict:
    files = sorted(p for p in folder.rglob("*") if p.is_file())
    manifest = {"kind": kind, "version": "0.15.3", "date": "2026-10-13",
                "status": "LOCAL_AUTHOR_STAGING_NOT_PUBLISHED",
                "files": {p.relative_to(folder).as_posix(): {"bytes": p.stat().st_size,
                           "sha256": sha(p)} for p in files}}
    (folder / "PACKAGE_CHECKSUMS.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(p for p in folder.rglob("*") if p.is_file()):
            archive.write(path, path.relative_to(folder))
    return {"file": target.name, "bytes": target.stat().st_size,
            "sha256": sha(target), "manifest_files": len(files), "zip_members": len(files) + 1}


def main() -> None:
    inventory = json.loads((ACCESS / "SOURCE_ACCESS_INVENTORY.json").read_text())
    rows = inventory["files"]
    required = [r for r in rows if r["class"] == "report_or_source_text"]
    assert all(r["retrieval"] == "verified_local" for r in required), "Finish source retrieval first"
    for row in required:
        path = STAGE / row["package_path"]
        assert path.stat().st_size == row["bytes"] and sha(path) == row["sha256"]
    extraction = json.loads((ACCESS / "NATIVE_SOURCE_EXTRACTION.json").read_text())
    for row in extraction["files"]:
        assert sha(STAGE / row["path"]) == row["sha256"]
    with tempfile.TemporaryDirectory(prefix="jsa-review-package-") as temporary:
        base = Path(temporary)
        core = base / "core"
        core.mkdir()
        for row in required:
            target = core / row["package_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(STAGE / row["package_path"], target)
        for name in ("REVIEWER_README.txt", "THIRD_PARTY_NOTICES.txt", "MODEL_ACCESS.json",
                     "SOURCE_ACCESS_INVENTORY.json", "NATIVE_SOURCE_EXTRACTION.json",
                     "RAW_ARCHIVE_ACCESS.json", "assemble_raw_archive.py",
                     "verify_review_package.py", "run_report_checks.py"):
            shutil.copy2(ACCESS / name, core / name)
        for name in ("RAW_RESTORE_VERIFICATION.json", "RAW_SCIENTIFIC_AUDIT.json", "RAW_RESTORE_HELPER_QA.json", "RAW_REPRODUCTION.txt"):
            if (ACCESS / name).exists():shutil.copy2(ACCESS / name, core / name)
        paper = core / "paper"
        paper.mkdir()
        for directory in ("data", "figures", "sections", "supplement"):
            shutil.copytree(ROOT / directory, paper / directory)
        for path in [*ROOT.glob("*.tex"), ROOT / "references.bib", ROOT / "CLAIM_EVIDENCE.md"]:
            shutil.copy2(path, paper / path.name)
        for name in ("main.pdf", "supplement.pdf"):
            shutil.copy2(ROOT / "output" / name, paper / name)
        (paper / "scripts").mkdir()
        for name in ("check_reported_data.py", "check_supplement_figures.py"):
            shutil.copy2(ROOT / "scripts" / name, paper / "scripts" / name)
        (paper / "provenance").mkdir()
        for name in ("SOURCE_MANIFEST.json", "REPORTED_DATA_CHECKS.json", "SUPPLEMENT_FIGURE_CHECKS_V0153.json"):
            shutil.copy2(ROOT / "provenance" / name, paper / "provenance" / name)
        native = base / "native"
        native.mkdir()
        shutil.copytree(STAGE / "native_source", native / "native_source")
        for name in ("NATIVE_SOURCE_EXTRACTION.json", "THIRD_PARTY_NOTICES.txt", "verify_review_package.py"):
            shutil.copy2(ACCESS / name, native / name)
        (native / "README.txt").write_text(
            "Fixed PR98 native source for inspection. Local author staging, not published.\n"
            "Run python3 verify_review_package.py to verify source bytes.\n"
            "Source extracted from native/source in the pinned SOURCE_RUNTIME_V02 capsule.\n"
            "Model weights, archived executable and runtime DLLs are not included.\n"
            "For environment, build records and numerical-runtime obligations, see the companion core package.\n"
            "Author-owned code is MIT; upstream notices and LICENSE_SCOPE.txt remain applicable.\n")
        for folder in (core, native):
            shutil.copytree(ACCESS / "licenses", folder / "licenses")
            shutil.copy2(ACCESS / "LICENSE_SCOPE.txt", folder / "LICENSE_SCOPE.txt")
        packages = [deliver(core, ROOT / "output/JSA_v0153_review_core.zip", "offline_report_review"),
                    deliver(native, ROOT / "output/JSA_v0153_native_source.zip", "native_source_inspection")]
        for package, command in zip(packages, ("run_report_checks.py", "verify_review_package.py")):
            restored = base / (package["kind"] if "kind" in package else package["file"] + ".restored")
            with zipfile.ZipFile(ROOT / "output" / package["file"]) as archive:
                assert all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in archive.namelist())
                archive.extractall(restored)
            subprocess.run([sys.executable, str(restored / command)], cwd=restored, check=True)
    groups = {}
    for campaign in sorted({r["campaign"] for r in rows}):
        subset = [r for r in rows if r["campaign"] == campaign]
        present = [r for r in subset if r["retrieval"] == "verified_local"]
        groups[campaign] = {"commit": subset[0]["commit"], "included_files": len(present),
                            "included_bytes": sum(r["bytes"] for r in present),
                            "not_in_core_files": len(subset) - len(present),
                            "not_in_core_bytes": sum(r["bytes"] for r in subset if r not in present),
                            "separately_verified_native_capsules": sum(r["retrieval"] == "verified_native_capsule" for r in subset)}
    status = {"date": "2026-10-13", "manuscript_version": "0.15.3",
              "status": "LOCAL_PACKAGES_VERIFIED_EXTERNAL_ACCESS_PENDING", "published": False,
              "live_reviewer_url": None, "registered_deposit_doi": None,
              "author_review_access_grant": "AUTHORIZED_UNPUBLISHED_READ_ONLY_ZENODO", "public_project_license": "MIT_CODE_CC_BY_4_0_AUTHOR_DATA_THIRD_PARTY_EXCLUDED",
              "packages": packages, "campaigns": groups,
              "native_source_files": len(extraction["files"]),
              "verification": "Both ZIPs extracted; file hashes checked; core report/figure checks passed",
              "not_performed": ["full raw archive restore/audit", "GPU rerun", "external deposit", "logged-out access test"],
              "remaining": ["remaining personal author declarations", "full raw/source-runtime archive retrieval and restoration",
                            "publisher-authorized model acquisition by the hardware reproducer", "workload and raw-content redistribution review",
                            "real deposit/link and logged-out download check", "data citation/availability update and journal portal checks"]}
    raw_receipt = ACCESS / "RAW_RESTORE_VERIFICATION.json"
    scientific_receipt = ACCESS / "RAW_SCIENTIFIC_AUDIT.json"
    if raw_receipt.exists():
        status["raw_restore"] = json.loads(raw_receipt.read_text())
        status["remaining"].remove("full raw/source-runtime archive retrieval and restoration")
        status["not_performed"].remove("full raw archive restore/audit")
        if scientific_receipt.exists():status["raw_scientific_audit"] = json.loads(scientific_receipt.read_text())
        else:status["not_performed"].append("raw scientific rederivation")
        status["not_performed"].append("external model weight rehash on this host")
    previous = json.loads((ACCESS / "ACCESS_STATUS.json").read_text()) if (ACCESS / "ACCESS_STATUS.json").exists() else {}
    for key in ("zenodo_drafts", "review_access_verification", "confidential_link_location"):
        if key in previous: status[key] = previous[key]
    if previous.get("zenodo_drafts"):
        status["status"] = "LOCAL_PACKAGES_REBUILT_REMOTE_UPLOAD_NEEDS_RECONCILIATION"
        status["not_performed"] = [item for item in status["not_performed"]
                                   if item not in ("external deposit", "logged-out access test")]
        status["not_performed"].append("remote upload/download reconciliation for these newly built ZIP hashes")
        status["remaining"].append("Compare new ZIP hashes with the draft; previous download receipts describe the prior bytes")
    (ACCESS / "ACCESS_STATUS.json").write_text(json.dumps(status, indent=2) + "\n")
    print(json.dumps({"packages": packages, "native_source_files": len(extraction["files"])}, indent=2))


if __name__ == "__main__":
    main()
