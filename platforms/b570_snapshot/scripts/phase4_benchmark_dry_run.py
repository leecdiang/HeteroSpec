import os
import argparse
import csv
import json
import random
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import openvino as ov
import openvino_genai as ov_genai
import torch
from pynvml import (
    NVML_CLOCK_MEM, NVML_CLOCK_SM, NVML_TEMPERATURE_GPU,
    nvmlDeviceGetClockInfo, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo,
    nvmlDeviceGetPowerUsage, nvmlDeviceGetTemperature, nvmlDeviceGetUtilizationRates,
    nvmlInit, nvmlShutdown,
)
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

import phase3_cached_speculative_suite as engine


ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
SEED = 20260903


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


class NvmlLogger:
    fields = ["timestamp", "run_id", "power_W", "gpu_util_pct", "memory_util_pct", "temperature_C", "sm_clock_MHz", "memory_clock_MHz", "vram_used_MB", "error"]

    def __init__(self, path):
        self.path = path
        self.run_id = ""
        self.stop_event = threading.Event()

    def loop(self):
        with self.path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.fields)
            writer.writeheader()
            while not self.stop_event.is_set():
                row = {"timestamp": now(), "run_id": self.run_id, "error": ""}
                try:
                    nvmlInit()
                    gpu = nvmlDeviceGetHandleByIndex(0)
                    utilization = nvmlDeviceGetUtilizationRates(gpu)
                    row.update(
                        power_W=round(nvmlDeviceGetPowerUsage(gpu) / 1000, 1),
                        gpu_util_pct=utilization.gpu, memory_util_pct=utilization.memory,
                        temperature_C=nvmlDeviceGetTemperature(gpu, NVML_TEMPERATURE_GPU),
                        sm_clock_MHz=nvmlDeviceGetClockInfo(gpu, NVML_CLOCK_SM),
                        memory_clock_MHz=nvmlDeviceGetClockInfo(gpu, NVML_CLOCK_MEM),
                        vram_used_MB=round(nvmlDeviceGetMemoryInfo(gpu).used / 1024**2, 1),
                    )
                except Exception as exc:
                    row["error"] = f"{type(exc).__name__}: {exc}"
                finally:
                    try:
                        nvmlShutdown()
                    except Exception:
                        pass
                writer.writerow(row)
                handle.flush()
                self.stop_event.wait(1.0)

    def start(self):
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def close(self):
        self.stop_event.set()
        self.thread.join()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-count", type=int, default=6)
    parser.add_argument("--output-tokens", type=int, default=32)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable")
    core = ov.Core()
    if "CPU" not in core.available_devices:
        raise RuntimeError("OpenVINO CPU unavailable")

    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    telemetry = ROOT / "telemetry" / f"phase4_dry_run_nvml_{stamp}.csv"
    logger = NvmlLogger(telemetry)
    logger.start()
    record = {
        "session_id": f"p4-dry-{stamp}", "started": now(), "status": "STARTED",
        "seed": SEED, "prompt_count": args.prompt_count, "output_cap": args.output_tokens,
        "configs": ["B0", "SPEC-k1", "SPEC-k2", "SPEC-k4", "SPEC-k6", "SPEC-k8"],
        "target_compute_dtype": "fp32", "target_attention": "eager",
        "draft_device": "CPU", "nvml_csv": str(telemetry), "runs": [],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    try:
        tokenizer = AutoTokenizer.from_pretrained(engine.TARGET, local_files_only=True)
        quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float32, bnb_4bit_use_double_quant=True)
        engine.ATTENTION_BACKEND = "eager"
        model = AutoModelForCausalLM.from_pretrained(
            engine.TARGET, local_files_only=True, device_map={"": 0}, quantization_config=quant,
            dtype=torch.float32, low_cpu_mem_usage=True, attn_implementation="eager",
        ).eval()
        draft = ov_genai.LLMPipeline(engine.DRAFT, "CPU")
        eos_ids = {tokenizer.eos_token_id}
        rng = random.Random(SEED)
        for prompt_id, text in list(engine.PROMPTS.items())[:args.prompt_count]:
            encoded = tokenizer.apply_chat_template([{"role": "user", "content": text}], tokenize=True, add_generation_prompt=True, enable_thinking=False)
            prompt = encoded.input_ids if hasattr(encoded, "input_ids") else tokenizer(encoded, add_special_tokens=False).input_ids
            order = list(record["configs"])
            rng.shuffle(order)
            baseline = None
            pending = []
            for config in order:
                run_id = f"dry-{prompt_id}-{config}-{uuid.uuid4().hex[:8]}"
                logger.run_id = run_id
                torch.cuda.reset_peak_memory_stats()
                start = now()
                tick = time.perf_counter()
                if config == "B0":
                    tokens = engine.cached_reference(model, prompt, args.output_tokens, eos_ids)
                    rounds = None
                    baseline = tokens
                else:
                    k = int(config.split("k")[1])
                    tokens, rounds = engine.cached_speculative(model, draft, prompt, args.output_tokens, k, eos_ids, 0.5)
                torch.cuda.synchronize()
                elapsed = time.perf_counter() - tick
                logger.run_id = ""
                run = {
                    "run_id": run_id, "prompt_id": prompt_id, "config": config,
                    "order_index": order.index(config), "started": start, "ended": now(),
                    "input_tokens": len(prompt), "output_tokens": len(tokens),
                    "seconds": elapsed, "tokens_per_second": len(tokens) / elapsed,
                    "token_sha256": engine.sha(tokens), "peak_cuda_allocated_gib": torch.cuda.max_memory_allocated() / 1024**3,
                    "rounds": rounds,
                }
                record["runs"].append(run)
                if config != "B0":
                    pending.append(run)
                output.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            for run in pending:
                run["exact_match_to_B0"] = run["token_sha256"] == engine.sha(baseline)
                run["speedup_vs_B0"] = next(item["seconds"] for item in record["runs"] if item["prompt_id"] == prompt_id and item["config"] == "B0") / run["seconds"]
                if not run["exact_match_to_B0"]:
                    raise RuntimeError(f"Correctness failure in {run['run_id']}")
        record["status"] = "PASS"
    finally:
        logger.close()
        record["ended"] = now()
        output.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": record["status"], "runs": len(record["runs"]), "nvml_csv": str(telemetry), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
