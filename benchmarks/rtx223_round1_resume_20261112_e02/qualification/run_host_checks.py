"""Record host-only tests in ordinary and optimized Python modes."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epoch", default="host-checks-v2")
    args = parser.parse_args()
    if not args.epoch.startswith("host-checks-") or not args.epoch.replace("-", "").isalnum():
        raise ValueError("invalid host check epoch")
    output = ROOT / "qualification" / args.epoch
    output.mkdir(exist_ok=False)
    records = []
    for mode, switches in (("normal", []), ("optimized", ["-O"])):
        argv = [sys.executable, *switches, "-m", "unittest", "discover", "-s", "tests", "-p", "test_admission.py", "-v"]
        result = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        (output / (mode + ".log")).write_bytes(result.stdout)
        records.append({"mode": mode, "argv": argv, "exit_code": result.returncode,
                        "log_sha256": hashlib.sha256(result.stdout).hexdigest()})
    sources = [ROOT / "src/admission.py", ROOT / "tests/test_admission.py", ROOT / "qualification/CASES.json",
               ROOT / "qualification/FALLBACK_ALLOWLIST.json", Path(__file__).resolve()]
    receipt = {"schema": "heterospec.rtx-round1.host-qualification.v1", "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "status": "PASS_HOST_ONLY" if all(x["exit_code"] == 0 for x in records) else "FAIL_HOST_ONLY",
               "python": sys.version, "checks": records,
               "source_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
               "native_qualification": "NOT_RUN", "model_requests": 0, "gpu_runs": 0,
               "scope": "Constructed CPU metadata/state fixtures and host guard logic only. No actual CUDA descriptor, model, loaded DLL or clean operator has been qualified by this receipt."}
    (output / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["status"] == "PASS_HOST_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
