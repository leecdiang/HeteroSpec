"""Actual fixed std-only processes with explicit CPU transport/IO fault injection."""
import argparse
import json
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from cpu_run import run_case, CPU_LAUNCHER_SHA256, CPU_WORKER_SHA256
from cpu_resource_fixture import cpu_domain_factory


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True); p.add_argument("--launcher", required=True)
    p.add_argument("--worker", required=True)
    a = p.parse_args()
    root = Path(a.out)
    if not root.is_absolute() or root.exists():
        raise RuntimeError("fresh unique CPU suite root required")
    root.mkdir(mode=0o700)
    cases = [("normal", "normal", None)]
    cases += [(b, b, None) for b in ("exit_nonzero", "no_close", "stdout_overflow", "stderr_overflow", "no_worker_hello")]
    cases += [(f, "normal", f) for f in ("before_bind_crash", "after_bind_crash", "parent_disconnect",
              "job_changed", "job_after_bind_changed", "result_unknown", "log_fsync", "log_partial")]
    results = []
    for name, behavior, fault in cases:
        r = run_case(root / name, Path(a.launcher), Path(a.worker), CPU_LAUNCHER_SHA256,
                     CPU_WORKER_SHA256, behavior=behavior, fault=fault, domain_factory=cpu_domain_factory)
        expected_pass = name == "normal"
        if (r["status"] == "PASS_CPU_BRIDGE") != expected_pass:
            raise RuntimeError("unexpected CPU outcome for " + name + ": " + json.dumps(r))
        if not expected_pass and (r["worker_index"] != 0 or r["stage_index"] != 0):
            raise RuntimeError("fault incorrectly released worker/stage: " + name)
        if r["counts"]["placements"] != 3:
            raise RuntimeError("failed launch budget refunded or retried: " + name)
        results.append({"case": name, "status": r["status"], "phase": r["phase"],
            "stop_reason": r["stop_reason"], "counts": r["counts"],
            "worker_index": r["worker_index"], "native_checks": "ALL_261_NOT_RUN"})
        print(json.dumps(results[-1], sort_keys=True), flush=True)
    report = {"status": "PASS_CPU_FIXED_PROCESS_FAULT_SUITE", "cases": results,
              "native_ELF_invocations": 0, "model_creations": 0, "GPU_contexts": 0,
              "backend_initializations": 0, "placement_actions": 0, "model_forwards": 0,
              "actual_kernel_cgroup_activations": 0, "native_checks": "ALL_261_NOT_RUN"}
    (root / "SUITE.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "cases": len(results), "actual_native_calls": 0}))


if __name__ == "__main__":
    main()
