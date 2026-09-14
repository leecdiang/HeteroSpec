#!/usr/bin/env python3
"""Apply the preregistered speculative-decoding break-even gate."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def classify(optimistic: float, central: float, margin: float) -> str:
    if optimistic < 1.0:
        return "NO-GO"
    if central >= 1.0 + margin:
        return "GO"
    return "BORDERLINE"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft-csv", type=Path, required=True, help="CSV columns: device,context,draft_k2_ms")
    parser.add_argument("--target-token-ms", type=float, required=True)
    parser.add_argument("--verification-factor", type=float, required=True)
    parser.add_argument("--residual-ms", type=float, required=True)
    parser.add_argument("--central-committed", type=float, required=True)
    parser.add_argument("--optimistic-committed", type=float, default=3.0)
    parser.add_argument("--go-margin", type=float, default=0.05)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not (1.0 <= args.central_committed <= args.optimistic_committed <= 3.0):
        parser.error("for frozen k=2, require 1 <= central <= optimistic <= 3 committed output tokens/round")
    if args.target_token_ms <= 0:
        parser.error("target-token-ms must be positive")
    if min(args.verification_factor, args.residual_ms) < 0:
        parser.error("verification-factor and residual-ms must be non-negative")

    rows = []
    with args.draft_csv.open(newline="", encoding="utf-8-sig") as handle:
        for source in csv.DictReader(handle):
            draft = float(source["draft_k2_ms"])
            denominator = draft + args.verification_factor * args.target_token_ms + args.residual_ms
            optimistic = args.target_token_ms * args.optimistic_committed / denominator
            central = args.target_token_ms * args.central_committed / denominator
            rows.append({
                "device": source["device"],
                "context": int(source["context"]),
                "draft_k2_ms": draft,
                "central_speedup_predicted": central,
                "optimistic_speedup_upper_bound": optimistic,
                "classification": classify(optimistic, central, args.go_margin),
            })

    payload = {
        "schema": "heterospec.358h.threshold_summary.v1",
        "inputs": {
            "target_token_ms": args.target_token_ms,
            "verification_factor": args.verification_factor,
            "residual_ms": args.residual_ms,
            "central_committed": args.central_committed,
            "optimistic_committed": args.optimistic_committed,
            "go_margin": args.go_margin,
        },
        "formula": "speedup = T_b * C / (T_d(k) + V_k * T_b + T_x)",
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
