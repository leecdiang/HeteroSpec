#!/usr/bin/env python3
"""Offline reconstruction of final reported contrasts and exact B570 CSVs.
RTX input: 12 session-level log vectors transcribed from fixed ANALYSIS.json.
This is NOT raw-request or raw-logit replay. No native execution/network calls.
"""
from __future__ import annotations
import csv, hashlib, json, math, statistics, argparse
from collections import defaultdict, Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'anc/final_20261101'
DATES = ('2026-10-30','2026-10-31','2026-11-01')
FIELDS = ('D_GS','D_PQ','D_QB','I_QB_vs_GS','C_QB_over_C_PQ','M_QB_over_M_PQ','R_over_C_GS','R_over_C_PQ','R_over_C_QB')
T2 = 6.205346816570706
BLOBS = {'b570_MATRIX.csv':'e67b215eb5fe992d6de06ef37dd984f27505d5f2',
         'b570_STATE_EFFECTS.csv':'c59910d9888cd01d60e91ce40f6a16a82f88e264'}

def blob(b:bytes)->str:
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def mean(xs):
    xs=list(xs)
    if not xs or any(not math.isfinite(v) for v in xs): raise ValueError('finite, nonempty sample required')
    return math.fsum(xs)/len(xs)
def read_csv(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def close(a,b):return math.isclose(a,b,rel_tol=2e-13,abs_tol=2e-13)

def reconstruct(root:Path=ROOT):
    data=root/'anc/final_20261101'; checks=[]
    def ck(name,condition):
        if not condition: raise ValueError('FAILED: '+name)
        checks.append(name)
    for f,sha in BLOBS.items():ck('Exact B570 Git blob '+f,blob((data/f).read_bytes())==sha)
    ck('RTX reported-session projection SHA256',hashlib.sha256((data/'rtx_session_logs.csv').read_bytes()).hexdigest()=='4d6d250c886b5e84a942dc543afaac76e657ac91dcfce5c6a5b0e891edb9d875')
    rows=read_csv(data/'rtx_session_logs.csv')
    ck('12 unique family/date/session projections',len(rows)==12 and len({(r['family'],r['date'],r['session']) for r in rows})==12)
    rtx={}
    for fam in ('Qwen','SmolLM2'):
        rs=[r for r in rows if r['family']==fam]
        ck(f'{fam}: six sessions and exact date grid',len(rs)==6 and {(r['date'],r['session']) for r in rs}=={(d,s) for d in DATES for s in ('0','1')})
        for r in rs:
            for k in FIELDS:
                r[k]=float(r[k]);ck(f'{fam}/{r["date"]}/{r["session"]}/{k} finite',math.isfinite(r[k]))
            ck(f'{fam}/{r["date"]}/{r["session"]}: scope interaction identity',close(r['I_QB_vs_GS'],r['D_QB']-r['D_GS']))
            ck(f'{fam}/{r["date"]}/{r["session"]}: local interaction identity',close(r['D_QB']-r['D_PQ'],r['M_QB_over_M_PQ']-r['C_QB_over_C_PQ']))
            ck(f'{fam}/{r["date"]}/{r["session"]}: strict-reference identity',close(r['R_over_C_QB']-r['R_over_C_PQ'],-r['C_QB_over_C_PQ']))
        ds=[dict(date=d,logs={k:mean(r[k] for r in rs if r['date']==d) for k in FIELDS}) for d in DATES]
        logs={k:mean(d['logs'][k] for d in ds) for k in FIELDS}
        ratios={k:math.exp(v) for k,v in logs.items()}
        for d in ds:d['ratios']={k:math.exp(v) for k,v in d['logs'].items()}
        se=statistics.stdev(d['logs']['I_QB_vs_GS'] for d in ds)/math.sqrt(3)
        ci=[math.exp(logs['I_QB_vs_GS']+z*T2*se) for z in (-1,1)]
        ck(f'{fam}: dates all favor scope interaction',all(d['logs']['I_QB_vs_GS']>0 for d in ds))
        ck(f'{fam}: no collapse of strict-R and draft baselines',not close(ratios['D_QB'],ratios['R_over_C_QB']))
        rtx[fam]={'ratios':ratios,'mean_logs':logs,'dates':ds,'sessions':rs,
                  'weak_date_sensitivity_interval':ci,'weak_date_sensitivity_df':2,
                  'scope':'reported-session reconstruction; fixed exposed panel, one host, three dates',
                  'observed_work_matched':fam=='Qwen',
                  'input_session_reversals_reported_not_recomputed':5 if fam=='Qwen' else 27,
                  'draft_latency_change_percent':100*(1/ratios['D_QB']-1)}
    expected={'Qwen':[.8346516609752586,1.121863272924304,1.1884384281215608,1.4238735555056776],
              'SmolLM2':[.6842051770288614,.8052837411644185,.8048766563979831,1.1763673871822098]}
    for fam,vals in expected.items():
        for k,v in zip(('D_GS','D_PQ','D_QB','I_QB_vs_GS'),vals):ck(f'{fam}/{k}: pinned reported aggregate',close(rtx[fam]['ratios'][k],v))
    ck('Qwen draft crossover on all dates',all(d['ratios']['D_GS']<1<d['ratios']['D_QB'] for d in rtx['Qwen']['dates']))
    ck('Smol no profitable scope on any date',all(d['ratios'][k]<1 for d in rtx['SmolLM2']['dates'] for k in ('D_GS','D_PQ','D_QB')))
    mat=read_csv(data/'b570_MATRIX.csv'); state=read_csv(data/'b570_STATE_EFFECTS.csv')
    ck('B570 48 complete coordinates',len(mat)==48 and len({(r['input_index'],r['producer'],r['consumer']) for r in mat})==48)
    ck('B570 eight inputs',len(state)==8 and {r['input_index'] for r in mat}=={str(i) for i in range(8)})
    counts={p:{c:sum(r['producer']==p and r['consumer']==c and r['strict_reference_equal']=='True' for r in mat) for c in ('C1','PQ','QB')} for p in ('P1','P4T')}
    ck('B570 strict-R counts, not evidence-qualified counts',counts=={'P1':{'C1':8,'PQ':5,'QB':5},'P4T':{'C1':7,'PQ':7,'QB':7}})
    ck('B570 39/48 match strict R',sum(v for d in counts.values() for v in d.values())==39)
    ck('All 48 evidence contracts qualified',all(r['contract_qualified']=='True' for r in mat))
    ck('All matrix cells excluded from performance inference',all(r['performance_eligible']=='False' for r in mat))
    idx={(r['input_index'],r['producer'],r['consumer']):r for r in mat}
    switches=[]
    for s in state:
        i=s['input_index']
        ck(f'{i}: both numerical state components change',s['kv_bytes_equal']=='False' and s['initial_logits_bytes_equal']=='False')
        for p in ('P1','P4T'):
            ck(f'{i}/{p}: local endpoints, cycles and vectors match',all(s[f'{p}_PQ_QB_{x}_equal']=='True' for x in ('endpoint','cycles','vectors')))
            for c in ('C1','PQ','QB'):
                ck(f'{i}/{p}/{c}: matrix/state agreement',idx[i,p,c]['strict_reference_equal']==s[f'{p}_{c}_strict_reference_equal'])
        if all(s[f'{p}_C1_strict_reference_equal']=='True' for p in ('P1','P4T')) and s['P1_PQ_strict_reference_equal']=='False' and s['P4T_PQ_strict_reference_equal']=='True':switches.append(s['input_id'])
    ck('Exact two fixed-reference producer switches',switches==['MATH500/test/prealgebra/1865.json','MATH500/test/prealgebra/1804.json'])
    ck('Third counterexample kept distinct',state[2]['natural_endpoints_equal']=='False' and state[2]['P4T_C1_strict_reference_equal']=='False')
    ck('Five state changes without endpoint change',sum(s['all_six_endpoints_match_R']=='True' for s in state)==5)
    # Independent reconstruction of the P0 exploratory E2 contrasts, from original request times.
    e2=read_csv(root/'anc/rtx104/E2_REQUEST_LATENCIES.csv'); groups=defaultdict(dict)
    for r in e2:
        if r['warmup'].lower()=='true' or r['arm']=='R':continue
        key=(r['family'],r['session'],r['slot'].split('|')[-1]);ck('E2 unique local arm '+str(key)+'/'+r['arm'],r['arm'] not in groups[key])
        groups[key][r['arm']]=float(r['latency_ms'])
    ck('E2 216 exact quartets',len(groups)==216 and all(set(g)=={'M_PQ','M_QB','C_PQ','C_QB'} for g in groups.values()))
    e2out={}
    for fam in sorted({k[0] for k in groups}):
        session=[]
        for s in sorted({k[1] for k in groups if k[0]==fam}):
            gs=[v for (f,ss,_),v in groups.items() if f==fam and ss==s]
            ck(f'E2/{fam}/{s}: twelve input quartets',len(gs)==12)
            session.append({l:mean(math.log(g['M_'+l]/g['C_'+l]) for g in gs) for l in ('PQ','QB')})
        e2out[fam]={l:{'ratio':math.exp(mean(s[l] for s in session)),
                         't5_pointwise_interval':[math.exp(mean(s[l] for s in session)+z*2.570581835636314*statistics.stdev(s[l] for s in session)/math.sqrt(6)) for z in (-1,1)]} for l in ('PQ','QB')}
    return {'status':'PASS','checks_passed':len(checks),'checks':checks,'rtx':rtx,
            'b570':{'counts':counts,'matrix':mat,'states':state,'fixed_reference_switches':switches},
            'e2_retrospective':e2out,'new_native_executions':0,
            'raw_archive_reexecution':False}

def outputs(root:Path=ROOT):
    a=reconstruct(root); files={}
    # Exact scope values and all date/session rows.
    lines=[r'\begin{table*}[t]\centering\small',r'\caption{Three-date scope--draft results. $D_L=T_{M_L}/T_{C_L}>1$ favors drafting; $\Gamma=D_{\QB}/D_{\GS}$. Inputs, sessions within date and dates receive equal log weights.}\label{tab:scopefinal}',r'\begin{tabular}{@{}llrrrr@{}}\toprule',r'Family & Date / pooled & $D_{\GS}$ & $D_{\PQ}$ & $D_{\QB}$ & $\Gamma$\\\midrule']
    for fam, f in a['rtx'].items():
        name='Qwen3' if fam=='Qwen' else fam
        for d in f['dates']:
            v=d['ratios'];lines.append(name+' & '+d['date']+' & '+' & '.join(f'{v[k]:.6f}' for k in ('D_GS','D_PQ','D_QB','I_QB_vs_GS'))+r'\\')
        v=f['ratios'];lines.append(r'\textbf{'+name+r'} & \textbf{Pooled} & '+' & '.join(f'{v[k]:.6f}' for k in ('D_GS','D_PQ','D_QB','I_QB_vs_GS'))+r'\\\midrule')
    lines[-1]=lines[-1].replace(r'\midrule',r'\bottomrule');lines += [r'\end{tabular}',r'\end{table*}','']
    files['tables/scope_final.tex']='\n'.join(lines)
    lines=[r'\begin{table*}[t]\centering\small',r'\caption{All six session means per family in the three-date study. A session averages its twelve input log contrasts. The 1,008 requests are not independent date samples.}\label{tab:scopesessions}',r'\begin{tabular}{@{}llrrrrr@{}}\toprule',r'Family & Date & Session & $D_{\GS}$ & $D_{\PQ}$ & $D_{\QB}$ & $\Gamma$\\\midrule']
    for fam,f in a['rtx'].items():
        for s in f['sessions']:
            lines.append(('Qwen3' if fam=='Qwen' else fam)+' & '+s['date']+' & '+s['session']+' & '+' & '.join(f'{math.exp(s[k]):.6f}' for k in ('D_GS','D_PQ','D_QB','I_QB_vs_GS'))+r'\\')
    lines += [r'\bottomrule\end{tabular}',r'\end{table*}',''];files['tables/scope_sessions.tex']='\n'.join(lines)
    lines=[r'\begin{table*}[t]\centering\small',r'\caption{Secondary three-date ratios and registered weak date-sensitivity intervals. QB/PQ ratios below one favor QB; $R/C$ compares a different baseline and is not the draft increment. The intervals are conditional $t_2$ sensitivity summaries, not robust population uncertainty.}\label{tab:scopesecondary}',r'\begin{tabular}{@{}lrrrrrl@{}}\toprule',r'Family & $C_{\QB}/C_{\PQ}$ & $M_{\QB}/M_{\PQ}$ & $R/C_{\GS}$ & $R/C_{\PQ}$ & $R/C_{\QB}$ & $\Gamma$ sensitivity\\\midrule']
    for fam,f in a['rtx'].items():
        v=f['ratios'];ci=f['weak_date_sensitivity_interval'];lines.append(('Qwen3' if fam=='Qwen' else fam)+' & '+' & '.join(f'{v[k]:.6f}' for k in ('C_QB_over_C_PQ','M_QB_over_M_PQ','R_over_C_GS','R_over_C_PQ','R_over_C_QB'))+f' & [{ci[0]:.6f}, {ci[1]:.6f}]'+r'\\')
    lines += [r'\bottomrule\end{tabular}',r'\end{table*}',''];files['tables/scope_secondary.tex']='\n'.join(lines)
    lines=[r'\begin{table*}[t]\centering\small',r'\caption{Complete B570 producer-conditioned endpoint outcomes. Local combines PQ and QB, whose endpoints, cycles and captured vectors agree within every producer. Strict $R$ and own-producer C1 comparisons have different denominators.}\label{tab:producerfull}',r'\begin{tabular}{@{}lrrrrrr@{}}\toprule',r'Input & Prompt IDs & P1 C1=$R$ & P4T C1=$R$ & P1 local=C1 & P4T local=C1 & First P1 departure\\\midrule']
    for s in a['b570']['states']:
        name=s['input_id'].replace('GSM8K/train/','GSM8K/').replace('MATH500/test/','MATH/').replace('.json','')
        vals=['yes' if s[k]=='True' else 'no' for k in ('P1_C1_strict_reference_equal','P4T_C1_strict_reference_equal','P1_PQ_producer_conditioned_equal','P4T_PQ_producer_conditioned_equal')]
        lines.append(name+' & '+s['prompt_tokens']+' & '+' & '.join(vals)+' & '+(s['P1_PQ_first_C1_difference_1based'] or '---')+r'\\')
    lines += [r'\bottomrule\end{tabular}',r'\end{table*}',''];files['tables/producer_full.tex']='\n'.join(lines)
    # Keep derived values compact; complete inputs and executable audit remain supplied.
    summary={k:v for k,v in a.items() if k not in ('checks','b570')}
    summary['b570']={k:a['b570'][k] for k in ('counts','fixed_reference_switches')}
    summary['b570']['matrix_source']='anc/final_20261101/b570_MATRIX.csv'
    summary['b570']['state_source']='anc/final_20261101/b570_STATE_EFFECTS.csv'
    files['anc/final_20261101/DERIVED.json']=json.dumps(summary,indent=2,allow_nan=False)+'\n'
    # Presentation-only renderer; all analysis inputs and estimators above are unchanged.
    import importlib.util
    spec=importlib.util.spec_from_file_location('hs_visual_figures',root/'scripts/visual_figures.py')
    visual=importlib.util.module_from_spec(spec);spec.loader.exec_module(visual)
    files['figures/scope_transfer.tex']=visual.scope_figure(a)
    files['figures/producer_boundary.tex']=visual.producer_figure(a)
    return files

def verify(check,root=ROOT):
    a=reconstruct(root)
    for name in a['checks']:check('Final evidence: '+name,True)
    for path,text in outputs(root).items():check('Final generated artifact: '+path,(root/path).read_text()==text)
    return {'checks':a['checks_passed'],'rtx_session_rows':12,'b570_scientific_cells':48,'b570_strict_R_matches':39,'e2_quartets':216,'scope':'report-level and exact CSV reconstruction; no full raw-logit audit'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    out=outputs()
    if args.check:
        for path,text in out.items():
            if (ROOT/path).read_text()!=text:raise SystemExit('Generated artifact differs: '+path)
        print(json.dumps({'status':'PASS','checks':reconstruct()['checks_passed'],'outputs':len(out),'native_executions':0}))
    else:
        for path,text in out.items():(ROOT/path).write_text(text,encoding='utf-8')
        print(json.dumps({'status':'GENERATED','checks':reconstruct()['checks_passed'],'outputs':len(out),'native_executions':0}))
