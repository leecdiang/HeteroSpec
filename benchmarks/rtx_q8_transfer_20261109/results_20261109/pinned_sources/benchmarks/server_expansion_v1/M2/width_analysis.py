"""Post-panel descriptive width contrasts; no model or native execution.

Consumes the complete CHECKED workers and the pre-timing declaration. This is
an additive report, not a change to the frozen panel analyzer or its results.
"""
from pathlib import Path
import argparse, hashlib, json


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ratio(a, b):
    return a / b if b else None


def analyze(work, text_index=None):
    panel = work / 'panel-01'
    declaration = work / 'WIDTH_CONTRASTS_PREDECLARED.json'
    declared = read(declaration)
    records = read(panel / 'CHECKED.json')
    plan = read(panel / 'PLAN.json')
    index = {x['path']: x for x in read(text_index)['files']} if text_index else {}

    def commitment(path):
        key = str(Path(work.name) / path.relative_to(work))
        if index:
            row = index[key]
            assert path.stat().st_size == row['exported_bytes'] and sha(path) == row['exported_sha256']
            return row['raw_bytes'], row['raw_sha256']
        return path.stat().st_size, sha(path)
    assert len(records) == len(plan['workers']) == 24
    assert [w['id'] for w in records] == [w['id'] for w in plan['workers']]
    assert all(w['status'] == 'COMPLETE' for w in records)
    assert declared['M2_timed_workers_started'] == 0
    modes = {}
    for mode, expected_workers, expected_calls in [('live', 16, 64), ('replay', 8, 32)]:
        workers = [w for w in records if w['proposal_mode'] == mode]
        assert len(workers) == expected_workers
        arms = {}
        for arm in plan['arms']:
            ws = [w for w in workers if w['arm'] == arm]
            calls = [c for w in ws for c in w['calls'] if c['kind'] == 'measurement']
            primers = [c for w in ws for c in w['calls'] if c['kind'] == 'primer']
            assert len(calls) == expected_calls // 8
            assert all(c['endpoint_equal'] and c['trace_valid'] for c in calls + primers)
            histogram = {}
            for c in calls:
                for width, count in c['physical']['verify_width_histogram'].items():
                    histogram[width] = histogram.get(width, 0) + count
            arms[arm] = dict(
                measurements=len(calls), primers=len(primers),
                service_s=sum(c['service_s'] for c in calls),
                request_s=sum(c['request_s'] for c in calls),
                target_prefill_s=sum(c['target_phases'].get('PREFILL', 0) for c in calls),
                target_verify_s=sum(c['target_phases'].get('VERIFY', 0) for c in calls),
                draft_phase_s=sum(sum(c['draft_phases'].values()) for c in calls),
                target_rows=sum(c['physical']['target_rows'] for c in calls),
                draft_rows=sum(c['physical']['draft_rows'] for c in calls),
                cycles=sum(c['cycles'] for c in calls),
                accepted_proposals=sum(c['accepted_proposals'] for c in calls),
                proposed=sum(c['proposed'] for c in calls),
                rejected_cycles=sum(c['rejected_cycles'] for c in calls),
                output_tokens=sum(c['output_tokens'] for c in calls),
                physical_verify_width_histogram=histogram,
                primer_service_s=sum(c['service_s'] for c in primers),
                native_process_wall_s=sum(w['actual_host']['worker_wall_s'] for w in ws),
                adapter_run_inclusive_s=sum(w['adapter_run_inclusive_s'] for w in ws),
                model_load_s=sum(w['model_load_s'] for w in ws),
                pool_setup_s=sum(w['pool_setup_s'] for w in ws),
                serialized_job_bytes=sum(commitment(panel / w['job'])[0] for w in ws),
            )
            a = arms[arm]
            a['proposals_not_accepted'] = a['proposed'] - a['accepted_proposals']
            a['proposal_acceptance_fraction'] = ratio(a['accepted_proposals'], a['proposed'])
            a['target_rows_per_output_token'] = ratio(a['target_rows'], a['output_tokens'])
            a['draft_rows_per_output_token'] = ratio(a['draft_rows'], a['output_tokens'])
        comparisons = {}
        for family in ('registered_PR197_LP7_over_all_other_arms', 'same_cut_projection_K7_over_K3'):
            comparisons[family] = [dict(
                numerator=n, denominator=d,
                service_ratio=ratio(arms[n]['service_s'], arms[d]['service_s']),
                service_saving_fraction=1 - ratio(arms[n]['service_s'], arms[d]['service_s']),
                target_verify_ratio=ratio(arms[n]['target_verify_s'], arms[d]['target_verify_s']),
                target_rows_ratio=ratio(arms[n]['target_rows'], arms[d]['target_rows']),
                draft_rows_ratio=ratio(arms[n]['draft_rows'], arms[d]['draft_rows']),
                native_process_wall_ratio=ratio(arms[n]['native_process_wall_s'], arms[d]['native_process_wall_s']),
            ) for n, d in declared[family]]
        modes[mode] = dict(arms=arms, comparisons=comparisons)
    return dict(
        schema='heterospec.m2.descriptive-width-analysis.v1', modes=modes,
        inputs=dict(checked_sha256=commitment(panel / 'CHECKED.json')[1], plan_sha256=commitment(panel / 'PLAN.json')[1],
                    pre_timing_declaration_sha256=commitment(declaration)[1]),
        interpretation=[
            'Descriptive only: four exposed roots, two live rounds and one replay round; no intervals or population inference.',
            'Read frozen same-k/same-projection results before cross-k totals; all new candidates use reserve8.',
            'Target replay excludes native drafting; common tape production costs are separate in the cost ledger.',
            'Proposals not accepted includes unconsumed work near cap/EOG; it is not a kernel-time estimate.',
            'Process clocks include startup/hash/load/primers/logging and warm file caches; categories overlap and must not be added.',
            'Serialized job bytes include configuration and replay tape; this is not network traffic or TTFT.',
            'Raw job byte lengths are host artifacts; public sanitized job lengths can differ after redaction.',
        ], new_native_jobs=0, model_forwards=0,
    )


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--text-index', type=Path, help='Public TEXT_INDEX for original-byte commitments after sanitization')
    args = p.parse_args()
    result = analyze(args.work, args.text_index)
    with args.out.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
