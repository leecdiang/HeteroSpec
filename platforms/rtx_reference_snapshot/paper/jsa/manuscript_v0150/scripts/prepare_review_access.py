#!/usr/bin/env python3
"""Stage fixed GitHub sources for author review; never publish or run experiments.

The default inventory mode only reads Git trees. --fetch retrieves report/source
text. GitHub CLI authentication belongs to the author, never to a reviewer.
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "review_access/source_selection.json"
STAGE = ROOT / "output/review_access_stage"


def api(endpoint: str) -> dict:
    for attempt in range(3):
        result = subprocess.run(["gh", "api", endpoint],
                                capture_output=True, timeout=180)
        if result.returncode == 0:
            return json.loads(result.stdout)
        if attempt < 2:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"GitHub retrieval failed after three attempts: {endpoint}")


def classification(path: str) -> str:
    parts = Path(path).parts
    if any(p in {"raw", "archive", "cas"} for p in parts):
        return "raw_or_archive_not_fetched"
    if re.search(r"\.(part|chunk)\d+$", path) or Path(path).suffix.lower() in {
            ".zip", ".gz", ".tgz", ".zst", ".bin", ".gguf", ".so", ".dll", ".exe"}:
        return "binary_or_archive_not_fetched"
    return "report_or_source_text"


def safe_path(relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Unsafe source path")
    return STAGE / path


def fetch_file(row: dict, repo: str) -> dict:
    dest = safe_path(row["package_path"])
    if dest.exists():
        data = dest.read_bytes()
    else:
        try:
            blob = api(f"repos/{repo}/git/blobs/{row['git_blob_sha1']}")
        except (RuntimeError, subprocess.TimeoutExpired):
            return {**row, "retrieval": "failed_retry_required"}
        if blob.get("encoding") != "base64":
            raise ValueError(f"Unexpected blob encoding: {row['path']}")
        data = base64.b64decode(blob["content"])
    digest = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
    if digest != row["git_blob_sha1"] or len(data) != row["bytes"]:
        raise ValueError(f"Source integrity mismatch: {row['path']}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return {**row, "retrieval": "verified_local", "sha256": hashlib.sha256(data).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text())
    repo = config["repository"]
    STAGE.mkdir(parents=True, exist_ok=True)
    cache = STAGE / "tree_cache"
    cache.mkdir(exist_ok=True)
    rows = []
    for campaign in config["campaigns"]:
        commit = campaign["commit"]
        cached = cache / f"{commit}.json"
        if cached.exists():
            tree = json.loads(cached.read_text())
        else:
            tree = api(f"repos/{repo}/git/trees/{commit}?recursive=1")
            cached.write_text(json.dumps(tree))
        if tree.get("truncated"):
            raise ValueError(f"Incomplete source tree: {commit}")
        selected = [f for f in tree["tree"] if f["type"] == "blob" and
                    any(f["path"].startswith(p) for p in campaign["prefixes"])]
        if not selected:
            raise ValueError(f"No selected sources: {campaign['id']}")
        for item in selected:
            path = item["path"]
            rows.append({"campaign": campaign["id"], "commit": commit,
                         "path": path, "bytes": item["size"],
                         "git_blob_sha1": item["sha"],
                         "source_url": f"https://github.com/{repo}/blob/{commit}/{path}",
                         "package_path": f"evidence/{campaign['id']}/{path}",
                         "class": classification(path), "retrieval": "not_fetched"})
        print(f"Inventoried {campaign['id']}: {len(selected)} files", flush=True)
    if args.fetch:
        wanted = [r for r in rows if r["class"] == "report_or_source_text"]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda r: fetch_file(r, repo), wanted))
        found = {(r["campaign"], r["path"]): r for r in results}
        rows = [found.get((r["campaign"], r["path"]), r) for r in rows]
    inventory = {"schema": 1, "date": config["date"],
                 "manuscript_version": config["manuscript_version"],
                 "repository_visibility": "private_checked_2026-10-13",
                 "status": "LOCAL_AUTHOR_STAGING_NOT_PUBLISHED",
                 "scope": config["selection"], "files": rows}
    target = ROOT / "review_access/SOURCE_ACCESS_INVENTORY.json"
    target.write_text(json.dumps(inventory, indent=2) + "\n")
    fetched = [r for r in rows if r["retrieval"] == "verified_local"]
    print(f"Verified local: {len(fetched)} files, {sum(r['bytes'] for r in fetched)} bytes")
    print(f"Inventoried only: {len(rows) - len(fetched)} files")
    failures = [r for r in rows if r["retrieval"] == "failed_retry_required"]
    if failures:
        print(f"RETRY REQUIRED: {len(failures)} source files; rerun --fetch.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
