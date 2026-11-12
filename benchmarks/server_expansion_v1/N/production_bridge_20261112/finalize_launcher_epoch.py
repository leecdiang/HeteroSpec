"""Hash-only finalization of the retained launcher03 build and CPU test logs.

This does not build or execute anything. The original runner rejected a relative
fixture path; the retained fixed CPU test was then run with an absolute path.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.task_root.resolve()
    out = root / "launcher-build-03"
    source = root / "launcher-source-03/benchmarks/server_expansion_v1/N/production_bridge_20261112"
    target = out / "BUILD.private.json"
    if target.exists():
        raise SystemExit("Do not overwrite a retained build receipt")
    pins = {
        "cpp_bridge_launcher": "770609a9fc019701a8252bbffc63f968b481789f34f4cbee7182b9344ca3290e",
        "native_bridge_launcher_NOT_ADMITTED": "b64b163ca5652f626affc1f1254c881f324a399041388e758f0b8735bc5b8eee",
        "cpu_supervisor_boundary": "7f7e84e1a714966bd48c30dacbbaf4740e679596221344ed28f464c99ed24f69",
    }
    artifacts = {}
    for name, expected in pins.items():
        path = out / name
        if sha(path) != expected:
            raise SystemExit("Artifact identity mismatch: " + name)
        artifacts[name] = {"bytes": path.stat().st_size, "sha256": expected,
                           "executed": name == "cpu_supervisor_boundary"}
    needed = {}
    for role in ["CPU", "NATIVE", "BOUNDARY"]:
        libs = re.findall(r"Shared library: \[([^]]+)\]", (out / (role + "-readelf.log")).read_text())
        if not libs or set(libs) - {"libstdc++.so.6", "libgcc_s.so.1", "libc.so.6", "libm.so.6"}:
            raise SystemExit("Unexpected retained dynamic dependencies")
        needed[role] = libs
    initial = (out / "BOUNDARY-test.log").read_text()
    if initial.strip() != "CPU_BOUNDARY_FAIL fresh absolute boundary fixture root required":
        raise SystemExit("Initial safe-rejection log differs")
    summary = json.loads((out / "BOUNDARY-test-02.log").read_text())
    if summary != {"status": "CPU_SUPERVISOR_BOUNDARY_PASS", "tests": 4,
                   "native_model_context_placement_forward_calls": 0}:
        raise SystemExit("Boundary result mismatch")
    native = json.loads((root / "native-bridge-build-01/BRIDGE_BUILD.private.json").read_text())
    names = ["cpp_bridge_launcher.cpp", "supervisor.hpp", "bridge_job.hpp", "bridge_client.hpp",
             "test_supervisor_boundary.cpp", "rebuild_launchers.py"]
    sources = [{"file": n, "bytes": (source / n).stat().st_size, "sha256": sha(source / n)} for n in names]
    logs = [{"file": p.name, "bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(out.glob("*.log"))]
    receipt = {
        "schema": "hs.production-bridge.launcher-only-rebuild.v1",
        "status": "COMPILED_INSPECTED_BOUNDARY_CPU_TEST_PASS",
        "artifacts": artifacts,
        "fixed_worker": {"path": "cpp-build-02/cpp_fixed_worker", "sha256": sha(root / "cpp-build-02/cpp_fixed_worker"), "rebuilt": False},
        "unchanged_native_worker_pins": {a["role"]: a["executable_sha256"] for a in native["artifacts"]},
        "NEEDED": needed, "sources": sources, "logs": logs, "boundary_tests": summary,
        "invocations": [
            {"command": ["launcher-build-03/cpu_supervisor_boundary", "launcher-build-03/boundary-fixture"],
             "outcome": "SAFE_REJECTION_BEFORE_FIXTURE_EXECUTION", "log": "BOUNDARY-test.log"},
            {"command": ["launcher-build-03/cpu_supervisor_boundary", str(out / "boundary-fixture")],
             "outcome": "FOUR_CPU_BOUNDARY_TESTS_PASS", "log": "BOUNDARY-test-02.log"}],
        "compile_recipe": "Retained source-snapshot rebuild_launchers.py; out was launcher-build-03. Only CPU boundary invocation corrected to absolute fixture path; no binary/source changes between invocations.",
        "native_executables_started": 0, "GPU_contexts": 0, "model_creations": 0,
        "backend_initializations": 0, "placement_actions": 0, "forwards": 0,
        "production_gate": "PERMANENT_DENIAL",
        "finalizer": {"sha256": sha(__file__), "scope": "READ_HASH_LOG_VALIDATION_ONLY_NO_EXEC"},
    }
    target.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "artifacts": artifacts, "boundary_tests": summary}))


if __name__ == "__main__":
    main()
