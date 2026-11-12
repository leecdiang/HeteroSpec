"""One final host-only suite; no imports of model or CUDA executors."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
import sys

root = Path(__file__).resolve().parent
out = root / "delivery/final-checks"
out.mkdir(parents=True, exist_ok=False)
tests = []
for mode in ([], ["-O"]):
    command = [sys.executable, "-B", *mode, "-m", "unittest", "discover", "-s", "tests", "-v"]
    r = subprocess.run(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    path = out / ("optimized.log" if mode else "normal.log")
    path.write_bytes(r.stdout)
    counts = re.findall(rb"Ran (\d+) tests?", r.stdout)
    tests.append({"argv": command, "returncode": r.returncode, "tests": int(counts[-1]) if counts else None,
                  "log": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(r.stdout).hexdigest()})
receipt = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "status": "PASS" if all(t["returncode"] == 0 for t in tests) else "FAIL",
           "test_runs": tests, "model_requests": 0, "GPU_launches": 0,
           "critical_sources": {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [*sorted((root / "src").glob("*.py")), root / "request/costs.py", root / "native/operator_probe.cu", root / "native/two_group_q8.cuh"]}}
(out / "RECEIPT.json").write_text(json.dumps(receipt, indent=2), encoding="utf8")
print(json.dumps(receipt))
if receipt["status"] != "PASS":
    raise SystemExit(1)
