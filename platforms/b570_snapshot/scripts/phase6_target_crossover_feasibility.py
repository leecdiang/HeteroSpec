import os
import argparse
import json
import statistics
import time
import traceback
import uuid
from datetime import datetime
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from phase4_benchmark_dry_run import NvmlLogger, now


ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
TEXT = (
    "Heterogeneous computing assigns work to processors with different strengths. "
    "A reproducible experiment records every configuration, timestamp, and device name. "
    "Correctness is checked before performance. "
)


def one_run(model, prompt, output_tokens):
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.synchronize()
    tick = time.perf_counter()
    with torch.inference_mode():
        result = model(input_ids=prompt, use_cache=True)
    torch.cuda.synchronize()
    ttft_ms = (time.perf_counter() - tick) * 1000
    cache = result.past_key_values
    token = int(result.logits[0, -1].argmax())
    output = [token]
    torch.cuda.synchronize()
    decode_tick = time.perf_counter()
    with torch.inference_mode():
        for _ in range(output_tokens - 1):
            result = model(
                input_ids=torch.tensor([[token]], dtype=torch.long, device="cuda:0"),
                past_key_values=cache, use_cache=True,
            )
            cache = result.past_key_values
            token = int(result.logits[0, -1].argmax())
            output.append(token)
    torch.cuda.synchronize()
    decode_ms = (time.perf_counter() - decode_tick) * 1000
    total_ms = ttft_ms + decode_ms
    return {
        "ttft_ms": ttft_ms,
        "decode_ms": decode_ms,
        "decode_ms_per_token": decode_ms / (output_tokens - 1),
        "sustained_tokens_s": (output_tokens - 1) / (decode_ms / 1000),
        "end_to_end_tokens_s": output_tokens / (total_ms / 1000),
        "peak_cuda_allocated_gib": torch.cuda.max_memory_allocated() / 1024**3,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--memory-fraction", type=float, default=0.85)
    parser.add_argument("--nonquant-dtype", choices=["fp32", "bf16"], default="fp32")
    parser.add_argument("--context", type=int, default=128)
    parser.add_argument("--output-tokens", type=int, default=256)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable; fallback prohibited")
    torch.cuda.set_per_process_memory_fraction(args.memory_fraction, 0)

    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    telemetry = ROOT / "telemetry" / f"phase6_{args.label}_nvml_{stamp}.csv"
    record = {
        "started": now(), "status": "STARTED", "model": args.model,
        "label": args.label, "revision": args.revision,
        "precision": f"bitsandbytes NF4, FP32 quant compute, {args.nonquant_dtype} non-quantized layers, double quant",
        "attention": "eager", "memory_fraction_limit": args.memory_fraction,
        "context_tokens": args.context, "output_tokens": args.output_tokens,
        "repetitions": args.repetitions, "nvml_csv": str(telemetry), "runs": [],
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    logger = NvmlLogger(telemetry)
    logger.start()
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
        quant = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float32, bnb_4bit_use_double_quant=True,
        )
        nonquant_dtype = torch.float32 if args.nonquant_dtype == "fp32" else torch.bfloat16
        model = AutoModelForCausalLM.from_pretrained(
            args.model, local_files_only=True, device_map={"": 0},
            quantization_config=quant, dtype=nonquant_dtype,
            low_cpu_mem_usage=True, attn_implementation="eager",
        ).eval()
        if not str(next(model.parameters()).device).startswith("cuda"):
            raise RuntimeError("Target model fallback detected")
        encoded = tokenizer(TEXT * 20, add_special_tokens=False).input_ids[:args.context]
        if len(encoded) != args.context:
            raise RuntimeError("Prompt construction too short")
        prompt = torch.tensor([encoded], dtype=torch.long, device="cuda:0")

        logger.run_id = f"phase6-{args.label}-warmup"
        one_run(model, prompt, 8)
        for repetition in range(1, args.repetitions + 1):
            logger.run_id = f"phase6-{args.label}-r{repetition}-{uuid.uuid4().hex[:8]}"
            run = one_run(model, prompt, args.output_tokens)
            run["repetition"] = repetition
            record["runs"].append(run)
            output_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        logger.run_id = ""
        for field in ["ttft_ms", "decode_ms_per_token", "sustained_tokens_s", "end_to_end_tokens_s", "peak_cuda_allocated_gib"]:
            record.setdefault("summary", {})[f"median_{field}"] = statistics.median(run[field] for run in record["runs"])
        record["status"] = "PASS"
    except torch.OutOfMemoryError as exc:
        record["status"] = "FAIL_SAFE_OOM"
        record["error"] = str(exc)
    except Exception as exc:
        record["status"] = "FAIL_SAFE_EXCEPTION"
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc()
    finally:
        logger.close()
        record["ended"] = now()
        output_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({"status": record["status"], "summary": record.get("summary"), "output": str(output_path)}, indent=2))
    raise SystemExit(0 if record["status"] == "PASS" else 2)


if __name__ == "__main__":
    main()
