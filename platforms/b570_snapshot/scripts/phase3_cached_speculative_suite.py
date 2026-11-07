import os
import argparse
import hashlib
import json
import time
from contextlib import contextmanager, nullcontext
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
ATTENTION_BACKEND = "cudnn"
PROMPTS = {
    "reproducibility": "Reproducible experiments fix inputs, software versions, devices, and measurement methods. ",
    "heterogeneous": "Heterogeneous systems assign each workload to the processor whose characteristics fit it best. ",
    "verification": "A target language model must verify every candidate proposed by a smaller draft model. ",
    "translation_de": "Translate into English: Die Wissenschaft lebt von überprüfbaren Ergebnissen.",
    "translation_zh": "将下面这句话翻译成英文：可靠的实验必须能够被独立复现。",
    "summary": "Summarize in one sentence: A laptop combines a CPU, integrated GPU, NPU, and discrete GPU, each with different latency and throughput characteristics.",
    "qa_science": "Why does water boil at a lower temperature at high altitude? Answer briefly.",
    "qa_history": "What was the main purpose of the printing press? Answer in two sentences.",
    "reasoning": "A box contains 7 red, 5 blue, and 8 green balls. How many are not blue?",
    "arithmetic": "Compute 17 * 23 and explain the calculation concisely.",
    "code_python": "Write a Python function that returns the median of a non-empty list without modifying it.",
    "code_debug": "Find the bug: def square_sum(xs): return sum(x for x in xs) ** 2",
    "json": "Return JSON with keys name, value, and valid for the measurement latency=12.5 ms.",
    "punctuation": "Explain the difference between '-', '–', and '—'.",
    "mixed": "设备 GPU.0 processed 128 tokens in 1.25 s; calculate tok/s.",
    "instruction": "List three practical steps for keeping benchmark conditions consistent.",
    "creative": "Write a two-line description of a quiet computer laboratory at midnight.",
    "comparison": "Compare latency and throughput without assuming that higher throughput always means lower latency.",
    "safety": "Explain why raw power domains should not be added when their measurement boundaries overlap.",
    "edge_text": "Continue this pattern exactly: A1, b2, C3, d4,",
}


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


def sha(ids):
    return hashlib.sha256(np.asarray(ids, dtype=np.int64).tobytes()).hexdigest()


@contextmanager
def cudnn():
    if ATTENTION_BACKEND == "cudnn":
        with sdpa_kernel(SDPBackend.CUDNN_ATTENTION):
            yield
    elif ATTENTION_BACKEND == "math":
        with sdpa_kernel(SDPBackend.MATH):
            yield
    else:
        with nullcontext():
            yield


def ov_input(ids):
    array = np.asarray(ids, dtype=np.int64).reshape(1, -1)
    return ov_genai.TokenizedInputs(ov.Tensor(array), ov.Tensor(np.ones_like(array)))


def propose(pipe, prefix, count):
    if hasattr(pipe, "propose"):
        return pipe.propose(prefix, count)
    cfg = ov_genai.GenerationConfig()
    cfg.max_new_tokens = count
    cfg.do_sample = False
    cfg.ignore_eos = True
    result = pipe.generate(ov_input(prefix), cfg)
    return [int(token) for token in result.tokens[0]]


def forward(model, ids, past=None):
    tensor = torch.tensor([ids], dtype=torch.long, device="cuda:0")
    with torch.inference_mode(), cudnn():
        result = model(input_ids=tensor, past_key_values=past, use_cache=True)
    return result.logits, result.past_key_values


def cached_reference(model, prompt, count, eos_ids):
    logits, cache = forward(model, prompt)
    next_token = int(logits[0, -1].argmax())
    output = []
    for index in range(count):
        output.append(next_token)
        if next_token in eos_ids:
            break
        if index + 1 < count:
            logits, cache = forward(model, [next_token], cache)
            next_token = int(logits[0, -1].argmax())
    torch.cuda.synchronize()
    return output


