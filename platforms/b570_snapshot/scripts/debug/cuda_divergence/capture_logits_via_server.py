#!/usr/bin/env python3
"""Isolated post-hoc logprob capture using the frozen llama.cpp server binary."""
import argparse, gzip, json, math, subprocess, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def load_prompt(dataset, prereg):
    with gzip.open(dataset, "rt", encoding="utf-8") as f:
        row = next(json.loads(x) for x in f if json.loads(x)["task_id"] == "HumanEval/106")
    p = json.loads(prereg.read_text(encoding="utf-8"))
    return p["fixed_runtime"]["prompt_template"].replace("{humaneval_prompt}", row["prompt"])

def request_json(url, payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=300) as r: return json.loads(r.read())

def wait_ready(port, proc):
    for _ in range(300):
        if proc.poll() is not None: raise RuntimeError(f"server exited {proc.returncode}")
        try:
            if request_json(f"http://127.0.0.1:{port}/health").get("status") == "ok": return
        except Exception: pass
        time.sleep(.2)
    raise TimeoutError("server readiness timeout")

def normalize_probs(item):
    # llama.cpp /completion returns candidates under probs[].tok_str/prob.
    candidates = item.get("probs", item.get("top_logprobs", []))
    out=[]
    for c in candidates:
        token = c.get("id", c.get("tok", c.get("token_id")))
        lp = c.get("logprob")
        prob = c.get("prob", c.get("probability"))
        out.append({"token_id":token,"token_text":c.get("token",c.get("tok_str",c.get("token_str",""))),"probability":prob if prob is not None else (math.exp(lp) if lp is not None else None),"log_probability":lp if lp is not None else (math.log(prob) if prob and prob>0 else None)})
    return out

def run_path(args, prompt, name, ubatch, speculative, run_id, port):
    cmd=[str(args.server),"--model",str(args.target),"--device","CUDA0","--n-gpu-layers","all","--fit","off","--ctx-size","4096","--flash-attn","off","--ubatch-size",str(ubatch),"--host","127.0.0.1","--port",str(port),"--parallel","1","--no-warmup","--cache-ram","0","--log-verbosity","3"]
    if speculative:
        cmd += ["--spec-type","draft-simple","--model-draft",str(args.draft),"--spec-draft-device","none","--spec-draft-ngl","0","--spec-draft-n-max","2","--spec-draft-n-min","0"]
    log=args.raw_dir/f"{run_id}-{name}-server.log"; log.parent.mkdir(parents=True,exist_ok=True)
    with log.open("w",encoding="utf-8") as lf:
        proc=subprocess.Popen(cmd,stdout=lf,stderr=subprocess.STDOUT,text=True,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        try:
            wait_ready(port,proc)
            payload={"messages":[{"role":"user","content":prompt}],"max_tokens":128,"temperature":0,"top_p":1,"seed":123,"logprobs":True,"top_logprobs":10,"stream":False,"chat_template_kwargs":{"enable_thinking":False}}
            res=request_json(f"http://127.0.0.1:{port}/v1/chat/completions",payload)
        finally:
            proc.terminate()
            try: proc.wait(10)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait()
    choice=res["choices"][0]; probs=choice.get("logprobs",{}).get("content",[])
    return {"path":name,"ubatch":ubatch,"speculative":speculative,"run_id":run_id,"command":cmd,"content":choice["message"]["content"],"tokens":[x.get("id",x.get("token_id",x.get("token"))) for x in probs],"positions":[{"index":i,"sampled_token_id":x.get("id",x.get("token_id",x.get("token"))),"top":normalize_probs(x),"raw":x} for i,x in enumerate(probs)],"response_keys":list(res),"raw_log":str(log.relative_to(ROOT))}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--runs",type=int,default=3)
    ap.add_argument("--server",type=Path,default=ROOT/"tools/llama-debug-build7/bin/llama-server.exe");ap.add_argument("--target",type=Path,default=ROOT/"models/gguf/Qwen3-8B-Q8_0.gguf");ap.add_argument("--draft",type=Path,default=ROOT/"models/gguf/Qwen3-0.6B-Q8_0.gguf")
    ap.add_argument("--dataset",type=Path,default=ROOT/"datasets/humaneval/HumanEval.jsonl.gz");ap.add_argument("--prereg",type=Path,default=ROOT/"benchmarks/m4_code_conditioned_30q/preregistration.json");ap.add_argument("--output",type=Path,default=ROOT/"logs/cuda-divergence-logits-server.json");ap.add_argument("--raw-dir",type=Path,default=ROOT/"logs/cuda-divergence-server")
    a=ap.parse_args(); prompt=load_prompt(a.dataset,a.prereg); out={"schema":"heterospec.cuda_divergence_logits.server.v1","formal_runtime_commit":"0cae43063","debug_instrumentation_commit":"0cae43063 plus server-context-logprobs.patch","build":"Zig 0.16.0, Release, static host, GGML_BACKEND_DL=ON; frozen official b10839 CUDA backend DLLs","instrumentation":"server response-only capture of target-context top-10 pre-sampling probabilities for accepted speculative tokens","prompt_id":"HumanEval/106","runs":[]}
    for r in range(1,a.runs+1):
        for i,(name,ub,spec) in enumerate((("baseline",1,False),("batched_ub2",2,True),("serialized_ub1",1,True))):
            print(f"run {r} {name}",flush=True); out["runs"].append(run_path(a,prompt,name,ub,spec,r,8100+i))
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"runs":len(out["runs"]),"token_counts":[len(x["tokens"]) for x in out["runs"]],"response_keys":[x["response_keys"] for x in out["runs"][:3]]},indent=2))
if __name__=="__main__": main()
