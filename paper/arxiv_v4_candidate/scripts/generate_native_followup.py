#!/usr/bin/env python3
"""Reconstruct the later fixed-panel studies from authenticated compact records.

No models, GPU calls, networking, raw-vector certification or source rewriting.
Only derived finite floating-point calculations allow absolute error <= 1e-12;
source bytes, JSON structure/types/counts and generated TeX remain exact.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
DATA = Path('anc/followup_20261026')
CELLS = [(1, 'resident'), (3, 'resident'), (1, 'fresh'), (3, 'fresh')]
ARMS = ['PQ_A', 'PQ_B', 'QB']
DERIVED_ABS_TOL = 1e-12


def require(value, message):
    if not value:
        raise ValueError(message)


def read_json(path):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'duplicate JSON key: ' + key)
            out[key] = value
        return out
    def invalid(value):
        raise ValueError('nonfinite JSON token: ' + value)
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs,
                      parse_constant=invalid)


def derived_equal(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(derived_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(derived_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, float):
        return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= DERIVED_ABS_TOL
    return a == b


def authenticate(root=ROOT):
    base = Path(root) / DATA
    index = read_json(base / 'SOURCE_INDEX.json')
    seen = set()
    for row in index:
        relative = row['local']
        require(relative not in seen, 'duplicate source index entry: ' + relative)
        seen.add(relative)
        path = (base / relative).resolve()
        require(path.is_relative_to(base.resolve()), 'source path escapes ancillary root')
        data = path.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        require(blob == row['git_blob'], 'source Git blob mismatch: ' + relative)
        if 'bytes' in row:
            require(len(data) == row['bytes'], 'source size mismatch: ' + relative)
        if 'sha256' in row:
            require(hashlib.sha256(data).hexdigest() == row['sha256'], 'source SHA256 mismatch: ' + relative)
    return len(index)


def csv_rows(path):
    with Path(path).open(newline='') as stream:
        return list(csv.DictReader(stream))


def gm(xs):
    return math.exp(statistics.mean(math.log(x) for x in xs))


def quantile(xs, probability):
    ordered = sorted(xs)
    position = (len(ordered) - 1) * probability
    left = int(position)
    fraction = position - left
    return ordered[left] * (1 - fraction) + ordered[min(left + 1, len(ordered) - 1)] * fraction


def interval(log_values, low=.025, high=.975):
    return [math.exp(quantile(log_values, low)), math.exp(quantile(log_values, high))]


def reconstruct_bridge(rows, freeze):
    """Validate every registered compact slot before constructing paired blocks."""
    sessions = freeze['sessions']
    require(sessions == 6 and freeze['seed'] == 20261026, 'unexpected bridge freeze')
    require([(x['k'], x['lifecycle']) for x in freeze['cells']] == CELLS,
            'unexpected frozen bridge cells')
    require(freeze['arms'] == ARMS, 'unexpected frozen bridge arms')
    require(len(rows) == freeze['total_requests'] == 936, 'missing or extra bridge timing rows')
    measurements, warmups, slots, identities, lengths = {}, set(), set(), {}, {}
    for row in rows:
        slot = row['slot_id']
        require(slot not in slots, 'duplicate bridge slot: ' + slot)
        slots.add(slot)
        session, task, k = (int(row[x]) for x in ('session', 'task', 'k'))
        cell = (k, row['lifecycle'])
        require(session in range(sessions) and task in range(12) and cell in CELLS,
                'invalid bridge session/input/cell')
        label, category = row['label'], row['category']
        require(label in ARMS and category in ('warmup', 'measurement'), 'invalid bridge arm/category')
        for key in ('service_seconds', 'request_seconds', 'setup_seconds', 'teardown_seconds'):
            value = float(row[key])
            require(math.isfinite(value) and value >= 0, 'invalid bridge time: ' + key)
        seconds = float(row['service_seconds'])
        require(seconds > 0, 'nonpositive bridge service time')
        require(task not in identities or identities[task] == row['input'], 'bridge input identity changed')
        identities[task] = row['input']
        length = int(row['output_length'])
        require(length > 0 and (task not in lengths or lengths[task] == length), 'bridge output length changed')
        lengths[task] = length
        if category == 'warmup':
            key = (session, *cell, label)
            require(task == 11 and key not in warmups, 'invalid or duplicate bridge warmup')
            warmups.add(key)
        else:
            key = (session, task, *cell, label)
            require(key not in measurements, 'duplicate bridge measurement')
            measurements[key] = seconds
    expected = {(s, t, *c, arm) for s in range(sessions) for t in range(12) for c in CELLS for arm in ARMS}
    require(set(measurements) == expected and len(measurements) == freeze['measurements'] == 864,
            'missing bridge measurement')
    require(warmups == {(s, *c, a) for s in range(sessions) for c in CELLS for a in ARMS}
            and len(warmups) == freeze['warmups'] == 72, 'missing bridge warmup')
    require(slots == {f's{s}-{i:04d}' for s in range(sessions) for i in range(156)}, 'bridge slot inventory differs')
    blocks = []
    for session, task, k, life in sorted({key[:4] for key in measurements}):
        a, b, q = (measurements[session, task, k, life, arm] for arm in ARMS)
        pq = (a + b) / 2
        blocks.append(dict(session=session, task=task, input=identities[task], k=k,
                           lifecycle=life, PQ_A=a, PQ_B=b, QB=q, dual_PQ=pq,
                           log_ratio=math.log(q / pq), log_AA=math.log(a / b),
                           ratio=q / pq, difference_ms=1000 * (q - pq)))
    return blocks


def compute_bridge(blocks, freeze):
    n = freeze['sessions']
    means = [[statistics.mean(b['log_ratio'] for b in blocks
                              if b['session'] == s and (b['k'], b['lifecycle']) == c)
              for c in CELLS] for s in range(n)]
    primary = freeze['intervals']['primary']
    count = re.search(r'(\d+) replicates', primary)
    require(count is not None and int(count.group(1)) == 20000,
            'unexpected frozen bootstrap replicate count')
    repetitions = int(count.group(1))
    rng = random.Random(freeze['seed'])
    bootstrap = []
    for _ in range(repetitions):
        selected = [means[rng.randrange(n)] for _ in range(n)]
        bootstrap.append([statistics.mean(row[i] for row in selected) for i in range(4)])
    cells = []
    for i, (k, life) in enumerate(CELLS):
        selected = [b for b in blocks if (b['k'], b['lifecycle']) == (k, life)]
        logs = [row[i] for row in means]
        ratio = math.exp(statistics.mean(logs))
        ci = interval([row[i] for row in bootstrap], .00625, .99375)
        aa = max(abs(math.exp(statistics.mean(b['log_AA'] for b in selected if b['task'] == t)) - 1)
                 for t in range(12))
        cells.append(dict(k=k, lifecycle=life, ratio=ratio, reduction_percent=100 * (1 - ratio),
                          simultaneous_family95_interval=ci,
                          pointwise95_interval=interval([row[i] for row in bootstrap]),
                          largest_input_AA=aa, session_ratios=[math.exp(x) for x in logs],
                          mean_PQ_seconds=statistics.mean(b['dual_PQ'] for b in selected),
                          mean_QB_seconds=statistics.mean(b['QB'] for b in selected),
                          difference_ms=statistics.mean(b['difference_ms'] for b in selected),
                          block_reversals=sum(b['ratio'] >= 1 for b in selected), blocks=len(selected),
                          practical_gain_established=ci[1] < .98 and 1 - ratio > max(.02, aa)
                                                     and all(x < 0 for x in logs)))
    contrasts = []
    for name, weights in [('k3_over_k1_resident', [-1, 1, 0, 0]),
                          ('k3_over_k1_fresh', [0, 0, -1, 1]),
                          ('fresh_over_resident_k1', [-1, 0, 1, 0]),
                          ('fresh_over_resident_k3', [0, -1, 0, 1]),
                          ('interaction', [1, -1, -1, 1])]:
        values = [sum(a * b for a, b in zip(row, weights)) for row in means]
        boot = [sum(a * b for a, b in zip(row, weights)) for row in bootstrap]
        contrasts.append(dict(name=name, ratio_of_layout_ratios=math.exp(statistics.mean(values)),
                              pointwise95_interval=interval(boot)))
    return dict(cells=cells, secondary_contrasts=contrasts, bootstrap_replicates=repetitions,
                bootstrap_seed=freeze['seed'], requests=freeze['total_requests'],
                measurements=freeze['measurements'], warmups=freeze['warmups'],
                uncertainty_scope='Process-session bootstrap; fixed exposed inputs, one host/date')


def summarize_control(rows, arms, ninput):
    index = {}
    for r in rows:
        key = (r['session'], r['input_index'], r['arm'], r['category'])
        require(key not in index, 'duplicate closeout slot')
        require(math.isfinite(r['seconds']) and r['seconds'] > 0, 'invalid closeout time')
        index[key] = r['seconds']
    expected = {(s, i, a, c) for s in range(4) for i in range(ninput)
                for a in arms for c in ['warmup', 'measured']}
    require(set(index) == expected, 'incomplete closeout panel')
    blocks = []
    ref, left, right, candidate = arms
    for s in range(4):
        for i in range(ninput):
            d = {a: index[s, i, a, 'measured'] for a in arms}
            control = (d[left] + d[right]) / 2
            blocks.append(dict(session=s, input_index=i, candidate_over_dual_control=d[candidate] / control,
                               candidate_over_R=d[candidate] / d[ref], dual_control_over_R=control / d[ref],
                               aa=d[left] / d[right]))
    out = {field: gm([b[field] for b in blocks])
           for field in ['candidate_over_dual_control', 'candidate_over_R', 'dual_control_over_R']}
    out['aa_max_input'] = max(abs(gm([b['aa'] for b in blocks if b['input_index'] == i]) - 1)
                              for i in range(ninput))
    out['session_ratios'] = [gm([b['candidate_over_dual_control'] for b in blocks if b['session'] == s])
                             for s in range(4)]
    out['practical_screen_pass'] = (1 - out['candidate_over_dual_control'] > max(.02, out['aa_max_input'])
                                    and all(x < 1 for x in out['session_ratios']))
    out['reversed_blocks'] = sum(b['candidate_over_dual_control'] > 1 for b in blocks)
    out['measured_requests'] = len(blocks) * len(arms)
    out['warmup_requests'] = len(blocks) * len(arms)
    out['paired_blocks'] = len(blocks)
    return out


def compare_fields(actual, expected, name):
    for key, value in actual.items():
        if key in expected:
            require(derived_equal(value, expected[key]), name + ' source-estimate mismatch: ' + key)


def closeouts(base):
    timing = csv_rows(base / 'closeout/rtx/results/TIMING_RECORDS.csv')
    require(len(timing) == 768, 'incomplete RTX transfer timing')
    groups = {}
    for row in timing:
        stage, session, family, item, arm, category = row['slot'].split('/')
        require(stage == 'E2' and family in ('Qwen', 'SmolLM2'), 'unexpected transfer timing family')
        require(row['exit_ok'] == row['identity_ok'] == 'True', 'unqualified transfer timing')
        groups.setdefault(family, []).append(dict(session=int(session), input_index=int(item),
             arm=arm, category=category, seconds=float(row['seconds'])))
    estimates = read_json(base / 'closeout/rtx/results/ESTIMATES.json')
    transfer = {family: summarize_control(rows, ['R', 'PQ_A', 'PQ_B', 'QB'], 12)
                for family, rows in groups.items()}
    qualification = read_json(base / 'closeout/rtx/results/INDEPENDENT_E1.json')
    for family, values in transfer.items():
        compare_fields(values, estimates[family], family)
        evidence = qualification[family]
        require(evidence['complete_qualified'] is True and evidence['q_gt_one_verification_witness'] is True,
                'transfer qualification not complete: ' + family)
        require({row['input_index'] for row in evidence['cells']} == set(range(12))
                and len(evidence['cells']) == 12 and all(not row['errors'] for row in evidence['cells']),
                'transfer qualification input coverage differs: ' + family)
        values['reported_reference_qualified_inputs'] = len(evidence['cells'])
    examples = read_json(base / 'closeout/rtx/results/COUNTEREXAMPLES.json')
    compact = []
    for item in examples:
        a, b = item['reference_output']['ids'], item['observed_output']['ids']
        first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y),
                     min(len(a), len(b)) if len(a) != len(b) else None)
        require(first == item['first_different_output_index_zero_based'], 'counterexample mismatch')
        compact.append({k: v for k, v in item.items()
                        if k not in ('reference_output', 'observed_output', 'worker')})
    llama = [r for r in examples if r['stage'] == 'E1' and r['family'] == 'Llama']
    require(len(llama) == 2 and {r['arm'] for r in llama} == {'PQ', 'QB'}, 'Llama counterexample missing')
    require(all(r['prompt_tokens'] == 737 and r['first_different_output_index_zero_based'] == 81
                and r['task_id'] == 'CodeContests/valid/108' for r in llama), 'Llama counterexample identity changed')
    require(llama[0]['observed_output'] == llama[1]['observed_output'], 'Llama PQ/QB endpoint differs')
    require(qualification['Llama']['complete_qualified'] is False
            and estimates['Llama']['status'] == 'NO_QUALIFIED_COMPLETE_COST_PANEL',
            'Llama failure disposition changed')
    ledger = read_json(base / 'closeout/rtx/results/RESOURCE_LEDGER.json')
    require(ledger['request_slot_counts'] == {'COMPLETED': 1018, 'NOT_RUN': 758}, 'transfer dispositions changed')
    normalized = read_json(base / 'closeout/b570/NORMALIZED_RECORDS.json')
    require(len(normalized) == 128 and all(r['qualified'] and r['exit_ok'] for r in normalized),
            'unqualified/incomplete B570 prefill timing')
    prefill = summarize_control(normalized, ['R', 'BASE_A', 'BASE_B', 'SUBMIT'], 4)
    compare_fields(prefill, read_json(base / 'closeout/b570/INDEPENDENT_ANALYSIS.json'), 'B570 prefill')
    table = csv_rows(base / 'closeout/b570/TIMING_TABLE.csv')
    by_slot = {r['slot']: r for r in normalized}
    require(len(table) == len(by_slot), 'B570 timing-table size mismatch')
    for row in table:
        require(float(row['service_seconds']) == by_slot[row['slot']]['seconds'] and
                float(row['request_seconds']) == by_slot[row['slot']]['request_seconds'],
                'B570 normalized/table cost mismatch')
    review = read_json(base / 'closeout/b570review/REVIEW_FINAL.json')
    return dict(transfer=transfer, transfer_counterexamples=compact,
                transfer_request_disposition=ledger['request_slot_counts'],
                transfer_llama_cost='NOT_RUN; no qualified estimate',
                b570_prefill=prefill,
                b570_prefill_fully_protocol_resource_compliant=review['fully_protocol_resource_compliant'])


def analyse(root=ROOT):
    root = Path(root)
    source_count = authenticate(root)
    base = root / DATA
    freeze = read_json(base / 'rtx_bridge/FREEZE.json')
    bridge = compute_bridge(reconstruct_bridge(csv_rows(base / 'rtx_bridge/TIMING.csv'), freeze), freeze)
    registered = read_json(base / 'rtx_bridge/ANALYSIS.json')
    for actual, expected in zip(bridge['cells'], registered['cells']):
        compare_fields(actual, expected, 'RTX bridge cell')
    for actual, expected in zip(bridge['secondary_contrasts'], registered['secondary_contrasts']):
        compare_fields(actual, expected, 'RTX bridge contrast')
    summary = read_json(base / 'b570_native/SUMMARY.json')
    native = {key: summary[key] for key in ['status', 'model_requests', 'model_processes', 'stage_processes',
              'stage_graph_computes', 'historical_full_vector_comparisons', 'ordinary_panel_vectors', 'ordinary_panel_requests']}
    native['scope'] = 'Authenticated source-host summary; no native replay or raw-vector audit by this script'
    require(sum(row['requests'] for row in summary['slots']) == native['model_requests'], 'native request accounting mismatch')
    require(sum(row['stage_computes'] for row in summary['slots']) == native['stage_graph_computes'], 'native stage accounting mismatch')
    native['retained_wrapper_failures'] = [row['slot'] for row in summary['slots'] if row['wrapper_status'] == 'failed']
    return dict(status='COMPACT_RECONSTRUCTION_PASS', source_files_authenticated=source_count,
                derived_float_absolute_tolerance=DERIVED_ABS_TOL, rtx_bridge=bridge,
                closeouts=closeouts(base), b570_native_reported=native, new_native_requests=0)


def bridge_table(result):
    lines = [r'\begin{table*}[t]\centering\small',
             r'\caption{Matched Qwen3 deployment bridge. Ratios compare QB with the arithmetic mean of identical PQ controls; aggregation gives equal weight to inputs and process sessions. Intervals are the registered Bonferroni-adjusted session-bootstrap intervals for the four-cell family. The practical screen also requires reduction above the A/A threshold and improvement in every session.}',
             r'\label{tab:nativebridge}', r'\begin{tabular}{@{}rlll@{}}\toprule',
             r'$k$ & Lifecycle & QB/dual-PQ [simultaneous interval] & Practical gain\\\midrule']
    for cell in result['rtx_bridge']['cells']:
        low, high = cell['simultaneous_family95_interval']
        status = 'Established' if cell['practical_gain_established'] else 'Not established'
        lines.append(f"{cell['k']} & {cell['lifecycle'].capitalize()} & {cell['ratio']:.6f} [{low:.6f}, {high:.6f}] & {status}" + r'\\')
    lines += [r'\bottomrule\end{tabular}', r'\end{table*}']
    return '\n'.join(lines) + '\n'


def transfer_table(result):
    lines = [r'\begin{table*}[t]\centering\small',
             r'\caption{Transfer to previously unexposed inputs within context1024. Each family has a registered 12-input panel. Qwen3 and SmolLM2 complete all inputs; the Llama reference failure stops that family before cost measurement. The layout screen uses a 2\% floor, input-aggregate A/A and every-session direction; no population interval is assigned.}',
             r'\label{tab:heldouttransfer}',
             r'\begin{tabular}{@{}llll@{}}\toprule',
             r'Family & Reference qualification & QB/dual-PQ (screen) & QB/R\\\midrule']
    for key, label in [('Qwen', 'Qwen3'), ('SmolLM2', 'SmolLM2')]:
        row = result['closeouts']['transfer'][key]
        screen = 'pass' if row['practical_screen_pass'] else 'not established'
        qualified = row['reported_reference_qualified_inputs']
        lines.append(f"{label} & {qualified}/12 inputs pass & {row['candidate_over_dual_control']:.6f} ({screen}) & {row['candidate_over_R']:.6f}" + r'\\')
    lines += [r'Llama & PQ and QB both depart from R & Not run & Not run\\',
              r'\bottomrule\end{tabular}', r'\end{table*}']
    return '\n'.join(lines) + '\n'


def outputs(root=ROOT):
    result = analyse(root)
    return {str(DATA / 'DERIVED.json'): json.dumps(result, indent=2, allow_nan=False) + '\n',
            'tables/native_bridge.tex': bridge_table(result),
            'tables/heldout_transfer.tex': transfer_table(result)}


def verify(check, root=ROOT):
    """Check existing artifacts without overwriting them; caller controls reporting."""
    expected = outputs(root)
    for name, text in expected.items():
        path = Path(root) / name
        if name.endswith('.json'):
            actual = read_json(path)
            consistent = derived_equal(actual, json.loads(text))
        else:
            consistent = path.read_text() == text
        check('Native follow-up source/derived consistency: ' + name, consistent)
    return {'status': 'PASS', 'source_files_authenticated': json.loads(next(iter(expected.values())))['source_files_authenticated'],
            'derived_outputs_checked': len(expected), 'new_native_requests': 0}


def main():
    for name, text in outputs().items():
        path = ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    print('Generated native follow-up summaries/tables from authenticated source records.')


if __name__ == '__main__':
    main()
