#!/usr/bin/env python3
import argparse, gzip, hashlib, json, random, re, subprocess
from datetime import datetime, timezone
from pathlib import Path

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
    p = subprocess.run(cmd, text=True, encoding="utf-8", errors="replace", capture_output=True)
    raw_dir = a.output.parent / "raw"; raw_dir.mkdir(parents=True, exist_ok=True)
    raw_stem = f"{task.replace('/', '-')}-r{rep}-{condition}"
    (raw_dir / f"{raw_stem}.stdout.txt").write_text(p.stdout, encoding="utf-8")
    (raw_dir / f"{raw_stem}.stderr.txt").write_text(p.stderr, encoding="utf-8")
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
    return {"run_id": f"{task.replace('/', '-')}-r{rep}-{condition}", "task_id": task,
            "repetition": rep, "condition": condition, "command": cmd, "exit_code": p.returncode,
            "tokens": tokens, "output_token_count": len(tokens),
            "semantic_output_cap": decode_cfg["semantic_output_cap"], "backend_requested_n_predict": int(n_predict),
            "token_sha256": hashlib.sha256(",".join(map(str, tokens)).encode()).hexdigest(),
            "metrics": metrics, "full_offload": True}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True); ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--llama-completion", type=Path, required=True); ap.add_argument("--llama-speculative", type=Path, required=True)
    ap.add_argument("--tokenize", type=Path, required=True)
    ap.add_argument("--target", type=Path, required=True); ap.add_argument("--draft", type=Path, required=True)
    ap.add_argument("--dataset", type=Path, required=True); a = ap.parse_args()
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
    save(record, a.output); prompt_dir = a.output.parent / "prompts"; prompt_dir.mkdir(parents=True, exist_ok=True)
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
