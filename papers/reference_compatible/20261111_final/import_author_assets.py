#!/usr/bin/env python3
"""Idempotent, byte-exact import of the author-owned manuscript archive into PR220.

No GPU, network or user directories are touched; only one pinned paper subtree.
Run from the exact PR branch. --sync writes files, --commit-and-push also pushes
one ordinary fast-forward commit. Never force-push or merge this Draft PR.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import tempfile
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

ARCHIVE_SHA = "e56013eace463b0615cf69dd130155b90bd2a26385286029891904689084f78b"
BRANCH = "paper/recovery-final-20261111"
ROOT = Path("papers/reference_compatible/20261111_final")


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def run(archive: Path, repo: Path, mode: str):
    archive, repo = archive.resolve(), repo.resolve()
    if not archive.is_file() or digest(archive.read_bytes()) != ARCHIVE_SHA:
        raise RuntimeError("Author archive missing or SHA256 differs from the fixed release")
    if git(repo, "rev-parse", "--abbrev-ref", "HEAD") != BRANCH:
        raise RuntimeError(f"Checkout PR220 branch {BRANCH} first")
    if git(repo, "status", "--porcelain"):
        raise RuntimeError("Working tree must be clean before a source import")
    wanted: dict[Path, bytes] = {}
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or len(names) != 130:
            raise RuntimeError("Unexpected zip entries or duplicate file names")
        manifest = json.loads(z.read("PACKAGE_MANIFEST.json"))
        if set(manifest) != set(names) - {"PACKAGE_MANIFEST.json"}:
            raise RuntimeError("Package manifest is incomplete or was replaced")
        for name in names:
            parts = PurePosixPath(name)
            if not name or name.startswith("/") or "\\" in name or ".." in parts.parts:
                raise RuntimeError(f"Unsafe archive path {name!r}")
            data = z.read(name)
            if name in manifest:
                info = manifest[name]
                if len(data) != info["bytes"] or digest(data) != info["sha256"]:
                    raise RuntimeError(f"Bad member integrity for {name}")
            if name.startswith(("paper/", "validation/", "visual_review/")):
                relative = Path(name)
            else:
                # Root metadata already exists in the initial text-only PR;
                # copy its byte-exact author original into a distinct folder.
                relative = Path("author_archive_root") / name
            target = repo / ROOT / relative
            if not target.resolve().is_relative_to((repo / ROOT).resolve()):
                raise RuntimeError(f"Unsafe destination {name}")
            wanted[target] = data
    changed = 0
    for target, data in wanted.items():
        if target.exists():
            if not target.is_file() or target.is_symlink():
                raise RuntimeError(f"Unexpected local target {target}")
            if target.read_bytes() != data:
                raise RuntimeError(f"Existing file differs from pinned archive: {target}")
        else:
            changed += 1
    print(json.dumps({"expected_files": len(wanted), "already_identical": len(wanted)-changed,
                      "new_files": changed, "archive_sha256": ARCHIVE_SHA,
                      "mode": mode}, indent=2))
    if mode == "check":
        return
    for target, data in wanted.items():
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    for target, data in wanted.items():
        if target.read_bytes() != data:
            raise RuntimeError(f"Post-write mismatch: {target}")
    print("All 130 author archive entries are byte-identical in the paper subtree.")
    if mode == "sync":
        return
    # Build in an isolated checkout copy: reproducibility checks must not mutate
    # any of the 130 byte-exact files committed from the author ZIP.
    with tempfile.TemporaryDirectory(prefix="pr220-clean-build-") as scratch:
        built = Path(scratch) / "paper"
        shutil.copytree(repo / ROOT / "paper", built)
        subprocess.run(["bash", "build.sh"], cwd=built, check=True)
        for pdf in ("main.pdf", "journal.pdf"):
            if not (built / pdf).is_file():
                raise RuntimeError(f"Missing compiled {pdf}")
        print("Independent build completed without rewriting the committed sources")
    for target, data in wanted.items():
        if target.read_bytes() != data:
            raise RuntimeError(f"Reproducibility check changed source bytes: {target}")
    subprocess.run(["git", "-C", str(repo), "add", "--", str(ROOT)], check=True)
    staged = git(repo, "diff", "--cached", "--name-only")
    if not staged:
        print("All assets already committed; no push needed")
        return
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "docs(paper): import byte-exact full 2026-11-11 author source and assets"], check=True)
    subprocess.run(["git", "-C", str(repo), "push", "origin", f"HEAD:{BRANCH}"], check=True)
    print("Fast-forward push finished. Read back the PR tree and keep it Draft.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--mode", choices=("check", "sync", "commit-and-push"), default="check")
    args = ap.parse_args()
    run(args.archive, args.repo, args.mode)
