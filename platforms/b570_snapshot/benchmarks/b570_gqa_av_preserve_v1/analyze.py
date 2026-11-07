"""CPU-only independent reconstruction of every returned stage and backing store."""
from pathlib import Path
import json, hashlib
import numpy as np
r=Path(__file__).parent
native=json.loads((r/"results/result.json").read_text())
receipt=json.loads((r/"PROCESS_RECEIPT.json").read_text(encoding="utf-8-sig"))
manifest=json.loads((r/"BUILD_MANIFEST.json").read_text())
for f in manifest["files"]:
    assert hashlib.sha256(Path(f["path"]).read_bytes()).hexdigest()==f["sha256"],f["path"]
report={"frozen_inputs_verified":len(manifest["files"]),"rows":[],"pairs":[],"native_status":native["status"],
        "budget":receipt,"independent_environment":False,"scope":"same-machine CPU reread of all produced raw, not external authentication"}
for row in native["rows"]:
    n,q,arm=row["n"],row["q"],row["arm"]
    p=r/"results"/f"{n}-q{q}-{arm}"
    Q=np.fromfile(p/"q.f32",np.float32).reshape(q,32,128).astype(np.float64)
    K=np.fromfile(p/"k_storage.f16",np.float16).reshape(1024,8,128)[:n].astype(np.float64)
    V=np.fromfile(p/"v_storage.f16",np.float16).reshape(8,128,1024)[:,:,:n].astype(np.float64)
    M=np.fromfile(p/"mask.f32",np.float32).reshape(32,n)[:q].astype(np.float64)
    for name,source in [("q","q.f32"),("k","k_storage.f16"),("v","v_storage.f16"),("mask","mask.f32")]:
        assert (p/source).read_bytes()==(p/f"{name}-before.bin").read_bytes()==(p/f"{name}-after.bin").read_bytes()
    S=np.einsum("jhd,thd->jht",Q,K[:,np.arange(32)//4,:])
    scale=np.float32(1)/np.sqrt(np.float32(128))
    logits=S*float(scale)+M[:,None,:]
    P=np.exp(logits-logits.max(axis=-1,keepdims=True));P/=P.sum(axis=-1,keepdims=True)
    A=np.einsum("hdt,jht->jhd",V[np.arange(32)//4],P)
    details={}
    for name,expected in [("qk",S),("softmax",P),("av",A),("final",A)]:
        actual=np.fromfile(p/f"{name}.f32",np.float32).reshape(expected.shape)
        err=np.abs(actual-expected)
        assert np.isfinite(actual).all() and (err<=.0002+.002*np.abs(expected)).all()
        details[name]={"elements":actual.size,"max_abs_error":float(err.max())}
    report["rows"].append({"n":n,"q":q,"arm":arm,"full_backing_bytes_unchanged":True,"fp64":details})
    if arm=="QB":
        pair={"n":n,"q":q,"stages":{}}
        for stage in ("qk","softmax","av","final"):
            aa=np.fromfile(r/"results"/f"{n}-q{q}-PQ"/f"{stage}.f32",np.float32)
            bb=np.fromfile(p/f"{stage}.f32",np.float32)
            inds=np.flatnonzero(aa.view(np.uint32)!=bb.view(np.uint32))
            d={"elements":aa.size,"mismatch_count":len(inds),"max_abs_difference":float(np.max(np.abs(aa.astype(float)-bb)))}
            if len(inds):
                i=int(inds[0]);d["first"]={"flat_index":i,"query":i//(32*128),"head":(i//128)%32,"dim":i%128,"pq":float(aa[i]),"qb":float(bb[i]),"pq_hex":hex(int(aa.view(np.uint32)[i])),"qb_hex":hex(int(bb.view(np.uint32)[i]))}
            pair["stages"][stage]=d
        report["pairs"].append(pair)
assert len(report["rows"])==12 and len(report["pairs"])==6
assert all(c["actual"]==c["expected"] for c in native["admission_controls"])
assert report["pairs"][-1]["stages"]["qk"]["mismatch_count"]==0
assert report["pairs"][-1]["stages"]["softmax"]["mismatch_count"]==0
assert all(s["mismatch_count"]==0 for pair in report["pairs"] for s in pair["stages"].values())
previous=Path("C:/hs/b570-gqa-admission-20261020184000/results")
report["prior_PQ_stage_files_verified"]=0
for row in report["rows"]:
    if row["arm"]!="PQ":continue
    d=f'{row["n"]}-q{row["q"]}-PQ'
    for name in ("qk","softmax","av","final"):
        old=previous/d/(name+".f32")
        if old.exists():
            assert old.read_bytes()==(r/"results"/d/(name+".f32")).read_bytes()
            report["prior_PQ_stage_files_verified"]+=1
assert report["prior_PQ_stage_files_verified"]==20
assert receipt["exit_observed"] and receipt["capture_complete"] and receipt["exit_code"]==0
assert native["normal_cleanup_returned"] and native["computes"]==12
assert abs(receipt["cumulative_charged_seconds"]-248.4105591-receipt["charged_seconds"])<1e-8
report["decision"]="SIX_COORDINATE_OPERATOR_PANEL_PASS; natural request remains unqualified"
(r/"CPU_RECHECK.json").write_text(json.dumps(report,indent=2))
print(json.dumps({"rows":len(report["rows"]),"pairs":len(report["pairs"]),"last_pair":report["pairs"][-1],"decision":report["decision"]},indent=2))
