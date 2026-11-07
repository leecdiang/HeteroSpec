from pathlib import Path
import json,statistics
r=Path(__file__).parent
a=json.loads((r/"ANALYSIS.json").read_text());rows=a["raw_timing_rows"]
out={"scope":"Descriptive arithmetic means over registered phase fields; no kernel attribution or causal hardware conclusion","arms":{}}
for arm in ("BASE_A","BASE_B","BULK1"):
    rr=[x for x in rows if x["arm"]==arm];keys=sorted({k for x in rr for k in x["phases"]})
    out["arms"][arm]={"requests":len(rr),"service_seconds":statistics.mean(x["service_seconds"]for x in rr),
        "request_seconds":statistics.mean(x["request_seconds"]for x in rr),
        "context_and_teardown_seconds":statistics.mean(x["context_and_teardown_seconds"]for x in rr),
        "unassigned_seconds":statistics.mean(x["unassigned_request_seconds"]for x in rr),
        "phases":{k:statistics.mean(x["phases"].get(k,0)for x in rr)for k in keys}}
p=statistics.mean(out["arms"][x]["phases"]["target_VERIFY"]for x in ("BASE_A","BASE_B"))
q=out["arms"]["BULK1"]["phases"]["target_VERIFY"]
out["target_verify_BASE_seconds"]=p;out["target_verify_BULK1_seconds"]=q
out["target_verify_reduction_descriptive"]=1-q/p
out["draft_decode_plus_prefill_BULK1_seconds"]=sum(v for k,v in out["arms"]["BULK1"]["phases"].items()if k.startswith("draft_"))
out["draft_prefill_BASE_seconds"]=statistics.mean(out["arms"][x]["phases"]["draft_PREFILL"]for x in ("BASE_A","BASE_B"))
out["draft_prefill_BULK1_seconds"]=out["arms"]["BULK1"]["phases"]["draft_PREFILL"]
out["draft_prefill_reduction"]=1-out["draft_prefill_BULK1_seconds"]/out["draft_prefill_BASE_seconds"]
(r/"STAGE_SUMMARY.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
