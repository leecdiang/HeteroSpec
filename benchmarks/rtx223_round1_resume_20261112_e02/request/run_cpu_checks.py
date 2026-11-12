"""Retain CPU fixture, trace inspection and tests. No native model execution."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from state_machine import main_fixture, compare_requests
from inspect_old_traces import inspect


def main():
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / "cpu_result"
    output.mkdir(exist_ok=False)
    r = main_fixture()
    (output / "CONSTRUCTED_RAW.json").write_text(json.dumps(r, indent=2), encoding="utf8")
    comparison = compare_requests(r, json.loads(json.dumps(r)))
    structural = inspect(HERE.parents[1] / "q8rtx213-supplement-runtime-20261109/runs")
    (output / "OLD_TRACE_STRUCTURE.json").write_text(json.dumps(structural, indent=2), encoding="utf8")
    tests = []
    for optimized in (False, True):
        cmd = [sys.executable, "-B"] + (["-O"] if optimized else []) + ["-m", "unittest", "discover", "-s", str(HERE.parent / "tests"), "-p", "test_request*.py", "-v"]
        p = subprocess.run(cmd, capture_output=True, text=True, check=False)
        name = "tests_optimized.log" if optimized else "tests.log"
        (output / name).write_text(p.stdout + p.stderr, encoding="utf8")
        tests.append({"argv": cmd, "returncode": p.returncode, "log": name})
        if p.returncode:
            raise RuntimeError("request tests failed; retain logs")
    report = {"status": "CPU_PREPARATION_COMPLETE_NATIVE_REQUEST_NOT_RUN", "comparison": comparison,
              "test_runs": tests, "new_model_requests": 0, "native_GPU_launches": 0,
              "model_rows": 0, "fixture_is_native_KV": False, "real_chain_covered": False,
              "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}}
    (output / "RESULT.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
