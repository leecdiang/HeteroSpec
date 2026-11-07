import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import openvino as ov
import openvino_genai as ov_genai


def iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--device", choices=["CPU", "GPU.0", "NPU"], default="NPU")
    parser.add_argument("--compiler", choices=["PREFER_PLUGIN", "PLUGIN", "DRIVER"], default="PREFER_PLUGIN")
    parser.add_argument("--max-prompt-len", type=int, default=128)
    parser.add_argument("--max-new-tokens", type=int, default=1)
    parser.add_argument("--repetitions", type=int, default=1)
    args = parser.parse_args()

    core = ov.Core()
    if args.device not in core.available_devices:
        raise RuntimeError(f"{args.device} is not available; fallback forbidden")

    record = {
        "started": iso(),
        "openvino": ov.__version__,
        "model": str(Path(args.model).resolve()),
        "requested_device": args.device,
        "compiler_requested": args.compiler if args.device == "NPU" else None,
        "max_prompt_len": args.max_prompt_len,
        "max_new_tokens": args.max_new_tokens,
        "repetitions": args.repetitions,
        "full_device_name": core.get_property(args.device, "FULL_DEVICE_NAME"),
        "npu_driver": str(core.get_property("NPU", "NPU_DRIVER_VERSION")) if args.device == "NPU" else None,
        "status": "STARTED",
    }
    print(json.dumps(record, ensure_ascii=False), flush=True)

    t0 = time.perf_counter()
    properties = {}
    if args.device == "NPU":
        properties["MAX_PROMPT_LEN"] = args.max_prompt_len
        properties["MIN_RESPONSE_LEN"] = max(1, args.max_new_tokens)
        properties["NPU_COMPILER_TYPE"] = args.compiler
    pipe = ov_genai.LLMPipeline(args.model, args.device, **properties)
    record["compile_seconds"] = time.perf_counter() - t0

    cfg = ov_genai.GenerationConfig()
    cfg.max_new_tokens = args.max_new_tokens
    cfg.do_sample = False
    cfg.ignore_eos = True
    prompt = "State one fact about reproducible experiments."
    results = []
    for repetition in range(1, args.repetitions + 1):
        t1 = time.perf_counter()
        result = str(pipe.generate(prompt, cfg))
        results.append({
            "repetition": repetition,
            "generation_seconds": time.perf_counter() - t1,
            "output": result,
            "output_sha256": hashlib.sha256(result.encode("utf-8")).hexdigest(),
        })
    record.update(
        ended=iso(),
        status="PASS",
        results=results,
        deterministic=len({item["output_sha256"] for item in results}) == 1,
    )
    print(json.dumps(record, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
