"""Deterministic CPU planner/selector and normalized-report checks. NOT a native runner."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent
SENTINELS = ('1248', '831', '1011', '1249')
ARMS = ('R', 'M_R', 'C_R_PQ', 'C_R_QH')
PILOT = ('R', 'R_SHADOW', 'M_R', 'C_R_MQ', 'C_R_PQ', 'C_R_QH')
GROUPS = tuple((d, b) for d in ('code', 'math') for b in ('short', 'medium', 'long'))
BINS = {'short': (64, 127), 'medium': (128, 255), 'long': (256, 512)}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha_valid(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def load(path):
    def unique(pairs):
        result = {}
        for k, v in pairs:
            require(k not in result, 'duplicate JSON key: ' + k)
            result[k] = v
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def write_new(path, data):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def cell_key(domain, stratum, i):
    return f'{domain}:{stratum}:{i}'


def validate_panel(panel):
    require(isinstance(panel, list) and len(panel) == 24, '24 panel entries required')
    cells, ids, prompts = set(), set(), set()
    for row in panel:
        require(isinstance(row, dict), 'panel row')
        d, b, i = row['domain'], row['stratum'], row['index']
        require((d, b) in GROUPS and type(i) is int and 0 <= i < 4, 'panel coordinate')
        key = cell_key(d, b, i)
        require(row['task_key'] == key and key not in cells, 'duplicate/wrong task key')
        require(isinstance(row['id'], str) and row['id'].strip(), 'source id')
        uid = (d, row['id'])
        require(uid not in ids, 'duplicate source id')
        require(sha_valid(row['prompt_sha256']) and sha_valid(row['token_ids_sha256']), 'input hash')
        require(row['prompt_sha256'] not in prompts, 'duplicate prompt')
        require(type(row['token_count']) is int and BINS[b][0] <= row['token_count'] <= BINS[b][1], 'token stratum')
        cells.add(key); ids.add(uid); prompts.add(row['prompt_sha256'])
    require(len(cells) == 24, 'panel incomplete')


def select(candidates, exposure):
    """Host supplies pinned tokenizer metadata; selection never reads outputs/timing."""
    require(isinstance(candidates, list), 'candidate inventory list')
    require(isinstance(exposure, dict) and exposure.get('inventory_audited') is True, 'audited exposure inventory required')
    require(sha_valid(exposure.get('inventory_sha256')), 'exposure source hash')
    require(isinstance(exposure.get('coverage'), str) and exposure['coverage'].strip(), 'exposure coverage disclosure')
    exposed = exposure['prompt_sha256']
    require(isinstance(exposed, list) and all(sha_valid(x) for x in exposed), 'exposure prompt hashes')
    buckets = defaultdict(list); seen_ids = set(); seen_prompts = set()
    for row in candidates:
        require(isinstance(row, dict), 'candidate row')
        require(not any(k in row for k in ('answer', 'latency', 'correct', 'logits', 'speedup')), 'outcome fields prohibited')
        d = row['domain']; require(d in ('code', 'math'), 'candidate domain')
        require(isinstance(row['id'], str) and row['id'].strip(), 'candidate id')
        uid = (d, row['id']); require(uid not in seen_ids, 'duplicate candidate id'); seen_ids.add(uid)
        require(type(row['token_count']) is int and row['token_count'] > 0, 'token count')
        require(sha_valid(row['prompt_sha256']) and sha_valid(row['token_ids_sha256']), 'candidate hash')
        # Inventory itself must deduplicate identical texts, including aliases.
        require(row['prompt_sha256'] not in seen_prompts, 'duplicate candidate prompt')
        seen_prompts.add(row['prompt_sha256'])
        if row['prompt_sha256'] in exposed:
            continue
        for b, (lo, hi) in BINS.items():
            if lo <= row['token_count'] <= hi:
                rank = hashlib.sha256(('b570-paper-support-v1|' + d + '|' + row['id'] + '|' + row['prompt_sha256']).encode()).hexdigest()
                buckets[d, b].append((rank, row))
    panel = []
    for d, b in GROUPS:
        require(len(buckets[d, b]) >= 4, f'unfilled stratum: {d}/{b}')
        for i, (_, row) in enumerate(sorted(buckets[d, b], key=lambda x: x[0])[:4]):
            panel.append({**{k: row[k] for k in ('id', 'domain', 'prompt_sha256', 'token_ids_sha256', 'token_count')},
                          'stratum': b, 'index': i, 'task_key': cell_key(d, b, i)})
    validate_panel(panel)
    return panel


def plan():
    processes = []
    def proc(stage, pid, kind, requests=None, **extra):
        processes.append(dict(stage=stage, process_id=pid, kind=kind, requests=requests or [], **extra))
    def request(pid, suffix, **kw):
        return dict(request_id=f'{pid}/{suffix}', **kw)
    for t in SENTINELS:
        pid = f'S1/capture/{t}'
        proc('S1', pid, 'model', [request(pid, k, task=t, role=k, arm='C_R_MQ')
                                for k in ('warmup', 'capture', 'observer')])
    proc('S1', 'S1/census', 'census', graph_computes=0)
    # q1 controls first; identity freezes map 0/last to actual model layer indices.
    for q in (1, 2):
        for t in SENTINELS:
            for layer in ('0', 'last'):
                for repeat in (0, 1):
                    for arm in ('MQ', 'PQ', 'QH_C'):
                        pid = f'S1/replay/{t}/{layer}/q{q}/{arm}/r{repeat}'
                        proc('S1', pid, 'operator', graph_computes=1, task=t, layer=layer,
                             q=q, arm=arm, repeat=repeat, derived_control=q == 1)
    # All original/shadow controls first. No performance selection of candidate order.
    for arm in PILOT[:2]:
        for t in SENTINELS:
            for rep in (0, 1):
                pid = f'S2/counts/{t}/{arm}/{rep}'
                proc('S2', pid, 'model', [request(pid, 'request', task=t, arm=arm, role='counts', repeat=rep)])
    for ti, t in enumerate(SENTINELS):
        for rep in (0, 1):
            arms = list(PILOT[2:]); shift = (ti + rep) % len(arms); arms = arms[shift:] + arms[:shift]
            if rep: arms.reverse()
            for arm in arms:
                pid = f'S2/counts/{t}/{arm}/{rep}'
                proc('S2', pid, 'model', [request(pid, 'request', task=t, arm=arm, role='counts', repeat=rep)])
    for t in SENTINELS:
        for arm in ('C_R_PQ', 'C_R_QH'):
            pid = f'S2/heavy/{t}/{arm}'
            proc('S2', pid, 'model', [request(pid, 'request', task=t, arm=arm, role='heavy')])
    for session in range(3):
        for block, (d, b) in enumerate(GROUPS):
            arms = list(ARMS); shift = (block + session) % 4; arms = arms[shift:] + arms[:shift]
            if session % 2: arms.reverse()
            for arm in arms:
                pid = f'S3/s{session}/b{block}/{arm}'
                reqs = [request(pid, 'warmup', session=session, block=block, arm=arm, role='warmup',
                                task_key=cell_key(d, b, 0), repeat=None)]
                for rep in (0, 1):
                    order = list(range(4)); rotation = (session + block) % 4
                    order = order[rotation:] + order[:rotation]
                    if rep: order.reverse()
                    for i in order:
                        reqs.append(request(pid, f'r{rep}/t{i}', session=session, block=block, arm=arm,
                                            role='measured', task_key=cell_key(d, b, i), repeat=rep))
                proc('S3', pid, 'model', reqs)
    ids = [p['process_id'] for p in processes]
    reqids = [r['request_id'] for p in processes for r in p['requests']]
    require(len(ids) == len(set(ids)) and len(reqids) == len(set(reqids)), 'duplicate plan identity')
    totals = dict(model_requests=len(reqids), model_process_attempts=sum(p['kind'] == 'model' for p in processes),
                  operator_and_census_process_attempts=sum(p['kind'] != 'model' for p in processes),
                  native_process_attempts=len(processes), standalone_graph_computes=sum(p.get('graph_computes', 0) for p in processes))
    require(totals == load(ROOT / 'BUDGET.json')['totals'], 'budget/plan disagreement')
    return dict(schema=1, status='ABSTRACT_PLAN_NOT_EXECUTION_F0', processes=processes, totals=totals)


def analyze(panel, rows):
    validate_panel(panel)
    require(isinstance(rows, list), 'records list')
    tasks = {r['task_key']: r for r in panel}
    expected = {r['request_id']: r for p in plan()['processes'] if p['stage'] == 'S3' for r in p['requests']}
    actual = {}; failures = []
    for row in rows:
        require(isinstance(row, dict) and row.get('request_id') in expected, 'unknown request')
        rid = row['request_id']; require(rid not in actual, 'duplicate request')
        e = expected[rid]
        for k in ('session', 'block', 'arm', 'role', 'task_key', 'repeat'):
            require(row.get(k) == e[k] and type(row.get(k)) is type(e[k]), 'request coordinate mismatch: ' + k)
        require(row.get('prompt_sha256') == tasks[e['task_key']]['prompt_sha256'] and
                row.get('token_ids_sha256') == tasks[e['task_key']]['token_ids_sha256'], 'input identity mismatch')
        require(type(row.get('qualified')) is bool, 'qualified must be boolean')
        if row['qualified']:
            require(sha_valid(row.get('endpoint_sha256')) and sha_valid(row.get('raw_sha256')), 'missing endpoint/raw hash')
            require(isinstance(row.get('raw_path'), str) and row['raw_path'].strip(), 'raw path')
            t = row.get('duration_ms')
            require(type(t) in (int, float) and math.isfinite(t) and 0 < t <= 1200000,
                    'positive finite duration within S3 process ceiling')
        else:
            require(isinstance(row.get('reason'), str) and row['reason'].strip(), 'invalid record needs reason')
            failures.append(rid)
        actual[rid] = row
    missing = sorted(set(expected) - set(actual))
    refs = {}; unstable = []
    for key in tasks:
        rids = [rid for rid, e in expected.items() if e['task_key'] == key and e['arm'] == 'R']
        vals = [actual[rid] for rid in rids if rid in actual and actual[rid]['qualified']]
        endpoints = {r['endpoint_sha256'] for r in vals}
        if len(vals) == len(rids) and len(endpoints) == 1:
            refs[key] = next(iter(endpoints))
        else:
            unstable.append(key)
    bad = defaultdict(list)
    for rid, e in expected.items():
        row = actual.get(rid)
        if row is None or not row['qualified'] or refs.get(e['task_key']) != row.get('endpoint_sha256'):
            bad[e['arm']].append(rid)
    comparisons = {}
    for numerator in ('C_R_PQ', 'M_R', 'R'):
        name = numerator + '/C_R_QH'
        admitted = not missing and not unstable and not bad[numerator] and not bad['C_R_QH']
        out = dict(qualified=admitted, ratio=None, sessions=None, task_session_rows=[], strata=[], regressions=[], summed_time_ratio=None)
        if admitted:
            values = defaultdict(list); sums = Counter()
            for row in actual.values():
                if row['role'] == 'measured' and row['arm'] in (numerator, 'C_R_QH'):
                    values[row['task_key'], row['session'], row['arm']].append(row['duration_ms'])
                    sums[row['arm']] += row['duration_ms']
            logs = defaultdict(list); strata = defaultdict(list); tasklogs = defaultdict(list)
            for key in sorted(tasks):
                for s in range(3):
                    a = values[key, s, numerator]; b = values[key, s, 'C_R_QH']
                    require(len(a) == len(b) == 2, 'two repeats required')
                    ratio = statistics.median(a) / statistics.median(b); v = math.log(ratio)
                    logs[s].append(v); tasklogs[key].append(v)
                    strata[tasks[key]['domain'], tasks[key]['stratum']].append(v)
                    out['task_session_rows'].append(dict(task_key=key, session=s, ratio=ratio))
            sessions = [math.exp(statistics.mean(logs[s])) for s in range(3)]
            out.update(ratio=math.exp(statistics.mean([statistics.mean(logs[s]) for s in range(3)])), sessions=sessions,
                       summed_time_ratio=sums[numerator]/sums['C_R_QH'])
            out['strata'] = [dict(domain=d, stratum=b, ratio=math.exp(statistics.mean(v))) for (d, b), v in sorted(strata.items())]
            out['regressions'] = [dict(task_key=k, ratio=math.exp(statistics.mean(v))) for k, v in sorted(tasklogs.items()) if statistics.mean(v) < 0]
        comparisons[name] = out
    primary = comparisons['C_R_PQ/C_R_QH']
    verdict = 'UNQUALIFIED_OR_INCOMPLETE'
    if primary['qualified']:
        verdict = 'MEASURED_FIXED_PANEL_GAIN' if primary['ratio'] > 1.02 and all(x > 1 for x in primary['sessions']) else 'QUALIFIED_TRANSFER_NO_PREDECLARED_GAIN'
    return dict(status=verdict, expected_requests=len(expected), observed_requests=len(actual), missing=missing,
                failed=failures, unstable_or_missing_reference_tasks=unstable,
                unqualified_by_arm={a: bad[a] for a in ARMS}, comparisons=comparisons,
                scope='Normalized report arithmetic only; independent host raw/timing/placement/control audit required. No native authenticity or population inference.')


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='action', required=True)
    a = sub.add_parser('plan'); a.add_argument('--output', required=True)
    a = sub.add_parser('select'); a.add_argument('--candidates', required=True); a.add_argument('--exposure', required=True); a.add_argument('--output', required=True)
    a = sub.add_parser('analyze'); a.add_argument('--panel', required=True); a.add_argument('--records', required=True); a.add_argument('--output', required=True)
    a = p.parse_args()
    if a.action == 'plan': result = plan()
    elif a.action == 'select': result = select(load(a.candidates), load(a.exposure))
    else: result = analyze(load(a.panel), load(a.records))
    write_new(a.output, result)
    print(json.dumps({'written': a.output, 'status': result.get('status') if isinstance(result, dict) else 'PANEL_SELECTED'}))


if __name__ == '__main__':
    main()
