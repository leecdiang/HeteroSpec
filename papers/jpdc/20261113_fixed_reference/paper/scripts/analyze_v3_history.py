#!/usr/bin/env python3
"""Reconstruct three historical mechanism tables from public record fields.

This is CPU counting of recorded output digests and equality flags. It neither
replays native tensors nor measures inference. Source projections and their
omissions are documented in data/v3/sources.json.
"""
from collections import Counter
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "v3"
OUT = ROOT / "generated"
OUT.mkdir(exist_ok=True)

def read_json(name):
    return json.loads((DATA / name).read_text())

def read_csv(name):
    with (DATA / name).open(newline="") as handle:
        return list(csv.DictReader(handle))

def true(value):
    assert value in ("True", "False")
    return value == "True"

def macro(name, rows):
    return "\\newcommand{\\" + name + "}{%\n" + "\n".join(rows) + "\n}\n"

operands = read_json("arithmetic_routes.json")
traces = read_json("arithmetic_dispatch.json")
assert Counter(x["model"] for x in operands) == {"0.6B": 8, "8B": 8}
width_results = []
width_rows = []
for q in (2, 4, 8, 16, 32):
    matches = {"wide": 0, "packed": 0}
    counts = {"wide": 0, "packed": 0}
    for item in operands:
        routes = [x for x in item["routes"] if x["q"] == q]
        scalar = next(x for x in routes if x["route"] == "scalar")
        for route in routes:
            equal = route["sha"] == scalar["sha"]
            assert equal == route["scalar_equal"]
            if route["route"] in counts:
                counts[route["route"]] += 1
                matches[route["route"]] += equal
    assert counts["wide"] == 16
    assert matches["wide"] == (16 if q <= 4 else 0)
    assert counts["packed"] == (16 if q >= 8 else 0)
    assert matches["packed"] == counts["packed"]
    fixups = 0
    for item in [x for x in operands if x["model"] == "8B"]:
        weight = item["descriptor"]["weight"]["name"]
        native = traces[f"{weight}/{q}-wide"]
        names = [x["name"] for x in native]
        if q <= 8:
            assert any("quantize_q8_1" in x and "mmq" not in x for x in names)
            mmvq = [x for x in native if "mul_mat_vec_q" in x["name"]]
            assert len(mmvq) == 1
            assert mmvq[0]["block"] == [32, 4 if q <= 4 else 2, 1]
        else:
            assert any("quantize_mmq" in x for x in names)
            assert any("mul_mat_q" in x and "fixup" not in x for x in names)
            fixups += any("fixup" in x for x in names)
        if q >= 8:
            packed = traces[f"{weight}/{q}-packed"]
            mmvq = [x for x in packed if "mul_mat_vec_q" in x["name"]]
            assert len(mmvq) == 1 and mmvq[0]["block"] == [32, 4, 1]
    if q >= 16:
        assert fixups == 7
    dispatch = (r"Row-Q8\_1; MMVQ, 4 warps" if q <= 4 else
                r"Row-Q8\_1; MMVQ, 2 warps" if q == 8 else
                r"MMQ quantization and MMQ\textsuperscript{a}")
    grouped = "---" if q <= 4 else "16/16"
    width_rows.append(f"{q} & {dispatch} & {matches['wide']}/16 & {grouped} " + r"\\")
    width_results.append({"q": q, "native_matches": matches["wide"], "native_n": 16,
                          "packed_matches": matches["packed"], "packed_n": counts["packed"],
                          "profiled_8b_fixup_count": fixups})

audits = read_json("attention_committed_rows.json")
controls = read_json("attention_controls.json")
assert len(audits) == 2
attention = []
coordinates = []
for audit in audits:
    rows = audit["cells"]
    assert len(rows) == 15
    assert len({x["input_id"] for x in rows}) == 3
    assert {x["arm"] for x in rows} == {"R", "M_PQ", "M_QB", "C_PQ", "C_QB"}
    coords = []
    bad = []
    for cell in rows:
        assert [x["output_index"] for x in cell["vectors"]] == list(range(128))
        for v in cell["vectors"]:
            coord = (cell["input_id"], cell["arm"], v["output_index"])
            coords.append(coord)
            if not v["bitwise_equal"]:
                bad.append(coord)
    coordinates.append(coords)
    attention.append({"status": audit["source_status"], "n": len(coords), "different": len(bad),
                      "different_by_cell": [{"input": i, "arm": a, "count": n}
                                            for (i, a), n in Counter((i, a) for i, a, _ in bad).items()]})
    if bad:
        assert set(bad) == {("CodeContests/valid/108", arm, row)
                            for arm in ("C_PQ", "C_QB") for row in range(29, 128)}
