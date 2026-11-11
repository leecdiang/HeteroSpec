"""Fixed candidate qualification and matched end-to-end cost panel."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from build import HERE,BASE,OUT
from mechanism import put
ROOT=OUT.parent
PREV=HERE.parent/"reference_batching_transfer_20261103/rtx_execution"
OLD=Path("E:/rtx164/confirmation01/qwen8b02")
ARMS=["R","S1","PQ-ext","QB-local","WB-cut","native32","native-full","native-ordinary"]
CFG=json.loads((OLD/"CONFIG.json").read_bytes())
def read(p):return json.loads(p.read_bytes())
def sha(p):
    with p.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
def run(exe,args,out,stdin=None):
    out.mkdir(parents=True,exist_ok=False)
    lock=Path(CFG["gpu_lock_file"])
    if shutil.disk_usage(out).free<12*1024**3:raise RuntimeError("disk admission")
    with lock.open("x") as f:json.dump({"pid":os.getpid(),"work":str(out)},f)
    start=time.monotonic()
    try:
        env={k:v for k,v in os.environ.items() if not k.startswith(("HS_","HSC_","GGML_","JSA_"))}
        env["CUDA_VISIBLE_DEVICES"]=CFG["gpu_uuid"]
        with (out/"native.log").open("xb") as log:
            r=subprocess.run([exe,*args],input=stdin,stdout=log,stderr=subprocess.STDOUT,env=env,timeout=3600)
        put(out/"exit.json",dict(code=r.returncode,elapsed=time.monotonic()-start))
        r.check_returncode()
    finally:lock.unlink()

def service(root,items,ctx,arms,mode,oracle=False,session=0):
    exe=(ROOT/"oracle01" if oracle else OUT/"bin")/"service.exe"
    blocks=[]
    for i,x in enumerate(items):
        for index in range(len(arms)):
            arm=arms[(index+i+session)%len(arms)]
            roles=["warm","timed"] if mode=="cost" else ["capture"]
            blocks.append(dict(arm=arm,slots=[dict(id=f"i{i}/{arm}/{r}",capture=r=="capture",input=x) for r in roles]))
    manifest=root.with_suffix(".json")
    put(manifest,dict(ctx=ctx,width=32,layers=999,blocks=blocks))
    run(exe,[CFG["target"],CFG["draft"],manifest,root],root)

def original(root,items):
    slots=read(OLD/"units/original/SLOTS.json")
    schedule=[dict(slots[0],slot_id=f"old/i{i}/heavy",source_index=i,input_id=x["id"],prompt_ids_sha256=x["prompt_ids_sha256"]) for i,x in enumerate(items)]
    panel=root.with_suffix(".inputs.json");put(panel,dict(inputs=items))
    schedulefile=root.with_suffix(".slots.json");put(schedulefile,schedule)
    args=[root/"raw",CFG["target"],CFG["draft"],panel,schedulefile,"Qwen",OLD/"ORIGINAL_BINDING.json",OLD/"PLAN.json"]
    run(CFG["original_worker"],args,root,("RUN\n"+"CONTINUE\n"*len(items)).encode())
    result=read(root/"raw/result.json");assert result["status"]=="COMPLETE"

def vectors(path,rec):
    files=[path/"target/initial.f32"]
    if rec["draft_enabled"]:
        for c in rec["cycles"]:
            files += [path/"target"/f"verify-{c['cycle']}-{i}.f32" for i in range(c["output_length"]-len(files))]
    else:files += [path/"target"/f"ordinary-{i}.f32" for i in range(1,len(rec["ids"]))]
    assert len(files)==len(rec["ids"])
    return list(map(sha,files))

def compare(root,items,oraclepath,legacy=False,arms=ARMS):
    report=[]
    for i,x in enumerate(items):
        old=oraclepath/(f"raw/old/i{i}/heavy" if legacy else f"i{i}/R/capture")
        ref=read(old.with_suffix(".json") if legacy else old/"receipt.json")
        baseline=vectors(old,ref)
        scalar=root/f"i{i}/S1/capture"
        s=read(scalar/"receipt.json") if scalar.is_dir() else None
        for arm in arms:
            d=root/f"i{i}/{arm}/capture"
            rec=read(d/"receipt.json")
            vec=vectors(d,rec)
            bad=[j for j in range(max(len(vec),len(baseline))) if vec[j:j+1]!=baseline[j:j+1]]
            branch=[]
            if s and rec["draft_enabled"]:
                for f in sorted((scalar/"target").glob("verify-*.f32")):
                    t=d/"target"/f.name
                    if not t.exists() or sha(f)!=sha(t):branch.append(f.name)
                branch+=sorted(p.name for p in (d/"target").glob("verify-*.f32") if not (scalar/"target"/p.name).exists())
            report.append(dict(input=x["id"],arm=arm,vectors=len(vec),endpoint=all(rec[k]==ref[k] for k in ("ids","eog","terminal_id","length","stop_reason")),different=bad,
                branch_diff=branch,cycles_equal=(rec["cycles"]==s["cycles"]) if s and rec["draft_enabled"] else None,
                committed_sha256=vec))
    put(root/"audit.json",report)
    return all(r["endpoint"] and not r["different"] and not r["branch_diff"] and r["cycles_equal"] is not False for r in report if r["arm"] in ARMS[:5])

def dev():
    root=ROOT/"devservice01";root.mkdir()
    prev=read(OLD/"PANEL.json")["inputs"]
    x=min(enumerate(prev),key=lambda pair:len(pair[1]["prompt_ids"]))
    service(root/"candidate",[x[1]],1024,ARMS,"heavy")
    old=OLD/"units/original/native/old"/f"i{x[0]}"/"heavy"
    ref=read(old.with_suffix(".json"));baseline=vectors(old,ref)
    for arm in ARMS:
        path=root/"candidate/i0"/arm/"capture"
        r=read(path/"receipt.json")
        actual=vectors(path,r)
        print(arm,len(actual),r["ids"]==ref["ids"],actual==baseline,flush=True)

if __name__=="__main__":dev()
