from __future__ import annotations

import os

import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
STAMP = "20260907"
ARCHIVES = ROOT / "archives"
SNAPSHOT = ARCHIVES / f"HeteroSpec-PC_5070Ti_closed_{STAMP}"
ZIP_PATH = ARCHIVES / f"HeteroSpec-PC_5070Ti_closed_{STAMP}.zip"

INCLUDE_TREES = ("reports", "scripts", "env", "logs", "datasets", "runs", "spec", "analysis")
ROOT_FILES = ("system_profile.json",)
TELEMETRY_LIGHTWEIGHT_SUFFIXES = {".csv", ".md", ".txt"}
EXTERNAL_LARGE_THRESHOLD = 100 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_file(source: Path, relative: Path, records: list[dict]) -> None:
    destination = SNAPSHOT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    records.append(
        {
            "path": relative.as_posix(),
            "size_bytes": destination.stat().st_size,
            "sha256": sha256(destination),
        }
    )


def main() -> None:
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    if SNAPSHOT.exists():
        shutil.rmtree(SNAPSHOT)
    SNAPSHOT.mkdir()

    records: list[dict] = []
    for name in ROOT_FILES:
        source = ROOT / name
        if source.is_file():
            copy_file(source, Path(name), records)

    for tree_name in INCLUDE_TREES:
        tree = ROOT / tree_name
        if not tree.exists():
            continue
        for source in sorted(path for path in tree.rglob("*") if path.is_file()):
            copy_file(source, source.relative_to(ROOT), records)

    telemetry = ROOT / "telemetry"
    if telemetry.exists():
        for source in sorted(path for path in telemetry.rglob("*") if path.is_file()):
            if source.suffix.lower() in TELEMETRY_LIGHTWEIGHT_SUFFIXES:
                copy_file(source, source.relative_to(ROOT), records)

    external_assets: list[dict] = []
    if telemetry.exists():
        for source in sorted(path for path in telemetry.rglob("*") if path.is_file()):
            if source.stat().st_size >= EXTERNAL_LARGE_THRESHOLD:
                external_assets.append(
                    {
                        "path": str(source),
                        "role": "large_raw_telemetry_retained_in_place",
                        "size_bytes": source.stat().st_size,
                        "sha256": sha256(source),
                    }
                )

    external_assets.extend(
        [
            {
                "path": str(ROOT / "models"),
                "role": "model_weights_excluded; use env/qwen3-8b-manifest.json and env/qwen3-14b-manifest.json",
                "size_bytes": sum(p.stat().st_size for p in (ROOT / "models").rglob("*") if p.is_file()),
            },
            {
                "path": str(ROOT / ".venv-target"),
                "role": "virtual_environment_excluded; use env/target-pip-freeze.txt",
            },
            {
                "path": str(ROOT / ".venv-intel"),
                "role": "virtual_environment_excluded; use env/intel-pip-freeze.txt",
            },
            {
                "path": str(ROOT / ".venv-npu-lab"),
                "role": "qualification_virtual_environment_excluded; qualification outputs are included",
            },
        ]
    )

    external_path = SNAPSHOT / "EXTERNAL_ASSETS.json"
    external_path.write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "note": "These assets are intentionally not embedded in the portable ZIP.",
                "assets": external_assets,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    records.append(
        {
            "path": "EXTERNAL_ASSETS.json",
            "size_bytes": external_path.stat().st_size,
            "sha256": sha256(external_path),
        }
    )

    readme = SNAPSHOT / "README_ARCHIVE.md"
    readme.write_text(
        "# HeteroSpec-PC stage snapshot\n\n"
        "This is the portable evidence snapshot for the speculative-decoding branch closed on 2026-09-06.\n\n"
        "Start with `reports/HETEROSPEC_PC_FINAL_STAGE_REPORT.md`. The archive includes reports, scripts, "
        "environment freezes/manifests, logs, lightweight telemetry, datasets, run metadata, and the platform profile.\n\n"
        "Model weights, virtual environments, and raw telemetry files over 100 MiB are not duplicated. "
        "Their locations and reproducibility references are recorded in `EXTERNAL_ASSETS.json`.\n"
        "The 420-question holdout was not opened, and this snapshot does not authorize Phase 1 or a new benchmark branch.\n",
        encoding="utf-8",
    )
    records.append(
        {
            "path": "README_ARCHIVE.md",
            "size_bytes": readme.stat().st_size,
            "sha256": sha256(readme),
        }
    )

    records.sort(key=lambda item: item["path"])
    manifest = SNAPSHOT / "ARCHIVE_MANIFEST.json"
    manifest.write_text(
        json.dumps(
            {
                "archive_name": ZIP_PATH.name,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source_root": str(ROOT),
                "file_count_excluding_manifest": len(records),
                "files": records,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for source in sorted(path for path in SNAPSHOT.rglob("*") if path.is_file()):
            archive.write(source, source.relative_to(SNAPSHOT.parent))

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP integrity failure at {bad}")

    zip_hash = sha256(ZIP_PATH)
    checksum = ARCHIVES / f"{ZIP_PATH.name}.sha256"
    checksum.write_text(f"{zip_hash}  {ZIP_PATH.name}\n", encoding="ascii")
    print(
        json.dumps(
            {
                "snapshot": str(SNAPSHOT),
                "zip": str(ZIP_PATH),
                "zip_size_bytes": ZIP_PATH.stat().st_size,
                "zip_sha256": zip_hash,
                "checksum": str(checksum),
                "manifest_files": len(records),
                "external_assets": len(external_assets),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
