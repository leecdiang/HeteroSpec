"""Retain a new immutable test epoch and own-worker raw safety fixtures."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
out = HERE / (sys.argv[1] if len(sys.argv) > 1 else "os-checks-v1")
out.mkdir(exist_ok=False)
result = []
for flags, name in (([], "normal"), (["-O"], "optimized")):
    argv = [sys.executable, "-B", *flags, "-m", "unittest", "discover", "-s", "tests", "-p", "test_windows_runner_os.py", "-v"]
    env = os.environ.copy()
    env["HS_SAFETY_KEEP_ROOT"] = str(out / "raw" / name)
    run = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    (out / (name + ".log")).write_bytes(run.stdout)
    count = re.findall(rb"Ran (\d+) tests?", run.stdout)
    result.append({"argv": argv, "returncode": run.returncode, "tests": int(count[-1]) if count else None,
                   "log_sha256": hashlib.sha256(run.stdout).hexdigest()})
receipt = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "kind": "REAL_WINDOWS_OS_CPU_FIXTURES_ONLY",
           "runs": result, "pass": all(r["returncode"] == 0 for r in result),
           "new_model_requests": 0, "new_target_draft_rows": 0, "new_GPU_kernel_launches": 0,
           "actual_GPU_lock_used": False, "namespace": "Global\\HeteroSpec-CPU-TEST-<unique UUID>",
           "native_gate": "BLOCKED_ORIGINAL_THREADS_UNVERIFIED",
           "sources": {"windows_runner.py": hashlib.sha256((HERE / "windows_runner.py").read_bytes()).hexdigest(),
                       "test_windows_runner_os.py": hashlib.sha256((ROOT / "tests/test_windows_runner_os.py").read_bytes()).hexdigest()}}
(out / "RECEIPT.json").write_text(json.dumps(receipt, indent=2), encoding="utf8")
print(json.dumps(receipt))
if not receipt["pass"]:
    raise SystemExit(1)
