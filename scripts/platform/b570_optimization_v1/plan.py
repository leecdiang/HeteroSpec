"""CPU-only guards/planner. Never imports a model runtime or starts a GPU worker."""
import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / 'docs/experiments/b570_optimization_20261011'
POLICY = json.loads((DOC / 'POLICY.json').read_text(encoding='utf-8'))


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def bind_evidence(items, root):
    if not items:
        raise ValueError('No evidence files; boolean assertions are insufficient')
    roles = set()
    for x in items:
        p = (Path(root) / x['path']).resolve()
        if not p.is_relative_to(Path(root).resolve()):
            raise ValueError('Evidence path outside receipt directory')
        if p.stat().st_size != x['bytes'] or sha(p) != x['sha256']:
            raise ValueError('Evidence bytes/hash mismatch: ' + x['path'])
        roles.add(x['role'])
    return roles


def assets_check(manifest):
    pins = read(DOC / 'ASSETS.json')['models']
    rows = []
    for key, path in manifest.items():
        pin = pins[key]
        p = Path(path)
        ok = p.stat().st_size == pin['bytes'] and sha(p) == pin['sha256']
        rows.append({'asset': key, 'path': str(p.resolve()), 'full_file_verified': ok})
    return {'status': 'ASSET_BYTES_PASS' if rows and all(x['full_file_verified'] for x in rows)
            else 'BLOCKED_ASSET_BYTES', 'assets': rows, 'native_vocab_status': 'NOT_CHECKED'}


def host_check(facts, evidence_root):
    """Check a source-bound native receipt, not truth of an unreviewed implementation."""
    reasons = []
    try:
        roles = bind_evidence(facts.get('evidence', []), evidence_root)
        needed = {'native_source', 'binary', 'numeric_modules', 'load_log',
                  'vocab_dump', 'memory_trace', 'boundary_capture_reset_log'}
        if not needed <= roles:
            reasons.append('MISSING_NATIVE_EVIDENCE_ROLES')
    except (ValueError, OSError, KeyError) as e:
        reasons.append(str(e))
    if 'Intel' not in facts.get('device_name', '') or 'B570' not in facts.get('device_name', ''):
        reasons.append('WRONG_DEVICE')
    if facts.get('backend') != 'Vulkan' or not facts.get('driver'):
        reasons.append('UNKNOWN_BACKEND_OR_DRIVER')
    if facts.get('source_review_status') != 'ACTUAL_SOURCE_AND_LOGS_REVIEWED':
        reasons.append('SOURCE_REVIEW_REQUIRED')
    for flag in ('full_native_vocab_equal', 'runtime_eog_flags_equal',
                 'native_compatibility_guard_enabled', 'no_shared_memory_spill',
                 'raw_commit_boundary_pass', 'capture_equivalence_pass', 'reset_pass'):
        if facts.get(flag) is not True:
            reasons.append(flag.upper())
    if facts.get('context') != 1024 or facts.get('kv_type') != 'F16':
        reasons.append('WRONG_CONTEXT_OR_KV')
    if facts.get('zero_load_forward_count') != 0:
        reasons.append('HIDDEN_LOAD_FORWARD_OR_UNKNOWN')
    for role in ('target', 'draft'):
        x = facts.get(role, {})
        key = x.get('asset_key')
        pin = read(DOC / 'ASSETS.json')['models'].get(key, {})
        if (not pin or not key.startswith(facts.get('family', '') + '_' + role + '_')
                or x.get('sha256') != pin.get('sha256') or x.get('bytes') != pin.get('bytes')
                or x.get('full_file_verified') is not True):
            reasons.append(role.upper() + '_ASSET_UNVERIFIED')
        if role == 'target' and pin.get('quantization') != 'Q8_0':
            reasons.append('TARGET_PRECISION_CHANGED')
        if (not isinstance(x.get('total_layers'), int) or x['total_layers'] <= 0
                or x.get('gpu_layers') != x['total_layers'] or x.get('kv_gpu') is not True):
            reasons.append(role.upper() + '_PARTIAL_OFFLOAD_OR_UNKNOWN')
    samples = facts.get('memory_samples', [])
    if not {'LOADED', 'ENGINEERING_PEAK'} <= {s.get('point') for s in samples}:
        reasons.append('MISSING_LOADED_OR_PEAK_SAMPLE')
    for s in samples:
        if (s.get('scope') != 'OWNED_MODEL_PROCESS' or not isinstance(facts.get('worker_pid'), int)
                or facts['worker_pid'] <= 0 or s.get('pid') != facts['worker_pid']
                or s.get('device_name') != facts.get('device_name') or not s.get('timestamp_utc')):
            reasons.append('MEMORY_PROBE_NOT_RESIDENT_WORKER')
        heaps = s.get('heaps', [])
        if not heaps or any(h.get('dedicated_device_local') is not True for h in heaps):
            reasons.append('SHARED_OR_UNKNOWN_HEAP')
            continue
        try:
            free = sum(h['budget_bytes'] - h['usage_bytes'] for h in heaps)
            if any(h['usage_bytes'] < 0 or h['budget_bytes'] < h['usage_bytes'] for h in heaps):
                raise ValueError('invalid heap')
            if free < POLICY['dedicated_headroom_min_bytes']:
                reasons.append('INSUFFICIENT_PEAK_HEADROOM')
        except (KeyError, TypeError, ValueError):
            reasons.append('UNKNOWN_MEMORY_BUDGET')
    return {'status': 'NATIVE_RECEIPT_CHECK_PASS_PENDING_INDEPENDENT_REVIEW' if not reasons
            else 'BLOCKED_OR_UNKNOWN', 'reasons': sorted(set(reasons)),
            'claim': 'No speedup certification; receipt provenance must be independently reviewed'}


