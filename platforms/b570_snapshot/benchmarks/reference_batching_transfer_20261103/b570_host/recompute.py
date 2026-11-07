"""Portable CPU reconstruction from a restored evidence archive. No study imports."""
from array import array
from pathlib import Path, PureWindowsPath
import argparse
import hashlib
import json
import math

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def digest(value):
    data=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()

def vectors(row, payload):
    tokens=row["endpoint"]["ids"]
    eog=row["endpoint"]["eog"]
    assert len(tokens)==len(eog)==row["endpoint"]["length"] and tokens[-1]==row["endpoint"]["terminal_id"]
    assert not any(eog[:-1]) and (eog[-1] or len(tokens)==128)
    emitted=[tokens[0]]
    names=["target_initial"]
    expected={"target_initial":tokens[0]}
    if row["cycles"]:
        position=row["cycles"][0]["base"]
        for number,cycle in enumerate(row["cycles"]):
            proposal=cycle["proposal"]
            decisions=cycle["decisions"]
            assert cycle["cycle"]==number and cycle["base"]==position
            assert cycle["batch_ids"]==[emitted[-1],proposal]
            matched=int(proposal==decisions[0])
            count=min(1+matched,len(tokens)-len(emitted))
            assert count>=1 and cycle["committed_ids"]==decisions[:count]
            names.extend(f"target_verify/{number}/{j}" for j in range(count))
            expected.update({f"target_verify/{number}/{j}":token for j,token in enumerate(decisions)})
            expected[f"draft_proposal/{number}"]=proposal
            emitted.extend(decisions[:count])
            position+=matched+1
            assert cycle["accepted"]==matched and cycle["keep"]==position
            assert cycle["target_kv_max"]==cycle["draft_kv_max"]==position-1
        assert emitted==tokens
    else:
        for index,token in enumerate(tokens[1:],1):
            name=f"target_ordinary/{index}"
            names.append(name)
            expected[name]=token
    saved=row["vectors"]
    if not saved:
        return []
    assert set(saved)==set(expected)
    for name,meta in saved.items():
        p=payload/meta["path"]
        raw=p.read_bytes()
        assert len(raw)==meta["bytes"]==151936*4
        assert hashlib.sha256(raw).hexdigest()==meta["sha256"]
        values=array("f")
        values.frombytes(raw)
        assert values.index(max(values))==expected[name]
    return [saved[name]["sha256"] for name in names]

def unit(root,name):
    p=root/"units"/name
    receipt=load(p/"RECEIPT.json")
    supervisor=load(p/"SUPERVISOR.json")
    d=load(p/"native/result.json")
    assert receipt["success"] and supervisor["job_accounting"]["active_processes"]==0
    assert d["normal_cleanup_returned"] and receipt["requests"]==len(d["requests"])
    return p,d,load(p/"JOB.json")

