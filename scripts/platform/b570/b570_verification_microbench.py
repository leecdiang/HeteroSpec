#!/usr/bin/env python3
import argparse, json, statistics, subprocess
from datetime import datetime, timezone
from pathlib import Path

def summarize(samples):
    mean = statistics.mean(samples); std = statistics.stdev(samples)
    return {"samples_ns": samples, "median_ns": statistics.median(samples), "mean_ns": mean,
            "std_ns": std, "cv": std / mean}
def save(value, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp"); tmp.write_text(json.dumps(value, indent=2), encoding="utf-8"); tmp.replace(path)
def run(exe, model, depth, batch, ubatch, repetitions):
    cmd = [str(exe), "-m", str(model), "-dev", "Vulkan0", "-ngl", "all", "-fitt", "off", "-fa", "off",
           "-p", "1,2", "-n", "0", "-d", str(depth), "-b", str(batch), "-ub", str(ubatch),
           "-r", str(repetitions), "-o", "json"]
    p = subprocess.run(cmd, text=True, encoding="utf-8", errors="replace", capture_output=True)
    if p.returncode: raise RuntimeError(f"llama-bench failed {p.returncode}: {p.stderr[-3000:]}")
    values = json.loads(p.stdout); by_pp = {int(v["n_prompt"]): summarize(v["samples_ns"]) for v in values}
    if set(by_pp) != {1, 2}: raise RuntimeError(f"Unexpected PP cells: {set(by_pp)}")
    return {"pp1": by_pp[1], "pp2": by_pp[2], "v2_ratio_of_medians": by_pp[2]["median_ns"] / by_pp[1]["median_ns"],
            "command": cmd, "stderr_tail": p.stderr[-4000:]}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--exe", type=Path, required=True); ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True); a = ap.parse_args()
    cfg = json.loads(a.config.read_text(encoding="utf-8")); vcfg = cfg["verification"]
    result = {"schema": "heterospec.b570.verification.v1", "status": "STARTED",
              "started": datetime.now(timezone.utc).isoformat(), "definition": vcfg["operation"],
              "config": cfg, "depths": {}}; save(result, a.output)
    for depth in vcfg["contexts"]:
        result["depths"][str(depth)] = {}
        for name, ubatch in vcfg["paths"].items():
            result["depths"][str(depth)][name] = run(a.exe, a.model, depth, vcfg["batch"], ubatch, vcfg["repetitions_per_cell"])
            save(result, a.output); print(f"depth={depth} path={name} V2={result['depths'][str(depth)][name]['v2_ratio_of_medians']:.6f}", flush=True)
    result["status"] = "PASS"; result["ended"] = datetime.now(timezone.utc).isoformat(); save(result, a.output)
if __name__ == "__main__": main()
