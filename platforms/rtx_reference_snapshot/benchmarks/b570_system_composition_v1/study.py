"""Offline planner/admission/analyzer for a bounded B570 system-composition study.

No native executor, network access, model loading, or implicit GPU authorization.
Python 3.11+, standard library. The host adapter must implement NATIVE_CONTRACT.md.
"""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
from typing import Any

CALIBRATION_IDS = {'GSM8K/test/1248', 'GSM8K/test/831',
                   'GSM8K/test/1011', 'GSM8K/test/1249'}
ARMS = ('R', 'M128', 'M512', 'C128_MQ', 'C128_PQ', 'C128_QB',
        'C512_MQ', 'C512_PQ', 'C512_QB', 'C128_SERIAL')
BINS = ((1, 128), (129, 256), (257, 512))
LIMITS = {'model_request_starts': 1576, 'operator_starts': 48,
          'native_process_starts': 904, 'owned_seconds': 21600,
          'new_output_bytes': 8 * 1024**3}
SEED = 20261015


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def encoded(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'), allow_nan=False) + '\n').encode()


def digest(value: Any) -> str:
    return hashlib.sha256(encoded(value)).hexdigest()


def load(path: Path) -> Any:
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, 'duplicate JSON key: ' + key)
            out[key] = value
        return out
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique)


