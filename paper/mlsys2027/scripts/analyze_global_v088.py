#!/usr/bin/env python3
"""Post-study finite-cohort descriptors; no change to frozen estimators."""
import csv, hashlib, io, json, statistics, zipfile
from pathlib import Path

CONDITIONS = ['B_TARGET_REFERENCE_UB1', 'B_BATCHED_K2_UB2', 'B_SERIALIZED_K2_UB1']

def quantile(xs, q):
    xs = sorted(xs)
    at = (len(xs)-1)*q
    lo = int(at)
    hi = min(lo+1, len(xs)-1)
    return xs[lo]+(xs[hi]-xs[lo])*(at-lo)

def compute(j):
    assert len(j['tasks']) == 19 and len(set(j['tasks'])) == 19
    assert len(j['B']) == 171 and len(j['A']) == 57
    rows, vectors = [], {c: [] for c in CONDITIONS}
    for task in j['tasks']:
        row = {'task_id': task}
        for c in CONDITIONS:
            rr = [r for r in j['B'] if r['task_id']==task and r['condition']==c]
            assert sorted(r['repetition'] for r in rr)==[1,2,3]
            times = [r['timer']['qpc_delta']/r['timer']['frequency'] for r in rr]
            assert all(t>0 for t in times)
            m = statistics.median(times)
            row[c] = m
            vectors[c].append(m)
        rows.append(row)
    distribution = {c: {'n_prompts': 19, 'min_s': min(v), 'q25_s': quantile(v,.25), 'median_s': statistics.median(v), 'q75_s': quantile(v,.75), 'max_s': max(v)} for c,v in vectors.items()}
    failed = {}
    for c in ['A_TARGET_ONLY_UB2', 'A_REFERENCE_UB1', 'A_H2_P_R', 'A_R_ONLY']:
        failures=[]
        for r in j['A']:
            own=r['conditions'][c]['ids'];live=r['conditions']['A_NATIVE_BATCHED_LIVE']['ids']
            if own!=live:
                first=next((i for i,(a,b) in enumerate(zip(own,live)) if a!=b),min(len(own),len(live)))
                failures.append({'task_id':r['task_id'],'repetition':r['repetition'],'first_index':first,'own_id':own[first] if first<len(own) else None,'live_id':live[first] if first<len(live) else None})
        failed[c]=failures
    assert {r['task_id'] for r in failed['A_TARGET_ONLY_UB2']}=={'HumanEval/15','HumanEval/25'}
    assert {r['task_id'] for r in failed['A_REFERENCE_UB1']}=={'HumanEval/15','HumanEval/18'}
    assert failed['A_H2_P_R']==failed['A_R_ONLY']==[]
    return {'analysis':'POST_STUDY_V088','units':'seconds; 19 prompt-condition medians per condition','distribution':distribution,'A_failures':failed,'frozen_B_report':j['reported_B'],'limits':'Selected exposure-conditioned cohort and observed medians; spread is not a CI. No new primary estimate or blocked speedup.'}, rows

def main():
    ROOT = Path(__file__).resolve().parents[3]
    P = ROOT / 'paper/mlsys2027'
    OUT = P / 'manuscript/output'
    E = P / 'evidence'
    source=OUT/'anonymous-evidence-index-v0.8.7.zip'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='36609ad6579775deeb7edccc70f89bd9a242346b7446cc28575703ee7a8e3a04'
    with zipfile.ZipFile(source) as z:
        raw=z.read('evidence/RTX_V4.json');j=json.loads(raw)
    result,rows=compute(j)
    result['source_member_sha256']=hashlib.sha256(raw).hexdigest()
    result['plan_sha256']=hashlib.sha256((P/'reviews/system_revision_v088/ANALYSIS_PLAN_V088.md').read_bytes()).hexdigest()
    (E/'GLOBAL_ANALYSIS_V088.json').write_text(json.dumps(result,indent=2)+'\n')
    with (E/'RTX_V4_PROMPT_MEDIANS_V088.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['task_id']+CONDITIONS);writer.writeheader();writer.writerows(rows)
    names={'B_TARGET_REFERENCE_UB1':'Target','B_BATCHED_K2_UB2':'Batched','B_SERIALIZED_K2_UB1':'Serialized'}
    table=r'''\begin{table}[t]
\caption{RTX V4 absolute prompt-median post-prefill latency (s): 19 medians per condition, each from three runs. Post-study spread, not uncertainty. Batched times are diagnostic; these distribution medians do not estimate the paired speedup.}
\label{tab:rtxv4absolute}
\centering
\begin{tabular}{@{}lrrrrr@{}}
\toprule
Condition & Min & Q25 & Median & Q75 & Max \\
\midrule
'''
    for c,d in result['distribution'].items():
        table+=names[c]+' & '+' & '.join(f"{d[k]:.3f}" for k in ['min_s','q25_s','median_s','q75_s','max_s'])+r' \\'+'\n'
    table+=r'''\bottomrule
\end{tabular}
\end{table}
'''
    (P/'manuscript/tables/rtx_v4_absolute_v088.tex').write_text(table)
    print(json.dumps({'status':'PASS','distribution':result['distribution'],'source_member_sha256':result['source_member_sha256']}))

if __name__=='__main__': main()
