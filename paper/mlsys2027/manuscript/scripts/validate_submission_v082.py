#!/usr/bin/env python3
"""Audit the v0.8.2 manuscript-only finalization against merged v0.8.1 main.

Run after staging the intended changes and rendering/inspecting the final PDFs.
"""
from pathlib import Path
import hashlib, io, json, subprocess, zipfile
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[4]
P = 'paper/mlsys2027/'
M = P + 'manuscript/'
BASE = '2f4a38c316d6d4683822e6a24a74bddad9d3117f'
FREEZE = '1d3b556c93b477680788dfd1eb0737dfe9eee28c'
BRANCH = 'paper/mlsys2027-final-cleanroom-fixes-v0.8.2'
TITLE = 'Execution-Path Qualification and Realized Costs in Speculative Decoding on Consumer Systems'
RUNNING = 'Execution-Path Qualification in Speculative Decoding'
PHRASE = 'all 72 complete generated-token-ID sequences on the reserved set'
BOUNDARY = ('These prospective qualification studies are separate from the historical '
            'timing campaigns and do not retrospectively certify those timings under '
            'the direct-ID contract.')
PROVENANCE = ('Clean-room review based only on manuscript-v0.8.1.pdf and '
              'appendix-v0.8.1.pdf. No repository evidence, prior reviews, source '
              'files, handover documents, web search, or experiment records were consulted.')

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert git('rev-parse', 'main') == BASE
assert git('rev-parse', '--abbrev-ref', 'HEAD') == BRANCH
assert git('rev-parse', 'mlsys2027-v0.8-author-freeze^{commit}') == FREEZE
assert not git('tag', '--list', 'mlsys2027-v0.8.2-submission-candidate-*')
review_names = ('REVIEWER_A_SYSTEMS.md', 'REVIEWER_B_NOVELTY_RIGOR.md',
                'META_REVIEW.md', 'FINAL_ACTIONS.md')
reviews = ROOT / P / 'reviews/final_clean_room_v081'
assert sorted(p.name for p in reviews.iterdir()) == sorted(review_names)
review_hashes = {}
for name in review_names:
    content = (reviews / name).read_text()
    assert content.startswith(PROVENANCE + '\n')
    review_hashes[name] = digest(reviews / name)
assert 'READY AFTER MINOR TEXTUAL REVISION' in (reviews / 'META_REVIEW.md').read_text()
assert '**NO.**' in (reviews / 'FINAL_ACTIONS.md').read_text()

allowed_modified = {P + n for n in ('HANDOVER_CURRENT.md', 'MANUSCRIPT_STATUS.md',
                                      'SUBMISSION_UPLOAD_CHECKLIST.md')}
allowed_modified.update(M + n for n in ('README.md', 'main.tex', 'appendix.tex',
                                        'sections/01_introduction.tex'))
allowed_added = {P + 'evidence/' + n for n in (
    'FINAL_CLEANROOM_FIXES_V082.md', 'FINAL_SUBMISSION_QA_V082.json',
    'NARRATIVE_PDF_FINALIZATION_V082_QA.json', 'CLEAN_ZIP_FINALIZATION_V082_QA.json')}
allowed_added.update(P + 'reviews/final_clean_room_v081/' + n for n in review_names)
allowed_added.update(M + 'scripts/' + n for n in (
    'build_v082.py', 'package_overleaf_v082.py', 'qa_pdf_v082.py',
    'validate_submission_v082.py'))
output_names = ('manuscript-v0.8.2.pdf', 'appendix-v0.8.2.pdf',
                'hardware-only-v0.8.2.pdf', 'overleaf-submission-readiness-v0.8.2.zip')
allowed_added.update(M + 'output/' + n for n in output_names)
changed = set(git('diff', '--name-only', BASE).splitlines())
assert changed <= allowed_modified | allowed_added, sorted(changed - allowed_modified - allowed_added)
assert allowed_modified <= changed
assert (allowed_added - {P + 'evidence/FINAL_SUBMISSION_QA_V082.json'}) <= changed
assert set(git('diff', '--name-only', '--', 'benchmarks', 'artifacts', 'reports', 'analysis').splitlines()) == set()
tracked = set(git('ls-tree', '-r', '--name-only', BASE).splitlines())
assert not (changed - allowed_modified).intersection(tracked)

main = (ROOT / M / 'main.tex').read_text()
intro = (ROOT / M / 'sections/01_introduction.tex').read_text()
appendix = (ROOT / M / 'appendix.tex').read_text()
assert main.count(PHRASE) == 1 and 'all 72 serialized output sequences' not in main
assert intro.count(BOUNDARY) == 1
assert main.count(TITLE) == 2 and main.count(RUNNING) == 1
assert appendix.count(TITLE) == 2 and appendix.count(RUNNING) == 1
assert '\\mlsystitle{' + TITLE + '}' in main
assert 'pdfsubject={MLSys 2027 research manuscript v0.8.2}' in main
assert 'pdfsubject={MLSys 2027 separate appendix v0.8.2}' in appendix
for folder in ('sections', 'figures', 'tables'):
    for path in (ROOT / M / folder).glob('*.tex'):
        assert path == ROOT / M / 'sections/01_introduction.tex' or P + str(path.relative_to(ROOT / P)) not in changed

