"""Compare the scientific edit with its authenticated visual baseline, CPU only.

This comparison needs the baseline directory; portable package reconstruction
uses the included source bindings and locked-asset receipt instead.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import math
import re

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def rows(path):
    return [[c.strip() for c in line.split('|')[1:-1]]
            for line in path.read_text().splitlines() if line.startswith('|')][2:]


def body_tokens(text):
    # A transparent English-prose heuristic, not TeXcount or submission words.
    text = re.sub(r'(?<!\\)%[^\n]*', '', text)
    text = re.sub(r'\\begin\{(figure\*?|table\*?|equation\*?)\}.*?\\end\{\1\}', '', text, flags=re.S)
    text = re.sub(r'\\(?:section\*?|subsection\*?|paragraph\*?|caption|label|ref|cite(?:p|t)?|input)\{[^}]*\}', '', text)
    text = re.sub(r'\$.*?\$', '', text, flags=re.S)
    text = re.sub(r'\\[A-Za-z]+\*?(?:\[[^]]*\])?', '', text)
    return len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", text))


def compute_ast(path):
    return ast.dump(next(n for n in ast.parse(path.read_text()).body
                         if isinstance(n, ast.FunctionDef) and n.name == 'compute'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', type=Path, default=ROOT.parent / 'manuscript_v0142')
    baseline = ap.parse_args().baseline.resolve()
    assert baseline.is_dir(), 'Supply the authenticated visual-baseline directory'
    receipt = json.loads((ROOT / 'provenance/EDITORIAL_BASELINE.json').read_text())
    prefix = 'paper/jsa/manuscript_v0142/'
    for entry in receipt['files']:
        assert entry['path'].startswith(prefix)
        path = baseline / entry['path'][len(prefix):]
        assert git_blob(path) == entry['sha'], entry['path']

    preserved = {}
    for directory in ['evidence', 'historical_sources', 'source_records']:
        original = {p.relative_to(baseline).as_posix(): sha256(p)
                    for p in (baseline / directory).rglob('*') if p.is_file()}
        current = {p.relative_to(ROOT).as_posix(): sha256(p)
                   for p in (ROOT / directory).rglob('*') if p.is_file()}
        assert current == original, directory
        preserved[directory] = len(original)
    lock = json.loads((ROOT / 'provenance/LOCKED_VISUAL_ASSETS.json').read_text())
    for name, wanted in lock['assets'].items():
        assert sha256(ROOT / name) == sha256(baseline / name) == wanted, name
    assert len(lock['assets']) == 18
    for name in ['references.bib', 'REFERENCE_AUDIT.json', 'elsarticle.cls',
                 'elsarticle-num.bst', 'Highlights.txt', 'declarations.tex',
                 'frozen_verifier.py', 'scripts/visual_figures.py', 'scripts/reconstruct.py']:
        assert (ROOT / name).read_bytes() == (baseline / name).read_bytes(), name
    assert compute_ast(ROOT / 'scripts/reconstruct.py') == compute_ast(baseline / 'scripts/reconstruct.py')
    assert json.loads((ROOT / 'output/NUMERICAL_QA.json').read_text()) == json.loads((baseline / 'output/NUMERICAL_QA.json').read_text())
    assert (ROOT / 'provenance/FIGURE_INPUTS_V0142.json').read_bytes() == (baseline / 'output/FIGURE_INPUTS.json').read_bytes()

    for name in ['main.tex', 'supplement.tex']:
        def preamble(path):
            return re.sub(r'v0\.14\.[23]', 'VERSION', path.read_text().split(r'\begin{document}')[0])
        assert preamble(ROOT / name) == preamble(baseline / name), name
    old_claims, new_claims = rows(baseline / 'CLAIM_EVIDENCE.md'), rows(ROOT / 'CLAIM_EVIDENCE.md')
    assert len(old_claims) == len(new_claims) == 26
    for old, new in zip(old_claims, new_claims):
        for index in [0, 2, 4, 5, 6]:
            assert old[index] == new[index], (old[0], index)
    old_exp = json.loads((baseline / 'EXPERIMENT_DESTINATIONS.json').read_text())['entries']
    new_exp = json.loads((ROOT / 'EXPERIMENT_DESTINATIONS.json').read_text())['entries']
    assert old_exp == new_exp and len(new_exp) == 28

    words = {p.name: dict(before=body_tokens((baseline / p.relative_to(ROOT)).read_text()),
                          after=body_tokens(p.read_text()))
             for p in sorted((ROOT / 'sections').glob('*.tex'))}
    changed = [p.relative_to(ROOT).as_posix() for directory in ['sections', 'supplement']
               for p in sorted((ROOT / directory).glob('*.tex'))
               if p.read_bytes() != (baseline / p.relative_to(ROOT)).read_bytes()]
    bound_reads = [
        'source_records/benchmarks/rtx_consistency_contract_v1/query_batch_patch.py',
        'source_records/benchmarks/rtx_consistency_phase2/scope_patch.py',
        'source_records/benchmarks/rtx_consistency_contract_v1/REPORT_ZH.md',
        'source_records/benchmarks/b570_partition_intervention_v1/DELIVERY_REPORT.md',
        'source_records/benchmarks/rtx_closeout_bcd/REPORT.md',
        'evidence/b57065/CAUSAL_RECHECK.json', 'evidence/rtx66/SOURCE_TIMER_AUDIT.md',
        'source_records/analysis/358h_phase3_summary.json']
    # Summary accounting, distinct from the inherited 180-row prompt-floor audit.
    summary = json.loads((ROOT / 'source_records/analysis/358h_phase3_summary.json').read_text())
    accounting = {}
    for device in ['CPU', 'NPU']:
        d = summary['decomposition'][device]
        total = d['draft_replay_plus_proposal_ms'] + d['target_verification_ms'] + d['orchestration_residual_ms']
        assert math.isclose(total, d['speculative_end_to_end_ms'], rel_tol=1e-12)
        for field, numerator in [('draft_replay_plus_proposal', 'draft_replay_plus_proposal_ms'),
                                 ('target_verification', 'target_verification_ms'),
                                 ('orchestration_residual', 'orchestration_residual_ms')]:
            assert math.isclose(d[numerator] / total, d['fractions_of_speculative_time'][field], rel_tol=1e-10)
        accounting[device] = dict(component_sum_ms=total,
            arithmetic_mean_target_floor=d['baseline_end_to_end_ms'] / d['target_verification_ms'])

    result = dict(version='v0.14.3', status='PASS', baseline_pr=73,
                  baseline_commit='f7d2a863265e6d619d3582d702e57cec1cfa9be2',
                  authenticated_baseline_files=len(receipt['files']),
                  unchanged_directories=preserved, unchanged_visual_assets=18,
                  compute_ast_equal=True, frozen_numerical_qa_equal=True,
                  bibliography_class_styles_declarations_equal=True,
                  document_preambles_equal_except_version_metadata=True,
                  claims=26, claim_ids_evidence_boundaries_destinations_equal=True,
                  experiment_groups=28, experiment_entries_equal=True,
                  changed_sections=changed,
                  body_prose_token_heuristic=dict(method='English regex tokens after removing figure/table/equation environments, headings, citation/reference commands and inline math; excludes abstract/captions/tables/references; not TeXcount',
                      before=sum(v['before'] for v in words.values()),
                      after=sum(v['after'] for v in words.values()), by_section=words),
                  targeted_source_read_sha256={name: sha256(ROOT / name) for name in bound_reads},
                  summary_358h_accounting=accounting,
                  scope='Included summary arithmetic only for 358H; original 180-row prompt floor audit inherited; source reads recorded manually; no private raw audit or inference')
    (ROOT / 'output/EDITORIAL_QA.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
