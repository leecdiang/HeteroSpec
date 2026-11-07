#!/usr/bin/env python3
"""Generate an explicit retrospective contrast from unchanged reported ratios.
No new timings, population intervals, native execution, or external services.
"""
from pathlib import Path
from decimal import Decimal
import csv, hashlib, json
ROOT=Path(__file__).resolve().parents[1]
FAMILIES=('Qwen3','SmolLM2','Llama')

def outputs(root=ROOT):
    source=root/'anc/rtx_repair_cost.csv'
    with source.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
    if len(rows)!=21 or any(x['qualified']!='True' or x['tasks']!='12' for x in rows):
        raise ValueError('Expected the complete original 21 qualified comparisons')
    c={(r['family'],r['comparison']):Decimal(r['ratio']) for r in rows}
    eps=Decimal('0.0000005'); data={}
    for fam in FAMILIES:
        q=c[fam,'M_QB/C_QB']; d={'QB':q}; bounds={'QB':[q-eps,q+eps]}
        for layout in ('GS','PQ'):
            a,b=c[fam,f'M_{layout}/M_QB'],c[fam,f'C_{layout}/C_QB']
            d[layout]=a*q/b
            bounds[layout]=[(a-eps)*(q-eps)/(b+eps),(a+eps)*(q+eps)/(b-eps)]
        a,b=c[fam,'C_GS/C_QB'],c[fam,'M_GS/M_QB']
        gamma=a/b
        data[fam]={'draft_value':{k:float(d[k]) for k in ('GS','PQ','QB')},
            'report_rounding_enclosures':{k:[float(v) for v in bounds[k]] for k in ('GS','PQ','QB')},
            'gamma_QB_from_GS':float(gamma),'gamma_report_rounding_enclosure':[float((a-eps)/(b+eps)),float((a+eps)/(b-eps))],
            'local_repair_crosses_draft_parity':d['GS']<1<min(d['PQ'],d['QB'])}
    audit={'status':'RETROSPECTIVE_REPORTED_RATIO_RECONSTRUCTION','source':'anc/rtx_repair_cost.csv',
           'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
           'source_git_blob':hashlib.sha1(b'blob '+str(source.stat().st_size).encode()+b'\0'+source.read_bytes()).hexdigest(),
           'source_scope':'Original seven-arm campaign: 12 exposed inputs/family, two adjacent sessions, four repetitions; original weights and resident-request window.',
           'formula':'D_L = S(M_L/M_QB) * D_QB / S(C_L/C_QB); Gamma = S(C_GS/C_QB) / S(M_GS/M_QB)',
           'rounding_note':'Enclosures propagate +/-0.5e-6 reporting-rounding bounds only. They are not sampling uncertainty or confidence intervals.',
           'novelty_note':'The draft-value identity and crossover already occur in the earlier manuscript. This release makes the contrast explicit and plots all three policies; it adds no experimental observation.',
           'not_component_time_decomposition':True,'new_native_executions':0,'families':data}
    fig=[r'\begin{tikzpicture}',r'\begin{groupplot}[group style={group size=3 by 1,horizontal sep=.70cm},',
         r'width=.305\textwidth,height=5.6cm,ymin=.5,ymax=3.5,ytick={1,2,3},',
         r'tick label style={font=\footnotesize},title style={font=\small,yshift=12pt},label style={font=\footnotesize,align=center},',
         r'axis lines*=left,axis line style={aux,line width=.45pt},tick style={aux},grid=major,grid style={gray!13}]']
    configs=[('C_PQ/C_QB',r'\textbf{A} Local representation',r'$T_{C_{\PQ}}/T_{C_{\QB}}$\\$>1$: QB faster',r'xmin=.995,xmax=1.09,xtick={1,1.04,1.08},yticklabels={Llama,SmolLM2,Qwen3}'),
             ('C_GS/C_QB',r'\textbf{B} Global serialization',r'$T_{C_{\GS}}/T_{C_{\QB}}$\\$>1$: QB faster',r'xmin=.95,xmax=2.55,xtick={1,1.5,2,2.5},yticklabels={,,}')]
    for comp,title,xlabel,opts in configs:
        fig.append(r'\nextgroupplot[title={'+title+'},xlabel={'+xlabel+'},'+opts+']')
        fig.append(r'\addplot[aux,dashed] coordinates {(1,.5)(1,3.5)};')
        for i,fam in enumerate(FAMILIES):
            value=float(c[fam,comp]); y=3-i
            fig.append(r'\addplot[only marks,mark=diamond*,mark size=2.7pt,qualified] coordinates {('+f'{value:.12f},{y}'+')};')
            fig.append(r'\node[font=\scriptsize,anchor=south] at (axis cs:'+f'{value:.12f},{y+.12}'+'){'+f'{value:.3f}'+'};')
    fig.append(r'\nextgroupplot[title={\textbf{C} Draft value by repair},xlabel={$D_L=T_{M_L}/T_{C_L}$\\$>1$: drafting faster},xmin=.53,xmax=1.27,xtick={.6,.8,1,1.2},yticklabels={,,},legend style={at={(.5,1.01)},anchor=south,draw=none,font=\scriptsize,fill=none},legend columns=3]')
    fig.append(r'\addplot[aux,dashed,forget plot] coordinates {(1,.5)(1,3.5)};')
    for layout,offset,color,marker in [('GS',.23,'aux','square*'),('PQ',0,'target','o'),('QB',-.23,'qualified','diamond*')]:
        coords=' '.join('('+f"{data[fam]['draft_value'][layout]:.12f},{3-i+offset:.2f}"+')' for i,fam in enumerate(FAMILIES))
        fig.append(r'\addplot[only marks,mark='+marker+r',mark size=2.4pt,'+color+r'] coordinates {'+coords+'};')
        fig.append(r'\addlegendentry{'+layout+'}')
    fig += [r'\end{groupplot}',r'\end{tikzpicture}','']
    tab=[r'\begin{table}[t]\centering\small',r'\caption{Retrospective repair--draft contrasts reconstructed from Table~\ref{tab:allcost}. $D_L>1$ favors drafting; $\Gamma$ compares draft value under QB and GS. These are common-panel ratios, not operator-time fractions.}\label{tab:repairinteraction}',r'\setlength{\tabcolsep}{3pt}',r'\begin{tabular}{@{}lrrrr@{}}\toprule',r'Family & $D_{\GS}$ & $D_{\PQ}$ & $D_{\QB}$ & $\Gamma$\\\midrule']
    for fam in FAMILIES:
        d=data[fam];tab.append(fam+' & '+' & '.join(f"{d['draft_value'][l]:.3f}" for l in ('GS','PQ','QB'))+' & '+f"{d['gamma_QB_from_GS']:.3f}"+r'\\')
    tab += [r'\bottomrule\end{tabular}',r'\end{table}','']
    return {'anc/repair_interaction.json':json.dumps(audit,indent=2)+'\n','figures/cost.tex':'\n'.join(fig),'tables/repair_interaction.tex':'\n'.join(tab)}

if __name__=='__main__':
    for name,text in outputs().items():
        p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
    print('Generated retrospective repair/draft contrasts; new measurements: 0.')
