#!/usr/bin/env python3
"""Recompute historical headroom and B2 paired operation ratios; no model runs."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path

SOURCES = {
    'live': {
        'sha256': 'd827073f6b24848428a8e73b12ca4012df33f2da67ed612a18713bee49b52a2b',
        'url': 'https://github.com/leecdiang/HeteroSpec/blob/ba5b4c8e01d50d4bfaab1ac3908f798347be063a/benchmarks/rtx_q8_transfer_20261109/results_20261109/LIVE_RESULTS.json',
    },
    'b2': {
        'sha256': '2944749ca52692b19cf90827d1f0ad0367328afb9a6604182e061aa6c8207b10',
        'url': 'https://github.com/leecdiang/HeteroSpec/blob/4fe337a8ff349d547023f9dd60b8e114e5323207/benchmarks/server_expansion_v1/strong_baseline_followup_20261110/RESULTS_B2_20261110/INDEPENDENT_PUBLIC_STATS_01.json',
    },
}

def bound_read(path, identity):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != identity['sha256']:
        raise ValueError('Historical source identity changed: ' + str(path))
    return json.loads(raw)

def positive(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError('Nonpositive or nonfinite timing')
    return value

def recompute(live, b2):
    if not live['complete'] or live['measured_requests'] != 1024 or len(live['all_eight_arms']) != 8:
        raise ValueError('Unexpected historical full-service population')
    fixed = min(live['all_eight_arms'], key=lambda r: positive(r['service_total_s']))
    if fixed['arm'] != 4 or fixed['measurements'] != 128:
        raise ValueError('Historical control identity changed')
    total = positive(fixed['service_total_s'])
    phases = []
    for field in ['target_prefill_s', 'target_verify_s', 'draft_prefill_s', 'draft_propose_s', 'draft_sync_s']:
        seconds = positive(fixed[field]); share = seconds / total
        phases.append({'field': field, 'seconds': seconds, 'service_fraction': share,
                       'required_fractional_phase_reduction_for_5pct_service': .05 / share})
    workers = defaultdict(lambda: defaultdict(list))
    metadata = {}
    for row in b2['observations']:
        if row['role'] != 'measured':
            continue
        if row['path'] not in {'q4pair', 'q8'}:
            raise ValueError('Unexpected B2 path')
        key = (row['core'], row['boundary'], row['worker'])
        if key in metadata and metadata[key] != row['round']:
            raise ValueError('Worker spans different rounds')
        metadata[key] = row['round']
        workers[key][row['path']].append(positive(row['operation_s']))
    if len(workers) != 16 or b2['measurements'] != 64:
        raise ValueError('Incomplete B2 measured population')
    ratios = defaultdict(list)
    for (core, boundary, worker), paths in sorted(workers.items()):
        if set(paths) != {'q4pair', 'q8'} or any(len(v) != 2 for v in paths.values()):
            raise ValueError('Incomplete same-worker pair')
        ratio = math.fsum(paths['q8']) / math.fsum(paths['q4pair'])
        ratios[(core, boundary)].append({'worker': worker, 'ratio_q8_over_q4pair': ratio})
    cells = []
    for key, values in sorted(ratios.items()):
        if len(values) != 4:
            raise ValueError('Incomplete B2 cell')
        point = math.exp(math.fsum(math.log(r['ratio_q8_over_q4pair']) for r in values) / len(values))
        published = next(x for x in b2['contrasts'] if (x['core'], x['boundary']) == key)
        if not math.isclose(point, published['geometric_B_over_A'], rel_tol=0, abs_tol=1e-12):
            raise ValueError('Independent B2 ratio does not match published summary')
        saving = 1 - point
        cells.append({'core': key[0], 'boundary': key[1], 'processes': len(values),
                      'ratio_q8_over_q4pair': point, 'local_operation_reduction_fraction': saving,
                      'minimum_process_ratio': min(x['ratio_q8_over_q4pair'] for x in values),
                      'maximum_process_ratio': max(x['ratio_q8_over_q4pair'] for x in values),
                      'hypothetical_service_coverage_needed_for_5pct': .05 / saving if saving > 0 else None,
                      'same_ratio_and_same_operation_count_assumption': True,
                      'per_process': values})
    return {
        'schema': 'heterospec.research.historical-economics.v1',
        'status': 'RECOMPUTED_HISTORICAL_DESCRIPTIVE_DATA',
        'sources': SOURCES,
        'rtx': {'fixed_control': fixed['label'], 'service_total_s': total,
                'root_clusters': live['root_clusters'], 'paired_order_blocks': live['paired_order_blocks'],
                'phases': phases},
        'B2': {'measured_operations': 64, 'warmups_excluded': 64, 'cells': cells,
               'process_ratio_definition': 'mean(q8 times) / mean(q4pair times) within one worker; geometric mean of four process ratios'},
        'limits': [
            'Existing exposed data, not a new GPU run, confirmation population or native numerical requalification.',
            'The RTX service fractions and B2 operation ratios are different deployment populations; never multiply them together.',
            'Coverage arithmetic assumes the observed local ratio applies to every replaced operation, with fixed operation count, all other costs unchanged, and no new overhead.',
            'The coverage calculation is a conditional break-even illustration, not a measured service bound or a forecast.',
            'Four processes in B2 are not four independent input roots; min/max are descriptive, not confidence intervals.',
            'Historical operation summaries are not admitted into the current controller cost catalog.',
        ],
        'new_model_requests': 0, 'new_GPU_operations': 0,
        'new_method_service_performance_claim': False,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', type=Path, required=True)
    parser.add_argument('--b2', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Use a fresh output path')
    result = recompute(bound_read(args.live, SOURCES['live']), bound_read(args.b2, SOURCES['b2']))
    result['analyzer_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2); handle.write('\n')
    print(json.dumps({'status': result['status'], 'out': str(args.out),
                      'B2_cells_recomputed': len(result['B2']['cells']), 'new_GPU_operations': 0}))

if __name__ == '__main__':
    main()