def machine_plan():
    cs = [{'candidate_id': f'{q}_{m}_k{k}', 'draft_quantization': q, 'mode': m, 'k_max': k}
          for q in POLICY['draft_quantizations'] for m in POLICY['candidate_modes']
          for k in POLICY['candidate_k_max']]
    engineering = 3 * (12 * 2 + 1) + 12 * (12 * 2 + 1) + 2 * (12 * 2 + 1) + 56 + 4
    assert engineering == POLICY['planned_engineering_max'] == 485
    assert len(cs) == POLICY['candidate_limit_per_family'] == 12
    assert 24 * 4 * 2 * 4 == POLICY['formal_requests_per_family'] == 768
    assert 2 * (640 + 768 + 32) == POLICY['total_request_hard_cap_two_families']
    return {'status': 'STATIC_PLAN_ONLY', 'candidates': cs, 'planned_engineering_max': engineering,
            'engineering_hard_cap': 640, 'formal_with_warmups': 800,
            'forward_calls_by_this_tool': 0, 'policy_sha256': sha(DOC / 'POLICY.json')}


def signature(r):
    ids, flags = r['committed_ids'], r['runtime_eog_flags']
    if (not ids or not all(type(i) is int and i >= 0 for i in ids)
            or len(ids) != len(flags) or not all(type(x) is bool for x in flags)
            or len(ids) > r['cap'] or r['cap'] != 128 or r['length'] != len(ids)
            or r['terminal_id'] != ids[-1] or not r['prompt_ids_sha256']):
        raise ValueError('INVALID_RAW_COMMIT_CONTRACT')
    if any(flags[:-1]):
        raise ValueError('RAW_EOG_SUFFIX_NOT_ALLOWED')
    if r['stop_reason'] == 'EOG':
        if not flags[-1]:
            raise ValueError('EOG_FLAG_MISSING')
    elif r['stop_reason'] == 'CAP':
        if any(flags) or len(ids) != 128:
            raise ValueError('CAP_CONTRACT_MISMATCH')
    else:
        raise ValueError('UNKNOWN_STOP_REASON')
    t = r['whole_request_seconds']
    if r['status'] != 'COMPLETE' or type(t) not in (int, float) or not math.isfinite(t) or t <= 0:
        raise ValueError('INCOMPLETE_OR_INVALID_TIMER')
    return (tuple(ids), len(ids), ids[-1], r['stop_reason'], tuple(flags), r['prompt_ids_sha256'])


def matrix(records, tasks, arms, sessions, rounds):
    expected = {(s, t, a, n) for s in sessions for t in tasks for a in arms for n in rounds}
    got = {}
    for r in records:
        key = (r['session'], r['task_id'], r['arm'], r['round'])
        if key not in expected or key in got:
            raise ValueError('UNEXPECTED_OR_DUPLICATE_SLOT')
        signature(r)
        got[key] = r
    if set(got) != expected:
        raise ValueError('INCOMPLETE_PAID_MATRIX')
    for t in tasks:
        sigs = {signature(got[s, t, a, n]) for s in sessions for a in arms for n in rounds}
        if len(sigs) != 1:
            raise ValueError('UNSTABLE_OR_DIVERGENT_RAW_OUTPUT: ' + t)
    return got


