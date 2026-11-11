#!/usr/bin/env python3
"""Verify the extracted core or native-source review package without network access."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / "PACKAGE_CHECKSUMS.json").read_text())
for relative, expected in manifest["files"].items():
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit(f"Unsafe path: {relative}")
    target = root / path
    if target.is_symlink() or not target.is_file():
        raise SystemExit(f"Missing or nonregular file: {relative}")
    data = target.read_bytes()
    if len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
        raise SystemExit(f"Integrity mismatch: {relative}")
print(f"PASS: {len(manifest['files'])} files match the delivered manifest.")
print("This verifies file integrity, not scientific validity or sharing rights.")
