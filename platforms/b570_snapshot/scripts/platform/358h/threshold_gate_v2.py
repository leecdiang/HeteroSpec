#!/usr/bin/env python3
"""Deterministic 358H Phase-2 break-even classifier.

The calculator consumes only same-platform observations and makes no performance
measurements itself. T_x is a preregistered favorable-bound constant (zero), so
the output predicts eligibility for Phase 3 rather than claiming realized speedup.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def samples(row: dict, name: str) -> np.ndarray:
    value = np.asarray(row[name], dtype=float)
    if value.ndim != 1 or len(value) < 3 or not np.all(np.isfinite(value)) or np.any(value < 0):
        raise ValueError(f"{name} must contain at least three finite, nonnegative samples")
    return value


def classify_point(row: dict, seed: int, resamples: int) -> dict:
    td = samples(row, "draft_round_ms_samples")
    tb = samples(row, "target_token_ms_samples")
    v2 = samples(row, "verification_fraction_samples")
    tx = float(row.get("residual_ms_favorable_bound", 0.0))
    if tx != 0.0:
        raise ValueError("frozen 358H v1 gate requires T_x=0 favorable bound")
    rng = np.random.default_rng(seed + int(row["context_tokens"]))
    td_b = rng.choice(td, resamples, replace=True)
    tb_b = rng.choice(tb, resamples, replace=True)
    v2_b = rng.choice(v2, resamples, replace=True)

    def speedup(c: int) -> np.ndarray:
        return tb_b * c / (td_b + v2_b * tb_b + tx)

    central = speedup(2)
    optimistic = speedup(3)
    central_summary = {
        "median": float(np.median(central)),
        "ci95": [float(np.quantile(central, 0.025)), float(np.quantile(central, 0.975))],
    }
    optimistic_summary = {
        "median": float(np.median(optimistic)),
        "ci95": [float(np.quantile(optimistic, 0.025)), float(np.quantile(optimistic, 0.975))],
    }
    exact = row.get("verification_exactness_admissible") is True
    if not exact:
        classification, reason = "NO-GO", "verification path did not pass the frozen exactness-admissibility gate"
    elif optimistic_summary["ci95"][1] < 1.0:
        classification, reason = "NO-GO", "optimistic 95% upper bound is below 1.00"
    elif central_summary["median"] >= 1.05 and central_summary["ci95"][0] > 1.0:
        classification, reason = "GO", "central median is at least 1.05 and its 95% lower bound exceeds 1.00"
    else:
        classification, reason = "BORDERLINE", "neither the frozen GO nor NO-GO rule is satisfied"
    return {
        "context_tokens": int(row["context_tokens"]),
        "classification": classification,
        "reason": reason,
        "central_C2": central_summary,
        "optimistic_C3": optimistic_summary,
        "T_x_ms": tx,
        "verification_exactness_admissible": exact,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", type=int, default=20260919)
    parser.add_argument("--resamples", type=int, default=10_000)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8-sig"))
    points = [classify_point(row, args.seed, args.resamples) for row in payload["context_points"]]
    labels = [point["classification"] for point in points]
    if labels and all(label == "NO-GO" for label in labels):
        overall = "NO-GO"
    elif labels and all(label == "GO" for label in labels):
        overall = "GO"
    else:
        overall = "BORDERLINE"
    result = {
        "schema": "heterospec.358h.phase2_gate.v1",
        "formal_measurement": False,
        "input": str(args.input),
        "bootstrap": {"method": "independent empirical resampling", "seed": args.seed, "resamples": args.resamples},
        "formula": "speedup = T_b*C/(T_d(2)+V_2*T_b+T_x)",
        "T_x_policy": "fixed zero favorable bound; output is predictive eligibility, not realized end-to-end speedup",
        "overall_classification": overall,
        "phase3_entry": "Only GO or BORDERLINE context points may enter Phase 3; stop if every point is NO-GO.",
        "points": points,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

