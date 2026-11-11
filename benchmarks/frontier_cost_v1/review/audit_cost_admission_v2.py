"""Independently exercise v2 against retained CPU evidence and negative copies.

This executes only Python/file hashing. It never loads a model/native library,
calls a CUDA API, or produces cost observations. Explicit fixture repinning is
only a way to reach internal checks; it is not real provenance admission.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
ORIGINAL_RUN_PIN = "135e1901e8c2715492f512c54dc949d21b363b9dddf9a7d01f7c9a4a16a4324f"


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True, help="Read-only original cpu_protocol_final directory")
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True, help="Explicit role to actual retained asset mapping")
    parser.add_argument("--redteam", type=Path, required=True, help="Existing v1_repro_01 negative copies")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists() and not args.out.is_symlink(), "Fresh output required")
    args.out.mkdir(parents=True)
    module_sha = sha(args.module)
    spec = importlib.util.spec_from_file_location("independent_cost_admission", args.module)
    admission = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(admission)
    assets = read(args.assets)
    before = {role: sha(path) for role, path in assets.items()}
    report = {
        "schema": "heterospec.independent-cost-admission-audit.v1",
        "admission_source_sha256": module_sha,
        "auditor_source_sha256": sha(__file__),
        "original_RUN_sha256": ORIGINAL_RUN_PIN,
        "pin_source": "Retained original PR221 CPU RUN identity, not a new fixture hash",
        "model_executions": 0, "CUDA_driver_calls": 0, "new_measurements": 0,
        "checks": [],
    }
    baseline = admission.validate_exact_run(args.baseline, args.inputs, assets, ORIGINAL_RUN_PIN)
    require(baseline["status"] == "EXACT_RUN_VALIDATED", "Original diagnostic failed integrity validation")
    costs = admission.diagnostic_costs(baseline)
    require(costs["status"] == "REJECTED_CPU_SMOKE_AS_DEPLOYMENT_COST", "CPU diagnostic was incorrectly admitted")
    require(not costs["macro_costs"] and not costs["stage_costs"] and costs["online_stage_cost_eligible"] is False,
            "CPU diagnostic exposed a deployable cost")
    report["checks"].append({"case": "unaltered_original_CPU", "integrity": baseline["status"],
                             "cost_admission": costs["status"], "macro_costs": 0, "stage_costs": 0,
                             "measurements_replayed": baseline["measurement_count"], "work": baseline["work"]})

    def reject(directory, pin, expected, scope):
        try:
            admission.validate_exact_run(directory, args.inputs, assets, pin)
        except admission.AdmissionError as error:
            require(error.code == expected, f"{directory.name}: expected {expected}, got {error.code}")
            report["checks"].append({"case": directory.name, "scope": scope,
                                     "status": "REJECTED", "reason": error.code, "detail": str(error)})
        else:
            raise RuntimeError("Unexpected acceptance: " + directory.name)

    cases = {
        "changed_same_length_history": "BINDING_MISMATCH",
        "failed_run_status": "RUN_NOT_SUCCESSFUL",
        "changed_model_identity": "BINDING_MISMATCH",
        "missing_repeat_panel": "RUN_WORK_BINDING",
        "empty_actual_module_inventory": "INCOMPLETE_ACTUAL_MODULES",
    }
    for case, reason in cases.items():
        directory = args.redteam / case
        reject(directory, ORIGINAL_RUN_PIN,
               "BINDING_MISMATCH" if case == "changed_same_length_history" else "RUN_PIN_MISMATCH",
               "ORIGINAL_EXTERNAL_PIN")
        reject(directory, sha(directory / "RUN.json"), reason,
               "REDTEAM_ONLY_INTERNAL_CHECK_NOT_TRUSTED_PROVENANCE")

    # Preserve aggregate counts and every source timing; duplicate one existing
    # same-shape observation in place of another repetition to isolate coverage.
    duplicate = args.out / "duplicate_measurement_identity"
    (duplicate / "native").mkdir(parents=True)
    for name in ("JOB.json", "PLAN.json"):
        shutil.copyfile(args.baseline / name, duplicate / name)
    shutil.copytree(args.baseline / "native/blobs", duplicate / "native/blobs")
    run, result = read(args.baseline / "RUN.json"), read(args.baseline / "native/RESULT.json")
    require(result["measurements"][0]["case"] == result["measurements"][2]["case"], "Fixture shape assumption changed")
    result["measurements"][2] = deepcopy(result["measurements"][0])
    save(duplicate / "native/RESULT.json", result)
    run["result"].update(bytes=(duplicate / "native/RESULT.json").stat().st_size,
                         sha256=sha(duplicate / "native/RESULT.json"))
    save(duplicate / "RUN.json", run)
    (duplicate / "REDTEAM_ONLY.txt").write_text("Duplicated an existing saved observation to test coverage. No experiment or new timing.\n")
    reject(duplicate, sha(duplicate / "RUN.json"), "MEASUREMENT_PANEL_COVERAGE",
           "REDTEAM_ONLY_INTERNAL_CHECK_NOT_TRUSTED_PROVENANCE")
    require(before == {role: sha(path) for role, path in assets.items()}, "Read-only assets changed")
    require(sha(args.module) == module_sha, "Admission source changed during audit")
    require(sha(args.baseline / "RUN.json") == ORIGINAL_RUN_PIN, "Original RUN changed")
    report.update(status="PASS_SPECIFIC_ADMISSION_REGRESSIONS", actual_assets_unchanged=True,
                  production_stage_costs_admitted=0, GPU_admission_executed=False,
                  limitation="CPU replay and structural negatives only; CUDA success path remains unobserved")
    save(args.out / "AUDIT.json", report)
    print(json.dumps({"status": report["status"], "checks": len(report["checks"]),
                      "model_executions": 0, "CUDA_driver_calls": 0, "production_stage_costs_admitted": 0}))


if __name__ == "__main__":
    main()
