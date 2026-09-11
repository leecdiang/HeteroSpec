#!/usr/bin/env python3
import argparse, ctypes, gzip, hashlib, json, random, re, subprocess, time
from datetime import datetime, timezone
from pathlib import Path
from integrate_energy import integrate, load_samples

def now(): return datetime.now(timezone.utc).isoformat()
def save(value, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    tmp.replace(path)
def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""): h.update(block)
    return h.hexdigest()
def divergence(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y: return i
    return None if len(a) == len(b) else min(len(a), len(b))
def qpc():
    value = ctypes.c_longlong(); ctypes.windll.kernel32.QueryPerformanceCounter(ctypes.byref(value)); return value.value
def qpf():
    value = ctypes.c_longlong(); ctypes.windll.kernel32.QueryPerformanceFrequency(ctypes.byref(value)); return value.value
def memory_snapshot():
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = MEMORYSTATUSEX(); m.dwLength = ctypes.sizeof(m); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    snap = {"ram_used_mib": (m.ullTotalPhys-m.ullAvailPhys)/1048576, "ram_available_mib": m.ullAvailPhys/1048576,
            "commit_used_mib": (m.ullTotalPageFile-m.ullAvailPageFile)/1048576, "commit_limit_mib": m.ullTotalPageFile/1048576}
    script = "$r=(Get-Counter '\\GPU Adapter Memory(*)\\Dedicated Usage' -ErrorAction SilentlyContinue).CounterSamples|%{[pscustomobject]@{instance=$_.InstanceName;mib=$_.CookedValue/1MB}}|sort mib -Descending|select -First 1;$r|ConvertTo-Json -Compress"
    try:
        row = json.loads(subprocess.run(["powershell.exe","-NoProfile","-Command",script], capture_output=True, text=True, check=True).stdout)
        snap.update(vram_instance=row.get("instance"), vram_used_mib=row.get("mib"), vram_headroom_mib=10074-row.get("mib"))
    except Exception as e: snap["vram_snapshot_error"] = str(e)
    return snap
def utc(): return datetime.now(timezone.utc).isoformat()
def start_telemetry(a, stem):
    td = a.run_root / "telemetry"; td.mkdir(parents=True, exist_ok=True)
    csv_path, meta_path, stop_path = td/f"{stem}.csv", td/f"{stem}.metadata.json", td/f"{stem}.stop"
    out = (a.run_root/"stdout"/f"{stem}.telemetry.log").open("w", encoding="utf-8")
    err = (a.run_root/"stderr"/f"{stem}.telemetry.log").open("w", encoding="utf-8")
    start_qpc, start_utc = qpc(), utc()
    process = subprocess.Popen([str(a.collector),str(csv_path),str(meta_path),"3600","100",str(stop_path)], stdout=out, stderr=err)
    time.sleep(5)
    if process.poll() is not None: raise RuntimeError(f"Telemetry collector exited early: {process.returncode}")
    return {"process":process,"out":out,"err":err,"csv":csv_path,"meta":meta_path,"stop":stop_path,"start_qpc":start_qpc,"start_utc":start_utc}
def stop_telemetry(t):
    time.sleep(5); t["stop"].touch(); t["process"].wait(timeout=15); end_qpc, end_utc = qpc(), utc(); t["out"].close(); t["err"].close()
    if t["process"].returncode: raise RuntimeError(f"Telemetry collector failed: {t['process'].returncode}")
    return end_qpc, end_utc
def load_dataset(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return {row["task_id"]: row for row in map(json.loads, f)}
def tokenize(exe, model, text):
    p = subprocess.run([str(exe), "--model", str(model), "--stdin", "--ids", "--no-bos"], input=text,
                       text=True, encoding="utf-8", errors="replace", capture_output=True, check=True)
    return json.loads(p.stdout.strip())
def normalized_generated_tokens(exe, model, stdout, prompt, generated_count, cap=128):
    displayed_prompt = prompt.rstrip()
    first = stdout.find(displayed_prompt)
    if first < 0 or stdout.find(displayed_prompt, first + 1) >= 0:
        raise RuntimeError("Generated-output prompt boundary absent or non-unique")
    generated_text = stdout[first + len(displayed_prompt):]
    ids = tokenize(exe, model, generated_text)
    wanted = min(generated_count, cap)
    if len(ids) < wanted:
        raise RuntimeError(f"Retokenized output shorter than runtime generated count: {len(ids)} < {wanted}")
    return ids[:wanted]
def parse_metrics(stderr):
    prompts = re.findall(r"prompt eval time\s*=\s*([0-9.]+) ms /\s*(\d+) tokens", stderr)
    decodes = re.findall(r"(?<!prompt )eval time\s*=\s*([0-9.]+) ms /\s*(\d+) (?:tokens|runs)", stderr)
    acceptance = re.search(r"draft acceptance\s*=\s*([0-9.]+) \(\s*(\d+) accepted /\s*(\d+) generated\), mean len =\s*([0-9.]+)", stderr)
    simple_drafted = re.search(r"n_drafted\s*=\s*(\d+)", stderr)
    simple_accepted = re.search(r"n_accept\s*=\s*(\d+)", stderr)
    simple_rate = re.search(r"accept\s*=\s*([0-9.]+)%", stderr)
    stats = re.search(r"statistics\s+draft-simple: #calls\(b,g,a\) =\s*(\d+)\s+(\d+)\s+(\d+),.*?#gen drafts =\s*(\d+), #acc drafts =\s*(\d+), #gen tokens =\s*(\d+), #acc tokens =\s*(\d+)", stderr)
    if not prompts or not decodes: raise RuntimeError("Required llama.cpp timing fields absent")
    prompt, decode = prompts[-1], decodes[-1]
    out = {"prompt_eval_ms": float(prompt[0]), "prompt_tokens": int(prompt[1]),
           "decode_ms": float(decode[0]), "output_tokens_runtime": int(decode[1])}
    if acceptance:
        out.update(acceptance_rate=float(acceptance.group(1)), accepted_tokens=int(acceptance.group(2)),
                   drafted_tokens=int(acceptance.group(3)), mean_spec_len=float(acceptance.group(4)))
    elif simple_drafted and simple_accepted:
        drafted, accepted = int(simple_drafted.group(1)), int(simple_accepted.group(1))
        out.update(acceptance_rate=(float(simple_rate.group(1)) / 100 if simple_rate else accepted / drafted if drafted else 0),
                   accepted_tokens=accepted, drafted_tokens=drafted)
    if stats:
        out.update(verification_rounds=int(stats.group(2)), drafted_sequences=int(stats.group(4)),
                   accepted_sequences=int(stats.group(5)), stats_drafted_tokens=int(stats.group(6)),
                   stats_accepted_tokens=int(stats.group(7)))
    out["placement_evidence"] = [line for line in stderr.splitlines() if
        "offloaded " in line or "using device Vulkan0" in line or "model buffer size" in line]
    return out

def run(a, prompt, task, rep, condition, prompt_path):
    executable = a.llama_speculative if condition == "vulkan_k2" else a.llama_completion
    decode_cfg = a.cfg["runtime"]["decode"]
    n_predict = str(decode_cfg["speculative_cli_n_predict"] if condition == "vulkan_k2" else decode_cfg["baseline_cli_n_predict"])
    cmd = [str(executable), "--model", str(a.target), "--device", "Vulkan0", "--n-gpu-layers", "all",
           "--fit", "off", "--ctx-size", str(decode_cfg["n_ctx"]), "--batch-size", str(decode_cfg["n_batch"]), "--ubatch-size", str(decode_cfg["n_ubatch"]),
           "--flash-attn", "off", "--file", str(prompt_path), "--n-predict", n_predict, "--temp", "0",
           "--top-k", "0", "--top-p", "1", "--min-p", "0", "--seed", "123"]
    if condition == "baseline":
        cmd += ["--reasoning", "off", "--simple-io", "--display-prompt", "--no-warmup",
                "--log-verbosity", "4", "--perf", "--no-conversation"]
    else:
        cmd += ["--verbose"]
    if condition == "vulkan_k2":
        cmd += ["--spec-type", "draft-simple", "--spec-draft-model", str(a.draft),
                "--spec-draft-device", "Vulkan0", "--spec-draft-ngl", "all",
                "--spec-draft-n-max", "2", "--spec-draft-n-min", "0"]
    raw_stem = f"{task.replace('/', '-')}-r{rep}-{condition}"
    before = memory_snapshot(); telemetry = start_telemetry(a, raw_stem)
    workload_start_qpc, workload_start_utc = qpc(), utc()
    p = subprocess.run(cmd, text=True, encoding="utf-8", errors="replace", capture_output=True)
    workload_end_qpc, workload_end_utc = qpc(), utc()
    telemetry_end_qpc, telemetry_end_utc = stop_telemetry(telemetry); after = memory_snapshot()
    stdout_path, stderr_path = a.run_root/"stdout"/f"{raw_stem}.txt", a.run_root/"stderr"/f"{raw_stem}.txt"
    stdout_path.write_text(p.stdout, encoding="utf-8"); stderr_path.write_text(p.stderr, encoding="utf-8")
    if p.returncode: raise RuntimeError(f"{task} r{rep} {condition} failed {p.returncode}: {p.stderr[-3000:]}")
    offloads = [(int(x), int(y)) for x, y in re.findall(r"offloaded\s+(\d+)/(\d+) layers to GPU", p.stderr)]
    expected = 2 if condition == "vulkan_k2" else 1
    if len(offloads) < expected or any(x != y for x, y in offloads[-expected:]):
        raise RuntimeError(f"Full-offload gate failed: {offloads}")
    metrics = parse_metrics(p.stderr)
    if condition == "vulkan_k2":
        actual = re.search(r"n_predict\s*=\s*(\d+)", p.stderr)
        generated_count = int(actual.group(1)) if actual else decode_cfg["semantic_output_cap"]
    else:
        generated_count = metrics["output_tokens_runtime"] + 1
    tokens = normalized_generated_tokens(a.tokenize, a.target, p.stdout, prompt, generated_count, decode_cfg["semantic_output_cap"])
    energy = integrate(load_samples(telemetry["csv"]), workload_start_qpc, workload_end_qpc, qpf())
    energy["output_tokens"] = len(tokens); energy["board_energy_j_per_output_token"] = energy["board_energy_j"] / len(tokens) if tokens else None
    recorded_cmd = [Path(x).name if x in (str(a.target),str(a.draft),str(a.llama_completion),str(a.llama_speculative),str(prompt_path)) else x for x in cmd]
    return {"run_id": f"{task.replace('/', '-')}-r{rep}-{condition}", "task_id": task,
            "repetition": rep, "condition": condition, "command": recorded_cmd, "exit_code": p.returncode,
            "tokens": tokens, "output_token_count": len(tokens),
            "semantic_output_cap": decode_cfg["semantic_output_cap"], "backend_requested_n_predict": int(n_predict),
            "token_sha256": hashlib.sha256(",".join(map(str, tokens)).encode()).hexdigest(),
            "metrics": metrics, "full_offload": True, "eos": len(tokens) < decode_cfg["semantic_output_cap"],
            "workload_start_utc": workload_start_utc, "workload_end_utc": workload_end_utc,
            "workload_start_qpc": workload_start_qpc, "workload_end_qpc": workload_end_qpc, "qpc_frequency_hz": qpf(),
            "telemetry_start_utc": telemetry["start_utc"], "telemetry_end_utc": telemetry_end_utc,
            "telemetry_start_qpc": telemetry["start_qpc"], "telemetry_end_qpc": telemetry_end_qpc,
            "telemetry_file": str(telemetry["csv"].relative_to(a.run_root)), "telemetry_metadata": str(telemetry["meta"].relative_to(a.run_root)),
            "energy": energy, "memory_before": before, "memory_after": after,
            "elapsed_s": (workload_end_qpc-workload_start_qpc)/qpf(),
            "throughput_tps": len(tokens)/((workload_end_qpc-workload_start_qpc)/qpf()) if tokens else None,
            "raw_stdout": str(stdout_path.relative_to(a.run_root)), "raw_stderr": str(stderr_path.relative_to(a.run_root))}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True); ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--llama-completion", type=Path, required=True); ap.add_argument("--llama-speculative", type=Path, required=True)
    ap.add_argument("--tokenize", type=Path, required=True)
    ap.add_argument("--target", type=Path, required=True); ap.add_argument("--draft", type=Path, required=True)
    ap.add_argument("--dataset", type=Path, required=True)
    ap.add_argument("--collector", type=Path, required=True); ap.add_argument("--run-root", type=Path, required=True)
    a = ap.parse_args(); a.run_root = a.run_root.resolve()
    for directory in (a.run_root/"stdout", a.run_root/"stderr", a.run_root/"telemetry", a.run_root/"raw", a.output.parent): directory.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(a.config.read_text(encoding="utf-8")); ccfg = cfg["correctness_gate"]; a.cfg = cfg
    if sha256(a.dataset) != "b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef": raise RuntimeError("Dataset SHA256 mismatch")
    if sha256(a.target) != cfg["runtime"]["target"]["sha256"]: raise RuntimeError("Target SHA256 mismatch")
    if sha256(a.draft) != cfg["runtime"]["draft"]["sha256"]: raise RuntimeError("Draft SHA256 mismatch")
    problems = load_dataset(a.dataset); rng = random.Random(ccfg["order_seed"])
    schedule = []
    for rep in range(1, ccfg["repetitions_per_condition_per_prompt"] + 1):
        ids = ccfg["task_ids"].copy(); rng.shuffle(ids)
        for task in ids:
            conditions = ccfg["conditions"].copy(); rng.shuffle(conditions)
            schedule.append({"task_id": task, "repetition": rep, "order": conditions})
    record = {"schema": "heterospec.b570.correctness.v1", "status": "STARTED", "started": now(),
              "config": cfg, "schedule": schedule, "runs": [], "mismatches": []}
    save(record, a.output); prompt_dir = a.run_root / "raw" / "prompts"; prompt_dir.mkdir(parents=True, exist_ok=True)
    for block in schedule:
        task = block["task_id"]
        prompt = "Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n" + problems[task]["prompt"]
        prompt_path = prompt_dir / f"{task.replace('/', '_')}.txt"; prompt_path.write_text(prompt, encoding="utf-8")
        pair = []
        for condition in block["order"]:
            item = run(a, prompt, task, block["repetition"], condition, prompt_path)
            pair.append(item); record["runs"].append(item); save(record, a.output)
            print(f"{item['run_id']} tokens={item['output_token_count']}", flush=True)
        baseline = next(x for x in pair if x["condition"] == "baseline")
        spec = next(x for x in pair if x["condition"] == "vulkan_k2")
        idx = divergence(baseline["tokens"], spec["tokens"]); spec["exact_match"] = idx is None
        spec["first_divergence_index"] = idx
        spec["baseline_token_at_divergence"] = baseline["tokens"][idx] if idx is not None and idx < len(baseline["tokens"]) else None
        spec["speculative_token_at_divergence"] = spec["tokens"][idx] if idx is not None and idx < len(spec["tokens"]) else None
        baseline["exact_match"] = True
        if idx is not None: record["mismatches"].append({"task_id": task, "repetition": block["repetition"], "index": idx,
            "baseline_token": spec["baseline_token_at_divergence"], "speculative_token": spec["speculative_token_at_divergence"]})
        save(record, a.output)
    record["status"] = "PASS" if not record["mismatches"] else "FAIL"
    record["ended"] = now(); save(record, a.output)
    print(json.dumps({"status": record["status"], "runs": len(record["runs"]), "mismatches": len(record["mismatches"])}))
    return 0 if record["status"] == "PASS" else 3
if __name__ == "__main__": raise SystemExit(main())
