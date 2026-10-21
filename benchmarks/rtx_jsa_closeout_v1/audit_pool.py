"""Read-only S0 length census using the inherited vocabulary-only helper.

This does not choose held-out tasks, create contexts or execute model forwards.
The unfiltered counts are upper bounds on any exposure-excluded pool.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
from datetime import datetime, timezone

from jinja2.sandbox import SandboxedEnvironment


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def read(path):
    return json.loads(Path(path).read_bytes())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def render(contract, raw, tokens):
    env = SandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
    def fail(message):
        raise ValueError(message)
    env.globals['raise_exception'] = fail
    return env.from_string(contract['template']).render(
        messages=[{'role': 'user', 'content': raw}],
        add_generation_prompt=True, enable_thinking=False,
        bos_token=tokens[contract['bos']], eos_token=tokens[contract['eos']])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    plan = read(args.plan)
    assert plan['status'] == 'CPU_VOCABULARY_CENSUS_ONLY'
    assert plan['model_contexts'] == plan['model_requests'] == 0
    args.out.mkdir(parents=True, exist_ok=False)
    save(args.out/'PLAN.json', plan)
    start = time.perf_counter()
    pins = {}
    for name, entry in plan['files'].items():
        actual = sha(entry['path'])
        assert actual == entry['sha256'], (name, actual)
        pins[name] = {'path': entry['path'], 'sha256': actual,
                      'bytes': Path(entry['path']).stat().st_size}
    save(args.out/'VERIFIED_IDENTITIES.json', pins)
    contract = read(plan['files']['model_contract']['path'])['families']
    spec = importlib.util.spec_from_file_location('inherited_gguf', plan['files']['metadata_reader']['path'])
    gguf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gguf)
    tasks = []
    for task in read(plan['files']['mbpp']['path']):
        tasks.append({'id': 'MBPP/'+str(task['task_id']), 'domain': 'MBPP',
                      'description': task['prompt'],
                      'raw_prompt': plan['formatting']['MBPP']+task['prompt']})
    for i, line in enumerate(Path(plan['files']['gsm8k']['path']).read_text(encoding='utf-8').splitlines()):
        task = json.loads(line)
        tasks.append({'id': 'GSM8K/test/'+str(i), 'domain': 'GSM8K',
                      'description': task['question'],
                      'raw_prompt': plan['formatting']['GSM8K']+task['question']})
    assert len({task['id'] for task in tasks}) == len(tasks)
    save(args.out/'NATURAL_TASKS.json', tasks)
    rows, receipts = [], []
    for family, family_contract in contract.items():
        assert digest(family_contract['template'].encode()) == family_contract['template_sha256']
        metadata, _ = gguf.Reader(family_contract['models']['target']['path']).metadata()
        assert metadata['tokenizer.chat_template'] == family_contract['template']
        queries = [{'task_id': task['id'],
                    'formatted_prompt': render(family_contract, task['raw_prompt'], metadata['tokenizer.ggml.tokens']),
                    'add_special': family_contract['added_special_for_template']} for task in tasks]
        save(args.out/(family+'-QUERIES.json'),
             {'vocab_only': True, 'forward_calls': 0, 'queries': queries})
        payload = ''.join(json.dumps(query, ensure_ascii=False)+'\n' for query in queries).encode()
        native = {}
        for role in ('target', 'draft'):
            assert time.perf_counter()-start < plan['owned_seconds']-plan['cleanup_seconds']
            command = [plan['files']['helper']['path'], plan['dll_directory'],
                       family_contract['models'][role]['path']]
            slot = family+'-'+role
            save(args.out/(slot+'-START.json'), {'command': command,
                 'utc': datetime.now(timezone.utc).isoformat(),
                 'timeout_seconds': plan['per_process_timeout_seconds'],
                 'model_contexts': 0, 'model_requests': 0})
            tick = time.perf_counter()
            child_env = {key: value for key, value in os.environ.items()
                         if not key.startswith(('HS_', 'GGML_', 'CUDA_', 'LLAMA_ARG_'))}
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, env=child_env,
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            timed_out = False
            try:
                stdout, stderr = process.communicate(payload, timeout=plan['per_process_timeout_seconds'])
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                stdout, stderr = process.communicate(timeout=plan['cleanup_seconds'])
            (args.out/(slot+'.stdout.jsonl')).write_bytes(stdout)
            (args.out/(slot+'.stderr.log')).write_bytes(stderr)
            receipt = {'slot': slot, 'pid': process.pid, 'exit_code': process.returncode,
                       'timed_out': timed_out, 'exit_verified': process.poll() is not None,
                       'seconds': time.perf_counter()-tick,
                       'stdout_sha256': digest(stdout), 'stderr_sha256': digest(stderr)}
            save(args.out/(slot+'-EXIT.json'), receipt)
            receipts.append(receipt)
            assert process.returncode == 0 and not timed_out
            records = [json.loads(line) for line in stdout.splitlines()]
            vocabulary = records[0]
            assert vocabulary['vocab_only'] and vocabulary['forward_calls'] == vocabulary['context_creations'] == 0
            vocabulary_hash = digest(json.dumps(vocabulary, ensure_ascii=False, separators=(',', ':')).encode())
            assert vocabulary_hash == family_contract['vocabulary_sha256']
            native[role] = {record['task_id']: record for record in records[1:]}
            assert len(native[role]) == len(tasks) == len(records)-1
        for task, query in zip(tasks, queries):
            target, draft = (native[role][task['id']] for role in ('target', 'draft'))
            assert target == draft
            assert target['vocab_only'] and target['forward_calls'] == 0
            ids = target['prompt_ids']
            rows.append({'family': 'Qwen3' if family == 'Qwen' else family,
                         'id': task['id'], 'domain': task['domain'], 'tokens': len(ids),
                         'raw_text_sha256': digest(task['raw_prompt'].encode()),
                         'normalized_description_sha256': digest(' '.join(task['description'].split()).encode()),
                         'formatted_prompt_sha256': digest(query['formatted_prompt'].encode()),
                         'token_ids_sha256': digest(json.dumps(ids, separators=(',', ':')).encode()),
                         'target_draft_ids_equal': True})
        print(family, 'inventory complete', flush=True)
    save(args.out/'LENGTHS.json', rows)
    summary = {}
    for family in sorted({row['family'] for row in rows}):
        group = [row for row in rows if row['family'] == family]
        strata = {name: {'minimum': low, 'maximum': high,
                        'unfiltered_count': sum(low <= row['tokens'] <= high for row in group),
                        'required': 4}
                  for name, low, high in plan['strata']}
        summary[family] = {'natural_inputs': len(group), 'maximum_tokens': max(row['tokens'] for row in group),
                           'strata': strata,
                           'missing_strata': [name for name, stat in strata.items() if stat['unfiltered_count'] < 4]}
    result = {'status': 'MISSING_COVERAGE_BEFORE_EXPOSURE_AUDIT'
                       if any(group['missing_strata'] for group in summary.values()) else 'EXPOSURE_AUDIT_REQUIRED',
              'families': summary, 'model_contexts': 0, 'model_requests': 0,
              'vocabulary_only_processes': len(receipts), 'process_receipts': receipts,
              'owned_seconds': time.perf_counter()-start,
              'selection_performed': False, 'exposure_audit_complete': False,
              'claim': 'Unfiltered counts upper-bound eligible counts. No held-out admission or speed estimate.'}
    save(args.out/'CENSUS.json', result)
    save(args.out/'RAW_MANIFEST.json', [{'name': path.name, 'bytes': path.stat().st_size, 'sha256': sha(path)}
                                       for path in sorted(args.out.iterdir()) if path.is_file()])
    print(json.dumps(result['families'], indent=2), flush=True)


if __name__ == '__main__':
    main()
