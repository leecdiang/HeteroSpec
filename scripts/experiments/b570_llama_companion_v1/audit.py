"""Reconstruct decisions and complete paired costs; raw outputs are never repaired."""
from __future__ import annotations
from array import array
from collections import Counter
import math
from pathlib import Path
import sys
from common import VOCAB, endpoint, need, read, sha
from design import ARMS, TIMING


def full_vector(path):
    data = Path(path).read_bytes()
    need(len(data) == VOCAB * 4, 'incomplete full-vocabulary vector')
    values = array('f');values.frombytes(data)
    if sys.byteorder != 'little': values.byteswap()
    need(all(math.isfinite(v) for v in values), 'nonfinite vector')
    best = max(range(len(values)), key=values.__getitem__)
    return best, sha(path)


def transactions(r):
    endpoint(r)
    cycles = r['cycles']
    if not r['slot']['arm'].startswith('C_'):
        need(not cycles, 'ordinary path has speculative cycles')
        return {i: ('initial' if i == 0 else f'ordinary-{i}') for i in range(r['length'])}
    generated = [r['ids'][0]]; mapping = {0: 'initial'};base = len(r['prompt_ids'])
    for ci, c in enumerate(cycles):
        need(c['cycle'] == ci and c['base'] == base and c['output_begin'] == len(generated), 'cycle identity')
        p, d = c['proposals'], c['decisions']
        need(len(p) == 3 and len(d) == 4, 'fixed k3 geometry; do not stop proposals at draft EOG')
        need(c['verify_ids'] == [generated[-1]] + p, 'pending ownership')
        a = 0; emitted = []; bonus = False
        for j, proposal in enumerate(p):
            match = d[j] == proposal
            if match: a += 1
            emitted.append(d[j])
            out_index = len(generated) + len(emitted) - 1
            need(out_index < r['length'], 'cycle emits past output')
            if r['eog'][out_index] or out_index + 1 == 128 or not match:
                break
        else:
            bonus = True;emitted.append(d[-1])
        need(emitted == c['emitted'] and a == c['accepted'] and bonus == c['bonus'], 'accept/correction/bonus mismatch')
        for j, token in enumerate(emitted):
            mapping[len(generated)] = f'verify-{ci}-{j}'
            generated.append(token)
        keep = base + 1 + a
        need(c['keep'] == keep and c['target_kv_max'] == keep - 1 and c['draft_kv_max'] == keep - 1, 'KV reconciliation')
        base = keep
    need(generated == r['ids'], 'emitted trajectory mismatch')
    return mapping


def record(path):
    path = Path(path);r = read(path);transactions(r)
    need(r['slot']['input']['prompt_ids'] == r['prompt_ids'] and r['slot']['input']['id'] == r['input_id'], 'request identity')
    need(r['diagnostic'] == (r['slot'].get('trace', False) or r['slot'].get('probe_cycle', -1) >= 0), 'diagnostic flag')
    if r['slot']['stage'] in ('qualification', 'warmup', 'measured', 'reference'):
        need(not r['diagnostic'], 'diagnostic leaked into confirmation')
    checked = {}
    if r['slot']['observer'] == 'heavy':
        names = {'target/initial.f32': r['ids'][0]}
        if r['slot']['arm'].startswith('C_'):
            for c in r['cycles']:
                for i, token in enumerate(c['proposals']): names[f'draft/proposal-{c["cycle"]}-{i}.f32'] = token
                for i, token in enumerate(c['decisions']): names[f'target/verify-{c["cycle"]}-{i}.f32'] = token
        else:
            names.update({f'target/ordinary-{i}.f32': t for i, t in enumerate(r['ids'][1:], 1)})
        root = path.with_suffix('')
        actual = {p.relative_to(root).as_posix() for role in ('target', 'draft') for p in (root / role).glob('*.f32')}
        need(actual == set(names), 'vector inventory differs')
        for name, token in names.items():
            best, h = full_vector(root / name);need(best == token, 'saved argmax differs: ' + name);checked[name] = h
        need((root / 'target_final.state').is_file(), 'missing target state')
        if r['slot']['arm'].startswith('C_'): need((root / 'draft_final.state').is_file(), 'missing draft state')
        # Actual scheduler metadata, not weight or buffer ownership.
        need(r['geometry'] and all(g.get('scheduler_backend') for g in r['geometry']), 'scheduler evidence absent')
        if r['slot']['arm'] != 'R':
            prefix = 'hs_qb_qk-' if 'QB' in r['slot']['arm'] else 'hs_pq_qk-'
            nodes = [g for g in r['geometry'] if g['name'].startswith(prefix)]
            layers = {int(g['name'].rsplit('-', 1)[-1]) for g in nodes}
            need(layers == set(range(32)), 'local transform not observed in all 32 layers')
            for g in nodes:
                n, q, heads, batches = g['ne']
                need(n in (256, 512, 768, 1024) and q == 1 and heads == 32, 'unadmitted QK output')
                need(2 <= batches <= 4 if 'QB' in r['slot']['arm'] else batches == 1, 'query batch mapping')
    return {'record': r, 'endpoint': endpoint(r), 'vectors': checked, 'record_sha256': sha(path)}