def run(root):
    root=Path(root)
    original_root=PureWindowsPath("I:/HeteroSpec/b570-qwen-transfer-20261103")
    def verify_pin(pin):
        path=PureWindowsPath(pin["path"]).relative_to(original_root)
        with root.joinpath(*path.parts).open("rb") as f:
            assert hashlib.file_digest(f,"sha256").hexdigest()==pin["sha256"]
    for pin in load(root/"FREEZE.json")["proofs"]:
        verify_pin(pin)
    original_dlls={PureWindowsPath(pin["path"]).name:pin["sha256"]
                   for pin in load(root/"historical/B1-4.launch.json")["files"] if pin["path"].endswith(".dll")}
    for role in ("original-final","shared-01"):
        for pin in load(root/role/"FILES.json")["files"]:
            verify_pin(pin)
            if role=="original-final" and pin["path"].endswith(".dll"):
                assert original_dlls[PureWindowsPath(pin["path"]).name]==pin["sha256"]
    panel=load(root/"UNSEEN.json")
    seal=load(root/"SELECTION.json")
    for file,key in [("FREEZE.json","freeze_sha256"),("UNSEEN.json","panel_sha256"),("COST_ORDER.json","order_sha256")]:
        assert hashlib.sha256((root/file).read_bytes()).hexdigest()==seal[key]
    assert len(panel)==8
    retained=[]
    for i in (4,6,2):
        history=load(root/"historical"/f"B1-{i}.result.json")["requests"]
        p,orig,_=unit(root,f"original-original-final-{i}")
        ref=orig["requests"][0]
        assert ref["endpoint"]==history[0]["endpoint"] and ref["vectors"]==history[2]["vectors"]
        target=vectors(ref,p/"payload")
        p,native,job=unit(root,f"retained-{i}-shared-01")
        for row,s in zip(native["requests"],job["slots"],strict=True):
            assert vectors(row,p/"payload")==target and row["endpoint"]==ref["endpoint"]
            state=row.get("restored_boundary",row.get("boundary"))
            assert all(state[k]["sha256"]==history[2]["boundary"][k]["sha256"] for k in ("kv","initial_logits"))
            retained.append(dict(id=s["input_id"],producer=s["producer"],consumer=s["consumer"],vectors=len(target)))
    p,rev,_=unit(root,"precision-off-shared-01")
    historical=load(root/"historical/B1-4.result.json")["requests"][8]
    negative=rev["requests"][1]
    assert all(negative[k]==historical[k] for k in ("endpoint","cycles","vectors"))
    vectors(negative,p/"payload")
    refs={};qual={};saved=0;committed=0
    for i,x in enumerate(panel.values()):
        p,original,_=unit(root,f"qual-{i}-R")
        r=original["requests"][0]
        refs[x["id"]]=r
        reference=vectors(r,p/"payload")
        saved+=len(r["vectors"])
        p,candidate,job=unit(root,f"qual-{i}-candidate")
        rows=candidate["requests"]
        for a,row,s in zip(("M_PQ","M_QB","C_PQ","C_QB"),rows[:4],job["slots"][:4],strict=True):
            assert s["input_id"]==x["id"] and s["prompt_ids_sha256"]==digest(x["prompt_ids"])
            assert row["endpoint"]==r["endpoint"] and vectors(row,p/"payload")==reference
            saved+=len(row["vectors"]);committed+=len(reference)
            qual[x["id"],a]=row
        for left,right in ((0,1),(2,3)):
            assert rows[left]["vectors"]==rows[right]["vectors"] and rows[left]["cycles"]==rows[right]["cycles"]
        if i==0:
            assert rows[3]["endpoint"]==rows[4]["endpoint"] and rows[3]["cycles"]==rows[4]["cycles"]
    arms=("R","M_PQ","M_QB","C_PQ","C_QB")
    blocks=[]
    total={k:[] for k in ("warmup_seconds","measured_seconds","model_load_seconds","process_seconds","host_owned_seconds")}
    order=load(root/"COST_ORDER.json")
    for session in range(3):
        inputs=sorted(panel,key=lambda id:digest(["qwen-cost-v1",session,id]))
        for n,id in enumerate(inputs):
            t={}
            for h,offset in enumerate((0,1,4,2,3)):
                index=session*40+n*5+h
                arm=arms[(int(digest(id)[:8],16)+session+offset)%5]
                assert order[index]=={"session":session,"id":id,"arm":arm}
                p,native,job=unit(root,f"cost-{index:03d}")
                assert len(native["requests"])==len(job["slots"])==2
                for j,label in enumerate(("warmup","measured")):
                    row=native["requests"][j]
                    assert job["slots"][j]["slot_id"]==f"{label}/{arm}" and job["slots"][j]["input_id"]==id
                    assert row["performance_eligible"] and row["endpoint"]==refs[id]["endpoint"]
                    assert not row["vectors"] and not row["geometry_files"] and not row["target_caller_trace"] and "phase_seconds" not in row
                    assert row["cycles"]==([] if arm=="R" else qual[id,arm]["cycles"])
                    vectors(row,p/"payload")
                    t[arm]=row["service_seconds"];assert math.isfinite(t[arm]) and t[arm]>0
                    total[label+"_seconds"].append(t[arm])
                total["model_load_seconds"].append(native["model_load_seconds"])
                total["process_seconds"].append(load(p/"SUPERVISOR.json")["charged_seconds"])
                total["host_owned_seconds"].append(load(p/"RECEIPT.json")["owned_seconds"])
            blocks.append((session,t))
    actual=load(root/"COST.json")
    assert len(blocks)==24 and actual["measurements"]==actual["warmups"]==120
    contrasts={}
    for a,b in [("M_QB","M_PQ"),("C_QB","C_PQ"),("M_QB","C_QB"),("M_QB","R"),("C_QB","R")]:
        ratios=[(s,t[a]/t[b]) for s,t in blocks]
        def gm(xs):return math.exp(math.fsum(math.log(v) for v in xs)/len(xs))
        key=f"{a}/{b}"
        means=[gm([v for s,v in ratios if s==j]) for j in range(3)]
        contrasts[key]=gm([v for _,v in ratios])
        assert actual["comparisons"][key]["ratio"]==contrasts[key] and actual["comparisons"][key]["sessions"]==means
    totals={k:math.fsum(x) for k,x in total.items()}
    assert all(actual["totals"][k]==v for k,v in totals.items())
    return dict(status="INDEPENDENT_RECONSTRUCTION_PASS",retained=retained,inputs=8,qualification_requests=41,
                qualification_saved_vectors=saved,committed_candidate_vectors=committed,warmups=120,measurements=120,
                contrasts=contrasts,totals=totals,model_forwards=0)

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,required=True);ap.add_argument("--out",type=Path,required=True);a=ap.parse_args()
    with a.out.open("x",encoding="utf-8") as f:json.dump(run(a.root),f,indent=2);f.write("\n")

