#!/usr/bin/env python3
"""Check the v0.2 narrative against the immutable v0.1 scientific baseline."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
EVID = HERE.parent / 'evidence'
baseline = json.loads((EVID / 'NARRATIVE_V02_BASELINE.json').read_text())
integration = json.loads((EVID / 'NARRATIVE_FIGURE_INTEGRATION_BASELINE.json').read_text())
checks = []
for path, expected in baseline['protected_sha256'].items():
    if path.startswith('paper/mlsys2027/figures/'):
        continue  # Author-requested PR #17 supersedes the earlier figure candidates.
    actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    assert actual == expected, ('frozen content changed', path)
    checks.append(path)
for path, expected in integration['protected_sha256'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected, path
    checks.append(path)

base = baseline['main_head']
def original(path):
    return subprocess.check_output(['git', 'show', f'{base}:{path}'], cwd=ROOT, text=True)

# Catch edits outside narrative, packaging and QA, including untracked experiment files.
tracked = subprocess.check_output(['git', 'diff', '--name-only', integration['main_head']], cwd=ROOT, text=True).splitlines()
untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
allowed = ('paper/mlsys2027/manuscript/', 'paper/mlsys2027/evidence/NARRATIVE_',
           'paper/mlsys2027/evidence/PDF_QA.json', 'paper/mlsys2027/MANUSCRIPT_STATUS.md',
           'paper/mlsys2027/MANUSCRIPT_V01_STATUS.md', 'paper/mlsys2027/WRITING_STATUS.md',
           'paper/mlsys2027/FORMAT_REQUIREMENTS.md', 'paper/mlsys2027/NARRATIVE_')
assert all(p.startswith(allowed) for p in tracked + untracked), (tracked, untracked)

# Keep table values and every generated figure coordinate byte-identical.
asset_paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', base,
    'paper/mlsys2027/manuscript/tables', 'paper/mlsys2027/manuscript/figures'], cwd=ROOT, text=True).splitlines()
for path in asset_paths:
    if '/tables/' in path or path.endswith('.dat') or path.endswith('03_coordinates.tex'):
        assert (ROOT/path).read_text() == original(path), path
        checks.append(path)

old_paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', base,
    'paper/mlsys2027/manuscript/sections'], cwd=ROOT, text=True).splitlines()
old_text = original('paper/mlsys2027/manuscript/main.tex') + ''.join(original(p) for p in old_paths)
new_text = (HERE/'main.tex').read_text() + ''.join(p.read_text() for p in (HERE/'sections').glob('*.tex'))
macros = json.loads((EVID/'published_values.json').read_text())['macros']
old_used = {m for m in macros if re.search(r'\\'+m+r'\b', old_text)}
new_used = {m for m in macros if re.search(r'\\'+m+r'\b', new_text)}
assert old_used <= new_used, ('quantitative coverage lost', sorted(old_used-new_used))
numerical = json.loads((EVID/'NUMERICAL_QA.json').read_text())
assert numerical['status'] == 'PASS' and len(numerical['checks']) == 228
assert all(c['pass'] for c in numerical['checks'])

report = {'status': 'PASS', 'main_baseline': base, 'integration_main': integration['main_head'],
    'unchanged_protected_files': checks,
    'existing_numerical_checks': 228,
    'all_existing_quantitative_macros_retained': sorted(old_used),
    'frozen_claim_ledger_unchanged': True,
    'selected_figure_tree_unchanged_since_integration_main': True,
    'experiment_data_and_source_unchanged': True,
    'scope_note': 'Narrative and causal interpretations require manual review; see NARRATIVE_REFACTOR_V02.md.'}
(EVID/'NARRATIVE_V02_QA.json').write_text(json.dumps(report, indent=2)+'\n')
print(f'Narrative PASS: {len(checks)} protected files, all {len(old_used)} prior prose numeric macros, 228 unchanged numerical checks.')
