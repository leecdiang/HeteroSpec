#!/usr/bin/env python3
"""Summarize the frozen M4 confirmatory run at the prompt level."""

import argparse
import csv
import json
import math
import random
import statistics as stats
from pathlib import Path

import matplotlib.pyplot as plt


def geomean(values):
    return math.exp(stats.mean(math.log(value) for value in values))


def correlation(left, right):
    lmean, rmean = stats.mean(left), stats.mean(right)
    return sum((x-lmean)*(y-rmean) for x, y in zip(left, right)) / (
        sum((x-lmean)**2 for x in left) * sum((y-rmean)**2 for y in right)
    ) ** 0.5


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path, required=True)
    parser.add_argument("--prompt-csv", type=Path, required=True)
    parser.add_argument("--figure", type=Path, required=True)
    args = parser.parse_args()
    record = json.loads(args.input.read_text(encoding="utf-8"))
    pairs = []
    for question_id in record["selection"]["question_ids"]:
        for repetition in range(1, 4):
            block = [r for r in record["runs"] if r["question_id"] == question_id and r["repetition"] == repetition]
            baseline = next(r for r in block if r["condition"] == "baseline")
            spec = next(r for r in block if r["condition"] == "k2")
            bm, sm = baseline["metrics"], spec["metrics"]
            pairs.append({
                "question_id": question_id, "group": spec["group"], "repetition": repetition,
                "speedup": bm["decode_ms"] / sm["decode_ms"],
                "acceptance": sm["accepted_tokens"] / sm["drafted_tokens"],
                "accepted_per_round": sm["accepted_tokens"] / sm["verification_rounds"],
                "prompt_tokens": sm["prompt_tokens"],
                "draft_top1_probability": sm["draft_confidence"]["mean_top1_probability"],
                "draft_top1_top2_margin": sm["draft_confidence"]["mean_top1_top2_margin"],
                "draft_entropy_nats": sm["draft_confidence"]["mean_truncated_entropy_nats"],
                "package_energy_ratio": bm["energy_per_output_token"]["package_j_per_token"] / sm["energy_per_output_token"]["package_j_per_token"],
                "baseline_package_j_per_token": bm["energy_per_output_token"]["package_j_per_token"],
                "spec_package_j_per_token": sm["energy_per_output_token"]["package_j_per_token"],
            })
    prompts = []
    for question_id in record["selection"]["question_ids"]:
        rows = [row for row in pairs if row["question_id"] == question_id]
        prompt = {"question_id": question_id, "group": rows[0]["group"]}
        for field in [
            "acceptance", "accepted_per_round", "prompt_tokens", "draft_top1_probability",
            "draft_top1_top2_margin", "draft_entropy_nats", "baseline_package_j_per_token",
            "spec_package_j_per_token",
        ]:
            prompt[field] = stats.mean(row[field] for row in rows)
        prompt["speedup"] = geomean([row["speedup"] for row in rows])
        prompt["package_energy_ratio"] = geomean([row["package_energy_ratio"] for row in rows])
        prompts.append(prompt)

    rng = random.Random(20260907)
    bootstrap = sorted(
        geomean([rng.choice(prompts)["speedup"] for _ in prompts]) for _ in range(10000)
    )
    ordered = sorted(prompts, key=lambda row: row["accepted_per_round"])
    tertiles = {"low": ordered[:8], "medium": ordered[8:16], "high": ordered[16:]}
    correlations = {
        field: correlation([row[field] for row in prompts], [row["speedup"] for row in prompts])
        for field in [
            "acceptance", "accepted_per_round", "prompt_tokens", "draft_top1_probability",
            "draft_top1_top2_margin", "draft_entropy_nats",
        ]
    }
    summary = {
        "schema": "heterospec.m4_confirmatory_summary.v1",
        "prompt_count": len(prompts), "paired_repetitions": len(pairs),
        "exact_pairs": sum(r.get("exact_match", False) for r in record["runs"] if r["condition"] == "k2"),
        "geomean_speedup": geomean([row["speedup"] for row in prompts]),
        "median_speedup": stats.median(row["speedup"] for row in prompts),
        "bootstrap_95_ci": [bootstrap[249], bootstrap[9749]],
        "faster_prompts": sum(row["speedup"] > 1 for row in prompts),
        "package_energy_improvement": geomean([row["package_energy_ratio"] for row in prompts]),
        "mean_package_j_per_token": {
            "baseline": stats.mean(row["baseline_package_j_per_token"] for row in prompts),
            "k2": stats.mean(row["spec_package_j_per_token"] for row in prompts),
        },
        "tertiles": {
            name: {
                "accepted_per_round_range": [rows[0]["accepted_per_round"], rows[-1]["accepted_per_round"]],
                "geomean_speedup": geomean([row["speedup"] for row in rows]),
                "package_energy_improvement": geomean([row["package_energy_ratio"] for row in rows]),
                "faster_prompts": sum(row["speedup"] > 1 for row in rows),
            } for name, rows in tertiles.items()
        },
        "predictor_correlations_with_speedup": correlations,
        "memory_gate_counts": {
            status: sum(r["metrics"]["memory_gate"]["status"] == status for r in record["runs"])
            for status in ["PASS", "WARN", "FAIL"]
        },
    }
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with args.prompt_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(prompts[0]))
        writer.writeheader()
        writer.writerows(prompts)

    colors = {
        "math_reasoning": "#0072B2", "multi_turn": "#E69F00", "qa": "#009E73",
        "rag": "#CC79A7", "summarization": "#56B4E9", "translation": "#D55E00",
    }
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for group in colors:
        rows = [row for row in prompts if row["group"] == group]
        ax.scatter([row["accepted_per_round"] for row in rows], [row["speedup"] for row in rows],
                   label=group.replace("_", " "), color=colors[group], s=48, alpha=0.9)
    ax.axhline(1.0, color="black", linestyle="--", linewidth=1.2, label="break-even")
    ax.set_xlabel("Accepted tokens per verification round")
    ax.set_ylabel("Paired decode speedup (baseline / k=2)")
    ax.set_title("M4 confirmatory validation: acceptance governs loss,\nbut profitable region did not generalize")
    ax.grid(alpha=0.2)
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    args.figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.figure, dpi=180)
    fig.savefig(args.figure.with_suffix(".pdf"))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
