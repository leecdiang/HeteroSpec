#!/usr/bin/env python3
"""Add uncertainty and drift diagnostics to a qualification-only overhead run."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def rank(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="stable")
    result = np.empty_like(values, dtype=float)
    result[order] = np.arange(len(values), dtype=float)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--bootstrap-seed", type=int, default=572)
    parser.add_argument("--bootstrap-resamples", type=int, default=10_000)
    args = parser.parse_args()

    source = args.run_directory / "overhead_qualification.json"
    result = json.loads(source.read_text(encoding="utf-8-sig"))
    records = result["records"]
    off = np.asarray([row["inner_duration_ms"] for row in records if row["condition"] == "OFF"], dtype=float)
    on = np.asarray([row["inner_duration_ms"] for row in records if row["condition"] == "ON"], dtype=float)
    rng = np.random.default_rng(args.bootstrap_seed)
    off_boot = np.median(rng.choice(off, (args.bootstrap_resamples, len(off)), replace=True), axis=1)
    on_boot = np.median(rng.choice(on, (args.bootstrap_resamples, len(on)), replace=True), axis=1)
    signed = (on_boot / off_boot - 1.0) * 100.0
    durations = np.asarray([row["inner_duration_ms"] for row in records], dtype=float)
    indices = np.arange(1, len(records) + 1, dtype=float)
    rho = float(np.corrcoef(rank(indices), rank(durations))[0, 1])
    midpoint = len(records) // 2
    sensor_meta = []
    for path in sorted(args.run_directory.glob("*-rapl.json")):
        sensor_meta.append(json.loads(path.read_text(encoding="utf-8-sig")))

    analysis = {
        "schema": "heterospec.358h.telemetry_overhead_analysis.v1",
        "formal_measurement": False,
        "performance_claim_prohibited": True,
        "source": str(source),
        "frozen_gate_result": {
            "absolute_median_overhead_percent": result["absolute_overhead_percent"],
            "threshold_percent": result["threshold_percent"],
            "qualification_pass": result["qualification_pass"],
        },
        "descriptive_uncertainty_not_used_as_gate": {
            "method": "independent nonparametric bootstrap of ON and OFF medians",
            "seed": args.bootstrap_seed,
            "resamples": args.bootstrap_resamples,
            "signed_overhead_percent_ci95": [float(np.quantile(signed, 0.025)), float(np.quantile(signed, 0.975))],
            "probability_absolute_overhead_le_1_percent": float(np.mean(np.abs(signed) <= 1.0)),
        },
        "dispersion": {
            "off_cv_percent": float(np.std(off, ddof=1) / np.mean(off) * 100.0),
            "on_cv_percent": float(np.std(on, ddof=1) / np.mean(on) * 100.0),
        },
        "order_and_thermal_diagnostics": {
            "spearman_index_vs_duration": rho,
            "first_half_median_ms": float(np.median(durations[:midpoint])),
            "second_half_median_ms": float(np.median(durations[midpoint:])),
            "second_vs_first_half_percent": float((np.median(durations[midpoint:]) / np.median(durations[:midpoint]) - 1.0) * 100.0),
            "interpretation": "descriptive only; randomized interleaving protects the frozen median comparison",
        },
        "collector": {
            "metadata_files": len(sensor_meta),
            "max_process_cpu_seconds": max((row["collector_process_cpu_seconds"] for row in sensor_meta), default=None),
            "max_cpu_fraction_of_wall": max((row["collector_cpu_fraction_of_wall"] for row in sensor_meta), default=None),
            "max_collection_call_ms": max((row["max_collection_call_ms"] for row in sensor_meta), default=None),
        },
    }
    output = args.run_directory / "overhead_analysis.json"
    output.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(analysis, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