def ratios(got, tasks, baseline, candidate, sessions, rounds):
    out = []
    for s in sessions:
        per_task = {t: statistics.median(got[s, t, baseline, n]['whole_request_seconds'] for n in rounds)
                    / statistics.median(got[s, t, candidate, n]['whole_request_seconds'] for n in rounds)
                    for t in tasks}
        out.append({'session': s, 'gm': math.exp(statistics.mean(math.log(v) for v in per_task.values())),
                    'per_task_ratio': per_task, 'regression_tasks': [t for t, v in per_task.items() if v < 1]})
    return out


def select(data):
    tasks = data['discovery_tasks']
    if len(set(tasks)) != 12 or any(not t.startswith(('MBPP/', 'GSM8K/')) for t in tasks):
        raise ValueError('WRONG_DISCOVERY_PANEL')
    if sum(t.startswith('MBPP/') for t in tasks) != 6:
        raise ValueError('UNBALANCED_DISCOVERY_PANEL')
    ordinary = ['R_32', 'R_128', 'R_512']
    # Stock must pass. A failed/unsupported optional UB stays visible, not eligible.
    stock = [r for r in data['records'] if r['arm'] == 'R_128']
    matrix(stock, tasks, ['R_128'], [0, 1], [0])
    cost, baseline_observations = {}, []
    for arm in ordinary:
        try:
            records = [r for r in data['records'] if r['arm'] in {arm, 'R_128'}]
            bg = matrix(records, tasks, list(dict.fromkeys(['R_128', arm])), [0, 1], [0])
            cost[arm] = statistics.mean(math.log(bg[s, t, arm, 0]['whole_request_seconds'])
                                       for s in (0, 1) for t in tasks)
            baseline_observations.append({'arm': arm, 'status': 'QUALIFIED'})
        except (ValueError, KeyError) as e:
            baseline_observations.append({'arm': arm, 'status': 'INELIGIBLE', 'reason': str(e)})
    fastest = min(cost, key=lambda a: (cost[a], int(a.split('_')[1])))
    allowed = {c['candidate_id']: c for c in machine_plan()['candidates']}
    candidates = data['candidates']
    if len(candidates) > 12 or len({c['candidate_id'] for c in candidates}) != len(candidates):
        raise ValueError('CANDIDATE_LIMIT_OR_DUPLICATION')
    observed = []
    eligible = []
    for c in candidates:
        cid = c['candidate_id']
        if cid not in allowed:
            raise ValueError('UNDECLARED_CANDIDATE')
        if c['matched_arm'] != 'M_' + allowed[cid]['mode']:
            raise ValueError('WRONG_MATCHED_TARGET_PATH')
        if type(c['peak_bytes']) is not int or c['peak_bytes'] < 0:
            raise ValueError('INVALID_PEAK_MEASUREMENT')
        row = {'candidate_id': cid, 'status': c['gate_status'], 'qualified_ratios': None}
        if c['gate_status'] == 'NATIVE_GATES_ADMITTED':
            arms = [fastest, 'R_128', c['matched_arm'], cid]
            arms = list(dict.fromkeys(arms))
            records = [r for r in data['records'] if r['arm'] in arms]
            try:
                got = matrix(records, tasks, arms, [0, 1], [0])
                rr = ratios(got, tasks, fastest, cid, [0, 1], [0])
                mr = ratios(got, tasks, c['matched_arm'], cid, [0, 1], [0])
                row.update(status='DISCOVERY_COMPLETE', qualified_ratios={'ordinary': rr, 'matched': mr})
                if all(x['gm'] > 1.05 for x in rr) and all(x['gm'] > 1 for x in mr):
                    score = min(x['gm'] for x in rr)
                    eligible.append((-score, allowed[cid]['k_max'], c['peak_bytes'], cid))
            except (ValueError, KeyError) as e:
                row.update(status='INCOMPLETE_OR_DIVERGENT', reason=str(e))
        observed.append(row)
    winner = min(eligible)[-1] if eligible else None
    return {'status': 'SELECTED_FOR_FRESH_CONFIRMATION' if winner else 'FEASIBLE_NO_PROMISING_GAIN',
            'candidate_id': winner, 'ordinary_arm': fastest, 'ordinary_ub': int(fastest.split('_')[1]),
            'candidate': allowed.get(winner), 'discovery_tasks': tasks, 'observations': observed,
            'baseline_observations': baseline_observations,
            'policy_sha256': sha(DOC / 'POLICY.json'), 'qualified_formal_ratio': None}


