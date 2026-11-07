"""CPU-only audit of all saved attempts, byte continuity, counters and observer gates."""
from pathlib import Path
import json,hashlib,re,statistics
root=Path(__file__).parent
roots={
 "failed_entry":Path("C:/hs/b570-model-bridge-20261020162000"),
 "bridge":Path("C:/hs/b570-model-bridge-20261020162500"),
 "serial_logger":Path("C:/hs/b570-model-profile-20261020163000"),
 "concurrent_missing_tail":Path("C:/hs/b570-model-concurrent-20261020163500"),
 "tail_fixed":Path("C:/hs/b570-model-tailfix-20261020163300"),"active_labels_fixed":root}
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
processes=[];checks=[];ledger=[];loaded={}
for label,d in roots.items():
    budget=read(d/"BUDGET_LEDGER.json")
    for x in budget["sessions"]:
        ledger.append({"stage":label,**x})
        f=d/f"session-{x['session']}"
        data=read(f/"result.json")
        if data["status"]=="STOPPED_FIRST_FAILURE":
            assert label=="failed_entry" and not data["runs"]
            continue
        assert data["status"]=="GEOMETRY_AND_OBSERVER_QUALIFIED" and data["normal_cleanup_returned"]
        assert len(data["runs"])==3
        loaded[(label,x["session"])]=data
        for run in data["runs"]:
            assert len(run["steps"])==16
            for s in run["steps"]:
                p=f/f"run-{run['run']}-step-{s['step']}.f32"
                ref=roots["bridge"]/"session-0"/f"run-0-step-{s['step']}.f32"
                assert sha(p)==sha(ref)
                vals=memoryview(p.read_bytes()).cast("f")
                assert len(vals)==151936 and max(range(len(vals)),key=vals.__getitem__)==s["token_id"]
                checks.append({"stage":label,"session":x["session"],"run":run["run"],"step":s["step"],"sha256":sha(p),"token_id":s["token_id"]})
        obs=data["runs"][1]
        assert obs["observer_asks"]>0 and obs["observer_unexpected_completions"]==0
        assert len(obs["signatures"])==360 and all("B570" in j["device"] for j in obs["signatures"])
        qks=[j for j in obs["signatures"] if re.fullmatch(r"kq-\d+",j["name"])]
        assert len(qks)==72 and all(j["ne"]==[256,1,32,1] for j in qks)
        times=[s["decode_completed_seconds"] for s in data["runs"][2]["steps"] if "decode_completed_seconds" in s]
        assert len(times)==15
        processes.append({"stage":label,"session":x["session"],"median_decode_ms":statistics.median(times)*1000,"all_decode_ms":[v*1000 for v in times]})
    for entry in read(d/"BUILD_MANIFEST.json")["files"]:
        assert sha(Path(entry["path"]))==entry["sha256"]
assert len(checks)==528 and len(processes)==11 and len(ledger)==12
prior=53.7774511
for row in ledger:
    assert abs(row["prior_cumulative_seconds"]-prior)<1e-8
    prior+=row["charged_seconds"]
    assert abs(row["cumulative_charged_seconds"]-prior)<1e-8
assert abs(prior-read(root/"BUDGET_LEDGER.json")["cumulative_charged_seconds"])<1e-8
def median(key):return next(p["median_decode_ms"] for p in processes if (p["stage"],p["session"])==key)
def gate(name,keys):
    a,p,b=map(median,keys)
    ratios=[b/a,p/a,p/b]
    return {"observer":name,"clean_a_ms":a,"profile_ms":p,"clean_b_ms":b,
     "clean_b_over_a":ratios[0],"profile_over_a":ratios[1],"profile_over_b":ratios[2],
     "coarse_10pct_gate_pass":all(.9<=r<=1.1 for r in ratios)}
gates=[
 gate("serial_per_op", [("bridge",0),("serial_logger",0),("serial_logger",1)]),
 gate("concurrent_missing_tail",[("serial_logger",1),("concurrent_missing_tail",0),("concurrent_missing_tail",1)]),
 gate("concurrent_tail_fixed",[("tail_fixed",0),("tail_fixed",1),("tail_fixed",2)]), gate("concurrent_active_labels_fixed",[("active_labels_fixed",0),("active_labels_fixed",1),("active_labels_fixed",2)])]
