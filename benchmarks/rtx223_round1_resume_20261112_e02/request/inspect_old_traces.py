"""Read-only structural coverage scan of the eight already-completed #215 traces.

Never imports the historical verifier or a model backend. This is not a new
numerical qualification, and deliberately does not splice separate traces.
"""
from pathlib import Path
import hashlib
import json


def inspect(root):
    root = Path(root)
    records = []
    for p in sorted(root.glob("rtx213-s1-*/native/boundary-natural-heavy/receipt.json")):
        raw = p.read_bytes()
        r = json.loads(raw)
        cycles = r["cycles"]
        k = r["k"]
        bonuses, fifth_rejections = [], []
        for i, c in enumerate(cycles):
            if c["accepted"] == 3 and c["commit_kind"] == "bonus" and not c["done"] and k == 3:
                next_cycle = cycles[i + 1] if i + 1 < len(cycles) else None
                bonuses.append({"cycle": c["cycle"], "bonus": c["pending_after"],
                                "next_seed": next_cycle["seed"] if next_cycle else None,
                                "continued_same_request": bool(next_cycle and next_cycle["seed"] == c["pending_after"])})
            if k == 7 and c["accepted"] == 4 and c["rejected"]:
                fifth_rejections.append({"cycle": c["cycle"], "L4_decision": c["decisions"][4],
                                         "proposal4": c["proposals"][4], "keep": c["keep"]})
        records.append({"path": str(p), "sha256": hashlib.sha256(raw).hexdigest(),
                        "k": k, "cycles": len(cycles), "k3_bonus_continuations": bonuses,
                        "k7_fifth_rejections": fifth_rejections,
                        "same_request_dynamic_chain": False})
    return {"scope": "READ_ONLY_EXISTING_TRACE_STRUCTURE_NOT_NUMERICAL_REQUALIFICATION",
            "trace_count": len(records), "records": records,
            "same_request_dynamic_chain": "NOT_COVERED_FIXED_K_WORKER",
            "new_model_requests": 0, "native_GPU_launches": 0}


if __name__ == "__main__":
    import sys
    print(json.dumps(inspect(sys.argv[1]), indent=2))
