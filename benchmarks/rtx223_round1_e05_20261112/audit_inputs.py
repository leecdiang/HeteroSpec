"""Read-only evidence audit. Run with Python -I -B -S; stdout is the receipt.

Argument: Windows workspace containing the e01/e02/e04 deliveries and repo/.
No image loading, SQLite, process launches other than git ls-tree, or native admission.
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HEAD = "7ce00b3c72ecf72adcd6d3832d78c3d359dbb6ac"
WORK = Path(sys.argv[1]).resolve(strict=True)
E04 = WORK / "rtx223-round1-resume-20261112-e04"
REMOTE = "benchmarks/rtx223_round1_e04_20261112"
checked = {}
inputs = {}
errors = []


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify(group, path, expected):
    path = Path(path)
    checked[group] = checked.get(group, 0) + 1
    if not path.is_file() or digest(path) != expected:
        errors.append({"group": group, "path": str(path)})


def bind(path, remote):
    data = path.read_bytes()
    oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    entry = subprocess.check_output(["git", "-C", str(WORK / "repo"), "ls-tree",
                                     HEAD, "--", remote]).decode().strip()
    if entry != f"100644 blob {oid}\t{remote}":
        raise ValueError(f"Cannot bind {remote} to pinned PR head")
    inputs[remote] = {"git_blob": oid, "sha256": hashlib.sha256(data).hexdigest()}


def read(rel):
    return json.loads((E04 / rel).read_bytes())


for rel in ("AGENTS.md", "e04/RESUME_REPORT_ZH.md", "e04/RESULT.json",
            "e04/budget/NATIVE_CLOSURE_REQUIREMENTS.md", "e04/budget/lifecycle_budget.py",
            "e04/budget/test_lifecycle_budget.py", "e04/budget/inspect_native_candidate.py",
            "e04/review/INDEPENDENT_REVIEW_ZH.md", "e04/review/FINAL_REVIEW.json",
            "e04/frontend/expected-modules-v1/MODULE_CLOSURE_v3.json",
            "runtime/build-v2/COMPILE_RECEIPTS.json", "e04/PRESERVATION_FINAL.json",
            "runtime/SOURCE_RECEIPT.json"):
    bind(E04 / rel, f"{REMOTE}/{rel}")
bind(WORK / "rtx221-round1-20261112/RESOURCE_PLAN.json",
     "benchmarks/rtx221_round1_20261112/RESOURCE_PLAN.json")
bind(WORK / "rtx223-round1-resume-20261112-e02/continuation/ORIGINAL_ROUND1_PROMPT.md",
     "benchmarks/rtx223_round1_resume_20261112_e02/continuation/ORIGINAL_ROUND1_PROMPT.md")
result = read("e04/RESULT.json")
for row in result["evidence"]:
    verify("e04_result_evidence", E04 / row["path"], row["sha256"])
for path, info in read("e04/freeze/v2/FREEZE.json")["inputs"].items():
    verify("frozen_inputs", path, info["sha256"])
source = E04 / "runtime/source-v1"
source_manifest = read("runtime/SOURCE_RECEIPT.json")["source_files_sha256"]
actual_members = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
if actual_members != {Path(p).as_posix() for p in source_manifest}:
    errors.append({"group": "source_membership", "actual": len(actual_members)})
for rel, expected in source_manifest.items():
    verify("source", source / rel, expected)
for row in read("runtime/build-v2/COMPILE_RECEIPTS.json"):
    for key in ("object", "dependency", "log"):
        verify(key, row[key], row[key + "_sha256"])
for mod in read("e04/frontend/expected-modules-v1/MODULE_CLOSURE_v3.json")["modules"].values():
    verify("staged_images", mod["path"], mod["sha256"])
verify("link_output", result["DLL"]["path"], result["DLL"]["sha256"])
for row in result["frontends"]:
    verify("frontend", row["exe"], row["sha256"])
for row in read("e04/PRESERVATION_FINAL.json")["ledgers"]:
    verify("old_ledger_file", row["path"], row["expected_sha256"])
print(json.dumps({"utc": datetime.now(timezone.utc).isoformat(), "head": HEAD,
                  "scope": "disk bytes only", "bound_inputs": inputs, "checked": checked,
                  "errors": errors, "pass": not errors}, indent=2))
sys.exit(bool(errors))
