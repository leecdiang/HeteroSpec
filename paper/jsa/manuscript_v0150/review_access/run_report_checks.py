#!/usr/bin/env python3
"""Run offline report checks in a temporary copy; never execute experiment scripts."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent
subprocess.run([sys.executable, str(root / "verify_review_package.py")], check=True)
source = root / "evidence/rtx98/benchmarks/rtx_querylayout_mechanism_v1/RESULTS.json"
raw = source.read_bytes()
report = json.loads(raw)
extract = json.loads((root / "paper/data/rtx_repair_report_extract.json").read_text())
assert hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest() == extract["source_blob_sha"]
assert hashlib.sha256(raw).hexdigest() == extract["source_sha256"]
for row in extract["comparisons"]:
    family = "Qwen" if row["family"] == "Qwen3" else row["family"]
    candidates = [r for r in report["families"][family]["comparisons"] if r["pair"] == row["pair"]]
    assert len(candidates) == 1
    for key, value in row.items():
        if key != "family":
            assert candidates[0][key] == value, (family, row["pair"], key)
print("PASS: all 21 extracted comparisons match the included fixed-commit PR98 report.")
with tempfile.TemporaryDirectory(prefix="jsa-report-check-") as temporary:
    paper = Path(temporary) / "paper"
    shutil.copytree(root / "paper", paper)
    for script in ("check_reported_data.py", "check_supplement_figures.py"):
        subprocess.run([sys.executable, str(paper / "scripts" / script)], cwd=paper, check=True)
print("PASS: offline report/figure checks. No native-record audit or GPU experiment was run.")