def confirm(data, selection):
    tasks = data['confirmation_tasks']
    if selection['status'] != 'SELECTED_FOR_FRESH_CONFIRMATION':
        raise ValueError('NO_FROZEN_PROMISING_SELECTION')
    if selection['policy_sha256'] != sha(DOC / 'POLICY.json'):
        raise ValueError('SELECTION_POLICY_CHANGED')
    if data['candidate_id'] != selection['candidate_id'] or data['ordinary_ub'] != selection['ordinary_ub']:
        raise ValueError('CONFIGURATION_CHANGED_AFTER_SELECTION')
    if len(set(tasks)) != 24 or sum(t.startswith('MBPP/') for t in tasks) != 12 or sum(t.startswith('GSM8K/') for t in tasks) != 12:
        raise ValueError('WRONG_CONFIRMATION_PANEL')
    if data.get('history_audit_status') != 'ACTUAL_FULL_HISTORY_AUDITED':
        raise ValueError('HISTORY_AUDIT_REQUIRED')
    minimum_excluded = set(read(DOC / 'BASE_EXCLUSIONS.json')['excluded_ids'])
    excluded = (set(data['historical_and_rtx_reserved_ids']) | set(selection['discovery_tasks'])
                | minimum_excluded)
    if set(tasks) & excluded:
        raise ValueError('CONFIRMATION_EXPOSURE_OVERLAP')
    if data.get('f0b_remote_status') != 'ACTUAL_GIT_BLOBS_VERIFIED':
        raise ValueError('REMOTE_F0B_RECEIPT_REQUIRED')
    arms = POLICY['confirmation_arms']
    got = matrix(data['records'], tasks, arms, [0, 1], range(4))
    comparisons = {}
    for baseline in arms[:-1]:
        rr = ratios(got, tasks, baseline, 'C_selected', [0, 1], range(4))
        domains = {d: ratios(got, [t for t in tasks if t.startswith(d + '/')], baseline,
                             'C_selected', [0, 1], range(4)) for d in ('MBPP', 'GSM8K')}
        comparisons[baseline + '/C_selected'] = {'sessions': rr, 'domains': domains,
            'gm': math.exp(statistics.mean(math.log(x['gm']) for x in rr))}
    ordinary = comparisons['R_prod/C_selected']
    matched = comparisons['M_match/C_selected']
    positive = (ordinary['gm'] >= 1.05 and all(x['gm'] > 1 for x in ordinary['sessions'])
                and all(x['gm'] > 1 for x in matched['sessions']))
    return {'status': 'POSITIVE_DESCRIPTIVE' if positive else 'NO_PRACTICAL_POSITIVE_RESULT',
            'comparisons': comparisons, 'formal_records': len(got), 'per_arm': 192,
            'date_ci': None, 'cross_date_status': 'UNTESTED',
            'limit': 'CPU arithmetic/contract gate only; independent native and provenance gates still required'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['plan', 'assets', 'host', 'select', 'confirm'])
    p.add_argument('--input', type=Path)
    p.add_argument('--selection', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    try:
        data = read(a.input) if a.input else None
        if a.command == 'plan':
            result = machine_plan()
        elif a.command == 'assets':
            result = assets_check(data)
        elif a.command == 'host':
            result = host_check(data, a.input.parent)
        else:
            # Native/provenance evidence must accompany discovery and confirmation matrices.
            roles = bind_evidence(data['evidence'], a.input.parent)
            if not {'native_gate_receipts', 'request_ledger', 'remote_freeze_receipt',
                    'asset_checks', 'history_audit', 'raw_records'} <= roles:
                raise ValueError('MISSING_STUDY_PROVENANCE_EVIDENCE_ROLES')
            if data.get('independent_native_review_status') != 'PASS':
                raise ValueError('INDEPENDENT_NATIVE_REVIEW_REQUIRED')
            result = select(data) if a.command == 'select' else confirm(data, read(a.selection))
            result['input_sha256'] = sha(a.input)
            if a.command == 'confirm':
                result['selection_sha256'] = sha(a.selection)
    except (ValueError, KeyError, OSError, TypeError) as e:
        result = {'status': 'BLOCKED_OR_UNQUALIFIED', 'qualified_ratio': None, 'reason': str(e)}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'status': result['status'], 'output': str(a.output.resolve()), 'model_calls': 0}))
    return 0 if result['status'] not in ('BLOCKED_OR_UNQUALIFIED', 'BLOCKED_ASSET_BYTES', 'BLOCKED_OR_UNKNOWN') else 2


if __name__ == '__main__':
    raise SystemExit(main())
