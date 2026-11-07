#!/usr/bin/env python3
"""Offline post-study paired contrast; never executes a model or changes evidence."""

import argparse
import hashlib
import json
import math
import random
import statistics
import tempfile
from pathlib import Path

from recompute_evidence_bundle import extract_verified

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE_SHA = "af73b8f0edeae5027357338a627d899b08db425884a1373162932a72f4f119ab"
MANIFEST_SHA = "877efc5871457e1fa5686ca5b4f44af20a6891cd7e014b52ac8521b4d7dae4a1"
SEED = 20260924
RESAMPLES = 10000
CONDITIONS = ("TARGET_ONLY", "ALWAYS_SPEC_K2", "GUARD_K2")
FORMAL_ID = "unattended-20260924t125921z-formal"
ARCHIVE = ROOT / "artifacts/m4_runtime/runtime-profitability-control-20260925/m4_runtime_complete_evidence.tar.gz"
BASE = ROOT / "benchmarks/m4_runtime"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_extracted(root):
    """Require the pinned manifest and all payload bytes, including no extra files."""
    canonical = ARCHIVE.with_name("bundle_manifest.json")
    if (root / "bundle_manifest.json").read_bytes() != canonical.read_bytes():
        raise ValueError("Extracted manifest differs from canonical sidecar")
    descriptor = load(ARCHIVE.with_name("archive_descriptor.json"))
    if digest(canonical) != MANIFEST_SHA or descriptor["bundle_manifest_sha256"] != MANIFEST_SHA or descriptor["sha256"] != ARCHIVE_SHA:
        raise ValueError("Canonical manifest descriptor changed")
    manifest = load(root / "bundle_manifest.json")
    entries = manifest["files"]
    expected = {x["path"] for x in entries} | {"bundle_manifest.json"}
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if manifest["entry_count"] != 62 or len(entries) != 62 or actual != expected:
        raise ValueError("Extracted archive file inventory differs")
    for item in entries:
        path = root / item["path"]
        if path.is_symlink() or path.stat().st_size != item["bytes"] or digest(path) != item["sha256"]:
            raise ValueError("Extracted payload changed: " + item["path"])
    return manifest


