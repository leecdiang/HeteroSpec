"""Verify a relocated B570 delivery and replay archived CPU audits only."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys

SOURCE_ARCHIVE_SHA256 = "78abc364729fed7ba0f8b92cf3594eed2511df181714e9f53b19ede2a4465973"
SOURCE_ARCHIVE_BYTES = 1367643308
SOURCE_MANIFEST_SHA256 = "94f748a6c6e38ae8e958a948b03f75d2db0947d7ad455682bc4aadd6f22148bb"
PROVENANCE_FILES = {"provenance/ORIGINAL_MANIFEST.json", "provenance/SOURCE_ARCHIVE.json"}
INPUT_IDS = ["HumanEval/38", "HumanEval/65", "HumanEval/115", "HumanEval/127"]
VECTOR_COUNTS = [258, 223, 175, 258]
OUTPUT_LENGTHS = [64, 53, 41, 64]
STOP_REASONS = ["CAP", "EOG", "EOG", "CAP"]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            check(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("Non-finite JSON constant: " + value)

    return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                      object_pairs_hook=pairs, parse_constant=invalid)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def portable_path(value):
    check(isinstance(value, str) and bool(value), "Invalid member path")
    check("\\" not in value and ":" not in value and "\x00" not in value,
          "Non-portable member path: " + value)
    path = PurePosixPath(value)
    check(bool(path.parts) and not path.is_absolute() and path.as_posix() == value and
          all(part not in (".", "..") and not part.endswith((" ", ".")) for part in path.parts),
          "Unsafe member path: " + value)
    return value


def rows_by_path(rows):
    check(isinstance(rows, list) and bool(rows), "Missing file inventory")
    result, aliases = {}, set()
    for row in rows:
        check(isinstance(row, dict), "Invalid file inventory row")
        name = portable_path(row.get("path"))
        check(name.casefold() not in aliases, "Duplicate/aliased member: " + name)
        aliases.add(name.casefold())
        size, sha = row.get("bytes"), row.get("sha256")
        check(type(size) is int and size >= 0, "Invalid byte size: " + name)
        check(isinstance(sha, str) and len(sha) == 64 and
              all(c in "0123456789abcdef" for c in sha), "Invalid SHA256: " + name)
        result[name] = row
    return result


def is_link(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def inventory(root):
    found = set()
    for directory, directories, files in os.walk(root, followlinks=False):
        base = Path(directory)
        for name in directories + files:
            path = base / name
            check(not is_link(path), "Links/reparse points are not package members: " + str(path))
            check(path.resolve(strict=True).is_relative_to(root), "Member escapes root: " + str(path))
        for name in files:
            path = base / name
            check(stat.S_ISREG(path.stat().st_mode), "Non-regular member: " + str(path))
            found.add(portable_path(path.relative_to(root).as_posix()))
    return found


def required_original_members(original, kind):
    if kind == "minimal":
        prefixes = ("kit/", "fixture/", "references/qual-2/",
                    "evidence/capture-a2/", "evidence/stage-a1/")
        return {name for name in original if name.startswith(prefixes) or
                name in {"upstream.tar.gz", "bundle_manifest.py"}}
    return {name for name in original if name.startswith("references/") or
            name in {"kit/audit_request.py", "kit/INPUT_PANEL.json"}}


def verify_integrity(root):
    root = Path(root).resolve(strict=True)
    check(root.is_dir(), "Package root is not a directory")
    actual = inventory(root)
    check("manifest.json" in actual, "Missing manifest.json")
    manifest = read_json(root / "manifest.json")
    check(isinstance(manifest, dict), "Manifest must be an object")
    check(type(manifest.get("schema")) is int and manifest["schema"] == 1, "Unsupported schema")
    check(manifest.get("platform") == "b570", "Wrong platform")
    kind = manifest.get("package_kind")
    check(kind in ("minimal", "four_input_references"), "Unsupported package kind")
    rows = rows_by_path(manifest.get("files"))
    check("manifest.json" not in rows, "Manifest must not inventory itself")
    missing, extra = set(rows) - actual, actual - set(rows) - {"manifest.json"}
    check(not missing and not extra,
          "Inventory mismatch; missing=" + repr(sorted(missing)) + "; extra=" + repr(sorted(extra)))
    check(PROVENANCE_FILES.issubset(rows), "Missing provenance files")
    for name, row in rows.items():
        path = root / name
        check(path.stat().st_size == row["bytes"] and digest(path) == row["sha256"],
              "Member integrity mismatch: " + name)
    check(manifest.get("source_archive_sha256") == SOURCE_ARCHIVE_SHA256,
          "Wrong original archive identity")
    check(manifest.get("source_manifest_sha256") == SOURCE_MANIFEST_SHA256 and
          digest(root / "provenance/ORIGINAL_MANIFEST.json") == SOURCE_MANIFEST_SHA256,
          "Wrong original manifest identity")
    source = read_json(root / "provenance/SOURCE_ARCHIVE.json")
    check(isinstance(source, dict), "SOURCE_ARCHIVE provenance must be an object")
    check(source.get("archive_sha256") == SOURCE_ARCHIVE_SHA256 and
          type(source.get("archive_bytes")) is int and source["archive_bytes"] == SOURCE_ARCHIVE_BYTES,
          "Wrong SOURCE_ARCHIVE provenance")
    original_manifest = read_json(root / "provenance/ORIGINAL_MANIFEST.json")
    check(original_manifest.get("schema") == 1 and original_manifest.get("platform") == "b570",
          "Wrong original manifest schema/platform")
    original = rows_by_path(original_manifest.get("files"))
    required = required_original_members(original, kind)
    check(required.issubset(rows), "Missing required original members: " + repr(sorted(required - set(rows))))
    origins = []
    for name, row in rows.items():
        origin = row.get("origin_member")
        if origin is None:
            check(name in PROVENANCE_FILES or name.startswith("delivery/"),
                  "Original member lacks provenance: " + name)
            continue
        origin = portable_path(origin)
        check(origin in original, "Unknown original member: " + origin)
        check(row["bytes"] == original[origin]["bytes"] and row["sha256"] == original[origin]["sha256"],
              "Original member identity mismatch: " + name)
        check(name == origin and name in required, "Unexpected/remapped original member: " + name)
        origins.append(origin)
    check(set(origins) == required and len(origins) == len(required), "Original-member coverage mismatch")
    return {"status": "PASS", "package_kind": kind, "verified_files": len(rows),
            "verified_original_members": len(origins), "total_bytes": sum(x["bytes"] for x in rows.values()),
            "manifest_sha256": digest(root / "manifest.json"), "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
            "source_manifest_sha256": SOURCE_MANIFEST_SHA256}


def load_auditor(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    check(spec is not None and spec.loader is not None, "Cannot load pinned CPU auditor")
    module = importlib.util.module_from_spec(spec)
    before = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = before
    return module


def without_paths(value, names):
    # The original auditor uses tuples for shapes; archived JSON stores arrays.
    return json.loads(json.dumps({key: item for key, item in value.items() if key not in names},
                                 allow_nan=False))


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def verify_input_binding(root, index, request_root):
    panel = read_json(root / "kit/INPUT_PANEL.json")["inputs"]
    check(len(panel) == 4 and [x["id"] for x in panel] == INPUT_IDS, "Fixed input panel changed")
    current = panel[index]
    native = read_json(request_root / "result.json")
    check(native["index"] == index and native["mode"] == "qual", "Request index/mode mismatch")
    check(len(native["requests"]) == 3, "Incomplete R/PQ/QB triplet")
    for arm, result in zip(("R", "PQ", "QB"), native["requests"]):
        check(result["arm"] == arm and result["input_id"] == current["id"], "Request input/arm binding")
        check(result["length"] == OUTPUT_LENGTHS[index] and result["length"] <= current["cap"] and
              result["stop_reason"] == STOP_REASONS[index], "Historical endpoint contract")
    for arm_index in (1, 2):
        result = native["requests"][arm_index]
        first = result["cycles"][0]
        check(first["base"] == len(current["prompt_ids"]), "Prompt length/first cycle binding")
        paths = sorted((request_root / f"qual-{arm_index}/target").glob("decode-*.json"),
                       key=lambda path: int(path.stem.split("-")[1]))
        check(bool(paths), "Missing first verification decode")
        decoded = read_json(paths[0])
        check(decoded["pos"] == first["base"] and decoded["input_ids"] == first["batch_ids"],
              "First decode/cycle binding")


def run_cpu_audits(root, out, kind):
    auditor = load_auditor(root / "kit/audit_request.py", "b570_pinned_request_auditor")
    if kind == "four_input_references":
        results = []
        for index in range(4):
            reference = root / f"references/qual-{index}"
            verify_input_binding(root, index, reference)
            result = auditor.audit(reference, reference)
            check(result["status"] == "HISTORICAL_REQUEST_REPLAY_PASS" and
                  result["full_vector_count"] == VECTOR_COUNTS[index], "Reference triplet audit failed")
            write_json(out / f"reference-{index}.json", result)
            results.append(result)
        check(sum(x["full_vector_count"] for x in results) == 914, "Four-input vector count")
        return {"status": "PASS", "reference_inputs": INPUT_IDS, "full_vector_count": 914,
                "audit_mode": "Authenticated reference bytes and internal R/PQ/QB consistency; no new model outputs"}

    actual, reference = root / "evidence/capture-a2", root / "references/qual-2"
    verify_input_binding(root, 2, actual)
    verify_input_binding(root, 2, reference)
    request = auditor.audit(actual, reference)
    check(request["status"] == "HISTORICAL_REQUEST_REPLAY_PASS" and request["full_vector_count"] == 175,
          "Natural request audit failed")
    expected_request = read_json(root / "kit/receipts/CAPTURE_A2_AUDIT.json")
    check(without_paths(request, {"actual", "reference"}) ==
          without_paths(expected_request, {"actual", "reference"}), "Historical request scientific fields differ")
    write_json(out / "request.json", request)
    stage = load_auditor(root / "kit/audit_stage.py", "b570_pinned_stage_auditor")
    before = sys.argv
    try:
        sys.argv = [str(root / "kit/audit_stage.py"), "--fixture", str(root / "fixture"),
                    "--request", str(actual), "--replay", str(root / "evidence/stage-a1"),
                    "--out", str(out / "stage.json")]
        with contextlib.redirect_stdout(io.StringIO()):
            stage.main()
    finally:
        sys.argv = before
    stage_result = read_json(out / "stage.json")
    check(stage_result["status"] == "REAL_STAGE_REPLAY_AUDIT_PASS" and
          stage_result["comparisons_passed"] == 16, "Stage audit failed")
    expected_stage = read_json(root / "kit/receipts/STAGE_AUDIT.json")
    ignored = {"request", "fixture", "replay"}
    check(without_paths(stage_result, ignored) == without_paths(expected_stage, ignored),
          "Historical stage scientific fields differ")
    return {"status": "PASS", "full_vector_count": 175, "stage_comparisons": 16,
            "visible_keys": stage_result["visible_keys"], "historical_scientific_fields_equal": True,
            "excluded_path_fields": {"request": ["actual", "reference"], "stage": sorted(ignored)}}


def verify_package(root, out):
    root = Path(root).resolve(strict=True)
    out = Path(out).resolve(strict=False)
    check(not out.exists(), "Output directory already exists")
    check(not out.is_relative_to(root), "Output directory must be outside package root")
    out.mkdir(parents=False)
    try:
        integrity = verify_integrity(root)
        audits = run_cpu_audits(root, out, integrity["package_kind"])
        result = {"status": "PASS", "root": str(root), "integrity": integrity, "cpu_audits": audits,
                  "gpu_requests": 0, "native_executables_started": 0,
                  "scope": "Package identity and existing archived numerical evidence; no new native qualification or timing"}
        write_json(out / "VERIFY_PACKAGE.json", result)
        return result
    except Exception as error:
        write_json(out / "VERIFY_PACKAGE.json", {"status": "FAIL", "root": str(root),
                   "error": str(error), "gpu_requests": 0, "native_executables_started": 0})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="New output directory outside the package")
    args = parser.parse_args(argv)
    try:
        result = verify_package(args.root, args.out)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
