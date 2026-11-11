"""Validate completion, source binding, direct-ID endpoints and benchmark comparability."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
EOG = {128247, 151643, 151645, 151662, 151663, 151664}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def validate(run):
    manifest = json.loads((run / 'manifest.json').read_text())
    args = manifest['args']
    inputs_bytes = subprocess.check_output(['git', '-C', str(ROOT), 'show', manifest['source_commit'] + ':' + manifest.get('input_repo_path', args['input_file'])])
    runner_bytes = subprocess.check_output(['git', '-C', str(ROOT), 'show', manifest['source_commit'] + ':' + manifest.get('runner_repo_path', 'run_pilot.py')])
    def bind_git_bytes(data, raw_digest):
        if digest(data) == raw_digest:
            return 'exact Git blob bytes'
        assert digest(data.replace(b'\n', b'\r\n')) == raw_digest, 'content mismatch beyond Git CRLF normalization'
        return 'Git LF blob reconstructed as Windows CRLF; raw digest preserved'
    input_binding = bind_git_bytes(inputs_bytes, manifest['inputs_sha256'])
    source_binding = bind_git_bytes(runner_bytes, manifest['source_sha256'])
    inputs = json.loads(inputs_bytes)
    expected = {(rnd, cond, task['id']) for rnd in range(args['rounds']) for cond in args['conditions'] for task in inputs}
    records = json.loads((run / 'records.json').read_text())
    actual = {(r['round'], r['condition'], r['task']) for r in records}
    assert expected == actual and len(actual) == len(records), 'incomplete or duplicate run matrix'
    prompt_bindings = {}
    quality = []
    for r in records:
        assert r['source_commit'] == manifest['source_commit']
        response = r['response']
        ids, t = response['tokens'], response['timings']
        assert ids and all(isinstance(x, int) and x >= 0 for x in ids)
        assert len(ids) == response['tokens_predicted'] == t['predicted_n'], 'native ID count mismatch'
        assert len(ids) <= r['cap'], 'raw speculative overshoot'
        assert t['cache_n'] == 0 and response['truncated'] is False, 'cache reuse or context truncation'
        if response['stop_type'] == 'eos':
            assert ids[-1] in EOG and not any(x in EOG for x in ids[:-1]), 'EOS boundary mismatch'
        elif response['stop_type'] == 'limit':
            assert len(ids) == r['cap'] and not any(x in EOG for x in ids), 'limit boundary mismatch'
        else:
            raise AssertionError('unexpected stop type')
        assert r['wall_ms'] >= t['prompt_ms'] + t['predicted_ms'] - 2, 'timer boundary inconsistency'
        prompt_identity = (response['prompt'], t['prompt_n'])
        if r['task'] in prompt_bindings:
            assert prompt_bindings[r['task']] == prompt_identity, 'different prompt across condition/round'
        prompt_bindings[r['task']] = prompt_identity
        if r['task'].startswith('Edit'):
            task = next(x for x in inputs if x['id'] == r['task'])
            source = task['prompt'].split('\n\n', 1)[1]
            expected_source = source.replace('values', 'numbers') if r['task'] == 'Edit-rename' else source.replace('"score"', '"rating"')
            try:
                ok = ast.dump(ast.parse(expected_source)) == ast.dump(ast.parse(response['content']))
            except SyntaxError:
                ok = False
            quality.append({'task': r['task'], 'condition': r['condition'], 'round': r['round'], 'requested_edit_ast_match': ok})
    result = {'run': run.name, 'status': 'PASS', 'measured_requests': len(records),
              'source_commit': manifest['source_commit'], 'source_sha256': manifest['source_sha256'],
              'inputs_sha256': manifest['inputs_sha256'], 'full_prompt_equal_across_conditions': True,
              'input_git_binding': input_binding, 'runner_git_binding': source_binding,
              'prompt_reuse_tokens': 0, 'native_id_counts_and_stopping_boundaries': 'PASS',
              'quality_checks': quality,
              'raw_record_bindings': [{'file': p.name, 'bytes': p.stat().st_size, 'sha256': digest(p.read_bytes())}
                  for p in sorted(run.glob('r[0-9]_*_*.json')) if not p.name.endswith(('_command.json', '_warmup.json'))]}
    (run / 'validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'raw_record_bindings'}, indent=2))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('run', type=Path)
    validate(ap.parse_args().run)
