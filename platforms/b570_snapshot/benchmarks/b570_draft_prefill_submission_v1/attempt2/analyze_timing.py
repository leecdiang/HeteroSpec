from pathlib import Path
import json,math,statistics,csv
r=Path(__file__).parent;p=Path("C:/hs/b570-formal-request-20261020")
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def gm(xs):return math.exp(statistics.mean(math.log(x)for x in xs))
assert read(r/"QUALIFICATION_RECHECK.json")["status"]=="PANEL_QUALIFIED"
full=read(r/"INPUT_PANEL.json");panel=[full["inputs"][i]for i in (0,2)]
orders=[["BASE_A","BASE_B","BULK1"],["BASE_B","BULK1","BASE_A"],["BULK1","BASE_A","BASE_B"]]
rows=[];warm=[]
for s in range(3):
    n=read(r/f"time-{s}/result.json");rc=read(r/f"time-{s}.PROCESS_RECEIPT.json")
    assert n["status"]=="TIMING_PASS" and n["normal_cleanup_returned"]
    assert rc["exit_code"]==0 and rc["capture_complete"] and not rc["deadline_kill_requested"]
    assert len(n["requests"])==9
    expected=[("warmup",full["warmup"])]*3+[( "steady",panel[(s+j)%2])for j in range(2)for _ in range(3)]
    for pos,x in enumerate(n["requests"]):
        cat,inp=expected[pos]
        assert x["category"]==cat and x["input_id"]==inp["id"] and x["label"]==orders[s][pos%3]
        if cat=="warmup":ref=read(Path("C:/hs/b570-spec-bridge-20261020200000/results/result.json"))["requests"][2]
        else:
            i=next(i for i,z in enumerate(full["inputs"])if z["id"]==inp["id"])
            ref=read(p/f"qual-{i}/result.json")["requests"][2]
        for k in ("ids","eog","length","terminal_id","stop_reason","cycles"):assert x[k]==ref[k]
        assert x["draft_prefill_api_calls"]==(1 if x["label"]=="BULK1"else len(inp["prompt_ids"]))
        assert x["draft_microbatch_limit"]==1 and not x["capture"]
        if cat=="warmup":warm.append({"session":s,**x});continue
        phases={f"target_{k}":v for k,v in x["target_decode_seconds"].items()}
        phases.update({f"draft_{k}":v for k,v in x["draft_decode_seconds"].items()})
        residual=x["request_seconds"]-sum(phases.values());assert residual>=0
        rows.append({"session":s,"input_id":x["input_id"],"arm":x["label"],"service_seconds":x["service_seconds"],
                     "request_seconds":x["request_seconds"],"context_and_teardown_seconds":x["service_seconds"]-x["request_seconds"],
                     "unassigned_request_seconds":residual,"phases":phases,"output_tokens":x["length"],"stop_reason":x["stop_reason"],
                     "cycles":len(x["cycles"]),"accepted":sum(c["accepted"]for c in x["cycles"])})
assert len(rows)==18 and len(warm)==9
pairs=[]
for s in range(3):
    for x in panel:
        a={z["arm"]:z for z in rows if z["session"]==s and z["input_id"]==x["id"]}
        assert len(a)==3
        base=statistics.mean(a[k]["service_seconds"]for k in ("BASE_A","BASE_B"))
        req=statistics.mean(a[k]["request_seconds"]for k in ("BASE_A","BASE_B"))
        pairs.append({"session":s,"input_id":x["id"],"service_BULK1_over_dualBASE":a["BULK1"]["service_seconds"]/base,
                      "request_BULK1_over_dualBASE":a["BULK1"]["request_seconds"]/req,
                      "service_BASEA_over_BASEB":a["BASE_A"]["service_seconds"]/a["BASE_B"]["service_seconds"]})
perinput=[]
for x in panel:
    ps=[z for z in pairs if z["input_id"]==x["id"]]
    perinput.append({"input_id":x["id"],**{k:gm(z[k]for z in ps)for k in ps[0]if k.startswith(("service_","request_"))}})
ratio=gm(x["service_BULK1_over_dualBASE"]for x in perinput)
noise=max(abs(x["service_BASEA_over_BASEB"]-1)for x in perinput)
session_ratios=[gm(x["service_BULK1_over_dualBASE"]for x in pairs if x["session"]==s)for s in range(3)]
passed=1-ratio>max(.02,noise) and all(x<1 for x in session_ratios)
out={"decision":"PRACTICAL_FINITE_PANEL_SCREEN_PASS"if passed else"NO_ESTABLISHED_PRACTICAL_PANEL_BENEFIT",
     "service_BULK1_over_dualBASE":ratio,"request_BULK1_over_dualBASE":gm(x["request_BULK1_over_dualBASE"]for x in perinput),
     "largest_aggregate_AA_imbalance":noise,"threshold":max(.02,noise),"per_session_ratios":session_ratios,
     "per_input":perinput,"paired_blocks":pairs,"raw_timing_rows":rows,"warmup":warm,
     "scope":"Two fixed exposed inputs,3 processes,one date; no population CI, equivalence claim or new target-only comparison"}
(r/"ANALYSIS.json").write_text(json.dumps(out,indent=2))
with(r/"TIMING_TABLE.csv").open("w",newline="")as f:
    w=csv.DictWriter(f,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
print(json.dumps({k:v for k,v in out.items()if k not in ("raw_timing_rows","warmup","paired_blocks")},indent=2))
