"""Separate parser for the original raw subset; does not import study helpers."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ART = 'artifacts/b570_prefill_diagnostic_v1'
DOC = 'benchmarks/b570_prefill_diagnostic_v1'
TASKS = [58,156,134,42,122,114,93,115,151,63,125,133,43,139,77,35,27,34,145,82,154,78,96,138]
CASES = {134,42,145,138}
CONDITIONS = ['R','T0','N0','T1','N1']

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def normalized(capture):
    ids = capture.get('ids', capture.get('generated_ids'))
    flags = capture['eog']
    assert ids and len(ids) == len(flags)
    assert all(type(i) is int and 0 <= i < 151936 for i in ids)
    assert all(type(f) is bool for f in flags)
    stop = next((i + 1 for i, flag in enumerate(flags) if flag), None)
    count = min(128, stop if stop is not None else len(ids))
    assert count == 128 or flags[count - 1]
    return (tuple(ids[:count]), tuple(flags[:count]), 'EOG' if flags[count-1] else 'CAP128')

def record_endpoint(record):
    return (tuple(record['ids']), tuple(record['eog']), record['endpoint'])

def main(root, predictions, output):
    protocol = load(root / DOC / 'PROTOCOL.json')
    assert protocol['tasks'] == ['HumanEval/' + str(t) for t in TASKS]
    assert protocol['conditions'] == CONDITIONS and protocol['repetitions'] == 3
    assert protocol['planned'] == 360 and not protocol['performance_claims']
    original = load(predictions)['predictions']
    expected = {(p['task_id'], p['repetition']): p for p in original}
    records, captures, arrays = {}, {}, {}
    graph_rows = []
    for path in sorted((root / ART / 'formal').glob('*/result.json')):
        r = load(path)
        key = (int(r['task'].split('/')[1]), r['variant'], r['rep'])
        assert key not in records and r['valid'] and r['exit_code'] == 0
        assert r['protocol_sha256'] == digest(root / DOC / 'PROTOCOL.json')
        x = load(root / r['capture'])
        a = normalized(x)
        assert a == record_endpoint(r)
        assert x['prompt_ids'] == load(root / ART / 'inputs' / r['task'].replace('/','_') / 'prompt_ids.json')
        for name, expected_hash in r['files'].items():
            if not name.endswith(('.kv', '.f32')):
                assert digest(root / name) == expected_hash, name
        args = r['command']
        def flag(name):
            assert args.count(name) == 1
            return args[args.index(name) + 1]
        for name, value in {'--device':'Vulkan0','--n-gpu-layers':'all','--ctx-size':'1024',
                            '--batch-size':'512','--temp':'0','--seed':'123','--flash-attn':'off'}.items():
            assert flag(name) == value, (key,name)
        native = r['variant'].startswith('N')
        assert flag('--ubatch-size') == ('128' if r['variant']=='R' else '1')
        assert flag('--n-predict') == ('127' if native else '128')
        env = r['env_overrides']
        assert set(env) == {'HS_PREFILL_OUTPUT','HS_PREFILL_UB','HS_MECHANISM_INPUT_IDS','HS_MECHANISM_OUTPUT'}
        assert env['HS_PREFILL_UB'] == ('128' if r['variant'] in ['R','T1','N1'] else '1')
        stderr = (root / r['capture']).parent / 'stderr.txt'
        text = stderr.read_text(errors='replace')
        assert 'using device Vulkan0 (Intel(R) Arc(TM) B570 Graphics)' in text
        offload = re.findall(r'offloaded\s+(\d+)/(\d+) layers to GPU', text)
        assert ('37','37') in offload
        if native:
            assert ('29','29') in offload
            assert flag('--spec-draft-n-max') == '2'
            assert flag('--spec-draft-device') == 'Vulkan0'
        if r['variant'] in ['R','T0','N0']:
            old = expected[(r['task'],r['rep'])]
            assert list(a[0]) == old['reference_ids' if r['variant']=='R' else 'predicted_ids']
        assert [c['id'] for c in x['commits']] == x['ids']
        assert [c['eog'] for c in x['commits']] == x['eog']
        if r['variant'] != 'R':
            move = x['transfer']
            assert move['source_ub'] == (128 if r['variant'] in ['T1','N1'] else 1)
            assert move['destination_ub'] == 1 and move['consumed_bytes'] == move['state_bytes']
            assert move['before'] == move['after'] == move['source_after']
            assert move['before']['min'] == 0 and move['before']['max'] == len(x['prompt_ids'])-1
            assert move['pending_id'] == x['ids'][0]
            assert move['sampler_chain'] == move['clone_chain']
            assert move['sampler_history'] == move['clone_history'] and move['seed'] == move['clone_seed'] == 123
            hashes = [value for name,value in r['files'].items() if name.endswith(('.before.kv','.restored.kv','.source_after.kv'))]
            assert len(hashes) == 3 and len(set(hashes)) == 1
        target_prefill = []
        for entry in x['trace']:
            if entry['event'] != 'decode':
                continue
            assert entry['exit_code'] == 0
            assert entry['caller_batch_length'] == len(entry['input_ids']) == len(entry['positions']) == len(entry['sequence_ids'])
            assert all(seq == [0] for seq in entry['sequence_ids'])
            if entry['role']=='draft':
                assert entry['ub_capacity'] == 1
            if entry['phase']=='continuation':
                assert entry['ub_capacity'] == (128 if r['variant']=='R' else 1)
            if entry['role']=='target' and entry['phase']=='prefill':
                assert entry['ub_capacity'] == (128 if r['variant'] in ['R','T1','N1'] else 1)
                target_prefill.append(entry)
        assert [i for e in target_prefill for i in e['input_ids']] == x['prompt_ids']
        assert [p for e in target_prefill for p in e['positions']] == list(range(len(x['prompt_ids'])))
        if native:
            assert [e['caller_batch_length'] for e in target_prefill] == [len(x['prompt_ids'])-1, 1]
        else:
            assert [e['caller_batch_length'] for e in target_prefill] == [len(x['prompt_ids'])]
        sizes = [g['ne1'] for e in target_prefill for g in e['graphs'] if g['tensor']=='embd']
        assert sizes and sum(sizes) == len(x['prompt_ids'])
        assert max(sizes) <= (128 if r['variant'] in ['R','T1','N1'] else 1)
        graph_rows.append({'task':r['task'],'condition':r['variant'],'rep':r['rep'],
                           'prefill_caller_lengths':[e['caller_batch_length'] for e in target_prefill],
                           'occupied_graph_tokens':sizes})
        records[key], captures[key], arrays[key] = r, x, a
    assert set(records) == {(t,c,r) for t in TASKS for c in CONDITIONS for r in range(1,4)}
    rows=[]
    for task in TASKS:
        row={'task':'HumanEval/'+str(task),'diagnostic':task in CASES}
        for left,right in [('T0','N0'),('T1','N1'),('N0','R'),('N1','R')]:
            row[left+'_'+right] = sum(arrays[task,left,r] == arrays[task,right,r] for r in range(1,4))
        row['stable']=all(len({arrays[task,c,r] for r in range(1,4)})==1 for c in CONDITIONS)
        rows.append(row)
    g0={}
    for path in (root / ART / 'g0').glob('*/result.json'):
        r=load(path);key=(int(r['task'].split('/')[1]),r['variant'],r['rep'])
        assert key not in g0 and r['exit_code']==0 and r['valid']
        x=load(root / r['capture']);a=normalized(x)
        old=expected[r['task'],r['rep']]
        assert list(a[0]) == old['reference_ids' if r['variant'].startswith('R') else 'predicted_ids']
        g0[key]=x
    assert len(g0)==120
    sham_pairs=0
    for task in sorted(CASES | {58}):
        for rep in range(1,4):
            for plain,moved in [('T_plain','T0'),('N_plain','N0')]:
                x,y=g0[task,plain,rep],g0[task,moved,rep]
                assert x['trace']==y['trace']
                assert [(c['id'],c['accepted'],c['proposal'],c['scores']) for c in x['commits']] == [(c['id'],c['accepted'],c['proposal'],c['scores']) for c in y['commits']]
                sham_pairs+=1
    lines=(root / ART / 'RUN_LEDGER.jsonl').read_bytes().splitlines(keepends=True)
    events=[json.loads(line) for line in lines]
    seals=[i for i,e in enumerate(events) if e['event']=='T1_SEALED']
    assert len(seals)==1
    seal=load(root / ART / 'T1_SEAL.json');index=seals[0]
    assert events[index]['seal_sha256']==digest(root / ART / 'T1_SEAL.json')
    assert seal['ledger_sha256_before_seal']==hashlib.sha256(b''.join(lines[:index])).hexdigest()
    assert seal['freeze_sha256']==digest(root / DOC / 'FREEZE.json')
    assert seal['protocol_sha256']==digest(root / DOC / 'PROTOCOL.json')
    assert seal['manifest_sha256']==digest(root / DOC / 'ASSET_MANIFEST.json')
    starts=[e for e in events if e['event']=='ATTEMPT_START' and e.get('formal')]
    ends=[e for e in events if e['event']=='ATTEMPT_END' and e.get('formal')]
    assert len(starts)==len(ends)==360 and len({e['attempt_id'] for e in starts})==360
    assert all(e['valid'] and e['exit_code']==0 for e in ends)
    assert all(i>index for i,e in enumerate(events) if e['event']=='ATTEMPT_START' and e.get('variant')=='N1')
    assert all(i<index for i,e in enumerate(events) if e['event']=='ATTEMPT_END' and e.get('formal') and '/T1/' in e.get('unit_id',''))
    assert len(seal['predictions'])==72
    for unit,prediction in seal['predictions'].items():
        r=load(root / prediction['path'])
        assert r['unit_id']==unit and digest(root / prediction['path'])==prediction['sha256']
        assert record_endpoint(prediction)==record_endpoint(r)
    totals={key:sum(r[key] for r in rows) for key in ['T0_N0','T1_N1','N0_R','N1_R']}
    result={'status':'PASS','formal_arrays':360,'formal_attempts':360,'G0_arrays':120,'sham_pairs':sham_pairs,
            'tasks':24,'stable_tasks':sum(r['stable'] for r in rows),'comparisons':totals,
            'recovered_cases':[r['task'] for r in rows if r['diagnostic'] and r['N1_R']==3],
            'control_regressions':[r['task'] for r in rows if not r['diagnostic'] and r['N1_R']!=3],
            'local_seal_order_and_prefix_hash':'PASS','device_and_command_checks':'PASS',
            'historical_prediction_file_sha256':digest(predictions),'study_helpers_imported':False,
            'limits':['Previously exposed tasks','Local chronology is not trusted absolute time',
                      'Omitted runtime/model bytes not authenticated','No functional-pass or performance conclusion'],
            'task_rows':rows,'prefill_graph_rows':graph_rows}
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['task_rows','prefill_graph_rows']},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--predictions',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.root,a.predictions,a.output)
