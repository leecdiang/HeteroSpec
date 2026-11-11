"""Verify the recorded prose pass and recover its exact pre-edit sources.

These checks protect scientific atoms and make every edit reversible. Semantic
equivalence also needs the documented manual reading; hashes cannot prove it.
"""
from pathlib import Path
import hashlib
import json
import re
from closeout_qa import recover_v0144

ROOT = Path(__file__).resolve().parents[1]


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def protected_atoms(text):
    return dict(
        numbers=re.findall(r'\d+(?:[.,]\d+)*', text),
        maths=re.findall(r'(?<!\\)\$[^$]*\$|\\\[.*?\\\]|'
                         r'\\begin\{equation\*?\}.*?\\end\{equation\*?\}', text, re.S),
        bound_commands=re.findall(r'\\(?:cite\w*|ref|label|input|nolinkurl|texttt)\{[^}]*\}|'
                                  r'\\includegraphics\[[^]]*\]\{[^}]*\}', text),
        tables=re.findall(r'\\begin\{table\*?\}.*?\\end\{table\*?\}', text, re.S),
        figures=re.findall(r'\\begin\{figure\*?\}.*?\\end\{figure\*?\}', text, re.S),
        layout_commands=re.findall(r'\\(?:documentclass|usepackage|setlength|renewcommand)\b[^\n]*', text))


def recover_before(text, name, receipt):
    if name not in receipt['files']:
        return text
    record = receipt['files'][name]
    assert sha(text) == record['after_sha256'], (name, 'Unrecorded current-source change')
    before = text
    for edit in reversed(record['edits']):
        assert before.count(edit['new']) == 1, (name, 'Rewrite is not uniquely reversible')
        before = before.replace(edit['new'], edit['old'])
    assert sha(before) == record['before_sha256'], (name, 'Pre-edit hash differs')
    assert protected_atoms(before) == protected_atoms(text), (name, 'Protected atoms differ')
    return before


def audit():
    receipt = json.loads((ROOT / 'provenance/HUMANIZER_EDIT_RECEIPT.json').read_text())
    expected = {'main.tex', 'supplement.tex', 'declarations.tex', 'Highlights.txt'}
    expected.update(str(p.relative_to(ROOT)) for p in (ROOT / 'sections').glob('*.tex'))
    expected.update(str(p.relative_to(ROOT)) for p in (ROOT / 'supplement').glob('*.tex'))
    assert receipt['status'] == 'PASS'
    assert set(receipt['files']) == expected and len(expected) == 19
    assert receipt['source']['commit'] == '225a6f39ac85f76ee48dbad772ea4abe4ed6c9d8'
    assert receipt['second_reading']['completed'] is True
    totals = {key: 0 for key in protected_atoms('')}
    files = {}
    for name in sorted(expected):
        text = recover_v0144((ROOT / name).read_text(), name)
        before = recover_before(text, name, receipt)
        counts = {key: len(values) for key, values in protected_atoms(text).items()}
        for key, count in counts.items():
            totals[key] += count
        files[name] = dict(changed=before != text, edits=len(receipt['files'][name]['edits']),
                           current_sha256=sha(text), pre_edit_source_exactly_recoverable=True,
                           protected_atoms_equal=True, protected_atom_counts=counts)
    changed = sum(item['changed'] for item in files.values())
    edits = sum(item['edits'] for item in files.values())
    assert (len(files), changed, edits) == (receipt['reviewed_files'], receipt['changed_files'],
                                          receipt['edited_paragraph_blocks'])
    result = dict(version='v0.14.4', inherited_through_v0145_exact_recovery=True, status='PASS', source=receipt['source'],
                  reviewed_files=len(files), changed_files=changed, edited_paragraph_blocks=edits,
                  all_pre_edit_sources_exactly_recoverable=True, protected_atoms_equal=True,
                  protected_atom_counts=totals, files=files, second_reading_completed=True,
                  new_model_requests=0,
                  boundary='Exact recoverability and atom equality are automated checks. '
                           'Scientific equivalence and readable prose were manually reviewed; '
                           'these checks are not an automated semantic proof or an AI-detection test.')
    (ROOT / 'output').mkdir(exist_ok=True)
    (ROOT / 'output/HUMANIZER_QA.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
