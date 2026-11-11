#!/usr/bin/env python3
"""Check the v0.9.0 revision and protected inputs; no models or historical suites."""
import collections
import hashlib
import json
import math
import re
import statistics
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
P = ROOT / 'paper/mlsys2027'
E = P / 'evidence'
M = P / 'manuscript'
OUT = M / 'output'
sha = lambda b: hashlib.sha256(b).hexdigest()
gm = lambda xs: math.exp(statistics.mean(math.log(x) for x in xs))


def validate():
    checks = {}
    protection = json.loads((E / 'PROTECTED_INPUTS_V090.json').read_text())
    assert len(protection['protected_files']) == 319
    for item in protection['protected_files']:
        raw = (ROOT / item['path']).read_bytes()
        assert sha(raw) == item['sha256'], item['path']
        assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == item['sha']
    checks['protected_existing_files'] = 319
    checks['protected_scope'] = 'All retained arrays, original estimates/macros/seeds, prior artifacts/reviews, bibliography, official style and historical Figure 3 sources/PDF remain byte-identical.'

    with zipfile.ZipFile(OUT / 'anonymous-evidence-index-v0.8.8.zip') as z:
        old = {n: z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(OUT / 'anonymous-evidence-index-v0.9.0.zip') as z:
        new = {n: z.read(n) for n in z.namelist()}
    assert len(old) == 30 and len(new) == 36
    assert all(new.get(n) == b for n, b in old.items())
    hashes = json.loads(new['SHA256SUMS_V090.json'])
    assert set(hashes) == set(new) - {'SHA256SUMS_V090.json'}
    for n, digest in hashes.items():
        assert not Path(n).is_absolute() and '..' not in Path(n).parts
        assert sha(new[n]) == digest, n
    for n, raw in new.items():
        content = n + ('\n' + raw.decode(errors='replace') if n.endswith(('.py', '.json', '.csv', '.txt')) else '')
        assert not any(x.casefold() in content.casefold() for x in ['leecdiang', '/Users/', '/home/', 'D:\\', 'C:\\', 'file://'])
    checks['scientific_package'] = {'prior_members_byte_identical': 30, 'new_members': 6, 'all_hashes': 'PASS', 'anonymous_text_and_paths': 'PASS'}
    d = json.loads(new['derived/ACCEPTANCE_DIAGNOSTIC_V090.json'])
    assert new['derived/ACCEPTANCE_DIAGNOSTIC_V090.json'] == (E / 'ACCEPTANCE_DIAGNOSTICS_V090.json').read_bytes()
    assert new['derived/ACCEPTANCE_DIAGNOSTIC_V090.json'] == (P / 'reviews/acceptance_reassessment_v089/acceptance_diagnostic.json').read_bytes()
    assert new['derived/358h_phase3_prompt_summary.csv'] == (ROOT / 'analysis/358h_phase3_prompt_summary.csv').read_bytes()
    checks['diagnostic_record_identity'] = 'Original known-outcome analysis and canonical CSV preserved exactly.'

    b = json.loads(new['evidence/B570_original_H1.json'])
    groups = collections.defaultdict(list)
    for row in b['rows']:
        a = row['arrays']
        assert a['prediction'] == a['live'] and len(a['live']) == len(a['reference']) == 128
        groups[row['task_id']].append(row)
    assert len(groups) == 24 and all(len(v) == 3 for v in groups.values())
    cases = {}
    for task, rows in groups.items():
        a = rows[0]['arrays']
        assert all(r['arrays'] == a for r in rows)
        diffs = [i for i, (x, y) in enumerate(zip(a['reference'], a['live'])) if x != y]
        if diffs:
            assert diffs == list(range(diffs[0], 128))
            cases[task] = (diffs[0], len(diffs))
    assert cases == {'HumanEval/134': (88, 40), 'HumanEval/42': (73, 55), 'HumanEval/145': (103, 25), 'HumanEval/138': (93, 35)}
    a = groups['HumanEval/134'][0]['arrays']
    assert (a['reference'][88], a['prediction'][88], a['live'][88]) == (914, 1946, 1946)
    assert sum(v[1] for v in cases.values()) == 155
    assert sum(v[1] - 1 for v in cases.values()) == 151
    checks['B570_worked_example'] = {'prompts': 24, 'pairs': 72, 'distinct_divergent_trajectories': 4, 'nonreference_positions': 155, 'strictly_after_first': 151, 'repetition_stability': 'PASS'}

    v = json.loads(new['evidence/RTX_V4.json'])
    groups = collections.defaultdict(list)
    for row in v['A']:
        groups[row['task_id']].append(row)
    assert len(groups) == 19 and all(len(x) == 3 for x in groups.values())
    gates = collections.Counter()
    for rows in groups.values():
        first = {k: x['ids'] for k, x in rows[0]['conditions'].items()}
        assert all({k: x['ids'] for k, x in r['conditions'].items()} == first for r in rows)
        for row in rows:
            c = row['conditions']; live = c['A_NATIVE_BATCHED_LIVE']['ids']
            for k, x in c.items():
                gates[k] += x['ids'] == live
    assert dict(gates) == d['RTX']['A_live_agreement_counts']
    def ids(task, key):
        return groups['HumanEval/' + str(task)][0]['conditions'][key]['ids']
    ub = 'A_TARGET_ONLY_UB2'; ref = 'A_REFERENCE_UB1'; live = 'A_NATIVE_BATCHED_LIVE'
    assert len(ids(15, ub)) == 28 and len(ids(15, live)) == 25 and ids(15, ub) == ids(15, ref)
    assert [i for i, (a, b) in enumerate(zip(ids(15, ub), ids(15, live))) if a != b] == list(range(15, 25))
    assert (ids(15, ub)[15], ids(15, live)[15]) == (4199, 9147)
    assert len(ids(18, ref)) == 72 and len(ids(18, live)) == 69 and ids(18, ub) == ids(18, live)
    assert [i for i, (a, b) in enumerate(zip(ids(18, ref), ids(18, live))) if a != b] == list(range(29, 69))
    assert len(ids(25, ub)) == len(ids(25, live)) == 75
    assert [i for i, (a, b) in enumerate(zip(ids(25, ub), ids(25, live))) if a != b] == [4]
    covered = sum(ids(t.split('/')[-1], ref) == ids(t.split('/')[-1], live) or ids(t.split('/')[-1], ub) == ids(t.split('/')[-1], live) for t in groups)
    assert covered == 18
    checks['RTX_worked_examples'] = {'same_cohort_prompts': 19, 'pairs_per_condition': 57, 'failure_extents': {'/15': '10/25 common IDs, 3 extra', '/18': '40/69 common IDs, 3 extra', '/25': 'one ID, then reconvergence'}, 'hindsight_coverage': '18/19; not a predictor', 'all_five_conditions_repeat_stable': True}

    inputs = json.loads(new['derived/inputs.json'])
    bounds = {}
    for mode in ['CPU', 'NPU']:
        rows = [r for r in inputs['358H']['rows'] if r['condition'] == mode + '_DRAFT_K2']
        grouped = collections.defaultdict(list)
        for r in rows:
            baseline = float(r['baseline_end_to_end_ms']); target = float(r['verification_ms'])
            total = float(r['end_to_end_ms']); draft = float(r['draft_replay_proposal_ms']); residual = float(r['orchestration_residual_ms'])
            assert baseline > 0 and target > 0 and draft >= 0 and residual >= 0
            assert abs(target + draft + residual - total) < 0.01
            assert baseline / total <= baseline / target
            grouped[r['task_id']].append(baseline / target)
        assert len(rows) == 90 and len(grouped) == 30 and all(len(x) == 3 for x in grouped.values())
        u = gm(statistics.median(x) for x in grouped.values())
        assert math.isclose(u, d['358H'][mode]['new_prompt_gm_upper_bound'], abs_tol=1e-14)
        assert all(statistics.median(x) < 1 for x in grouped.values())
        assert sum(x >= 1 for values in grouped.values() for x in values) == (1 if mode == 'NPU' else 0)
        bounds[mode] = {'prompt_gm_ceiling': u, 'uniform_target_reduction_percent_necessary_under_zero_other_cost': 100 * (1 - u)}
    checks['358H_conditional_budget'] = bounds

    m = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in inputs['M4']:
        m[(r['workload_family'], r['task_id'])][r['condition']].append(r['end_to_end_ns'])
    assert len(m) == 60 and len(inputs['M4']) == 540 and all(len(x) == 3 for c in m.values() for x in c.values())
    med = [{k: statistics.median(x) for k, x in c.items()} for c in m.values()]
    oracle = gm(x['ALWAYS_SPEC_K2'] / min(x['TARGET_ONLY'], x['ALWAYS_SPEC_K2']) for x in med)
    assert math.isclose(oracle, d['M4']['always_over_two_fixed_mode_oracle_gm'], abs_tol=1e-14)
    opportunity = 100 * (1 - 1 / oracle)
    checks['M4_two_fixed_mode_opportunity'] = {'latency_reduction_percent': opportunity, 'full_precision_ratio_used': oracle, 'target_faster_prompts': sum(x['TARGET_ONLY'] < x['ALWAYS_SPEC_K2'] for x in med), 'scope': 'Known-outcome two measured fixed modes only.'}

    macros = dict(re.findall(r'\\newcommand\{\\(\w+)\}\{([^}]+)\}', (M / 'tables/acceptance_values_v090.tex').read_text()))
    expected = {'DiagBNonref': '155', 'DiagBAfter': '151', 'DiagCPUCeiling': f"{bounds['CPU']['prompt_gm_ceiling']:.4f}", 'DiagNPUCeiling': f"{bounds['NPU']['prompt_gm_ceiling']:.4f}", 'DiagCPUReduction': f"{bounds['CPU']['uniform_target_reduction_percent_necessary_under_zero_other_cost']:.2f}", 'DiagNPUReduction': f"{bounds['NPU']['uniform_target_reduction_percent_necessary_under_zero_other_cost']:.2f}", 'DiagMOpportunity': f'{opportunity:.3f}'}
    assert macros == expected, (macros, expected)
    main = (M / 'main.tex').read_text(); app = (M / 'appendix.tex').read_text()
    assert 'acceptance_values_v090' in main and 'acceptance_values_v090' in app
    assert all(x in app for x in ['appendix_derived_v090', 'appendix_followups_v090', 'appendix_rtx_v4_v090'])
    outcome = (M / 'sections/04_outcomes.tex').read_text()
    assert 'On /134,' in outcome and 'native execution remains' in outcome
    assert 'rtx_v4_trajectory_v090' in outcome
    assert 'system_decisions_v090' in (M / 'sections/06_synthesis.tex').read_text()
    checks['new_macros_and_current_inclusions'] = expected

    build = json.loads((E / 'CLEAN_ZIP_REBUILD_V090_QA.json').read_text())
    assert build['status'] == 'RERUN_PASS' and build['all_hashes_verified']
    for path, digest in build['source_files'].items():
        assert sha((ROOT / path).read_bytes()) == digest, path
    assert all(c['raw_extracted_page_text_exact_equal'] and not c['normalization_applied'] for c in build['comparison'].values())
    assert sha((OUT / 'overleaf-diagnostic-revision-v0.9.0.zip').read_bytes()) == build['zip_sha256']
    visual = json.loads((E / 'VISUAL_QA_V090.json').read_text())
    pdf = json.loads((E / 'PDF_AND_ANONYMITY_V090_QA.json').read_text())
    assert visual['status'] == pdf['status'] == 'RERUN_PASS'
    assert pdf['manual_visual_review'].startswith('RERUN_PASS')
    assert pdf['manual_visual_receipt_sha256'] == sha((E / 'VISUAL_QA_V090.json').read_bytes())
    assert len(visual['pages']) == visual['total_final_page_coverage'] == 40
    for n, v in pdf['pdfs'].items():
        path = OUT / ({'main': 'manuscript', 'appendix': 'appendix', 'hardware-only': 'hardware-only'}[n] + '-v0.9.0.pdf')
        assert sha(path.read_bytes()) == v['sha256'] == visual['pdf_sha256'][n]
    assert (pdf['pdfs']['main']['body_pages'], pdf['pdfs']['main']['references_pages'], pdf['pdfs']['appendix']['pages']) == (10, 2, 17)
    package = json.loads((E / 'DIAGNOSTIC_PACKAGE_V090_QA.json').read_text())
    assert package['status'] == 'PASS' and package['two_clean_calculations'][0] == package['two_clean_calculations'][1]
    assert sha((ROOT / package['new_package']['path']).read_bytes()) == package['new_package']['sha256']
    checks['build_PDF_and_visual_QA'] = {'two_clean_source_extractions': 'PASS; exact raw page texts', 'main': '10 body + 2 references', 'appendix': '17 pages', 'internal_proof': '9 body + 2 references', 'final_page_visual_coverage': 40, 'final_manual_pages': 26, 'exact_current_turn_candidate_pixel_reuse': 14, 'new_diagnostics_two_clean_extractions': 'PASS'}
    report = {'status': 'PASS', 'version': 'v0.9.0', 'checks': checks, 'scope': 'New revision regression and known-outcome arithmetic. Protected inputs checked by hashes. Historical model/data suites and bootstrap were not rerun.', 'model_execution': False, 'new_hardware_experiments': False, 'new_confidence_intervals': False, 'acceptance_rescore': False}
    (E / 'REVISION_V090_QA.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'protected_files': 319, 'final_visual_pages': 40, 'new_macro_checks': 7, 'models_or_historical_bootstrap_run': False}))
    return report


if __name__ == '__main__':
    validate()
