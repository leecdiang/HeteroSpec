"""Recompute equality gates and paired, same-work latency ratios from raw JSON."""
import argparse
import csv
import json
from pathlib import Path
from statistics import median

def identity(record):
    r = record['response']
    return (r['tokens'], r['stop_type'], r['stopping_word'], r['truncated'])

def first_diff(a, b):
    return next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)) if len(a) != len(b) else None)

def analyze(run):
    records = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(run.glob('r[0-9]_*_*.json'))
               if not p.name.endswith(('_command.json', '_warmup.json'))]
    refs = {(r['round'], r['task']): r for r in records if r['condition'] == 'target'}
    pairs = []
    for r in records:
        base = refs.get((r['round'], r['task']))
        if base is None:
            continue
        t = r['response']['timings']
        bt = base['response']['timings']
        pairs.append({'round': r['round'], 'condition': r['condition'], 'task': r['task'], 'group': r['group'],
            'exact': identity(r) == identity(base), 'first_diff': first_diff(base['response']['tokens'], r['response']['tokens']),
            'tokens': len(r['response']['tokens']), 'ref_tokens': len(base['response']['tokens']),
            'stop': r['response']['stop_type'], 'ref_stop': base['response']['stop_type'],
            'wall_ms': r['wall_ms'], 'ref_wall_ms': base['wall_ms'], 'wall_speedup': base['wall_ms'] / r['wall_ms'],
            'gen_ms': t['predicted_ms'], 'ref_gen_ms': bt['predicted_ms'], 'gen_speedup': bt['predicted_ms'] / t['predicted_ms'],
            'prompt_ms': t['prompt_ms'], 'cached': t['cache_n'],
            'draft_n': t.get('draft_n', 0), 'draft_accepted': t.get('draft_n_accepted', 0)})
    tasks = sorted({r['task'] for r in records})
    stable = {task: len({json.dumps(identity(r), sort_keys=True) for r in refs.values() if r['task'] == task}) == 1 for task in tasks}
    summary = []
    for condition in sorted({p['condition'] for p in pairs}):
        for label in sorted({p['group'] for p in pairs}) + tasks:
            ps = [p for p in pairs if p['condition'] == condition and (p['group'] == label or p['task'] == label)]
            if not ps:
                continue
            rounds = sorted({p['round'] for p in ps})
            wall = [sum(p['ref_wall_ms'] for p in ps if p['round'] == rnd) / sum(p['wall_ms'] for p in ps if p['round'] == rnd) for rnd in rounds]
            gen = [sum(p['ref_gen_ms'] for p in ps if p['round'] == rnd) / sum(p['gen_ms'] for p in ps if p['round'] == rnd) for rnd in rounds]
            exact = all(p['exact'] and stable[p['task']] for p in ps)
            dn, da = sum(p['draft_n'] for p in ps), sum(p['draft_accepted'] for p in ps)
            summary.append({'condition': condition, 'scope': label, 'requests': len(ps), 'rounds': len(rounds),
                'exact_matches': sum(p['exact'] for p in ps), 'reference_stable': all(stable[p['task']] for p in ps),
                'qualified': exact, 'median_wall_speedup': median(wall), 'min_wall_speedup': min(wall),
                'median_gen_speedup': median(gen), 'min_gen_speedup': min(gen),
                'acceptance': da / dn if dn else None,
                'advance': condition != 'target' and len(rounds) >= 3 and exact and median(wall) >= 1 / 0.9 and min(wall) > 1 and min(gen) > 1})
    result = {'records': len(records), 'pairs': len(pairs), 'reference_stability': stable, 'summary': summary}
    (run / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    for name, rows in [('paired.csv', pairs), ('summary.csv', summary)]:
        if rows:
            with (run / name).open('w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('run', type=Path)
    analyze(ap.parse_args().run)
