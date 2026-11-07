"""Numerical qualification only; never a performance result."""
from collections import defaultdict
import study as s


def qualification(design, bundle, family):
    audit, selected = s.audit(design, bundle)
    s.need(not audit["failures"], "shared admission failure: " + str(audit["failures"]))
    rows = [r for r in selected if r["family"] == family and r["stage"] == "qualification"]
    expected = [r for r in s.lines(design / "SLOTS.jsonl") if r["family"] == family and r["stage"] == "qualification"]
    s.need(len(rows) == 98 and [r["slot_id"] for r in rows] == [r["slot_id"] for r in expected],
           "complete validated qualification unit required: " + str(audit["families"][family]["errors"]))
    grouped = defaultdict(dict)
    for row in rows:
        grouped[(row["input_id"], row["observer"])][row["arm"]] = row
    for key, arms in grouped.items():
        s.need(set(arms) == set(s.ARMS), "qualification arm missing")
        for prefix in ("M", "C"):
            pq, qb = arms[prefix + "_PQ"], arms[prefix + "_QB"]
            for field in ("cycles", "target_final_kv", "draft_final_kv"):
                s.need(pq[field] == qb[field], "PQ/QB canonical state differs")
            if key[1] == "heavy":
                vectors = lambda r: {v["name"]: (v["bytes"], v["sha256"]) for v in r["raw_vectors"]}
                s.need(vectors(pq) == vectors(qb), "PQ/QB full decision vectors differ")
    panel = s.read(design / "PANEL.json")["families"][family]
    for index in (0, 11):
        on, off = grouped[(panel[index]["id"], "heavy")], grouped[(panel[index]["id"], "off")]
        for arm in s.ARMS:
            for field in ("endpoint", "cycles", "target_final_kv", "draft_final_kv"):
                s.need(on[arm][field] == off[arm][field], "observer sentinel differs")
    return {"status": "NUMERICALLY_QUALIFIED", "family": family, "requests": 98,
            "qualification_attempt": rows[0]["attempt_id"], "qualified_performance": None}
