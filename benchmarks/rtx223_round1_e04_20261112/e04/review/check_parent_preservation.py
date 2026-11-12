"""Read-only independent e03 preservation receipt; never imports project code."""
import datetime
import hashlib
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PARENT = ROOT.parent / "rtx223-round1-resume-20261112-e03"


def read_bytes(path):
    path = str(pathlib.Path(path).resolve())
    if os.name == "nt" and not path.startswith("\\\\?\\"):
        path = "\\\\?\\" + path
    with open(path, "rb") as stream:
        return stream.read()


manifest_path = PARENT / "delivery/DELIVERY_MANIFEST.json"
manifest_bytes = read_bytes(manifest_path)
manifest = json.loads(manifest_bytes)
binding = json.loads(read_bytes(ROOT / "e04/PARENT_BINDING.json"))
bad = []
if hashlib.sha256(manifest_bytes).hexdigest() != binding["e03_manifest_sha256"]:
    bad.append({"path": "delivery/DELIVERY_MANIFEST.json", "reason": "manifest changed"})
for item in manifest["files"]:
    path = PARENT / item["path"]
    try:
        if os.path.commonpath((str(path.resolve()), str(PARENT.resolve()))) != str(PARENT.resolve()):
            raise ValueError("manifest member leaves parent root")
        raw = read_bytes(path)
        digest = hashlib.sha256(raw).hexdigest()
        git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if len(raw) != item["bytes"] or digest != item["sha256"] or git_blob != item["git_blob"]:
            bad.append({"path": item["path"], "reason": "bytes/SHA256/git-blob mismatch"})
    except (OSError, ValueError) as exc:
        bad.append({"path": item["path"], "reason": type(exc).__name__})
receipt = {
    "schema": "heterospec.e04.independent-parent-preservation.v1",
    "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "parent": str(PARENT), "parent_head_bound": binding["parent_head"],
    "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
    "members_checked": len(manifest["files"]), "checks": ["bytes", "SHA256", "git_blob_SHA1"],
    "mismatches": bad, "passed": len(manifest["files"]) == 1749 and not bad,
    "old_source_or_ledger_writes": 0, "tests_rerun": 0,
    "CUDA_calls": 0, "model_requests": 0,
    "script_sha256": hashlib.sha256(read_bytes(__file__)).hexdigest(),
}
name = sys.argv[1] if len(sys.argv) > 1 else "PARENT_PRESERVATION_INITIAL.json"
out = pathlib.Path(__file__).resolve().parent / name
if out.exists():
    raise ValueError("Refuse to overwrite a preservation receipt")
out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": receipt["passed"], "members": receipt["members_checked"],
                  "mismatches": bad, "receipt": str(out)}))
raise SystemExit(not receipt["passed"])
