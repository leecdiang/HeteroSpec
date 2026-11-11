"""CPU-only preregistered paired-block analysis. No GPU or GGML imports."""
import os
os.environ["OPENBLAS_NUM_THREADS"]="1"
import json, pathlib, math
import numpy as np
root=pathlib.Path(__file__).parent
coords=[(n,q) for n in (1023,1024,1025) for q in (1,2,4)]
arms=["QB_A","QB_B","QH_C"]
data=np.empty((9,3,3,6,3),dtype=np.float64)
audit=[]
for session in range(3):
    folder=root/f"session-{session}"
    result=json.loads((folder/"result.json").read_text())
    assert result["status"]=="EXPLORATORY_ALL_PASS"
    assert len(result["rows"])==81 and all(x["numerical"]=="PASS" and x["timing"]=="PASS" for x in result["rows"])
    records=[json.loads(s) for s in (folder/"timing.jsonl").read_text().splitlines()]
    assert len(records)==162
    seen=set()
    for rec in records:
        n,q,i,b=rec["key"],rec["q"],rec["input"],rec["block"]
        token=(n,q,i,b);assert token not in seen;seen.add(token)
        assert rec["session"]==session and set(p["permutation"] for p in rec["permutations"])==set(range(6))
        samples={a:[] for a in arms}
        positions={a:[0,0,0] for a in arms}
        for perm in rec["permutations"]:
            assert {v["arm"] for v in perm["visits"]}==set(arms)
            for visit in perm["visits"]:
                a=visit["arm"];positions[a][visit["position"]]+=1
                assert len(visit["samples_ms"])==5 and all(math.isfinite(v) and v>0 for v in visit["samples_ms"])
                samples[a].extend(visit["samples_ms"])
        for a in arms:
            assert positions[a]==[2,2,2] and len(samples[a])==30
            assert abs(np.mean(samples[a])-rec["arm_means_ms"][a])<1e-12
        data[coords.index((n,q)),session,i,b,:]=[np.mean(samples[a])*1000 for a in arms]
    audit.append({"session":session,"blocks":len(records),"timed_calls":len(records)*90,"balance_pass":True,"native_graph_calls":result["graph_computations_returned"]})
# Resample three session clusters and blocks within each fixed input, preserving arm pairing.
# Shared resampling indices across coordinates retain block/session covariance for the core panel.
rng=np.random.default_rng(20261020);B=20000
ss=rng.integers(0,3,size=(B,3))
bb=rng.integers(0,6,size=(B,3,3,6))
ii=np.arange(3)[None,None,:,None]
alpha=.05/10
def interval(x):return np.quantile(x,[alpha/2,1-alpha/2]).tolist()
boots_d=[];boots_log=[];rows=[]
def evaluate(arr,bd,bl,label):
    base=(arr[...,0]+arr[...,1])/2
    diff=arr[...,2]-base
    aa=arr[...,1]-arr[...,0]
    ci=interval(bd)
    threshold=max(1.0,.02*float(base.mean()),float(np.quantile(np.abs(aa),.95)))
    session_d=diff.mean(axis=(1,2));input_d=diff.mean(axis=(0,2))
    da=float((arr[...,2]-arr[...,0]).mean());db=float((arr[...,2]-arr[...,1]).mean())
    slower=ci[0]>threshold and (session_d>0).all() and (input_d>0).all() and min(da,db)>threshold
    faster=ci[1]<-threshold and (session_d<0).all() and (input_d<0).all() and max(da,db)<-threshold
    return {"coordinate":label,"qb_a_mean_us":float(arr[...,0].mean()),"qb_b_mean_us":float(arr[...,1].mean()),
      "qh_c_mean_us":float(arr[...,2].mean()),"qh_minus_qb_mean_us":float(diff.mean()),
      "qh_over_qb_geomean":float(np.exp(np.log(arr[...,2]/base).mean())),
      "paired_difference_ci_us":ci,"paired_ratio_ci":np.exp(interval(bl)).tolist(),
      "aa_mean_difference_us":float(aa.mean()),"aa_p95_abs_block_difference_us":float(np.quantile(np.abs(aa),.95)),
      "screen_threshold_us":threshold,"session_mean_differences_us":session_d.tolist(),"input_mean_differences_us":input_d.tolist(),
      "raw_screen":"QH_C_SLOWER_BEYOND_AA" if slower else "QH_C_FASTER_BEYOND_AA" if faster else "UNRESOLVED",
      "paired_blocks":54,"independent_process_sessions":3}
for c,(n,q) in enumerate(coords):
    arr=data[c]
    draw=arr[ss[:,:,None,None],ii,bb,:]
    base=(draw[...,0]+draw[...,1])/2
    bd=(draw[...,2]-base).mean(axis=(1,2,3))
    bl=np.log(draw[...,2]/base).mean(axis=(1,2,3))
    boots_d.append(bd);boots_log.append(bl)
    row=evaluate(arr,bd,bl,{"key":n,"q":q});rows.append(row)
calibrated=all(row["raw_screen"]=="UNRESOLVED" for row in rows if row["coordinate"]["q"]==1)
for row in rows:
    row["conclusion"]=row["raw_screen"] if calibrated else "OBSERVER_NOT_CALIBRATED"
core=[c for c,(_,q) in enumerate(coords) if q>1]
core_arr=data[core].mean(axis=0)
panel=evaluate(core_arr,np.mean([boots_d[c] for c in core],axis=0),np.mean([boots_log[c] for c in core],axis=0),"Fixed equal-weight q2/q4 core panel")
# Panel ratio point estimate must use the same equal-weight coordinate log window as its bootstrap.
panel["qh_over_qb_geomean"]=float(np.exp(np.mean([np.log(data[c,...,2]/((data[c,...,0]+data[c,...,1])/2)).mean() for c in core])))
panel["conclusion"]=panel["raw_screen"] if calibrated else "OBSERVER_NOT_CALIBRATED"
report={"status":"ANALYSIS_COMPLETE","gpu_execution":False,"q1_calibration_passed":calibrated,
 "method":{"bootstrap_replicates":B,"seed":20261020,"family_claims":10,"per_claim_ci_level":1-alpha,
 "unit":"Paired six-permutation block means; calls are technical repeats, not independent samples",
 "resampling":"Session clusters, then blocks within fixed input; shared indices across coordinates",
 "screen":"Family-adjusted CI wholly beyond max(1 us,2% QB mean,p95 absolute AA block noise), all session/input directions agree, point differences exceed threshold against both QB arms",
 "q1_rule":"Any q1 raw screen triggers observer-not-calibrated for all mapping conclusions",
 "scope":"Three fresh processes on one device/date with three fixed inputs. Few clusters; descriptive preregistered screen, not population-level proof."},
 "audit":audit,"coordinates":rows,"core_panel":panel}
(root/"ANALYSIS.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"q1_calibration_passed":calibrated,"coordinate_screens":[{"key":r["coordinate"]["key"],"q":r["coordinate"]["q"],"difference_us":r["qh_minus_qb_mean_us"],"threshold_us":r["screen_threshold_us"],"result":r["conclusion"]} for r in rows],"core_panel":panel},indent=2))
