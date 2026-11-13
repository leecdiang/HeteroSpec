"""Saved-data analysis; never starts a native worker or modifies input evidence."""
import argparse
import json
import math
from pathlib import Path
import random
from native import read, write


def estimate(points):
    """Resample whole roots within domain, preserving dates and rounds."""
    rng = random.Random(20261113)
    domains = [[p['mean_log_CB'] for p in points if p['domain'] == d] for d in ('code', 'math')]
    samples = sorted(math.exp(sum(rng.choice(group) for group in domains for _ in group) / 12) for _ in range(20000))
    def quantile(p):
        index = (len(samples) - 1) * p
        i = int(index)
        return samples[i] + (samples[min(i + 1, len(samples) - 1)] - samples[i]) * (index - i)
    ratio = math.exp(sum(p['mean_log_CB'] for p in points) / 12)
    return dict(CB=ratio, reduction_percent=100 * (1 - ratio), CI95=[quantile(.025), quantile(.975)],
                simultaneous_CI975=[quantile(.0125), quantile(.9875)], root_count=12, bootstrap_draws=20000,
                unit='paired root within domain; rounds/dates remain attached', roots=points)


def panel_data(root, panel):
    path = root / panel
    if not path.exists(): return dict(status='NOT_STARTED'), []
    status = read(path / 'STATUS.json') if (path / 'STATUS.json').exists() else dict(status='STARTING')
    rows = read(path / 'ROWS.json') if (path / 'ROWS.json').exists() else []
    measured = [x for x in rows if x['role'] == 'measured']
    pairs = {}
    for row in measured: pairs.setdefault(row['pair_id'], {})[row['arm']] = row
    points = []
    complete = [p for p in pairs.values() if set(p) == {'B', 'C'}]
    for slot in range(12):
        selected = [p for p in complete if p['B']['slot'] == slot]
        if selected:
            logs = [math.log(p['C']['elapsed_s'] / p['B']['elapsed_s']) for p in selected]
            points.append(dict(slot=slot, root_id=selected[0]['B']['root_id'], domain='code' if slot < 6 else 'math',
                               mean_log_CB=sum(logs) / len(logs), CB=math.exp(sum(logs) / len(logs)),
                               rounds=[dict(round=p['B']['round'], B_s=p['B']['elapsed_s'], C_s=p['C']['elapsed_s'],
                                            CB=p['C']['elapsed_s'] / p['B']['elapsed_s'],
                                            first=min(p, key=lambda a: p[a]['start_ns'])) for p in selected]))
    result = dict(**status, checked_clean_requests=len(rows), complete_measured_pairs=len(complete), roots=points)
    if status['status'] == 'COMPLETE' and len(measured) == 48 and len(points) == 12 and all(len(p['rounds']) == 2 for p in points):
        result['estimate'] = estimate(points)
    else: result['inference'] = 'Partial: paired observations descriptive; registered full-panel estimate unavailable'
    result['phases'] = {}
    for arm in ('B', 'C'):
        selected = [x for x in measured if x['arm'] == arm]
        sums = {key: sum(x[key] for x in selected) for key in ('elapsed_s', 'reset_s', 'prefill_s', 'decode_s', 'planning_s', 'owned_output_copy_s')}
        sums['unpartitioned_residual_s'] = sums['elapsed_s'] - sum(v for k, v in sums.items() if k != 'elapsed_s')
        result['phases'][arm] = dict(requests=len(selected), **sums)
    result['order_check'] = {first: [p['C']['elapsed_s'] / p['B']['elapsed_s'] for p in complete if min(p, key=lambda a:p[a]['start_ns']) == first] for first in ('B', 'C')}
    return result, points


def analyze(root, out):
    results = {}; points = {}
    for panel in ('R1', 'R2', 'H1'):
        results[panel], points[panel] = panel_data(root, panel)
    if all('estimate' in results[p] for p in ('R1', 'R2')):
        combined = []
        for first, second in zip(points['R1'], points['R2']):
            value = (first['mean_log_CB'] + second['mean_log_CB']) / 2
            combined.append(dict(slot=first['slot'], root_id=first['root_id'], domain=first['domain'], mean_log_CB=value,
                                 CB=math.exp(value), dates=[first, second]))
        results['R_combined'] = dict(estimate=estimate(combined), scope='Conditional on these two tested dates; no population-of-days interval')
    else: results['R_combined'] = dict(status='NOT_COMPLETE', scope='Both registered dates required')
    ledger = [json.loads(x) for x in (root / 'requests.jsonl').read_text().splitlines()] if (root / 'requests.jsonl').exists() else []
    reserved = [x for x in ledger if x['event'] == 'RESERVE']
    results['accounting'] = {c: dict(requests=sum(x['requests'] for x in reserved if c == 'ALL' or x['cohort'] == c),
                                   reserved_rows=sum(x['reserved_rows'] for x in reserved if c == 'ALL' or x['cohort'] == c),
                                   workers=sum(c == 'ALL' or x['cohort'] == c for x in reserved)) for c in ('R', 'H', 'ALL')}
    results['historical_S3'] = dict(CB=.9848637428511184, included_in_new_estimates=False)
    results['H_scope'] = 'Prospectively selected new workload; later project exposure unknown'
    write(out, results)
    return results


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True); p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(); analyze(a.root, a.out)
