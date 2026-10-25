#!/usr/bin/env python3
"""Inventory explicitly selected files; SHA256 integrity is not native qualification."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import sys

SCOPE = "File integrity only; no GPU execution or native numerical qualification is inferred."
IDENTITY_FIELDS = ("source_commit", "build_identity", "model_identity", "device_identity")


def read_json(path):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("duplicate JSON key: " + key)
            value[key] = item
        return value
    def invalid(value):
        raise ValueError("non-finite JSON value: " + value)
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=pairs, parse_constant=invalid)


def resolve_file(root, name):
    """Accept portable relative paths; do not follow links outside the bundle."""
    if not isinstance(name, str) or not name:
        raise ValueError("file path must be a non-empty string")
    portable = name.replace("\\", "/")
    rel = PurePosixPath(portable)
    if rel.is_absolute() or PureWindowsPath(name).drive or ".." in rel.parts:
        raise ValueError("path must stay inside the bundle: " + name)
    if not rel.parts or rel == PurePosixPath("."):
        raise ValueError("select files, not the bundle root")
    base = Path(root).resolve(strict=True)
    if not base.is_dir():
        raise ValueError("bundle root is not a directory")
    target = base.joinpath(*rel.parts)
    try:
        target.resolve().relative_to(base)
    except ValueError as exc:
        raise ValueError("symlink or path escapes the bundle: " + name) from exc
    return rel.as_posix(), target


def file_identity(path):
    if not path.is_file():
        raise ValueError("selected path is not a regular file: " + str(path))
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            count += len(block)
            digest.update(block)
    return {"bytes": count, "sha256": digest.hexdigest()}


def create(root, includes, platform, output, identity=None):
    if platform not in ("rtx", "b570"):
        raise ValueError("platform must be rtx or b570")
    if not includes:
        raise ValueError("at least one explicit file is required")
    identity = {} if identity is None else identity
    if not isinstance(identity, dict):
        raise ValueError("identity JSON must be an object")
    files = {}
    for name in includes:
        rel, path = resolve_file(root, name)
        if rel in files:
            raise ValueError("duplicate selected path: " + rel)
        files[rel] = {"path": rel, **file_identity(path)}
    missing_identity = [key for key in IDENTITY_FIELDS if not identity.get(key)]
    manifest = {
        "schema": 1, "platform": platform, "scope": SCOPE,
        "native_qualification": "NOT_ASSESSED",
        "identity": identity,
        "identity_completeness": {
            "status": "PARTIAL" if missing_identity else "DECLARED",
            "recommended_fields_missing": missing_identity,
            "note": "Identity values are declarations, not independently verified by this tool."
        },
        "files": [files[key] for key in sorted(files)],
    }
    body = json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(body)
    return {"status": "CREATED", "platform": platform, "files": len(files),
            "identity_completeness": manifest["identity_completeness"],
            "scope": SCOPE, "native_qualification": "NOT_ASSESSED"}


def verify(root, manifest):
    if not isinstance(manifest, dict) or manifest.get("schema") != 1:
        raise ValueError("unsupported manifest schema")
    if manifest.get("platform") not in ("rtx", "b570"):
        raise ValueError("invalid platform")
    rows = manifest.get("files")
    if not isinstance(rows, list) or not rows:
        raise ValueError("manifest must select at least one file")
    seen, checked, missing, changed = set(), [], [], []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid file entry")
        rel, path = resolve_file(root, row.get("path"))
        if rel in seen:
            raise ValueError("duplicate manifest path: " + rel)
        seen.add(rel)
        expected_size, expected_hash = row.get("bytes"), row.get("sha256")
        if (type(expected_size) is not int or expected_size < 0 or
                not isinstance(expected_hash, str) or len(expected_hash) != 64 or
                any(c not in "0123456789abcdef" for c in expected_hash)):
            raise ValueError("invalid expected identity: " + rel)
        if not path.is_file():
            missing.append(rel)
            continue
        actual = file_identity(path)
        if actual["bytes"] != expected_size or actual["sha256"] != expected_hash:
            changed.append({"path": rel, "expected": {"bytes": expected_size,
                            "sha256": expected_hash}, "actual": actual})
        else:
            checked.append(rel)
    return {"status": "PASS" if not missing and not changed else "FAIL",
            "verified_files": checked, "missing": missing, "changed": changed,
            "platform": manifest["platform"], "scope": SCOPE,
            "native_qualification": "NOT_ASSESSED"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("create", help="create a new, explicit file inventory")
    build.add_argument("--root", required=True, type=Path)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--platform", required=True, choices=("rtx", "b570"))
    build.add_argument("--include", required=True, action="append", help="one file relative to root; repeat as needed")
    build.add_argument("--identity-json", type=Path)
    check = commands.add_parser("verify", help="verify selected files without writing")
    check.add_argument("--root", required=True, type=Path)
    check.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            identity = read_json(args.identity_json) if args.identity_json else {}
            result = create(args.root, args.include, args.platform, args.output, identity)
        else:
            result = verify(args.root, read_json(args.manifest))
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 1 if result["status"] == "FAIL" else 0
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc), "scope": SCOPE},
                         ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
