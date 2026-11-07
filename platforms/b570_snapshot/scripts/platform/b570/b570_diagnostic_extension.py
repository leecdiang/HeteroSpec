#!/usr/bin/env python3
"""Execute the frozen post-gate B570 diagnostic extension."""
import argparse, copy, gzip, hashlib, json, os, random, threading
from datetime import datetime, timezone
from pathlib import Path

import b570_correctness_gate as cg
import b570_verification_microbench as vb

def utc(): return datetime.now(timezone.utc).isoformat()
def save(value, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8"); tmp.replace(path)
def update(a, **fields):
    with a.status_lock:
        try: s=json.loads(a.status.read_text(encoding="utf-8-sig"))
        except Exception: s={}
        s.update(fields); s.update(schema="heterospec.b570.diagnostic-task.v1",run_id=a.run_root.name,
                                   worker_pid=os.getpid(),heartbeat_at=utc())
        save(s,a.status); (a.status.parent/"DIAGNOSTIC_STATUS.txt").write_text("\n".join(f"{k}={v}" for k,v in s.items())+"\n",encoding="utf-8")
def heartbeat(a):
    while not a.stop.wait(20): update(a)
def shared_prefix_hash(tokens, index):
    payload=",".join(map(str,tokens[:index])).encode(); return hashlib.sha256(payload).hexdigest()
def load_dataset(path):
    with gzip.open(path,"rt",encoding="utf-8") as f: return {x["task_id"]:x for x in map(json.loads,f)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--diagnostic-config",type=Path,required=True); p.add_argument("--base-config",type=Path,required=True)
    p.add_argument("--run-root",type=Path,required=True); p.add_argument("--status",type=Path,required=True)
    p.add_argument("--llama-completion",type=Path,required=True); p.add_argument("--llama-speculative",type=Path,required=True)
    p.add_argument("--tokenize",type=Path,required=True); p.add_argument("--bench",type=Path,required=True)
    p.add_argument("--target",type=Path,required=True); p.add_argument("--draft",type=Path,required=True)
    p.add_argument("--dataset",type=Path,required=True); p.add_argument("--collector",type=Path,required=True)
    a=p.parse_args(); a.run_root=a.run_root.resolve(); a.status=a.status.resolve(); a.status_lock=threading.Lock(); a.stop=threading.Event()
    for d in ("raw","processed","telemetry","stdout","stderr"): (a.run_root/d).mkdir(parents=True,exist_ok=True)
    threading.Thread(target=heartbeat,args=(a,),daemon=True).start()
    diag=json.loads(a.diagnostic_config.read_text(encoding="utf-8")); base=json.loads(a.base_config.read_text(encoding="utf-8"))
    if cg.sha256(a.target)!=diag["platform"]["target"]["sha256"] or cg.sha256(a.draft)!=diag["platform"]["draft"]["sha256"]: raise RuntimeError("Frozen model hash mismatch")
    if cg.sha256(a.dataset)!="b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef": raise RuntimeError("Dataset hash mismatch")

    # Stage A: failing fast path is intentionally labeled raw, never exact.
    vout={"schema":"heterospec.b570.v2_raw.v1","status":"STARTED","started":utc(),"definition":diag["stage_a_v2_raw"]["definition"],"cells":{}}
    vroot=a.run_root/"v2raw"; [ (vroot/d).mkdir(parents=True,exist_ok=True) for d in ("stdout","stderr","telemetry") ]
    va=argparse.Namespace(exe=a.bench,model=a.target,collector=a.collector,run_root=vroot)
    for depth in diag["stage_a_v2_raw"]["contexts"]:
        update(a,state="RUNNING",stage="V2_raw",current_context=depth,completed_cells=len(vout["cells"]),total_cells=2)
        try:
            cell=vb.run(va,depth,diag["stage_a_v2_raw"]["batch"],diag["stage_a_v2_raw"]["path"]["ubatch"],diag["stage_a_v2_raw"]["repetitions_per_cell"],"raw_fast_ubatch2")
            cell["scientific_label"]="V2_raw; DIAGNOSTIC; not V2_exact; not end-to-end speedup"
            cell["microbench_energy_reliability"]="NOT RELIABLE FOR PER-OPERATION ENERGY; telemetry covers combined PP1/PP2 process"
            vout["cells"][str(depth)]=cell
        except Exception as e:
            if depth==2048: vout["cells"][str(depth)]={"status":"NOT_RUN_CAPACITY","error":str(e)}
            else: raise
        save(vout,a.run_root/"processed/v2_raw.json")
    vout["status"]="PASS"; vout["ended"]=utc(); save(vout,a.run_root/"processed/v2_raw.json")

    # Stage B: exact M4/Windows selection and pre-frozen deterministic schedule.
    tasks=diag["stage_b_humaneval30"]["task_ids"]; problems=load_dataset(a.dataset); rng=random.Random(diag["stage_b_humaneval30"]["schedule_seed"])
    schedule=[]
    for rep in range(1,4):
        ids=tasks.copy(); rng.shuffle(ids)
        for task in ids:
            order=["baseline","vulkan_k2"]; rng.shuffle(order); schedule.append({"task_id":task,"repetition":rep,"order":order})
    hout={"schema":"heterospec.b570.humaneval30_diagnostic.v1","status":"STARTED","started":utc(),"schedule":schedule,"runs":[],"pairs":[],"mismatches":[],"scientific_label":"DIAGNOSTIC EXTENSION; fast path remains correctness-blocked"}
    save(hout,a.run_root/"processed/humaneval30_diagnostic.json"); hroot=a.run_root/"humaneval30"; prompt_dir=hroot/"raw/prompts"; prompt_dir.mkdir(parents=True,exist_ok=True)
    for d in ("stdout","stderr","telemetry"): (hroot/d).mkdir(parents=True,exist_ok=True)
    ca=argparse.Namespace(llama_completion=a.llama_completion,llama_speculative=a.llama_speculative,tokenize=a.tokenize,target=a.target,draft=a.draft,dataset=a.dataset,collector=a.collector,run_root=hroot,cfg=base)
    for block in schedule:
        task=block["task_id"]; prompt="Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n"+problems[task]["prompt"]
        prompt_path=prompt_dir/f"{task.replace('/','_')}.txt"; prompt_path.write_text(prompt,encoding="utf-8")
        pair=[]
        for condition in block["order"]:
            update(a,state="RUNNING",stage="HumanEval30",current_prompt=task,repetition=block["repetition"],condition=condition,completed_workloads=len(hout["runs"]),total_workloads=180)
            item=cg.run(ca,prompt,task,block["repetition"],condition,prompt_path); pair.append(item); hout["runs"].append(item); save(hout,a.run_root/"processed/humaneval30_diagnostic.json")
        baseline=next(x for x in pair if x["condition"]=="baseline"); spec=next(x for x in pair if x["condition"]=="vulkan_k2")
        idx=cg.divergence(baseline["tokens"],spec["tokens"]); cls="EXACT_ADMISSIBLE" if idx is None else "MISMATCH_DIAGNOSTIC"
        summary={"task_id":task,"repetition":block["repetition"],"classification":cls,"exact":idx is None,"first_divergence_index":idx,"shared_prefix_length":idx,
                 "baseline_token":baseline["tokens"][idx] if idx is not None and idx<len(baseline["tokens"]) else None,
                 "speculative_token":spec["tokens"][idx] if idx is not None and idx<len(spec["tokens"]) else None,
                 "shared_prefix_sha256":shared_prefix_hash(baseline["tokens"],idx) if idx is not None else None,
                 "baseline_run_id":baseline["run_id"],"speculative_run_id":spec["run_id"],
                 "raw_speedup":baseline["elapsed_s"]/spec["elapsed_s"],"acceptance":spec["metrics"].get("acceptance_rate"),
                 "runtime_commit":diag["platform"]["runtime_commit"],"target_sha256":diag["platform"]["target"]["sha256"],"draft_sha256":diag["platform"]["draft"]["sha256"],"backend_device":diag["platform"]["device"]}
        hout["pairs"].append(summary)
        if idx is not None: hout["mismatches"].append(summary)
        save(hout,a.run_root/"processed/humaneval30_diagnostic.json")
    hout["status"]="PASS"; hout["ended"]=utc(); save(hout,a.run_root/"processed/humaneval30_diagnostic.json")

    # One preregistered fallback only; no fallback HumanEval30.
    fout={"schema":"heterospec.b570.serialized_fallback.v1","status":"STARTED","started":utc(),"candidate":diag["single_fallback_candidate"],"runs":[],"pairs":[],"mismatches":[]}
    fallback=copy.deepcopy(base); fallback["runtime"]["decode"]["n_ubatch"]=1
    froot=a.run_root/"fallback"; (froot/"raw/prompts").mkdir(parents=True,exist_ok=True)
    for d in ("stdout","stderr","telemetry"): (froot/d).mkdir(parents=True,exist_ok=True)
    gate=diag["single_fallback_candidate"]["initial_scope"]["task_ids"]
    frng=random.Random(diag["stage_b_humaneval30"]["schedule_seed"]+1)
    for rep in range(1,4):
        ids=gate.copy(); frng.shuffle(ids)
        for task in ids:
            order=["baseline","vulkan_k2"]; frng.shuffle(order); prompt="Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n"+problems[task]["prompt"]
            prompt_path=froot/"raw/prompts"/f"{task.replace('/','_')}.txt"; prompt_path.write_text(prompt,encoding="utf-8"); pair=[]
            for condition in order:
                ca.cfg=base if condition=="baseline" else fallback; ca.run_root=froot
                update(a,state="RUNNING",stage="fallback_gate",current_prompt=task,repetition=rep,condition=condition,completed_workloads=len(fout["runs"]),total_workloads=36)
                item=cg.run(ca,prompt,task,rep,condition,prompt_path); item["fallback_candidate"]="serialized_n_ubatch_1" if condition=="vulkan_k2" else "paired_frozen_baseline"; pair.append(item); fout["runs"].append(item)
            b=next(x for x in pair if x["condition"]=="baseline"); s=next(x for x in pair if x["condition"]=="vulkan_k2"); idx=cg.divergence(b["tokens"],s["tokens"])
            ps={"task_id":task,"repetition":rep,"exact":idx is None,"classification":"EXACT_ADMISSIBLE" if idx is None else "MISMATCH_DIAGNOSTIC","first_divergence_index":idx}
            fout["pairs"].append(ps)
            if idx is not None: fout["mismatches"].append(ps)
            save(fout,a.run_root/"processed/fallback.json")
    if fout["mismatches"]:
        fout["status"]="FAIL_STOP_BRANCH"; fout["v2_exact"]="NOT_RUN_BY_STOP_RULE"
    else:
        fout["status"]="PASS"; fout["v2_exact"]={}
        fvroot=a.run_root/"fallback_v2"; [ (fvroot/d).mkdir(parents=True,exist_ok=True) for d in ("stdout","stderr","telemetry") ]
        fva=argparse.Namespace(exe=a.bench,model=a.target,collector=a.collector,run_root=fvroot)
        for depth in (512,2048):
            update(a,state="RUNNING",stage="fallback_V2_exact",current_context=depth)
            try: fout["v2_exact"][str(depth)]=vb.run(fva,depth,512,1,20,"fallback_exact_ubatch1")
            except Exception as e:
                if depth==2048: fout["v2_exact"][str(depth)]={"status":"NOT_RUN_CAPACITY","error":str(e)}
                else: raise
    fout["ended"]=utc(); save(fout,a.run_root/"processed/fallback.json")
    a.stop.set(); update(a,state="MEASUREMENTS_COMPLETE",stage="finalization",detail="All authorized diagnostic workloads finished")

if __name__=="__main__": main()
