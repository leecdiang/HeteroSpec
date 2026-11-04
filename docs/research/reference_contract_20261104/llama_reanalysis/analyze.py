from pathlib import Path
import json, hashlib, zipfile, collections, statistics as st, math
ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
manifest = json.loads((ROOT / 'SOURCE_MANIFEST.json').read_text())
for name, pin in manifest['files'].items():
    if not (ROOT / name).stat().st_size == pin['bytes']:
        raise ValueError("Validation failed: (ROOT / name).stat().st_size == pin['bytes']")
    if not hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == pin['sha256']:
        raise ValueError("Validation failed: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == pin['sha256']")
cost = json.loads((ROOT / 'data/FINAL_COST.json').read_text())
meta = json.loads((ROOT / 'data/strata.json').read_text())
records = {}
for session in range(6):
    for x in json.loads((ROOT / f'data/session{session}.json').read_text()):
        if not (x['category'] == 'measured' and (not x['capture']) and (x['observer_mode'] == 'off') and (x['lifecycle'] == 'fresh') and (x['repair_prefill'] == 'native')):
            raise ValueError("Validation failed: x['category'] == 'measured' and (not x['capture']) and (x['observer_mode'] == 'off') and (x['lifecycle'] == 'fresh') and (x['repair_prefill'] == 'native')")
        if not x['worker_source_sha256'] == 'e6dca9e58f61dc2aae0bf43e8d90f2147067f9447a043e5e1b4b025adcee8a2a':
            raise ValueError("Validation failed: x['worker_source_sha256'] == 'e6dca9e58f61dc2aae0bf43e8d90f2147067f9447a043e5e1b4b025adcee8a2a'")
        key = (x['session'], x['input'], x['experiment_arm'])
        if not key not in records:
            raise ValueError('Validation failed: key not in records')
        records[key] = x
if not len(records) == 864:
    raise ValueError('Validation failed: len(records) == 864')
rows = []
for b in cost['blocks']:
    s, i = (b['session'], b['input'])
    for arm, t in b['service_seconds'].items():
        if not records[s, i, arm]['service_seconds'] == t:
            raise ValueError("Validation failed: records[s, i, arm]['service_seconds'] == t")
    for arm, marm in [('C_QB', 'M_QB'), ('C_PQ_A', 'M_PQ'), ('C_PQ_B', 'M_PQ')]:
        m, c = (records[s, i, marm], records[s, i, arm])
        if not (m['length'] == c['length'] and (m['stop_reason'] == c['stop_reason'])):
            raise ValueError("Validation failed: m['length'] == c['length'] and (m['stop_reason'] == c['stop_reason'])")
        M, C = (m['service_seconds'], c['service_seconds'])
        mp, cp = (m['target_phases']['PREFILL'], c['target_phases']['PREFILL'])
        dp = c['draft_phases']['PREFILL']
        o = m['target_phases']['ORDINARY']
        v = c['target_phases']['VERIFY']
        p = c['draft_phases']['PROPOSE']
        seed = c['draft_phases']['DRAFT_SYNC']
        n = c['cycles_count']
        L = c['length']
        accepted = c['accepted']
        proposed = c['proposed']
        mg = M - sum(m['target_phases'].values())
        cg = C - sum(c['target_phases'].values()) - sum(c['draft_phases'].values())
        B = o - v - p - seed
        F = dp + cp - mp
        H = cg - mg
        if not abs(C - M - (F - B + H)) < 1e-12:
            raise ValueError('Validation failed: abs(C - M - (F - B + H)) < 1e-12')
        if not (c['target_calls'] == n + 1 and c['draft_calls'] == 4 * n + 1 and (proposed == 3 * n) and (m['target_calls'] == L)):
            raise ValueError("Validation failed: c['target_calls'] == n + 1 and c['draft_calls'] == 4 * n + 1 and (proposed == 3 * n) and (m['target_calls'] == L)")
        rows.append(dict(session=s, input=i, input_id=c['input_id'], domain=meta[i]['domain'], stratum=meta[i]['stratum'], arm=arm, prompt_tokens=c['prompt_tokens'], L=L, stop_reason=c['stop_reason'], cycles=n, accepted=accepted, proposed=proposed, acceptance=accepted / proposed, output_per_cycle=(L - 1) / n, M=M, C=C, D=M / C, M_target_prefill=mp, C_target_prefill=cp, C_draft_prefill=dp, M_ordinary=o, C_verify=v, C_propose=p, C_seed=seed, decode_saving=B, full_nonprefill_saving=B - H, extra_prefill=F, host_gap_delta=H, setup_delta=c['setup_seconds'] - m['setup_seconds'], teardown_delta=c['teardown_seconds'] - m['teardown_seconds'], M_source=m['_source'], C_source=c['_source']))
groups = collections.defaultdict(list)
for r in rows:
    groups[r['arm'], r['domain'], r['stratum']].append(r)
summary = []
for (arm, domain, band), g in groups.items():
    summary.append(dict(arm=arm, domain=domain, band=band, n=len(g), D_gm=math.exp(st.mean((math.log(x['D']) for x in g))), losing=sum((x['C'] > x['M'] for x in g)), decode_negative=sum((x['decode_saving'] < 0 for x in g)), still_loss_without_draft_prefill=sum((x['C'] - x['C_draft_prefill'] > x['M'] for x in g)), **{k: st.mean((x[k] for x in g)) for k in ['prompt_tokens', 'L', 'acceptance', 'output_per_cycle', 'C_draft_prefill', 'M_target_prefill', 'C_target_prefill', 'M_ordinary', 'C_verify', 'C_propose', 'C_seed', 'decode_saving', 'full_nonprefill_saving', 'extra_prefill', 'host_gap_delta', 'setup_delta', 'teardown_delta']}))
session_budgets = []
for session in range(6):
    q = [x for x in rows if x['arm'] == 'C_QB' and x['session'] == session]
    M = sum((x['M'] for x in q))
    C = sum((x['C'] for x in q))
    P = sum((x['C_draft_prefill'] for x in q))
    session_budgets.append(dict(session=session, M_sum=M, C_sum=C, draft_prefill_sum=P, C_over_M_total=C / M, ideal_prefill_fraction_for_total_parity=(C - M) / P))
out = {'QB_session_budgets': session_budgets, 'records': len(records), 'pairs': len(rows), 'service_matches': 864, 'summary': summary, 'rows': rows}
(ROOT / 'mechanism.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(summary, indent=2))