def analyze(root, manifest):
    eligible = [p for p in (root / "attempts").rglob("manifest.json") if load(p).get("stage") == "formal"]
    if len(eligible) != 1:
        raise ValueError("Exactly one eligible formal dataset required")
    attempt = load(eligible[0])
    if attempt["attempt_id"] != FORMAL_ID or attempt["planned_observations"] != 540:
        raise ValueError("Unexpected formal attempt or schedule")
    stage = eligible[0].parent
    raw = stage / "observations.jsonl"
    completion = load(stage / "completion.json")
    rows = [json.loads(line) for line in raw.read_text().splitlines()]
    if (completion["status"] != "COMPLETE" or completion["observations"] != 540 or
            completion["observations_sha256"] != digest(raw) or len(rows) != 540 or
            sorted(x["observation_index"] for x in rows) != list(range(540))):
        raise ValueError("Incomplete formal records")
    heldout_path = root / "frozen_repo/benchmarks/m4_runtime/HELDOUT_SPLIT.json"
    tasks = load(heldout_path)["tasks"]
    identities = [(x["workload_family"], x["task_id"]) for x in tasks]
    if len(identities) != 60 or len(set(identities)) != 60:
        raise ValueError("Expected 60 unique held-out prompts")
    by = {(x["workload_family"], x["task_id"], x["repetition"], x["condition"]): x for x in rows}
    expected_keys = {(*tid, rep, condition) for tid in identities for rep in range(3) for condition in CONDITIONS}
    if len(by) != 540 or set(by) != expected_keys:
        raise ValueError("Duplicate, missing, or unexpected formal prompt/repetition/condition")
    archived_analysis = root / "analysis/FORMAL_ANALYSIS.json"
    if archived_analysis.read_bytes() != (BASE / "FORMAL_ANALYSIS.json").read_bytes():
        raise ValueError("Archived and repository primary analysis differ")
    primary = load(archived_analysis)
    if primary["attempt_id"] != FORMAL_ID or primary["formal_observations_sha256"] != digest(raw):
        raise ValueError("Primary analysis identifies different raw records")
    prompts = []
    counts = {"guard_faster": 0, "always_faster": 0, "ties": 0}
    exact = {"ALWAYS_SPEC_K2": 0, "GUARD_K2": 0}
    for index, tid in enumerate(identities):
        medians = {}
        for condition in CONDITIONS:
            times = [by[(*tid, rep, condition)]["result"]["end_to_end_ns"] for rep in range(3)]
            if any(type(t) is not int or t <= 0 for t in times):
                raise ValueError("Latency must be positive integer nanoseconds")
            medians[condition] = statistics.median(times)
        for rep in range(3):
            target = by[(*tid, rep, "TARGET_ONLY")]["result"]["generated_token_ids"]
            for condition in exact:
                if by[(*tid, rep, condition)]["result"]["generated_token_ids"] != target:
                    raise ValueError("Direct generated-ID mismatch")
                exact[condition] += 1
        prompt = {"workload_family": tid[0], "task_id": tid[1],
                  "target_median_ns": medians["TARGET_ONLY"],
                  "always_median_ns": medians["ALWAYS_SPEC_K2"], "guard_median_ns": medians["GUARD_K2"]}
        original = primary["per_prompt"][index]
        if any(original[key] != value for key, value in prompt.items()):
            raise ValueError("Raw median or held-out order differs from primary analysis")
        guard, always = prompt["guard_median_ns"], prompt["always_median_ns"]
        prompt["guard_over_always"] = guard / always
        prompts.append(prompt)
        counts["guard_faster" if guard < always else "always_faster" if guard > always else "ties"] += 1
    if len(primary["per_prompt"]) != 60 or exact != {c: 180 for c in exact}:
        raise ValueError("Primary prompt/correctness count differs")
    ratios = [x["guard_over_always"] for x in prompts]
    def gm(data):
        return math.exp(statistics.mean(math.log(x) for x in data))
    rng = random.Random(SEED)
    samples = sorted(gm([ratios[rng.randrange(60)] for _ in range(60)]) for _ in range(RESAMPLES))
    def percentile(q):
        position = (RESAMPLES - 1) * q
        lo, hi = math.floor(position), math.ceil(position)
        return samples[lo] + (samples[hi] - samples[lo]) * (position - lo)
    interval = [percentile(.025), percentile(.975)]
    interpretation = ("GUARD_HIGHER_LATENCY" if interval[0] > 1 else
                      "GUARD_LOWER_LATENCY" if interval[1] < 1 else "INTERVAL_INCLUDES_PARITY")
    return {
        "schema": "heterospec.m4_runtime.guard_always_secondary.v1",
        "analysis_status": "POST_STUDY_SECONDARY",
        "analysis_plan_sha256": digest(BASE / "GUARD_ALWAYS_SECONDARY_ANALYSIS_PLAN.md"),
        "source_archive_sha256": ARCHIVE_SHA,
        "verified_payload_files": manifest["entry_count"],
        "formal_attempt_id": FORMAL_ID, "formal_observations_sha256": digest(raw),
        "heldout_split_sha256": digest(heldout_path), "primary_analysis_sha256": digest(archived_analysis),
        "prompt_count": 60, "repetitions_per_condition": 3, "formal_observations": 540,
        "formula": "r_i = median(Guard_i[3 repetitions]) / median(Always-Spec_i[3 repetitions]); exp(mean(log(r_i)))",
        "orientation": "<1 Guard lower latency; =1 parity; >1 Guard higher latency (Always-Spec lower)",
        "bootstrap_unit": "paired held-out prompt", "bootstrap_seed": SEED, "bootstrap_resamples": RESAMPLES,
        "bootstrap_random_stream": "fresh standalone random.Random(20260924); randrange(60); archived held-out order",
        "percentile_convention": "linear interpolation of sorted estimates at (10000-1)*q; q=0.025,0.975",
        "geometric_mean_guard_over_always": gm(ratios),
        "guard_over_always_95pct_prompt_bootstrap_ci": interval, "prompt_counts": counts,
        "interpretation": interpretation, "per_prompt": prompts,
        "primary_medians_exact_match": True,
        "correctness_scope": {"reference": "FORMAL_ANALYSIS.json:correctness; frozen target-only generated IDs",
                              "direct_id_exact_pairs": exact, "mismatches": 0},
        "provenance_note": "Archive hashes verified; original freeze-hash metadata defect, recovery, and STOPPED markers retained. Aggregate results already known; no blinding or preregistration of this contrast.",
        "no_new_measurement": True, "new_model_execution": False, "energy": "NOT_CLAIMED",
        "analysis_choices_changed_after_result": False,
        "scope": "One M4 model/runtime pair, fixed k=2, frozen held-out prompts, post-prefill timing; prompt interval excludes session/recalibration variation.",
    }


