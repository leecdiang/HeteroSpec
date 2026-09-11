#!/usr/bin/env python3
import argparse, ctypes, json, statistics, subprocess, time
from datetime import datetime, timezone
from pathlib import Path
from integrate_energy import integrate, load_samples

def qpc():
    value=ctypes.c_longlong(); ctypes.windll.kernel32.QueryPerformanceCounter(ctypes.byref(value)); return value.value
def qpf():
    value=ctypes.c_longlong(); ctypes.windll.kernel32.QueryPerformanceFrequency(ctypes.byref(value)); return value.value

def summarize(samples):
    mean = statistics.mean(samples); std = statistics.stdev(samples)
    return {"samples_ns": samples, "median_ns": statistics.median(samples), "mean_ns": mean,
            "std_ns": std, "cv": std / mean}
def save(value, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp"); tmp.write_text(json.dumps(value, indent=2), encoding="utf-8"); tmp.replace(path)
def run(a, depth, batch, ubatch, repetitions, path_name):
    exe, model = a.exe, a.model
    cmd = [str(exe), "-m", str(model), "-dev", "Vulkan0", "-ngl", "all", "-fitt", "off", "-fa", "off",
           "-p", "1,2", "-n", "0", "-d", str(depth), "-b", str(batch), "-ub", str(ubatch),
           "-r", str(repetitions), "-o", "json"]
    stem=f"v2-n{depth}-{path_name}"; td=a.run_root/"telemetry"; td.mkdir(parents=True, exist_ok=True)
    csv_path,meta_path,stop_path=td/f"{stem}.csv",td/f"{stem}.metadata.json",td/f"{stem}.stop"
    tout=(a.run_root/"stdout"/f"{stem}.telemetry.log").open("w",encoding="utf-8"); terr=(a.run_root/"stderr"/f"{stem}.telemetry.log").open("w",encoding="utf-8")
    telemetry_start_qpc=qpc(); telemetry_start_utc=datetime.now(timezone.utc).isoformat()
    tp=subprocess.Popen([str(a.collector),str(csv_path),str(meta_path),"3600","100",str(stop_path)],stdout=tout,stderr=terr)
    time.sleep(5)
    if tp.poll() is not None: raise RuntimeError(f"Telemetry collector exited early: {tp.returncode}")
    workload_start_qpc=qpc(); workload_start_utc=datetime.now(timezone.utc).isoformat()
    p = subprocess.run(cmd, text=True, encoding="utf-8", errors="replace", capture_output=True)
    workload_end_qpc=qpc(); workload_end_utc=datetime.now(timezone.utc).isoformat()
    time.sleep(5); stop_path.touch(); tp.wait(timeout=15); telemetry_end_qpc=qpc(); telemetry_end_utc=datetime.now(timezone.utc).isoformat(); tout.close(); terr.close()
    (a.run_root/"stdout"/f"{stem}.txt").write_text(p.stdout,encoding="utf-8"); (a.run_root/"stderr"/f"{stem}.txt").write_text(p.stderr,encoding="utf-8")
    if tp.returncode: raise RuntimeError(f"Telemetry collector failed: {tp.returncode}")
    if p.returncode: raise RuntimeError(f"llama-bench failed {p.returncode}: {p.stderr[-3000:]}")
    values = json.loads(p.stdout); by_pp = {int(v["n_prompt"]): summarize(v["samples_ns"]) for v in values}
    if set(by_pp) != {1, 2}: raise RuntimeError(f"Unexpected PP cells: {set(by_pp)}")
    energy=integrate(load_samples(csv_path),workload_start_qpc,workload_end_qpc,qpf())
    recorded_cmd=[Path(x).name if x in (str(exe),str(model)) else x for x in cmd]
    return {"pp1": by_pp[1], "pp2": by_pp[2], "v2_ratio_of_medians": by_pp[2]["median_ns"] / by_pp[1]["median_ns"],
            "command": recorded_cmd, "stderr_tail": p.stderr[-4000:], "workload_start_qpc":workload_start_qpc,"workload_end_qpc":workload_end_qpc,
            "workload_start_utc":workload_start_utc,"workload_end_utc":workload_end_utc,"qpc_frequency_hz":qpf(),
            "telemetry_start_qpc":telemetry_start_qpc,"telemetry_end_qpc":telemetry_end_qpc,
            "telemetry_start_utc":telemetry_start_utc,"telemetry_end_utc":telemetry_end_utc,
            "telemetry_file":str(csv_path.relative_to(a.run_root)),"telemetry_metadata":str(meta_path.relative_to(a.run_root)),"process_board_energy_diagnostic":energy}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--exe", type=Path, required=True); ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True); ap.add_argument("--collector",type=Path,required=True); ap.add_argument("--run-root",type=Path,required=True); a = ap.parse_args()
    a.run_root=a.run_root.resolve(); (a.run_root/"stdout").mkdir(parents=True,exist_ok=True); (a.run_root/"stderr").mkdir(parents=True,exist_ok=True)
    cfg = json.loads(a.config.read_text(encoding="utf-8")); vcfg = cfg["verification"]
    result = {"schema": "heterospec.b570.verification.v1", "status": "STARTED",
              "started": datetime.now(timezone.utc).isoformat(), "definition": vcfg["definition"],
              "config": cfg, "depths": {}}; save(result, a.output)
    for depth in vcfg["contexts"]:
        result["depths"][str(depth)] = {}
        for name, ubatch in vcfg["paths"].items():
            result["depths"][str(depth)][name] = run(a, depth, vcfg["batch"], ubatch, vcfg["repetitions_per_cell"], name)
            save(result, a.output); print(f"depth={depth} path={name} V2={result['depths'][str(depth)][name]['v2_ratio_of_medians']:.6f}", flush=True)
    result["status"] = "PASS"; result["ended"] = datetime.now(timezone.utc).isoformat(); save(result, a.output)
if __name__ == "__main__": main()
