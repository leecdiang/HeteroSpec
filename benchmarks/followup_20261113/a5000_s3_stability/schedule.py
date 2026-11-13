#!/usr/bin/env python3
"""CPU-only schedule; never imports a model backend or starts native processes."""
import argparse
import json
import random
from pathlib import Path

def schedule(cohort, seed=20261113):
    if cohort not in ("R", "H"):
        raise ValueError("cohort must be R or H")
    days = (1, 2) if cohort == "R" else (1,)
    result = []
    for day in days:
        for round_id in (1, 2):
            # Interleaved domains, deterministic root order; independent of outcomes.
            rng = random.Random(seed + day * 100 + round_id)
            code, math = list(range(6)), list(range(6, 12))
            rng.shuffle(code); rng.shuffle(math)
            roots = [x for pair in zip(code, math) for x in pair]
            for slot in roots:
                first_bc = ((slot % 6) + day) % 2 == 0
                if round_id == 2:
                    first_bc = not first_bc
                arms = ("B", "C") if first_bc else ("C", "B")
                pair_id = f"{cohort}-day{day}-round{round_id}-root{slot:02d}"
                for arm in arms:
                    result.append(dict(cohort=cohort, day=day, round=round_id,
                        root_slot=slot, domain="code" if slot < 6 else "math",
                        pair_id=pair_id, arm=arm,
                        requests=["warm", "measured"], rows_reserved_max=640))
    return result

def self_test():
    for cohort, expected in (("R", 96), ("H", 48)):
        rows = schedule(cohort)
        assert len(rows) == expected
        assert sum(len(x["requests"]) for x in rows) == 2 * expected
        pairs = {}
        for x in rows:
            pairs.setdefault(x["pair_id"], []).append(x["arm"])
        assert all(sorted(v) == ["B", "C"] for v in pairs.values())
        for day in sorted({x["day"] for x in rows}):
            for slot in range(12):
                orders = [[x["arm"] for x in rows if x["day"] == day
                           and x["root_slot"] == slot and x["round"] == r]
                          for r in (1, 2)]
                assert orders[0] == list(reversed(orders[1]))
    return {"status": "CPU_SCHEDULE_PASS", "R_workers": 96, "H_workers": 48,
            "R_formal_plus_warm_requests": 192, "H_formal_plus_warm_requests": 96,
            "native_calls": 0}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cohort", choices=["R", "H"])
    p.add_argument("--out", type=Path)
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        print(json.dumps(self_test(), indent=2))
    else:
        if a.cohort is None or a.out is None:
            p.error("--cohort and --out required")
        # Never overwrite a frozen schedule.
        with a.out.open("x", encoding="utf-8") as f:
            json.dump({"status": "DESIGN_NOT_EXECUTED", "cohort": a.cohort,
                       "root_manifest": "REQUIRED_BEFORE_NATIVE_EXECUTION",
                       "workers": schedule(a.cohort)}, f, indent=2)
            f.write("\n")