def cached_speculative(model, draft, prompt, count, k, eos_ids, verification_margin):
    logits, cache = forward(model, prompt)
    next_logits = logits[0, -1]
    sequence = list(prompt)
    generated = []
    rounds = []
    while len(generated) < count:
        offered = min(k, count - len(generated))
        d0 = time.perf_counter()
        candidates = propose(draft, sequence, offered)
        draft_ms = (time.perf_counter() - d0) * 1000

        prefix_length = len(sequence)
        t0 = time.perf_counter()
        candidate_logits, candidate_cache = forward(model, candidates, cache)
        predictions = [int(next_logits.argmax())]
        first_top2 = torch.topk(next_logits.float(), 2).values
        margins = [float(first_top2[0] - first_top2[1])]
        if len(candidates) > 1:
            predictions.extend(candidate_logits[0, :-1].argmax(dim=-1).tolist())
            top2 = torch.topk(candidate_logits[0, :-1].float(), 2, dim=-1).values
            margins.extend((top2[:, 0] - top2[:, 1]).tolist())
        bonus_prediction = int(candidate_logits[0, -1].argmax())

        if min(margins) <= verification_margin:
            # Quantized GEMMs can flip near-tied argmax decisions when sequence width changes.
            # Recreate the canonical one-token cache path only for these ambiguous blocks.
            del cache, candidate_cache, candidate_logits
            torch.cuda.empty_cache()
            canonical_logits, canonical_cache = forward(model, sequence)
            canonical_next = canonical_logits[0, -1]
            accepted = 0
            mismatch = None
            for index, candidate in enumerate(candidates):
                prediction = int(canonical_next.argmax())
                if candidate != prediction:
                    mismatch = index
                    correction = prediction
                    break
                accepted += 1
                step_logits, canonical_cache = forward(model, [candidate], canonical_cache)
                canonical_next = step_logits[0, -1]
            else:
                correction = None

            generated.extend(candidates[:accepted])
            sequence.extend(candidates[:accepted])
            bonus = None
            if any(token in eos_ids for token in candidates[:accepted]):
                eos_at = next(i for i, token in enumerate(candidates[:accepted]) if token in eos_ids)
                trim = accepted - eos_at - 1
                if trim:
                    generated = generated[:-trim]
                    sequence = sequence[:-trim]
            elif mismatch is not None and len(generated) < count:
                generated.append(correction)
                sequence.append(correction)
                if correction not in eos_ids and len(generated) < count:
                    correction_logits, cache = forward(model, [correction], canonical_cache)
                    next_logits = correction_logits[0, -1]
                else:
                    cache = canonical_cache
            else:
                cache = canonical_cache
                next_logits = canonical_next
                if len(generated) < count:
                    bonus = int(canonical_next.argmax())
                    generated.append(bonus)
                    sequence.append(bonus)
                    if bonus not in eos_ids and len(generated) < count:
                        bonus_logits, cache = forward(model, [bonus], cache)
                        next_logits = bonus_logits[0, -1]
            torch.cuda.synchronize()
            rounds.append({
                "offered": len(candidates), "accepted": accepted,
                "mismatch_index": mismatch, "correction_token": correction,
                "bonus_token": bonus, "draft_ms": draft_ms,
                "target_ms": (time.perf_counter() - t0) * 1000,
                "verification_margins": margins, "precision_guard": True,
            })
            if generated and generated[-1] in eos_ids:
                break
            continue

        accepted = 0
        mismatch = None
        for index, candidate in enumerate(candidates):
            if candidate != predictions[index]:
                mismatch = index
                break
            accepted += 1

        remaining = count - len(generated)
        correction = None
        bonus = None
        if mismatch is not None:
            accepted_tokens = candidates[:mismatch]
            generated.extend(accepted_tokens)
            sequence.extend(accepted_tokens)
            if any(token in eos_ids for token in accepted_tokens):
                stop = accepted_tokens.index(next(token for token in accepted_tokens if token in eos_ids)) + 1
                generated = generated[:len(generated) - len(accepted_tokens) + stop]
                sequence = sequence[:len(sequence) - len(accepted_tokens) + stop]
                rounds.append({"offered": len(candidates), "accepted": stop, "mismatch_index": None, "correction_token": None, "bonus_token": None, "draft_ms": draft_ms, "target_ms": 0.0, "stopped_on_eos": True})
                break
            correction = predictions[mismatch]
            if len(generated) < count:
                generated.append(correction)
                sequence.append(correction)
            if correction in eos_ids:
                rounds.append({"offered": len(candidates), "accepted": accepted, "mismatch_index": mismatch, "correction_token": correction, "bonus_token": None, "draft_ms": draft_ms, "target_ms": (time.perf_counter() - t0) * 1000, "stopped_on_eos": True})
                break
            # Discard the mismatching token and all later speculative cache entries.
            candidate_cache.crop(-(len(candidates) - mismatch))
            if len(generated) < count:
                correction_logits, cache = forward(model, [correction], candidate_cache)
                next_logits = correction_logits[0, -1]
            else:
                cache = candidate_cache
        else:
            take = min(len(candidates), remaining)
            generated.extend(candidates[:take])
            sequence.extend(candidates[:take])
            eos_positions = [index for index, token in enumerate(candidates[:take]) if token in eos_ids]
            if eos_positions:
                keep = eos_positions[0] + 1
                generated = generated[:len(generated) - take + keep]
                sequence = sequence[:len(sequence) - take + keep]
                rounds.append({"offered": len(candidates), "accepted": keep, "mismatch_index": None, "correction_token": None, "bonus_token": None, "draft_ms": draft_ms, "target_ms": (time.perf_counter() - t0) * 1000, "stopped_on_eos": True})
                break
            cache = candidate_cache
            next_logits = candidate_logits[0, -1]
            if take == len(candidates) and len(generated) < count:
                bonus = bonus_prediction
                generated.append(bonus)
                sequence.append(bonus)
                if bonus in eos_ids:
                    rounds.append({"offered": len(candidates), "accepted": accepted, "mismatch_index": None, "correction_token": None, "bonus_token": bonus, "draft_ms": draft_ms, "target_ms": (time.perf_counter() - t0) * 1000, "stopped_on_eos": True})
                    break
                bonus_logits, cache = forward(model, [bonus], cache)
                next_logits = bonus_logits[0, -1]
        torch.cuda.synchronize()
        target_ms = (time.perf_counter() - t0) * 1000
        rounds.append({
            "offered": len(candidates), "accepted": accepted,
            "mismatch_index": mismatch, "correction_token": correction,
            "bonus_token": bonus, "draft_ms": draft_ms, "target_ms": target_ms,
            "verification_margins": margins,
        })
    return generated[:count], rounds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contexts", default="64,128")
    parser.add_argument("--ks", default="1,2,4,8")
    parser.add_argument("--output-tokens", type=int, default=32)
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--prompt-limit", type=int, default=20)
    parser.add_argument("--natural-prompts", action="store_true")
    parser.add_argument("--chat-template", action="store_true")
    parser.add_argument("--verification-margin", type=float, default=0.5)
    parser.add_argument("--target-compute-dtype", choices=["bf16", "fp32"], default="bf16")
    parser.add_argument("--target-attention", choices=["cudnn", "math", "eager"], default="cudnn")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    contexts = [int(value) for value in args.contexts.split(",")]
    ks = [int(value) for value in args.ks.split(",")]
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable; fallback forbidden")
    core = ov.Core()
    if "CPU" not in core.available_devices:
        raise RuntimeError("OpenVINO CPU unavailable; fallback forbidden")

    global ATTENTION_BACKEND
    ATTENTION_BACKEND = args.target_attention
    record = {
        "started": now(), "status": "STARTED", "implementation": "cached-greedy-speculative-v1",
        "contexts": contexts, "ks": ks, "output_tokens": args.output_tokens,
        "repetitions": args.repetitions, "natural_prompts": args.natural_prompts,
        "chat_template": args.chat_template, "verification_margin": args.verification_margin,
        "target_compute_dtype": args.target_compute_dtype,
        "draft_device": "CPU",
        "draft_device_name": core.get_property("CPU", "FULL_DEVICE_NAME"),
        "target_device": "cuda:0", "target_device_name": torch.cuda.get_device_name(0),
        "target_attention_backend": args.target_attention, "cases": [],
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    tokenizer = AutoTokenizer.from_pretrained(TARGET, local_files_only=True)
    compute_dtype = torch.bfloat16 if args.target_compute_dtype == "bf16" else torch.float32
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=compute_dtype, bnb_4bit_use_double_quant=True)
    load = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(
        TARGET, local_files_only=True, device_map={"": 0}, quantization_config=quant,
        dtype=compute_dtype, low_cpu_mem_usage=True, attn_implementation=("eager" if args.target_attention == "eager" else "sdpa"),
    ).eval()
    record["target_load_seconds"] = time.perf_counter() - load
    if not str(next(model.parameters()).device).startswith("cuda"):
        raise RuntimeError("Target fallback")
    compile_start = time.perf_counter()
    draft = ov_genai.LLMPipeline(DRAFT, "CPU")
    record["draft_compile_seconds"] = time.perf_counter() - compile_start

    eos_ids = {tokenizer.eos_token_id}
    selected_prompts = list(PROMPTS.items())[:args.prompt_limit]
    for prompt_id, text in selected_prompts:
        for requested_context in ([None] if args.natural_prompts else contexts):
            if args.chat_template:
                prompt = tokenizer.apply_chat_template([{"role": "user", "content": text}], tokenize=True, add_generation_prompt=True, enable_thinking=False)
                if isinstance(prompt, str):
                    prompt = tokenizer(prompt, add_special_tokens=False).input_ids
                elif hasattr(prompt, "input_ids"):
                    prompt = prompt.input_ids
            else:
                prompt = tokenizer(text, add_special_tokens=False).input_ids
            if requested_context is not None:
                prompt = tokenizer(text * (requested_context // 10 + 10), add_special_tokens=False).input_ids[:requested_context]
                if len(prompt) != requested_context:
                    raise RuntimeError("Exact prompt construction failed")
            context = len(prompt)
            reference_start = time.perf_counter()
            reference = cached_reference(model, prompt, args.output_tokens, eos_ids)
            reference_seconds = time.perf_counter() - reference_start
            for k in ks:
                for repetition in range(1, args.repetitions + 1):
                    torch.cuda.reset_peak_memory_stats()
                    started = time.perf_counter()
                    result, rounds = cached_speculative(model, draft, prompt, args.output_tokens, k, eos_ids, args.verification_margin)
                    seconds = time.perf_counter() - started
                    case = {
                        "prompt_id": prompt_id, "context_tokens": context, "prompt_sha256": sha(prompt),
                        "k": k, "repetition": repetition, "reference_sha256": sha(reference),
                        "result_sha256": sha(result), "exact_match": result == reference,
                        "reference_token_ids": reference, "result_token_ids": result,
                        "reference_seconds": reference_seconds, "speculative_seconds": seconds,
                        "rounds": rounds, "offered": sum(r["offered"] for r in rounds),
                        "accepted": sum(r["accepted"] for r in rounds),
                        "peak_cuda_allocated_gib": torch.cuda.max_memory_allocated() / 1024**3,
                    }
                    case["acceptance_rate"] = case["accepted"] / case["offered"]
                    record["cases"].append(case)
                    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                    if not case["exact_match"]:
                        record.update(status="FAIL", ended=now())
                        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                        raise RuntimeError(f"Exactness failure: {prompt_id}, context={context}, k={k}, repetition={repetition}")

    record["status"] = "PASS"
    record["ended"] = now()
    record["exact_matches"] = sum(case["exact_match"] for case in record["cases"])
    record["peak_cuda_allocated_gib"] = max(case["peak_cuda_allocated_gib"] for case in record["cases"])
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": record["status"], "cases": len(record["cases"]),
        "exact_matches": record["exact_matches"],
        "peak_cuda_allocated_gib": record["peak_cuda_allocated_gib"], "output": str(path),
    }, indent=2))


if __name__ == "__main__":
    main()