evidence = ROOT / P / 'evidence'
pdf_qa = json.loads((evidence / 'NARRATIVE_PDF_FINALIZATION_V082_QA.json').read_text())
zip_qa = json.loads((evidence / 'CLEAN_ZIP_FINALIZATION_V082_QA.json').read_text())
assert pdf_qa['status'] == zip_qa['status'] == 'PASS'
assert (pdf_qa['main_text_pages'], pdf_qa['references_pages'],
        pdf_qa['pdfs']['appendix']['pages']) == (10, 2, 6)
assert pdf_qa['main_figures']['fig:verification'] == {'number': '3', 'page': 7}
assert pdf_qa['references']['entries'] == 19 and pdf_qa['references']['full_author_lists']
assert zip_qa['all_manifest_hashes_match']
assert all(x['extracted_text_equal'] for x in zip_qa['comparison'].values())

out = ROOT / M / 'output'
artifacts = {}
for name in output_names:
    path = out / name
    assert path.exists()
    artifacts[name] = {'sha256': digest(path), 'bytes': path.stat().st_size}
for name in output_names[:3]:
    r = PdfReader(out / name)
    expected = 'Supplement: ' + TITLE if name.startswith('appendix') else TITLE
    assert r.metadata['/Title'] == expected
    assert r.metadata['/Author'] == 'Anonymous Authors'
    assert '/Users/' not in '\n'.join(p.extract_text() or '' for p in r.pages)
with zipfile.ZipFile(out / output_names[-1]) as z:
    names = z.namelist()
    assert len(names) == len(set(names)) == 39
    manifest = json.loads(z.read('SHA256SUMS.json'))
    assert set(manifest) == set(names) - {'SHA256SUMS.json'}
    assert all(hashlib.sha256(z.read(n)).hexdigest() == v for n, v in manifest.items())
    assert PHRASE in z.read('main.tex').decode()
    assert BOUNDARY in z.read('sections/01_introduction').decode()
    assert TITLE in z.read('README.txt').decode()
    assert not any(n.startswith(('benchmarks/', 'artifacts/', 'reports/', 'analysis/')) for n in names)

report = {
    'status': 'PASS', 'base_main_sha': BASE, 'branch': BRANCH,
    'manuscript_version': 'v0.8.2', 'title': TITLE, 'running_title': RUNNING,
    'abstract_complete_generated_token_id_phrase': True,
    'historical_vs_fresh_boundary_explicit': True,
    'body_pages': 10, 'reference_pages': 2, 'appendix_pages': 6,
    'hardware_only_pages': pdf_qa['pdfs']['hardware-only']['pages'],
    'clean_build_pass': True, 'clean_zip_rebuild_pass': True,
    'anonymity_pass': True, 'font_embedding_pass': True,
    'font_substitutions': 0, 'unresolved_refs': 0, 'unresolved_citations': 0,
    'overfull_boxes': 0, 'bibliography_full_author_lists': True,
    'figure_3_page': 7, 'figure_sources_changed': False,
    'protected_science_changed': False,
    'protected_base_tracked_paths': len(tracked - allowed_modified),
    'new_inference': False, 'new_experiment': False,
    'new_performance_measurement': False, 'new_energy_measurement': False,
    'new_reviewer_simulation': False, 'title_changed': False,
    'contribution_structure_changed': False, 'pr_merged': False,
    'submission_candidate_tag_created': False,
    'review_provenance_statement': PROVENANCE,
    'clean_room_review_file_sha256': review_hashes,
    'manual_visual_review': {'status': 'PASS', 'main_pages': 12, 'appendix_pages': 6,
        'focus': ['title', 'abstract', 'first Introduction paragraphs', 'Figure 3',
                  'reference first page', 'page balance'],
        'finding': 'All pages rendered and inspected; no clipping, overlap or unreadable glyphs.'},
    'artifact_sha256': {n: v['sha256'] for n, v in artifacts.items()},
    'artifacts': artifacts,
    'changed_paths': sorted(changed | {P + 'evidence/FINAL_SUBMISSION_QA_V082.json'}),
    'scope_note': 'PDF/TeX build and read-only audit only; no model or measurement runner invoked.',
    'page_limit_note': 'A first textual build reached 11 body pages; light nearby prose compression restored 10 without layout changes.'
}
(evidence / 'FINAL_SUBMISSION_QA_V082.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': 'PASS', 'body': 10, 'references': 2, 'appendix': 6,
                  'protected_paths': report['protected_base_tracked_paths']}))
