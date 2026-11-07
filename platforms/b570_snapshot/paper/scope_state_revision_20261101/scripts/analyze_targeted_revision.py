#!/usr/bin/env python3
"""Reconstruct approved post-hoc contrasts from unchanged report-level inputs.
No native inference, network, raw-logit replay, fitting or uncertainty estimation.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('D_GS','D_PQ','D_QB','I_QB_vs_GS','C_QB_over_C_PQ',
          'M_QB_over_M_PQ','R_over_C_GS','R_over_C_PQ','R_over_C_QB')
DATES = ('2026-10-30','2026-10-31','2026-11-01')
SOURCE_HASHES = {'anc/final_20261101/rtx_session_logs.csv': '4d6d250c886b5e84a942dc543afaac76e657ac91dcfce5c6a5b0e891edb9d875', 'anc/final_20261101/DERIVED.json': '026954c9bc84720316a8cf369ca9ef0ba9b5ece555370ac146e0ae6857a3374e', 'anc/final_20261101/b570_MATRIX.csv': 'de73abff0826ec8e0ad3c76ae19e6e6d6f24759f2464380dd229ef064ee6b699', 'anc/final_20261101/b570_STATE_EFFECTS.csv': 'b578e7a0311484a06447f99836b02beabbb90c7e964512b0d28b5c4dcafd38ac'}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline='', encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def mean(values) -> float:
    values = list(values)
    if not values or any(not math.isfinite(v) for v in values):
        raise ValueError('finite nonempty values required')
    return math.fsum(values) / len(values)


def boolean(value: str) -> bool:
    if value not in ('True', 'False'):
        raise ValueError('expected explicit boolean')
    return value == 'True'


def independent_labels(matrix: list[list[int]]) -> list:
    """Enumerate independent producer/consumer labels for the observed 2x2 set."""
    return [(g, h) for g in itertools.product((0, 1), repeat=2)
            for h in itertools.product((0, 1), repeat=2)
            if all((g[i] & h[j]) == matrix[i][j] for i in range(2) for j in range(2))]


def reconstruct(root: Path = ROOT) -> dict:
    checks = []
    def ck(name: str, ok: bool) -> None:
        if not ok:
            raise ValueError('FAILED: ' + name)
        checks.append(name)
    for name, expected in SOURCE_HASHES.items():
        ck('Unchanged report input: ' + name,
           hashlib.sha256((root/name).read_bytes()).hexdigest() == expected)
    data = root/'anc/final_20261101'
    logs = read_csv(data/'rtx_session_logs.csv')
    original = json.loads((data/'DERIVED.json').read_text())
    ck('Twelve session rows', len(logs) == 12)
    result = {'status':'POST_HOC_REPORT_RECONSTRUCTION',
              'source_baseline':'28a44f6d5755ff718e23609d73666f31b14a386c',
              'new_model_executions':0, 'new_uncertainty_tests':0,
              'scope':'Common-panel algebra and finite matrix interpretation; not raw-request replay or online-policy validation.',
              'source_sha256':SOURCE_HASHES, 'rtx':{}, 'b570':{}}
    for fam in ('Qwen', 'SmolLM2'):
        rows = [r for r in logs if r['family'] == fam]
        ck(f'{fam}: all fixed date/session keys',
           {(r['date'],int(r['session'])) for r in rows} == {(d,s) for d in DATES for s in (0,1)} and len(rows)==6)
        daily = []
        for date in DATES:
            subset = [r for r in rows if r['date'] == date]
            logmean = {k:mean(float(r[k]) for r in subset) for k in FIELDS}
            ratios = {k:math.exp(v) for k,v in logmean.items()}
            daily.append({'date':date,'log_means':logmean,'ratios':ratios,
                          'scope_factor':ratios['D_PQ']/ratios['D_GS'],
                          'layout_draft_factor':ratios['D_QB']/ratios['D_PQ']})
        ratios = {k:math.exp(mean(d['log_means'][k] for d in daily)) for k in FIELDS}
        for key in FIELDS:
            ck(f'{fam}: reproduce registered {key}', math.isclose(ratios[key], original['rtx'][fam]['ratios'][key], rel_tol=2e-13, abs_tol=2e-13))
        scope = ratios['D_PQ']/ratios['D_GS']
        eta = ratios['D_QB']/ratios['D_PQ']
        ck(f'{fam}: interaction product', math.isclose(scope*eta,ratios['I_QB_vs_GS'],rel_tol=2e-13))
        ck(f'{fam}: independent eta identity', math.isclose(eta,ratios['M_QB_over_M_PQ']/ratios['C_QB_over_C_PQ'],rel_tol=2e-13))
        costs = {'R':1.0}
        for layout in ('GS','PQ','QB'):
            costs['C_'+layout] = 1/ratios['R_over_C_'+layout]
            costs['M_'+layout] = ratios['D_'+layout]*costs['C_'+layout]
            ck(f'{fam}/{layout}: normalization identity', math.isclose(costs['M_'+layout]/costs['C_'+layout],ratios['D_'+layout],rel_tol=2e-13))
        result['rtx'][fam] = {'ratios':ratios, 'scope_factor':scope,'layout_draft_factor':eta,
                             'draft_off_reduction_percent':100*(1-ratios['M_QB_over_M_PQ']),
                             'draft_on_reduction_percent':100*(1-ratios['C_QB_over_C_PQ']),
                             'relative_to_R':costs,'dates':daily}
    matrix = read_csv(data/'b570_MATRIX.csv')
    states = read_csv(data/'b570_STATE_EFFECTS.csv')
    ck('48 scientific rows and eight state comparisons',len(matrix)==48 and len(states)==8)
    q={(r['input_id'],r['producer'],r['consumer']):boolean(r['strict_reference_equal']) for r in matrix}
    inputs=list(dict.fromkeys(r['input_id'] for r in matrix))
    ck('Complete fixed matrix', len(q)==48 and set(q)=={(i,p,c) for i in inputs for p in ('P1','P4T') for c in ('C1','PQ','QB')})
    wrong=[]; witnesses=[]
    for inp in inputs:
        for producer in ('P1','P4T'):
            ck(f'{inp}/{producer}: local reference outcomes agree',q[inp,producer,'PQ']==q[inp,producer,'QB'])
            if not q[inp,producer,'PQ']:
                wrong.append({'input':inp,'producer':producer})
        sub=[[int(q[inp,p,c]) for c in ('C1','PQ')] for p in ('P1','P4T')]
        if not independent_labels(sub):
            witnesses.append({'input':inp,'matrix':sub})
    ck('Two exact independent-label counterexamples',len(witnesses)==2 and all(w['matrix']==[[1,0],[1,1]] for w in witnesses))
    ck('Four jointly divergent local pairs',len(wrong)==4)
    ck('39 strict-reference cells',sum(q.values())==39)
    for row in states:
        ck(row['input_id']+': original local vector/cycle comparisons',
           all(boolean(row[f'{p}_PQ_QB_{kind}_equal']) for p in ('P1','P4T') for kind in ('endpoint','cycles','vectors')))
    result['b570']={'cells':48,'strict_reference_matches':39,'local_pairs':16,
                    'jointly_divergent_pairs':wrong,'independent_label_counterexamples':witnesses,
                    'scope':'Eight fixed inputs, complete KV and initial-logit boundary, validated clean receiver; no population rate or general impossibility result.'}
    result['checks_passed']=len(checks)
    return result


def outputs(root: Path = ROOT) -> dict[str,str]:
    result=reconstruct(root)
    lines=[r'\begin{table}[htbp]\centering\small',
           r'\caption{Pooled factors from the unchanged three-date panel. Their product is the original $\Gamma$; no new uncertainty test is added.}\label{tab:scopefactors}',
           r'\setlength{\tabcolsep}{3pt}', r'\begin{tabular}{@{}lrrr@{}}\toprule',
           r'Family & $D_{\PQ}/D_{\GS}$ & $\eta=D_{\QB}/D_{\PQ}$ & $\Gamma$\\\midrule']
    norm=[r'\begin{table}[htbp]\centering\small',
          r'\caption{Common-panel geometric request-cost ratios normalized to $R=1$. Lower is cheaper. These are neither total batch times nor an evaluated online selection policy.}\label{tab:normalizedcosts}',
          r'\setlength{\tabcolsep}{3pt}',r'\begin{tabular}{@{}lrrrr@{}}\toprule',
          r'Family & $M_{\PQ}$ & $M_{\QB}$ & $C_{\PQ}$ & $C_{\QB}$\\\midrule']
    for fam,f in result['rtx'].items():
        label='Qwen3' if fam=='Qwen' else fam
        lines.append(f"{label} & {f['scope_factor']:.6f} & {f['layout_draft_factor']:.6f} & {f['ratios']['I_QB_vs_GS']:.6f}"+r'\\')
        norm.append(label+' & '+' & '.join(f"{f['relative_to_R'][k]:.6f}" for k in ('M_PQ','M_QB','C_PQ','C_QB'))+r'\\')
    lines.extend([r'\bottomrule\end{tabular}',r'\end{table}',''])
    norm.extend([r'\bottomrule\end{tabular}',r'\end{table}',''])
    return {'anc/targeted_20261101/DERIVED.json':json.dumps(result,indent=2,ensure_ascii=False)+'\n',
            'tables/scope_factors.tex':'\n'.join(lines),'tables/normalized_costs.tex':'\n'.join(norm)}


def verify(check, root: Path = ROOT) -> dict:
    result=reconstruct(root)
    check('Targeted: immutable report inputs and post-hoc identities',result['checks_passed']>0)
    for name,text in outputs(root).items():
        check('Targeted generated artifact: '+name,(root/name).read_text()==text)
    primary=(root/'sections/05_evaluation.tex').read_text()
    for number in ('1.344110','1.059343','1.176962','0.999494','6.579','6.532'):
        check('Targeted printed factor/value: '+number,number in primary)
    return {'status':result['status'],'internal_checks':result['checks_passed'],
            'new_model_executions':0,'new_uncertainty_tests':0}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    for name,text in outputs().items():
        path=ROOT/name
        if args.check:
            if not path.is_file() or path.read_text()!=text:
                raise SystemExit('Generated artifact differs: '+name)
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(text,encoding='utf-8')
    print(json.dumps({'status':'PASS','mode':'check' if args.check else 'generate',
                      'internal_checks':reconstruct()['checks_passed'],'new_model_executions':0}))
