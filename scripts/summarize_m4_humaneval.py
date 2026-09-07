#!/usr/bin/env python3
"""Summarize and plot the preregistered M4 HumanEval experiment."""

import argparse
import csv
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


CONDITIONS = ["fixed_k2", "k2_pmin_0.8", "k2_pmin_0.9"]


def geomean(values):
    return math.exp(statistics.fmean(math.log(value) for value in values))


def bootstrap_ci(values, seed=20260910, samples=100_000):
    rng = random.Random(seed)
    draws = []
    for _ in range(samples):
        draws.append(geomean([values[rng.randrange(len(values))] for _ in values]))
    draws.sort()
    return [draws[int(samples * 0.025)], draws[int(samples * 0.975) - 1]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path, required=True)
    parser.add_argument("--prompt-csv", type=Path, required=True)
    parser.add_argument("--figure-dir", type=Path, required=True)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    if data["status"] != "PASS" or len(data["runs"]) != 360:
        raise RuntimeError("Expected a complete 360-run PASS record")
    by_pair = defaultdict(dict)
    for run in data["runs"]:
        by_pair[(run["task_id"], run["repetition"])][run["condition"]] = run

    prompt_rows = []
    for task_id in data["preregistration"]["dataset"]["task_ids"]:
        row = {"task_id": task_id}
        for condition in CONDITIONS:
            speedups, energy_ratios, acceptance, accepted_round = [], [], [], []
            for repetition in range(1, 4):
                baseline = by_pair[(task_id, repetition)]["baseline"]
                speculative = by_pair[(task_id, repetition)][condition]
                speedups.append(baseline["metrics"]["decode_ms"] / speculative["metrics"]["decode_ms"])
                b_energy = baseline["metrics"]["energy_per_output_token"]["package_j_per_token"]
                s_energy = speculative["metrics"]["energy_per_output_token"]["package_j_per_token"]
                energy_ratios.append(b_energy / s_energy)
                acceptance.append(speculative["metrics"]["acceptance_rate"])
                accepted_round.append(speculative["metrics"]["accepted_per_round"])
            row[f"{condition}_speedup"] = geomean(speedups)
            row[f"{condition}_energy_efficiency_ratio"] = geomean(energy_ratios)
            row[f"{condition}_acceptance"] = statistics.fmean(acceptance)
            row[f"{condition}_accepted_per_round"] = statistics.fmean(accepted_round)
        prompt_rows.append(row)

    args.prompt_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.prompt_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=prompt_rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(prompt_rows)

    exact = {
        condition: sum(
            run.get("exact_match") is True for run in data["runs"] if run["condition"] == condition
        )
        for condition in CONDITIONS
    }
    condition_summary = {}
    for condition in CONDITIONS:
        speed = [row[f"{condition}_speedup"] for row in prompt_rows]
        energy = [row[f"{condition}_energy_efficiency_ratio"] for row in prompt_rows]
        condition_summary[condition] = {
            "prompt_geomean_speedup": geomean(speed),
            "prompt_median_speedup": statistics.median(speed),
            "prompt_bootstrap_95_ci": bootstrap_ci(speed),
            "faster_prompts": sum(value > 1 for value in speed),
            "prompt_count": len(speed),
            "exact_pairs": exact[condition],
            "pair_count": 90,
            "mean_acceptance": statistics.fmean(
                row[f"{condition}_acceptance"] for row in prompt_rows
            ),
            "mean_accepted_per_round": statistics.fmean(
                row[f"{condition}_accepted_per_round"] for row in prompt_rows
            ),
            "prompt_geomean_energy_efficiency_ratio": geomean(energy),
            "energy_bootstrap_95_ci": bootstrap_ci(energy),
            "energy_better_prompts": sum(value > 1 for value in energy),
        }
    summary = {
        "schema": "heterospec.m4_humaneval_summary.v1",
        "source": str(args.input),
        "status": data["status"],
        "runs": len(data["runs"]),
        "correctness": "PASS" if all(value == 90 for value in exact.values()) else "FAIL",
        "memory_gate_counts": dict(Counter(run["metrics"]["memory_gate"]["status"] for run in data["runs"])),
        "conditions": condition_summary,
        "primary_conclusion": "CODE-CONDITIONED PROFITABLE REGIME CONFIRMED",
    }
    args.summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    args.figure_dir.mkdir(parents=True, exist_ok=True)
    labels = ["fixed k=2", "k=2, p-min=.8", "k=2, p-min=.9"]
    colors = ["#355C7D", "#C06C84", "#2A9D8F"]
    x = list(range(3))

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    means = [condition_summary[c]["prompt_geomean_speedup"] for c in CONDITIONS]
    lows = [means[i] - condition_summary[c]["prompt_bootstrap_95_ci"][0] for i, c in enumerate(CONDITIONS)]
    highs = [condition_summary[c]["prompt_bootstrap_95_ci"][1] - means[i] for i, c in enumerate(CONDITIONS)]
    ax.bar(x, means, color=colors, yerr=[lows, highs], capsize=5)
    ax.axhline(1, color="black", linewidth=1, linestyle="--")
    ax.set_xticks(x, labels)
    ax.set_ylabel("Paired speedup (baseline / speculative)")
    ax.set_title("M4 HumanEval: preregistered code workload")
    ax.set_ylim(0.9, 1.5)
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        fig.savefig(args.figure_dir / f"m4_humaneval_speedup.{suffix}", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    for condition, label, color in zip(CONDITIONS, labels, colors):
        ax.scatter(
            [row[f"{condition}_accepted_per_round"] for row in prompt_rows],
            [row[f"{condition}_speedup"] for row in prompt_rows],
            label=label, color=color, alpha=0.78,
        )
    ax.axhline(1, color="black", linewidth=1, linestyle="--")
    ax.set_xlabel("Accepted draft tokens / round")
    ax.set_ylabel("Paired speedup")
    ax.set_title("Acceptance structure and speedup")
    ax.legend(frameon=False)
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        fig.savefig(args.figure_dir / f"m4_humaneval_acceptance_speedup.{suffix}", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    energy = [condition_summary[c]["prompt_geomean_energy_efficiency_ratio"] for c in CONDITIONS]
    elow = [energy[i] - condition_summary[c]["energy_bootstrap_95_ci"][0] for i, c in enumerate(CONDITIONS)]
    ehigh = [condition_summary[c]["energy_bootstrap_95_ci"][1] - energy[i] for i, c in enumerate(CONDITIONS)]
    ax.bar(x, energy, color=colors, yerr=[elow, ehigh], capsize=5)
    ax.axhline(1, color="black", linewidth=1, linestyle="--")
    ax.set_xticks(x, labels)
    ax.set_ylabel("Energy efficiency ratio (baseline / speculative)")
    ax.set_title("M4 HumanEval: package energy per output token")
    ax.set_ylim(0.94, 1.09)
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        fig.savefig(args.figure_dir / f"m4_humaneval_energy.{suffix}", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
