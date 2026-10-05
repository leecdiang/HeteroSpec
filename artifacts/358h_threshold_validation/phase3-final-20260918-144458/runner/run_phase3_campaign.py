#!/usr/bin/env python3
"""Frozen Phase-3 campaign driver for the 358H heterogeneous runner.

This driver changes no inference semantics.  It supplies the preregistered
HumanEval schedule, persistence, post-prefill timing boundary, and paired
target-only observations around the already-qualified runner components.
"""
from __future__ import annotations

import argparse, ctypes as C, gzip, hashlib, json, os, platform, random, sys, time
from datetime import datetime, timezone
from pathlib import Path

import openvino as ov
import openvino_genai as ov_genai

from phase3_heterogeneous_runner import (
    EXPECTED, DRAFT_IR, LlamaAPI, LlamaTarget, NPU_BINDING,
    OpenVINODraftReplay, TARGET, sha,
)

ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "datasets/humaneval/HumanEval.jsonl.gz"
DATASET_SHA = "b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef"
RUNNER = ROOT / "scripts/platform/358h/phase3_heterogeneous_runner.py"
RUNNER_SHA = "1d11e42d008f981ee6a91ac7bfeb478f11c060d51e79b9e060fe04ece70153e8"
FREEZE_COMMIT = "18072058fa28f06c5e0a8c80549990b7c48b207a"
SMALL = [3, 10, 19, 20, 106, 129]
FULL = [3,10,19,20,28,32,44,47,48,50,54,57,62,64,68,70,89,90,101,104,105,106,107,111,119,123,126,128,129,162]
WARMUP = 0
CONDITIONS = ["TARGET_BASELINE", "CPU_DRAFT_K2", "NPU_DRAFT_K2"]
CPU_AFFINITY = list(range(12))
ALL_AFFINITY = list(range(os.cpu_count() or 16))

def utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_json(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)

def load_tasks() -> dict[int, dict]:
    if sha(DATASET) != DATASET_SHA:
        raise RuntimeError("HumanEval dataset hash mismatch")
    out = {}
    with gzip.open(DATASET, "rt", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line); out[int(row["task_id"].split("/")[-1])] = row
    return out

def prompt_for(row: dict) -> str:
    return "Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n" + row["prompt"]

def formatted_prompt(prompt: str) -> str:
    return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"

def detokenize(api: LlamaAPI, vocab, tokens: list[int]) -> str:
    fn = api.ll.llama_token_to_piece
    fn.argtypes = [C.c_void_p, C.c_int32, C.c_char_p, C.c_int32, C.c_int32, C.c_bool]
    fn.restype = C.c_int32
    pieces = []
    for token in tokens:
        cap = 256; buf = C.create_string_buffer(cap)
        n = fn(vocab, int(token), buf, cap, 0, True)
        if n < 0:
            cap = -n; buf = C.create_string_buffer(cap); n = fn(vocab, int(token), buf, cap, 0, True)
        if n > 0: pieces.append(buf.raw[:n])
    return b"".join(pieces).decode("utf-8", errors="replace")

def divergence(a: list[int], b: list[int]):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y: return {"index": i, "baseline_token": x, "speculative_token": y}
    if len(a) != len(b):
        i = min(len(a), len(b)); return {"index": i, "baseline_token": a[i] if i < len(a) else None, "speculative_token": b[i] if i < len(b) else None}
    return None

def set_affinity(condition: str) -> list[int]:
    chosen = CPU_AFFINITY if condition == "CPU_DRAFT_K2" else ALL_AFFINITY
    try: os.sched_setaffinity(0, chosen)
    except AttributeError:
        import psutil; psutil.Process().cpu_affinity(chosen)
    return chosen

def baseline(tgt: LlamaTarget, pt: list[int], n: int) -> dict:
    tgt.reset_prefill(pt)
    s = time.perf_counter_ns(); tokens = tgt.baseline(n); e = time.perf_counter_ns()
    return {"tokens": tokens, "end_to_end_ns": e-s, "rounds": [], "draft_replay_proposal_ns": 0,
            "target_verification_ns": e-s, "orchestration_residual_ns": 0, "proposed": 0, "accepted": 0}

