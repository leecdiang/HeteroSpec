"""Static-only inspection of frozen build artifacts; never loads/executes them."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--task-root", type=Path, required=True)
    a = p.parse_args()
    root = a.task_root.resolve()
    target = root / "launcher-build-03/STATIC_IDENTITY.private.json"
    if target.exists():
        raise SystemExit("Retained static receipt already exists")
    items = [
        ("R", "native-bridge-build-01/R/n1a-native-not-admitted", "7bc87ec910740a2eb6b511f5e6e6f98ceac44ffd0563a5d1b2318633fc0dc235"),
        ("loop4", "native-bridge-build-01/loop4/n1a-native-not-admitted", "5d4b49bbba871655c5d6af24b32cb322faf171524f04648a9106c9d687e38981"),
        ("native_launcher", "launcher-build-03/native_bridge_launcher_NOT_ADMITTED", "b64b163ca5652f626affc1f1254c881f324a399041388e758f0b8735bc5b8eee"),
        ("CPU_launcher", "launcher-build-03/cpp_bridge_launcher", "770609a9fc019701a8252bbffc63f968b481789f34f4cbee7182b9344ca3290e"),
        ("CPU_worker", "cpp-build-02/cpp_fixed_worker", "8ea68312efbdcf00fbf0c5d58354055a741ea91c4ddb3d9406af18538f2f1295"),
    ]
    out = []
    for role, name, expected in items:
        artifact = root / name
        if sha(artifact) != expected:
            raise SystemExit("Identity changed: " + role)
        command = ["nm", "-C", "--defined-only", str(artifact)]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=60)
        log = root / ("launcher-build-03/static-" + role + "-symbols.log")
        if log.exists():
            raise SystemExit("Retained symbol log already exists")
        log.write_bytes(result.stdout)
        lines = result.stdout.decode().splitlines()
        needles = ["BridgeClient::", "BridgeJob::", "bridge_io(", "ProductionGate::", "supervise_bridge<", " main"]
        selected = {n: [line for line in lines if n in line][:3] for n in needles}
        out.append({"role": role, "path": name, "bytes": artifact.stat().st_size, "sha256": expected,
                    "symbols": selected, "complete_symbols": {"path": str(log.relative_to(root)), "bytes": log.stat().st_size, "sha256": sha(log)},
                    "native_executable_started_by_inspector": False})
    receipt = {"schema": "hs.production-bridge.static-artifact-identity.v1", "status": "STATIC_ONLY_NOT_NATIVE_QUALIFICATION",
               "artifacts": out, "native_executables_started": 0, "model_backend_context_placement_forward_calls": 0,
               "inspector_sha256": sha(__file__)}
    target.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "artifact_count": len(out), "native_executables_started": 0}))


if __name__ == "__main__":
    main()
