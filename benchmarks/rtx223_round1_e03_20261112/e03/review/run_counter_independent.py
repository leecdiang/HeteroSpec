"""New e03 counter CPU mocks only. Does not rerun inherited 41/18 suites."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "counter-independent-v1"


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    producer = ROOT / "e03/launch_budget/cpu-checks-v3"
    receipt = json.loads((producer / "RECEIPT.json").read_bytes())
    exe = producer / "launch_counter_cpu_mock.exe"
    need(sha(exe) == receipt["exe_sha256"], "CPU mock executable identity")
    for name, h in receipt["sources"].items():
        need(sha(producer / "source_snapshot" / name) == h, "CPU compiled source snapshot identity")
        need(sha(ROOT / "e03/launch_budget" / name) == h, "CPU canonical source changed")
    dumpbin = Path("D:/rtx184-tools/msvc/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/dumpbin.exe")
    imported = subprocess.run([str(dumpbin), "/imports", str(exe)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10)
    (OUT / "imports.log").write_bytes(imported.stdout)
    need(imported.returncode == 0 and not any(token in imported.stdout.lower() for token in (b"nvcuda", b"cudart", b"cublas")), "CPU mock imports CUDA")
    scenarios = ["unarmed", "invalid-limit", "boundary-4096", "multithread-4096", "two-TUs-one-state", "inherited-reservation", "failed-submission-no-refund", "prelaunch-order", "reconfigure-denied", "reentry-denied", "graph-replay-denied", "opaque-BLAS-denied", "opaque-CUB-denied", "zero-remaining", "failstop-unarmed", "failstop-opaque"]
    rows = []
    for scenario in scenarios:
        run = subprocess.run([str(exe), scenario], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10)
        log = OUT / (scenario + ".log")
        log.write_bytes(run.stdout)
        if scenario.startswith("failstop-"):
            expected = 0xE0330001 if scenario == "failstop-unarmed" else 0xE0330004
            passed = run.returncode in (expected, expected - 2**32) and b"UNSAFE_MOCK_DRIVER_EXECUTED" not in run.stdout and b"HeteroSpec" in run.stdout
            parsed = {"expected_own_process_exit_code": expected, "unreachable_mock_driver_marker_present": b"UNSAFE_MOCK_DRIVER_EXECUTED" in run.stdout}
        else:
            parsed = json.loads(run.stdout)
            passed = run.returncode == 0 and parsed["pass"] is True and parsed["CPU_MOCK_ONLY"] is True and parsed["actual_GPU_launches"] == 0
            if scenario in ("boundary-4096", "multithread-4096"):
                passed = passed and parsed["admitted_mock_attempts"] == 4096
            if scenario == "two-TUs-one-state":
                passed = passed and parsed["admitted_mock_attempts"] == 10
            if scenario in ("graph-replay-denied", "opaque-BLAS-denied", "opaque-CUB-denied"):
                passed = passed and parsed["mock_submissions"] == 0 and parsed["admitted_mock_attempts"] == 0
        rows.append({"scenario": scenario, "returncode": run.returncode, "passed": passed, "log_sha256": sha(log), "result": parsed})
    result = {"schema": "heterospec.e03.independent-counter-mocks.v1", "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "CPU_ONLY": True, "scenario_count": len(rows), "all_pass": all(r["passed"] for r in rows), "exe_sha256": sha(exe), "producer_receipt_sha256": sha(producer / "RECEIPT.json"), "compiled_sources": receipt["sources"], "imports_log_sha256": sha(OUT / "imports.log"), "results": rows, "actual_GPU_kernel_launches": 0, "models": 0, "old_41_or_18_suites_rerun": False, "scope": "Shared process CPU mock counter state, two translation units, thread/cap/no-reset and own-process failstop semantics only. Not dynamic physical CUDA-kernel coverage or a runnable model profile."}
    (OUT / "RECEIPT.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps({"scenario_count": len(rows), "all_pass": result["all_pass"], "actual_GPU_kernel_launches": 0, "failed": [r["scenario"] for r in rows if not r["passed"]]}, indent=2))
    need(result["all_pass"], "Independent counter CPU tests failed; retain all logs")


if __name__ == "__main__":
    main()
