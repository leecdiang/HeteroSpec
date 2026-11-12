"""Targeted independent Windows CPU safety checks; never runs a model/GPU."""
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
OUT = HERE / "safety-independent-v1"


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    sources = {str(p.relative_to(ROOT)): sha(p) for p in (ROOT / "continuation/safety/windows_runner.py", ROOT / "tests/test_windows_runner_os.py")}
    runs = []
    for flags, label in (([], "normal"), (["-O"], "optimized")):
        args = [sys.executable, "-B", *flags, "-m", "unittest", "discover", "-s", "tests", "-p", "test_windows_runner_os.py", "-v"]
        env = os.environ.copy()
        env["HS_SAFETY_KEEP_ROOT"] = str(OUT / "raw" / label)
        run = subprocess.run(args, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=45)
        log = OUT / (label + ".log")
        log.write_bytes(run.stdout)
        counts = re.findall(rb"Ran (\d+) tests", run.stdout)
        runs.append({"mode": label, "argv": args, "returncode": run.returncode, "tests": int(counts[-1]) if counts else None, "log_sha256": sha(log)})
    need(all(sha(ROOT / path) == h for path, h in sources.items()), "Safety sources changed during review")
    receipt = {"schema": "heterospec.e02.independent-windows-safety.v1", "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "source_sha256": sources, "test_runs": runs, "pass": all(r["returncode"] == 0 and r["tests"] == 18 for r in runs), "scope": "Own Windows CPU processes and synthetic CPU-TEST mutex names only", "actual_GPU_lock_used": False, "new_model_requests": 0, "new_target_draft_rows": 0, "new_GPU_kernel_launches": 0, "old_41_test_suite_rerun": False, "raw_counter_note": "The deliberate overrun fixture fabricates a launch counter of one in plain CPU Python. It is not a CUDA launch or study usage."}
    (OUT / "RECEIPT.json").write_text(json.dumps(receipt, indent=2), encoding="utf8")
    print(json.dumps(receipt, indent=2))
    need(receipt["pass"], "Independent safety tests failed; retain raw logs")


if __name__ == "__main__":
    main()
