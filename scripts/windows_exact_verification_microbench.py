#!/usr/bin/env python3
"""Measure target pp2/pp1 cost with batched and exact-serialized CUDA paths."""
import argparse, json, statistics, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(exe, model, ubatch, repetitions, depth):
    cmd = [str(exe), "-m", str(model), "-dev", "CUDA0", "-ngl", "99", "-fa", "off",
           "-p", "1,2", "-n", "0", "-d", str(depth), "-b", "512", "-ub", str(ubatch), "-r", str(repetitions), "-o", "json"]
    p = subprocess.run(cmd, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    values = json.loads(p.stdout)
    out = {}
    for v in values:
        samples = v["samples_ns"]
        out[f"pp{v['n_prompt']}"] = {"samples_ns": samples, "median_ns": statistics.median(samples)}
    out["ratio_pp2_over_pp1"] = out["pp2"]["median_ns"] / out["pp1"]["median_ns"]
    out["command"] = cmd
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repetitions",type=int,default=20)
    ap.add_argument("--exe",type=Path,default=ROOT/"tools/llama-b10839/llama-bench.exe")
    ap.add_argument("--model",type=Path,default=ROOT/"models/gguf/Qwen3-8B-Q8_0.gguf")
    ap.add_argument("--output",type=Path,default=ROOT/"logs/windows-exact-verification-microbench.json")
    a=ap.parse_args(); result={"schema":"heterospec.windows_exact_verification_cost.v1","definition":"median PP2 wall time / median PP1 wall time; same target, CUDA, Q8_0, FA off, llama-bench; PP2 is a verification-kernel proxy","depths":{}}
    for depth in (0,256):
        result["depths"][str(depth)]={"batched_ubatch2":run(a.exe,a.model,2,a.repetitions,depth),"serialized_ubatch1":run(a.exe,a.model,1,a.repetitions,depth)}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))
if __name__=="__main__": main()
