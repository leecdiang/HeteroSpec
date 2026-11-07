#!/usr/bin/env python3
"""Retrieve the fixed PR98 source capsule and extract source only, without execution."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import zipfile
from prepare_review_access import api

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "output/review_access_stage"
SOURCE = "benchmarks/rtx_querylayout_mechanism_v1/SOURCE_RUNTIME_V02.part001"
COMMIT = "3235d44c26edd92db33e574094c26af8e29d2452"
EXPECTED_SHA256 = "36be0d738ad5d29579b75825f68337003eb127405cc5418abc566cb07718a4d8"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Download the 20,245,939-byte capsule if not cached")
    args = parser.parse_args()
    inventory = json.loads((ROOT / "review_access/SOURCE_ACCESS_INVENTORY.json").read_text())
    rows = [r for r in inventory["files"] if r["campaign"] == "rtx98" and r["path"] == SOURCE]
    assert len(rows) == 1 and rows[0]["commit"] == COMMIT
    row = rows[0]
    capsule = STAGE / "capsules/SOURCE_RUNTIME_V02.zip"
    if not capsule.exists():
        if not args.download:
            raise SystemExit("Capsule absent. Use --download with the author's GitHub access.")
        blob = api(f"repos/leecdiang/HeteroSpec/git/blobs/{row['git_blob_sha1']}")
        assert blob["encoding"] == "base64"
        data = base64.b64decode(blob["content"])
        capsule.parent.mkdir(parents=True, exist_ok=True)
    else:
        data = capsule.read_bytes()
    assert len(data) == row["bytes"] == 20245939
    assert hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest() == row["git_blob_sha1"]
    assert hashlib.sha256(data).hexdigest() == EXPECTED_SHA256
    capsule.write_bytes(data)
    records = []
    with zipfile.ZipFile(capsule) as archive:
        for name in archive.namelist():
            if not name.startswith("native/source/") or name.endswith("/"):
                continue
            relative = Path(name.removeprefix("native/source/"))
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Unsafe source member")
            package_path = Path("native_source/rtx98_v02") / relative
            target = STAGE / package_path
            if not target.resolve().is_relative_to(STAGE.resolve()):
                raise ValueError("Source destination escapes stage")
            content = archive.read(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            records.append({"path": package_path.as_posix(), "sha256": hashlib.sha256(content).hexdigest(),
                            "bytes": len(content), "archive_member": name})
    manifest = {"date": "2026-10-13", "source_commit": COMMIT, "source_path": SOURCE,
                "capsule_sha256": EXPECTED_SHA256, "capsule_bytes": len(data),
                "extraction_scope": "native/source only; preserves upstream license notices; no archived executable or DLL redistributed by this extraction",
                "native_source_file_count": len(records), "files": records}
    (ROOT / "review_access/NATIVE_SOURCE_EXTRACTION.json").write_text(json.dumps(manifest, indent=2) + "\n")
    row.update({"retrieval": "verified_native_capsule", "sha256": EXPECTED_SHA256,
                "local_capsule_path": "capsules/SOURCE_RUNTIME_V02.zip",
                "distribution": "Source subtree only, in separate native-source package; capsule binary is not in core ZIP"})
    (ROOT / "review_access/SOURCE_ACCESS_INVENTORY.json").write_text(json.dumps(inventory, indent=2) + "\n")
    print(f"Verified and extracted {len(records)} source files. No code was built or executed.")


if __name__ == "__main__":
    main()
