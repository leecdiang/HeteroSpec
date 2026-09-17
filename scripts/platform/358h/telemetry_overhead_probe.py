#!/usr/bin/env python3
"""Qualification-only workload for measuring telemetry observer overhead."""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import json
import time
from pathlib import Path

import openvino_genai as genai
import ittapi

ITT_DOMAIN = ittapi.domain('HeteroSpec-358H')


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--device', choices=['CPU', 'NPU'], required=True)
    p.add_argument('--model-dir', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--iterations', type=int, default=20)
    p.add_argument('--lead-tail-seconds', type=int, default=5)
    p.add_argument('--emit-itt', action='store_true')
    args = p.parse_args()
    properties = {'PERFORMANCE_HINT': 'LATENCY'}
    if args.device == 'NPU':
        properties = {
            'MAX_PROMPT_LEN': 128,
            'MIN_RESPONSE_LEN': 4,
            'PREFILL_HINT': 'DYNAMIC',
            'GENERATE_HINT': 'FAST_COMPILE',
            'CACHE_DIR': str((args.output.parent / 'npu_cache').resolve())
        }
    pipe = genai.LLMPipeline(str(args.model_dir), args.device, properties)
    config = genai.GenerationConfig()
    config.do_sample = False
    config.max_new_tokens = 4
    config.min_new_tokens = 4
    config.ignore_eos = True
    prompt = pipe.get_tokenizer().encode('HeteroSpec telemetry qualification.', add_special_tokens=False)
    for _ in range(3):
        pipe.generate(prompt, config)
    time.sleep(args.lead_tail_seconds)
    start_ns = time.perf_counter_ns()
    hashes = []
    marker = ittapi.task(f'qualification|{args.device}|generate-loop', domain=ITT_DOMAIN) if args.emit_itt else nullcontext()
    with marker:
        for _ in range(args.iterations):
            result = pipe.generate(prompt, config)
            hashes.append([int(x) for x in result.tokens[0]])
    end_ns = time.perf_counter_ns()
    time.sleep(args.lead_tail_seconds)
    payload = {
        'schema': 'heterospec.358h.telemetry_overhead_probe.v1',
        'formal_measurement': False,
        'performance_claim_prohibited': True,
        'device': args.device,
        'iterations': args.iterations,
        'lead_tail_seconds': args.lead_tail_seconds,
        'itt_marker_emitted': args.emit_itt,
        'start_perf_counter_ns': start_ns,
        'end_perf_counter_ns': end_ns,
        'inner_duration_ms': (end_ns - start_ns) / 1e6,
        'outputs': hashes,
        'structurally_valid': all(len(x) == 4 for x in hashes)
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    if not payload['structurally_valid']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()

