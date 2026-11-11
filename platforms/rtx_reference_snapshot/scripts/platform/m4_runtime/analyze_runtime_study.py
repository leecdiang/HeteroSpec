#!/usr/bin/env python3
"""Analyze a complete formal attempt with prompt-level uncertainty."""

import argparse
import hashlib
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "benchmarks/m4_runtime"
RUNS = ROOT / "runs/m4/runtime_profitability_control_20260924"
SEED = 20260924


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gm(values):
    if not values or any(x <= 0 for x in values):
        raise ValueError("Geometric mean requires positive values")
    return math.exp(statistics.mean(math.log(x) for x in values))


def quantile(values, q):
    sorted_values = sorted(values)
    index = (len(sorted_values) - 1) * q
    lo = math.floor(index)
    hi = math.ceil(index)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (index - lo)


def ci_gm(values, rng):
    n = len(values)
    samples = [gm([values[rng.randrange(n)] for _ in range(n)]) for _ in range(10000)]
    return [quantile(samples, 0.025), quantile(samples, 0.975)]


def summarize(task_rows, rng):
    speedup_guard = [x["target_median_ns"] / x["guard_median_ns"] for x in task_rows]
    speedup_always = [x["target_median_ns"] / x["always_median_ns"] for x in task_rows]
    regret = [x["guard_median_ns"] / x["oracle_median_ns"] for x in task_rows]
    additive = [(x["guard_median_ns"] - x["oracle_median_ns"]) / 1e6 for x in task_rows]
    return {
        "prompt_count": len(task_rows),
        "geometric_mean_target_over_guard": gm(speedup_guard),
        "target_over_guard_95pct_prompt_bootstrap_ci": ci_gm(speedup_guard, rng),
        "geometric_mean_target_over_always_spec": gm(speedup_always),
        "target_over_always_spec_95pct_prompt_bootstrap_ci": ci_gm(speedup_always, rng),
        "geometric_mean_guard_over_oracle": gm(regret),
        "guard_over_oracle_95pct_prompt_bootstrap_ci": ci_gm(regret, rng),
        "median_additive_oracle_regret_ms": statistics.median(additive),
        "p90_additive_oracle_regret_ms": quantile(additive, 0.9),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", required=True)
    args = parser.parse_args()
    freeze = json.loads((BASE / "CALIBRATION_FREEZE.json").read_text())
    qualification = json.loads((BASE / "QUALIFICATION_REPORT.json").read_text())
    if qualification["status"] != "PASS":
        raise RuntimeError("Qualification did not pass")
    path = RUNS / "formal" / args.attempt
    complete = json.loads((path / "completion.json").read_text())
    raw = path / "observations.jsonl"
    if complete["status"] != "COMPLETE" or complete["observations_sha256"] != sha(raw):
        raise RuntimeError("Incomplete or changed formal attempt")
    with raw.open(encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream]
    if len(rows) != 60 * 3 * 3 or sorted(row["observation_index"] for row in rows) != list(range(len(rows))):
        raise RuntimeError("Formal schedule incomplete")
    marker = json.loads((RUNS / f"FORMAL_ATTEMPT_{args.attempt}_STARTED").read_text())
    if marker["freeze_sha256"] != sha(BASE / "CALIBRATION_FREEZE.json"):
        raise RuntimeError("Formal freeze changed")
    by = {(x["workload_family"], x["task_id"], x["repetition"], x["condition"]): x for x in rows}
    if len(by) != len(rows):
        raise RuntimeError("Duplicate formal condition")
    split = json.loads((BASE / "HELDOUT_SPLIT.json").read_text())["tasks"]
    mismatches = []
    task_rows = []
    guard_rows = []
    all_spec_rows = []
    for task in split:
        identity = (task["workload_family"], task["task_id"])
        times = defaultdict(list)
        for rep in range(3):
            ref = by[(*identity, rep, "TARGET_ONLY")]["result"]
            for condition in ("TARGET_ONLY", "ALWAYS_SPEC_K2", "GUARD_K2"):
                result = by[(*identity, rep, condition)]["result"]
                times[condition].append(result["end_to_end_ns"])
                if condition != "TARGET_ONLY" and result["generated_token_ids"] != ref["generated_token_ids"]:
                    other = result["generated_token_ids"]
                    target = ref["generated_token_ids"]
                    idx = next((i for i, (a, b) in enumerate(zip(target, other)) if a != b), min(len(target), len(other)))
                    mismatches.append({
                        "workload_family": identity[0], "task_id": identity[1],
                        "repetition": rep, "condition": condition,
                        "first_mismatch_index": idx,
                        "target_id": target[idx] if idx < len(target) else None,
                        "other_id": other[idx] if idx < len(other) else None,
                        "fallback_round": result["fallback_round"],
                        "rounds": result["rounds"],
                    })
            guard_rows.append(by[(*identity, rep, "GUARD_K2")]["result"])
            all_spec_rows.append(by[(*identity, rep, "ALWAYS_SPEC_K2")]["result"])
        target_median = statistics.median(times["TARGET_ONLY"])
        always_median = statistics.median(times["ALWAYS_SPEC_K2"])
        guard_median = statistics.median(times["GUARD_K2"])
        task_rows.append({
            "workload_family": identity[0], "task_id": identity[1], "stratum": task["stratum"],
            "target_median_ns": target_median, "always_median_ns": always_median,
            "guard_median_ns": guard_median,
            "oracle_median_ns": min(target_median, always_median),
        })
    admissible = {condition: not any(x["condition"] == condition for x in mismatches)
                  for condition in ("ALWAYS_SPEC_K2", "GUARD_K2")}
    rng = random.Random(SEED)
    result = {
        "schema": "heterospec.m4_runtime.formal_analysis.v0.1",
        "analyzed_utc": datetime.now(timezone.utc).isoformat(),
        "attempt_id": args.attempt,
        "formal_observations_sha256": sha(raw),
        "freeze_sha256": sha(BASE / "CALIBRATION_FREEZE.json"),
        "qualification_sha256": sha(BASE / "QUALIFICATION_REPORT.json"),
        "energy": "NOT_CLAIMED", "bootstrap_seed": SEED,
        "bootstrap_resamples": 10000, "bootstrap_unit": "prompt",
        "correctness": {
            "required_direct_id_pairs_per_condition": 180,
            "mismatch_count": len(mismatches), "mismatches": mismatches,
            "performance_admissible": admissible,
        },
        "selected_policy": freeze["selected"],
        "target_reference_ns_per_token": freeze["target_reference_ns_per_token"],
        "per_prompt": task_rows,
    }
    if all(admissible.values()):
        result["overall"] = summarize(task_rows, rng)
        strata = defaultdict(list)
        for task in task_rows:
            strata[task["workload_family"]].append(task)
            strata[f"{task['workload_family']}:{task['stratum']}"].append(task)
        result["strata"] = {name: summarize(group, rng) for name, group in sorted(strata.items())}
        fallback = [x for x in guard_rows if x["fallback_triggered"]]
        proposed = sum(round_["proposed"] for x in guard_rows for round_ in x["rounds"])
        accepted = sum(round_["accepted"] for x in guard_rows for round_ in x["rounds"])
        committed = []
        for x in guard_rows:
            prior = 0
            for round_ in x["rounds"]:
                committed.append(round_["committed"] - prior)
                prior = round_["committed"]
        guard_total = sum(x["end_to_end_ns"] for x in guard_rows)
        guard_compute = sum(x["guard_compute_ns"] for x in guard_rows)
        transition = sum(x["fallback_transition_ns"] for x in guard_rows)
        result["control"] = {
            "fallback_request_fraction": len(fallback) / len(guard_rows),
            "fallback_round_distribution": dict(sorted(Counter(x["fallback_round"] for x in fallback).items())),
            "speculative_committed_token_fraction": sum(x["speculative_committed_token_count"] for x in guard_rows) /
                sum(x["generated_token_count"] for x in guard_rows),
            "target_only_committed_token_fraction": sum(x["target_only_committed_token_count"] for x in guard_rows) /
                sum(x["generated_token_count"] for x in guard_rows),
            "accepted_draft_fraction": accepted / proposed if proposed else None,
            "mean_committed_tokens_per_verification_round": statistics.mean(committed) if committed else None,
            "guard_compute_total_ns": guard_compute,
            "fallback_transition_total_ns": transition,
            "control_total_ns": guard_compute + transition,
            "control_fraction_of_guard_latency": (guard_compute + transition) / guard_total,
            "mean_guard_compute_ns_per_request": guard_compute / len(guard_rows),
            "mean_transition_ns_per_fallback": transition / len(fallback) if fallback else 0,
            "always_spec_accepted_draft_fraction": (
                sum(r["accepted"] for x in all_spec_rows for r in x["rounds"]) /
                sum(r["proposed"] for x in all_spec_rows for r in x["rounds"])
            ),
        }
    output = BASE / "FORMAL_ANALYSIS.json"
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# M4 prospective runtime profitability-control study",
             "", f"Formal attempt: `{args.attempt}`. Selected policy: `{freeze['selected']['candidate_id']}`.",
             f"Direct token-ID pairs: 180 per speculative condition; mismatches: {len(mismatches)}.",
             "Energy: NOT_CLAIMED.", ""]
    if all(admissible.values()):
        overall = result["overall"]
        lines += [
            "## Primary results", "",
            "| Measure | Estimate | 95% prompt bootstrap CI |", "| --- | ---: | ---: |",
            f"| Target / guard geometric mean | {overall['geometric_mean_target_over_guard']:.4f} | "
            f"{overall['target_over_guard_95pct_prompt_bootstrap_ci'][0]:.4f}–{overall['target_over_guard_95pct_prompt_bootstrap_ci'][1]:.4f} |",
            f"| Target / fixed k=2 geometric mean | {overall['geometric_mean_target_over_always_spec']:.4f} | "
            f"{overall['target_over_always_spec_95pct_prompt_bootstrap_ci'][0]:.4f}–{overall['target_over_always_spec_95pct_prompt_bootstrap_ci'][1]:.4f} |",
            f"| Guard / offline oracle geometric mean | {overall['geometric_mean_guard_over_oracle']:.4f} | "
            f"{overall['guard_over_oracle_95pct_prompt_bootstrap_ci'][0]:.4f}–{overall['guard_over_oracle_95pct_prompt_bootstrap_ci'][1]:.4f} |",
            "", f"Median additive oracle regret: {overall['median_additive_oracle_regret_ms']:.2f} ms; "
            f"p90: {overall['p90_additive_oracle_regret_ms']:.2f} ms.", "",
            "## Control trace", "",
            f"Fallback fraction: {result['control']['fallback_request_fraction']:.3f}; "
            f"speculative committed-token fraction: {result['control']['speculative_committed_token_fraction']:.3f}; "
            f"accepted draft fraction: {result['control']['accepted_draft_fraction']:.3f}.",
            f"Measured guard and transition work: {result['control']['control_total_ns']/1e6:.2f} ms total "
            f"({result['control']['control_fraction_of_guard_latency']:.4%} of guard latency).", "",
            "## Prospective strata", "",
            "| Stratum | Prompts | Target / guard | Guard / oracle |", "| --- | ---: | ---: | ---: |",
        ]
        for name, group in result["strata"].items():
            lines.append(f"| {name} | {group['prompt_count']} | {group['geometric_mean_target_over_guard']:.4f} | "
                         f"{group['geometric_mean_guard_over_oracle']:.4f} |")
        lines += ["", "Bootstrap resampled prompts 10,000 times with seed 20260924; repetitions were reduced to "
                  "per-prompt medians before resampling. The offline oracle is descriptive and was not available to the policy.", ""]
    else:
        lines += ["## Performance admissibility", "",
                  "At least one speculative condition failed direct token-ID equality. Performance claims for that "
                  "condition are inadmissible. See `FORMAL_ANALYSIS.json` for mismatch positions and the full trace.", ""]
    (BASE / "FORMAL_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"admissible": admissible, "mismatches": len(mismatches),
                      "overall": result.get("overall"), "control": result.get("control")}, indent=2))


if __name__ == "__main__":
    main()