def matrix(candidate_paths, oracle_paths, expected_ids):
    candidates = [record(p) for p in candidate_paths];oracles = [record(p) for p in oracle_paths]
    def indexed(rows):
        out = {}
        for x in rows:
            r = x['record'];key = (r['input_id'], r['slot']['arm'], r['slot']['observer'])
            need(key not in out, 'duplicate matrix cell');out[key] = x
        return out
    c, o = indexed(candidates), indexed(oracles)
    need(set(o) == {(i, 'R', obs) for i in expected_ids for obs in ('off', 'heavy')}, 'incomplete oracle matrix')
    need(set(c) == {(i, arm, obs) for i in expected_ids for arm in ARMS for obs in ('off', 'heavy')}, 'incomplete candidate matrix')
    cells = []; all_ok = True
    for i in expected_ids:
        need(o[i, 'R', 'off']['endpoint'] == o[i, 'R', 'heavy']['endpoint'], 'oracle observer instability')
        for arm in ARMS:
            a, b = c[i, arm, 'off'], c[i, arm, 'heavy']
            stable = a['endpoint'] == b['endpoint'] and a['record']['cycles'] == b['record']['cycles']
            reference = a['endpoint'] == o[i, 'R', 'off']['endpoint']
            reference_vectors = b['vectors'] == o[i, 'R', 'heavy']['vectors'] if arm == 'R' else None
            all_ok &= stable and reference and reference_vectors is not False
            cells.append({'input_id': i, 'arm': arm, 'observer_stable': stable,
                          'local_reference_equal': reference, 'candidate_R_full_vectors_equal': reference_vectors})
    pairs=[]
    for i in expected_ids:
        for prefix in ('M_', 'C_'):
            a,b=c[i,prefix+'PQ','heavy'],c[i,prefix+'QB','heavy']
            pairs.append({'input_id':i, 'path':prefix, 'full_vectors_equal':a['vectors']==b['vectors'],
                          'transactions_equal':a['record']['cycles']==b['record']['cycles']})
    return {'local_pairs':pairs, 'pure_layout_correspondence':all(p['full_vectors_equal'] and p['transactions_equal'] for p in pairs),
            'status': 'QUALIFIED' if all_ok else 'REFERENCE_OR_CONTROL_FAILURE', 'all_reference_equal': bool(all_ok),
            'cells': cells, 'reference': 'frozen B570 stock oracle; not CUDA output',
            'requests': len(c) + len(o)}


def gm(values):
    need(values and all(math.isfinite(x) and x > 0 for x in values), 'nonpositive cost')
    return math.exp(math.fsum(map(math.log, values)) / len(values))


def performance(rows, panel_ids, sessions=6):
    need(sessions == 6, 'frozen six-period design')
    grouped = {}
    for r in rows:
        s = r['slot']
        if s['stage'] != 'measured': continue
        need(not r['diagnostic'] and r['performance_eligible'], 'unqualified timer')
        key = (s['session'], r['input_id'], s['label'])
        need(key not in grouped, 'duplicate measured coordinate')
        grouped[key] = r['service_seconds']
    need(set(grouped) == {(s, i, a) for s in range(sessions) for i in panel_ids for a in TIMING}, 'incomplete paired costs')
    blocks = []
    for s in range(sessions):
        for i in panel_ids:
            t = {a: grouped[s, i, a] for a in TIMING}
            need(all(math.isfinite(v) and v > 0 for v in t.values()), 'invalid seconds')
            pq = (t['C_PQ_A'] + t['C_PQ_B']) / 2
            blocks.append({'session': s, 'input_id': i, 'seconds': t,
                'layout': t['C_QB'] / pq, 'AA': t['C_PQ_A'] / t['C_PQ_B'],
                'D_QB': t['M_QB'] / t['C_QB'], 'D_PQ': t['M_PQ'] / pq,
                'CQB_R': t['C_QB'] / t['R'], 'MQB_R': t['M_QB'] / t['R']})
    means = {k: gm([b[k] for b in blocks]) for k in ('layout', 'AA', 'D_QB', 'D_PQ', 'CQB_R', 'MQB_R')}
    aa = [gm([b['AA'] for b in blocks if b['input_id'] == i]) for i in panel_ids]
    threshold = max(.02, max(max(x, 1/x)-1 for x in aa))
    session_ratios = [gm([b['layout'] for b in blocks if b['session'] == s]) for s in range(sessions)]
    return {'blocks': blocks, 'means': means, 'AA_threshold': threshold, 'session_layout': session_ratios,
            'practical_layout_screen': 1-means['layout'] > threshold and all(x < 1 for x in session_ratios),
            'QB_slower_blocks': sum(b['layout'] > 1 for b in blocks), 'no_population_independence_claim': True}
