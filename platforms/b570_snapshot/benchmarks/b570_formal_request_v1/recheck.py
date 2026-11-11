from pathlib import Path
import json,hashlib,sys
r=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
panel=read(r/"INPUT_PANEL.json")["inputs"]
rows=[];failures=[];raw=[]
for i,input in enumerate(panel):
    path=r/f"qual-{i}/result.json"
    if not path.exists():rows.append({"input":input["id"],"status":"NOT_EXECUTED"});continue
    n=read(path);receipt=read(r/f"qual-{i}.PROCESS_RECEIPT.json")
    out={"input":input["id"],"status":n["status"],"requests":len(n["requests"]),"error":n.get("error"),"charge":receipt["charged_seconds"]}
    for f in sorted(path.parent.rglob("*.f32")):
        raw.append({"path":str(f.relative_to(r)).replace("\\","/"),"bytes":f.stat().st_size,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()})
    if n["status"]!="QUALIFICATION_PASS":
        if len(n["requests"])>=2:
            a,b=n["requests"][:2]
            out["endpoint_differences"]={k:{"R":a[k],"PQ":b[k]}for k in ("ids","eog","length","terminal_id","stop_reason")if a[k]!=b[k]}
            out["first_id_mismatch"]=next((j for j,(x,y)in enumerate(zip(a["ids"],b["ids"]))if x!=y),None)
        rows.append(out);failures.append(input["id"]);continue
    assert receipt["exit_code"]==0 and receipt["capture_complete"] and not receipt["deadline_kill_requested"]
    a,b,c=n["requests"]
    for key in ("ids","eog","length","terminal_id","stop_reason"):assert a[key]==b[key]==c[key]
    assert b["cycles"]==c["cycles"]
    pairs=0
    for f in (path.parent/"qual-1").rglob("*.f32"):
        assert f.read_bytes()==(path.parent/"qual-2"/f.relative_to(path.parent/"qual-1")).read_bytes()
        pairs+=1
    assert pairs==n["full_logit_pairs"]
    shapes=set();layers=set()
    for x in c["actual_signatures"]:
        assert "B570"in x["device"]
        if x["name"].startswith("hs_qb_qk"):
            assert x["ne"][0]in (256,512) and x["ne"][1:]==[1,32,2]
            assert x["sources"][0]["ne"]==[128,x["ne"][0],8,1]
            layers.add(int(x["name"].split("-")[-1]));shapes.add(tuple(x["ne"]))
    assert layers==set(range(36))
    out.update(full_logit_pairs=pairs,geometry=sorted(shapes),layers=len(layers),tokens=a["length"],stop=a["stop_reason"],cycles=len(b["cycles"]),accepted=sum(x["accepted"]for x in b["cycles"]))
    rows.append(out)
out={"status":"PANEL_QUALIFIED"if all(x["status"]=="QUALIFICATION_PASS"for x in rows)else"NOT_QUALIFIED","rows":rows,"raw_files":len(raw),"failures":failures}
(r/"RAW_LOGITS_MANIFEST.json").write_text(json.dumps(raw,indent=2))
name="QUALIFICATION_RECHECK.json"if out["status"]=="PANEL_QUALIFIED"else"QUALIFICATION_STATUS.json"
(r/name).write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
if out["status"]!="PANEL_QUALIFIED":sys.exit(2)
