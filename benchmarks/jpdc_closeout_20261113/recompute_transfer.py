"""CPU-only independent PR203 transfer statistics; NumPy is needed for frozen PCG64 draws."""
import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

from recompute_panels import compare, percentile


def estimate(plan, rows):
    roots, arms = plan['roots'], plan['arms']
    values = {}
    expected = {(r, s, a) for r in roots for s in range(4) for a in arms}
    for row in rows:
        key = row['root'], int(row['session']), row['arm']
        value = float(row['service_s'])
        if key not in expected or key in values or not math.isfinite(value) or value <= 0:
            raise ValueError('Unknown, duplicate, or invalid transfer row')
        values[key] = value
    if values.keys() != expected:
        raise ValueError('Incomplete transfer panel')
    totals = {a: [math.fsum(values[r, s, a] for s in range(4)) for r in roots] for a in arms}
    draws = np.random.Generator(np.random.PCG64(plan['bootstrap_seed'])).integers(
        0, len(roots), (plan['bootstrap_draws'], len(roots)))
    boot = {a: [math.fsum(totals[a][int(i)] for i in ix) for ix in draws] for a in arms}
    contrasts = []
    tail = .05 / len(plan['primary']) / 2
    for a, b in plan['primary']:
        ratios = [x / y for x, y in zip(totals[a], totals[b])]
        samples = [x / y for x, y in zip(boot[a], boot[b])]
        contrasts.append(dict(numerator=a, denominator=b,
            total_ratio=math.fsum(totals[a]) / math.fsum(totals[b]),
            adjusted_interval=[percentile(samples, tail), percentile(samples, 1-tail)],
            per_root=ratios,
            per_session=[math.fsum(values[r, s, a] for r in roots) /
                         math.fsum(values[r, s, b] for r in roots) for s in range(4)],
            equal_root_geometric=math.exp(math.fsum(map(math.log, ratios)) / len(roots))))
    return dict(totals_s={a: math.fsum(totals[a]) for a in arms}, contrasts=contrasts)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', type=Path, default=Path(__file__).parent / 'statistics' / 'pr203')
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    plan = json.loads((args.data / 'PLAN.json').read_text())
    with (args.data / 'TIMING_ROWS.csv').open(newline='') as f:
        rows = list(csv.DictReader(f))
    actual = estimate(plan, rows)
    saved = json.loads((args.data / 'ORIGINAL_RESULTS.json').read_text())
    compare(actual, {k: saved[k] for k in ('totals_s', 'contrasts')})
    result = dict(status='PASS_INDEPENDENT_TIMING_ESTIMANDS', rows=len(rows),
                  numpy_version=np.__version__, model_calls=0, GPU_contexts=0,
                  limitation='Timing statistics only; host clocks and numerical tensors not requalified',
                  result=actual)
    if args.out:
        with args.out.open('x') as f:
            json.dump(result, f, indent=2)
            f.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'rows', 'numpy_version')}))


if __name__ == '__main__':
    main()
