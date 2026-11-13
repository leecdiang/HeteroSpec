"""Independently reconstruct the S0 census from archived native tokenizer bytes.

Standard library only. Does not import the census producer or launch processes.
"""
import argparse
import hashlib
import json
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def verify(root):
    for record in load(root/'RAW_MANIFEST.json'):
        data = (root/record['name']).read_bytes()
        if len(data) != record['bytes'] or digest(data) != record['sha256']:
            raise ValueError('raw identity mismatch: '+record['name'])
    plan = load(root/'PLAN.json')
    contract_path = root/'SOURCE/MODEL_CONTRACT.json'
    if not contract_path.is_file():
        contract_path = Path(plan['files']['model_contract']['path'])
    if digest(contract_path.read_bytes()) != plan['files']['model_contract']['sha256']:
        raise ValueError('historical model contract mismatch')
    contracts = load(contract_path)['families']
    tasks = load(root/'NATURAL_TASKS.json')
    if len({task['id'] for task in tasks}) != len(tasks):
        raise ValueError('duplicate natural task')
    expected = []
    for native_family, family in [('Qwen', 'Qwen3'), ('SmolLM2', 'SmolLM2'), ('Llama', 'Llama')]:
        query_list = load(root/(native_family+'-QUERIES.json'))['queries']
        query_map = {query['task_id']: query for query in query_list}
        if len(query_map) != len(tasks) or len(query_list) != len(tasks):
            raise ValueError('incomplete query inventory')
        records = {}
        vocabularies = []
        for role in ('target', 'draft'):
            slot = native_family+'-'+role
            lines = [json.loads(line) for line in (root/(slot+'.stdout.jsonl')).read_bytes().splitlines()]
            vocabulary = lines[0]
            if (vocabulary['vocab_only'], vocabulary['context_creations'], vocabulary['forward_calls']) != (True, 0, 0):
                raise ValueError('unexpected native initialization')
            vocabulary_hash = digest(json.dumps(vocabulary, ensure_ascii=False, separators=(',', ':')).encode())
            if vocabulary_hash != contracts[native_family]['vocabulary_sha256']:
                raise ValueError('historical vocabulary mismatch')
            vocabularies.append(vocabulary)
            records[role] = {row['task_id']: row for row in lines[1:]}
            if len(records[role]) != len(tasks) or len(lines)-1 != len(tasks):
                raise ValueError('missing/duplicate native task')
            receipt = load(root/(slot+'-EXIT.json'))
            if receipt['exit_code'] != 0 or receipt['timed_out'] or receipt['exit_verified'] is not True:
                raise ValueError('unclean tokenizer process')
            if receipt['stdout_sha256'] != digest((root/(slot+'.stdout.jsonl')).read_bytes()):
                raise ValueError('process receipt differs')
        if vocabularies[0] != vocabularies[1] or records['target'] != records['draft']:
            raise ValueError('target/draft tokenizer mismatch')
        for task in tasks:
            record = records['target'][task['id']]
            if record['forward_calls'] != 0 or record['vocab_only'] is not True:
                raise ValueError('unexpected model forward')
            expected.append({'family': family, 'id': task['id'], 'domain': task['domain'],
                             'tokens': len(record['prompt_ids']),
                             'raw_text_sha256': digest(task['raw_prompt'].encode()),
                             'normalized_description_sha256': digest(' '.join(task['description'].split()).encode()),
                             'formatted_prompt_sha256': digest(query_map[task['id']]['formatted_prompt'].encode()),
                             'token_ids_sha256': digest(json.dumps(record['prompt_ids'], separators=(',', ':')).encode()),
                             'target_draft_ids_equal': True})
    if expected != load(root/'LENGTHS.json'):
        raise ValueError('raw-to-normalized length/hash reconstruction differs')
    census = load(root/'CENSUS.json')
    families = {}
    for family in ('Llama', 'Qwen3', 'SmolLM2'):
        rows = [row for row in expected if row['family'] == family]
        strata = {name: {'minimum': low, 'maximum': high,
                        'unfiltered_count': sum(low <= row['tokens'] <= high for row in rows), 'required': 4}
                  for name, low, high in [('short', 64, 192), ('medium', 256, 448), ('long', 640, 832)]}
        families[family] = {'natural_inputs': len(rows), 'maximum_tokens': max(row['tokens'] for row in rows),
                            'strata': strata,
                            'missing_strata': [name for name, stats in strata.items() if stats['unfiltered_count'] < 4]}
    if families != census['families']:
        raise ValueError('census reconstruction differs')
    if not all(family['missing_strata'] == ['medium', 'long'] for family in families.values()):
        raise ValueError('expected stopping condition not reproduced')
    return {'status': 'PASS_RAW_TO_NORMALIZED_S0', 'families': families,
            'records_reconstructed': len(expected), 'vocabulary_only_processes': 6,
            'model_contexts': 0, 'model_requests': 0,
            'exposure_certification': False, 'held_out_selection': False,
            'scope': 'Same-host independent implementation; no model correctness or speed claim.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.root)
    with args.out.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(result['status'], result['records_reconstructed'])
