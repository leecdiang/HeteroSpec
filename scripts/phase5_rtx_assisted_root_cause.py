import os
import argparse
import gc
import json
import random
import time
import uuid
from datetime import datetime
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

import phase3_cached_speculative_suite as engine
from phase4_benchmark_dry_run import NvmlLogger, now


ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
DATA = ROOT / "datasets" / "Spec-Bench" / "data" / "spec_bench" / "question.jsonl"
PILOT = ROOT / "env" / "specbench_pilot_ids.json"
DRAFT = ROOT / "models" / "qwen3-0.6b-source"
SEED = 20260903


def diagnostic_ids():
    split = json.loads(PILOT.read_text(encoding="utf-8"))
    groups = {}
    for item in split["items"]:
        groups.setdefault(item["category"], []).append(item["question_id"])
    # Length-only safety selection, fixed before observing RTX-assisted results.
    # These are the two shortest completed B0 inputs in each pilot task group.
    selected = {
        "math_reasoning": [469, 438], "multi_turn": [108, 160],
        "qa": [395, 346], "rag": [503, 552],
        "summarization": [291, 315], "translation": [164, 239],
    }
    if set(selected) != set(groups):
        raise RuntimeError("Pilot task groups changed")
    return [question_id for group in groups for question_id in selected[group]]


def render(tokenizer, messages):
    encoded = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, enable_thinking=False,
        return_tensors="pt",
    )
    if hasattr(encoded, "input_ids"):
        encoded = encoded.input_ids
    return encoded.to("cuda:0")


def generate(target, input_ids, max_new_tokens, assistant=None):
    eos_token_id = target.generation_config.eos_token_id
    pad_token_id = eos_token_id[0] if isinstance(eos_token_id, list) else eos_token_id
    kwargs = dict(
        input_ids=input_ids,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        use_cache=True,
        eos_token_id=eos_token_id,
        pad_token_id=pad_token_id,
    )
    if assistant is not None:
        kwargs["assistant_model"] = assistant
    with torch.inference_mode():
        output = target.generate(**kwargs)
    torch.cuda.synchronize()
    return output[0, input_ids.shape[1]:].tolist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--question-id", type=int)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--target-model", default=str(engine.TARGET))
    parser.add_argument("--target-nonquant-dtype", choices=["fp32", "bf16"], default="fp32")
    parser.add_argument("--assistant-device", choices=["cuda", "cpu"], default="cuda")
    parser.add_argument("--memory-fraction", type=float, default=1.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable")
    torch.cuda.set_per_process_memory_fraction(args.memory_fraction, 0)

    questions = {row["question_id"]: row for row in map(json.loads, DATA.read_text(encoding="utf-8").splitlines())}
    ids = [args.question_id] if args.question_id is not None else diagnostic_ids()
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    telemetry = ROOT / "telemetry" / f"phase5_rtx_assisted_nvml_{stamp}.csv"
    output_path = Path(args.output)
    record = {
        "session_id": f"p5-rtx-assisted-{stamp}", "started": now(), "status": "STARTED",
        "question_ids": ids, "max_new_tokens": args.max_new_tokens,
        "selection_rule": "two shortest completed B0 inputs per pilot task group; frozen before assisted results",
        "target": args.target_model, "assistant": str(DRAFT),
        "target_dtype": f"nf4-fp32compute-{args.target_nonquant_dtype}-nonquant", "target_attention": "eager",
        "assistant_dtype": "bf16", "assistant_device": args.assistant_device,
        "memory_fraction_limit": args.memory_fraction,
        "num_assistant_tokens": 1, "num_assistant_tokens_schedule": "constant",
        "nvml_csv": str(telemetry), "questions": [],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    logger = NvmlLogger(telemetry)
    logger.start()
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.target_model, local_files_only=True)
        quant = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float32, bnb_4bit_use_double_quant=True,
        )
        target_dtype = torch.float32 if args.target_nonquant_dtype == "fp32" else torch.bfloat16
        target = AutoModelForCausalLM.from_pretrained(
            args.target_model, local_files_only=True, device_map={"": 0},
            quantization_config=quant, dtype=target_dtype,
            low_cpu_mem_usage=True, attn_implementation="eager",
        ).eval()
        assistant = AutoModelForCausalLM.from_pretrained(
            DRAFT, local_files_only=True,
            device_map={"": 0} if args.assistant_device == "cuda" else {"": "cpu"}, dtype=torch.bfloat16,
            low_cpu_mem_usage=True, attn_implementation="eager",
        ).eval()
        assistant.generation_config.num_assistant_tokens = 1
        assistant.generation_config.num_assistant_tokens_schedule = "constant"
        assistant.generation_config.assistant_confidence_threshold = 0.0

        warm = render(tokenizer, [{"role": "user", "content": "Reply with OK."}])
        generate(target, warm, 4)
        generate(target, warm, 4, assistant)
        del warm
        gc.collect()
        torch.cuda.empty_cache()

        rng = random.Random(SEED)
        for question_id in ids:
            question = questions[question_id]
            qrecord = {"question_id": question_id, "category": question["category"], "configs": []}
            order = ["A-RTX-baseline", "C-RTX-assisted-k1"]
            rng.shuffle(order)
            for config in order:
                messages = []
                turns = []
                for turn_index, user_text in enumerate(question["turns"]):
                    messages.append({"role": "user", "content": user_text})
                    input_ids = render(tokenizer, messages)
                    gc.collect()
                    torch.cuda.empty_cache()
                    torch.cuda.reset_peak_memory_stats()
                    run_id = f"p5-q{question_id}-t{turn_index}-{config}-{uuid.uuid4().hex[:8]}"
                    logger.run_id = run_id
                    wall_start = now()
                    tick = time.perf_counter()
                    tokens = generate(target, input_ids, args.max_new_tokens, assistant if config.startswith("C-") else None)
                    elapsed = time.perf_counter() - tick
                    wall_end = now()
                    logger.run_id = ""
                    messages.append({"role": "assistant", "content": tokenizer.decode(tokens, skip_special_tokens=True)})
                    turns.append({
                        "run_id": run_id, "turn_index": turn_index,
                        "input_tokens": input_ids.shape[1], "output_tokens": len(tokens),
                        "seconds": elapsed, "tokens_per_second": len(tokens) / elapsed,
                        "timestamp_start": wall_start, "timestamp_end": wall_end,
                        "token_sha256": engine.sha(tokens),
                        "peak_cuda_allocated_gib": torch.cuda.max_memory_allocated() / 1024**3,
                    })
                qrecord["configs"].append({"config": config, "turns": turns, "seconds": sum(t["seconds"] for t in turns)})
            baseline = next(c for c in qrecord["configs"] if c["config"].startswith("A-"))
            assisted = next(c for c in qrecord["configs"] if c["config"].startswith("C-"))
            assisted["exact_match_to_baseline"] = [t["token_sha256"] for t in assisted["turns"]] == [t["token_sha256"] for t in baseline["turns"]]
            assisted["speedup_vs_baseline"] = baseline["seconds"] / assisted["seconds"]
            record["questions"].append(qrecord)
            output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        failures = [
            q["question_id"] for q in record["questions"]
            if not next(c for c in q["configs"] if c["config"].startswith("C-"))["exact_match_to_baseline"]
        ]
        record["exact_match_failures"] = failures
        record["status"] = "PASS" if not failures else "FAIL_CORRECTNESS"
    finally:
        logger.close()
        record["ended"] = now()
        output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": record["status"], "questions": len(record["questions"]), "output": str(output_path)}, indent=2))


if __name__ == "__main__":
    main()
