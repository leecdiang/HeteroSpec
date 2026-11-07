import argparse
import csv
import hashlib
import json
import os
import platform
import socket
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openvino as ov
import openvino_genai as ov_genai
import psutil
import ittapi


ROOT = Path(os.environ.get("HETEROSPEC_ROOT", Path(__file__).resolve().parents[1]))
MODEL_DIR = ROOT / "models" / "qwen3-0.6b-int4-ov"
MANIFEST_PATH = ROOT / "env" / "qwen3-0.6b-int4-ov-manifest.json"
BASE_TEXT = (
    "Heterogeneous computing assigns work to processors with different strengths. "
    "A reproducible experiment records every configuration, timestamp, and device name. "
    "Correctness is checked before performance, and raw measurements are never discarded. "
    "Candidate tokens are verified in order, while timing and energy remain separate measurements. "
)
ITT_DOMAIN = ittapi.domain("HeteroSpec-PC")


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


def pair(value):
    return {"mean": float(value.mean), "std": float(value.std)}


def tokenized_context(tokenizer, length):
    text = BASE_TEXT * (length // 30 + 20)
    encoded = tokenizer.encode(text, add_special_tokens=False)
    ids = np.array(encoded.input_ids.data, copy=True, dtype=np.int64).reshape(-1)
    if ids.size < length:
        raise RuntimeError(f"Unable to construct {length} tokens; only {ids.size} available")
    ids = ids[:length].reshape(1, -1)
    mask = np.ones_like(ids, dtype=np.int64)
    digest = hashlib.sha256(ids.tobytes()).hexdigest()
    return ov_genai.TokenizedInputs(ov.Tensor(ids), ov.Tensor(mask)), digest


def generation_config(output_tokens):
    config = ov_genai.GenerationConfig()
    config.max_new_tokens = output_tokens
    config.min_new_tokens = output_tokens
    config.ignore_eos = True
    config.do_sample = False
    config.apply_chat_template = False
    return config


def execute(pipe, inputs, config, marker_name):
    start_utc = now_iso()
    start_perf_ns = time.perf_counter_ns()
    rss_start = psutil.Process().memory_info().rss
    with ittapi.task(marker_name, domain=ITT_DOMAIN):
        result = pipe.generate(inputs, config)
    end_perf_ns = time.perf_counter_ns()
    end_utc = now_iso()
    rss_end = psutil.Process().memory_info().rss
    metrics = result.perf_metrics
    raw = metrics.raw_metrics
    token_ids = [int(value) for value in result.tokens[0]]
    return {
        "start_utc": start_utc,
        "end_utc": end_utc,
        "start_perf_counter_ns": start_perf_ns,
        "end_perf_counter_ns": end_perf_ns,
        "host_completion_time_ms": (end_perf_ns - start_perf_ns) / 1e6,
        "rss_start_mb": rss_start / 1024**2,
        "rss_end_mb": rss_end / 1024**2,
        "input_tokens": int(metrics.get_num_input_tokens()),
        "output_tokens": int(metrics.get_num_generated_tokens()),
        "ttft_ms": pair(metrics.get_ttft()),
        "tpot_ms": pair(metrics.get_tpot()),
        "throughput_tokens_s": pair(metrics.get_throughput()),
        "generate_duration_ms": pair(metrics.get_generate_duration()),
        "inference_duration_ms": pair(metrics.get_inference_duration()),
        "tokenization_duration_ms": pair(metrics.get_tokenization_duration()),
        "detokenization_duration_ms": pair(metrics.get_detokenization_duration()),
        "sampling_duration_ms": pair(metrics.get_sampling_duration()),
        "token_ids": token_ids,
        "token_ids_sha256": hashlib.sha256(np.asarray(token_ids, dtype=np.int64).tobytes()).hexdigest(),
        "raw_metrics": {
            "new_token_times_ms_monotonic": [float(x) for x in raw.m_new_token_times],
            "token_infer_durations_us": [float(x) for x in raw.token_infer_durations],
            "inter_token_durations_us": [float(x) for x in raw.m_durations],
            "sampling_durations_us": [float(x) for x in raw.sampling_durations],
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", required=True, choices=["CPU", "GPU.0"])
    parser.add_argument("--contexts", default="512,2048,8192")
    parser.add_argument("--output-tokens", type=int, default=128)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--warmup-max", type=int, default=5)
    parser.add_argument("--stability-pct", type=float, default=5.0)
    args = parser.parse_args()

    contexts = [int(value) for value in args.contexts.split(",")]
    date_dir = datetime.now().strftime("%Y-%m-%d")
    device_slug = args.device.replace(".", "_")
    base_dir = ROOT / "runs" / date_dir / "qwen3" / "DRAFT-QUAL" / device_slug
    base_dir.mkdir(parents=True, exist_ok=True)
    model_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    session = {
        "session_id": f"p1-{device_slug}-{datetime.now().strftime('%Y%m%dT%H%M%S')}",
        "started": now_iso(),
        "device_requested": args.device,
        "device_actual": None,
        "available_devices": list(ov.Core().available_devices),
        "model_repo": model_manifest["repo_id"],
        "model_revision": model_manifest["resolved_revision"],
        "model_total_bytes": model_manifest["total_bytes"],
        "python": platform.python_version(),
        "openvino": ov.__version__,
        "openvino_genai": ov_genai.get_version(),
        "host": socket.gethostname(),
        "contexts": contexts,
        "output_tokens": args.output_tokens,
        "repetitions": args.repetitions,
        "warmup_policy": "always 3; continue to max 5 while warmup #2 vs #3/latest pair differs by >5%",
        "valid": False,
        "error": None,
        "cells": [],
    }
    log_path = ROOT / "logs" / f"phase1-qualification-{session['session_id']}.json"

    try:
        core = ov.Core()
        if args.device not in core.available_devices:
            raise RuntimeError(f"Requested device {args.device} is unavailable")
        session["device_actual"] = core.get_property(args.device, "FULL_DEVICE_NAME")
        tokenizer = ov_genai.Tokenizer(MODEL_DIR)
        prepared = {context: tokenized_context(tokenizer, context) for context in contexts}

        load_start = time.perf_counter_ns()
        pipe = ov_genai.LLMPipeline(MODEL_DIR, args.device, PERFORMANCE_HINT="LATENCY")
        session["host_load_ms"] = (time.perf_counter_ns() - load_start) / 1e6
        config = generation_config(args.output_tokens)

        for context in contexts:
            inputs, prompt_hash = prepared[context]
            cell = {
                "context_tokens": context,
                "prompt_token_ids_sha256": prompt_hash,
                "warmups": [],
                "measured_run_ids": [],
                "warmup_stable": False,
            }
            for warmup_index in range(1, args.warmup_max + 1):
                warm = execute(pipe, inputs, config, f"warmup|{device_slug}|c{context}|w{warmup_index}")
                cell["warmups"].append({
                    "index": warmup_index,
                    "throughput_tokens_s": warm["throughput_tokens_s"]["mean"],
                    "ttft_ms": warm["ttft_ms"]["mean"],
                    "tpot_ms": warm["tpot_ms"]["mean"],
                    "token_ids_sha256": warm["token_ids_sha256"],
                })
                if warmup_index >= 3:
                    previous = cell["warmups"][-2]["throughput_tokens_s"]
                    current = cell["warmups"][-1]["throughput_tokens_s"]
                    difference = abs(current - previous) / ((current + previous) / 2) * 100
                    cell["warmup_last_pair_diff_pct"] = difference
                    if difference <= args.stability_pct:
                        cell["warmup_stable"] = True
                        break

            for repetition in range(1, args.repetitions + 1):
                run_id = f"p1-{device_slug}-c{context}-r{repetition}-{uuid.uuid4().hex[:8]}"
                run_dir = base_dir / f"context_{context}" / run_id
                run_dir.mkdir(parents=True, exist_ok=False)
                run = execute(pipe, inputs, config, f"run|{run_id}")
                valid = run["input_tokens"] == context and run["output_tokens"] == args.output_tokens
                meta = {
                    "run_id": run_id,
                    "phase": "P1",
                    "model_pair": "qwen",
                    "config": "DRAFT-QUAL",
                    "prompt_id": f"fixed-context-{context}",
                    "draft_model": model_manifest["repo_id"],
                    "draft_revision": model_manifest["resolved_revision"],
                    "draft_device_requested": args.device,
                    "draft_device_actual": session["device_actual"],
                    "draft_precision": "INT4_ASYM_ratio0.8_group128_OpenVINO",
                    "input_tokens": context,
                    "max_new_tokens": args.output_tokens,
                    "repetition": repetition,
                    "warmup_count": len(cell["warmups"]),
                    "warmup_stable": cell["warmup_stable"],
                    "prompt_token_ids_sha256": prompt_hash,
                    "telemetry_trace_prefix": os.environ.get("HETEROSPEC_TELEMETRY_PREFIX"),
                    "start_utc": run["start_utc"],
                    "end_utc": run["end_utc"],
                    "start_perf_counter_ns": run["start_perf_counter_ns"],
                    "end_perf_counter_ns": run["end_perf_counter_ns"],
                    "valid": valid,
                    "invalid_reason": None if valid else "token_count_mismatch",
                }
                (run_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
                (run_dir / "result.json").write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
                with (run_dir / "generation.jsonl").open("w", encoding="utf-8") as stream:
                    token_times = run["raw_metrics"]["new_token_times_ms_monotonic"]
                    for token_index, token_id in enumerate(run["token_ids"]):
                        stream.write(json.dumps({
                            "token_index": token_index,
                            "token_id": token_id,
                            "emit_monotonic_ms": token_times[token_index] if token_index < len(token_times) else None,
                        }) + "\n")
                cell["measured_run_ids"].append(run_id)
            session["cells"].append(cell)

        session["valid"] = True
    except Exception as exc:
        session["error"] = f"{type(exc).__name__}: {exc}"
        session["traceback"] = traceback.format_exc()
    finally:
        session["ended"] = now_iso()
        log_path.write_text(json.dumps(session, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(session, indent=2, ensure_ascii=False))

    raise SystemExit(0 if session["valid"] else 2)


if __name__ == "__main__":
    main()
