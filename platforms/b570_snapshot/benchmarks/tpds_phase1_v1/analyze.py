"""Frozen phase-one estimands; NumPy is needed only for interval computation.

Canonical records: slot_id, status=COMPLETE, qualified=true, service_s,
reference_id. Plan metadata, not record labels, determines grouping. Never use
this to turn a partial/failed confirmation into a qualified-subset speed claim.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
from design import FACTOR, BURST, require, seed_for, write_new


def complete(plan, records):
    expected = {r['slot_id']: r for r in plan}
    require(len(expected) == len(plan), 'Duplicate planned slots')
    actual = {}
    for r in records:
        key = r.get('slot_id')
        require(key in expected and key not in actual, 'Unknown or duplicate record slot')
        require(r.get('status') == 'COMPLETE' and r.get('qualified') is True, 'Failed/unqualified version; retain records, no complete-panel inference')
        require(r.get('window') == expected[key]['window'], 'Timing window differs from frozen plan')
        if expected[key]['window']=='append_after_valid_state':
            require(r.get('native_timing_field') in ('append_ms/1000','append_seconds'), 'Structural comparisons require append timing, not full service')
        t = r.get('service_s')
        require(type(t) in (int, float) and math.isfinite(t) and t > 0, 'Invalid complete timing')
        require(isinstance(r.get('reference_id'), str) and r['reference_id'], 'Missing numerical reference binding')
        actual[key] = r
    require(set(actual) == set(expected), 'Incomplete plan, including warmups')
    return [dict(expected[k], service_s=actual[k]['service_s'], reference_id=actual[k]['reference_id']) for k in expected]


def paired_summary(rows, arms, comparisons, seed, draws=10000, interaction=False):
    require(rows and draws > 0, 'Empty analysis')
    require(len({r['reference_id'] for r in rows}) == 1, 'Different references cannot be pooled')
    roots = sorted({r['root'] for r in rows}); sessions = sorted({r['session'] for r in rows})
    values = {}
    for r in rows:
        key = (r['root'], r['session'], r['arm'])
        require(key not in values and r['arm'] in arms, 'Duplicate or unknown paired cell')
        values[key] = r['service_s']
    require(len(values) == len(roots) * len(sessions) * len(arms), 'Unbalanced paired panel')
    x = np.array([[[values[(root, s, arm)] for arm in arms] for s in sessions] for root in roots])
    totals = x.sum(axis=1)
    idx = np.random.Generator(np.random.PCG64(seed)).integers(0, len(roots), size=(draws, len(roots)))
    boot = totals[idx].sum(axis=1)
    family_size = len(comparisons) + int(interaction)
    alpha = .05 / family_size
    result = {'independent_roots': len(roots), 'sessions': len(sessions), 'seed': seed, 'bootstrap_draws': draws,
              'family_size': family_size, 'interval_level': 1-alpha, 'roots': roots,
              'totals_s': dict(zip(arms, totals.sum(axis=0).tolist())), 'contrasts': []}
    for a, b in comparisons:
        i, j = arms.index(a), arms.index(b)
        rr = totals[:, i] / totals[:, j]
        result['contrasts'].append(dict(numerator=a, denominator=b,
            total_ratio=float(totals[:, i].sum()/totals[:, j].sum()),
            adjusted_interval=np.quantile(boot[:, i]/boot[:, j], [alpha/2, 1-alpha/2]).tolist(),
            absolute_total_difference_s=float(totals[:, i].sum()-totals[:, j].sum()),
            mean_request_difference_s=float((totals[:, i].sum()-totals[:, j].sum())/(len(roots)*len(sessions))),
            equal_root_geometric=float(np.exp(np.log(rr).mean())), per_root=rr.tolist(),
            per_session=(x[:, :, i].sum(axis=0)/x[:, :, j].sum(axis=0)).tolist(),
            adverse_roots=[roots[k] for k in range(len(roots)) if rr[k] > 1]))
    if interaction:
        require(tuple(arms) == FACTOR, 'Interaction requires explicit 2x2 ordering')
        z = np.log(totals[:, 3]/totals[:, 2])-np.log(totals[:, 1]/totals[:, 0])
        result['packing_by_cut_interaction'] = dict(log_interaction=float(z.mean()), ratio=float(np.exp(z.mean())),
            adjusted_interval=np.exp(np.quantile(z[idx].mean(axis=1), [alpha/2, 1-alpha/2])).tolist(),
            per_root_log=z.tolist(), interpretation='Below one: packing helps more under local cuts')
    return result


def analyze_natural(plan, records, draws=10000):
    data = complete(plan, records)
    require({r['stage'] for r in data} == {'R1_NATURAL'}, 'Wrong schedule')
    cmp = [('L_L4','W_L4'), ('L_P','W_P'), ('W_P','W_L4'), ('L_P','L_L4')]
    result = {}
    for family in ('Qwen', 'Smol'):
        rows = [r for r in data if r['family'] == family and r['kind'] == 'measurement']
        require(len({r['root'] for r in rows}) == 16 and len(rows) == 256, 'Expected 16 roots x four arms x four sessions')
        result[family] = paired_summary(rows, FACTOR, cmp, seed_for('factor', family), draws, True)
    return dict(scope='New R1 only; never pool historical timing', families=result)


def analyze_structural(plan, records):
    rows = complete(plan, records); result = []
    for cell in sorted({r['root'] for r in rows}):
        subset = [r for r in rows if r['root'] == cell and r['kind'] == 'measurement']
        require(len({r['reference_id'] for r in subset}) == 1, 'Mismatched state/reference within coordinate')
        arms = sorted({r['arm'] for r in subset})
        times = {a: [r['service_s'] for r in subset if r['arm'] == a] for a in arms}
        totals = {a: sum(v) for a,v in times.items()}
        result.append(dict(cell=cell, times_s=times, totals_s=totals,
            paired_total_ratios={f'{a}/{b}': totals[a]/totals[b] for i,a in enumerate(arms) for b in arms[i+1:]}))
    return dict(scope='Fixed known-token append diagnostics; no natural-population interval or global speed average', coordinates=result)


def analyze_burst(plan, records, draws=10000):
    expected = {w['worker_id']: w for w in plan}; seen=set(); rows=[]; windows=[]
    from baselines import baseline_set
    require(plan and all(w.get('protocol_version') == 'review-v2' for w in plan), 'Use v1 code for an already frozen v1 panel')
    coverage = plan[0]['baseline_coverage']
    require(coverage == baseline_set(coverage['review']), 'Baseline review identity mismatch')
    arms = tuple(coverage['arms']); controls = tuple(coverage['target_only_arms'])
    require(all(w.get('baseline_coverage') == coverage for w in plan), 'Mixed baseline freezes')
    require(len(expected) == len(plan) == 4*len(arms), 'Missing or duplicate persistent workers')
    require({(w['session'], w['arm']) for w in plan} == {(s,a) for s in range(4) for a in arms}, 'Invalid worker matrix')
    for record in records:
        key=record.get('worker_id'); require(key in expected and key not in seen, 'Unknown/duplicate worker')
        seen.add(key); worker=expected[key]
        require(record.get('status') == 'COMPLETE', 'Incomplete burst; retain history')
        require(record.get('provision_count') == 1 and record.get('process_count') == 1, 'Not one persistent worker')
        calls=record.get('requests', []); require(len(calls) == 18, 'Two primers plus sixteen timed requests required')
        refs=set()
        for wanted, actual in zip(worker['requests'], calls):
            require(actual.get('root') == wanted['root'] and actual.get('kind') == wanted['kind'], 'Burst order changed')
            require(actual.get('qualified') is True and actual.get('status') == 'COMPLETE', 'Unqualified request')
            t=actual.get('service_s'); require(type(t) in (int,float) and math.isfinite(t) and t>0, 'Invalid service')
            ref=actual.get('reference_id'); require(isinstance(ref,str) and ref, 'Missing reference'); refs.add(ref)
            if wanted['kind']=='measurement': rows.append(dict(root=wanted['root'],session=worker['session'],arm=worker['arm'],service_s=t,reference_id=ref))
        require(len(refs)==1, 'Inconsistent burst reference')
        # Actual host clocks are mandatory; no setup/N extrapolation.
        names=('launch_to_first_result_s','launch_to_first_test_result_s','test_burst_wall_s','worker_wall_s','model_setup_s','peak_device_bytes')
        for name in names:
            v=record.get(name); require(type(v) in (int,float) and math.isfinite(v) and v>=0, f'Missing actual {name}')
        require(record['launch_to_first_result_s']<=record['launch_to_first_test_result_s']<=record['worker_wall_s'], 'Inconsistent first-result clocks')
        require(record['test_burst_wall_s']<=record['worker_wall_s'], 'Inconsistent burst clock')
        windows.append(dict(worker_id=key, arm=worker['arm'], session=worker['session'], **{n:record[n] for n in names}))
    require(seen==set(expected), 'Missing workers')
    primary=paired_summary(rows,arms,[('L_D4',a) for a in controls],seed_for('burst-primary-v2'),draws)
    sensitivity=paired_summary(rows,arms,[('L_M_MATCHED','L_M_TARGET_ONLY')],seed_for('burst-sensitivity-v2'),draws)
    return dict(primary=primary, baseline_coverage=coverage, all_fixed_target_only_contrasts_reported=True,
                separately_labelled_residency_sensitivity=sensitivity, actual_host_windows=windows,
                note='Root-cluster intervals condition on these four shared worker sessions; worker overhead descriptive, not independent worker replicates per request. No post-hoc minimum-M test replaces the simultaneous fixed controls.')


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('task',choices=['natural','structural','burst'])
    p.add_argument('plan',type=Path);p.add_argument('records',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    fn={'natural':analyze_natural,'structural':analyze_structural,'burst':analyze_burst}[a.task]
    write_new(a.out,fn(json.loads(a.plan.read_text()),json.loads(a.records.read_text())))
if __name__=='__main__': main()
