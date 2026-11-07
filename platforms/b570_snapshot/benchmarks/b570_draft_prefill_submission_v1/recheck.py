from pathlib import Path
import json,hashlib,sys
r=Path(__file__).parent;p=Path("C:/hs/b570-formal-request-20261020")
def read(x):return json.loads(x.read_text(encoding="utf-8-sig"))
rows=[];raw=[]
for i,inp in enumerate(read(r/"INPUT_PANEL.json")["inputs"]):
    path=r/f"qual-{i}/result.json"
    if not path.exists():rows.append({"input":inp["id"],"status":"NOT_EXECUTED"});continue
    n=read(path);old=read(p/f"qual-{i}/result.json")["requests"][2]
    out={"input":inp["id"],"status":n["status"],"error":n.get("error")}
    if n["status"]!="QUALIFICATION_PASS":rows.append(out);continue
    rc=read(r/f"qual-{i}.PROCESS_RECEIPT.json");assert rc["exit_code"]==0 and rc["capture_complete"]and not rc["deadline_kill_requested"]
    x=n["requests"][0]
    for k in ("ids","eog","length","terminal_id","stop_reason","cycles"):assert x[k]==old[k]
    assert x["draft_prefill_api_calls"]==1 and x["draft_prefill_q_observed"]==1 and x["draft_microbatch_limit"]==1
    pairs=0
    for a in sorted((p/f"qual-{i}/qual-2").rglob("*.f32")):
        rel=a.relative_to(p/f"qual-{i}/qual-2");b=r/f"qual-{i}/qual-0"/rel
        assert a.read_bytes()==b.read_bytes(),(i,rel)
        raw.append({"path":str(b.relative_to(r)).replace("\\","/"),"bytes":b.stat().st_size,"sha256":hashlib.sha256(b.read_bytes()).hexdigest()});pairs+=1
    assert pairs==n["historical_full_logits_matched"]
    out.update(full_logit_pairs=pairs,tokens=x["length"],stop=x["stop_reason"],cycles=len(x["cycles"]),draft_prefill_api_calls=1,physical_prefill_q=x['draft_prefill_q_observed'])
    rows.append(out)
out={"status":"PANEL_QUALIFIED"if all(x["status"]=="QUALIFICATION_PASS"for x in rows)else"NOT_QUALIFIED","rows":rows,"full_logits":len(raw)}
(r/"RAW_LOGITS_MANIFEST.json").write_text(json.dumps(raw,indent=2))
(r/("QUALIFICATION_RECHECK.json"if out["status"]=="PANEL_QUALIFIED"else"QUALIFICATION_STATUS.json")).write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
if out["status"]!="PANEL_QUALIFIED":sys.exit(2)
