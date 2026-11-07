#!/usr/bin/env python3
"""Qualification-only workload for measuring telemetry observer overhead."""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import json
import time
import hashlib
from pathlib import Path

import openvino_genai as genai
import ittapi
import numpy as np
import openvino as ov
import psutil

ITT_DOMAIN = ittapi.domain('HeteroSpec-358H')


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--device', choices=['CPU', 'NPU'], required=True)
    p.add_argument('--model-dir', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--iterations', type=int, default=20)
    p.add_argument('--lead-tail-seconds', type=int, default=5)
    p.add_argument('--context-tokens', type=int, default=0,
                   help='When nonzero, construct an exact synthetic token context of this length.')
    p.add_argument('--output-tokens', type=int, default=4)
    p.add_argument('--warmups', type=int, default=3)
    p.add_argument('--affinity-cpus', default='', help='Optional comma-separated logical CPU list.')
    p.add_argument('--emit-itt', action='store_true')
    args = p.parse_args()
    process = psutil.Process()
    requested_affinity = [int(value) for value in args.affinity_cpus.split(',') if value.strip()]
    if requested_affinity:
        process.cpu_affinity(requested_affinity)
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
    config.max_new_tokens = args.output_tokens
    config.min_new_tokens = args.output_tokens
    config.ignore_eos = True
    tokenizer = pipe.get_tokenizer()
    if args.context_tokens:
        base = (
            'Heterogeneous computing assigns work to processors with different strengths. '
            'A reproducible experiment records every configuration, timestamp, and device name. '
            'Correctness is checked before performance, and raw measurements are never discarded. '
            'Candidate tokens are verified in order, while timing and energy remain separate measurements. '
        )
        encoded = tokenizer.encode(base * (args.context_tokens // 30 + 20), add_special_tokens=False)
        ids = np.asarray(encoded.input_ids.data, dtype=np.int64).reshape(-1)[:args.context_tokens]
        if len(ids) != args.context_tokens:
            raise RuntimeError(f'could not construct exact {args.context_tokens}-token input')
        matrix = ids.reshape(1, -1)
        prompt = genai.TokenizedInputs(ov.Tensor(matrix), ov.Tensor(np.ones_like(matrix)))
        prompt_hash = hashlib.sha256(ids.tobytes()).hexdigest()
    else:
        prompt = tokenizer.encode('HeteroSpec telemetry qualification.', add_special_tokens=False)
        prompt_hash = None
    for _ in range(args.warmups):
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
        'context_tokens': args.context_tokens or None,
        'prompt_token_ids_sha256': prompt_hash,
        'output_tokens_per_iteration': args.output_tokens,
        'warmups': args.warmups,
        'requested_affinity_cpus': requested_affinity or None,
        'effective_affinity_cpus': process.cpu_affinity(),
        'lead_tail_seconds': args.lead_tail_seconds,
        'itt_marker_emitted': args.emit_itt,
        'start_perf_counter_ns': start_ns,
        'end_perf_counter_ns': end_ns,
        'inner_duration_ms': (end_ns - start_ns) / 1e6,
        'outputs': hashes,
        'structurally_valid': all(len(x) == args.output_tokens for x in hashes)
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    if not payload['structurally_valid']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()