assert coordinates[0] == coordinates[1]
assert [x["different"] for x in attention] == [198, 0]
for key in ("projection_only", "combined", "prefix_off"):
    assert controls[key]["all_reference_equal"]
    assert all(x["local_reference_equal"] for x in controls[key]["cells"])
assert not controls["projection_off"]["all_reference_equal"]
reversal = controls["prefix_factor_reversal"]
assert reversal["status"] == "COMPLETE_FACTOR_REVERSAL_PASS"
assert len(reversal["rows"]) == reversal["requests"] == 36
assert sum(x["vectors"] for x in reversal["rows"]) == reversal["vectors"] == 3152
attention_rows = [
    r"Projection repair & Match & 99/128 & 198/1,920 \\",
    r"Projection + attention repair & Match & 0/128 & 0/1,920 \\",
    r"Same binary, attention repair off & Match & 99/128\textsuperscript{b} & 198/1,920\textsuperscript{b} \\",
    r"Same binary, projection repair off & Differ & --- & --- \\",
]

matrix = read_csv("producer_matrix.csv")
states = read_csv("producer_state_effects.csv")
assert len(matrix) == 48 and len(states) == 8
ids = [r["input_id"] for r in states]
assert len(set(ids)) == 8
lookup = {(r["input_id"], r["producer"], r["consumer"]): r for r in matrix}
assert len(lookup) == 48
patterns = Counter()
members = {}
for row in states:
    i = row["input_id"]
    assert not true(row["kv_bytes_equal"]) and not true(row["initial_logits_bytes_equal"])
    for producer in ("P1", "P4T"):
        for boundary in ("endpoint", "cycles", "vectors"):
            assert true(row[f"{producer}_PQ_QB_{boundary}_equal"])
        for consumer in ("C1", "PQ", "QB"):
            assert true(lookup[(i, producer, consumer)]["strict_reference_equal"]) == true(row[f"{producer}_{consumer}_strict_reference_equal"])
        assert lookup[(i, producer, "PQ")]["strict_reference_equal"] == lookup[(i, producer, "QB")]["strict_reference_equal"]
    pattern = tuple(true(lookup[(i, p, c)]["strict_reference_equal"])
                    for p, c in (("P1", "C1"), ("P4T", "C1"), ("P1", "PQ"), ("P4T", "PQ")))
    patterns[pattern] += 1
    members.setdefault(pattern, []).append(i)
expected = {(True, True, True, True): 5, (True, True, False, True): 2, (True, False, False, False): 1}
assert patterns == expected
names = {p: n for p, n in zip(expected, ["Unchanged endpoints", "Prealgebra 1865 and 1804", "GSM8K train 1184"])}
producer_rows = []
for pattern, count in expected.items():
    producer_rows.append(f"{names[pattern]} & {count} & " + " & ".join("Match" if x else "Differ" for x in pattern) + r" \\")

tex = "% Generated by scripts/analyze_v3_history.py; edit sources, not counts.\n"
tex += macro("HistoryWidthRows", width_rows)
tex += macro("HistoryRepairRows", attention_rows)
tex += macro("HistoryProducerRows", producer_rows)
(OUT / "table_history.tex").write_text(tex)
summary = {"arithmetic": width_results, "attention": attention,
           "prefix_off_inference": "Recorded complete trajectory equality restores projection-only committed differences.",
           "producer": [{"pattern": list(p), "n": n, "inputs": members[p]} for p, n in expected.items()],
           "producer_pq_qb_agreement_pairs": 16, "producer_joint_kv_logits_changes": 8,
           "scope": "Counts of public recorded comparisons, not new independent workloads or native reruns.",
           "model_calls": 0, "gpu_contexts": 0}
(OUT / "history_mechanism_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({"status": "PASS", "descriptor_cases": 16, "committed_rows_per_audit": 1920,
                  "producer_inputs": 8, "tables": 3, "model_calls": 0, "gpu_contexts": 0}))
