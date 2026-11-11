"""Offline negative fixtures for PR221's diagnostic replay interface.

All cases copy existing q1 CPU evidence; no model, driver, native executable,
new timing, or new qualification is run. Mutated copies are REDTEAM_ONLY.
The originals are read-only inputs, and every output directory must be fresh.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True


def read(path):
    return json.loads(path.read_text())


def identity(path):
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def work_totals(result, job):
    lengths = {case["name"]: len(case["history"]) for case in job["cases"]}
    contexts = calls = rows = 0
    records = []
    for cell in result["qualification"]:
        records.append((cell["case"], cell["q"], cell["reference"], False))
        records.extend((cell["case"], cell["q"], c, False) for c in cell["candidates"])
    records.extend((m["case"], m["q"], m, m["mode"] == "one_shape_warmup_then_reset")
                   for m in result["measurements"])
    for name, q, record, warm in records:
        p = lengths[name]
        contexts += 1
        calls += (p + 31) // 32 + len(record["schedule"]) + 1
        rows += p + q + 1
        if warm:
            calls += (p + 31) // 32 + len(record["schedule"])
            rows += p + q
    return {"contexts": contexts, "attempted_native_calls": calls, "attempted_target_rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True,
                        help="Read-only continuation_20261111/matched_cost directory")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    baseline = args.baseline.resolve()
    source = baseline / "cpu_protocol_final"
    if args.out.exists() or args.out.is_symlink():
        raise ValueError("fresh output required")
    out = args.out.resolve()
    out.mkdir(parents=True)
    original_paths = [source / n for n in ["RUN.json", "JOB.json", "PLAN.json", "native/RESULT.json"]]
    original_paths += sorted((source / "native/blobs").iterdir())
    original_identity = {str(p.relative_to(source)): identity(p) for p in original_paths}
    sys.path.insert(0, str(baseline))
    verifier = importlib.import_module("verify_run")
    summarizer = importlib.import_module("summarize_cost")
    report = {
        "schema": "heterospec.v1-admission-redteam.v1",
        "scope": "Offline negative fixtures from an existing q1 CPU run. Not observations or new model runs.",
        "native_model_executions": 0,
        "CUDA_driver_calls": 0,
        "new_measurements": 0,
        "baseline_source": {n: identity(baseline / n) for n in ["verify_run.py", "summarize_cost.py"]},
        "baseline_original_records": original_identity,
        "cases": [],
    }
    cases = ["baseline_copy", "changed_same_length_history", "failed_run_status",
             "changed_model_identity", "missing_repeat_panel", "empty_actual_module_inventory"]
    for name in cases:
        case = out / name
        (case / "native").mkdir(parents=True)
        for filename in ["RUN.json", "JOB.json", "PLAN.json"]:
            shutil.copyfile(source / filename, case / filename)
        shutil.copyfile(source / "native/RESULT.json", case / "native/RESULT.json")
        shutil.copytree(source / "native/blobs", case / "native/blobs")
        run, job, result = read(case / "RUN.json"), read(case / "JOB.json"), read(case / "native/RESULT.json")
        detail = {"name": name, "kind": "UNMODIFIED_COPY" if name == "baseline_copy" else "REDTEAM_ONLY_MUTATED_COPY"}
        (case / "REDTEAM_ONLY.txt").write_text("Not a new experiment. No model or timing was executed. Do not use as a cost observation.\n")
        rebind_result = False
        if name == "changed_same_length_history":
            before = job["cases"][0]["history"][0]
            job["cases"][0]["history"][0] = (before + 1) % 128
            write(case / "JOB.json", job)
            detail.update(change="Only JOB's first history token changed, same length; RUN's job hash remains original.",
                          original_job_sha256=run["job"]["sha256"], mutated_job_sha256=identity(case / "JOB.json")["sha256"])
        elif name == "failed_run_status":
            run["status"] = "TIMEOUT_OWNED_NATIVE_CHILD"
            run["returncode"] = 124
            run["native_process"] = {"timed_out": True, "returncode": -9, "child_reaped": True}
            write(case / "RUN.json", run)
            detail["change"] = "Only RUN execution status/returncode changed to timeout; complete saved RESULT bytes untouched."
        elif name == "changed_model_identity":
            run["model"]["sha256"] = "0" * 64
            write(case / "RUN.json", run)
            detail["change"] = "Only RUN's model digest changed; saved RESULT and blobs untouched."
        elif name == "missing_repeat_panel":
            result["measurements"] = [m for m in result["measurements"] if m["repeat"] == 0]
            result["work"].update(work_totals(result, job))
            rebind_result = True
            detail.update(change="Only existing repeat-0 observations retained, result work recomputed; declared repeats=2, PLAN and RUN work remain complete-panel values.",
                          retained_measurements=len(result["measurements"]), declared_repeats=job["repeats"])
        elif name == "empty_actual_module_inventory":
            result["native_modules_before"] = {}
            result["native_modules_after"] = {}
            rebind_result = True
            detail.update(change="Saved actual-module inventories removed; RUN's four bound numerical libraries remain.",
                          expected_bound_libraries=len(run["libraries_before"]))
        if rebind_result:
            write(case / "native/RESULT.json", result)
            run["result"].update(identity(case / "native/RESULT.json"))
            write(case / "RUN.json", run)
            detail["intentional_structural_fixture_result_digest_updated"] = True
        try:
            replay = verifier.verify(case)
            cost = summarizer.summarize(case)
            detail.update(legacy_replay_accepted=True, replay=replay,
                          cost_summary_status=cost["status"], emitted_cost_pairs=len(cost["pairs"]))
        except Exception as error:
            detail.update(legacy_replay_accepted=False, error=repr(error))
        detail["controller_admission_expected"] = "REJECT_CPU_FIXTURE" if name == "baseline_copy" else "REJECT_MUTATED_OR_INCOMPLETE_ARTIFACT"
        report["cases"].append(detail)
    after = {str(p.relative_to(source)): identity(p) for p in original_paths}
    if after != original_identity:
        raise ValueError("read-only baseline changed")
    report["baseline_unchanged"] = True
    report["conclusion"] = "Legacy PASS means consistency of selected saved records, not controller cost admission. No cost pairs or new observations were generated."
    write(out / "REPRODUCTION.json", report)
    print(json.dumps({"cases": [{"name": c["name"], "legacy_replay_accepted": c["legacy_replay_accepted"],
                                 "cost_summary_status": c.get("cost_summary_status"), "emitted_cost_pairs": c.get("emitted_cost_pairs")}
                                for c in report["cases"]], "baseline_unchanged": True,
                      "native_model_executions": 0, "new_measurements": 0}, indent=2))


if __name__ == "__main__":
    main()
