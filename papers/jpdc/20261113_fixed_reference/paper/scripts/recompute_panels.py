"""CPU-only independent root bootstrap of the retained public timing rows."""
import argparse
import csv
import json
import math
import random
from pathlib import Path


def percentile(values, p):
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    lower, upper = math.floor(position), math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def estimate(plan, records):
    roots, arms, rounds = plan['roots'], plan['arms'], plan['sessions']
    expected = {(r, s, a) for r in roots for s in range(rounds) for a in arms}
    values = {}
    for record in records:
        key = (record['root'], int(record['session']), record['arm'])
        value = float(record['service_s'])
        if key not in expected or key in values or not math.isfinite(value) or value <= 0:
            raise ValueError('Unknown, duplicate, or invalid timing row')
        values[key] = value
    if values.keys() != expected:
        raise ValueError('Incomplete panel; successful-subset inference is forbidden')
    n = len(roots)
    totals = {a: [math.fsum(values[r, s, a] for s in range(rounds)) for r in roots]
              for a in arms}
    rng = random.Random(plan['seed'])
    indices = [[rng.randrange(n) for _ in roots] for _ in range(plan['bootstrap_draws'])]
    draws = {a: [math.fsum(totals[a][i] for i in ix) for ix in indices] for a in arms}
    family = len(plan['contrasts']) + bool(plan.get('interaction'))
    tail = 0.05 / family / 2
    contrasts = []
    for candidate, control in plan['contrasts']:
        ratios = [x / y for x, y in zip(totals[candidate], totals[control])]
        samples = [x / y for x, y in zip(draws[candidate], draws[control])]
        contrasts.append(dict(
            numerator=candidate, denominator=control,
            total_ratio=math.fsum(totals[candidate]) / math.fsum(totals[control]),
            interval=[percentile(samples, tail), percentile(samples, 1 - tail)],
            root_ratios=ratios,
            equal_root_geometric=math.exp(math.fsum(map(math.log, ratios)) / n),
            session_ratios=[math.fsum(values[r, s, candidate] for r in roots) /
                            math.fsum(values[r, s, control] for r in roots)
                            for s in range(rounds)]))
    interaction = None
    if plan.get('interaction'):
        lp, wl4, wp, ll4 = plan['interaction']
        logs = [math.log(totals[lp][i]) + math.log(totals[wl4][i]) -
                math.log(totals[wp][i]) - math.log(totals[ll4][i]) for i in range(n)]
        samples = [math.exp(math.fsum(logs[i] for i in ix) / n) for ix in indices]
        interaction = dict(
            definition='geomean((L_P/W_P)/(L_L4/W_L4)) across roots',
            ratio=math.exp(math.fsum(logs) / n),
            interval=[percentile(samples, tail), percentile(samples, 1 - tail)])
    return dict(scope=plan['sample_scope'], metric=plan['metric'], root_count=n,
                adjusted_family_size=family, inference=plan['inference'],
                bootstrap_draws=plan['bootstrap_draws'], seed=plan['seed'],
                conditional_on_observed_sessions=True, all_fixed_controls=contrasts,
                interaction=interaction,
                totals={a: math.fsum(totals[a]) for a in arms},
                no_historical_timing_pooling=True)


def compare(actual, expected, where='result'):
    if isinstance(expected, dict):
        if actual.keys() != expected.keys():
            raise ValueError('Different result fields: ' + where)
        for key in expected:
            compare(actual[key], expected[key], where + '.' + key)
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError('Different result length: ' + where)
        for i, (a, e) in enumerate(zip(actual, expected)):
            compare(a, e, where + '[' + str(i) + ']')
    elif type(expected) is float:
        if not math.isclose(actual, expected, rel_tol=2e-12, abs_tol=2e-12):
            raise ValueError('Numerical mismatch: ' + where)
    elif actual != expected:
        raise ValueError('Different result: ' + where)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', type=Path, default=Path(__file__).parent / 'statistics')
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    reports = []
    for study in ('pr204', 'pr205', 'pr206', 'pr208'):
        folder = args.data / study
        plan = json.loads((folder / 'PLAN.json').read_text())
        with (folder / 'TIMING_ROWS.csv').open(newline='') as f:
            rows = list(csv.DictReader(f))
        actual = estimate(plan, rows)
        expected = json.loads((folder / 'ORIGINAL_RESULTS.json').read_text())
        compare(actual, expected)
        reports.append(dict(study=study, status='PASS_INDEPENDENT_ALL_ESTIMANDS',
                            rows=len(rows), result=actual))
    result = dict(status='PASS', model_calls=0, GPU_contexts=0,
                  method='Independent math.fsum implementation; original root order, seed, draws, family and estimands',
                  numeric_comparison_tolerance=2e-12, reports=reports)
    if args.out:
        with args.out.open('x') as f:
            json.dump(result, f, indent=2)
            f.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'model_calls', 'GPU_contexts')}))
    print('Independent complete-panel rows:', sum(x['rows'] for x in reports))


if __name__ == '__main__':
    main()