def write_new(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(encoded(value))


def recipe(arm: str) -> dict:
    require(arm in ARMS or arm == 'R_PORT', 'unknown arm')
    if arm in ('R', 'R_PORT'):
        return {'kind': 'legacy_reference', 'runtime': 'original' if arm == 'R' else 'new_reference_port',
                'reference_recipe': 'EXACT_PR92_R_STOCK_F0_REQUIRED', 'restore': False}
    producer = 'P128' if '128' in arm else 'P512'
    spec = arm.startswith('C')
    return {'kind': 'speculative' if spec else 'ordinary_matched',
            'producer': producer, 'prefill_layout': 'MQ', 'prefill_ub': 512,
            'consumer': arm.rsplit('_', 1)[1] if spec else 'MQ',
            'continuation_ub': 1 if arm.endswith('_SERIAL') else 4, 'output_capacity': 4,
            'draft_enabled': spec, 'maximum_k': 3 if spec else 0,
            'draft_recipe': 'EXACT_PR92_DRAFT_RECIPE_REQUIRED' if spec else None,
            'n_ctx': 1024, 'logical_batch': 512, 'threads': 10,
            'kv_dtype': 'F16', 'flash_attention': False, 'streams': 1,
            'restore': False, 'extra_numerical_verifier': False}


def chunks(n: int, width: int) -> list[int]:
    require(type(n) is int and 0 < n <= 512 and width in (128, 512), 'invalid prefill')
    return [min(width, n-i) for i in range(0, n, width)]


def check_task(task: dict) -> None:
    ids = task['prompt_ids']
    require(task['domain'] in ('MBPP', 'GSM8K'), 'unsupported domain')
    require(isinstance(ids, list) and 0 < len(ids) <= 512, 'prompt length outside initial domain')
    require(all(type(i) is int and 0 <= i < 128256 for i in ids), 'invalid pinned Llama IDs')
    require(task['prompt_sha256'] == digest(ids), 'prompt hash mismatch')
    require(isinstance(task.get('source'), str) and bool(task['source']), 'source provenance required')
    require(not any(k in task for k in ('answer', 'solution', 'reference_output', 'latency')), 'outcome-bearing input')


def select_holdout(pool: list[dict], history: dict, calibration: list[dict]) -> list[dict]:
    require(history.get('exposure_manifest_sha256') and history.get('scope'), 'document exposure audit')
    excluded_ids = set(history['task_ids']) | {t['id'] for t in calibration}
    excluded_hashes = set(history['prompt_hashes']) | {t['prompt_sha256'] for t in calibration}
    seen_ids, seen_hashes, eligible = set(), set(), []
    for task in pool:
        check_task(task)
        require(task['id'] not in seen_ids, 'duplicate pool task ID')
        seen_ids.add(task['id'])
        if task['id'] in excluded_ids or task['prompt_sha256'] in excluded_hashes:
            continue
        require(task['prompt_sha256'] not in seen_hashes, 'duplicate eligible token sequence')
        seen_hashes.add(task['prompt_sha256']); eligible.append(task)
    selected = []
    for domain in ('MBPP', 'GSM8K'):
        ordered = sorted((t for t in eligible if t['domain'] == domain),
                         key=lambda t: (len(t['prompt_ids']), digest([SEED,t['id'],t['prompt_sha256']])))
        require(len(ordered) >= 12, f'insufficient unexposed {domain} population; do not fabricate prompts')
        for group in range(3):
            cell = ordered[len(ordered)*group//3:len(ordered)*(group+1)//3]
            cell.sort(key=lambda t: digest([SEED,t['id'],t['prompt_sha256']]))
            require(len(cell) >= 4, 'length rank stratum too small')
            for item in cell[:4]:
                x = copy.deepcopy(item); x['length_stratum'] = ('SHORT','MEDIUM','LONG')[group]
                selected.append(x)
    require(len(selected) == 24, 'holdout count')
    return selected


def make_slot(stage: str, session: int, task: dict, arm: str, mode: str,
              role: str = 'measure', worker_id: str | None = None) -> dict:
    require(mode in ('counts', 'heavy'), 'observation mode')
    coordinate = [stage, session, task['id'], arm, mode, role]
    slot = digest(coordinate)[:24]
    r = recipe(arm)
    return {'id': slot, 'stage': stage, 'session': session, 'task': task['id'],
            'prompt_ids': task['prompt_ids'], 'prompt_sha256': task['prompt_sha256'],
            'domain': task['domain'], 'arm': arm, 'recipe': r, 'mode': mode,
            'role': role, 'worker_id': worker_id or slot,
            'cap': 128, 'prefill_schedule': chunks(len(task['prompt_ids']), 128 if r.get('producer') == 'P128' else 512)
            if arm not in ('R', 'R_PORT') else None}


def plan_study(calibration: list[dict], pool: list[dict], history: dict) -> dict:
    require(len(calibration) == 4 and {t['id'] for t in calibration} == CALIBRATION_IDS, 'fixed exposed calibration tasks required')
    for t in calibration:
        check_task(t)
    cal = sorted(calibration, key=lambda t: t['id'])
    held = select_holdout(pool, history, cal)
    rows = []
    for repeat in range(2):
        for t in cal:
            for arm in ('R', 'R_PORT'):
                rows.append(make_slot('bridge', repeat, t, arm, 'counts'))
    for repeat, mode in ((0, 'counts'), (1, 'counts'), (0, 'heavy')):
        for i, t in enumerate(cal):
            arms = list(ARMS); random.Random(SEED+i+repeat+100*(mode == 'heavy')).shuffle(arms)
            for arm in arms:
                rows.append(make_slot('pilot', repeat, t, arm, mode))
    warm = cal[0]
    for session in range(3):
        tasks = copy.deepcopy(held); random.Random(SEED+session).shuffle(tasks)
        for i, task in enumerate(tasks):
            arms = list(ARMS); random.Random(SEED+1000+session*100+i//2).shuffle(arms)
            if i % 2:
                arms.reverse()
            for arm in arms:
                worker = digest(['validation', session, task['id'], arm])[:24]
                w = make_slot('validation', session, warm, arm, 'counts', 'warmup', worker)
                w['id'] = digest(['warmup', worker])[:24]
                rows.extend((w, make_slot('validation', session, task, arm, 'counts', 'measure', worker)))
    operators = [{'id': digest(['operator', q, n, arm, repeat])[:24], 'q': q, 'key_extent': n,
                  'arm': arm, 'repeat': repeat, 'input_seed': SEED+q*1000+n,
                  'scope': 'synthetic_native_operator_smoke_not_model_mechanism'}
                 for q in (1, 2, 3, 4) for n in (128, 384)
                 for arm in ('MQ', 'PQ', 'QB') for repeat in range(2)]
    result = {'schema': 1, 'study': 'b570_system_composition_v1', 'calibration': cal,
              'holdout': held, 'length_stratification': 'WITHIN_DOMAIN_TOKEN_LENGTH_RANK_TERTILES_BEFORE_INFERENCE', 'history': history, 'requests': rows, 'operators': operators,
              'limits': LIMITS, 'policy': {'candidate': 'C128_QB', 'fallback': 'R',
              'rule': 'pilot-qualified C128_QB for registered static domain; otherwise stop before holdout'},
              'runtime_status': 'HOST_NATIVE_PORT_AND_EXECUTION_FREEZE_REQUIRED',
              'native_execution_started_here': False}
    validate_plan(result)
    return result


def validate_plan(plan: dict) -> None:
    rows = plan['requests']
    require(len(rows) == LIMITS['model_request_starts'] and len({r['id'] for r in rows}) == len(rows), 'request inventory')
    require(Counter(r['stage'] for r in rows) == {'bridge': 16, 'pilot': 120, 'validation': 1440}, 'stage budgets')
    require(len(plan['operators']) == 48 and len({r['id'] for r in plan['operators']}) == 48, 'operator inventory')
    require(len({r['worker_id'] for r in rows})+48 == LIMITS['native_process_starts'], 'process budget')
    require(sum(r['role'] == 'warmup' for r in rows) == 720, 'warmup accounting')
    for row in rows:
        require(row['recipe'] == recipe(row['arm']) and row['prompt_sha256'] == digest(row['prompt_ids']), 'recipe/input drift')
        if row['arm'] not in ('R', 'R_PORT'):
            expected = chunks(len(row['prompt_ids']), 128 if row['recipe']['producer'] == 'P128' else 512)
            require(row['prefill_schedule'] == expected and row['recipe']['prefill_layout'] == 'MQ', 'producer/consumer confounding')
    require(plan['limits'] == LIMITS, 'unapproved budget mutation')
    tasks = {t['id']: t for t in plan['calibration'] + plan['holdout']}
    require(len(tasks) == 28 and {t['id'] for t in plan['calibration']} == CALIBRATION_IDS,
            'task inventory')
    for task in tasks.values():
        check_task(task)
    coordinates = set()
    for row in rows:
        t = tasks[row['task']]
        require(row['prompt_ids'] == t['prompt_ids'] and row['domain'] == t['domain']
                and row['cap'] == 128, 'actual task/cap binding')
        coord = (row['stage'], row['session'], row['task'], row['arm'], row['mode'], row['role'], row['worker_id'])
        require(coord not in coordinates, 'duplicate logical coordinate'); coordinates.add(coord)
        if row['stage'] == 'bridge':
            require(row['task'] in CALIBRATION_IDS and row['session'] in (0,1)
                    and row['arm'] in ('R','R_PORT') and row['mode'] == 'counts'
                    and row['role'] == 'measure', 'bridge coordinate')
        elif row['stage'] == 'pilot':
            require(row['task'] in CALIBRATION_IDS and row['arm'] in ARMS
                    and (row['session'],row['mode']) in ((0,'counts'),(1,'counts'),(0,'heavy'))
                    and row['role'] == 'measure', 'pilot coordinate')
        else:
            require(row['session'] in (0,1,2) and row['arm'] in ARMS and row['mode'] == 'counts',
                    'validation coordinate')
            require((row['role'] == 'warmup' and row['task'] == plan['calibration'][0]['id'])
                    or (row['role'] == 'measure' and row['task'] not in CALIBRATION_IDS), 'warmup/holdout split')
        expected = make_slot(row['stage'],row['session'],t,row['arm'],row['mode'],row['role'],row['worker_id'])
        if row['role'] == 'warmup': expected['id'] = digest(['warmup',row['worker_id']])[:24]
        require(row == expected, 'slot canonical binding')
    workers = {}
    for row in rows: workers.setdefault(row['worker_id'], []).append(row)
    for group in workers.values():
        if group[0]['stage'] == 'validation':
            require(len(group) == 2 and [r['role'] for r in group] == ['warmup','measure']
                    and group[0]['arm'] == group[1]['arm'] and group[0]['session'] == group[1]['session'],
                    'worker must own one warmup and one measurement')
        else: require(len(group) == 1, 'fresh bridge/pilot worker')
    expected_ops = {(q,n,a,rr) for q in (1,2,3,4) for n in (128,384) for a in ('MQ','PQ','QB') for rr in (0,1)}
    require({(o['q'],o['key_extent'],o['arm'],o['repeat']) for o in plan['operators']} == expected_ops,
            'operator coordinates')


def native_request(slot: dict, runtime_fingerprint: str, plan_sha256: str) -> dict:
    require(all(len(h) == 64 and all(c in '0123456789abcdef' for c in h) for h in (runtime_fingerprint, plan_sha256)), 'full SHA256 fingerprints required')
    return {'op': 'SYSTEM_COMPOSITION_V1', 'slot': slot['id'], 'task': slot['task'],
            'prompt_ids': copy.deepcopy(slot['prompt_ids']), 'cap': slot['cap'],
            'recipe': copy.deepcopy(slot['recipe']), 'schedule': slot['prefill_schedule'],
            'observation_mode': slot['mode'], 'restore': None,
            'runtime_fingerprint': runtime_fingerprint, 'plan_sha256': plan_sha256}


def admit_request(actual: dict, slot: dict, runtime_fingerprint: str, plan_sha256: str) -> str:
    require(actual == native_request(slot, runtime_fingerprint, plan_sha256), 'actual request differs from admitted cell')
    return digest(actual)  # Host sends THIS object; no later registry lookup.


def endpoint(output: dict) -> tuple:
    ids, flags = output['ids'], output['eog']
    require(isinstance(ids, list) and 0 < len(ids) <= 128, 'output length')
    require(all(type(i) is int and 0 <= i < 128256 for i in ids), 'invalid output IDs')
    expected = [i in (128001, 128008, 128009) for i in ids]
    require(flags == expected and not any(flags[:-1]), 'EOG contract')
    require(output['length'] == len(ids) and output['terminal_id'] == ids[-1] and output['cap'] == 128, 'endpoint contract')
    require(output['stop_reason'] == ('EOG' if flags[-1] else 'CAP') and (flags[-1] or len(ids) == 128), 'stop contract')
    return tuple(ids), tuple(flags), output['stop_reason'], 128


def classify(record: dict, reference: dict) -> str:
    if record['status'] != 'COMPLETED':
        return 'EXECUTION_ERROR'
    return 'QUALIFIED' if endpoint(record['output']) == endpoint(reference['output']) else 'SCIENTIFIC_NONQUALIFIED'


def verify_pins(root: Path, pins: list[dict]) -> None:
    require(bool(pins), 'raw evidence pins missing')
    root = root.resolve()
    for pin in pins:
        p = (root/pin['path']).resolve()
        require(p.is_relative_to(root), 'raw path escape')
        require(p.stat().st_size == pin['bytes'], 'raw size differs')
        with p.open('rb') as f:
            require(hashlib.file_digest(f, 'sha256').hexdigest() == pin['sha256'], 'raw hash differs')



def verify_record_evidence(root: Path, record: dict, request: dict) -> None:
    """Read immutable actual wire/native result/controller timer/identity, not just pin labels.

    Host integration must emit this native summary schema; there is no arbitrary
    field-mapping loader that could quietly select a different endpoint or timer.
    """
    verify_pins(root, record['raw_pins'])
    pinned = {p['path'] for p in record['raw_pins']}
    paths = {k: record[k] for k in ('raw_request_path', 'raw_result_path',
                                   'raw_timer_path', 'raw_identity_path')}
    require(set(paths.values()) <= pinned and len(set(paths.values())) == 4,
            'four distinct evidence sources must be pinned')
    bodies = {k: load(root/v) for k, v in paths.items()}
    require(bodies['raw_request_path'] == request, 'wire request differs')
    native = bodies['raw_result_path']
    for key in ('slot', 'status', 'pid', 'worker_id', 'output', 'observation_mode',
                'natural_prefill', 'restore_used', 'actual_prefill_schedule', 'counts'):
        require(native[key] == record[key], 'native/export disagreement: ' + key)
    timer = bodies['raw_timer_path']
    require(timer['slot'] == record['slot'] and timer['pid'] == record['pid'], 'timer ownership')
    require(type(timer['start_ns']) is int and type(timer['end_ns']) is int
            and timer['end_ns'] > timer['start_ns'], 'timer endpoints')
    require(timer['scope'] == 'INCLUSIVE_NATURAL_REQUEST_WITH_SELECTION_AND_STATE_TRANSITION',
            'wrong timer scope')
    elapsed = (timer['end_ns'] - timer['start_ns']) / 1e6
    require(math.isclose(elapsed, record['request_ms'], rel_tol=1e-12, abs_tol=1e-9), 'timer/export mismatch')
    identity = bodies['raw_identity_path']
    require(identity['pid'] == record['pid'] and identity['slot'] == record['slot']
            and identity['runtime_fingerprint'] == request['runtime_fingerprint']
            and identity['status'] == 'PASS' and identity['load_forward_calls'] == 0
            and identity['pre_request_reset_passed'] is True,
            'actual identity/zero-forward receipt')
    require(identity['added_sync'] is record['added_sync']
            and identity['heavy_capture'] is record['heavy_capture'], 'observer identity')


def workload(record: dict) -> dict:
    c = record['counts']; hist = c['target_continuation_width_hist']
    require(all(str(int(k)) == k and 1 <= int(k) <= 4 and type(v) is int and v >= 0 for k, v in hist.items()), 'width histogram')
    graphs = sum(hist.values()); rows = sum(int(k)*v for k, v in hist.items())
    require(graphs == c['target_continuation_micrographs'] and rows == c['target_continuation_rows'], 'physical work accounting')
    out = len(record['output']['ids'])
    return {'physical_rows_per_micrograph': rows/graphs if graphs else None,
            'target_micrographs_per_output_token': graphs/out,
            'physical_multiquery_observed': any(int(k) > 1 and v > 0 for k, v in hist.items()),
            'scope': 'measured micrographs, NOT shader launches/occupancy/DRAM bandwidth',
            'hardware_residency': 'UNKNOWN_UNLESS_SEPARATELY_MEASURED'}


def analyze_validation(plan: dict, records: list[dict], root: Path,
                       runtime_fingerprint: str, verify_files: bool = True) -> dict:
    validate_plan(plan); slots = {r['id']: r for r in plan['requests'] if r['stage'] == 'validation'}
    indexed, invalid = {}, []
    plan_hash = digest(plan)
    for rec in records:
        require(rec['slot'] in slots and rec['slot'] not in indexed, 'unknown/duplicate record')
        s = slots[rec['slot']]; indexed[rec['slot']] = rec
        require(rec['request_sha256'] == digest(native_request(s, runtime_fingerprint, plan_hash)), 'wrong-cell actual request')
        if rec['status'] != 'COMPLETED':
            if verify_files:
                verify_pins(root, rec['raw_pins'])
                require(rec['raw_failure_path'] in {x['path'] for x in rec['raw_pins']}, 'failure receipt not pinned')
                failure = load(root/rec['raw_failure_path'])
                require(failure['slot'] == rec['slot'] and failure['status'] == rec['status'], 'failure/export mismatch')
            invalid.append(rec['slot']); continue
        if verify_files:
            verify_record_evidence(root, rec, native_request(s, runtime_fingerprint, plan_hash))
        endpoint(rec['output'])
        require(type(rec['pid']) is int and rec['pid'] > 0 and rec['worker_id'] == s['worker_id'], 'owned process binding missing')
        require(rec['runtime_verified'] is True and rec['observation_mode'] == 'counts'
                and rec['added_sync'] is False and rec['heavy_capture'] is False, 'runtime/observer not admitted')
        require(math.isfinite(rec['request_ms']) and rec['request_ms'] > 0, 'invalid inclusive latency')
        require(rec['natural_prefill'] is True and rec['restore_used'] is False, 'not a natural execution')
        if s['arm'] != 'R':
            require(rec['actual_prefill_schedule'] == s['prefill_schedule'], 'wrong producer schedule')
            workload(rec)
    missing = sorted(set(slots)-set(indexed))
    by_coord = {(s['session'], s['task'], s['arm']): indexed[s['id']]
                for s in slots.values() if s['role'] == 'measure' and s['id'] in indexed}
    refs_stable = True
    for t in plan['holdout']:
        rr = [by_coord.get((s, t['id'], 'R')) for s in range(3)]
        if any(r is None or r['status'] != 'COMPLETED' for r in rr):
            refs_stable = False
        elif len({endpoint(r['output']) for r in rr}) != 1:
            refs_stable = False
    complete = not missing and not invalid and refs_stable
    comparisons = []
    for arm in ARMS[1:]:
        mismatches, session_ratios = [], []
        for session in range(3):
            pairs = []
            for t in plan['holdout']:
                r, c = by_coord.get((session, t['id'], 'R')), by_coord.get((session, t['id'], arm))
                if r is None or c is None or r['status'] != 'COMPLETED' or c['status'] != 'COMPLETED':
                    continue
                if classify(c, r) != 'QUALIFIED':
                    mismatches.append([session, t['id']])
                pairs.append((r['request_ms'], c['request_ms']))
            if len(pairs) == 24 and complete and not mismatches:
                session_ratios.append(sum(a for a, _ in pairs)/sum(b for _, b in pairs))
        qualified = complete and not mismatches
        if qualified:
            session_ratios = [sum(by_coord[(s, t['id'], 'R')]['request_ms'] for t in plan['holdout']) /
                              sum(by_coord[(s, t['id'], arm)]['request_ms'] for t in plan['holdout']) for s in range(3)]
        comparisons.append({'arm': arm, 'qualified': qualified, 'mismatches': mismatches,
                            'session_total_request_ratios': session_ratios if qualified else None,
                            'speed_ratio': math.exp(statistics.fmean(map(math.log, session_ratios))) if qualified else None})
    direct = []
    qualified_arms = {'R'} | {r['arm'] for r in comparisons if r['qualified']}
    for numerator, denominator in (
            ('C128_PQ', 'C128_QB'), ('C512_PQ', 'C512_QB'),
            ('C128_SERIAL', 'C128_QB'), ('M128', 'C128_QB'),
            ('M512', 'C512_QB'), ('C512_MQ', 'C128_MQ'),
            ('C512_PQ', 'C128_PQ'), ('C512_QB', 'C128_QB')):
        ok = complete and {numerator, denominator} <= qualified_arms
        ratios = [sum(by_coord[(ss, t['id'], numerator)]['request_ms'] for t in plan['holdout']) /
                  sum(by_coord[(ss, t['id'], denominator)]['request_ms'] for t in plan['holdout'])
                  for ss in range(3)] if ok else None
        direct.append({'comparison': numerator+'/'+denominator, 'qualified': ok,
                       'session_total_request_ratios': ratios,
                       'speed_ratio': math.exp(statistics.fmean(map(math.log, ratios))) if ok else None})
    return {'status': 'COMPLETE_FINITE_PANEL' if complete else 'INCOMPLETE_OR_REFERENCE_UNSTABLE',
            'missing': missing, 'execution_errors': invalid, 'reference_stable': refs_stable,
            'comparisons': comparisons, 'direct_comparisons': direct, 'confidence_interval': None,
            'scope': '24 held-out task identities, 3 sessions, one fixed model/backend; no population guarantee',
            'cost_scope': 'inclusive natural requests; warmups excluded from time, never from budgets'}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('plan'); a.add_argument('--inputs', type=Path, required=True); a.add_argument('--output', type=Path, required=True)
    a = sub.add_parser('analyze'); a.add_argument('--plan', type=Path, required=True); a.add_argument('--records', type=Path, required=True)
    a.add_argument('--raw-root', type=Path, required=True); a.add_argument('--runtime-fingerprint', required=True); a.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.command == 'plan':
        data = load(args.inputs); result = plan_study(data['calibration'], data['pool'], data['history'])
    else:
        result = analyze_validation(load(args.plan), load(args.records), args.raw_root, args.runtime_fingerprint)
    write_new(args.output, result)


if __name__ == '__main__':
    main()
