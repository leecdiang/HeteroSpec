#!/usr/bin/env python3
"""Integrate a single, explicitly selected power domain over exact QPC bounds."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def interpolate(t0: float, y0: float, t1: float, y1: float, t: float) -> float:
    if t1 == t0:
        return y0
    return y0 + (y1 - y0) * ((t - t0) / (t1 - t0))


def integrate(rows: list[tuple[float, float]], start: float, end: float) -> float:
    if start >= end or len(rows) < 2:
        raise ValueError("invalid integration interval or insufficient samples")
    rows = sorted(rows)
    if start < rows[0][0] or end > rows[-1][0]:
        raise ValueError("workload boundary is outside telemetry coverage")
    points: list[tuple[float, float]] = []
    for bound in (start, end):
        for left, right in zip(rows, rows[1:]):
            if left[0] <= bound <= right[0]:
                points.append((bound, interpolate(*left, *right, bound)))
                break
    points.extend((t, p) for t, p in rows if start < t < end)
    points.sort()
    return sum((b[0] - a[0]) * (a[1] + b[1]) / 2.0 for a, b in zip(points, points[1:]))


def self_test() -> None:
    assert abs(integrate([(0, 10), (1, 10), (2, 10)], 0.25, 1.75) - 15) < 1e-12
    assert abs(integrate([(0, 0), (1, 2), (2, 4)], 0, 2) - 4) < 1e-12


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--boundary", type=Path, required=True,
                        help="JSON containing start_qpc_ticks, end_qpc_ticks, qpc_frequency")
    parser.add_argument("--power-column", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test and not args.csv.exists():
        print("self-test: PASS")
        return
    boundary = json.loads(args.boundary.read_text(encoding="utf-8-sig"))
    frequency = float(boundary["qpc_frequency"])
    start = float(boundary["start_qpc_ticks"]) / frequency
    end = float(boundary["end_qpc_ticks"]) / frequency
    samples: list[tuple[float, float]] = []
    with args.csv.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            samples.append((float(row["qpc_ticks"]) / float(row["qpc_frequency"]),
                            float(row[args.power_column])))
    energy_j = integrate(samples, start, end)
    result = {
        "schema_version": 1,
        "method": "linear boundary interpolation plus trapezoidal integration",
        "power_column": args.power_column,
        "duration_s": end - start,
        "energy_j": energy_j,
        "mean_power_w": energy_j / (end - start),
        "sample_count_total": len(samples),
        "overlap_warning": "Do not add overlapping power domains."
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

