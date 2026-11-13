"""CPU-only S3 stratified root inference and descriptive two-case free-service sums."""
import argparse
import csv
import json
import math
import random
from pathlib import Path

from recompute_panels import percentile, compare


def estimate_s3(rows):
    measured = [r for r in rows if r['role'] == 'measured']
    if len(rows) != 288 or len(measured) != 144:
        raise ValueError('Incomplete warm/measured panel')
    lookup = {}
    roots = {}
    for row in rows:
        slot = int(row['slot'])
        if slot in roots and roots[slot] != row['root']:
            raise ValueError('Mixed root identity within slot')
        roots[slot] = row['root']
        key = (int(row['slot']), int(row['round']), row['arm'], row['role'])
        if key in lookup or not math.isfinite(float(row['service_s'])) or float(row['service_s']) <= 0:
            raise ValueError('Duplicate or invalid service row')
        lookup[key] = float(row['service_s'])
    expected = {(s, r, a, role) for s in range(12) for r in range(4)
                for a in 'GBC' for role in ('warm', 'measured')}
    if lookup.keys() != expected:
        raise ValueError('Wrong S3 slots')
    if len(set(roots.values())) != 12:
        raise ValueError('Repeated root cannot be treated as independent roots')
    for row in rows:
        if row['domain'] != ('code' if int(row['slot']) < 6 else 'math'):
            raise ValueError('Wrong frozen stratum assignment')
    totals = {a: math.fsum(lookup[s, r, a, 'measured'] for s in range(12) for r in range(4))
              for a in 'GBC'}
    contrasts = []
    for candidate, control, confidence in [('C', 'B', .95), ('B', 'G', .975), ('C', 'G', .975)]:
        logs = [math.fsum(math.log(lookup[s, r, candidate, 'measured'] /
                                  lookup[s, r, control, 'measured']) for r in range(4)) / 4
                for s in range(12)]
        rng = random.Random(20261110)
        boot = []
        for _ in range(20000):
            code = math.fsum(logs[rng.randrange(6)] for _ in range(6)) / 6
            math_stratum = math.fsum(logs[6 + rng.randrange(6)] for _ in range(6)) / 6
            boot.append(math.exp((code + math_stratum) / 2))
        tail = (1 - confidence) / 2
        contrasts.append(dict(candidate=candidate, baseline=control, confidence=confidence,
                              ratio=math.exp(math.fsum(logs) / 12),
                              interval=[percentile(boot, tail), percentile(boot, 1 - tail)],
                              ratio_of_totals=totals[candidate] / totals[control]))
    return dict(totals=totals, contrasts=contrasts, roots=12, rounds=4,
                bootstrap_draws=20000, seed=20261110)


def estimate_free(rows):
    values = {}
    for row in rows:
        key = (row['case'], int(row['round']), row['arm'])
        response, reset, service = (float(row[k]) for k in ('response_s', 'reset_s', 'service_s'))
        total = response + reset
        if (key in values or not all(math.isfinite(v) and v >= 0 for v in (response, reset, service))
                or total <= 0 or abs(total - service) > 1e-10):
            raise ValueError('Invalid descriptive pair or overlapping-clock sum')
        values[key] = total
    if values.keys() != {(c, r, a) for c in ('C0', 'C1') for r in range(2) for a in 'WL'}:
        raise ValueError('Incomplete two-case paired panel')
    totals = {a: math.fsum(v for (c, r, arm), v in values.items() if arm == a) for a in 'WL'}
    return dict(totals=totals, L_over_W=totals['L'] / totals['W'], measured_episodes=8)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', type=Path, default=Path(__file__).parent / 'statistics' / 'service')
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    with (args.data / 'S3_TIMINGS.csv').open(newline='') as f:
        s3 = estimate_s3(list(csv.DictReader(f)))
    with (args.data / 'FREE_EPISODES.csv').open(newline='') as f:
        free = estimate_free(list(csv.DictReader(f)))
    actual = dict(S3=s3, free=free)
    compare(actual, json.loads((args.data / 'ORIGINAL_RESULTS.json').read_text()))
    result = dict(status='PASS_S3_AND_FREE_STATISTICS', result=actual,
                  model_calls=0, GPU_contexts=0,
                  limits='S3 root-level inference; free is descriptive, no population CI. No raw tensor comparison.')
    if args.out:
        with args.out.open('x') as f:
            json.dump(result, f, indent=2)
            f.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
