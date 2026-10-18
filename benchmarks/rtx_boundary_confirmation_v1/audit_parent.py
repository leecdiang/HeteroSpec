"""Recompute motivating diagnostics from pinned PR120 compact tables; CPU only."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics as st
from study import PARENT


def mean_ratio(values):
    return math.exp(st.mean(math.log(x) for x in values))


def audit(host_csv, r1_csv):
    with host_csv.open(newline="", encoding="utf-8") as file:
        hosts = [r for r in csv.DictReader(file) if r["stage"] == "T1" and r["cost_view"] == "resident_graph" and r["timing_eligible"] == "True"]
    indexed = {}
    for row in hosts:
        key = row["context_id"], int(row["block"]), row["layout"]
        if key in indexed:
            raise ValueError("duplicate host")
        indexed[key] = row
    pairs = []
    for cid, block in sorted({(k[0], k[1]) for k in indexed}):
        a, b, c = [indexed[cid, block, name] for name in ("PQ", "QB", "QH_C")]
        pairs.append(dict(context_id=cid, block=block, q=int(a["q"]),
                          QB_QH=float(b["mean"])/float(c["mean"]), PQ_QB=float(a["mean"])/float(b["mean"])))
    core = [p for p in pairs if p["q"] > 1]
    q1 = [p for p in pairs if p["q"] == 1]
    blocks = [dict(block=b, QB_QH=mean_ratio([p["QB_QH"] for p in q1 if p["block"] == b]),
                   PQ_QB=mean_ratio([p["PQ_QB"] for p in q1 if p["block"] == b])) for b in sorted({p["block"] for p in q1})]
    with r1_csv.open(newline="", encoding="utf-8") as file:
        r1 = [r for r in csv.DictReader(file) if r["cost_view"] == "resident_graph" and r["eligible"] == "True" and r["numerator"] == "QB" and int(r["q"]) == 1]
    return dict(parent_commit=PARENT,
                inputs={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (host_csv, r1_csv)},
                core=dict(pairs=len(core), blocks=sorted({p["block"] for p in core}),
                          QB_QH=mean_ratio([p["QB_QH"] for p in core]),
                          PQ_QB=mean_ratio([p["PQ_QB"] for p in core]),
                          QB_lower_than_QH=sum(p["QB_QH"] < 1 for p in core),
                          QB_lower_than_PQ=sum(p["PQ_QB"] > 1 for p in core)),
                q1_per_block=blocks,
                R1_q1={split: dict(pairs=sum(r["split"] == split for r in r1),
                                    QB_QH=mean_ratio([float(r["ratio"]) for r in r1 if r["split"] == split]))
                       for split in ("development", "holdout")},
                scope="recalculation of committed compact host/contrast tables;not raw byte audit or new GPU data",
                conclusion="same-path variation motivates concurrent A/A controls;does not retroactively change PR120 eligibility")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-csv", type=Path, required=True)
    parser.add_argument("--r1-csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.host_csv, args.r1_csv)
    with args.out.open("x", encoding="utf-8", newline="\n") as file:
        json.dump(result, file, indent=2, allow_nan=False)
        file.write("\n")
    print(json.dumps(result["core"]))


if __name__ == "__main__":
    main()
