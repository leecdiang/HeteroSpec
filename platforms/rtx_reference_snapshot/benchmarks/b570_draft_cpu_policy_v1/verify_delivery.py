from pathlib import Path
import json,math,hashlib,datetime
r=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def digest(p):
    h=hashlib.sha256()
    with p.open("rb")as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""):h.update(chunk)
    return h.hexdigest()
m=read(r/"BUILD_MANIFEST.json")
for x in m["files"]:assert digest(Path(x["path"]))==x["sha256"],x["path"]
ref=read(Path("C:/hs/b570-spec-bridge-20261020200000/results/result.json"))
warm=0;measured=0;ratios=[];prior_exit=None
for step in range(8):
    mode="qual"if step<4 else"time";idx=step%4
    rc=read(r/f"{mode}-{idx}.PROCESS_RECEIPT.json")
    assert rc["exit_code"]==0 and rc["capture_complete"] and rc["exit_observed"] and not rc["deadline_kill_requested"]
    assert rc["status"]=="PROCESS_COMPLETED"
    if prior_exit:assert rc["started_utc"]>prior_exit
    prior_exit=rc["os_exit_utc"]
    if mode=="qual":continue
    n=read(r/f"{mode}-{idx}/result.json")
    assert n["normal_cleanup_returned"]and n["status"]=="TIMING_PASS"
    for x in n["requests"]:
        assert x["service_seconds"]>=x["request_seconds"]>0 and not x["capture"]
        if x["category"]=="warmup":
            y=ref["requests"][0 if x["label"]=="R"else 2]
            for k in ("ids","eog","length","terminal_id","stop_reason"):assert x[k]==y[k]
            if x["label"]!="R":assert x["cycles"]==y["cycles"]
            warm+=1
        else:measured+=1
    for inp in read(r/"INPUT_PANEL.json")["inputs"]:
        cells={x["label"]:x for x in n["requests"]if x["category"]=="steady"and x["input_id"]==inp["id"]}
        ratios.append(cells["DRAFT1"]["service_seconds"]/(.5*(cells["BASE_A"]["service_seconds"]+cells["BASE_B"]["service_seconds"])))
primary=math.prod(ratios)**(1/16)
assert abs(primary-read(r/"ANALYSIS.json")["service_DRAFT1_over_dualBASE"])<1e-12
l=read(r/"BUDGET_LEDGER.json")
assert abs(sum(x["charged_seconds"]for x in l["sessions"])-l["new_charged_seconds"])<1e-9
assert abs(l["all_history_cumulative_seconds"]-(1817.8040152+l["new_charged_seconds"]))<1e-9
assert measured==64 and warm==16
out={"status":"PASS","frozen_inputs_unchanged":len(m["files"]),"warmups_rechecked":warm,"measured_requests":measured,"independently_recomputed_service_ratio":primary,"nonoverlapping_native_processes":8,"ledger_sum_verified":True}
(r/"DELIVERY_CHECK.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
