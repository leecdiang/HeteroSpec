#!/usr/bin/env python3
"""Integrate PresentMon GPU Card Power over an exact QPC workload window."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path


def load_samples(path: Path) -> list[tuple[int, float]]:
    samples: list[tuple[int, float]] = []
    with path.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            raw = row.get("gpu_card_power_w", "")
            if not raw:
                continue
            qpc, power = int(row["qpc_timestamp"]), float(raw)
            if math.isfinite(power):
                samples.append((qpc, power))
    if any(b[0] <= a[0] for a, b in zip(samples, samples[1:])):
        raise ValueError("telemetry QPC timestamps are not strictly increasing")
    return samples


def interpolate(samples: list[tuple[int, float]], qpc: int) -> float:
    for (q0, p0), (q1, p1) in zip(samples, samples[1:]):
        if q0 <= qpc <= q1:
            fraction = (qpc - q0) / (q1 - q0)
            return p0 + fraction * (p1 - p0)
    raise ValueError("workload boundary is outside the telemetry sample range")


def integrate(samples: list[tuple[int, float]], start: int, end: int, frequency: int) -> dict:
    if start >= end or frequency <= 0:
        raise ValueError("invalid QPC workload window")
    if len(samples) < 2 or start < samples[0][0] or end > samples[-1][0]:
        raise ValueError("telemetry does not bracket the complete workload window")
    points = [(start, interpolate(samples, start))]
    points.extend((q, p) for q, p in samples if start < q < end)
    points.append((end, interpolate(samples, end)))
    energy = sum((p0 + p1) * 0.5 * (q1 - q0) / frequency for (q0, p0), (q1, p1) in zip(points, points[1:]))
    powers = [p for _, p in points]
    duration = (end - start) / frequency
    return {
        "method": "trapezoidal integration of PM_METRIC_GPU_CARD_POWER over exact QPC workload interval",
        "energy_boundary": "Intel Arc B570 graphics adapter board",
        "workload_start_qpc": start,
        "workload_end_qpc": end,
        "qpc_frequency_hz": frequency,
        "duration_s": duration,
        "sample_points_including_interpolated_boundaries": len(points),
        "board_energy_j": energy,
        "mean_board_power_w": energy / duration,
        "median_observed_board_power_w": statistics.median(powers),
        "peak_observed_board_power_w": max(powers),
    }


def self_test() -> None:
    constant = integrate([(0, 10.0), (10, 10.0), (20, 10.0)], 5, 15, 10)
    ramp = integrate([(0, 0.0), (10, 10.0), (20, 20.0)], 0, 20, 10)
    assert abs(constant["board_energy_j"] - 10.0) < 1e-12
    assert abs(ramp["board_energy_j"] - 20.0) < 1e-12
    print("PASS: synthetic constant-power and linear-ramp traces")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--telemetry", type=Path)
    parser.add_argument("--window", type=Path, help="JSON containing workload_start_qpc, workload_end_qpc, qpc_frequency_hz")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-tokens", type=int)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not (args.telemetry and args.window and args.output):
        parser.error("--telemetry, --window, and --output are required unless --self-test is used")
    window = json.loads(args.window.read_text(encoding="utf-8-sig"))
    result = integrate(
        load_samples(args.telemetry),
        int(window["workload_start_qpc"]),
        int(window["workload_end_qpc"]),
        int(window["qpc_frequency_hz"]),
    )
    result["telemetry_file"] = str(args.telemetry.resolve())
    if args.output_tokens is not None:
        result["output_tokens"] = args.output_tokens
        result["board_energy_j_per_output_token"] = result["board_energy_j"] / args.output_tokens if args.output_tokens else None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
