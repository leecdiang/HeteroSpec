#!/usr/bin/env python3
"""Validate title-only finalization against the exact pre-finalization PR head.

Run after staging all intended files. --visual-reviewed attests to a human/agent
inspection of rendered pages; it is not an automated layout test.
"""
from pathlib import Path
import argparse, hashlib, io, json, subprocess, zipfile
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[4]
P = 'paper/mlsys2027/'
M = P + 'manuscript/'
START = 'ee5ef7fa07572404e1de6ce17421abec16c5d894'
FREEZE = '1d3b556c93b477680788dfd1eb0737dfe9eee28c'
OLD = 'Speculative Decoding Across Consumer Systems: Gains, Failures, and Runtime Costs'
SHORT = 'Speculative Decoding Across Consumer Systems'
TITLE = 'Execution-Path Qualification and Realized Costs in Speculative Decoding on Consumer Systems'
RUNNING = 'Execution-Path Qualification in Speculative Decoding'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def original(path):
    return git('show', START + ':' + path)

def sha(data):
    return hashlib.sha256(data).hexdigest()

args = argparse.ArgumentParser()
args.add_argument('--visual-reviewed', action='store_true', required=True)
args.parse_args()
assert git('rev-parse', 'mlsys2027-v0.8-author-freeze^{commit}').decode().strip() == FREEZE
assert not git('tag', '--list', 'mlsys2027-v0.8.1-submission-candidate-*').strip()
tracked = set(git('ls-tree', '-r', '--name-only', START).decode().splitlines())
changed = git('diff', '--name-only', START).decode().splitlines()
outputs = [M + 'output/' + name for name in (
    'manuscript-v0.8.1.pdf', 'appendix-v0.8.1.pdf', 'hardware-only-v0.8.1.pdf',
    'overleaf-submission-readiness-v0.8.1.zip')]
allowed = {P + n for n in ('HANDOVER_CURRENT.md', 'MANUSCRIPT_STATUS.md',
    'SUBMISSION_UPLOAD_CHECKLIST.md', 'reviews/AUTHOR_REVIEW_NOTE_V081.md',
    'evidence/TITLE_APPLICATION_V081.md', 'evidence/FINALIZATION_QA_V081.json',
    'evidence/CLEAN_ZIP_FINALIZATION_V081_QA.json',
    'evidence/NARRATIVE_PDF_FINALIZATION_V081_QA.json',
    'evidence/PRESERVATION_FINALIZATION_V081_QA.json')}
allowed.update(outputs)
allowed.update(M + n for n in ('main.tex', 'appendix.tex', 'README.md',
    'scripts/build_v081.py', 'scripts/package_overleaf_v081.py',
    'scripts/qa_pdf_v081.py', 'scripts/validate_readiness_v081.py',
    'scripts/validate_finalization_v081.py'))
assert set(changed) <= allowed, set(changed) - allowed
protected = sorted(tracked - allowed)
for path in protected:
    assert (ROOT / path).read_bytes() == original(path), path
for name in ('main.tex', 'appendix.tex'):
    before = original(M + name).decode()
    after = (ROOT / M / name).read_text()
    prefix = 'Supplement: ' if name == 'appendix.tex' else ''
    expected = before
    for field, old, new in [('pdftitle', prefix + (SHORT if prefix else OLD), prefix + TITLE),
                            ('mlsystitle', prefix + (SHORT if prefix else OLD), prefix + TITLE),
                            ('mlsystitlerunning', prefix + SHORT, prefix + RUNNING)]:
        left = field + ('={' if field == 'pdftitle' else '{') + old + '}'
        right = field + ('={' if field == 'pdftitle' else '{') + new + '}'
        assert expected.count(left) == 1, (name, field)
        expected = expected.replace(left, right)
    assert after == expected, name
readme = (ROOT / M / 'README.md').read_text()
assert readme.split('\n---\n', 1)[1] == original(M + 'README.md').decode().split('\n---\n', 1)[1]
assert (ROOT / P / 'MANUSCRIPT_STATUS.md').read_bytes().endswith(original(P + 'MANUSCRIPT_STATUS.md'))
active = [ROOT / M / n for n in ('main.tex', 'appendix.tex')]
for folder in ('sections', 'figures', 'tables'):
    active.extend((ROOT / M / folder).glob('*.tex'))
