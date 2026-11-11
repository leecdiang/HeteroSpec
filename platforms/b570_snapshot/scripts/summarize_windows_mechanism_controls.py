#!/usr/bin/env python3
import csv, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"reports/5070ti"
micro=json.loads((ROOT/"logs/windows-exact-verification-microbench.json").read_text(encoding="utf-8"))
div=json.loads((ROOT/"logs/windows-cuda-divergence-minrepro.json").read_text(encoding="utf-8"))
cost=[]
for depth, block in micro["depths"].items():
    for path, v in block.items():
        cost.append({"context_depth":int(depth),"path":path,"ubatch":2 if "2" in path else 1,"pp1_median_ms":v["pp1"]["median_ns"]/1e6,"pp2_median_ms":v["pp2"]["median_ns"]/1e6,"T_verify2_over_T_decode1":v["ratio_pp2_over_pp1"],"repetitions":len(v["pp1"]["samples_ns"])})
with (OUT/"WINDOWS_EXACT_VERIFICATION_COST.csv").open("w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=list(cost[0]));w.writeheader();w.writerows(cost)
lookup={(r["task_id"],r["repetition"],r["condition"]):r for r in div["runs"]}; drows=[]
for task in ("HumanEval/106","HumanEval/129"):
    for rep in (1,2,3):
        b=lookup[(task,rep,"baseline")];s=lookup[(task,rep,"cpu_k2")];idx=s["first_divergent_token"]
        drows.append({"task_id":task,"repetition":rep,"ubatch":2,"exact_match":s["exact_match"],"captured_first_divergence_index_zero_based":idx if idx is not None else "","baseline_token_id":b["tokens"][idx] if idx is not None else "","spec_token_id":s["tokens"][idx] if idx is not None else "","acceptance_rate":s["metrics"].get("acceptance_rate"),"logit_margin":"unavailable_in_llama_cli"})
with (OUT/"WINDOWS_CUDA_DIVERGENCE_MINREPRO.csv").open("w",newline="",encoding="utf-8-sig") as f:
    w=csv.DictWriter(f,fieldnames=list(drows[0]));w.writeheader();w.writerows(drows)
print(json.dumps({"cost":cost,"divergence":drows},indent=2))
