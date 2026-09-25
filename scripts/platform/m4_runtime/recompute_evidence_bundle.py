#!/usr/bin/env python3
"""Verify and independently recompute the closed M4 study from its archive only."""

import argparse
import hashlib
import json
import math
import random
import statistics
import tarfile
import tempfile
from pathlib import Path


ROOT_NAME = "m4-runtime-evidence"
SEED = 20260924
CONDITIONS = ("TARGET_ONLY", "ALWAYS_SPEC_K2", "GUARD_K2")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(root, name):
    return json.loads((root / name).read_text(encoding="utf-8"))


def rows(root, stage):
    return [json.loads(line) for line in (root / f"attempts/{stage}/observations.jsonl").read_text().splitlines()]


def gm(values):
    return math.exp(statistics.mean(math.log(value) for value in values))


def quantile(values, q):
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lo, hi = math.floor(index), math.ceil(index)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)


def ci(values, rng):
    n = len(values)
    samples = [gm([values[rng.randrange(n)] for _ in range(n)]) for _ in range(10000)]
    return [quantile(samples, 0.025), quantile(samples, 0.975)]


def key(row):
    return row["workload_family"], row["task_id"], row["repetition"], row["condition"]


def identity(row):
    return row["workload_family"], row["task_id"]


def check_close(actual, expected, label):
    if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
        raise RuntimeError(f"{label}: recomputed {actual}, reported {expected}")


def extract_verified(archive, destination):
    prefix = ROOT_NAME + "/"
    with tarfile.open(archive, "r:gz") as stream:
        names = set()
        for member in stream:
            if not member.isfile() or not member.name.startswith(prefix):
                raise RuntimeError(f"Unexpected archive entry: {member.name}")
            relative = Path(member.name[len(prefix):])
            if not relative.parts or any(part in (".", "..") for part in relative.parts):
                raise RuntimeError(f"Unsafe archive path: {member.name}")
            if relative.as_posix() in names:
                raise RuntimeError(f"Duplicate archive entry: {member.name}")
            names.add(relative.as_posix())
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with stream.extractfile(member) as source, target.open("wb") as output:
                while block := source.read(8 << 20):
                    output.write(block)
    manifest = load(destination, "bundle_manifest.json")
    expected = {entry["path"] for entry in manifest["files"]} | {"bundle_manifest.json"}
    if names != expected or manifest["entry_count"] != len(expected) - 1:
        raise RuntimeError("Archive entries differ from bundle manifest")
    for entry in manifest["files"]:
        data = (destination / entry["path"]).read_bytes()
        if len(data) != entry["bytes"] or sha(data) != entry["sha256"]:
            raise RuntimeError(f"Archive byte/hash failure: {entry['path']}")
    return manifest


def check_attempt(root, stage, expected):
    raw = root / f"attempts/{stage}/observations.jsonl"
    digest = sha(raw.read_bytes())
    completion = load(root, f"attempts/{stage}/completion.json")
    manifest = load(root, f"attempts/{stage}/manifest.json")
    data = rows(root, stage)
    if (completion["status"] != "COMPLETE" or completion["observations"] != expected or
            completion["observations_sha256"] != digest or len(data) != expected or
            sorted(row["observation_index"] for row in data) != list(range(expected)) or
            manifest["planned_observations"] != expected):
        raise RuntimeError(f"Incomplete or changed {stage} attempt")
    return data, manifest, digest


