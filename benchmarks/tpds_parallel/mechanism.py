"""Mechanism probes. Preserve raw logits and append-only native attempt directories."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from build import OUT

def put(path,obj):
    with path.open("x") as f: json.dump(obj,f,indent=2)

def run(exe,model,manifest,out):
    out.mkdir(parents=True)
    put(out/"input.json",manifest)
    lock=Path("D:/HeteroSpec-PC/RTX_EXPERIMENT.lock")
    if shutil.disk_usage(out).free<8*1024**3: raise RuntimeError("disk admission")
    with lock.open("x") as f: json.dump({"pid":os.getpid(),"work":str(out)},f)
    started=time.monotonic()
    try:
        env={k:v for k,v in os.environ.items() if not k.startswith(("HS_","HSC_","GGML_","JSA_"))}
        env["HS_TPDS_TRACE"]="1"
        with (out/"native.log").open("xb") as f:
            r=subprocess.run([exe,model,out/"input.json",out],stdout=f,stderr=subprocess.STDOUT,timeout=1800,env=env)
        put(out/"exit.json",{"code":r.returncode,"elapsed":time.monotonic()-started})
        return r.returncode
    finally:
        lock.unlink()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("label");ap.add_argument("--model",default="0.6B")
    ap.add_argument("--bases",default="0");ap.add_argument("--widths",default="2,4,8,16,32")
    ap.add_argument("--ctx",type=int,default=1024)
    a=ap.parse_args()
    root=OUT.parent/"probes"/a.label
    root.mkdir(parents=True,exist_ok=False)
    model=Path("D:/HeteroSpec-PC/models/gguf")/f"Qwen3-{a.model}-Q8_0.gguf"
    results=[]
    for base in map(int,a.bases.split(",")):
        for width in map(int,a.widths.split(",")):
            ids=[113+(i*173)%2309 for i in range(base+width)]
            for arm in ("oracle","S1","PQ-ext","QB-local","WB-cut","native"):
                cell=root/f"{base}-{width}-{arm}"
                conf={"id":"row","arm":"S1" if arm=="oracle" else arm,"width":width,"base":base,"ctx":a.ctx,"tokens":ids}
                exe=(OUT.parent/"oracle01" if arm=="oracle" else OUT/"bin")/"probe.exe"
                rc=run(exe,model,{"layers":24 if a.model=="14B" else 999,"units":[conf]},cell)
                ref=root/f"{base}-{width}-oracle"/"row"
                mismatch=None
                if rc==0:
                    mismatch=[r for r in range(width) if digest(ref/f"{r}.f32")!=digest(cell/"row"/f"{r}.f32")]
                row=dict(base=base,width=width,arm=arm,exit=rc,mismatch=mismatch)
                results.append(row)
                print(row,flush=True)
    put(root/"comparison.json",results)

if __name__=="__main__":main()