def parse_tables(path):
    out=[]
    for block in path.read_text().split("Vulkan Timings:\n")[1:]:
        rows=[]
        for line in block.splitlines():
            m=re.fullmatch(r"(.+): (\d+) x ([\d.eE+-]+) us = ([\d.eE+-]+) us(?: .*)?",line)
            if m:rows.append({"group":m[1],"count":int(m[2]),"mean_us":float(m[3]),"total_us":float(m[4])})
            m=re.fullmatch(r"Total time: ([\d.eE+-]+) us\.",line)
            if m:total=float(m[1]);break
        assert abs(sum(x["total_us"] for x in rows)-total)/total<1e-4
        out.append({"context":len(out),"total_us":total,"rows":rows})
    assert len(out)==3
    return out
old_tables=parse_tables(roots["concurrent_missing_tail"]/"session-0.stderr.log")
tables=parse_tables(root/"session-1.stderr.log")
core={"MUL_MAT_VEC f16 m=128 n=1 k=256 batch=32","MUL_MAT_VEC f16 m=256 n=1 k=128 batch=32","SOFT_MAX"}
lmhead="MUL_MAT_VEC q8_0 m=151936 n=1 k=4096"
for table in old_tables:
    assert sum(r["count"]*r["group"].split(", ").count(lmhead) for r in table["rows"])==0
for table in tables:
    assert all(' n=0 ' not in row['group'] for row in table['rows'])
    counts={name:0 for name in core|{lmhead,"CONT"}}
    subtotal={"attention_core_pure":0.0,"attention_core_mixed":0.0,"quantized_matvec_groups":0.0,"recombine_cont":0.0,"other":0.0}
    for r in table["rows"]:
        parts=r["group"].split(", ")
        for name in counts:counts[name]+=r["count"]*parts.count(name)
        if all(p in core for p in parts):cat="attention_core_pure"
        elif any(p in core for p in parts):cat="attention_core_mixed"
        elif all("MUL_MAT" in p and "q8_0" in p for p in parts):cat="quantized_matvec_groups"
        elif parts==["CONT"]:cat="recombine_cont"
        else:cat="other"
        r["classification"]=cat;subtotal[cat]+=r["total_us"]
    assert counts[lmhead]==16 and all(counts[name]==5004 for name in core|{"CONT"})
    table["effective_op_counts"]=counts
    table["group_subtotals_us"]=subtotal
    table["group_fractions"]={k:v/table["total_us"] for k,v in subtotal.items()}
    table["core_fraction_bounds"]=[subtotal["attention_core_pure"]/table["total_us"],(subtotal["attention_core_pure"]+subtotal["attention_core_mixed"])/table["total_us"]]
report={"status":"ALL_RAW_AND_COUNTER_CHECKS_PASS","gpu_execution":False,"successful_native_processes":11,
 "failed_entry_processes":1,"requests":33,"complete_logits_arrays":528,"values_per_array":151936,
 "geometry":{"model":"Qwen3-8B Q8_0","Hq":32,"Hkv":8,"d":128,"physical_key":256,"q":1,"layers":36,"prompt_tokens":124,"generated_tokens":16,"input":"HumanEval/42 previously exposed"},
 "qualification_scope":"All528 complete logits and greedy IDs match original bridge CLEAN_A reference, including fixed DLL and logger variants. Not full workload qualification.",
 "observer_gates":gates,"old_concurrent_lm_head_count":0,"corrected_profile_tables":tables,
 "processes":processes,"budget_receipts":ledger,"cumulative_seconds":prior,"remaining_seconds":300-prior,
 "new_charge_this_turn_seconds":prior-53.7774511,
 "limitations":["single exposed prompt and single device/date","15 dependent decode times per process; descriptive calibration only","timestamp sums are GPU instrumented subtotals, not natural-request critical-path fractions","no physical bandwidth/occupancy/power measurement","QKV and output projections belong to quantized groups, not the small QK/softmax/AV core","no multiquery/model optimization enabled","no actor RTL CPU8 or merge"],
 "raw_byte_checks":checks}
(root/"ANALYSIS.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"status":report["status"],"requests":33,"arrays":528,"gates":gates,
 "third_context":{k:v for k,v in tables[2].items() if k!="rows"},"cumulative":prior,"remaining":300-prior},indent=2))
