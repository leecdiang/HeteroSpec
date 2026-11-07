#!/usr/bin/env python3
"""Execute the frozen B570 exact-fallback validation."""
import argparse, copy, gzip, hashlib, json, os, random, threading
from datetime import datetime, timezone
from pathlib import Path

import b570_correctness_gate as cg
import b570_verification_microbench as vb

def utc(): return datetime.now(timezone.utc).isoformat()
def save(value, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
def update(a, **fields):
    with a.status_lock:
        try: state=json.loads(a.status.read_text(encoding="utf-8-sig"))
        except Exception: state={}
        state.update(fields)
        state.update(schema="heterospec.b570.exact-fallback-task.v1", run_id=a.run_root.name,
                     worker_pid=os.getpid(), heartbeat_at=utc())
        save(state, a.status)
        (a.status.parent/"EXACT_FALLBACK_STATUS.txt").write_text(
            "\n".join(f"{k}={v}" for k,v in state.items())+"\n", encoding="utf-8")
def heartbeat(a):
    while not a.stop.wait(20): update(a)
def load_dataset(path):
    with gzip.open(path,"rt",encoding="utf-8") as f: return {x["task_id"]:x for x in map(json.loads,f)}
def prefix_hash(tokens, index): return hashlib.sha256(",".join(map(str,tokens[:index])).encode()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--config",type=Path,required=True); p.add_argument("--base-config",type=Path,required=True)
    p.add_argument("--run-root",type=Path,required=True); p.add_argument("--status",type=Path,required=True)
    p.add_argument("--llama-completion",type=Path,required=True); p.add_argument("--llama-speculative",type=Path,required=True)
    p.add_argument("--tokenize",type=Path,required=True); p.add_argument("--bench",type=Path,required=True)
    p.add_argument("--target",type=Path,required=True); p.add_argument("--draft",type=Path,required=True)
    p.add_argument("--dataset",type=Path,required=True); p.add_argument("--collector",type=Path,required=True)
    a=p.parse_args(); a.run_root=a.run_root.resolve(); a.status=a.status.resolve()
    a.status_lock=threading.Lock(); a.stop=threading.Event()
    for d in ("processed","telemetry","stdout","stderr"): (a.run_root/d).mkdir(parents=True,exist_ok=True)
    threading.Thread(target=heartbeat,args=(a,),daemon=True).start()
    cfg=json.loads(a.config.read_text(encoding="utf-8")); base=json.loads(a.base_config.read_text(encoding="utf-8"))
    if cg.sha256(a.target)!=cfg["platform"]["target"]["sha256"]: raise RuntimeError("Frozen target hash mismatch")
    if cg.sha256(a.draft)!=cfg["platform"]["draft"]["sha256"]: raise RuntimeError("Frozen draft hash mismatch")
    if cg.sha256(a.dataset)!=cfg["stage_b_humaneval30"]["dataset_sha256"]: raise RuntimeError("Frozen dataset hash mismatch")

    # Stage A: clean serialized-path verification mechanism cells.
    v={"schema":"heterospec.b570.v2_exact.serialized.v1","status":"STARTED","started":utc(),
       "definition":cfg["stage_a_v2_exact"]["definition"],"cells":{}}
    vroot=a.run_root/"v2_exact"
    for d in ("stdout","stderr","telemetry"): (vroot/d).mkdir(parents=True,exist_ok=True)
    va=argparse.Namespace(exe=a.bench,model=a.target,collector=a.collector,run_root=vroot)
    for depth in cfg["stage_a_v2_exact"]["contexts"]:
        update(a,state="RUNNING",stage="V2_exact",current_context=depth,completed_cells=len(v["cells"]),total_cells=2)
        v["cells"][str(depth)]=vb.run(va,depth,cfg["stage_a_v2_exact"]["batch"],
                                      cfg["stage_a_v2_exact"]["ubatch"],
                                      cfg["stage_a_v2_exact"]["repetitions_per_cell"],"serialized_exact_ubatch1")
        v["cells"][str(depth)]["scientific_label"]="V2_exact serialized-path mechanism proxy; not end-to-end speedup"
        save(v,a.run_root/"processed/v2_exact.json")
    v["status"]="PASS"; v["ended"]=utc(); save(v,a.run_root/"processed/v2_exact.json")

    # Stage B: the full frozen selection runs regardless of Stage A result.
    tasks=cfg["stage_b_humaneval30"]["task_ids"]; problems=load_dataset(a.dataset)
    rng=random.Random(cfg["stage_b_humaneval30"]["schedule_seed"]); schedule=[]
    for rep in range(1,4):
        ids=tasks.copy(); rng.shuffle(ids)
        for task in ids:
            order=["baseline","vulkan_k2"]; rng.shuffle(order)
            schedule.append({"task_id":task,"repetition":rep,"order":order})
    out={"schema":"heterospec.b570.exact_fallback_humaneval30.v1","status":"STARTED","started":utc(),
         "schedule":schedule,"runs":[],"pairs":[],"mismatches":[]}
    save(out,a.run_root/"processed/humaneval30_exact_fallback.json")
    hroot=a.run_root/"humaneval30"; prompt_dir=hroot/"raw/prompts"; prompt_dir.mkdir(parents=True,exist_ok=True)
    for d in ("stdout","stderr","telemetry"): (hroot/d).mkdir(parents=True,exist_ok=True)
    fallback=copy.deepcopy(base); fallback["runtime"]["decode"]["n_ubatch"]=1
    ca=argparse.Namespace(llama_completion=a.llama_completion,llama_speculative=a.llama_speculative,
        tokenize=a.tokenize,target=a.target,draft=a.draft,dataset=a.dataset,collector=a.collector,run_root=hroot,cfg=base)
    for block in schedule:
        task=block["task_id"]; rep=block["repetition"]
        prompt="Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n"+problems[task]["prompt"]
        prompt_path=prompt_dir/f"{task.replace('/','_')}.txt"; prompt_path.write_text(prompt,encoding="utf-8")
        pair=[]
        for condition in block["order"]:
            ca.cfg=base if condition=="baseline" else fallback
            update(a,state="RUNNING",stage="HumanEval30_exact_fallback",current_prompt=task,repetition=rep,
                   condition=condition,completed_workloads=len(out["runs"]),total_workloads=180)
            item=cg.run(ca,prompt,task,rep,condition,prompt_path)
            item["candidate"]="serialized_n_ubatch_1" if condition=="vulkan_k2" else "frozen_baseline"
            pair.append(item); out["runs"].append(item); save(out,a.run_root/"processed/humaneval30_exact_fallback.json")
        b=next(x for x in pair if x["condition"]=="baseline"); s=next(x for x in pair if x["condition"]!="baseline")
        idx=cg.divergence(b["tokens"],s["tokens"])
        ps={"task_id":task,"repetition":rep,"exact":idx is None,
            "classification":"EXACT_ADMISSIBLE" if idx is None else "MISMATCH",
            "first_divergence_index":idx,
            "baseline_token":b["tokens"][idx] if idx is not None and idx<len(b["tokens"]) else None,
            "speculative_token":s["tokens"][idx] if idx is not None and idx<len(s["tokens"]) else None,
            "shared_prefix_sha256":prefix_hash(b["tokens"],idx) if idx is not None else None,
            "baseline_run_id":b["run_id"],"speculative_run_id":s["run_id"],
            "speedup":b["elapsed_s"]/s["elapsed_s"],
            "board_energy_ratio":b["energy"]["board_energy_j_per_output_token"]/s["energy"]["board_energy_j_per_output_token"],
            "acceptance":s["metrics"].get("acceptance_rate")}
        out["pairs"].append(ps)
        if idx is not None: out["mismatches"].append(ps)
        save(out,a.run_root/"processed/humaneval30_exact_fallback.json")
    out["status"]="PASS" if not out["mismatches"] else "CORRECTNESS_FAIL"
    out["ended"]=utc(); save(out,a.run_root/"processed/humaneval30_exact_fallback.json")
    a.stop.set(); update(a,state="MEASUREMENTS_COMPLETE",stage="finalization",detail="All frozen exact-fallback workloads finished")

if __name__=="__main__": main()
