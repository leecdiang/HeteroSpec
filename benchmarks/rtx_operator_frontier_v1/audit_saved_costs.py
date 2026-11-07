"""Recompute PR168's published service costs; no model calls or raw-tensor replay.

Inputs below were transcribed from the connected GitHub file at the pinned
commit. This validates arithmetic, not the authenticity of underlying GPU runs.
Run with Python 3.10+; stdout is a JSON review record.
"""
import json
import math

SOURCE = "9c79594f679ea4aad1956d8a385fdf6a7352d892"
ARMS = ["R", "S1", "PQ-ext", "QB-local", "WB-cut", "native32", "native-full", "native-ordinary"]
ROWS = [
    [1024, "MATH/algebra/train/687", 0, 6.0255422, 8.4604896, 3.3543782, 3.3667498, 3.2787875, 2.1111329, 1.7588005, 2.2670062],
    [1024, "MATH/algebra/train/687", 1, 6.8076036, 9.1693653, 3.3349261, 3.0019119, 3.1282012, 2.0569803, 1.849857, 2.2679921],
    [1024, "APPS/train/920", 0, 11.203647, 15.1599011, 5.9178533, 5.5140358, 5.3890916, 2.7226722, 2.4347119, 2.327165],
    [1024, "APPS/train/920", 1, 11.2126694, 15.6097754, 5.8505359, 5.4300973, 5.5868312, 2.7212786, 2.4648919, 2.3281529],
    [1536, "MATH/algebra/train/687", 0, 6.0296406, 8.0842752, 3.3411875, 3.0973744, 3.1971003, 1.8848888, 1.8256935, 2.7853662],
    [1536, "MATH/algebra/train/687", 1, 7.4824998, 8.7491607, 3.3324018, 3.073571, 3.1810156, 1.9578631, 1.8129006, 2.7846368],
    [1536, "APPS/train/920", 0, 11.2086695, 14.1326059, 5.6510572, 5.5182489, 5.2740617, 2.811984, 2.4714902, 2.3286194],
    [1536, "APPS/train/920", 1, 11.2111805, 14.1360236, 5.731954, 5.4058303, 5.6349119, 2.6891103, 2.3708506, 2.328357],
]
PUBLISHED_GM = [8.574332027018096, 11.265438427703351, 4.3968696093474255, 4.137836519961513, 4.180761881080242, 2.3396475989292087, 2.100308751727792, 2.418752786652299]


def gm(values):
    values = list(values)
    if not values or any(not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("positive finite observations required")
    return math.exp(math.fsum(math.log(v) for v in values) / len(values))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def partition(head, width, padding=256):
    extents = [padding * ((head + i) // padding + 1) for i in range(width)]
    return 1 + sum(a != b for a, b in zip(extents, extents[1:]))


def main():
    blocks = [{"context": r[0], "input": r[1], "session": r[2], "seconds": dict(zip(ARMS, r[3:], strict=True))} for r in ROWS]
    require(len({(r["context"], r["input"], r["session"]) for r in blocks}) == 8, "duplicate or missing block")
    result = {"source_commit": SOURCE, "source_path": "benchmarks/tpds_parallel/evidence/cost.json", "scope": "64 connector-transcribed service times; no raw native replay", "independent_inputs": 2, "comparisons": {}}
    for arm, published in zip(ARMS, PUBLISHED_GM, strict=True):
        mean = gm(r["seconds"][arm] for r in blocks)
        require(math.isclose(mean, published, rel_tol=1e-12), "published geometric mean mismatch: " + arm)
        ratios = [r["seconds"][arm] / r["seconds"]["QB-local"] for r in blocks]
        result["comparisons"][arm] = {"gm_seconds": mean, "baseline_over_QB": gm(ratios), "QB_time_reduction_percent": 100 * (1 - 1 / gm(ratios)), "QB_faster_blocks": sum(v > 1 for v in ratios), "QB_slower_blocks": sum(v < 1 for v in ratios), "session_ratios": [gm(r["seconds"][arm] / r["seconds"]["QB-local"] for r in blocks if r["session"] == s) for s in (0, 1)]}
    total = math.fsum(v for r in blocks for v in r["seconds"].values())
    require(math.isclose(total, 325.6375658, rel_tol=1e-12), "total mismatch")
    require(all(partition(h, min(32, n - h)) == 1 for n in (255, 593) for h in range(0, n, 32)), "unexpected aligned-prefill crossing")
    # Review-plan geometry checks, not GPU qualification.
    cells = []
    for boundary in (256, 1024):
        for width in (8, 32):
            for crossed, head in ((False, boundary - width), (True, boundary - 3)):
                require(head + width <= 1536, "diagnostic exceeds context")
                require(partition(head, width) == 1 + int(crossed), "incorrect predicted grouping")
                cells.append({"head": head, "width": width, "context": 1536, "crossed": crossed, "group_widths": [3, width - 3] if crossed else [width]})
    result.update({"measured_seconds_sum": total, "aligned_prefill_crossings": 0, "planned_diagnostic_cells": cells})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
