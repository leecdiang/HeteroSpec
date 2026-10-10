"""Authenticate v0.14.5 against #75 and reverse its bounded editorial changes.

This receipt preserves the older humanizer/scientific audit chain. It does not
claim that hashing proves semantic equivalence; the second reading is manual.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
TEX_FILES = {'main.tex', 'supplement.tex', 'sections/01_introduction.tex',
             'sections/08_conclusion.tex'}
DELIVERY_FILES = {'build.py', 'scripts/check_package.py', 'scripts/flat_sources.py',
                  'scripts/render_qa.py', 'scripts/humanizer_qa.py',
                  'scripts/revision_qa.py', 'README.md', 'VALIDATION_LOG.md'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def recover_v0144(text, name):
    receipt = json.loads((ROOT / 'provenance/CLOSEOUT_EDIT_RECEIPT.json').read_text())
    if name not in receipt['files']:
        return text
    record = receipt['files'][name]
    assert sha(text.encode()) == record['after_sha256'], (name, 'Unrecorded closeout change')
    for edit in reversed(record['edits']):
        assert text.count(edit['new']) == 1, (name, 'Non-unique reversal')
        text = text.replace(edit['new'], edit['old'])
    assert sha(text.encode()) == record['before_sha256'], (name, 'Baseline recovery failed')
    return text


def audit():
    baseline = json.loads((ROOT / 'provenance/V0144_CLOSEOUT_BASELINE.json').read_text())
    receipt = json.loads((ROOT / 'provenance/CLOSEOUT_EDIT_RECEIPT.json').read_text())
    assert baseline['baseline_commit'] == '92b08a0ffab2ca08c835b411d9d7478ccd57603b'
    assert len(baseline['files']) == 299
    assert set(receipt['files']) == TEX_FILES
    assert set(receipt['delivery_files']) == DELIVERY_FILES
    assert receipt['status'] == 'PASS' and receipt['second_reading']['completed']
    unchanged = []
    for name, record in baseline['files'].items():
        data = (ROOT / name).read_bytes()
        if name in TEX_FILES:
            before = recover_v0144(data.decode(), name).encode()
            assert sha(before) == record['sha256'], name
            # No equation, citation, result reference, input, table or figure changes.
            patterns = [r'(?<!\\)\$[^$]*\$',
                        r'\\(?:cite\w*|ref|label|input)\{[^}]*\}',
                        r'\\begin\{(?:table|figure)\*?\}.*?\\end\{(?:table|figure)\*?\}',
                        r'\\(?:documentclass|usepackage|setlength|renewcommand)\b[^\n]*']
            for pattern in patterns:
                assert re.findall(pattern, before.decode(), re.S) == re.findall(pattern, data.decode(), re.S), (name, pattern)
        elif name in DELIVERY_FILES:
            change = receipt['delivery_files'][name]
            assert change['before_sha256'] == record['sha256']
            assert sha(data) == change['after_sha256'], name
        else:
            assert sha(data) == record['sha256'], name
            unchanged.append(name)
    assert len(unchanged) == 287
    locked = json.loads((ROOT / 'provenance/LOCKED_REVISION_ASSETS.json').read_text())['assets']
    assert len(locked) == 22
    for name, expected in locked.items():
        assert sha((ROOT / name).read_bytes()) == expected == baseline['files'][name]['sha256'], name
    cost = (ROOT / 'sections/06_cost.tex').read_text()
    assert '1.170' in cost and '1.169' in cost
    for path in ['main.tex', 'supplement.tex']:
        text = (ROOT / path).read_text()
        assert 'Diagnosis, Repair Scope, and Measured Cost' in text
        assert 'Chengzhan Li' in text and 'University of Electronic Science and Technology of China' in text
    for value in ['1.742', '1.683', '1.035']:
        assert value in (ROOT / 'main.tex').read_text()
    result = dict(version='v0.14.5', status='PASS', baseline_pr=75,
                  baseline_commit=baseline['baseline_commit'], authenticated_baseline_files=299,
                  unchanged_files=len(unchanged), reversible_manuscript_files=4,
                  delivery_files=len(DELIVERY_FILES), unchanged_figure_and_table_assets=22,
                  equations_citations_references_inputs_figures_tables_layout_equal=True,
                  omitted_abstract_generation_ratios_retained_in_body=True,
                  historical_humanizer_receipt_unchanged=True,
                  second_reading=receipt['second_reading'],
                  deferred_scientific_gaps=receipt['deferred_scientific_gaps'],
                  author_metadata_from_published_v1=True, journal_declarations_pending=True, new_inference=0,
                  boundary='Editorial closeout, frozen-export checks and local compilation; no new scientific evidence or live arXiv acceptance.')
    (ROOT / 'output').mkdir(exist_ok=True)
    (ROOT / 'output/CLOSEOUT_QA.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
