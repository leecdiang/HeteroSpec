from pathlib import Path
import json,hashlib,collections
r=Path(__file__).parent
n=json.loads((r/"results/result.json").read_text())
receipt=json.loads((r/"PROCESS_RECEIPT.json").read_text(encoding="utf-8-sig"))
R,P,Q=n["requests"]
assert [x["arm"] for x in (R,P,Q)]==["R","PQ","QB"]
for field in ("ids","eog","length","terminal_id","stop_reason"):
    assert R[field]==P[field]==Q[field],field
assert P["cycles"]==Q["cycles"]
old=Path("C:/hs/b570-model-bridge-20261020162500/session-0")
oldj=json.loads((old/"result.json").read_text())
assert R["ids"]==[x["token_id"]for x in oldj["runs"][0]["steps"]]
old_matches=[]
for i in range(16):
    name="initial" if i==0 else f"ordinary-{i}"
    a=r/"results/R/target"/(name+".f32");b=old/f"run-0-step-{i}.f32"
    assert a.read_bytes()==b.read_bytes()
    old_matches.append(hashlib.sha256(a.read_bytes()).hexdigest())
matches=[]
for a in sorted((r/"results/PQ").rglob("*.f32")):
    rel=a.relative_to(r/"results/PQ");b=r/"results/QB"/rel
    assert a.read_bytes()==b.read_bytes(),rel
    matches.append({"file":str(rel),"bytes":a.stat().st_size,"sha256":hashlib.sha256(a.read_bytes()).hexdigest()})
assert len(matches)==len(list((r/"results/QB").rglob("*.f32")))
layers=set();geometry=collections.Counter()
for j in Q["actual_signatures"]:
    assert "B570" in j["device"]
    if j["name"].startswith("hs_qb_qk"):
        assert j["ne"]==[256,1,32,2]
        assert j["sources"][0]["ne"]==[128,256,8,1]
        layers.add(int(j["name"].split("-")[-1]));geometry[str(j["ne"])]+=1
assert layers==set(range(36))
assert len(P["cycles"])==10 and all(x["q_caller"]==2 for x in P["cycles"])
assert sum(x["accepted"]for x in P["cycles"])==6
assert n["qualification"]=="PASS" and n["timing_status"]=="NOT_ADMITTED_INTERNAL_TIME_RESERVE"
assert receipt["exit_code"]==0 and receipt["capture_complete"] and not receipt["deadline_kill_requested"]
out={"status":"QUALIFICATION_PASS_NO_CLEAN_TIMING","old_q1_full_logits_verified":len(old_matches),
     "PQ_QB_full_logits_pairs_verified":len(matches),"full_logits_pairs":matches,
     "actual_QB_q":2,"actual_key":256,"Hq":32,"Hkv":8,"layers_verified":len(layers),
     "endpoint_tokens":16,"stop_reason":"CAP","verify_cycles_per_arm":10,"accepted_proposals":6,
     "rejected_proposals":4,"scope":"One exposed prompt; new native bridge, no generalization or performance conclusion",
     "receipt":receipt}
(r/"CPU_RECHECK.json").write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items()if k not in ("full_logits_pairs","receipt")}))
