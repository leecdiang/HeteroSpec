#!/usr/bin/env python3
"""Offline planning calculations. No network, model execution or repository mutation."""
import json
import math
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTRASTS = (
    ("QB", "AUTO"), ("WB-cut", "AUTO"), ("WB-rechunk", "AUTO"),
    ("WB-cut", "QB"), ("WB-rechunk", "QB"), ("WB-cut", "WB-rechunk"),
)
Z_SUM = statistics.NormalDist().inv_cdf(0.975) + statistics.NormalDist().inv_cdf(0.80)

def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))

def variance(dataset):
    assert dataset["independent_roots"] == 32
    rows = dataset["root_results"]
    assert len(rows) == 32 and len({r["root_id"] for r in rows}) == 32
    output = []
    for num, den in CONTRASTS:
        values = [
            math.log(r["baseline_over_AUTO"][num])
            - (0.0 if den == "AUTO" else math.log(r["baseline_over_AUTO"][den]))
            for r in rows
        ]
        sigma = statistics.stdev(values)
        output.append({
            "numerator": num, "denominator": den, "n": len(values),
            "sd_root_log": sigma,
            "approximate_mde32_reduction": 1 - math.exp(-Z_SUM * sigma / math.sqrt(32)),
            "approximate_n_for_3pct": math.ceil((Z_SUM * sigma / -math.log(.97)) ** 2),
        })
    return output

def main():
    historical = read("historical_variance.json")
    out = {
        "status": "PLANNING_ONLY_NO_DEVICE_EXECUTION",
        "z_sum": Z_SUM,
        "sources": historical["sources"],
        "historical_root_log_sd": {},
        "sensitivity": [],
        "request_budgets": [],
        "warnings": [
            "Historical root contrasts average four sessions of old arms.",
            "These are not new B4/P4 variance estimates or power guarantees.",
            "Normal approximation is illustrative and not a valid tiny-n recommendation.",
            "The 3% effect is against zero, not a lower confidence bound above 3%.",
            "Pilot requests and operator submissions must remain in cumulative accounting.",
        ],
    }
    for host in ("rtx", "b570"):
        calculated = variance(read(f"historical_{host}_analysis.json"))
        for expected, actual in zip(historical["variance"][host], calculated):
            assert expected["num"] == actual["numerator"]
            assert expected["den"] == actual["denominator"]
            assert math.isclose(expected["sd_root_log"], actual["sd_root_log"], rel_tol=1e-12)
        out["historical_root_log_sd"][host] = calculated
    for sigma in (.045, .045 * math.sqrt(2), .0675, .09):
        out["sensitivity"].append({
            "assumed_root_log_sd": sigma,
            "mde_reduction_by_roots": {
                str(n): 1 - math.exp(-Z_SUM * sigma / math.sqrt(n))
                for n in (16, 32, 64)
            },
            "approximate_n_for_3pct": math.ceil((Z_SUM * sigma / -math.log(.97)) ** 2),
            "approximate_n_for_1pct": math.ceil((Z_SUM * sigma / -math.log(.99)) ** 2),
        })
    for n in (8, 16, 32, 48, 64):
        out["request_budgets"].append({
            "roots": n,
            "two_arm": {"qualification": 6*n, "measured": 4*n, "warmup": 4*n, "total": 14*n},
            "three_arm": {"qualification": 8*n, "measured": 6*n, "warmup": 6*n, "total": 20*n},
        })
    assert 4*(4+5+8+32) + 16*2 + 16*2*2*11 + 4*2 == 940
    out["operator_smoke"] = {
        "cases": 16, "qualification_graph_submissions": 228,
        "warm_and_measured_graph_submissions": 704,
        "optional_profiler_graph_submissions": 8,
        "planned_graph_submissions": 940, "hard_allowance": 1024,
    }
    out["two_arm_main32_logits_raw_bytes"] = 32*128*151936*4*4
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()

