"""Build reviewable summaries; raw telemetry stays in the local archive."""
import csv
import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'bundle'
RUNS = ['screen-fa-on-v2', 'ablation-fa-off-ub1', 'ablation-fa-off-ub512', 'ablation-fa-on-ub1',
        'expansion-fa-on-ub512', 'shortdraft-fa-on-ub512']

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(name, data):
    serialized = json.dumps(data, ensure_ascii=False, indent=2)
    if name == 'TOKEN_OUTCOMES.json':
        serialized = re.sub(r'"ids": \[\n\s*([0-9,\s]+?)\n\s*\]',
                            lambda m: '"ids": [' + ', '.join(m.group(1).replace(',', ' ').split()) + ']', serialized)
    (DEST / name).write_text(serialized + '\n', encoding='utf-8', newline='\n')

def table(name, rows):
    with (DEST / name).open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)

def main():
    DEST.mkdir(exist_ok=True)
    summaries, pairs, compact, receipts, manifests = [], [], [], [], []
    for run_name in RUNS:
        run = ROOT / 'runs' / run_name
        for script in ['analyze.py', 'validate.py']:
            subprocess.run([sys.executable, '-X', 'utf8', '-B', str(ROOT / script), str(run)], check=True, stdout=subprocess.DEVNULL)
        validation = json.loads((run / 'validation.json').read_text())
        analysis = json.loads((run / 'analysis.json').read_text())
        manifest = json.loads((run / 'manifest.json').read_text())
        manifests.append({'run': run_name, 'source_commit': manifest['source_commit'], 'source_sha256': manifest['source_sha256'],
            'input_file': manifest['args']['input_file'], 'inputs_sha256': manifest['inputs_sha256'],
            'runtime_sha256': manifest['runtime_sha256'], 'rounds': manifest['args']['rounds'],
            'conditions': manifest['args']['conditions'], 'flash_attn': manifest['args']['flash_attn'],
            'ubatch': manifest['args']['ubatch'], 'measured_requests': validation['measured_requests'],
            'started': manifest['started'], 'boundary': manifest['boundary']})
        receipts.append(validation)
        for row in analysis['summary']:
            scope = row['scope']
            quality = False if scope in ('Edit-rename', 'synthetic_edit') else True if scope == 'Edit-field' else None
            summaries.append({'run': run_name, **row, 'requested_edit_ast_match': quality,
                'qualified_speedup': row['median_wall_speedup'] if row['qualified'] and quality is not False else None,
                'advance': row['advance'] and quality is not False})
        with (run / 'paired.csv').open(encoding='utf-8') as f:
            pairs.extend({'run': run_name, **row} for row in csv.DictReader(f))
        by_key = {(q['round'], q['condition'], q['task']): q['requested_edit_ast_match'] for q in validation['quality_checks']}
        for r in json.loads((run / 'records.json').read_text()):
            response, timing = r['response'], r['response']['timings']
            raw_path = run / f"r{r['round']}_{r['condition']}_{r['task']}.json"
            compact.append({'run': run_name, 'round': r['round'], 'condition': r['condition'], 'task': r['task'],
                'group': r['group'], 'cap': r['cap'], 'ids': response['tokens'], 'stop_type': response['stop_type'],
                'stopping_word': response['stopping_word'], 'truncated': response['truncated'], 'wall_ms': r['wall_ms'],
                'prompt_ms': timing['prompt_ms'], 'gen_ms': timing['predicted_ms'], 'prompt_n': timing['prompt_n'],
                'cache_n': timing['cache_n'], 'draft_n': timing.get('draft_n', 0), 'draft_accepted': timing.get('draft_n_accepted', 0),
                'prompt_sha256': sha(response['prompt'].encode()),
                'requested_edit_ast_match': by_key.get((r['round'], r['condition'], r['task'])),
                'raw_record_sha256': sha(raw_path.read_bytes()), 'source_commit': r['source_commit']})
    assert len(compact) == 300 and all(r['cache_n'] == 0 for r in compact)
    table('SUMMARY.csv', summaries)
    table('PAIRED.csv', pairs)
    save('TOKEN_OUTCOMES.json', {'scope': 'Generated direct-ID outcome and timer summaries, not native logs/state or raw telemetry', 'records': compact})
    save('RUNS.json', manifests)
    save('VALIDATION.json', {'status': 'PASS', 'measured_requests': 300, 'warmup_requests': 48,
        'infrastructure_attempt_excluded': {'run': 'screen-fa-on-v1', 'warmup_requests': 1, 'completed_target_requests': 1,
            'reason': 'Incorrect interpretation of top-level tokens_cached, corrected to timings.cache_n before restart'},
        'checks': receipts, 'analysis_threshold_note': 'At least 10% latency reduction means speedup >=1/0.9; analyzer corrected from 1.1 to this declared threshold.'})
    baseline = {(r['task'], r['round']): r for r in compact if r['run'] == 'screen-fa-on-v2' and r['condition'] == 'target'}
    cross = []
    for r in compact:
        if r['condition'] != 'target' or r['run'] not in RUNS[1:4]:
            continue
        b = baseline[(r['task'], r['round'])]
        diff = next((i for i,(x,y) in enumerate(zip(b['ids'],r['ids'])) if x!=y), min(len(b['ids']),len(r['ids'])) if len(b['ids'])!=len(r['ids']) else None)
        cross.append({'run':r['run'],'task':r['task'],'round':r['round'],'same_reference_ids':r['ids']==b['ids'],
            'first_diff_zero_based':diff,'tokens':len(r['ids']),'FA_on_UB512_tokens':len(b['ids'])})
    expansion = {(r['task'],r['round']):r for r in compact if r['run']=='expansion-fa-on-ub512' and r['condition']=='target'}
    repeat = [{'task':r['task'],'round':r['round'],'same_reference_ids':r['ids']==expansion[(r['task'],r['round'])]['ids']}
        for r in compact if r['run']=='shortdraft-fa-on-ub512' and r['condition']=='target']
    assert len(repeat)==24 and all(x['same_reference_ids'] for x in repeat)
    save('CROSS_CONFIG_REFERENCES.json',{'scope':'Separate cross-configuration identity, not same-output speedup ratios',
        'relative_to_FA_on_UB512':cross,'expansion_vs_shortdraft_target':repeat})
    bindings=[]
    for name in ['run_pilot.py','analyze.py','validate.py','export_results.py','inputs.json','inputs_ablation.json',
                 'inputs_expansion.json','inputs_shortdraft.json','PROTOCOL.md','FOLLOWUP_PROTOCOL.md','SHORT_DRAFT_PROTOCOL.md']:
        (DEST/name).write_text((ROOT/name).read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
        bindings.append({'file':name,'sha256':sha((DEST/name).read_bytes())})
    frozen=DEST/'frozen';frozen.mkdir(exist_ok=True)
    frozen_entries=[]
    for item in manifests:
        git_sha=item['source_commit']
        for name in ['run_pilot.py',item['input_file']]:
            data=subprocess.check_output(['git','-C',str(ROOT),'show',git_sha+':'+name])
            target=frozen/(git_sha+'_'+name)
            target.write_bytes(data)
            frozen_entries.append({'local_source_commit':git_sha,'file':str(target.relative_to(DEST)).replace('\\','/'),
                'git_blob_LF_sha256':sha(data),'raw_execution_sha256':item['source_sha256'] if name=='run_pilot.py' else item['inputs_sha256']})
    save('SOURCE_BINDINGS.json',{'base_main':'e87291d26df32f2cb9571e005ab173b1c7a6830b','current_export_source_files':bindings,
        'frozen_execution_sources':frozen_entries,'local_freeze_commits_not_github_commits':True,
        'model_hashes_inherited_from_verified_local_inventory':{'Qwen3-8B-Q8_0.gguf':'408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6',
            'Qwen3-0.6B-Q8_0.gguf':'9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031'},
        'scope':'All local freeze commits are retained in the delivered Git bundle. Windows raw input SHA differs from Git LF blob SHA only by reconstructed CRLF, independently checked.'})
    print('Exported300 requests, six completed matrices, source-bound native-ID/endpoint checks and explicit quality exclusions')

if __name__ == '__main__':
    main()
