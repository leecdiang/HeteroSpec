import os
import argparse
import gc
import json
import random
import time
import uuid
from datetime import datetime
from pathlib import Path

import openvino_genai as ov_genai
import ittapi
import torch
from pynvml import nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo, nvmlInit, nvmlShutdown
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

import phase3_cached_speculative_suite as engine
from phase4_benchmark_dry_run import NvmlLogger, now


ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
DATA = ROOT / "datasets" / "Spec-Bench" / "data" / "spec_bench" / "question.jsonl"
PILOT = ROOT / "env" / "specbench_pilot_ids.json"
SEED = 20260903
CONFIGS = ["B0", "SPEC-k1", "SPEC-k2", "SPEC-k4", "SPEC-k6", "SPEC-k8"]
ITT_DOMAIN = ittapi.domain("HeteroSpec-PC")


class CudaDraft:
    def __init__(self, model):
        self.model = model

    def propose(self, prefix, count):
        input_ids = torch.tensor([prefix], dtype=torch.long, device="cuda:0")
        tokens = []
        with torch.inference_mode():
            result = self.model(input_ids=input_ids, use_cache=True)
            cache = result.past_key_values
            token = int(result.logits[0, -1].argmax())
            for index in range(count):
                tokens.append(token)
                if index + 1 < count:
                    result = self.model(
                        input_ids=torch.tensor([[token]], dtype=torch.long, device="cuda:0"),
                        past_key_values=cache, use_cache=True,
                    )
                    cache = result.past_key_values
                    token = int(result.logits[0, -1].argmax())
        torch.cuda.synchronize()
        return tokens


def render(tokenizer, messages):
    encoded = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, enable_thinking=False)
    return encoded.input_ids if hasattr(encoded, "input_ids") else tokenizer(encoded, add_special_tokens=False).input_ids


