#!/usr/bin/env python3
"""Frozen same-platform 358H target T_b and exact-path V_2 runner."""
from __future__ import annotations

import argparse, hashlib, json, os, random, re, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[3]
ADDENDUM = ROOT / "benchmarks/358h_threshold_validation/protocol_addendum_v1.json"
BENCH = ROOT / "tools/llama-b10839/llama-bench.exe"
TARGET = ROOT / "models/gguf/Qwen3-8B-Q8_0.gguf"

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""): h.update(b)
    return h.hexdigest()

def run_one(context, prompts, reps, output_dir, label):
    cmd=[str(BENCH),"-m",str(TARGET),"-dev","Vulkan0","-ngl","99","-fa","off",
         "-p",prompts,"-n","0","-d",str(context),"-b","512","-ub","1","-r",str(reps),"-o","json","-v"]
    p=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="replace")
    stamp=f"{label}-c{context}-{int(time.time()*1000)}"
    (output_dir/f"{stamp}.stdout.json").write_text(p.stdout,encoding="utf-8")
    (output_dir/f"{stamp}.stderr.txt").write_text(p.stderr,encoding="utf-8")
    if p.returncode: raise RuntimeError(f"llama-bench failed: {p.stderr[-2000:]}")
    rows=json.loads(p.stdout)
    if not rows or any(r.get("devices")!="Vulkan0" for r in rows): raise RuntimeError("explicit Vulkan0 evidence missing")
    offloads=[tuple(map(int,x)) for x in re.findall(r"offloaded\s+(\d+)/(\d+) layers to GPU",p.stderr)]
    if not offloads or any(a!=b for a,b in offloads): raise RuntimeError(f"full-offload gate failed: {offloads}")
    return {"command":cmd,"rows":rows,"placement":{"requested":"Vulkan0","json_devices":[r["devices"] for r in rows],
            "full_offload":True,"offload_records":offloads},"raw_stdout":f"{stamp}.stdout.json","raw_stderr":f"{stamp}.stderr.txt"}

def warm(context, prompts, policy, out, label):
    values=[]
    for i in range(1,policy["maximum"]+1):
        row=run_one(context,prompts,1,out,f"warmup-{label}-{i}")
        value=float(row["rows"][-1]["avg_ns"])
        values.append(value)
        if i>=policy["minimum"] and abs(values[-1]-values[-2])/((values[-1]+values[-2])/2)<=policy["stability_fraction"]:
            return values
    raise RuntimeError(f"warm-up stability failed for {label} context {context}")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--check",action="store_true")
    ap.add_argument("--execute-formal",choices=["tb","v2"]); ap.add_argument("--exactness-result",type=Path)
    a=ap.parse_args()
    try:
        cfg=json.loads(ADDENDUM.read_text(encoding="utf-8-sig"))
        if cfg.get("status")!="FROZEN": raise RuntimeError("addendum not frozen")
        if sha256(TARGET)!=cfg["target_gpu"]["model_sha256"]: raise RuntimeError("target hash mismatch")
        if sha256(BENCH)!=cfg["target_gpu"]["llama_bench_sha256"]: raise RuntimeError("llama-bench hash mismatch")
        battery=psutil.sensors_battery()
        if battery is None or battery.power_plugged is not True: raise RuntimeError("AC power not online")
        if (os.environ.get("SESSIONNAME") or "").upper().startswith("RDP"): raise RuntimeError("RDP forbidden")
    except Exception as e:
        print(json.dumps({"ready":False,"reason":str(e)},indent=2)); return 2
    if a.check: print(json.dumps({"ready":True},indent=2)); return 0
    if not a.execute_formal: ap.error("use --execute-formal tb|v2")
    design=cfg[a.execute_formal]
    if a.execute_formal=="v2":
        if not a.exactness_result: raise RuntimeError("V2 requires --exactness-result")
        exact=json.loads(a.exactness_result.read_text(encoding="utf-8-sig"))
        if exact.get("status")!="PASS" or exact.get("exact_pairs")!=18: raise RuntimeError("18/18 exactness gate not PASS")
    run_id=f"358h-{a.execute_formal}-{datetime.now().strftime('%Y%m%dT%H%M%S')}"
    out=ROOT/"runs/358h/phase2"/run_id; out.mkdir(parents=True,exist_ok=False)
    record={"schema":f"heterospec.358h.{a.execute_formal}.v1","formal":True,"run_id":run_id,
            "started":datetime.now(timezone.utc).isoformat(),"cells":[]}
    prompts="1" if a.execute_formal=="tb" else "1,2"
    for context in design["context_order"]:
        ws=warm(context,prompts,design["warmup"],out,a.execute_formal)
        formal=run_one(context,prompts,design["repetitions_per_context"],out,"formal")
        record["cells"].append({"context_tokens":context,"warmup_avg_ns":ws,"formal":formal})
    record["ended"]=datetime.now(timezone.utc).isoformat(); record["status"]="COMPLETE"
    (out/"session.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"run_id":run_id,"status":"COMPLETE"},indent=2)); return 0

if __name__=="__main__": raise SystemExit(main())

