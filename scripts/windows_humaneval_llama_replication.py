#!/usr/bin/env python3
"""Matched HumanEval replication using llama.cpp CUDA on Windows."""

import argparse
import csv
import gzip
import hashlib
import json
import os
import random
import re
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def save_json(value, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temporary.replace(path)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_dataset(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return {row["task_id"]: row for row in map(json.loads, stream)}


def first_divergence(left, right):
    for index, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return index
    return None if len(left) == len(right) else min(len(left), len(right))


def tokenize(executable, model, text):
    result = subprocess.run(
        [str(executable), "--model", str(model), "--stdin", "--ids"],
        input=text, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return json.loads(result.stdout.strip())


def log_seconds(line):
    match = re.match(r"(\d+)\.(\d{2})\.(\d{3})\.(\d{3})", line)
    if not match:
        return None
    minutes, seconds, millis, micros = map(int, match.groups())
    return minutes * 60 + seconds + millis / 1000 + micros / 1_000_000


def parse_output(stdout, stderr):
    if "\n> " not in stdout or "\n\n[ Prompt:" not in stdout:
        raise RuntimeError("Could not isolate completion from llama-cli output")
    body = stdout.rsplit("\n> ", 1)[1]
    completion = body.split("\n", 1)[1].rsplit("\n\n[ Prompt:", 1)[0]
    prompt_perf = re.search(r"prompt eval time\s*=\s*([0-9.]+) ms /\s*(\d+) tokens", stderr)
    eval_perf = re.search(r"\|\s+eval time\s*=\s*([0-9.]+) ms /\s*(\d+) tokens", stderr)
    acceptance = re.search(
        r"draft acceptance\s*=\s*([0-9.]+) \(\s*(\d+) accepted /\s*(\d+) generated\), mean len =\s*([0-9.]+)",
        stderr,
    )
    stats = re.search(
        r"statistics\s+draft-simple: #calls\(b,g,a\) =\s*(\d+)\s+(\d+)\s+(\d+),.*?"
        r"#gen drafts =\s*(\d+), #acc drafts =\s*(\d+), #gen tokens =\s*(\d+), #acc tokens =\s*(\d+)",
        stderr,
    )
    durations = re.search(
        r"statistics\s+draft-simple:.*?dur\(b,g,a\) =\s*([0-9.]+),\s*([0-9.]+),\s*([0-9.]+) ms",
        stderr,
    )
    if not prompt_perf or not eval_perf:
        raise RuntimeError("Required llama.cpp timing fields were not found")
    result = {
        "completion_text": completion,
        "prompt_eval_ms": float(prompt_perf.group(1)),
        "prompt_tokens": int(prompt_perf.group(2)),
        "decode_ms": float(eval_perf.group(1)),
        "output_tokens_runtime": int(eval_perf.group(2)),
        "decode_tok_s": int(eval_perf.group(2)) / (float(eval_perf.group(1)) / 1000),
    }
    if acceptance:
        result.update(
            acceptance_rate=float(acceptance.group(1)),
            accepted_tokens=int(acceptance.group(2)),
            drafted_tokens=int(acceptance.group(3)),
            accepted_per_round=float(acceptance.group(4)) - 1.0,
        )
    if stats:
        result["verification_rounds"] = int(stats.group(2))
        result["spec_calls"] = {
            "batch": int(stats.group(1)), "generate": int(stats.group(2)), "accept": int(stats.group(3)),
            "draft_sequences": int(stats.group(4)), "accepted_sequences": int(stats.group(5)),
            "drafted_tokens": int(stats.group(6)), "accepted_tokens": int(stats.group(7)),
        }
    if durations:
        result["spec_impl_duration_ms"] = {
            "batch": float(durations.group(1)), "draft_generate": float(durations.group(2)),
            "accept": float(durations.group(3)),
        }
    placement = [line for line in stderr.splitlines() if any(fragment in line for fragment in (
        "offloaded ", "model buffer size", "KV buffer size", "memory breakdown", "CUDA0 (", "device_info:",
    ))]
    result["placement_evidence"] = placement
    offload = re.search(r"offloaded\s+(\d+)/(\d+) layers to GPU", stderr)
    result["target_full_offload"] = bool(offload and offload.group(1) == offload.group(2))
    return result


class NvmlSampler:
    def __init__(self, run_id, csv_path):
        self.run_id, self.csv_path = run_id, csv_path
        self.rows, self.stop_event = [], threading.Event()

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            while not self.stop_event.is_set():
                util, mem = pynvml.nvmlDeviceGetUtilizationRates(handle), pynvml.nvmlDeviceGetMemoryInfo(handle)
                self.rows.append({
                    "timestamp": utc_now(), "run_id": self.run_id,
                    "power_W": round(pynvml.nvmlDeviceGetPowerUsage(handle) / 1000, 1),
                    "gpu_util_pct": util.gpu, "memory_util_pct": util.memory,
                    "temperature_C": pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU),
                    "sm_clock_MHz": pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM),
                    "memory_clock_MHz": pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM),
                    "vram_used_MB": round(mem.used / 1024**2, 1),
                })
                self.stop_event.wait(1.0)
            pynvml.nvmlShutdown()
        except Exception as exc:
            self.error = repr(exc)

    def stop(self):
        self.stop_event.set(); self.thread.join()
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        exists = self.csv_path.exists()
        if self.rows:
            with self.csv_path.open("a", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(self.rows[0]))
                if not exists: writer.writeheader()
                writer.writerows(self.rows)
        return {
            "samples": len(self.rows),
            "peak_vram_MB": max((row["vram_used_MB"] for row in self.rows), default=None),
            "mean_power_W": sum(row["power_W"] for row in self.rows) / len(self.rows) if self.rows else None,
            "error": getattr(self, "error", None),
        }


