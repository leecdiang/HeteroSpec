#!/usr/bin/env python3
"""Counterbalanced 12Q llama.cpp Metal performance/energy decision experiment."""

import argparse
import csv
import hashlib
import json
import random
import re
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from m4_mlx_smoke import first_divergence, memory_gate, memory_snapshot


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SELECTION = ROOT / "benchmarks/root_cause_12q/selection.json"
DEFAULT_DATASET = ROOT / "datasets/Spec-Bench/data/spec_bench/question.jsonl"


def now():
    return datetime.now(timezone.utc).isoformat()


def save(record, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(record, indent=2), encoding="utf-8")
    temporary.replace(output)


def tokenize(model, text):
    result = subprocess.run(
        ["llama-tokenize", "--model", str(model), "--stdin", "--ids"],
        input=text, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return json.loads(result.stdout.strip())


def log_seconds(line):
    match = re.match(r"(\d+)\.(\d{2})\.(\d{3})\.(\d{3})", line)
    if not match:
        return None
    minutes, seconds, millis, micros = map(int, match.groups())
    return minutes * 60 + seconds + millis / 1000 + micros / 1_000_000


def parse_cli(stdout, stderr, prompt):
    if "\n> " not in stdout or "\n\n[ Prompt:" not in stdout:
        raise RuntimeError("Could not isolate completion from llama-cli output")
    prompt_echo_and_completion = stdout.rsplit("\n> ", 1)[1]
    if "\n" not in prompt_echo_and_completion:
        raise RuntimeError("llama-cli prompt echo has no completion boundary")
    completion = prompt_echo_and_completion.split("\n", 1)[1].rsplit("\n\n[ Prompt:", 1)[0]
    prompt_perf = re.search(r"prompt eval time\s*=\s*([0-9.]+) ms /\s*(\d+) tokens", stderr)
    eval_perf = re.search(r"\|\s+eval time\s*=\s*([0-9.]+) ms /\s*(\d+) tokens", stderr)
    acceptance = re.search(
        r"draft acceptance\s*=\s*([0-9.]+) \(\s*(\d+) accepted /\s*(\d+) generated\), mean len =\s*([0-9.]+)",
        stderr,
    )
    spec_stats = re.search(
        r"statistics\s+draft-simple: #calls\(b,g,a\) =\s*(\d+)\s+(\d+)\s+(\d+),.*?"
        r"#gen drafts =\s*(\d+), #acc drafts =\s*(\d+), #gen tokens =\s*(\d+), #acc tokens =\s*(\d+)",
        stderr,
    )
    spec_durations = re.search(
        r"statistics\s+draft-simple:.*?dur\(b,g,a\) =\s*([0-9.]+),\s*([0-9.]+),\s*([0-9.]+) ms",
        stderr,
    )
    launch_s = None
    end_s = None
    for line in stderr.splitlines():
        if launch_s is None and "launching slot" in line and '"id":0' in line:
            launch_s = log_seconds(line)
        if "slot print_timing" in line and "total time" in line:
            end_s = log_seconds(line)
    if not prompt_perf or not eval_perf or launch_s is None or end_s is None:
        raise RuntimeError("Required llama.cpp timing fields were not found")
    result = {
        "completion_text": completion,
        "prompt_eval_ms": float(prompt_perf.group(1)),
        "prompt_tokens": int(prompt_perf.group(2)),
        "decode_ms": float(eval_perf.group(1)),
        "output_tokens_runtime": int(eval_perf.group(2)),
        "ttft_ms_proxy": float(prompt_perf.group(1)),
        "decode_window_relative_s": [launch_s, end_s],
    }
    if acceptance:
        result["acceptance_rate"] = float(acceptance.group(1))
        result["accepted_tokens"] = int(acceptance.group(2))
        result["drafted_tokens"] = int(acceptance.group(3))
        result["accepted_per_round"] = float(acceptance.group(4)) - 1.0
    if spec_stats:
        result["spec_calls"] = {
            "batch": int(spec_stats.group(1)), "generate": int(spec_stats.group(2)),
            "accept": int(spec_stats.group(3)), "draft_sequences": int(spec_stats.group(4)),
            "accepted_sequences": int(spec_stats.group(5)), "drafted_tokens": int(spec_stats.group(6)),
            "accepted_tokens": int(spec_stats.group(7)),
        }
        result["verification_rounds"] = int(spec_stats.group(2))
    if spec_durations:
        result["spec_impl_duration_ms"] = {
            "batch": float(spec_durations.group(1)),
            "draft_generate": float(spec_durations.group(2)),
            "accept": float(spec_durations.group(3)),
        }
    return result


def peak_rss_sampler(process, result):
    peak_kib = 0
    while process.poll() is None:
        sample = subprocess.run(
            ["ps", "-o", "rss=", "-p", str(process.pid)], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        ).stdout.strip()
        if sample:
            peak_kib = max(peak_kib, int(sample))
        time.sleep(0.05)
    result.append(peak_kib / 1024)


def run_cli(target, draft, prompt_path, max_tokens, condition, extra_args=None):
    command = [
        "llama-cli", "--model", str(target), "--device", "MTL0", "--n-gpu-layers", "all",
        "--file", str(prompt_path), "--n-predict", str(max_tokens), "--temp", "0",
        "--top-k", "0", "--top-p", "1", "--min-p", "0", "--seed", "123",
        "--single-turn", "--simple-io", "--no-display-prompt", "--no-warmup",
        "--chat-template-kwargs", '{"enable_thinking":false}', "--log-verbosity", "5",
    ]
    if condition != "baseline":
        k = int(condition[1:])
        command += [
            "--spec-type", "draft-simple", "--model-draft", str(draft),
            "--spec-draft-device", "MTL0", "--spec-draft-ngl", "all",
            "--spec-draft-n-max", str(k), "--spec-draft-n-min", "0",
        ]
    if extra_args:
        command += list(extra_args)
    before = memory_snapshot()
    wall_start_ns = time.time_ns()
    started = time.perf_counter()
    process = subprocess.Popen(
        command, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    peaks = []
    sampler = threading.Thread(target=peak_rss_sampler, args=(process, peaks), daemon=True)
    sampler.start()
    stdout, stderr = process.communicate()
    sampler.join()
    wall_end_ns = time.time_ns()
    if process.returncode:
        raise RuntimeError(f"llama-cli failed ({process.returncode}): {stderr[-2000:]}")
    parsed = parse_cli(stdout, stderr, prompt_path.read_text(encoding="utf-8"))
    parsed.update({
        "wall_start_unix_ns": wall_start_ns,
        "wall_end_unix_ns": wall_end_ns,
        "process_ms": (time.perf_counter() - started) * 1000,
        "peak_rss_mib": peaks[0] if peaks else None,
        "memory_before": before,
        "memory_after": memory_snapshot(),
    })
    parsed["memory_gate"] = memory_gate(parsed["memory_before"], parsed["memory_after"], parsed["process_ms"] / 1000)
    parsed["decode_start_unix_ns"] = wall_start_ns + int(parsed["decode_window_relative_s"][0] * 1e9)
    parsed["decode_end_unix_ns"] = wall_start_ns + int(parsed["decode_window_relative_s"][1] * 1e9)
    return parsed


def start_telemetry(probe, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    stream = output.open("w", encoding="utf-8")
    process = subprocess.Popen([str(probe), "250", "100000"], stdout=stream, stderr=subprocess.PIPE, text=True)
    time.sleep(1.0)
    if process.poll() is not None:
        raise RuntimeError(f"Silemetry failed to start: {process.stderr.read()}")
    return process, stream


def stop_telemetry(process, stream):
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    stream.close()


def integrate_energy(csv_path, start_ns, end_ns):
    with csv_path.open(newline="", encoding="utf-8") as stream:
        samples = [row for row in csv.DictReader(stream) if start_ns <= int(row["wall_clock_unix_ns"]) <= end_ns]
    if len(samples) < 2:
        return {"samples": len(samples), "status": "INSUFFICIENT"}
    domains = ["cpu_power_w", "gpu_power_w", "ane_power_w", "dram_power_w", "package_power_w"]
    energy = {name.replace("_power_w", "_energy_j"): 0.0 for name in domains}
    for left, right in zip(samples, samples[1:]):
        dt = (int(right["wall_clock_unix_ns"]) - int(left["wall_clock_unix_ns"])) / 1e9
        for name in domains:
            energy[name.replace("_power_w", "_energy_j")] += (float(left[name]) + float(right[name])) * 0.5 * dt
    return {"samples": len(samples), "status": "PASS", **energy}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--telemetry-probe", type=Path, default=ROOT / "work/m4/silemetry_csv_probe")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--telemetry-output", type=Path, required=True)
    parser.add_argument("--max-tokens", type=int, default=64)
    args = parser.parse_args()

    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    ids = selection["question_ids"]
    if len(ids) != 12:
        raise RuntimeError(f"Expected 12 frozen questions, got {len(ids)}")
    wanted = set(ids)
    questions = {row["question_id"]: row for row in map(json.loads, args.dataset.read_text().splitlines()) if row["question_id"] in wanted}
    if questions.keys() != wanted:
        raise RuntimeError(f"Missing questions: {sorted(wanted - questions.keys())}")

    seed = selection["seed"]
    rng = random.Random(seed)
    conditions = ["baseline", "k2", "k4", "k6"]
    orders = {}
    for question_id in ids:
        order = conditions.copy()
        rng.shuffle(order)
        orders[str(question_id)] = order
    record = {
        "schema": "heterospec.m4_llama_metal_12q.v1", "started": now(), "status": "STARTED",
        "target": str(args.target), "draft": str(args.draft), "selection": selection,
        "order_seed": seed, "condition_orders": orders, "temperature": 0, "max_tokens": args.max_tokens,
        "memory_before": memory_snapshot(), "runs": [], "telemetry_csv": str(args.telemetry_output),
    }
    save(record, args.output)
    telemetry, stream = start_telemetry(args.telemetry_probe, args.telemetry_output)
    try:
        total = len(ids) * len(conditions)
        completed = 0
        for question_id in ids:
            prompt = questions[question_id]["turns"][0]
            prompt_path = args.output.parent / f"llama_12q_q{question_id}_prompt.txt"
            prompt_path.write_text(prompt, encoding="utf-8")
            block = []
            for order_index, condition in enumerate(orders[str(question_id)]):
                metrics = run_cli(args.target, args.draft, prompt_path, args.max_tokens, condition)
                tokens = tokenize(args.target, metrics["completion_text"])
                item = {
                    "question_id": question_id, "category": questions[question_id].get("category"),
                    "order_index": order_index, "condition": condition, "tokens": tokens,
                    "token_sha256": hashlib.sha256(",".join(map(str, tokens)).encode()).hexdigest(),
                    "metrics": metrics,
                }
                record["runs"].append(item)
                block.append(item)
                completed += 1
                save(record, args.output)
                print(f"[{completed}/{total}] q={question_id} {condition} decode={metrics['decode_ms']:.2f}ms memory={metrics['memory_gate']['status']}", flush=True)
            baseline = next(item for item in block if item["condition"] == "baseline")
            for item in block:
                item["exact_match"] = item["tokens"] == baseline["tokens"]
                item["first_divergent_token"] = first_divergence(baseline["tokens"], item["tokens"])
            save(record, args.output)
            if not all(item["exact_match"] for item in block):
                record["status"] = "ABORTED_CORRECTNESS"
                break
        else:
            record["status"] = "PASS"
    finally:
        stop_telemetry(telemetry, stream)
    for item in record["runs"]:
        metrics = item["metrics"]
        metrics["energy"] = integrate_energy(args.telemetry_output, metrics["decode_start_unix_ns"], metrics["decode_end_unix_ns"])
    record["memory_after"] = memory_snapshot()
    record["ended"] = now()
    save(record, args.output)
    print(json.dumps({"status": record["status"], "runs": len(record["runs"]), "output": str(args.output)}, indent=2))
    return 0 if record["status"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
