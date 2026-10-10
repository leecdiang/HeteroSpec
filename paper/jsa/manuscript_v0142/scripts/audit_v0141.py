"""Independent CPU checks of the v0.14.2 core arithmetic and evidence ledger.

Uses only the Python standard library and committed exports. It neither invokes
the inherited verifier nor runs a model/runtime, and does not parse private raw
archives. The full interval/digest reconstruction remains in reconstruct.py.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import statistics

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads((ROOT / path).read_text())


def read_csv(path):
    with (ROOT / path).open(newline='') as handle:
        return list(csv.DictReader(handle))


def gm(values):
    values = list(values)
    assert values and all(math.isfinite(v) and v > 0 for v in values)
    return math.exp(statistics.mean(math.log(v) for v in values))


def equal(actual, expected):
    assert math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12), (actual, expected)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_preservation():
    receipts = read_json('provenance/READ_SOURCE_INDEX.json')['files']
    receipts += read_json('provenance/ADDITIONAL_SOURCE_INDEX.json')['records']
    names = set()
    for record in receipts:
        path = ROOT / 'source_records' / record['path']
        data = path.read_bytes()
        assert len(data) == record['bytes']
        assert sha(path) == record['sha256']
        assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == record.get('git_blob', record.get('git_blob_sha'))
        names.add(record['path'])
    assert len(names) == len(receipts)
    manifest = {}
    baseline = ROOT.parent / 'manuscript_v014'
    comparison_count = 0
    for directory in ['evidence', 'historical_sources']:
        files = sorted(p for p in (ROOT / directory).rglob('*') if p.is_file())
        for path in files:
            relative = path.relative_to(ROOT)
            bound = ROOT / 'source_records/paper/jsa/manuscript_v013' / relative
            assert path.read_bytes() == bound.read_bytes(), str(relative)
            if baseline.exists():
                assert path.read_bytes() == (baseline / relative).read_bytes(), str(relative)
                comparison_count += 1
        manifest[directory] = {str(p.relative_to(ROOT)): sha(p) for p in files}
    return {
        'authenticated_source_copies': len(receipts),
        'evidence_files': len(manifest['evidence']),
        'historical_files': len(manifest['historical_sources']),
        'v014_sibling_comparisons': comparison_count,
        'binding_scope': 'Git blob/SHA-256 receipts and bound source copies; no private raw archive reopened',
        'sha256': manifest,
    }


def rtx_costs():
    rows = read_csv('evidence/rtx66/RAW_COSTS.csv')
    tasks = list(dict.fromkeys(r['task'] for r in rows))
    conditions = ['scalar_reference', 'matched_target', 'target_scopes', 'all_scopes']
    assert len(rows) == 384 and len(tasks) == 24
    by_key = {(r['task'], r['condition'], int(r['repetition'])): r for r in rows}
    assert len(by_key) == len(rows)
    assert set(by_key) == {(t, c, n) for t in tasks for c in conditions for n in range(1, 5)}
    assert all(r['qualified'] == 'True' and r['timer_unit'] == 'ms' for r in rows)
    medians = {(t, c, timer): statistics.median(float(by_key[t, c, n][timer + '_ms']) for n in range(1, 5))
               for t in tasks for c in conditions for timer in ['generation', 'whole']}
    results = []
    for summary in read_json('evidence/rtx66/COST_SUMMARY.json')['comparisons']:
        b, c, timer = summary['baseline'], summary['candidate'], summary['timer']
        ratios = [medians[t, b, timer] / medians[t, c, timer] for t in tasks]
        actual = gm(ratios)
        equal(actual, summary['task_median_gm'])
        assert sum(r > 1 for r in ratios) == summary['faster_tasks']
        rounds = []
        for n, expected in enumerate(summary['rounds'], 1):
            value = gm(float(by_key[t, b, n][timer + '_ms']) / float(by_key[t, c, n][timer + '_ms']) for t in tasks)
            equal(value, expected['gm'])
            rounds.append(value)
        results.append({'baseline': b, 'candidate': c, 'timer': timer, 'gm': actual, 'rounds': rounds})
    for timer in ['generation', 'whole']:
        for t in tasks:
            r, m, c = (medians[t, name, timer] for name in ['scalar_reference', 'matched_target', 'target_scopes'])
            equal(r / c, (r / m) * (m / c))
        equal(gm(medians[t, 'scalar_reference', timer] / medians[t, 'target_scopes', timer] for t in tasks),
              gm(medians[t, 'scalar_reference', timer] / medians[t, 'matched_target', timer] for t in tasks) *
              gm(medians[t, 'matched_target', timer] / medians[t, 'target_scopes', timer] for t in tasks))
    regressions = [t for t in tasks if medians[t, 'matched_target', 'whole'] < medians[t, 'target_scopes', 'whole']]
    assert regressions == ['MBPP/439', 'MBPP/124', 'MBPP/458', 'MBPP/437', 'MBPP/115', 'MBPP/454', 'MBPP/393']
    assert next(r for r in results if r['baseline'] == 'matched_target' and r['candidate'] == 'target_scopes' and r['timer'] == 'whole')['rounds'][1] < 1
    return {'formal_rows': len(rows), 'tasks': len(tasks), 'conditions': len(conditions),
            'comparisons_recomputed': len(results), 'round_gms_recomputed': 4 * len(results),
            'identity_checks': {'task_timer_cells': 48, 'aggregate_timers': 2},
            'matched_request_regressions': regressions, 'ratios': results,
            'scope': 'Absolute-time CSV medians and ratios; arrays/digest joins checked by the full reconstruction separately'}


def b570_costs():
    rows = read_csv('evidence/b57065/COSTS_RECOMPUTED.csv')
    assert len(rows) == 119 and len({r['unit_id'] for r in rows}) == 119
    assert 'E/FORMAL/1/old_N1/MBPP/400' not in {r['unit_id'] for r in rows}
    tasks = sorted({r['task'] for r in rows})
    conditions = ['ordinary_R', 'matched_target', 'candidate', 'old_N1']
    timers = ['generation_ms', 'whole_ms', 'host_ms']
    medians = {}
    for t in tasks:
        for c in conditions:
            pair = [r for r in rows if r['task'] == t and r['label'] == c]
            assert len(pair) == (1 if (t, c) == ('MBPP/400', 'old_N1') else 2)
            if len(pair) == 2:
                for timer in timers:
                    medians[t, c, timer] = statistics.median(float(r[timer]) for r in pair)
    result = []
    pairs = {}
    summary = read_json('evidence/b57065/COST_SUMMARY.json')['comparisons']
    for b, c in [('ordinary_R', 'candidate'), ('matched_target', 'candidate'), ('old_N1', 'candidate'), ('ordinary_R', 'matched_target')]:
        name = b + '/' + c
        eligible = [t for t in tasks if (t, b, timers[0]) in medians and (t, c, timers[0]) in medians]
        pairs[name] = len(eligible)
        assert len(eligible) == summary[name]['tasks'] == (14 if b == 'old_N1' else 15)
        for timer in timers:
            value = gm(medians[t, b, timer] / medians[t, c, timer] for t in eligible)
            equal(value, summary[name]['metrics'][timer]['task_GM'])
            result.append({'comparison': name, 'tasks': len(eligible), 'timer': timer, 'gm': value})
    by_key = {(r['task'], r['label'], int(r['round'])): r for r in rows}
    for b in ['ordinary_R', 'matched_target']:
        assert all(float(by_key[t, b, n][timer]) < float(by_key[t, 'candidate', n][timer])
                   for t in tasks for n in [1, 2] for timer in timers)
    old_reversal = {timer: float(by_key['MBPP/245', 'old_N1', 2][timer]) / float(by_key['MBPP/245', 'candidate', 2][timer])
                    for timer in ['whole_ms', 'host_ms']}
    assert all(r < 1 for r in old_reversal.values())
    candidate = [r for r in rows if r['label'] == 'candidate']
    assert len(candidate) == 30
    totals = {field: sum(int(r[field]) for r in candidate) for field in ['endpoint_length', 'raw_length', 'raw_suffix']}
    assert totals == {'endpoint_length': 1150, 'raw_length': 1176, 'raw_suffix': 26}
    assert all(int(r['raw_length']) == int(r['endpoint_length']) + int(r['raw_suffix']) for r in rows)
    qualification = read_csv('evidence/b57065/QUALIFICATION_RECOMPUTED.csv')
    assert len(qualification) == 299
    formal = [r for r in qualification if r['unit_id'].startswith('E/FORMAL/')]
    assert {r['unit_id'] for r in formal} == {r['unit_id'] for r in rows}
    assert all(r['reference_endpoint_equal'] == 'True' and r['all_suffix_work_paid'] == 'True' for r in formal)
    work = read_csv('evidence/b57065/WORK_BREAKDOWN.csv')
    work_totals = {f: sum(int(r[f]) for r in work) for f in ['drafted', 'accepted', 'target_verification_caller_tokens', 'draft_proposal_tokens', 'draft_catchup_tokens']}
    assert len(work) == 30 and work_totals['drafted'] == 888 and work_totals['accepted'] == 702
    assert work_totals['target_verification_caller_tokens'] == 1332
    assert work_totals['draft_proposal_tokens'] + work_totals['draft_catchup_tokens'] == 1362
    return {'formal_rows': 119, 'planned_rows': 120, 'paired_tasks': pairs,
            'timer_aggregates_recomputed': len(result), 'ratios': result,
            'strong_baselines_faster_all_complete_rounds_and_timers': True,
            'old_n1_MBPP245_round2_reversal': old_reversal, 'paid_suffix_totals': totals, 'work_totals': work_totals,
            'missing_payload_or_interruption_cost_imputed': False}


def phase_and_width():
    phase = read_json('source_records/benchmarks/rtx_consistency_phase2/results/A1_RESULTS.json')['conditions']
    assert {c['mask'] for c in phase} == set(range(16))
    assert len(phase) == 16 and sum(c['requests'] for c in phase) == 128
    passing = [c['mask'] for c in phase if all(c['task_matches'].values())]
    assert passing == [3, 7, 11, 15]
    assert all(c['qualifies'] == all(c['task_matches'].values()) for c in phase)
    assert not any(c['mask'] != 3 and c['qualifies'] and c['mask'] & 3 == c['mask'] for c in phase)
    fixed = read_json('evidence/RTX_FIXED_UB_RESULTS.json')
    checked = 0
    for group in [fixed] + list(fixed['cohorts'].values()):
        for c in group['costs']:
            if c['qualified']:
                for timer in ['generation', 'wall']:
                    equal(gm(c[timer]['task_ratios'].values()), c[timer]['task_median_geomean_speedup'])
                    checked += 1
    assert fixed['qualification'] == {'matched_target': True, 'anchor_speculation': True, 'wider_speculation': True, 'ordinary_wider': False}
    return {'phase_passing_masks': passing, 'phase_requests': 128,
            'minimality_scope': 'Inclusion-minimal in the tested four-switch family only',
            'fixed_ub_saved_task_ratio_gms_checked': checked,
            'width_scope': 'Saved task-ratio export arithmetic; no independent raw timing parse'}


def ledger():
    groups = read_json('EXPERIMENT_DESTINATIONS.json')
    entries = groups['entries']
    assert [e['id'] for e in entries] == [f'E{i:02d}' for i in range(1, 29)]
    allowed = {'main-core', 'main-brief-supplement-detail', 'supplement-boundary-history-reproducibility'}
    assert all(e['v0141_disposition'] in allowed and e['v0141_destination'] and e['original_sources'] for e in entries)
    assert all(e['original_evidence_preserved'] for e in entries)
    for e in entries:
        for path in e['supplementary_source'].split('; '):
            assert (ROOT / path).is_file(), path
    original_rows = [[c.strip() for c in line.split('|')[1:-1]] for line in (ROOT / 'provenance/PLANNING_EVIDENCE_LEDGER.md').read_text().splitlines() if line.startswith('|')][2:]
    assert len(original_rows) == 28
    for e, original in zip(entries, original_rows):
        assert [e[k] for k in ['original_group', 'original_key_facts', 'original_destination', 'original_sources']] == original
    claims = read_csv('CLAIM_EVIDENCE.csv')
    assert [c['claim_id'] for c in claims] == [f'C{i:02d}' for i in range(1, 27)]
    assert all(c['v0141_disposition'] and c['detailed_destination'] and c['scientific_boundary'] for c in claims)
    return {'original_groups': 28, 'covered_groups': 28, 'unassigned_groups': 0, 'claims': 26,
            'dispositions': {k: sum(e['v0141_disposition'] == k for e in entries) for k in sorted(allowed)},
            'original_planning_facts_and_source_paths_unchanged': True}


def main():
    result = {'revision': 'v0.14.2', 'status': 'PASS',
              'scope': 'Independent standard-library CPU recomputation from committed exports and ledger; no private raw audit',
              'preservation': source_preservation(), 'rtx': rtx_costs(), 'b570': b570_costs(),
              'phase_and_width': phase_and_width(), 'ledger': ledger(),
              'new_model_requests': 0, 'new_forwards': 0, 'new_warmups': 0,
              'toolchain': {'python': __import__('sys').version.split()[0], 'third_party_numeric_packages': 'None'}}
    output = ROOT / 'output/SCIENTIFIC_QA.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'rtx_rows': result['rtx']['formal_rows'],
                      'b570_rows': result['b570']['formal_rows'], 'ledger': result['ledger']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
