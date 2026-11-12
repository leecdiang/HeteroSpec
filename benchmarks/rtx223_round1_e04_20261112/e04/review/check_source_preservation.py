"""Read-only rehash of unexported old numerical source trees, no tests."""
import datetime
import hashlib
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OLD = ROOT.parent / "rtx223-round1-resume-20261112-e03"


def sha(path):
    p = str(pathlib.Path(path).resolve())
    if os.name == "nt" and not p.startswith("\\\\?\\"):
        p = "\\\\?\\" + p
    h = hashlib.sha256()
    with open(p, "rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


prep = json.loads((OLD / "runtime/SOURCE_PREPARED.json").read_text(encoding="utf-8"))
final = json.loads((OLD / "runtime/FINAL_SOURCE_IDENTITIES.json").read_text(encoding="utf-8"))
records = []
for label, root, entries in [
    ("original_numerical_core", pathlib.Path(prep["old_root"]), prep["old_source_sha256"]),
    ("e03_uniform_source", OLD / "runtime/final-source", final["source_files_sha256"]),
]:
    bad = [rel for rel, digest in entries.items() if sha(root / rel) != digest]
    records.append({"label": label, "root": str(root), "members": len(entries), "mismatches": bad})
receipt = {"schema": "heterospec.e04.independent-old-source-preservation.v1",
           "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "trees": records, "passed": not any(x["mismatches"] for x in records),
           "old_writes": 0, "tests_or_native_runs": 0,
           "script_sha256": sha(__file__)}
out = pathlib.Path(__file__).resolve().parent / "SOURCE_PRESERVATION_FINAL.json"
if out.exists():
    raise ValueError("Refuse replacing preservation receipt")
out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": receipt["passed"], "members": [x["members"] for x in records]}))
raise SystemExit(not receipt["passed"])