def run_cli(args, prompt, task_id, repetition, condition, telemetry_csv):
    prompt_dir = args.output.parent / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = prompt_dir / f"{task_id.replace('/', '_')}.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    command = [
        str(args.llama_cli), "--model", str(args.target), "--device", "CUDA0",
        "--n-gpu-layers", "all", "--fit", "off", "--ctx-size", str(args.ctx_size),
        "--flash-attn", args.flash_attn,
        "--ubatch-size", str(args.ubatch_size),
        "--file", str(prompt_path), "--n-predict", str(args.max_tokens), "--temp", "0",
        "--top-k", "0", "--top-p", "1", "--min-p", "0", "--seed", "123",
        "--single-turn", "--simple-io", "--no-display-prompt", "--no-warmup",
        "--cache-ram", "0", "--chat-template-kwargs", '{"enable_thinking":false}',
        "--log-verbosity", "4", "--perf",
    ]
    if condition == "cpu_k2":
        command += [
            "--spec-type", "draft-simple", "--model-draft", str(args.draft),
            "--spec-draft-device", "none", "--spec-draft-ngl", "0",
            "--spec-draft-n-max", "2", "--spec-draft-n-min", "0",
        ]
    elif condition == "rtx_k2":
        command += [
            "--spec-type", "draft-simple", "--model-draft", str(args.draft),
            "--spec-draft-device", "CUDA0", "--spec-draft-ngl", "all",
            "--spec-draft-n-max", "2", "--spec-draft-n-min", "0",
        ]
    run_id = f"{task_id.replace('/', '-')}-r{repetition}-{condition}"
    sampler = NvmlSampler(run_id, telemetry_csv); sampler.start()
    started = utc_now(); t0 = time.perf_counter()
    process = subprocess.run(command, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process_ms = (time.perf_counter() - t0) * 1000; ended = utc_now()
    telemetry = sampler.stop()
    if process.returncode:
        raise RuntimeError(f"llama-cli failed {process.returncode}: {process.stderr[-4000:]}")
    metrics = parse_output(process.stdout, process.stderr)
    if not metrics["target_full_offload"]:
        raise RuntimeError("Target did not report full CUDA layer offload")
    tokens = tokenize(args.llama_tokenize, args.target, metrics["completion_text"])
    return {
        "run_id": run_id, "task_id": task_id, "repetition": repetition, "condition": condition,
        "started": started, "ended": ended, "process_ms": process_ms, "command": command,
        "tokens": tokens, "token_sha256": hashlib.sha256(",".join(map(str, tokens)).encode()).hexdigest(),
        "metrics": metrics, "telemetry": telemetry,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--llama-cli", type=Path, default=ROOT / "tools/llama-b10839/llama-cli.exe")
    parser.add_argument("--llama-tokenize", type=Path, default=ROOT / "tools/llama-b10839/llama-tokenize.exe")
    parser.add_argument("--target", type=Path, default=ROOT / "models/gguf/Qwen3-8B-Q8_0.gguf")
    parser.add_argument("--draft", type=Path, default=ROOT / "models/gguf/Qwen3-0.6B-Q8_0.gguf")
    parser.add_argument("--dataset", type=Path, default=ROOT / "datasets/humaneval/HumanEval.jsonl.gz")
    parser.add_argument("--preregistration", type=Path, default=ROOT / "benchmarks/m4_code_conditioned_30q/preregistration.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--telemetry-csv", type=Path, required=True)
    parser.add_argument("--conditions", nargs="+", choices=["baseline", "cpu_k2", "rtx_k2"], default=["baseline", "cpu_k2"])
    parser.add_argument("--task-ids", nargs="*")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--ctx-size", type=int, default=4096)
    parser.add_argument("--flash-attn", choices=["on", "off", "auto"], default="off")
    parser.add_argument("--ubatch-size", type=int, default=512)
    args = parser.parse_args()
    prereg = json.loads(args.preregistration.read_text(encoding="utf-8"))
    frozen_ids = prereg["dataset"]["task_ids"]
    ids = args.task_ids or frozen_ids
    if any(task_id not in frozen_ids for task_id in ids):
        raise RuntimeError("Every task must belong to the frozen M4 set")
    problems = load_dataset(args.dataset)
    rng = random.Random(20260909)
    schedule = []
    for repetition in range(1, args.repetitions + 1):
        rep_ids = ids.copy(); rng.shuffle(rep_ids)
        for task_id in rep_ids:
            order = args.conditions.copy(); rng.shuffle(order)
            schedule.append({"task_id": task_id, "repetition": repetition, "order": order})
    record = {
        "schema": "heterospec.windows_humaneval_llama_replication.v1", "status": "STARTED",
        "started": utc_now(), "relationship": "post-hoc fixed-sample cross-platform replication",
        "source_preregistration_commit": "1646c56", "m4_result_commit": None,
        "m4_result_commit_status": "not present in fetched remote history at experiment start",
        "dataset_sha256": sha256(args.dataset), "target_sha256": sha256(args.target), "draft_sha256": sha256(args.draft),
        "conditions": args.conditions, "schedule": schedule, "runs": [],
        "runtime": {"llama_cpp_build": 10839, "llama_cpp_commit": "0cae43063", "backend": "CUDA12.4", "ctx_size": args.ctx_size, "flash_attn": args.flash_attn, "ubatch_size": args.ubatch_size},
    }
    save_json(record, args.output)
    total = len(schedule) * len(args.conditions); completed = 0
    for block in schedule:
        prompt = prereg["fixed_runtime"]["prompt_template"].replace("{humaneval_prompt}", problems[block["task_id"]]["prompt"])
        pair = []
        for condition in block["order"]:
            item = run_cli(args, prompt, block["task_id"], block["repetition"], condition, args.telemetry_csv)
            pair.append(item); record["runs"].append(item); completed += 1
            save_json(record, args.output)
            print(f"[{completed}/{total}] {item['run_id']} decode={item['metrics']['decode_ms']:.2f}ms vram={item['telemetry']['peak_vram_MB']}", flush=True)
        baseline = next(item for item in pair if item["condition"] == "baseline")
        for item in pair:
            item["exact_match"] = item["tokens"] == baseline["tokens"]
            item["first_divergent_token"] = first_divergence(baseline["tokens"], item["tokens"])
            if item["condition"] != "baseline": item["paired_speedup"] = baseline["metrics"]["decode_ms"] / item["metrics"]["decode_ms"]
        save_json(record, args.output)
        if not all(item["exact_match"] for item in pair):
            record["status"] = "ABORTED_CORRECTNESS"; break
    else:
        record["status"] = "PASS"
    record["ended"] = utc_now(); save_json(record, args.output)
    print(json.dumps({"status": record["status"], "runs": len(record["runs"])}, indent=2))
    return 0 if record["status"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