def speculative(tgt: LlamaTarget, draft: OpenVINODraftReplay, pt: list[int], n: int) -> dict:
    tgt.reset_prefill(pt); out=[]; rounds=[]; draft_ns=target_ns=0
    start=time.perf_counter_ns()
    ts=time.perf_counter_ns(); first=tgt.verify([]); te=time.perf_counter_ns(); target_ns += te-ts
    out.extend(first[:n]); rounds.append({"round_id":0,"prefix_before":len(pt),"proposals":[],"target_committed":first[:n],
        "accepted":0,"correction":first[0],"bonus":None,"C":len(first[:n]),"draft_replay_proposal_ns":0,
        "target_verification_ns":te-ts,"native_initial_target_only":True})
    while len(out)<n:
        before=len(pt)+len(out); remaining=n-len(out); width=min(2,max(0,remaining-1)); props=[]; dt=0
        if width: props,dt=draft.propose(pt+out,width); draft_ns+=dt
        ts=time.perf_counter_ns(); committed=tgt.verify(props); te=time.perf_counter_ns(); vt=te-ts; target_ns+=vt
        committed=committed[:remaining]; out.extend(committed); accepted=max(0,len(committed)-1) if props else 0
        rounds.append({"round_id":len(rounds),"prefix_before":before,"proposals":props,"target_committed":committed,
            "accepted":accepted,"correction":committed[-1] if accepted<len(props) else None,
            "bonus":committed[-1] if accepted==len(props) and props else None,"C":len(committed),
            "draft_replay_proposal_ns":dt,"target_verification_ns":vt,"native_initial_target_only":False})
    end=time.perf_counter_ns()
    return {"tokens":out,"end_to_end_ns":end-start,"rounds":rounds,"draft_replay_proposal_ns":draft_ns,
            "target_verification_ns":target_ns,"orchestration_residual_ns":max(0,end-start-draft_ns-target_ns),
            "proposed":sum(len(r["proposals"]) for r in rounds),"accepted":sum(r["accepted"] for r in rounds)}

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--stage",choices=["dry","small","full"],required=True)
    ap.add_argument("--output-dir",type=Path,required=True); ap.add_argument("--tokens",type=int,default=128)
    ap.add_argument("--devices",nargs="+",choices=["CPU","NPU"],default=["CPU","NPU"])
    a=ap.parse_args(); formal=a.stage in ("small","full")
    if formal and a.tokens != 128: raise RuntimeError("formal output cap must be 128")
    if sha(RUNNER)!=RUNNER_SHA: raise RuntimeError("frozen runner hash mismatch")
    for p,h in EXPECTED.items():
        if sha(p)!=h: raise RuntimeError(f"hash mismatch: {p}")
    tasks=load_tasks(); ids=[WARMUP] if a.stage=="dry" else (SMALL if a.stage=="small" else FULL)
    seed=20260912 if a.stage=="small" else 20260909
    a.output_dir.mkdir(parents=True,exist_ok=False)
    schedule=[]
    for task_id in ids:
        reps=range(1) if a.stage=="dry" else range(3)
        for rep in reps:
            cs=["TARGET_BASELINE"]+[f"{d}_DRAFT_K2" for d in a.devices]; random.Random(seed+task_id*1009+rep).shuffle(cs)
            schedule.append({"task_id":task_id,"repetition":rep,"conditions":cs})
    write_json(a.output_dir/"schedule.json",schedule)
    status={"schema":"heterospec.358h.phase3.formal_status.v1","stage":a.stage,"formal":formal,
        "formal_data_started":False,"created_at_utc":utc(),"repo_head":FREEZE_COMMIT,"runner_sha256":RUNNER_SHA,
        "driver_sha256":sha(Path(__file__)),"dataset_sha256":DATASET_SHA,"model_hashes":{str(p.relative_to(ROOT)):h for p,h in EXPECTED.items()},
        "openvino":ov.get_version(),"openvino_genai":getattr(ov_genai,"__version__","unknown"),"python":sys.version,
        "platform":platform.platform(),"devices":a.devices,"completed_observations":0,"complete":False}
    write_json(a.output_dir/"FORMAL_PHASE3_STATUS.json",status)
    api=LlamaAPI(); tgt=LlamaTarget(api,TARGET,"Vulkan0",4096)
    drafts={d:OpenVINODraftReplay(d) for d in a.devices}
    session={"requested_target_device":"Vulkan0","target_binding":"37/37 model layers and 36/36 KV layers on Vulkan0; stderr is authoritative session log",
        "available_openvino_devices":ov.Core().available_devices,"draft_execution_devices":{d:drafts[d].execution_devices for d in a.devices},
        "timing_note":"draft_replay_proposal_ns is one indivisible synchronous LLMPipeline full-prefix replay plus proposal call; proposal-only and replay-only are unavailable without changing inference.",
        "energy":"NOT_CLAIMED / NPU NOT_ADMISSIBLE"}
    write_json(a.output_dir/"session.json",session)
    # Mandatory non-formal warm-up, outside both frozen formal task sets.
    warm_pt=tgt.tokenize(formatted_prompt(prompt_for(tasks[WARMUP])),True)
    warm=[]
    for cond in ["TARGET_BASELINE"]+[f"{d}_DRAFT_K2" for d in a.devices]:
        set_affinity(cond); r=baseline(tgt,warm_pt,min(8,a.tokens)) if cond=="TARGET_BASELINE" else speculative(tgt,drafts[cond.split('_')[0]],warm_pt,min(8,a.tokens))
        warm.append({"condition":cond,"tokens":r["tokens"],"claim_status":"NON_FORMAL / INVALID_FOR_CLAIMS"})
    write_json(a.output_dir/"warmup.json",warm)
    if formal:
        status["formal_data_started"]=True; status["formal_data_started_at_utc"]=utc(); status["driver_sha256_at_start"]=sha(Path(__file__)); write_json(a.output_dir/"FORMAL_PHASE3_STATUS.json",status)
    records=[]; baselines={}
    raw=a.output_dir/"observations.jsonl"
    for unit in schedule:
        task_id=unit["task_id"]; rep=unit["repetition"]; prompt=prompt_for(tasks[task_id]); pt=tgt.tokenize(formatted_prompt(prompt),True)
        for cond in unit["conditions"]:
            affinity=set_affinity(cond); started=utc()
            r=baseline(tgt,pt,a.tokens) if cond=="TARGET_BASELINE" else speculative(tgt,drafts[cond.split('_')[0]],pt,a.tokens)
            rec={"schema":"heterospec.358h.phase3.observation.v1","formal":formal,"stage":a.stage,"task_id":f"HumanEval/{task_id}","repetition":rep,
                "condition":cond,"started_at_utc":started,"ended_at_utc":utc(),"prompt":prompt,"prompt_token_count":len(pt),
                "generated_token_ids":r["tokens"],"generated_text":detokenize(api,tgt.vocab,r["tokens"]),"output_token_count":len(r["tokens"]),
                "timing":{"end_to_end_ns":r["end_to_end_ns"],"draft_replay_proposal_ns":r["draft_replay_proposal_ns"],
                    "target_verification_ns":r["target_verification_ns"],"orchestration_residual_ns":r["orchestration_residual_ns"]},
                "rounds":r["rounds"],"proposed":r["proposed"],"accepted":r["accepted"],"process_affinity":affinity,
                "requested_target_device":"Vulkan0","target_full_offload_evidence":"37/37 model; 36/36 KV; see session stderr",
                "requested_draft_device":None if cond=="TARGET_BASELINE" else cond.split('_')[0],
                "draft_execution_devices":None if cond=="TARGET_BASELINE" else drafts[cond.split('_')[0]].execution_devices,"errors":[],"warnings":[]}
            key=(task_id,rep)
            if cond=="TARGET_BASELINE": baselines[key]=r["tokens"]
            else:
                if key not in baselines:
                    # The preregistered randomized order permits the shared baseline to occur later.
                    rec["exact_vs_baseline"]=None; rec["first_divergence"]=None
                else:
                    rec["exact_vs_baseline"]=r["tokens"]==baselines[key]; rec["first_divergence"]=divergence(baselines[key],r["tokens"])
            records.append(rec)
            with raw.open("a",encoding="utf-8",newline="\n") as f: f.write(json.dumps(rec,ensure_ascii=False,separators=(",",":"))+"\n"); f.flush(); os.fsync(f.fileno())
            status["completed_observations"]+=1; status["last_observation"]={"task_id":task_id,"repetition":rep,"condition":cond}; write_json(a.output_dir/"FORMAL_PHASE3_STATUS.json",status)
    # Resolve comparisons whose randomized baseline appeared after the speculative condition.
    for rec in records:
        if rec["condition"]!="TARGET_BASELINE":
            base=baselines[(int(rec["task_id"].split("/")[-1]),rec["repetition"])]
            rec["exact_vs_baseline"]=rec["generated_token_ids"]==base; rec["first_divergence"]=divergence(base,rec["generated_token_ids"])
    write_json(a.output_dir/"observations.resolved.json",records)
    status["complete"]=True; status["completed_at_utc"]=utc(); status["exact_counts"]={d:{"exact":sum(1 for r in records if r["condition"]==f"{d}_DRAFT_K2" and r["exact_vs_baseline"]),"total":sum(1 for r in records if r["condition"]==f"{d}_DRAFT_K2")} for d in a.devices}; write_json(a.output_dir/"FORMAL_PHASE3_STATUS.json",status)
    print(json.dumps(status["exact_counts"],indent=2)); return 0 if all(v["exact"]==v["total"] for v in status["exact_counts"].values()) else 2

if __name__=="__main__": raise SystemExit(main())
