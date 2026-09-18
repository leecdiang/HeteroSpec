#!/usr/bin/env python3
"""Frozen 18-pair token-exact verification-control gate for 358H Vulkan0."""
from __future__ import annotations
import argparse, gzip, hashlib, json, random, re, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
ADDENDUM=ROOT/"benchmarks/358h_threshold_validation/protocol_addendum_v1.json"
CLI=ROOT/"tools/llama-b10839/llama-cli.exe"
TOKENIZE=ROOT/"tools/llama-b10839/llama-tokenize.exe"
TARGET=ROOT/"models/gguf/Qwen3-8B-Q8_0.gguf"
DRAFT=ROOT/"models/gguf/Qwen3-0.6B-Q8_0.gguf"
DATASET=ROOT/"datasets/humaneval/HumanEval.jsonl.gz"

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""): h.update(b)
    return h.hexdigest()
def tokenize(text):
    p=subprocess.run([str(TOKENIZE),"--model",str(TARGET),"--stdin","--ids","--no-bos"],input=text,
                     capture_output=True,text=True,encoding="utf-8",errors="replace",check=True)
    return json.loads(p.stdout.strip())
def execute(prompt_path, condition, out, stem):
    cmd=[str(CLI),"--model",str(TARGET),"--device","Vulkan0","--n-gpu-layers","99","--fit","off",
         "--ctx-size","16384","--batch-size","512","--ubatch-size","1","--flash-attn","off",
         "--file",str(prompt_path),"--n-predict","128","--temp","0","--top-k","0","--top-p","1",
         "--min-p","0","--seed","123","--ignore-eos","--reasoning","off","--simple-io",
         "--no-display-prompt","--no-warmup","--perf"]
    if condition=="speculative":
        cmd += ["--spec-type","draft-simple","--spec-draft-model",str(DRAFT),"--spec-draft-device","Vulkan0",
                "--spec-draft-ngl","99","--spec-draft-n-max","2","--spec-draft-n-min","0"]
    p=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="replace")
    (out/f"{stem}.stdout.txt").write_text(p.stdout,encoding="utf-8")
    (out/f"{stem}.stderr.txt").write_text(p.stderr,encoding="utf-8")
    if p.returncode: raise RuntimeError(f"{stem} failed: {p.stderr[-3000:]}")
    off=[tuple(map(int,x)) for x in re.findall(r"offloaded\s+(\d+)/(\d+) layers to GPU",p.stderr)]
    required=2 if condition=="speculative" else 1
    if len(off)<required or any(a!=b for a,b in off[-required:]): raise RuntimeError(f"full-offload failed: {off}")
    ids=tokenize(p.stdout)[:128]
    return {"condition":condition,"token_ids":ids,"token_ids_sha256":hashlib.sha256(json.dumps(ids).encode()).hexdigest(),
            "output_tokens":len(ids),"requested_device":"Vulkan0","full_offload":True,
            "stdout":f"{stem}.stdout.txt","stderr":f"{stem}.stderr.txt"}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--check",action="store_true"); ap.add_argument("--execute-formal",action="store_true"); a=ap.parse_args()
    cfg=json.loads(ADDENDUM.read_text(encoding="utf-8-sig")); gate=cfg["v2"]["exactness_gate"]
    checks={"addendum_frozen":cfg.get("status")=="FROZEN","target":sha256(TARGET)==cfg["target_gpu"]["model_sha256"],
            "draft":sha256(DRAFT)==cfg["canonical_draft_gguf_sha256"],"dataset":sha256(DATASET)==gate["dataset_sha256"],
            "cli":sha256(CLI)==cfg["target_gpu"]["llama_cli_sha256"],"tokenize":sha256(TOKENIZE)==cfg["target_gpu"]["llama_tokenize_sha256"]}
    if a.check: print(json.dumps({"ready":all(checks.values()),"checks":checks},indent=2)); return 0 if all(checks.values()) else 2
    if not a.execute_formal: ap.error("use --execute-formal")
    if not all(checks.values()): raise RuntimeError(checks)
    with gzip.open(DATASET,"rt",encoding="utf-8") as f: problems={r["task_id"]:r for r in map(json.loads,f)}
    run_id="358h-exactness-"+datetime.now().strftime("%Y%m%dT%H%M%S"); out=ROOT/"runs/358h/phase2"/run_id
    (out/"prompts").mkdir(parents=True,exist_ok=False)
    schedule=[]; rng=random.Random(gate["order_seed"])
    for rep in range(1,gate["repetitions_per_task"]+1):
        tasks=list(gate["task_ids"]); rng.shuffle(tasks)
        for task in tasks:
            order=["baseline","speculative"]; rng.shuffle(order); schedule.append((task,rep,order))
    record={"schema":"heterospec.358h.exactness_gate.v1","formal":True,"started":datetime.now(timezone.utc).isoformat(),
            "schedule":[{"task_id":t,"repetition":r,"order":o} for t,r,o in schedule],"pairs":[]}
    for task,rep,order in schedule:
        prompt="Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n"+problems[task]["prompt"]
        pp=out/"prompts"/f"{task.replace('/','_')}.txt"; pp.write_text(prompt,encoding="utf-8")
        rows={c:execute(pp,c,out,f"{task.replace('/','-')}-r{rep}-{c}") for c in order}
        exact=rows["baseline"]["token_ids"]==rows["speculative"]["token_ids"]
        record["pairs"].append({"task_id":task,"repetition":rep,"exact":exact,"runs":rows})
        (out/"result.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    record["exact_pairs"]=sum(p["exact"] for p in record["pairs"]); record["total_pairs"]=len(record["pairs"])
    record["status"]="PASS" if record["exact_pairs"]==18 and record["total_pairs"]==18 else "FAIL"
    record["ended"]=datetime.now(timezone.utc).isoformat(); (out/"result.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"run_id":run_id,"status":record["status"],"exact_pairs":record["exact_pairs"]},indent=2)); return 0 if record["status"]=="PASS" else 3
if __name__=="__main__": raise SystemExit(main())

