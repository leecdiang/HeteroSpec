import os
import argparse
import json
import platform
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openvino as ov
import openvino_genai as ov_genai


ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
MODEL_DIR = ROOT / "models" / "qwen3-0.6b-int4-ov"
BASE_TEXT = (
    "Heterogeneous computing assigns work to processors with different strengths. "
    "A reproducible experiment records every configuration, timestamp, and device name. "
    "Correctness is checked before performance, and raw measurements are never discarded. "
)


def pair_value(value):
    return {"mean": float(value.mean), "std": float(value.std)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", required=True, choices=["CPU", "GPU.0", "NPU"])
    parser.add_argument("--context", type=int, default=64)
    parser.add_argument("--output", type=int, default=8)
    args = parser.parse_args()

    record = {
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
        "device_requested": args.device,
        "device_actual": None,
        "context_tokens": args.context,
        "output_tokens_requested": args.output,
        "model_dir": str(MODEL_DIR),
        "python": platform.python_version(),
        "openvino": ov.__version__,
        "openvino_genai": ov_genai.get_version(),
        "valid": False,
        "error": None,
    }
    result_path = ROOT / "logs" / f"phase1-smoke-{args.device.replace('.', '_')}.json"

    try:
        core = ov.Core()
        available = list(core.available_devices)
        if args.device not in available:
            raise RuntimeError(f"Requested device {args.device} not in {available}")
        record["device_actual"] = core.get_property(args.device, "FULL_DEVICE_NAME")

        tokenizer = ov_genai.Tokenizer(MODEL_DIR)
        repeated = BASE_TEXT * (args.context // 20 + 10)
        encoded = tokenizer.encode(repeated, add_special_tokens=False)
        all_ids = np.array(encoded.input_ids.data, copy=True, dtype=np.int64).reshape(-1)
        if all_ids.size < args.context:
            raise RuntimeError(f"Only produced {all_ids.size} input tokens")
        input_ids = all_ids[: args.context].reshape(1, -1)
        attention = np.ones_like(input_ids, dtype=np.int64)
        tokenized = ov_genai.TokenizedInputs(ov.Tensor(input_ids), ov.Tensor(attention))

        load_start = time.perf_counter_ns()
        pipe = ov_genai.LLMPipeline(MODEL_DIR, args.device, PERFORMANCE_HINT="LATENCY")
        record["host_load_ms"] = (time.perf_counter_ns() - load_start) / 1e6

        config = ov_genai.GenerationConfig()
        config.max_new_tokens = args.output
        config.min_new_tokens = args.output
        config.ignore_eos = True
        config.do_sample = False
        config.apply_chat_template = False

        start = time.perf_counter_ns()
        result = pipe.generate(tokenized, config)
        record["host_generate_ms"] = (time.perf_counter_ns() - start) / 1e6
        metrics = result.perf_metrics
        record["metrics"] = {
            "input_tokens": int(metrics.get_num_input_tokens()),
            "generated_tokens": int(metrics.get_num_generated_tokens()),
            "load_time_ms": float(metrics.get_load_time()),
            "generate_duration_ms": pair_value(metrics.get_generate_duration()),
            "inference_duration_ms": pair_value(metrics.get_inference_duration()),
            "ttft_ms": pair_value(metrics.get_ttft()),
            "tpot_ms": pair_value(metrics.get_tpot()),
            "throughput_tokens_s": pair_value(metrics.get_throughput()),
        }
        record["generated_token_ids"] = [int(x) for x in result.tokens[0]]
        if record["metrics"]["input_tokens"] != args.context:
            raise RuntimeError(f"Input token mismatch: {record['metrics']['input_tokens']}")
        if record["metrics"]["generated_tokens"] != args.output:
            raise RuntimeError(f"Output token mismatch: {record['metrics']['generated_tokens']}")
        record["valid"] = True
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc()
    finally:
        result_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(record, indent=2, ensure_ascii=False))

    raise SystemExit(0 if record["valid"] else 2)


if __name__ == "__main__":
    main()
