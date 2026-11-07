#!/usr/bin/env python3
"""Small discriminating CPU fixtures. Every timing/token here is synthetic."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path
import tempfile
import sys
import study as s


def run():
    checks = []
    def check(name, ok):
        s.need(ok, name)
        checks.append({"name": name, "status": "PASS"})
    def rejects(name, fn):
        try:
            fn()
        except (s.ContractError, KeyError, ValueError):
            checks.append({"name": name, "status": "PASS"})
        else:
            raise s.ContractError("accepted invalid fixture: " + name)

    design = s.DESIGN
    report = s.check_plan(design)
    check("exact 196 qualification + 1008 measurement + 84 warmup plan", report["factorial_slots"] == {"qualification": 196, "formal": 1008, "warmup": 84})
    slots = s.lines(design / "SLOTS.jsonl")
    for family in s.FAMILIES:
        formal = [r for r in slots if r["family"] == family and r["stage"] == "formal"]
        first_arms = {}
        for r in formal:
            first_arms.setdefault(r["block_id"], r["arm"])
        counts = s.Counter(first_arms.values())
        check("seven-arm Latin positions balanced to one block: " + family, set(counts.values()) == {10, 11})

    model = s.read(design / "MODEL_PINS.json")["families"]["Qwen"]
    end = {"ids": [model["eog"][0]], "eog": [True], "length": 1, "terminal_id": model["eog"][0], "stop_reason": "EOG"}
    check("synthetic full EOG endpoint validates", s.endpoint(end, model) == end)
    bad = deepcopy(end); bad["eog"] = [False]
    rejects("mismatched EOG identity rejected", lambda: s.endpoint(bad, model))
    truncated = {"ids": [1], "eog": [False], "length": 1, "terminal_id": 1, "stop_reason": "CAP"}
    rejects("shared prefix cannot masquerade as complete endpoint", lambda: s.endpoint(truncated, model))

    item = s.read(design / "PANEL.json")["families"]["Qwen"][0]
    n, eog = item["prompt_tokens"], model["eog"][0]
    native = {"draft_enabled": True, "k": 3, "endpoint": {"ids": [1, 2, 3, eog]},
              "target_final_kv": {"min": 0, "max": n + 2}, "draft_final_kv": {"min": 0, "max": n + 2},
              "cycles": [{"cycle": 0, "base": n, "seed": 1, "proposals": [2, 3, 4],
                          "decisions": [2, 3, eog, 5], "caller_rows": 4, "accepted": 2,
                          "rejected": True, "commit_kind": "correction", "output_length": 4,
                          "pending_after": None, "done": True, "keep": n + 3,
                          "target_before": {"min": 0, "max": n - 1}, "draft_before": {"min": 0, "max": n - 1},
                          "target_after": {"min": 0, "max": n + 2}, "draft_after": {"min": 0, "max": n + 2}}]}
    s.validate_cycles(native, item, model)
    check("synthetic rejection/terminal transaction reconstructs", True)
    bad = deepcopy(native); bad["cycles"][0]["decisions"].pop()
    rejects("unexamined verification row cannot be omitted", lambda: s.validate_cycles(bad, item, model))

    calendar = ["2026-11-01", "2026-11-02", "2026-11-03"]
    receipts = []
    origin = datetime(2026, 11, 1, 1, tzinfo=timezone.utc)
    for d in range(3):
        for session in range(2):
            for fi, family in enumerate(s.FAMILIES if d % 2 == 0 else s.FAMILIES[::-1]):
                start = origin + timedelta(days=d, hours=session * 3 + fi)
                receipts.append({"unit_id": f"formal/d{d}/s{session}/{family}", "date_slot": d,
                                 "session_slot": session, "family": family,
                                 "process_start_utc": start.isoformat(), "process_end_utc": (start + timedelta(minutes=20)).isoformat()})
    check("actual Asia/Shanghai dates and >=20h spacing", s.dates_ok(receipts, calendar))
    check("UTC date is not silently substituted for user date", s.local_date("2026-11-01T16:01:00Z") == "2026-11-02")
    bad = deepcopy(receipts)
    for r in bad:
        if r["date_slot"] == 1:
            start = s.utc(r["process_start_utc"]) - timedelta(hours=6)
            r["process_start_utc"] = start.isoformat()
            r["process_end_utc"] = (start + timedelta(minutes=20)).isoformat()
    rejects("distinct local dates with too-close first sessions rejected", lambda: s.dates_ok(bad, calendar))

    # Algorithm fixture only. These invented seconds are never saved as results
    # and cannot be passed off as native evidence by audit()/analyze().
    fake = []
    for r in slots:
        if r["stage"] == "formal" and r["family"] == "Qwen":
            times = {"R": 10, "M_GS": 8, "M_PQ": 11, "M_QB": [12, 15, 18][r["date_slot"]],
                     "C_GS": 10, "C_PQ": 10, "C_QB": 10}
            fake.append({**r, "service_seconds": times[r["arm"]], "is_synthetic": True})
    estimates = s.finite_panel_estimates(fake, "Qwen", calendar)
    interaction = next(x for x in estimates["summary"] if x["contrast"] == "I_QB_vs_GS")
    expected = (1.5 * 1.875 * 2.25) ** (1 / 3)
    check("date-weighted synthetic interaction matches analytic geometric mean", math.isclose(interaction["ratio"], expected, rel_tol=1e-14))
    rejects("missing arm cannot generate even a complete-panel arithmetic estimate", lambda: s.finite_panel_estimates(fake[:-1], "Qwen", calendar))
    with tempfile.TemporaryDirectory(prefix="rtx-scope-fixture-") as directory:
        bundle = Path(directory)
        # Valid-looking speed values without real bound identity/raw endpoints
        # must remain ineligible. This is not a native qualification fixture.
        s.save_lines(bundle / "REQUESTS.jsonl", fake)
        result = s.analyze(design, bundle)
        check("synthetic or missing native identity/raw records yield no qualified gain", result["qualified_performance"] is None and all(v is None for v in result["results"].values()))
    return {"schema": 1, "status": "PASS", "fixture_kind": "SYNTHETIC_CPU_ONLY_NOT_EXPERIMENTAL_DATA",
            "checks": checks, "check_count": len(checks), "new_native_executions": 0,
            "native_worker_built": False, "native_worker_qualified": False,
            "positive_native_bundle_validation": "PENDING_HOST_IMPLEMENTATION_AND_REAL_PAYLOADS",
            "scope": "Exact design reconstruction, endpoint/transaction rejection, local date gap gate, finite-panel arithmetic and fail-closed missing/synthetic evidence. No GPU or empirical performance result."}


if __name__ == "__main__":
    result = run()
    if len(sys.argv) == 3 and sys.argv[1] == "--out":
        s.save(Path(sys.argv[2]), result)
    elif len(sys.argv) != 1:
        raise SystemExit("usage: test_cpu.py [--out FILE]")
    print(s.json.dumps({"status": result["status"], "check_count": result["check_count"], "new_native_executions": 0}))
