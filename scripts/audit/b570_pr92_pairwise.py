"""Read-only CPU audit of the pinned PR92 archive. Never imports archived code."""
import argparse
import collections
import hashlib
import io
import itertools
import json
import math
import os
from pathlib import Path
import statistics
import urllib.request
import zipfile

REPO = 'leecdiang/HeteroSpec'
HEAD = '82946adf946491e6cf7fef761bcc1ec0772e914e'
MANIFEST_SHA = '9980272eb9490eccc137da47480f279af24ab37f0a6e21138006c658bc0ece27'
CAS_SHA = '94f2d57e3292544a2c4849725493da69289e0a22b429d124524ed2c9fbf36c58'
PARTS = [
    ('189f29cf31cbd0c72c7d08528a937a51f3a2e1ef', 50331648,
     '1bbcd96b47acd3389a63e7d8fcb2644c3d45ac0fa31695ad89d651ed55a01fc2'),
    ('a456fa5f65b28dfd328b2aab1c5835d1f56d53d7', 5433127,
     'ce7ef78c89713be9d6f5e55409d497fd4c2a84569f025e5560321018d6a7092a')]
ARMS = ['R_stock', 'R_prod', 'M_match', 'N_k1', 'C_k1']
EOG = {128001, 128008, 128009}

def digest_bytes(b):
    return hashlib.sha256(b).hexdigest()

def blob(sha):
    req = urllib.request.Request(
        f'https://api.github.com/repos/{REPO}/git/blobs/{sha}',
        headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                 'Accept': 'application/vnd.github.raw+json',
                 'User-Agent': 'HeteroSpec-CPU-pairwise-audit'})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()

def read_json(b):
    return json.loads(b.decode('utf-8-sig'))

def signature(record):
    o = record['output']
    ids, flags = o['ids'], o['eog_flags']
    assert isinstance(ids, list) and 0 < len(ids) <= 128
    assert all(type(i) is int and i >= 0 for i in ids)
    assert all(type(f) is bool for f in flags)
    assert flags == [i in EOG for i in ids] and not any(flags[:-1])
    assert o['length'] == len(ids) and o['terminal_id'] == ids[-1]
    assert (flags[-1] and o['stop_reason'] == 'EOG') or (
        not flags[-1] and len(ids) == 128 and o['stop_reason'] == 'CAP')
    assert o['cached_tokens'] == 0 and o['truncated'] is False
    return (tuple(ids), tuple(flags), len(ids), ids[-1], o['stop_reason'])

def first_difference(a, b):
    for i, (x, y) in enumerate(itertools.zip_longest(a, b)):
        if x != y:
            return {'index': i, 'left_id': x, 'right_id': y}
    return None

