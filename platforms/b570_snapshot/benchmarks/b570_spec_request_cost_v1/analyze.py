from pathlib import Path
import json,statistics,hashlib
r=Path(__file__).parent
ref=json.loads((r/"QUALIFIED_REFERENCE.json").read_text())["requests"][1]
rows=[]
for i in range(3):
    n=json.loads((r/f"session-{i}/result.json").read_text())
    rc=json.loads((r/f"session-{i}.PROCESS_RECEIPT.json").read_text(encoding="utf-8-sig"))
    assert n["status"]=="COST_SESSION_PASS" and n["normal_cleanup_returned"]
    assert rc["exit_code"]==0 and rc["exit_observed"] and rc["capture_complete"] and not rc["deadline_kill_requested"]
    values={}
    for req in n["requests"]:
        assert req["capture"] is False
        for field in ("ids","eog","length","terminal_id","stop_reason","cycles"):
            assert req[field]==ref[field],(i,req["label"],field)
        assert req["reference_endpoint_and_cycles_match"]
        values[req["label"]]=req["request_seconds"]
    a,b,q=values["PQ_A"],values["PQ_B"],values["QB"];base=(a+b)/2
    rows.append({"session":i,"order":n["order"],"seconds":values,"dual_PQ_seconds":base,
                 "QB_minus_dual_PQ_seconds":q-base,"QB_over_dual_PQ":q/base,
                 "PQ_A_minus_PQ_B_seconds":a-b,"QB_faster_than_both":q<min(a,b),"parent_charge":rc["charged_seconds"]})
baseline=statistics.mean(x["dual_PQ_seconds"]for x in rows)
qmean=statistics.mean(x["seconds"]["QB"]for x in rows)
noise=max(abs(x["PQ_A_minus_PQ_B_seconds"])for x in rows)
threshold=max(.02*baseline,noise)
gain=baseline-qmean
decision="PRACTICAL_BENEFIT_SCREEN_PASS" if gain>threshold and all(x["QB_faster_than_both"]for x in rows) else "NO_ESTABLISHED_PRACTICAL_REQUEST_GAIN"
ledger=json.loads((r/"BUDGET_LEDGER.json").read_text(encoding="utf-8-sig"))
assert abs(sum(x["parent_charge"]for x in rows)-ledger["new_study_charged_seconds"])<1e-8
out={"rows":rows,"mean_dual_PQ_seconds":baseline,"mean_QB_seconds":qmean,
     "mean_gain_seconds":gain,"ratio_of_means":qmean/baseline,
     "largest_AA_difference_seconds":noise,"predeclared_screen_seconds":threshold,
     "decision":decision,"requests_verified":9,"complete_endpoint_and_cycle_trace_matches":9,
     "independent_processes":3,"independent_inputs":1,"dates":1,
     "confidence_interval":None,"note":"Descriptive bounded pilot, no population inference or per-operator attribution.",
     "ledger":ledger}
(r/"ANALYSIS.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