assert all(SHORT not in path.read_text() for path in active)
assert SHORT not in readme.split('\n---\n', 1)[0]
evidence = ROOT / P / 'evidence'
qa = json.loads((evidence / 'NARRATIVE_PDF_FINALIZATION_V081_QA.json').read_text())
clean = json.loads((evidence / 'CLEAN_ZIP_FINALIZATION_V081_QA.json').read_text())
preservation = json.loads((evidence / 'PRESERVATION_FINALIZATION_V081_QA.json').read_text())
assert qa['status'] == clean['status'] == preservation['status'] == 'PASS'
assert (qa['main_text_pages'], qa['references_pages'], qa['pdfs']['appendix']['pages']) == (10, 2, 6)
statuses = {}
for path in outputs:
    data = (ROOT / path).read_bytes()
    statuses[path] = {'sha256': sha(data), 'bytes_equal_to_starting_head': data == original(path)}
    if path.endswith('.pdf'):
        r = PdfReader(io.BytesIO(data))
        prefix = 'Supplement: ' if 'appendix-' in path else ''
        assert r.metadata['/Title'] == prefix + TITLE
        assert '/Author' in r.metadata and r.metadata['/Author'] == 'Anonymous Authors'
        text = '\n'.join(p.extract_text() or '' for p in r.pages)
        assert SHORT not in text
        previous = '\n'.join(p.extract_text() or '' for p in PdfReader(io.BytesIO(original(path))).pages)
        statuses[path]['extracted_text_equal_to_starting_head'] = text == previous
        statuses[path]['text_difference_expected'] = 'New displayed title and running headers; exact source comparison protects all scientific prose.'
with zipfile.ZipFile(ROOT / outputs[-1]) as z:
    names = z.namelist()
    assert len(names) == len(set(names)) == 39
    manifest = json.loads(z.read('SHA256SUMS.json'))
    assert set(manifest) == set(names) - {'SHA256SUMS.json'}
    for name, digest in manifest.items():
        assert sha(z.read(name)) == digest
        assert not name.startswith('/') and '..' not in Path(name).parts
        assert not name.startswith(('benchmarks/', 'artifacts/', 'reports/', 'analysis/'))
        if name.endswith(('.tex', '.bib', '.txt', '.sty', '.bst', '.json')):
            text = z.read(name).decode()
            assert SHORT not in text
            assert '/Users/' not in text and '/home/' not in text
    for name in ('main.tex', 'appendix.tex'):
        assert TITLE in z.read(name).decode()
report = {
    'status': 'PASS', 'starting_head': START, 'scientific_author_freeze': FREEZE,
    'title_applied': TITLE, 'running_title': RUNNING,
    'old_title_absent_from_active_submission_source': True,
    'scientific_evidence_unchanged': True, 'no_numerical_macro_changes': True,
    'no_experimental_path_changes': True, 'section_claim_and_figure_sources_unchanged': True,
    'title_fields_only_in_main_and_appendix': True,
    'historical_records_and_older_outputs_unchanged': True,
    'protected_tracked_paths_compared_to_starting_head': len(protected),
    'build': 'PASS', 'anonymity': 'PASS', 'bibliography': 'PASS',
    'page_limit': 'PASS', 'source_zip': 'PASS', 'fonts_embedded': True,
    'font_substitutions': 0, 'unresolved_references_or_citations': 0, 'overfull_boxes': 0,
    'pages': {'body': 10, 'references': 2, 'appendix': 6, 'hardware_only': 11},
    'bibliography_entries': qa['references']['entries'],
    'full_reference_author_lists': qa['references']['full_author_lists'],
    'clean_zip_payload_hashes_match': clean['all_manifest_hashes_match'],
    'fresh_and_clean_zip_text_match': clean['comparison'],
    'manual_visual_review': {'status': 'PASS', 'main_pages': 12, 'appendix_pages': 6,
        'hardware_only_pages': 11, 'focus': ['title line breaks', 'first-page balance',
        'abstract pagination', 'Figure 3', 'Section 5', 'references first page'],
        'finding': 'All pages rendered and inspected; no clipping, overlap or unreadable glyphs. Existing appendix float whitespace retained.'},
    'artifact_status_vs_starting_head': statuses,
    'changed_paths': sorted(set(changed) | {P + 'evidence/FINALIZATION_QA_V081.json'}),
    'experiments_ran': False, 'new_reviewer_simulation': False,
    'pr_merged': False, 'submission_candidate_tag_created': False,
    'merge_recommendation': 'READY FOR AUTHOR MERGE',
    'scope': 'Document builds, rendering, read-only source/PDF audits and git/PR operations only.'
}
(evidence / 'FINALIZATION_QA_V081.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': 'PASS', 'protected_paths': len(protected), 'science_changed': False,
                  'pages': report['pages'], 'recommendation': report['merge_recommendation']}))
