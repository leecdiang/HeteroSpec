"""Offline planning and complete-panel summaries. Never launches a model.

Native execution is the qualified PR196 successor's responsibility. A plan or
synthetic test is not qualification. Units are roots/conversations, not repeats.
"""
from __future__ import annotations
import argparse, hashlib, json, math, random, re
from pathlib import Path


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def read(path):
    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result, f'duplicate JSON key {k}')
            result[k] = v
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False); f.write('\n')


def binding_check(binding):
    """Validate declarations and local identities, not scientific truth."""
    require(isinstance(binding.get('runtime_commit'),str) and re.fullmatch('[0-9a-f]{40}', binding['runtime_commit']), 'Bind actual Linux successor commit')
    require(binding.get('not_pr196_worktree') is True, 'Separate study worktree required')
    require(binding.get('authorization_id') and binding.get('gpu_uuid'), 'Actual allocation required')
    require(binding.get('pr196_quiet_coordination') is True, 'Coordinate shared-host interference')
    require(binding.get('reference_id') and binding.get('deployment_id'), 'Independent deployment/reference identity required')
    for role in ('runtime_evidence', 'reference_evidence', 'model_manifest'):
        item = binding[role]
        require(sha(item['path']) == item['sha256'], f'{role} changed')
    require(binding.get('numeric_qualification') == 'HOST_EVIDENCE_REQUIRED',
            'Binding must not self-certify native qualification')
    return True


def schedule(study, panel_name, roots):
    panel = study['panels'][panel_name]
    ids = [r['root'] for r in roots]
    require(len(ids) == panel['roots'] and len(set(ids)) == len(ids), 'Wrong/duplicate root cohort')
    require(all(isinstance(r, str) and r for r in ids), 'Root identifiers required')
    arms = panel['arms']; sessions = panel['sessions']
    require(len(arms) == len(set(arms)) and len(arms) >= 2 and sessions >= 2, 'Invalid factorial schedule')
    for a, b in panel['contrasts']:
        require(a in arms and b in arms and a != b, 'Contrast outside fixed arms')
    workers = []; slots = []
    for session in range(sessions):
        order = arms[session % len(arms):] + arms[:session % len(arms)]
        cohort = list(ids); random.Random(study['seed'] + session).shuffle(cohort)
        for arm in order:
            wid = f"{study['id']}-{panel_name}-s{session}-{arm}"
            workers.append(dict(worker_id=wid, session=session, arm=arm,
                                roots=cohort, primer_count=panel.get('primers', 2)))
            for root in cohort:
                slots.append(dict(root=root, session=session, arm=arm, worker_id=wid))
    return dict(schema='server-expansion.plan.v1', study=study['id'], panel=panel_name,
                roots=ids, arms=arms, sessions=sessions, workers=workers, slots=slots,
                contrasts=panel['contrasts'], interaction=panel.get('interaction'),
                seed=study['seed'], bootstrap_draws=10000,
                inference=panel.get('inference', 'conditional_root_bootstrap'),
                measurements=len(slots), primers=sum(w['primer_count'] for w in workers),
                reference_and_qualification_requests='SEPARATE_CHARGED',
                sample_scope=panel['scope'], metric=panel.get('metric', 'service_s'),
                order_design='Prospective cyclic worker rows; not claimed fully carryover-balanced',
                status='PLAN_ONLY_NOT_GPU_EXECUTION')


def quantile(values, p):
    v = sorted(values); x = (len(v)-1)*p; i = int(x); f = x-i
    return v[i] if i+1 == len(v) else v[i]*(1-f) + v[i+1]*f


def coverage(values, expected):
    require(type(expected) is int and expected >= 0, 'Expected count')
    require(len(values) <= expected, 'Too many cost records')
    known = [x for x in values if x is not None]
    require(all(type(x) in (int, float) and math.isfinite(x) and x >= 0 for x in known), 'Invalid cost')
    complete = len(values) == len(known) == expected
    return dict(total_s=sum(known) if complete else None, observed_sum_s=sum(known),
                present=len(values), measured=len(known), expected=expected,
                unknown_or_absent=expected-len(known))


