#!/usr/bin/env python3
"""Check observed backend transitions on a previously exposed historical prompt."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs/m4/runtime_profitability_control_20260924/r0"


def main():
    short = json.loads((RUN / "qualification_smoke.json").read_text())["records"]
    long = json.loads((RUN / "full_cap_smoke.json").read_text())
    target, always, early, never, late, reset = short
    expected = target["generated_token_ids"]
    if not all(row["status"] == "OK" and row["generated_token_ids"] == expected for row in short):
        raise RuntimeError("R0 direct token-ID or reset failure")
    if target["stop_reason"] != "CAP" or len(expected) != 32:
        raise RuntimeError("R0 cap path missing")
    rounds = always["rounds"]
    for accepted in (0, 1, 2):
        if not any(r["proposed"] == 2 and r["accepted"] == accepted for r in rounds):
            raise RuntimeError(f"R0 k=2 accept/reject position {accepted} missing")
    if early["fallback_round"] != 2 or late["fallback_round"] != 8 or never["fallback_triggered"]:
        raise RuntimeError("Early/late/no-fallback state transition failed")
    if not (early["guard_compute_ns"] > 0 and early["fallback_transition_ns"] > 0):
        raise RuntimeError("Guard/transition work was not charged")
    if early["target_only_committed_token_count"] <= 0 or late["target_only_committed_token_count"] <= 0:
        raise RuntimeError("Fallback did not continue target-only")
    if any(r["round"] > early["fallback_round"] for r in early["rounds"]):
        raise RuntimeError("Speculation resumed after fallback")
    first = long[0]["generated_token_ids"]
    if long[0]["stop_reason"] != "EOS" or not all(row["generated_token_ids"] == first for row in long):
        raise RuntimeError("EOS/full-cap direct-ID qualification failed")
    print(json.dumps({"status": "PASS", "full_accept": True, "rejection_positions": [0, 1],
                      "correction_and_bonus": True, "early_fallback_round": 2,
                      "late_fallback_round": 8, "eos": True, "cap": True,
                      "reset": True, "charged_control": True}, indent=2))


if __name__ == "__main__":
    main()
