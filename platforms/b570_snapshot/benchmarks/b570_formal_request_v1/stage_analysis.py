from pathlib import Path
import json,statistics
r=Path(__file__).parent
a=json.loads((r/"ANALYSIS.json").read_text());rows=a["raw_timing_rows"]
out={"scope":"Descriptive arithmetic means over registered phase fields; no kernel attribution or causal hardware conclusion","arms":{}}
for arm in ("R","PQ_A","PQ_B","QB"):
    rr=[x for x in rows if x["arm"]==arm];keys=sorted({k for x in rr for k in x["phases"]})
    out["arms"][arm]={"requests":len(rr),"service_seconds":statistics.mean(x["service_seconds"]for x in rr),
        "request_seconds":statistics.mean(x["request_seconds"]for x in rr),
        "context_and_teardown_seconds":statistics.mean(x["context_and_teardown_seconds"]for x in rr),
        "unassigned_seconds":statistics.mean(x["unassigned_request_seconds"]for x in rr),
        "phases":{k:statistics.mean(x["phases"].get(k,0)for x in rr)for k in keys}}
p=statistics.mean(out["arms"][x]["phases"]["target_VERIFY"]for x in ("PQ_A","PQ_B"))
q=out["arms"]["QB"]["phases"]["target_VERIFY"]
out["target_verify_PQ_seconds"]=p;out["target_verify_QB_seconds"]=q
out["target_verify_reduction_descriptive"]=1-q/p
out["draft_decode_plus_prefill_QB_seconds"]=sum(v for k,v in out["arms"]["QB"]["phases"].items()if k.startswith("draft_"))
(r/"STAGE_SUMMARY.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