def analyze(plan, records, draws=None):
    """Paired root bootstrap of session sums. Failed/missing slots forbid inference.

    `reference_id` must be constant within this deployment panel. Actual capture
    checks belong to the native adapter; booleans alone are not supporting proof.
    """
    expected = {(s['root'], s['session'], s['arm']) for s in plan['slots']}
    found = {}; references = set(); devices = {}
    metric = plan['metric']
    for r in records:
        key = (r['root'], r['session'], r['arm'])
        require(key in expected and key not in found, 'Unknown/duplicate native slot')
        require(r['status'] == 'COMPLETE' and r['qualified'] is True, 'No successful-subset analysis')
        require(r.get('evidence_path') and r.get('evidence_sha256'), 'Bind actual receipt, not a fabricated PASS flag')
        require(sha(r['evidence_path']) == r['evidence_sha256'], 'Native receipt changed')
        value = r.get(metric)
        require(type(value) in (int,float) and math.isfinite(value) and value > 0, 'Missing/invalid declared clock')
        require(r.get('reference_id') and r.get('gpu_uuid'), 'Missing R/device identity')
        references.add(r['reference_id'])
        block = (r['root'], r['session'])
        devices.setdefault(block, r['gpu_uuid'])
        require(devices[block] == r['gpu_uuid'], 'Compare all methods on the same target GPU within a block')
        found[key] = float(value)
    require(set(found) == expected and len(references) == 1, 'Incomplete or mixed-reference panel')
    roots = plan['roots']; arms = plan['arms']; n = len(roots)
    y = {a: [sum(found[(r,s,a)] for s in range(plan['sessions'])) for r in roots] for a in arms}
    inference = plan.get('inference', 'conditional_root_bootstrap')
    require(inference in ('conditional_root_bootstrap', 'descriptive'), 'Unknown inference mode')
    count = (draws or plan['bootstrap_draws']) if inference != 'descriptive' else 0
    require(type(count) is int and count >= 0, 'Draw count')
    rng = random.Random(plan['seed']); indices = [[rng.randrange(n) for _ in range(n)] for _ in range(count)]
    boot = {a: [sum(y[a][i] for i in ix) for ix in indices] for a in arms}
    family = len(plan['contrasts']) + bool(plan.get('interaction')); require(family > 0, 'No estimands')
    alpha = .05 / family; result = []
    for a,b in plan['contrasts']:
        ratios = [u/v for u,v in zip(y[a],y[b])]
        samples = [u/v for u,v in zip(boot[a],boot[b])]
        result.append(dict(numerator=a, denominator=b, total_ratio=sum(y[a])/sum(y[b]),
             interval=[quantile(samples,alpha/2),quantile(samples,1-alpha/2)] if count else None,
             root_ratios=ratios, equal_root_geometric=math.exp(sum(map(math.log,ratios))/n),
             session_ratios=[sum(found[r,s,a] for r in roots)/sum(found[r,s,b] for r in roots) for s in range(plan['sessions'])]))
    interaction = None
    if plan.get('interaction'):
        lp, wl4, wp, ll4 = plan['interaction']
        require(set((lp,wl4,wp,ll4)) <= set(arms), 'Interaction arm missing')
        logs=[math.log(y[lp][i]*y[wl4][i]/(y[wp][i]*y[ll4][i])) for i in range(n)]
        samples=[math.exp(sum(logs[i] for i in ix)/n) for ix in indices]
        interaction=dict(definition='geomean((L_P/W_P)/(L_L4/W_L4)) across roots',
            ratio=math.exp(sum(logs)/n),interval=[quantile(samples,alpha/2),quantile(samples,1-alpha/2)] if count else None)
    return dict(scope=plan['sample_scope'], metric=metric, root_count=n,
        adjusted_family_size=family if count else None, inference=inference, bootstrap_draws=count, seed=plan['seed'],
        conditional_on_observed_sessions=True, all_fixed_controls=result, interaction=interaction,
        totals={a:sum(y[a]) for a in arms}, no_historical_timing_pooling=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__); s=p.add_subparsers(dest='command',required=True)
    a=s.add_parser('plan'); a.add_argument('study');a.add_argument('panel');a.add_argument('roots');a.add_argument('out')
    a=s.add_parser('analyze');a.add_argument('plan');a.add_argument('records');a.add_argument('out')
    a=s.add_parser('bind');a.add_argument('binding')
    a=p.parse_args()
    if a.command=='plan':save(a.out,schedule(read(a.study),a.panel,read(a.roots)['roots']))
    elif a.command=='analyze':save(a.out,analyze(read(a.plan),read(a.records)['records']))
    else:binding_check(read(a.binding));print('Source/allocation declarations bound; native qualification not inferred')
