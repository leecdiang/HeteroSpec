#!/usr/bin/env python3
"""Summarize B570 PresentMon sampling stability and idle/load response."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    lo, hi = math.floor(position), math.ceil(position)
    return ordered[lo] if lo == hi else ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)


def summarize(values: list[float]) -> dict:
    return {
        "count": len(values),
        "mean": statistics.fmean(values) if values else None,
        "median": statistics.median(values) if values else None,
        "p95": percentile(values, 0.95) if values else None,
        "maximum": max(values) if values else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--telemetry", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--window", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    meta = json.loads(args.metadata.read_text(encoding="utf-8-sig"))
    window = json.loads(args.window.read_text(encoding="utf-8-sig"))
    rows = []
    with args.telemetry.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            rows.append({"qpc": int(row["qpc_timestamp"]), "power": float(row["gpu_card_power_w"]),
                         "util": float(row["gpu_utilization_pct"]), "frequency": float(row["gpu_frequency_mhz"])})
    frequency = int(meta["qpc_frequency"])
    intervals = [(b["qpc"] - a["qpc"]) * 1000 / frequency for a, b in zip(rows, rows[1:])]
    period = int(meta["polling_period_ms"])
    expected = round((rows[-1]["qpc"] - rows[0]["qpc"]) / frequency * 1000 / period) + 1
    start, end = int(window["workload_start_qpc"]), int(window["workload_end_qpc"])
    pre = [r for r in rows[1:] if r["qpc"] < start]
    load = [r for r in rows if start <= r["qpc"] <= end]
    post = [r for r in rows if r["qpc"] > end]
    result = {
        "telemetry": str(args.telemetry.resolve()),
        "adapter_name": meta["adapter_name"],
        "period_ms": period,
        "samples": len(rows),
        "timestamps_strictly_monotonic": all(b["qpc"] > a["qpc"] for a, b in zip(rows, rows[1:])),
        "sampling_interval_ms": summarize(intervals),
        "expected_samples_from_span": expected,
        "estimated_missing_samples": max(0, expected - len(rows)),
        "card_power_zero_samples_all": sum(r["power"] == 0 for r in rows),
        "card_power_zero_samples_after_initial": sum(r["power"] == 0 for r in rows[1:]),
        "segments": {},
    }
    for name, segment in (("pre_idle", pre), ("workload", load), ("post_idle", post)):
        result["segments"][name] = {
            "card_power_w": summarize([r["power"] for r in segment]),
            "gpu_utilization_pct": summarize([r["util"] for r in segment]),
            "gpu_frequency_mhz": summarize([r["frequency"] for r in segment]),
        }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
