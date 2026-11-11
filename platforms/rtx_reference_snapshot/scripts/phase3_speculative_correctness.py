import os
import argparse
import hashlib
import json
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openvino as ov
import openvino_genai as ov_genai
import torch
from torch.nn.attention import SDPBackend, sdpa_kernel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
TARGET = ROOT / "models" / "qwen3-8b"
DRAFT = ROOT / "models" / "qwen3-0.6b-int4-sym-npu-v2"
TEXT = (
    "Heterogeneous computing assigns work to processors with different strengths. "
    "A reproducible experiment records every configuration, timestamp, and device. "
    "Correctness must be established before performance is measured. "
)


def iso_now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


def digest(ids):
    return hashlib.sha256(np.asarray(ids, dtype=np.int64).tobytes()).hexdigest()


@contextmanager
def cudnn_attention():
    with sdpa_kernel(SDPBackend.CUDNN_ATTENTION):
        yield


def ov_inputs(ids):
    values = np.asarray(ids, dtype=np.int64).reshape(1, -1)
    return ov_genai.TokenizedInputs(ov.Tensor(values), ov.Tensor(np.ones_like(values)))


def draft_tokens(pipe, prefix, count):
    cfg = ov_genai.GenerationConfig()
    cfg.max_new_tokens = count
    cfg.do_sample = False
    cfg.ignore_eos = True
    result = pipe.generate(ov_inputs(prefix), cfg)
    return [int(value) for value in result.tokens[0]]


def target_predictions(model, sequence, start_index):
    ids = torch.tensor([sequence], dtype=torch.long, device="cuda:0")
    mask = torch.ones_like(ids)
    with torch.inference_mode(), cudnn_attention():
        logits = model(input_ids=ids, attention_mask=mask, use_cache=False).logits
    return logits[0, start_index:, :].argmax(dim=-1).tolist()


def target_reference(model, prefix, output_tokens):
    sequence = list(prefix)
    generated = []
    for _ in range(output_tokens):
        prediction = target_predictions(model, sequence, len(sequence) - 1)[0]
        sequence.append(prediction)
        generated.append(prediction)
    return generated


def speculative(model, draft_pipe, prefix, output_tokens, k):
    sequence = list(prefix)
    generated = []
    rounds = []
    while len(generated) < output_tokens:
        offer = min(k, output_tokens - len(generated))
        t0 = time.perf_counter()
        candidates = draft_tokens(draft_pipe, sequence, offer)
        draft_seconds = time.perf_counter() - t0

        t1 = time.perf_counter()
        predictions = target_predictions(model, sequence + candidates, len(sequence) - 1)
        torch.cuda.synchronize()
        target_seconds = time.perf_counter() - t1

        accepted = 0
        mismatch = None
        for index, candidate in enumerate(candidates):
            if candidate != predictions[index]:
                mismatch = index
                break
            sequence.append(candidate)
            generated.append(candidate)
            accepted += 1
            if len(generated) == output_tokens:
                break

        correction = None
        bonus = None
        if len(generated) < output_tokens:
            if mismatch is not None:
                correction = int(predictions[mismatch])
                sequence.append(correction)
                generated.append(correction)
            elif accepted == len(candidates):
                bonus = int(predictions[len(candidates)])
                sequence.append(bonus)
                generated.append(bonus)

        rounds.append({
            "offered": len(candidates),
            "accepted": accepted,
            "mismatch_index": mismatch,
            "correction_token": correction,
            "bonus_token": bonus,
            "draft_seconds": draft_seconds,
            "target_seconds": target_seconds,
        })
    return generated[:output_tokens], rounds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, required=True)
    parser.add_argument("--prompt-tokens", type=int, default=64)
    parser.add_argument("--output-tokens", type=int, default=16)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.k < 1:
        raise ValueError("k must be positive")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable; fallback forbidden")
    core = ov.Core()
    if "CPU" not in core.available_devices:
        raise RuntimeError("OpenVINO CPU unavailable; fallback forbidden")

    record = {
        "started": iso_now(),
        "status": "STARTED",
        "algorithm": "greedy speculative decoding, recompute correctness prototype",
        "k": args.k,
        "prompt_tokens": args.prompt_tokens,
        "output_tokens": args.output_tokens,
        "draft_device_requested": "CPU",
        "draft_device_name": core.get_property("CPU", "FULL_DEVICE_NAME"),
        "target_device_requested": "cuda:0",
        "target_device_name": torch.cuda.get_device_name(0),
        "target_attention_backend": "cudnn",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2), encoding="utf-8")

    tokenizer = AutoTokenizer.from_pretrained(TARGET, local_files_only=True)
    prompt = tokenizer(TEXT * (args.prompt_tokens // 20 + 10), add_special_tokens=False).input_ids[:args.prompt_tokens]
    if len(prompt) != args.prompt_tokens:
        raise RuntimeError("Could not construct exact prompt length")
    record["prompt_sha256"] = digest(prompt)
    record["tokenizer_vocab_size"] = tokenizer.vocab_size

    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    load_start = time.perf_counter()
    target = AutoModelForCausalLM.from_pretrained(
        TARGET,
        local_files_only=True,
        device_map={"": 0},
        quantization_config=quant,
        dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
        attn_implementation="sdpa",
    ).eval()
    if not str(next(target.parameters()).device).startswith("cuda"):
        raise RuntimeError("Target device fallback")
    record["target_load_seconds"] = time.perf_counter() - load_start

    draft_start = time.perf_counter()
    draft_pipe = ov_genai.LLMPipeline(DRAFT, "CPU")
    record["draft_compile_seconds"] = time.perf_counter() - draft_start

    torch.cuda.reset_peak_memory_stats()
    reference_start = time.perf_counter()
    reference = target_reference(target, prompt, args.output_tokens)
    torch.cuda.synchronize()
    record["reference_seconds"] = time.perf_counter() - reference_start

    speculative_start = time.perf_counter()
    proposed, rounds = speculative(target, draft_pipe, prompt, args.output_tokens, args.k)
    torch.cuda.synchronize()
    record["speculative_seconds"] = time.perf_counter() - speculative_start
    record["reference_token_ids"] = reference
    record["speculative_token_ids"] = proposed
    record["reference_sha256"] = digest(reference)
    record["speculative_sha256"] = digest(proposed)
    record["exact_match"] = proposed == reference
    record["rounds"] = rounds
    record["draft_tokens_offered"] = sum(item["offered"] for item in rounds)
    record["draft_tokens_accepted"] = sum(item["accepted"] for item in rounds)
    record["acceptance_rate"] = record["draft_tokens_accepted"] / record["draft_tokens_offered"]
    record["peak_cuda_allocated_gib"] = torch.cuda.max_memory_allocated() / 1024**3
    record["ended"] = iso_now()
    record["status"] = "PASS" if record["exact_match"] else "FAIL"
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: record[key] for key in (
        "status", "k", "exact_match", "reference_sha256", "speculative_sha256",
        "draft_tokens_offered", "draft_tokens_accepted", "acceptance_rate",
        "reference_seconds", "speculative_seconds", "peak_cuda_allocated_gib",
    )}, indent=2))
    raise SystemExit(0 if record["exact_match"] else 2)


if __name__ == "__main__":
    main()