def pairwise(records):
    assert len(records) == 1200
    tasks = sorted({r['task'] for r in records})
    assert len(tasks) == 24
    assert collections.Counter(t.split('/')[0] for t in tasks) == {'MBPP': 12, 'GSM8K': 12}
    rows, signatures = {}, {}
    for r in records:
        assert r['phase'] == 'formal' and r['status'] == 'COMPLETED' and r['warmup'] is False
        assert r['family'] == 'Llama' and r['condition'] in ARMS
        assert r['session'] in (0, 1) and r['round'] in range(5)
        k = (r['task'], r['session'], r['round'], r['condition'])
        assert k not in rows, 'duplicate request coordinate'
        assert math.isfinite(r['wall_ms']) and r['wall_ms'] > 0
        assert r['measurement_mode'] == 'counts'
        assert r['observation'] == {'phase_timers': False, 'heavy_capture': False,
                                    'etw': False, 'added_sync': False}
        rows[k] = r
        signatures[k] = signature(r)
    expected = set(itertools.product(tasks, range(2), range(5), ARMS))
    assert set(rows) == expected, 'missing arm/task/session/round'
    stable = {}
    for arm in ARMS:
        stable[arm] = all(len({signatures[(t,s,j,arm)] for s in range(2) for j in range(5)}) == 1
                          for t in tasks)
    matrix = []
    for a, b in itertools.combinations(ARMS, 2):
        mismatch = []
        task_rows = []
        for t in tasks:
            unequal = []
            for s in range(2):
                for j in range(5):
                    ka, kb = (t,s,j,a), (t,s,j,b)
                    assert rows[ka]['input_sha256'] == rows[kb]['input_sha256']
                    if signatures[ka] != signatures[kb]:
                        unequal.append({'session':s, 'round':j,
                            'first_difference':first_difference(signatures[ka][0],signatures[kb][0])})
            if unequal:
                mismatch.append({'task':t,'count':len(unequal),'differences':unequal})
            ratios = []
            for s in range(2):
                ma = statistics.median(rows[(t,s,j,a)]['wall_ms'] for j in range(5))
                mb = statistics.median(rows[(t,s,j,b)]['wall_ms'] for j in range(5))
                ratios.append(ma/mb)
            task_rows.append({'task':t,'domain':t.split('/')[0],
                              'ratio':math.exp(statistics.mean(map(math.log,ratios))),
                              'session_ratios':ratios})
        ratio = math.exp(statistics.mean(math.log(r['ratio']) for r in task_rows))
        matrix.append({'pair':a+'/'+b,'matched_requests':240-sum(x['count'] for x in mismatch),
                       'planned_requests':240,'matched_tasks':24-len(mismatch),
                       'both_arms_stable':stable[a] and stable[b],
                       'complete_pairwise_equal':not mismatch and stable[a] and stable[b],
                       'diagnostic_cost_ratio':ratio,
                       'negative_tasks':sum(r['ratio']<1 for r in task_rows),
                       'domains':{d:math.exp(statistics.mean(math.log(r['ratio']) for r in task_rows
                                                           if r['domain']==d)) for d in ['MBPP','GSM8K']},
                       'mismatches':mismatch,'task_effects':task_rows})
    return {'status':'CPU_FULL_OUTPUT_PAIRWISE_AUDIT_COMPLETE','source_head':HEAD,
            'formal_records':1200,'stable_by_arm':stable,'pairs':matrix,
            'scope':'post-hoc complete pairwise audit; original R_stock qualification is not changed',
            'model_status':'MODEL_TIMING_UNAVAILABLE','physical_residency':'UNKNOWN'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='audit-output');args=ap.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    manifest_bytes=blob('9c84ca9b97d982995643f61208a25150dc96f29e')
    assert digest_bytes(manifest_bytes)==MANIFEST_SHA
    manifest=read_json(manifest_bytes)
    pieces=[]
    for sha,size,h in PARTS:
        b=blob(sha);assert len(b)==size and digest_bytes(b)==h
        pieces.append(b)
    cas=b''.join(pieces);assert digest_bytes(cas)==CAS_SHA
    assert zipfile.is_zipfile(io.BytesIO(cas)), 'archive is not ZIP'
    z=zipfile.ZipFile(io.BytesIO(cas));names=z.namelist()
    print('CAS_LAYOUT '+json.dumps(names[:12]))
    file_entries={f['path']:f for f in manifest['files']}
    assert len(file_entries)==manifest['logical_files']==7379
    objects={}
    hashes={f['sha256'] for f in file_entries.values()}
    for name in names:
        for part in name.split('/'):
            if part in hashes:
                assert part not in objects, 'ambiguous object hash'
                objects[part]=name
    assert hashes<=set(objects), 'archive object layout not recognized'
    checked={}
    for h,name in objects.items():
        b=z.read(name);assert digest_bytes(b)==h
        checked[h]=len(b)
    assert all(checked[f['sha256']]==f['bytes'] for f in file_entries.values())
    def read(path):
        return read_json(z.read(objects[file_entries[path]['sha256']]))
    records=read('FORMAL_RECORDS.json')
    print('RECORD_SCHEMA '+json.dumps({'type':type(records).__name__,
          'sample':records[0] if isinstance(records,list) else list(records)})[:16000])
    first_raw=next(p for p in file_entries if p.startswith('raw/formal') and p.endswith('.RESULT.json'))
    print('RAW_SCHEMA '+json.dumps({'path':first_raw,'sample':read(first_raw)})[:16000])
    result=pairwise(records)
    result['archive_verification']={'status':'ALL_MANIFEST_FILES_HASH_VERIFIED',
        'manifest_sha256':MANIFEST_SHA,'archive_sha256':CAS_SHA,
        'logical_files':len(file_entries),'unique_objects':len(objects),
        'formal_records_sha256':file_entries['FORMAL_RECORDS.json']['sha256'],
        'models_rehashed':False,'archived_code_executed':False,'new_model_forwards':0}
    (out/'PAIRWISE_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    compact={k:v for k,v in result.items() if k!='pairs'}
    compact['pairs']=[{k:v for k,v in p.items() if k not in ('task_effects','mismatches')} for p in result['pairs']]
    print('AUDIT_RESULT '+json.dumps(compact,ensure_ascii=False))
    # Small source excerpts assist static attribution review, never execution.
    excerpts={}
    for p in ['code/runtime.py','code/formal.py','native/worker.cpp','code/independent_verify.py']:
        if p in file_entries:
            data=z.read(objects[file_entries[p]['sha256']]).decode('utf-8-sig')
            (out/Path(p).name).write_text(data)
            excerpts[p]={'sha256':file_entries[p]['sha256'],'bytes':file_entries[p]['bytes']}
    (out/'SOURCE_EXCERPTS.json').write_text(json.dumps(excerpts,indent=2)+'\n')

if __name__=='__main__':main()
