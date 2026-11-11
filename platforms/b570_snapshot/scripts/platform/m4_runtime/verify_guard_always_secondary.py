#!/usr/bin/env python3
"""Independent raw-record secondary QA; shares only the old archive extractor."""

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess
import tempfile

from recompute_evidence_bundle import extract_verified

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "benchmarks/m4_runtime"
ARCHIVE = ROOT / "artifacts/m4_runtime/runtime-profitability-control-20260925/m4_runtime_complete_evidence.tar.gz"
SHA = "af73b8f0edeae5027357338a627d899b08db425884a1373162932a72f4f119ab"
PLAN_COMMIT = "8e7be49"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument("--result", type=Path, default=BASE / "GUARD_ALWAYS_SECONDARY_ANALYSIS.json")
    parser.add_argument("--receipt", type=Path, default=ROOT / "paper/mlsys2027/evidence/M4_GUARD_ALWAYS_SECONDARY_QA_V06.json")
    args = parser.parse_args()
    checks = []
    def check(label, condition):
        if not condition:
            raise AssertionError(label)
        checks.append(label)
    def read(path):
        return json.loads(path.read_text())
    check("canonical archive SHA-256", digest(args.archive) == SHA)
    plan = BASE / "GUARD_ALWAYS_SECONDARY_ANALYSIS_PLAN.md"
    plan_rel = plan.relative_to(ROOT).as_posix()
    plan_commit = subprocess.check_output(["git", "rev-parse", PLAN_COMMIT], cwd=ROOT, text=True).strip()
    frozen_plan = subprocess.check_output(["git", "show", plan_commit + ":" + plan_rel], cwd=ROOT)
    check("plan remains identical to pre-calculation commit", plan.read_bytes() == frozen_plan)
    check("plan commit precedes result in branch history", subprocess.run(
        ["git", "merge-base", "--is-ancestor", plan_commit, "HEAD"], cwd=ROOT).returncode == 0)
    with tempfile.TemporaryDirectory(prefix="m4-secondary-independent-") as tmp:
        root = Path(tmp)
        manifest = extract_verified(args.archive, root)
        check("all 62 frozen payloads verified", manifest["entry_count"] == 62)
        manifests = [(p, read(p)) for p in (root / "attempts").rglob("manifest.json")]
        formal = [(p, m) for p, m in manifests if m.get("stage") == "formal"]
        check("exactly one formal dataset", len(formal) == 1)
        path, attempt = formal[0]
        check("frozen formal attempt", attempt["attempt_id"] == "unattended-20260924t125921z-formal")
        raw = path.with_name("observations.jsonl")
        records = [json.loads(line) for line in raw.read_text().splitlines()]
        completion = read(path.with_name("completion.json"))
        check("complete 540-record schedule", len(records) == attempt["planned_observations"] == completion["observations"] == 540
              and completion["status"] == "COMPLETE" and completion["observations_sha256"] == digest(raw))
        check("unique sequential observation indices", sorted(r["observation_index"] for r in records) == list(range(540)))
        split = root / "frozen_repo/benchmarks/m4_runtime/HELDOUT_SPLIT.json"
        tasks = read(split)["tasks"]
        ids = [(t["workload_family"], t["task_id"]) for t in tasks]
        check("60 unique frozen prompts", len(ids) == len(set(ids)) == 60)
        expected = {(f, t, rep, c) for f, t in ids for rep in range(3)
                    for c in ("TARGET_ONLY", "ALWAYS_SPEC_K2", "GUARD_K2")}
        keys = [(r["workload_family"], r["task_id"], r["repetition"], r["condition"]) for r in records]
        check("all and only formal pairing keys once", len(set(keys)) == 540 and set(keys) == expected)
        primary_path = root / "analysis/FORMAL_ANALYSIS.json"
        check("repository primary equals archive bytes", primary_path.read_bytes() == (BASE / "FORMAL_ANALYSIS.json").read_bytes())
        primary = read(primary_path)
        check("primary references same formal attempt and raw", primary["attempt_id"] == attempt["attempt_id"]
              and primary["formal_observations_sha256"] == digest(raw) and len(primary["per_prompt"]) == 60)
        prompts, ratios = [], []
        guard_faster = always_faster = ties = 0
        exact = {"ALWAYS_SPEC_K2": 0, "GUARD_K2": 0}
        # Independently select records by prompt, then sort each three-time vector.
        # No analyzer imports, keyed median routine, or statistics.mean/median calls.
        for n, (family, task_id) in enumerate(ids):
            group = [r for r in records if (r["workload_family"], r["task_id"]) == (family, task_id)]
            medians = {}
            for condition, name in (("TARGET_ONLY", "target_median_ns"), ("ALWAYS_SPEC_K2", "always_median_ns"), ("GUARD_K2", "guard_median_ns")):
                times = sorted(r["result"]["end_to_end_ns"] for r in group if r["condition"] == condition)
                check(f"prompt {n}: positive three-repetition {condition}", len(times) == 3 and all(type(v) is int and v > 0 for v in times))
                medians[name] = times[1]
            for rep in range(3):
                paired = {r["condition"]: r["result"]["generated_token_ids"] for r in group if r["repetition"] == rep}
                for condition in exact:
                    check(f"prompt {n} repetition {rep}: direct-ID {condition}", paired[condition] == paired["TARGET_ONLY"])
                    exact[condition] += 1
            prompt = {"workload_family": family, "task_id": task_id, **medians}
            check(f"prompt {n}: exact primary medians and order", all(primary["per_prompt"][n][k] == v for k, v in prompt.items()))
            g, a = medians["guard_median_ns"], medians["always_median_ns"]
            prompt["guard_over_always"] = g / a
            ratios.append(g / a)
            prompts.append(prompt)
            guard_faster += g < a
            always_faster += a < g
            ties += a == g
        # Exact rational accumulation of binary log floats independently reproduces
        # the frozen mean convention; cached logs change no estimator or draw order.
        logs = [Fraction.from_float(math.log(r)) for r in ratios]
        headline = math.exp(float(sum(logs, Fraction(0)) / 60))
        generator = random.Random(20260924)
        draws = []
        for _ in range(10000):
            total = Fraction(0)
            for _ in range(60):
                total += logs[generator.randrange(60)]
            draws.append(math.exp(float(total / 60)))
        draws.sort()
        endpoints = []
        for q in (.025, .975):
            position = 9999 * q
            lower = int(position)
            upper = lower + (position != lower)
            endpoints.append(draws[lower] + (draws[upper] - draws[lower]) * (position - lower))
        result = read(args.result)
        check("all 60 secondary prompt rows exactly reproduced", result["per_prompt"] == prompts)
        check("paired geometric mean exactly reproduced", result["geometric_mean_guard_over_always"] == headline)
        check("both finite-bootstrap endpoints exactly reproduced", result["guard_over_always_95pct_prompt_bootstrap_ci"] == endpoints)
        counts = {"guard_faster": guard_faster, "always_faster": always_faster, "ties": ties}
        check("descriptive counts exactly reproduced", result["prompt_counts"] == counts and sum(counts.values()) == 60)
        expected_status = "GUARD_HIGHER_LATENCY" if endpoints[0] > 1 else "GUARD_LOWER_LATENCY" if endpoints[1] < 1 else "INTERVAL_INCLUDES_PARITY"
        check("interval interpretation follows frozen direction", result["interpretation"] == expected_status)
        for field, expected_value in {
            "schema": "heterospec.m4_runtime.guard_always_secondary.v1", "analysis_status": "POST_STUDY_SECONDARY",
            "source_archive_sha256": SHA, "analysis_plan_sha256": digest(plan), "verified_payload_files": 62,
            "formal_attempt_id": attempt["attempt_id"], "formal_observations_sha256": digest(raw),
            "heldout_split_sha256": digest(split), "primary_analysis_sha256": digest(primary_path),
            "prompt_count": 60, "repetitions_per_condition": 3, "formal_observations": 540,
            "bootstrap_seed": 20260924, "bootstrap_resamples": 10000, "bootstrap_unit": "paired held-out prompt",
            "primary_medians_exact_match": True, "no_new_measurement": True, "new_model_execution": False,
            "energy": "NOT_CLAIMED", "analysis_choices_changed_after_result": False,
            "correctness_scope": {"reference": "FORMAL_ANALYSIS.json:correctness; frozen target-only generated IDs",
                                  "direct_id_exact_pairs": exact, "mismatches": 0},
        }.items():
            check("secondary metadata " + field, result[field] == expected_value)
    receipt = {
        "schema": "heterospec.m4_runtime.guard_always_secondary.qa.v1", "status": "PASS",
        "analysis_status": "POST_STUDY_SECONDARY", "checks": checks, "check_count": len(checks),
        "starting_main": "50050f62a44064b11948263d064aa6b1bb7a3359", "analysis_plan_commit": plan_commit,
        "source_archive_sha256": SHA, "result_sha256": digest(args.result),
        "analysis_plan_sha256": digest(plan), "independent_verifier_sha256": digest(Path(__file__)),
        "independent_method": "raw prompt filtering; sorted middle of three latencies; exact Fraction sum of binary log floats; standalone Random; explicit linear percentile interpolation; no analyzer calculation imported",
        "headline": headline, "ci95": endpoints, "prompt_counts": counts, "formal_exact_pairs": exact,
        "primary_medians_exact_match": True, "new_model_execution": False,
        "limits": ["Post-study secondary, aggregate result already known.", "Prompt-bootstrap interval excludes session/recalibration variation.", "Original freeze-hash defect and markers unchanged."],
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "checks": len(checks), "headline": headline, "ci95": endpoints, "prompt_counts": counts}))


if __name__ == "__main__":
    main()
