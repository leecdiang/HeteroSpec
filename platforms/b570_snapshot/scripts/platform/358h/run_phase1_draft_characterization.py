#!/usr/bin/env python3
"""Fail-closed Phase-1 runner for the frozen 358H CPU/NPU draft comparison.

This program cannot execute while Phase 0 or preregistration is unfinished. Merely
invoking --check performs no model inference and records no performance data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import socket
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openvino as ov
import openvino_genai as ov_genai
import psutil

ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / "runs/358h/qualification/phase0_gate.json"
PREREG = ROOT / "benchmarks/358h_threshold_validation/preregistration_v1.json"
MODEL = ROOT / "models/openvino/qwen3-0.6b-6130ef-int4-sym-g128"
BASE_TEXT = (
    "Heterogeneous computing assigns work to processors with different strengths. "
    "A reproducible experiment records every configuration, timestamp, and device name. "
    "Correctness is checked before performance, and raw measurements are never discarded. "
    "Candidate tokens are verified in order, while timing and energy remain separate measurements. "
)
EXPECTED_IR = {
    "openvino_model.xml": "fc8ad94dbecfc0c45cf3db4f0624344d2bea2cdd6997e0b45ca52d4f7baa1103",
    "openvino_model.bin": "2e129cffb1a7239007a3df27e0f3f7bb12f65a40e5c9b1e24a250d952da47837",
}
NPU_CACHE = ROOT / 'runs/358h/qualification_ac_20260918/npu_cache_ctx8192/5153695462235992255.blob'
EXPECTED_NPU_CACHE_SHA256 = '3008579cfaa057bfddc430c70dae3f9f0e184589b72d2df816c2cf157d9ae915'
BINDING_EVIDENCE = {
    "CPU": ROOT / "runs/358h/qualification_ac_20260918/environment_cpu.json",
    "NPU": ROOT / "runs/358h/qualification_ac_20260918/npu_cache_binding_ctx8192.json",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


def active_power_scheme() -> tuple[str, bool]:
    completed = subprocess.run(["powercfg", "/GETACTIVESCHEME"], capture_output=True)
    raw = completed.stdout
    return raw.decode("utf-8", errors="replace").strip(), b"381b4222-f694-41f0-9685-ff5bb260df2e" in raw.lower()


def readiness() -> tuple[dict, dict]:
    gate = json.loads(GATE.read_text(encoding="utf-8-sig"))
    prereg = json.loads(PREREG.read_text(encoding="utf-8-sig"))
    errors = []
    if gate.get("status") != "PASS" or not gate.get("qualification_pass"):
        errors.append("replacement Phase-0 gate is not PASS")
    if prereg.get("status") != "FROZEN" or prereg.get("formal_measurement_authorized") is not True:
        errors.append("Phase-1 preregistration is not FROZEN/authorized")
    if prereg.get("repository_commit", "").startswith("FILL_"):
        errors.append("repository_commit is not frozen")
    battery = psutil.sensors_battery()
    if battery is None or battery.power_plugged is not True:
        errors.append("external AC power is not positively online")
    _, balanced = active_power_scheme()
    if not balanced:
        errors.append("Windows Balanced power scheme is not active")
    if (os.environ.get("SESSIONNAME") or "").upper().startswith("RDP"):
        errors.append("remote desktop session is forbidden by the frozen protocol")
    for name, expected in EXPECTED_IR.items():
        path = MODEL / name
        if not path.is_file() or sha256(path) != expected:
            errors.append(f"IR missing or hash-mismatched: {name}")
    if not NPU_CACHE.is_file() or sha256(NPU_CACHE) != EXPECTED_NPU_CACHE_SHA256:
        errors.append('AC-qualified NPU cache is missing or hash-mismatched')
    if errors:
        raise RuntimeError("; ".join(errors))
    return gate, prereg


def prepared_input(tokenizer, count: int, expected_hash: str):
    encoded = tokenizer.encode(BASE_TEXT * (count // 30 + 20), add_special_tokens=False)
    ids = np.asarray(encoded.input_ids.data, dtype=np.int64).reshape(-1)[:count]
    if len(ids) != count:
        raise RuntimeError(f"could not construct exact {count}-token input")
    digest = hashlib.sha256(ids.tobytes()).hexdigest()
    if digest != expected_hash:
        raise RuntimeError(f"prompt token hash mismatch at context {count}: {digest}")
    matrix = ids.reshape(1, -1)
    return ov_genai.TokenizedInputs(ov.Tensor(matrix), ov.Tensor(np.ones_like(matrix))), digest


def generate(pipe, inputs, config, marker: str):
    start_ns = time.perf_counter_ns()
    rss_start = psutil.Process().memory_info().rss
    result = pipe.generate(inputs, config)
    rss_end = psutil.Process().memory_info().rss
    end_ns = time.perf_counter_ns()
    metrics = result.perf_metrics
    tokens = [int(v) for v in result.tokens[0]]
    return {
        "start_perf_counter_ns": start_ns,
        "end_perf_counter_ns": end_ns,
        "host_generate_duration_ms": (end_ns - start_ns) / 1e6,
        "rss_start_bytes": rss_start,
        "rss_end_bytes": rss_end,
        "input_tokens": int(metrics.get_num_input_tokens()),
        "output_tokens": int(metrics.get_num_generated_tokens()),
        "ttft_ms": float(metrics.get_ttft().mean),
        "tpot_ms": float(metrics.get_tpot().mean),
        "throughput_tokens_s": float(metrics.get_throughput().mean),
        "generate_duration_ms": float(metrics.get_generate_duration().mean),
        "inference_duration_ms": float(metrics.get_inference_duration().mean),
        "generated_token_ids": tokens,
        "generated_token_ids_sha256": hashlib.sha256(np.asarray(tokens, dtype=np.int64).tobytes()).hexdigest(),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--device", choices=["CPU", "NPU"])
    p.add_argument("--check", action="store_true")
    p.add_argument("--execute-formal", action="store_true")
    args = p.parse_args()
    if args.check:
        try:
            readiness()
        except Exception as exc:
            print(json.dumps({"ready": False, "reason": str(exc)}, indent=2))
            return 2
        print(json.dumps({"ready": True}, indent=2))
        return 0
    if not args.execute_formal or not args.device:
        p.error("formal execution requires both --execute-formal and --device")

    gate, prereg = readiness()
    core = ov.Core()
    if args.device not in core.available_devices:
        raise RuntimeError(f"requested physical device unavailable: {args.device}")
    phase = prereg["phase1_primary_latency_track"]
    affinity = phase["process_affinity"][args.device]
    if isinstance(affinity, list):
        psutil.Process().cpu_affinity([int(value) for value in affinity])
    expected_prompts = phase["prompt_construction"]["token_id_sha256_by_context"]
    tokenizer = ov_genai.Tokenizer(MODEL)
    inputs = {n: prepared_input(tokenizer, n, expected_prompts[str(n)]) for n in phase["context_tokens"]}
    config = ov_genai.GenerationConfig()
    config.max_new_tokens = phase["output_cap_generated_tokens"]
    config.min_new_tokens = phase["output_cap_generated_tokens"]
    config.ignore_eos = True
    config.do_sample = False
    config.apply_chat_template = False

    pipe_config = {"PERFORMANCE_HINT": "LATENCY"}
    if args.device == "NPU":
        pipe_config = dict(phase["npu_compile_policy"])
        pipe_config["CACHE_DIR"] = str((ROOT / "runs/358h/qualification_ac_20260918/npu_cache_ctx8192").resolve())
    pipe = ov_genai.LLMPipeline(str(MODEL), args.device, pipe_config)
    binding_evidence = BINDING_EVIDENCE[args.device]
    binding_evidence_sha256 = sha256(binding_evidence)
    session_id = f"358h-p1-{args.device.lower()}-{datetime.now().strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
    out = ROOT / "runs/358h/phase1" / session_id
    out.mkdir(parents=True, exist_ok=False)
    session = {
        "schema": "heterospec.358h.phase1.v2",
        "session_id": session_id,
        "formal": True,
        "started": now(),
        "host": socket.gethostname(),
        "python": platform.python_version(),
        "openvino": ov.get_version(),
        "requested_device": args.device,
        "process_affinity": psutil.Process().cpu_affinity(),
        "binding_evidence": str(binding_evidence.relative_to(ROOT)),
        "binding_evidence_sha256": binding_evidence_sha256,
        "phase0_gate": gate,
        "preregistration_sha256": sha256(PREREG),
        "telemetry_prefix": os.environ.get("HETEROSPEC_TELEMETRY_PREFIX"),
        "preflight": {
            "power_plugged": psutil.sensors_battery().power_plugged,
            "power_scheme": active_power_scheme()[0],
            "session_name": os.environ.get("SESSIONNAME"),
        },
        "cells": [],
    }
    expected_device_order = phase["condition_order"]["device_order"]
    if args.device not in expected_device_order:
        raise RuntimeError(f"device is absent from frozen order: {args.device}")
    context_order = phase["condition_order"]["context_order_by_device"][args.device]
    if sorted(context_order) != sorted(phase["context_tokens"]):
        raise RuntimeError("frozen context order does not match frozen context set")
    if args.device == "NPU":
        prior = []
        for prior_path in (ROOT / "runs/358h/phase1").glob("*/session.json"):
            prior_session = json.loads(prior_path.read_text(encoding="utf-8-sig"))
            if (prior_session.get("formal") is True and prior_session.get("status") == "COMPLETE"
                    and prior_session.get("requested_device") == "CPU"
                    and prior_session.get("preregistration_sha256") == sha256(PREREG)):
                prior.append(str(prior_path.relative_to(ROOT)))
        if not prior:
            raise RuntimeError("frozen device order requires a completed CPU session with the same preregistration before NPU")
        session["prior_cpu_session_evidence"] = prior[-1]
    session["frozen_device_order"] = expected_device_order
    session["frozen_context_order"] = context_order
    for context in context_order:
        tokenized, prompt_hash = inputs[context]
        warmups = []
        stable = False
        for index in range(1, phase["warmup"]["maximum"] + 1):
            warm = generate(pipe, tokenized, config, f'warmup|{args.device}|c{context}|w{index}')
            warmups.append({"index": index, "throughput_tokens_s": warm["throughput_tokens_s"]})
            if index >= phase["warmup"]["minimum"]:
                a, b = warmups[-2]["throughput_tokens_s"], warmups[-1]["throughput_tokens_s"]
                difference = abs(a - b) / ((a + b) / 2) * 100
                if difference <= 5:
                    stable = True
                    break
        if not stable:
            raise RuntimeError(f"warm-up stability gate failed at context {context}")
        cell = {"context_tokens": context, "prompt_token_ids_sha256": prompt_hash, "warmups": warmups, "runs": []}
        for repetition in range(1, phase["repetitions_per_cell"] + 1):
            result = generate(pipe, tokenized, config, f'formal|{args.device}|c{context}|r{repetition}')
            result["requested_device"] = args.device
            result["actual_execution_devices"] = args.device
            result["binding_evidence_sha256"] = binding_evidence_sha256
            if result["input_tokens"] != context or result["output_tokens"] != phase["output_cap_generated_tokens"]:
                raise RuntimeError("token-count contract failed")
            run_id = f"c{context}-r{repetition}"
            (out / f"{run_id}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            (out / f"{run_id}.boundary.json").write_text(json.dumps({
                "start_qpc_ticks": result["start_perf_counter_ns"],
                "end_qpc_ticks": result["end_perf_counter_ns"],
                "qpc_frequency": 1_000_000_000
            }, indent=2) + "\n", encoding="utf-8")
            cell["runs"].append(run_id)
        session["cells"].append(cell)
    session["ended"] = now()
    post_battery = psutil.sensors_battery()
    post_scheme, post_balanced = active_power_scheme()
    session["postflight"] = {"power_plugged": post_battery.power_plugged if post_battery else None, "power_scheme": post_scheme}
    if post_battery is None or post_battery.power_plugged is not True or not post_balanced:
        raise RuntimeError("post-run AC/power-scheme gate failed; session is incomplete and inadmissible")
    session["status"] = "COMPLETE"
    (out / "session.json").write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"session": session_id, "status": "COMPLETE"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

