"""Independent CPU-only recheck of saved F16 operands and all numerical evidence."""
import os
os.environ["OPENBLAS_NUM_THREADS"]="1"
import json,hashlib,pathlib
import numpy as np
root=pathlib.Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compare(a,b):
    assert a.shape==b.shape
    e=np.abs(a.astype(np.float64)-b)
    assert np.isfinite(a).all() and np.isfinite(b).all()
    assert (e<=.0002+.002*np.abs(b)).all()
    return float(e.max())
report={"status":"STARTED","gpu_execution":False,"sessions":[],"stage_checks":0,"input_readbacks":0,"post_block_byte_checks":0,"pair_byte_checks":0}
for s in range(3):
    result=json.loads((root/f"session-{s}"/"result.json").read_text())
    witnesses=[];hashes={};max_error=0
    for row in result["rows"]:
        n,q,i,arm=row["key"],row["q"],row["input"],row["mode"]
        p=root/f"session-{s}"/f"{n}-q{q}-i{i}-{arm}"
        Q=np.fromfile(p/"q.f32",dtype="<f4").astype(np.float64).reshape(8,q,128)
        K=np.fromfile(p/"k.f16",dtype="<f2").astype(np.float64).reshape(8,n,128)
        V=np.fromfile(p/"v.f16",dtype="<f2").astype(np.float64).reshape(8,128,n)
        M=np.fromfile(p/"mask.f32",dtype="<f4").astype(np.float64).reshape(32,n)[:q]
        expected=np.zeros((q,n))
        for j in range(q):expected[j,n-q+j+1:]=-np.inf
        assert np.array_equal(M,expected)
        scores=np.einsum("hjd,hnd->jhn",Q,K)
        logits=scores*float(np.float32(1.0)/np.sqrt(np.float32(128.0)))+M[:,None,:]
        probs=np.exp(logits-logits.max(axis=-1,keepdims=True));probs/=probs.sum(axis=-1,keepdims=True)
        final=np.einsum("hdn,jhn->jhd",V,probs)
        def stage(file,width):
            a=np.fromfile(p/file,dtype="<f4")
            return a.reshape(8,q,width).transpose(1,0,2) if arm=="QH_C" and q>1 else a.reshape(q,8,width)
        errs={}
        for file,width,ref in [("gpu_qk.f32",n,scores),("gpu_softmax.f32",n,probs),("gpu_av.f32",128,final)]:
            errs[file]=compare(stage(file,width),ref);report["stage_checks"]+=1
        errs["gpu_final.f32"]=compare(np.fromfile(p/"gpu_final.f32",dtype="<f4").reshape(q,8,128),final);report["stage_checks"]+=1
        base_hash=sha(p/"gpu_final.f32")
        for b in range(6):
            f=p/f"gpu_final_block{b}.f32"
            assert sha(f)==base_hash;report["post_block_byte_checks"]+=1
            compare(np.fromfile(f,dtype="<f4").reshape(q,8,128),final);report["stage_checks"]+=1
        if arm=="QB_A":
            hashes[(n,q,i)]=base_hash
        else:
            assert base_hash==hashes[(n,q,i)];report["pair_byte_checks"]+=1
        for name,orig in [("q","q.f32"),("k","k.f16"),("v","v.f16"),("mask","mask.f32")]:
            for when in ["before","after-numerical","after-timing"]:
                assert sha(p/orig)==sha(p/f"{name}.{when}.bin");report["input_readbacks"]+=1
        max_error=max(max_error,errs["gpu_final.f32"])
        witnesses.append({"key":n,"q":q,"input":i,"arm":arm,"max_abs_errors":errs,"final_sha256":base_hash})
    # Different inputs are materialized distinctly, and the same fixed inputs recur in every session.
    for n in (1023,1024,1025):
        for q in (1,2,4):
            assert len({sha(root/f"session-{s}"/f"{n}-q{q}-i{i}-QB_A"/"q.f32") for i in range(3)})==3
    report["sessions"].append({"session":s,"slots":len(witnesses),"max_final_abs_error":max_error,"witnesses":witnesses})
report["status"]="CPU_RAW_RECHECK_ALL_PASS"
(root/"CPU_RAW_RECHECK.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k!="sessions"}))
