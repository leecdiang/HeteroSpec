"""Recover exact RTX Llama inputs/identities and retain distinct B570 Q6/Qwen history."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from common import BASE, HISTORY, RTX, DEVELOPMENT, digest, git_bytes, need, write


def recover(repo, out):
    out = Path(out);need(not out.exists(), 'fresh history directory');out.mkdir(parents=True)
    prefix = 'benchmarks/rtx_scope_transfer_v1/sidecar_execution/diagnostic/'
    paths = {'panel': prefix + 'PANEL.json', 'identity': prefix + 'EXECUTION_IDENTITY.json',
             'audit': prefix + 'AUDIT.json', 'references': prefix + 'REFERENCES.json'}
    objects = {}
    pins = []
    import hashlib
    for key, path in paths.items():
        data = git_bytes(repo, HISTORY, path)
        (out / (key + '.json')).write_bytes(data)
        objects[key] = json.loads(data)
        pins.append({'commit': HISTORY, 'path': path, 'sha256': hashlib.sha256(data).hexdigest()})
    panel = objects['panel']['inputs']
    by_id = {x['id']: x for x in panel}
    need(set(DEVELOPMENT) <= set(by_id), 'retained Llama inputs missing')
    selected = []
    for identifier in DEVELOPMENT:
        x = dict(by_id[identifier])
        # Preserve the historical checksum separately; new tools state their encoding explicitly.
        x['historical_prompt_hash'] = x.get('prompt_ids_sha256')
        x['prompt_ids_sha256'] = digest(x['prompt_ids'])
        need(x['cap'] == 128, 'historical cap changed')
        selected.append(x)
    write(out / 'DEVELOPMENT.json', selected)
    write(out / 'MODEL_IDENTITY.json', objects['identity']['families']['Llama'])
    for key, path in {
        'B570_Q6_HISTORY': 'benchmarks/b570_final_causal_closeout_v1/RESULTS.md',
        'B570_Q8_BRIDGE': 'benchmarks/b570_native_reproduction_v1/patches/03-request-bridge.patch',
        'B570_QWEN_HISTORY': 'benchmarks/b570_producer_consumer_boundary_v1/RESULT.md'}.items():
        data = git_bytes(repo, BASE, path);(out / (key + '.txt')).write_bytes(data)
        pins.append({'commit': BASE, 'path': path, 'sha256': hashlib.sha256(data).hexdigest()})
    write(out / 'HISTORY.json', {'status': 'COMMITTED_EVIDENCE_RECOVERED', 'pins': pins,
          'bulk_vectors_reopened_here': False, 'RTX_original_reference_reused_as_Vulkan_oracle': False,
          'cause': 'UNLOCATED_ON_LLAMA', 'next': 'Authenticate raw PR151 records/vectors with the PR160 history tool; build local Vulkan oracle separately.'})
    return out


def decision_rows(r):
    result = {0: 'target/initial.f32'}
    if not r['draft_enabled']:
        result.update({i: f'target/ordinary-{i}.f32' for i in range(1, len(r['ids']))})
        return result
    previous = 1
    for cycle in r['cycles']:
        end = cycle['output_length']
        need(previous < end <= len(r['ids']) and cycle['seed'] == r['ids'][previous-1], 'historical cycle ownership')
        for j in range(end-previous):
            need(cycle['decisions'][j] == r['ids'][previous+j], 'historical committed row')
            result[previous+j] = f'target/verify-{cycle["cycle"]}-{j}.f32'
        previous = end
    need(previous == len(r['ids']), 'incomplete historical output mapping')
    return result


def raw_audit(repo, raw_root, out):
    import hashlib
    from common import confined, sha, read, endpoint
    from audit import full_vector
    prefix = 'benchmarks/rtx_scope_transfer_v1/sidecar_execution/diagnostic/'
    data = git_bytes(repo, HISTORY, prefix+'REQUESTS.jsonl')
    need(hashlib.sha256(data).hexdigest() == '2e52aee27acb551f3f3556a566ec5f83b123aa0d50a9c01da3666ac33a2fa4b9', 'historical request manifest changed')
    rows = [json.loads(l) for l in data.decode().splitlines() if l]
    need(len(rows) == 54, 'complete diagnostic history')
    count = 0;index = {};findings = []
    for row in rows:
        pin = row['raw_native_record'];p = confined(raw_root,pin['path'])
        need(p.stat().st_size == pin['bytes'] and sha(p) == pin['sha256'], 'historical raw record drift')
        r = read(p);endpoint(r);mapping = decision_rows(r)
        for v in row['raw_vectors']:
            f = confined(raw_root,v['path']);need(sha(f) == v['sha256'], 'historical full vector drift')
            full_vector(f);count += 1
        key = (row['stage'],row['source_index'],row['producer'],row['arm'],row['observer'])
        need(key not in index, 'duplicate history coordinate');index[key]=(r,p,mapping)
    need(count == 5916, 'historical vector inventory incomplete')
    for i in (8,6,3):
        r,rp,rm = index['diagnostic_A1',i,'NATIVE','R','heavy']
        for arm in ('C_PQ','C_QB'):
            c,cp,cm = index['diagnostic_A1',i,'NATIVE',arm,'heavy']
            fd=next((j for j,(a,b) in enumerate(zip(r['ids'],c['ids'])) if a!=b),None)
            if fd is None and len(r['ids'])!=len(c['ids']):fd=min(len(r['ids']),len(c['ids']))
            limit=min(len(r['ids']),len(c['ids']),fd+1 if fd is not None else 128)
            first=next((j for j in range(limit) if sha(rp.with_suffix('')/rm[j])!=sha(cp.with_suffix('')/cm[j])),None)
            findings.append({'input_id':r['input_id'],'arm':arm,'first_output_difference':fd,'earliest_saved_decision_vector_difference':first,
                'candidate_decision_file':cm.get(fd),'same_token_prefix_does_not_prove_same_state':True})
    report={'status':'HISTORICAL_RAW_RECONSTRUCTED','requests':54,'full_vectors':count,'findings':findings,
            'new_model_requests':0,'scope':'RTX history audit; NOT a Vulkan reference or root-cause assertion'}
    write(out,report);return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__);p.add_argument('--repo', required=True);p.add_argument('--out', required=True)
    p.add_argument('--raw-root')
    a = p.parse_args();print(raw_audit(a.repo,a.raw_root,a.out) if a.raw_root else recover(a.repo, a.out))
