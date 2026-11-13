#!/usr/bin/env python3
"""CPU-only conditional memory planner. Never launches or qualifies a GPU runtime.

All byte quantities are integers; GiB means 2**30 bytes, not 10**9 bytes.
Measurements are caller-supplied evidence, not independently verified here.
"""
import argparse
import json
import sys

GIB = 1 << 30
CAPACITY = 24 * GIB
PIN = "a679bb86ce36e883a98a97733492b686e5b9a08e"


def integer(value, name, minimum=1):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def fields(obj, required, name):
    if type(obj) is not dict or set(obj) != set(required.split()):
        raise ValueError(f"{name} must contain exactly: {required}")


def choice(value, options, name):
    if type(value) is not str or value not in options:
        raise ValueError(f"{name} must be one of {options}")
    return value


def ceildiv(n, d):
    return (n + d - 1) // d


def plan(p):
    fields(p, "mode model parameter_count parameter_basis weight_bits weight_payload_bytes tp weight_layout metadata_bytes replicated_bytes extras_per_rank_bytes imbalance_percent kv hardware", "plan")
    choice(p['mode'], ('memory_estimate', 'official_deepinfer'), 'mode')
    if type(p['model']) is not str or not p['model'].strip():
        raise ValueError('model must be nonempty text')
    choice(p['parameter_basis'], ('nominal_unverified', 'snapshot_confirmed'), 'parameter_basis')
    n = integer(p['parameter_count'], 'parameter_count')
    bits = integer(p['weight_bits'], 'weight_bits')
    if bits not in (2, 3, 4, 8, 16, 32):
        raise ValueError('weight_bits must be 2, 3, 4, 8, 16 or 32')
    tp = integer(p['tp'], 'tp')
    if tp not in (1, 2, 4, 8):
        raise ValueError('tp must be 1, 2, 4 or 8')
    layout = choice(p['weight_layout'], ('sharded', 'replicated'), 'weight_layout')
    metadata = integer(p['metadata_bytes'], 'metadata_bytes', 0)
    replicated = integer(p['replicated_bytes'], 'replicated_bytes', 0)
    extras = integer(p['extras_per_rank_bytes'], 'extras_per_rank_bytes', 0)
    imbalance = integer(p['imbalance_percent'], 'imbalance_percent', 0)
    h = p['hardware']
    fields(h, 'gpu_count gpu_name sm nominal_bytes_per_gpu free_bytes_per_rank memory_evidence topology_evidence', 'hardware')
    if integer(h['gpu_count'], 'gpu_count') != 8 or h['gpu_name'] != 'RTX A5000' or integer(h['sm'], 'sm') != 86 or integer(h['nominal_bytes_per_gpu'], 'nominal_bytes_per_gpu') != CAPACITY:
        raise ValueError('this planner models only 8 separate RTX A5000 SM86 devices with nominal 24 GiB each')
    for key in ('memory_evidence', 'topology_evidence'):
        if h[key] is not None and (type(h[key]) is not str or not h[key].strip()):
            raise ValueError(f'{key} must be null or nonempty measurement description')
    free = h['free_bytes_per_rank']
    if free is not None:
        if type(free) is not list or len(free) != tp:
            raise ValueError('free_bytes_per_rank must contain exactly tp measured usable free byte counts')
        for value in free:
            integer(value, 'free_bytes_per_rank entry', 0)
            if value > CAPACITY:
                raise ValueError('free bytes cannot exceed nominal device capacity')
        if h['memory_evidence'] is None:
            raise ValueError('free bytes require memory_evidence')
    elif h['memory_evidence'] is not None:
        raise ValueError('memory_evidence requires free byte measurements')
    kv = p['kv']
    if type(kv) is not dict or 'kind' not in kv:
        raise ValueError('kv must be an object with kind')
    kind = choice(kv['kind'], ('gqa', 'mla_unmodeled'), 'kv.kind')
    kv_bytes = None
    heads = None
    if kind == 'mla_unmodeled':
        fields(kv, 'kind', 'kv')
    else:
        fields(kv, 'kind layers sequence_length batch_size kv_heads head_dim dtype_bytes allocation', 'kv')
        dims = {k: integer(kv[k], 'kv.' + k) for k in ('layers', 'sequence_length', 'batch_size', 'kv_heads', 'head_dim', 'dtype_bytes')}
        if dims['dtype_bytes'] not in (1, 2, 4):
            raise ValueError('KV dtype_bytes must be 1, 2 or 4')
        allocation = choice(kv['allocation'], ('sharded', 'replicated'), 'kv.allocation')
        if allocation == 'sharded' and dims['kv_heads'] % tp:
            raise ValueError('KV heads must divide TP exactly; explicitly choose replicated KV otherwise')
        heads = dims['kv_heads'] if allocation == 'replicated' else dims['kv_heads'] // tp
        kv_bytes = dims['layers'] * dims['sequence_length'] * dims['batch_size'] * 2 * heads * dims['head_dim'] * dims['dtype_bytes']
    nominal_floor = ceildiv(n * bits, 8)
    payload = p['weight_payload_bytes']
    if payload is not None:
        integer(payload, 'weight_payload_bytes')
    weight_floor = nominal_floor if payload is None else payload
    # metadata is global for sharded layout, per complete copy for replicated layout.
    base = ceildiv(weight_floor + metadata, tp) if layout == 'sharded' else weight_floor + metadata
    weight_budget = ceildiv(base * (100 + imbalance), 100)
    per_rank = weight_budget + replicated + extras + (kv_bytes or 0)
    reasons = []
    if p['mode'] == 'official_deepinfer':
        reasons.append(f'Official DeepInfer {PIN}: NVIDIA SM100 and DeepSeek-V4.1-Flash only; SM86 is unsupported. No setting override is accepted.')
    if free is None:
        reasons.append('Missing measured usable free bytes for every selected rank.')
    if h['topology_evidence'] is None:
        reasons.append('Missing measured topology/interconnect evidence; TP execution is unqualified.')
    if kv_bytes is None:
        reasons.append('MLA KV is unmodeled; GQA formula is not applicable.')
    payload_per_rank = ceildiv(weight_floor, tp) if layout == 'sharded' else weight_floor
    payload_exceeds = payload_per_rank > CAPACITY or (free is not None and any(payload_per_rank > f for f in free))
    budget_exceeds = per_rank > CAPACITY or (free is not None and any(per_rank > f for f in free))
    if payload_exceeds:
        reasons.append('Weight payload alone exceeds at least one rank memory bound; aggregate VRAM is not pooled.')
    elif budget_exceeds:
        reasons.append('Planned budget exceeds at least one rank memory bound; this includes caller-chosen reserves and imbalance, not just unavoidable tensor payload.')
    status = 'unsupported_native' if p['mode'] == 'official_deepinfer' else ('payload_exceeds_memory' if payload_exceeds else ('budget_exceeds_memory' if budget_exceeds else ('unsupported_missing_evidence' if reasons else 'estimated_possible')))
    return {
        'status': status, 'runtime_admission': False, 'gpu_tested': False,
        'conditional_estimate_only': True, 'model': p['model'], 'parameter_basis': p['parameter_basis'],
        'official_deepinfer_pin': PIN, 'official_deepinfer_sm86_supported': False,
        'tp': tp, 'weight_lower_bound_bytes': weight_floor,
        'nominal_parameter_bit_floor_bytes': nominal_floor,
        'weight_lower_bound_source': 'nominal_parameter_bits' if payload is None else 'caller_supplied_index_tensor_payload',
        'weight_and_metadata_budget_per_rank_bytes': weight_budget,
        'kv_heads_per_rank': heads, 'kv_bytes_per_rank': kv_bytes,
        'weight_payload_lower_bound_per_rank_bytes': payload_per_rank,
        'planned_budget_per_rank_bytes': per_rank,
        'planned_budget_all_selected_ranks_bytes': per_rank * tp,
        'nominal_bytes_per_gpu': CAPACITY,
        'usable_free_bytes_per_rank': free,
        'headroom_bytes_per_rank': None if free is None else [f - per_rank for f in free],
        'reasons': reasons,
        'caveats': ['User-supplied measurements are not verified by this CPU-only tool.',
                    'Index payload is a snapshot/moving-source observation, not headers, resident allocation or exact parameter-count proof.',
                    'No runtime, kernel, topology, correctness or performance qualification.',
                    'Quantization scales/zeros, padding, workspace, allocator, graph and communication buffers must be budgeted explicitly.',
                    'Nominal parameter counts require exact checkpoint/config confirmation; even a snapshot-confirmed claim is caller supplied.',
                    'Imbalance percent inflates weight/metadata per-rank budget only; extras and KV are added separately.']
    }


def unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON key: ' + key)
        out[key] = value
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', help='JSON plan; no execution controls are supported')
    args = parser.parse_args(argv)
    try:
        with open(args.plan, encoding='utf-8') as stream:
            p = json.load(stream, object_pairs_hook=unique_object,
                          parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON number: ' + x)))
        result = plan(p)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'status': 'invalid_input', 'error': str(exc), 'runtime_admission': False}))
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result['status'] == 'estimated_possible' else 1


if __name__ == '__main__':
    sys.exit(main())
