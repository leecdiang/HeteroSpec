#!/usr/bin/env python3
"""Analyze randomized/interleaved telemetry OFF/ON timing observations."""

from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path


def percentile(values: list[float], p: float) -> float:
    values = sorted(values)
    x = (len(values) - 1) * p
    lo = int(x)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (x - lo)


def cv(values: list[float]) -> float:
    return statistics.stdev(values) / statistics.fmean(values)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = json.loads(args.input.read_text(encoding="utf-8-sig"))
    values = {condition: [float(r["llama_bench_avg_ns"]) for r in rows if r["condition"] == condition]
              for condition in ("OFF", "ON")}
    medians = {condition: statistics.median(v) for condition, v in values.items()}
    ratio = medians["ON"] / medians["OFF"]
    rng = random.Random(570)
    bootstrap = []
    for _ in range(10000):
        off = [rng.choice(values["OFF"]) for _ in values["OFF"]]
        on = [rng.choice(values["ON"]) for _ in values["ON"]]
        bootstrap.append(statistics.median(on) / statistics.median(off))
    result = {
        "elapsed_metric": "llama-bench avg_ns, non-formal Qwen3-0.6B PP1024",
        "repetitions_per_condition": {key: len(value) for key, value in values.items()},
        "median_off_ns": medians["OFF"],
        "median_on_ns": medians["ON"],
        "on_off_ratio": ratio,
        "change_percent": (ratio - 1.0) * 100,
        "cv_off": cv(values["OFF"]),
        "cv_on": cv(values["ON"]),
        "bootstrap_ratio_ci95": [percentile(bootstrap, 0.025), percentile(bootstrap, 0.975)],
        "gate_absolute_change_le_1_percent": abs(ratio - 1.0) <= 0.01,
        "individual": rows,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