def nvml_free_vram_mib():
    nvmlInit()
    try:
        memory = nvmlDeviceGetMemoryInfo(nvmlDeviceGetHandleByIndex(0))
        return memory.free / 1024**2
    finally:
        nvmlShutdown()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--question-id", type=int)
    parser.add_argument("--question-ids")
    parser.add_argument("--configs", nargs="+", choices=CONFIGS, default=CONFIGS)
    parser.add_argument("--draft-device", choices=["CPU", "CUDA"], default="CPU")
    parser.add_argument("--target-model", default=str(engine.TARGET))
    parser.add_argument("--target-nonquant-dtype", choices=["fp32", "bf16"], default="fp32")
    parser.add_argument("--memory-fraction", type=float, default=1.0)
    parser.add_argument("--output", required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    torch.cuda.set_per_process_memory_fraction(args.memory_fraction, 0)
    all_questions = {row["question_id"]: row for row in (json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines())}
    split = json.loads(PILOT.read_text(encoding="utf-8"))
    if args.question_id is not None and args.question_ids:
        raise RuntimeError("Use only one of --question-id and --question-ids")
    explicit_ids = [int(value) for value in args.question_ids.split(",")] if args.question_ids else None
    selected = ([all_questions[args.question_id]] if args.question_id is not None else
                [all_questions[value] for value in explicit_ids] if explicit_ids else
                [all_questions[item["question_id"]] for item in split["items"][:args.limit]])
    expected_count = 1 if args.question_id is not None else len(explicit_ids) if explicit_ids else args.limit
    if len(selected) != expected_count:
        raise RuntimeError("Pilot selection incomplete")

    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    telemetry = ROOT / "telemetry" / f"phase4_specbench_pilot_nvml_{stamp}.csv"
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.resume and output.exists():
        record = json.loads(output.read_text(encoding="utf-8"))
        if record["question_count"] != len(selected) or record["max_new_tokens"] != args.max_new_tokens:
            raise RuntimeError("Resume configuration does not match existing session")
        record["status"] = "STARTED"
        record.setdefault("resume_events", []).append({"timestamp": now(), "telemetry": str(telemetry)})
        record.setdefault("nvml_csv_segments", [record["nvml_csv"]]).append(str(telemetry))
    else:
        record = {
            "session_id": f"p4-pilot-{stamp}", "started": now(), "status": "STARTED",
            "dataset": str(DATA), "split": str(PILOT), "split_seed": SEED,
            "question_count": len(selected), "max_new_tokens": args.max_new_tokens,
            "configs": args.configs, "target_compute_dtype": "fp32",
            "target_nonquant_dtype": args.target_nonquant_dtype,
            "target_model": args.target_model, "target_attention": "eager",
            "memory_fraction_limit": args.memory_fraction,
            "draft_device": args.draft_device, "nvml_csv": str(telemetry),
            "nvml_csv_segments": [str(telemetry)], "questions": [],
        }
    logger = NvmlLogger(telemetry)
    logger.start()
    output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.target_model, local_files_only=True)
        quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float32, bnb_4bit_use_double_quant=True)
        engine.ATTENTION_BACKEND = "eager"
        nonquant_dtype = torch.float32 if args.target_nonquant_dtype == "fp32" else torch.bfloat16
        target = AutoModelForCausalLM.from_pretrained(
            args.target_model, local_files_only=True, device_map={"": 0}, quantization_config=quant,
            dtype=nonquant_dtype, low_cpu_mem_usage=True, attn_implementation="eager",
        ).eval()
        if args.draft_device == "CPU":
            draft = ov_genai.LLMPipeline(engine.DRAFT, "CPU")
        else:
            draft_model = AutoModelForCausalLM.from_pretrained(
                ROOT / "models" / "qwen3-0.6b-source", local_files_only=True,
                device_map={"": 0}, dtype=torch.bfloat16, low_cpu_mem_usage=True,
                attn_implementation="eager",
            ).eval()
            draft = CudaDraft(draft_model)
        eos_ids = {tokenizer.eos_token_id}
        rng = random.Random(SEED)

        for question in selected:
            order = list(args.configs)
            rng.shuffle(order)
            if any(item["question_id"] == question["question_id"] for item in record["questions"]):
                continue
            qrecord = {"question_id": question["question_id"], "category": question["category"], "config_order": order, "configs": []}
            outputs_by_config = {}
            for config in order:
                messages = []
                turn_records = []
                config_start = time.perf_counter()
                for turn_index, user_text in enumerate(question["turns"]):
                    messages.append({"role": "user", "content": user_text})
                    prompt = render(tokenizer, messages)
                    run_id = f"p4-q{question['question_id']}-t{turn_index}-{config}-{uuid.uuid4().hex[:8]}"
                    logger.run_id = run_id
                    gc.collect()
                    torch.cuda.empty_cache()
                    free_before_mib = nvml_free_vram_mib()
                    if free_before_mib < 1024:
                        raise RuntimeError(f"VRAM safety guard: only {free_before_mib:.1f} MiB free before {run_id}")
                    torch.cuda.reset_peak_memory_stats()
                    wall_start = now()
                    tick = time.perf_counter()
                    with ittapi.task(f"run|{run_id}", domain=ITT_DOMAIN):
                        if config == "B0":
                            tokens = engine.cached_reference(target, prompt, args.max_new_tokens, eos_ids)
                            rounds = None
                        else:
                            k = int(config.split("k")[1])
                            tokens, rounds = engine.cached_speculative(target, draft, prompt, args.max_new_tokens, k, eos_ids, 0.5)
                    torch.cuda.synchronize()
                    elapsed = time.perf_counter() - tick
                    wall_end = now()
                    logger.run_id = ""
                    messages.append({"role": "assistant", "content": tokenizer.decode(tokens, skip_special_tokens=True)})
                    turn_records.append({
                        "run_id": run_id, "turn_index": turn_index, "input_tokens": len(prompt),
                        "output_tokens": len(tokens), "seconds": elapsed,
                        "timestamp_start": wall_start, "timestamp_end": wall_end,
                        "token_sha256": engine.sha(tokens), "hit_cap": len(tokens) == args.max_new_tokens,
                        "free_vram_before_mib": free_before_mib,
                        "free_vram_source": "NVML",
                        "peak_cuda_allocated_gib": torch.cuda.max_memory_allocated() / 1024**3,
                        "rounds": rounds,
                    })
                outputs_by_config[config] = [item["token_sha256"] for item in turn_records]
                qrecord["configs"].append({"config": config, "seconds": time.perf_counter() - config_start, "turns": turn_records})
                output.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            if "B0" not in outputs_by_config:
                raise RuntimeError("B0 is required for exact-match validation")
            baseline_hashes = outputs_by_config["B0"]
            for config_record in qrecord["configs"]:
                config_record["exact_match_to_B0"] = [item["token_sha256"] for item in config_record["turns"]] == baseline_hashes
                if not config_record["exact_match_to_B0"]:
                    raise RuntimeError(f"Correctness failure q={question['question_id']} config={config_record['config']}")
            record["questions"].append(qrecord)
            output.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        record["status"] = "PASS"
    finally:
        logger.close()
        record["ended"] = now()
        output.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": record["status"], "questions": len(record["questions"]), "output": str(output), "nvml": str(telemetry)}, indent=2))


if __name__ == "__main__":
    main()
