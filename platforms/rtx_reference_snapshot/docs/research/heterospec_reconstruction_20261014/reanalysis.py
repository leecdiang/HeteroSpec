"""CPU-only arithmetic checks of frozen REPORTED values, not a native/raw audit.

Python >=3.11, standard library only. No network, model, GPU or repository writes.
Default output is stdout. --output uses exclusive creation (never overwrites).
"""
from __future__ import annotations
import argparse
import csv
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
COST_BLOB = 'e883410f6f97c65455b8fe00710478eb9051ce88'


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def read_json(path: Path) -> Any:
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, f'duplicate JSON key: {key}')
            value[key] = item
        return value
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def load_cost(path: Path) -> dict[str, dict[str, Decimal]]:
    require(git_blob(path.read_bytes()) == COST_BLOB, 'exact source CSV Git blob mismatch')
    result = {}
    with path.open(newline='', encoding='utf-8') as stream:
        for row in csv.DictReader(stream):
            require(row['qualified'] == 'True' and row['tasks'] == '12', 'cost qualification changed')
            family = result.setdefault(row['family'], {})
            require(row['comparison'] not in family, 'duplicate cost coordinate')
            ratio = Decimal(row['ratio'])
            require(ratio.is_finite() and ratio > 0, 'invalid cost ratio')
            family[row['comparison']] = ratio
    require(set(result) == {'Qwen3', 'SmolLM2', 'Llama'}, 'three-family inventory changed')
    require(all(len(value) == 7 for value in result.values()), '21-comparison inventory changed')
    return result


def derived_cost(cost: dict, same_panel_and_weights: bool) -> dict:
    require(same_panel_and_weights, 'multiplication requires identical pairing and weights')
    out = {}
    eps = Decimal('0.0000005')  # Source rounding only, NOT a confidence interval.
    with localcontext() as ctx:
        ctx.prec = 45
        for family, row in cost.items():
            q = row['M_QB/C_QB']
            answer = {'D_QB': str(q), 'rounding_intervals_not_CI': {}}
            for layout in ('PQ', 'GS'):
                m, c = row[f'M_{layout}/M_QB'], row[f'C_{layout}/C_QB']
                answer['D_' + layout] = str(m*q/c)
                answer['rounding_intervals_not_CI'][layout] = [str((m-eps)*(q-eps)/(c+eps)), str((m+eps)*(q+eps)/(c-eps))]
            answer['QB_vs_PQ_speculative_latency_reduction'] = str(1-1/row['C_PQ/C_QB'])
            answer['scope'] = 'PR98 completed panel algebra; not PR104 interim aggregation or component timing'
            out[family] = answer
    return out


def interim_rows(value: dict) -> list[dict]:
    require(value['sessions_completed'] == [0, 1, 2, 3, 4], 'this snapshot admits only sessions0..4')
    require(value['required_sessions'] == 6 and value['aggregate_qualified'] is False, 'interim qualification changed')
    result = []
    for row in value['comparisons']:
        logs = row['session_logs']
        require(len(logs) == 5 and all(math.isfinite(x) for x in logs), 'five finite session contrasts required')
        ratios = [math.exp(x) for x in logs]
        result.append({'family_path': row['family_path'], 'session_ratios': ratios,
                       'session_ratio_range': [min(ratios), max(ratios)],
                       'task_session_regressions': row['task_session_regressions'],
                       'task_session_coordinates': row['task_session_coordinates'],
                       'final_estimate': None, 'final_interval': None,
                       'scope': 'descriptive observed sessions only; no stopping/inference rule changed'})
    return result


def canonical_scalar(pair: list[int], value: str) -> str:
    require(len(pair) == 2 and pair[0] != pair[1], 'distinct ordered token pair required')
    x = Fraction.from_float(float(value))
    return str(x if pair[0] < pair[1] else -x)


def threshold_fit(rows: list[dict]) -> dict:
    """Exhaustive increasing-threshold separation for these reported four values."""
    xs = sorted({Decimal(r['norm']) for r in rows})
    require(len(xs) == 4, 'four distinct measured ranks required')
    thresholds = [xs[0]-1] + [(a+b)/2 for a,b in zip(xs, xs[1:])] + [xs[-1]+1]
    outcomes = []
    for t in thresholds:
        misses = [r['task'] for r in rows if (Decimal(r['norm']) > t) != r['different']]
        outcomes.append({'threshold': str(t), 'misclassified_tasks': misses})
    witness = [(a['task'], b['task']) for a in rows for b in rows
               if a['different'] and not b['different'] and Decimal(a['norm']) < Decimal(b['norm'])]
    return {'perfect_increasing_threshold_exists': any(not r['misclassified_tasks'] for r in outcomes),
            'rank_counterexamples': witness, 'tested_rank_cuts': outcomes,
            'scope': 'finite retrospective falsification of norm-only monotone explanation; not a risk classifier'}


def analyze(root: Path = ROOT) -> dict:
    observations = read_json(root/'inputs/reported_observations.json')
    cost = derived_cost(load_cost(root/'inputs/rtx_repair_cost.csv'), observations['cost_scope']['paired_panel_and_weights_identical'])
    f = observations['b570_frontier']; e, k, v, j = [Fraction.from_float(float(x)) for x in f['d']]
    residual = j-k-v+e
    require(residual == Fraction(f['reported_I']), 'reported four-cell residual does not reconstruct')
    additive = k+v-e
    c = observations['canonical']
    canonical = [canonical_scalar(r['pair'], r['I']) for r in c['canonical_1248_t47']]
    require(len(set(canonical)) == 1, 'canonical scalar mismatch')
    # 12 direction-pairs x2 oriented rows=24 POSITION rows; remaining20 L0 rows.
    position_rows = c['position_direction_pairs']*2
    l0_rows = c['historical_rows']-position_rows
    require(l0_rows == 20 and l0_rows % 2 == 0, 'reported dependency accounting changed')
    return {
        'scope': 'Report-level arithmetic reconstruction and analytic deductions only. No full logits, models or native archive restored.',
        'PR98_factorial_algebra': cost,
        'PR104_interim_descriptive': interim_rows(observations['rtx_interim']),
        'L0_exact_rational_arithmetic': {
            'number_contract': 'Parse reported shortest round-trip strings as binary64, then use exact rational arithmetic; not raw-vector verification',
            'additive_prediction': str(additive), 'additive_prediction_decimal': float(additive),
            'actual_joint': str(j), 'actual_joint_decimal': float(j),
            'I': str(residual), 'I_decimal': float(residual),
            'opposite_pairwise_sign': additive > 0 and j < 0,
            'actual_argmax_source': 'reported full-vocabulary argmax; not recomputed from vectors here',
            'kernel_or_natural_mediation': 'NOT_ESTABLISHED'},
        'POSITION_canonical_scalar': canonical[0],
        'reported_dependence_accounting': {
            'oriented_repeat_rows': c['historical_rows'], 'oriented_repeat_pairs': c['repeat_pairs'],
            'POSITION_observed_task_positions': c['position_unique_task_positions'],
            'L0_oriented_task_positions': l0_rows//2,
            'canonical_logical_contrasts': c['position_unique_task_positions']+l0_rows//2,
            'independent_inputs': 4,
            'scope': 'Logical accounting conditional on upstream byte-mapping audit; not independent statistical sample count'},
        'norm_only_threshold': threshold_fit(observations['b570_norm']['rows']),
        'new_gpu_processes': 0, 'new_gpu_requests': 0, 'original_files_modified': False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    body = json.dumps(analyze(args.input_root), ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(body)
    else:
        print(body, end='')

if __name__ == '__main__':
    main()
