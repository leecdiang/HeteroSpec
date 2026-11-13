"""CPU panel preparation, session files, and paired-root analysis. Standard library only."""
import argparse
import collections
import json
import math
from pathlib import Path
import random
import statistics


def read_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def length_bin(n):
    if not 1 <= n <= 768:
        raise ValueError('prompt outside 1..768')
    return next(i for i, top in enumerate((128, 256, 512, 768)) if n <= top)


def tokens(xs, n=None):
    if not isinstance(xs, list) or not xs or any(type(x) is not int or x < 0 for x in xs):
        raise ValueError('token IDs must be nonnegative integers, not booleans')
    if n is not None and len(xs) != n:
        raise ValueError('continuation must contain exactly 128 tokens')


def panel(candidates):
    buckets = collections.defaultdict(list)
    seen = set()
    identities = set()
    for c in candidates:
        root = c['root']
        if not isinstance(root, str) or not root or root in seen:
            raise ValueError('duplicate/invalid root')
        seen.add(root)
        if not c.get('source') or not c.get('tokenizer_identity'):
            raise ValueError('missing provenance/tokenizer')
        identities.add(c['tokenizer_identity'])
        tokens(c['prompt_ids']); tokens(c['continuation_ids'], 128)
        b = length_bin(len(c['prompt_ids']))
        if c['domain'] not in ('code', 'math'):
            raise ValueError('domain must be code or math')
        buckets[b, c['domain']].append(dict(c, length_bin=b))
    if len(identities) != 1:
        raise ValueError('panel mixes tokenizer identities')
    chosen = []
    for b in range(4):
        for domain in ('code', 'math'):
            items = sorted(buckets[b, domain], key=lambda x: x['root'])
            if len(items) < 2:
                raise ValueError(f'need two distinct {domain} roots in bin {b}; do not pad')
            chosen.extend(items[:2])
    return chosen


def schedule(p):
    if len(p) != 16 or len({r['root'] for r in p}) != 16:
        raise ValueError('expected 16 distinct roots')
    sessions = []
    serial = 0
    for mode, orders in [('P', ('RM', 'MR', 'MR', 'RM')), ('G', ('RM', 'MR'))]:
        for block, order in enumerate(orders):
            offset = (4*block) % 16
            roots = p[offset:] + p[:offset]
            for arm in order:
                session = []
                for warm, c in [(True, roots[0])] + [(False, c) for c in roots]:
                    serial += 1
                    session.append(dict(c, id=serial, mode=mode, block=block, arm=arm, warmup=warm))
                sessions.append(session)
    return sessions


def prepare(candidates, output):
    p = panel(candidates)
    out = Path(output); out.mkdir(parents=True, exist_ok=False)
    (out/'panel.json').write_text(json.dumps(p, indent=2), encoding='utf-8')
    sessions = schedule(p)
    for i, s in enumerate(sessions):
        stem = f'{i:02d}_{s[0]["mode"]}_{s[0]["arm"]}'
        (out/(stem+'.json')).write_text(json.dumps(s, indent=2), encoding='utf-8')
        lines = []
        for r in s:
            values = [r['id'], r['mode'], len(r['prompt_ids']), 128] + r['prompt_ids'] + r['continuation_ids']
            lines.append(' '.join(map(str, values)))
        (out/(stem+'.tsv')).write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return {'sessions': len(sessions), 'formal_requests': 192, 'warmups': 12,
            'qualification_not_in_schedule': 16, 'reserve': 8, 'status': 'CPU_PREPARED'}


def analyze(records, mode='P', draws=20000):
    if mode not in ('P', 'G'):
        raise ValueError('mode')
    rows = [r for r in records if r.get('mode') == mode and not r.get('warmup')]
    indexed = {}
    bins = {}
    expected_blocks = 4 if mode == 'P' else 2
    for r in rows:
        key = (r['root'], r['block'], r['arm'])
        if key in indexed or r['arm'] not in ('R', 'M') or r['block'] not in range(expected_blocks):
            raise ValueError('duplicate or unknown measurement key')
        if r.get('status') != 'ok' or not math.isfinite(r['seconds']) or r['seconds'] <= 0:
            raise ValueError('failed/nonfinite measurement; do not silently discard')
        if r['root'] in bins and bins[r['root']] != r['length_bin']:
            raise ValueError('inconsistent stratum')
        bins[r['root']] = r['length_bin']
        indexed[key] = r
    if len(bins) != 16 or len(indexed) != 16*expected_blocks*2:
        raise ValueError('incomplete formal panel; descriptive partial report required')
    estimates = {}
    for root in sorted(bins):
        logs = []
        for block in range(expected_blocks):
            r, m = (indexed[root, block, arm] for arm in ('R', 'M'))
            if r['prompt_ids'] != m['prompt_ids']:
                raise ValueError('different prompt work')
            if mode == 'P' and (r['continuation_ids'] != m['continuation_ids'] or r['rows'] != m['rows']):
                raise ValueError('different fixed continuation work')
            logs.append(math.log(m['seconds']/r['seconds']))
        estimates[root] = statistics.mean(logs)
    groups = [[r for r in estimates if bins[r] == b] for b in range(4)]
    if any(len(g) != 4 for g in groups):
        raise ValueError('expected four roots per stratum')
    rng = random.Random(244)
    boot = sorted(math.exp(statistics.mean(estimates[rng.choice(g)] for g in groups for _ in g)) for _ in range(draws))
    ratio = math.exp(statistics.mean(estimates.values()))
    return {'mode': mode, 'ratio_M_over_R': ratio, 'root_ratios': {k: math.exp(v) for k,v in estimates.items()},
            'ci95': [boot[int(.025*draws)], boot[min(draws-1, int(.975*draws))]],
            'unit': 'root', 'roots': 16, 'blocks': expected_blocks,
            'interpretation': 'fixed-work replay' if mode == 'P' else 'own-greedy, unequal work possible'}


def collect(directory):
    result = []
    for path in sorted(Path(directory).glob('[0-9][0-9]_*.json')):
        specs = json.loads(path.read_text(encoding='utf-8'))
        raw = read_jsonl(path.with_suffix('.results.jsonl'))
        if not raw or raw[-1].get('event') != 'done':
            raise ValueError('worker did not complete: '+str(path))
        receipts = [x for x in raw if x.get('event') == 'request']
        if [x['id'] for x in receipts] != [x['id'] for x in specs]:
            raise ValueError('receipt order/count mismatch')
        for spec, receipt in zip(specs, receipts):
            if receipt['mode'] != spec['mode']:
                raise ValueError('mode mismatch')
            if spec['mode'] == 'P' and (receipt['tokens'] != spec['continuation_ids'] or receipt['rows'] != len(spec['prompt_ids'])+128):
                raise ValueError('fixed-work receipt mismatch')
            result.append(dict(spec, **{k:v for k,v in receipt.items() if k not in spec}, status='ok'))
    return result


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    sub = a.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('prepare'); p.add_argument('candidates'); p.add_argument('output')
    p = sub.add_parser('analyze'); p.add_argument('directory'); p.add_argument('--mode', choices=['P','G'], default='P')
    x = a.parse_args()
    print(json.dumps(prepare(read_jsonl(x.candidates), x.output) if x.cmd == 'prepare' else analyze(collect(x.directory), x.mode), indent=2))
