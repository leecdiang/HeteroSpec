import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openvino as ov
import openvino_genai as ov_genai


BASE_TEXT = (
    "Reproducible experiments fix software versions, inputs, device selection, "
    "randomness, and measurement procedure. Results retain raw data and metadata. "
)


def iso_now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


def tokenized_context(tokenizer, length):
    encoded = tokenizer.encode(BASE_TEXT * (length // 20 + 10), add_special_tokens=False)
    ids = np.asarray(encoded.input_ids.data, dtype=np.int64).reshape(-1)[:length]
    if ids.size != length:
        raise RuntimeError(f"Could not construct exactly {length} tokens")
    mask = np.ones_like(ids, dtype=np.int64)
    digest = hashlib.sha256(ids.tobytes()).hexdigest()
    return ov_genai.TokenizedInputs(ov.Tensor(ids.reshape(1, -1)), ov.Tensor(mask.reshape(1, -1))), digest


def generate_once(pipe, inputs, cfg):
    start = iso_now()
    t0 = time.perf_counter()
    result = pipe.generate(inputs, cfg)
    elapsed = time.perf_counter() - t0
    token_ids = [int(value) for value in result.tokens[0]]
    return {
        "started": start,
        "ended": iso_now(),
        "seconds": elapsed,
        "output_tokens": len(token_ids),
        "token_ids": token_ids,
        "token_ids_sha256": hashlib.sha256(np.asarray(token_ids, dtype=np.int64).tobytes()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--device", required=True, choices=["CPU", "GPU.0", "NPU"])
    parser.add_argument("--contexts", default="32,64,128")
    parser.add_argument("--output-tokens", type=int, default=32)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--npu-compiler", choices=["PREFER_PLUGIN", "PLUGIN", "DRIVER"], default="PREFER_PLUGIN")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    contexts = [int(value) for value in args.contexts.split(",")]
    core = ov.Core()
    if args.device not in core.available_devices:
        raise RuntimeError(f"Requested device {args.device} unavailable; fallback forbidden")

    record = {
        "started": iso_now(),
        "status": "STARTED",
        "model": str(Path(args.model).resolve()),
        "openvino": ov.__version__,
        "requested_device": args.device,
        "full_device_name": core.get_property(args.device, "FULL_DEVICE_NAME"),
        "available_devices_at_start": list(core.available_devices),
        "contexts": contexts,
        "output_tokens": args.output_tokens,
        "warmups": args.warmups,
        "repetitions": args.repetitions,
        "npu_compiler": args.npu_compiler if args.device == "NPU" else None,
        "cells": [],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2), encoding="utf-8")

    properties = {}
    if args.device == "NPU":
        properties.update(
            MAX_PROMPT_LEN=max(contexts),
            MIN_RESPONSE_LEN=args.output_tokens,
            NPU_COMPILER_TYPE=args.npu_compiler,
        )
    compile_start = time.perf_counter()
    pipe = ov_genai.LLMPipeline(args.model, args.device, **properties)
    record["compile_seconds"] = time.perf_counter() - compile_start
    tokenizer = ov_genai.Tokenizer(args.model)

    cfg = ov_genai.GenerationConfig()
    cfg.max_new_tokens = args.output_tokens
    cfg.do_sample = False
    cfg.ignore_eos = True

    for context in contexts:
        inputs, prompt_hash = tokenized_context(tokenizer, context)
        cell = {"context_tokens": context, "prompt_token_ids_sha256": prompt_hash, "warmup": [], "runs": []}
        for index in range(1, args.warmups + 1):
            item = generate_once(pipe, inputs, cfg)
            item["index"] = index
            cell["warmup"].append(item)
        for repetition in range(1, args.repetitions + 1):
            item = generate_once(pipe, inputs, cfg)
            item["repetition"] = repetition
            cell["runs"].append(item)
        cell["valid"] = all(item["output_tokens"] == args.output_tokens for item in cell["runs"])
        cell["unique_token_hashes"] = len({item["token_ids_sha256"] for item in cell["runs"]})
        cell["mean_seconds"] = sum(item["seconds"] for item in cell["runs"]) / len(cell["runs"])
        cell["throughput_tokens_s"] = args.output_tokens / cell["mean_seconds"]
        record["cells"].append(cell)
        output.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    record["ended"] = iso_now()
    record["status"] = "PASS" if all(cell["valid"] for cell in record["cells"]) else "FAIL"
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": record["status"],
        "device": args.device,
        "compile_seconds": record["compile_seconds"],
        "cells": [{k: c[k] for k in ("context_tokens", "valid", "unique_token_hashes", "mean_seconds", "throughput_tokens_s")} for c in record["cells"]],
        "output": str(output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