def report(result):
    value = result["geometric_mean_guard_over_always"]
    lo, hi = result["guard_over_always_95pct_prompt_bootstrap_ci"]
    c = result["prompt_counts"]
    finding = {"GUARD_HIGHER_LATENCY": "The interval lies entirely above parity: Guard had higher latency than Always-Spec on this frozen comparison.",
               "GUARD_LOWER_LATENCY": "The interval lies entirely below parity: Guard had lower latency than Always-Spec on this frozen comparison.",
               "INTERVAL_INCLUDES_PARITY": "The interval includes parity and does not establish a latency difference under this interval."}[result["interpretation"]]
    return f"""# M4 Guard / Always-Spec paired secondary report

Reviewer-requested **post-study paired secondary analysis**, not the registered
primary endpoint or a preregistration. Aggregate results were already known.
The committed plan fixes all choices; none changed after seeing this result.

Guard / Always-Spec geometric-mean latency ratio: **{value!r}**.
95% paired prompt-bootstrap interval: **[{lo!r}, {hi!r}]**.
Values above one mean Guard is slower. {finding}

Prompt medians: Guard faster **{c['guard_faster']}**, Always-Spec faster
**{c['always_faster']}**, exact ties **{c['ties']}** (60 total).
These counts are descriptive; no subgroup or additional tests were performed.

The verified archive SHA-256 is
`{ARCHIVE_SHA}`; formal attempt
`{FORMAL_ID}`. All 540 records reconstruct the same 60 prompt
medians as the immutable primary analysis. Each condition has three formal
repetitions. Both speculative conditions remain 180/180 direct generated-ID
exact against their matched target-only references.

For each prompt, divide its Guard median by its Always-Spec median, then take
`exp(mean(log(r_i)))`. Bootstrap the paired prompts 10,000 times with a fresh
standalone Python `random.Random(20260924)` stream in frozen held-out order;
each draw uses `randrange(60)`. Linearly interpolate sorted estimates at
`(10000-1)*0.025` and `(10000-1)*0.975`. Repetitions are not bootstrap units.
Full prompt medians, ratios, and source hashes are in the adjacent JSON.

No new measurements, model execution, timing, tuning, policy search, or changes
to primary results occurred. Energy remains NOT_CLAIMED. The original
freeze-hash metadata defect and stopped pipeline markers remain intact.
This comparison covers one M4 model/runtime pair, fixed k=2, one held-out set,
and one post-prefill boundary. Its interval excludes session and recalibration
variation. It supplies no robustness, risk-reduction, near-optimality, or
general controller-superiority claim.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, nargs="?", default=ARCHIVE)
    parser.add_argument("--output-dir", type=Path, default=BASE)
    parser.add_argument("--check", action="store_true", help="Reproduce and compare existing artifacts without writing")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="m4-secondary-") as tmp:
        if args.source.is_file():
            if digest(args.source) != ARCHIVE_SHA:
                raise ValueError("Archive SHA-256 differs from frozen canonical bundle")
            root = Path(tmp)
            manifest = extract_verified(args.source, root)
        else:
            root = args.source
            manifest = verify_extracted(root)
        result = analyze(root, manifest)
    outputs = {"GUARD_ALWAYS_SECONDARY_ANALYSIS.json": json.dumps(result, indent=2) + "\n",
               "GUARD_ALWAYS_SECONDARY_REPORT.md": report(result)}
    for name, content in outputs.items():
        path = args.output_dir / name
        if args.check:
            if path.read_text() != content:
                raise ValueError("Secondary artifact differs from exact reconstruction: " + name)
        else:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("analysis_status", "geometric_mean_guard_over_always",
                                           "guard_over_always_95pct_prompt_bootstrap_ci", "prompt_counts", "interpretation")}))


if __name__ == "__main__":
    main()