def recompute(root, entry_count):
    baseline, base_manifest, base_sha = check_attempt(root, "calibration_baselines", 240)
    candidates, cand_manifest, cand_sha = check_attempt(root, "calibration_candidates", 1080)
    qualification, qual_manifest, qual_sha = check_attempt(root, "qualification", 144)
    formal, formal_manifest, formal_sha = check_attempt(root, "formal", 540)
    freeze_path = root / "freeze/CALIBRATION_FREEZE.json"
    freeze = load(root, "freeze/CALIBRATION_FREEZE.json")
    qual_report = load(root, "freeze/QUALIFICATION_REPORT.json")
    analysis = load(root, "analysis/FORMAL_ANALYSIS.json")
    closure = load(root, "provenance/provenance_closure.json")
    actual_freeze_sha = sha(freeze_path.read_bytes())
    build_sha = sha((root / "build/manifest.json").read_bytes())
    global_marker = load(root, "markers/FORMAL_DATA_STARTED")
    attempt_marker = load(root, "markers/FORMAL_ATTEMPT_STARTED")
    if (actual_freeze_sha != closure["actual_calibration_freeze_sha256"] or
            build_sha != closure["erroneously_recorded_build_manifest_sha256"] or
            any(item["freeze_sha256"] != build_sha for item in
                (global_marker, attempt_marker, qual_report, formal_manifest)) or
            global_marker["head"] != closure["formal_start_commit"] or
            sha((root / "freeze/QUALIFICATION_REPORT.json").read_bytes()) != global_marker["qualification_sha256"] or
            analysis["provenance_audit"]["actual_freeze_sha256"] != actual_freeze_sha):
        raise RuntimeError("Freeze-hash defect does not reconcile with original evidence")
    for name, digest in freeze["source_data_sha256"].items():
        source = root / "frozen_repo" / name
        if sha(source.read_bytes()) != digest:
            raise RuntimeError(f"Frozen source changed: {name}")
        if any(m["source_data_sha256"][name] != digest for m in
               (base_manifest, cand_manifest, qual_manifest, formal_manifest)):
            raise RuntimeError(f"Attempt source hash changed: {name}")
    if (freeze["baseline_observations_sha256"] != base_sha or
            freeze["candidate_observations_sha256"] != cand_sha or
            qual_report["observations_sha256"] != qual_sha or
            analysis["formal_observations_sha256"] != formal_sha):
        raise RuntimeError("Attempt raw-data hash changed")

    prompt_tasks = load(root, "frozen_repo/benchmarks/m4_runtime/PROMPT_TOKENS.json")["tasks"]
    calibration_tasks = [task for task in prompt_tasks if task["split"] == "CALIBRATION"]
    baseline_by = {(identity(row), row["repetition"], row["condition"]): row for row in baseline}
    candidate_by = {(identity(row), row["repetition"], row["candidate_id"]): row for row in candidates}
    target_ratios = []
    for task in calibration_tasks:
        target, counts = [], []
        for rep in range(3):
            a = baseline_by[(identity(task), rep, "TARGET_ONLY")]["result"]
            b = baseline_by[(identity(task), rep, "ALWAYS_SPEC_K2")]["result"]
            if a["generated_token_ids"] != b["generated_token_ids"]:
                raise RuntimeError("Calibration baseline token mismatch")
            target.append(a["end_to_end_ns"])
            counts.append(a["generated_token_count"])
        target_ratios.append(statistics.median(target) / statistics.median(counts))
    target_ref = statistics.median(target_ratios)
    check_close(target_ref, freeze["target_reference_ns_per_token"], "target reference")
    grid = load(root, "frozen_repo/benchmarks/m4_runtime/POLICY_CANDIDATES.json")
    scored = []
    for E in grid["exploration_rounds_E"]:
        for margin in grid["margins"]:
            candidate_id = f"E{E}_M{round(100 * margin):03d}"
            regret, overhead = [], []
            exact = True
            for task in calibration_tasks:
                tid = identity(task)
                target = [baseline_by[(tid, rep, "TARGET_ONLY")]["result"]["end_to_end_ns"] for rep in range(3)]
                fixed = [baseline_by[(tid, rep, "ALWAYS_SPEC_K2")]["result"]["end_to_end_ns"] for rep in range(3)]
                guard = []
                for rep in range(3):
                    result = candidate_by[(tid, rep, candidate_id)]["result"]
                    guard.append(result["end_to_end_ns"])
                    overhead.append(result["guard_compute_ns"])
                    exact &= result["generated_token_ids"] == baseline_by[(tid, rep, "TARGET_ONLY")]["result"]["generated_token_ids"]
                regret.append(statistics.median(guard) / min(statistics.median(target), statistics.median(fixed)))
            if exact:
                scored.append((gm(regret), statistics.mean(overhead), E, -margin, candidate_id))
    winner = min(scored)
    if winner[-1] != freeze["selected"]["candidate_id"]:
        raise RuntimeError("Independent calibration selected a different policy")
    check_close(winner[0], freeze["selected"]["geometric_mean_oracle_regret"], "calibration regret")

    def exact_pairs(data, expected_per_condition):
        by = {key(row): row for row in data}
        if len(by) != len(data):
            raise RuntimeError("Duplicate condition/repetition")
        counts = {"ALWAYS_SPEC_K2": 0, "GUARD_K2": 0}
        triples = {(row["workload_family"], row["task_id"], row["repetition"]) for row in data}
        for family, task, rep in triples:
            target = by[(family, task, rep, "TARGET_ONLY")]["result"]["generated_token_ids"]
            for condition in counts:
                if by[(family, task, rep, condition)]["result"]["generated_token_ids"] != target:
                    raise RuntimeError(f"Direct-ID mismatch: {condition} {task} repetition {rep}")
                counts[condition] += 1
        if counts != {name: expected_per_condition for name in counts}:
            raise RuntimeError("Exact-pair count changed")
        return by, counts

    _, qualification_counts = exact_pairs(qualification, 48)
    formal_by, formal_counts = exact_pairs(formal, 180)
    if qual_report["counts"] != qualification_counts or analysis["correctness"]["mismatch_count"] != 0:
        raise RuntimeError("Recorded direct-ID result changed")
    heldout = load(root, "frozen_repo/benchmarks/m4_runtime/HELDOUT_SPLIT.json")["tasks"]
    prompt_medians = []
    for task in heldout:
        family, task_id = identity(task)
        medians = {}
        for condition in CONDITIONS:
            values = [formal_by[(family, task_id, rep, condition)]["result"]["end_to_end_ns"] for rep in range(3)]
            medians[condition] = statistics.median(values)
        prompt_medians.append(medians)
    if len(prompt_medians) != 60:
        raise RuntimeError("Held-out prompt count changed")
    target_guard = [x["TARGET_ONLY"] / x["GUARD_K2"] for x in prompt_medians]
    target_fixed = [x["TARGET_ONLY"] / x["ALWAYS_SPEC_K2"] for x in prompt_medians]
    guard_oracle = [x["GUARD_K2"] / min(x["TARGET_ONLY"], x["ALWAYS_SPEC_K2"]) for x in prompt_medians]
    rng = random.Random(SEED)
    computed = {
        "geometric_mean_target_over_guard": gm(target_guard),
        "target_over_guard_95pct_prompt_bootstrap_ci": ci(target_guard, rng),
        "geometric_mean_target_over_always_spec": gm(target_fixed),
        "target_over_always_spec_95pct_prompt_bootstrap_ci": ci(target_fixed, rng),
        "geometric_mean_guard_over_oracle": gm(guard_oracle),
        "guard_over_oracle_95pct_prompt_bootstrap_ci": ci(guard_oracle, rng),
    }
    for name, value in computed.items():
        reported = analysis["overall"][name]
        if isinstance(value, list):
            for index in range(2):
                check_close(value[index], reported[index], f"{name}[{index}]")
        else:
            check_close(value, reported, name)
    fallback = sum(row["result"]["fallback_triggered"] for row in formal if row["condition"] == "GUARD_K2") / 180
    check_close(fallback, analysis["control"]["fallback_request_fraction"], "fallback fraction")
    return {
        "status": "PASS", "verified_payload_files": entry_count,
        "observation_counts": {"baseline": 240, "candidates": 1080, "qualification": 144, "formal": 540},
        "selected_policy": winner[-1], "qualification_exact_pairs": qualification_counts,
        "formal_exact_pairs": formal_counts, "heldout_prompts": 60,
        "overall": computed, "fallback_fraction": fallback,
        "freeze_sha256": actual_freeze_sha,
        "recorded_incorrect_digest": build_sha,
        "formal_start_commit": global_marker["head"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args()
    if args.expected_sha256 and sha(args.archive.read_bytes()) != args.expected_sha256:
        raise RuntimeError("Archive SHA-256 differs from expected")
    with tempfile.TemporaryDirectory(prefix="m4-evidence-verify-") as temporary:
        root = Path(temporary)
        manifest = extract_verified(args.archive, root)
        print(json.dumps(recompute(root, manifest["entry_count"]), indent=2))


if __name__ == "__main__":
    main()
