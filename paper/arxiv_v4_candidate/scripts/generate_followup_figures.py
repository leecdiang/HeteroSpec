#!/usr/bin/env python3
"""Generate the follow-up TeX figures and tables from the frozen reported data.
No native inference, plotting service, or network access is used.
"""
from pathlib import Path
import csv, math, json, hashlib
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'anc/closure'
def gm(x):
 x=list(x)
 if not x or not all(math.isfinite(v) and v>0 for v in x):raise ValueError('positive finite ratios required')
 return math.exp(sum(map(math.log,x))/len(x))
def load():
 with (DATA/'rtx_blocks.csv').open(newline='') as f:r=list(csv.DictReader(f))
 with (DATA/'b570_blocks.csv').open(newline='') as f:b=list(csv.DictReader(f))
 out={}
 for key,rows,cols in [('RTX',r,('QB_dual_PQ','QB_R','PQ_A_PQ_B')),('B570',b,('service_QB_over_dualPQ','service_QB_over_R','service_PQA_over_PQB'))]:
  out[key]=[{'session':int(x['session']),'input':x['input_id'],'layout':float(x[cols[0]]),'economics':float(x[cols[1]]),'aa':float(x[cols[2]]),'pq_economics':float(x[cols[1]])/float(x[cols[0]])} for x in rows]
 return out

def outputs():
 panels=load(); result={};summary={}
 for k,rows in panels.items():
  inp=list(dict.fromkeys(r['input'] for r in rows))
  summary[k]={'layout':gm(r['layout'] for r in rows),'economics':gm(r['economics'] for r in rows),'pq_economics':gm(r['pq_economics'] for r in rows),
              'aa':max(abs(gm(r['aa'] for r in rows if r['input']==i)-1) for i in inp),
              'sessions':[gm(r['layout'] for r in rows if r['session']==s) for s in range(4)],
              'inputs':[dict(input=i,**{c:gm(r[c] for r in rows if r['input']==i) for c in ('layout','economics','pq_economics','aa')}) for i in inp]}
 # The primary plots retain all blocks. Vertical offsets are fixed display positions,
 # not another variable or an uncertainty estimate. No new measurement is added.
 fig=[r'\begin{tikzpicture}',r'\begin{groupplot}[group style={group size=3 by 1,horizontal sep=.68cm},',
 r'width=.305\textwidth,height=6.1cm,ymin=.5,ymax=2.65,ytick={1,2},',
 r'tick label style={font=\footnotesize},title style={font=\small},label style={font=\footnotesize,align=center},',
 r'axis lines*=left,axis line style={aux,line width=.45pt},tick style={aux},',
 r'grid=major,grid style={gray!12},clip=false]']
 configs=[('layout',r'\textbf{A} Layout increment',r'$T_{\QB}/\bar T_{\PQ}$\\$<1$: QB faster',r'xmin=.82,xmax=1.18,xtick={.85,1,1.15},yticklabels={B570,RTX}', 'qualified'),
 ('aa',r'\textbf{B} Identical-PQ control',r'$T_{\PQ_A}/T_{\PQ_B}$\\identical implementation',r'xmin=.80,xmax=1.18,xtick={.85,1,1.15},yticklabels={,}','target'),
 ('economics',r'\textbf{C} Value of drafting',r'Service / $T_R$ (log scale)\\$<1$: speculation faster',r'xmode=log,log basis x=10,xmin=.44,xmax=3.45,xtick={.5,1,2,3},xticklabels={0.5,1,2,3},yticklabels={,}','qualified')]
 for field,title,xlabel,opts,col in configs:
  fig.append(r'\nextgroupplot[title={'+title+'},xlabel={'+xlabel+'},'+opts+']')
  fig.append(r'\addplot[aux,dashed,line width=.65pt] coordinates {(1,.5)(1,2.65)};')
  if field=='layout':
   fig.append(r'\addplot[aux,densely dotted] coordinates {(.98,.5)(.98,2.65)};')
  elif field=='aa':
   for v in ('.98','1.02'):fig.append(r'\addplot[aux,densely dotted] coordinates {('+v+r',.5)('+v+r',2.65)};')
  for platform,y in [('RTX',2),('B570',1)]:
   rows=panels[platform]
   if field=='economics':
    # Two already measured speculative paths against the same R. Blue squares
    # identify PQ; green diamonds identify QB, including in grayscale.
    for f,offset,c,mark,label in [('economics',.19,'qualified','diamond*','QB'),('pq_economics',-.18,'target','square*','PQ')]:
     coords=' '.join('('+f'{x[f]:.12f},{y+offset-.10+i*.013:.3f}'+')' for i,x in enumerate(rows))
     fig.append(r'\addplot[only marks,mark=o,mark size=1.1pt,mark options={draw='+c+r',fill=white,line width=.45pt},'+c+r'] coordinates {'+coords+'};')
     val=gm(x[f] for x in rows)
     fig.append(r'\addplot[only marks,mark='+mark+r',mark size=2.5pt,'+c+r'] coordinates {('+f'{val:.12f},{y+offset:.3f}'+')};')
     fig.append(r'\node[font=\scriptsize,text='+c+r',anchor=south] at (axis cs:'+f'{val:.12f},{y+offset+.11:.3f}'+'){'+label+' '+f'{val:.4f}'+'};')
   else:
    coords=' '.join('('+f'{x[field]:.12f},{y-.21+i*.027:.3f}'+')' for i,x in enumerate(rows))
    fig.append(r'\addplot[only marks,mark=o,mark size=1.3pt,mark options={draw='+col+r',fill=white,line width=.5pt},'+col+r'] coordinates {'+coords+'};')
    val=gm(x[field] for x in rows)
    fig.append(r'\addplot[only marks,mark=diamond*,mark size=2.8pt,'+col+r'] coordinates {('+f'{val:.12f},{y}'+')};')
    if field=='layout':
     fig.append(r'\node[font=\footnotesize,text='+col+r',anchor=south] at (axis cs:'+f'{val:.12f},{y+.23}'+'){'+f'{val:.4f}'+'};')
    else:
     fig.append(r'\node[font=\scriptsize,text=aux,anchor=south] at (axis cs:0.99,'+f'{y+.24}'+'){max. task imbalance '+f'{100*summary[platform]["aa"]:.2f}'+r'\%};')
 fig += [r'\end{groupplot}',r'\end{tikzpicture}','']
 result['figures/service_panels.tex']='\n'.join(fig)
 mapping=r'''\begin{tikzpicture}[font=\footnotesize]
\node[anchor=north west,inner sep=0] at (0,0) {\begin{minipage}[t]{.48\textwidth}
\textbf{A\quad Fixed logical length 1023: RTX}\par\vspace{5pt}
\begin{tabular}{@{}rrrr@{}}\toprule
Physical extent & Qualification & Kernels & Cost / native A\\\midrule
1023 (native) & 4/4 pass & 8 & 1.000000\\
1024 (padded) & \textcolor{draft}{4/4 fail} & 3$^\ast$ & ---\\
1025 (padded) & \textcolor{qualified}{4/4 pass} & 8 & 1.014783\\\bottomrule
\end{tabular}\par\vspace{5pt}
$^\ast$First-call trace only; the failed path has no qualified clean cost. Logical inputs and original mask columns are unchanged.
\end{minipage}};
\node[anchor=north west,inner sep=0] at (.515\textwidth,0) {\begin{minipage}[t]{.48\textwidth}
\textbf{B\quad Complete Q-representation transactions}\par\vspace{5pt}
\begin{tabular}{@{}llr@{}}\toprule
Panel & Comparator & Compact-QH ratio\\\midrule
RTX $q=2$ & QB\_A / QB\_B & 1.002216 / 1.008295\\
RTX $q=4$ & QB\_A / QB\_B & 1.001598 / 1.004167\\
B570 $q=2,4$ & dual-QB & 0.992244\\\bottomrule
\end{tabular}\par\vspace{5pt}
B570 adjusted interval: [0.979908, 1.004691]. All tested practical-effect screens remain unresolved; no QH advantage is established.
\end{minipage}};
\end{tikzpicture}
'''
 result['figures/mapping_boundary.tex']=mapping
 lines=[r'\begin{table*}[t]\centering\small',r'\caption{All input-aggregate service ratios. Four sessions contribute to each row. A/A is the ratio of two identical PQ controls. Lower QB ratios favor QB. Inputs are different between platforms.}\label{tab:serviceinputs}',r'\begin{tabular}{@{}llrrrr@{}}\toprule',r'Platform & Input & Output / stop & QB / dual-PQ & QB / R & PQ\_A / PQ\_B\\\midrule']
 outcomes={'RTX':['34/EOG','128/CAP','128/CAP','128/CAP'],'B570':['64/CAP','53/EOG','41/EOG','64/CAP']}
 for platform in ['RTX','B570']:
  for i,x in enumerate(summary[platform]['inputs']):
   lines.append(platform+' & '+x['input'].replace('GSM8K/test/','GSM8K/')+' & '+outcomes[platform][i]+' & '+f"{x['layout']:.6f} & {x['economics']:.6f} & {x['aa']:.6f}"+r'\\')
  s=summary[platform]; lines.append(r'\textbf{'+platform+r'} & \textbf{Equal-weight mean} & --- & '+f"{s['layout']:.6f} & {s['economics']:.6f}"+r' & ---\\\midrule')
 lines[-1]=lines[-1].replace(r'\midrule',r'\bottomrule')
 lines += [r'\end{tabular}',r'\end{table*}','']
 result['tables/service_input_table.tex']='\n'.join(lines)
 lines=[r'\begin{table*}[t]\centering\footnotesize',r'\caption{Every input/session block from the two service panels. Each platform has its own input set; adjacent rows do not form cross-platform pairs. Exact source blocks are included in the ancillary CSV files.}\label{tab:serviceblocks}']
 for j,platform in enumerate(['RTX','B570']):
  if j: lines.append(r'\hfill')
  lines += [r'\begin{minipage}[t]{.485\textwidth}\centering',r'\textbf{'+platform+r'}\par\vspace{4pt}',r'\setlength{\tabcolsep}{3pt}\begin{tabular}{@{}rlrrr@{}}\toprule',r'$s$ & Input & QB/PQ & QB/R & A/A\\\midrule']
  for x in panels[platform]:
   name=x['input'].replace('GSM8K/test/','G/').replace('MBPP/','M/').replace('HumanEval/','HE/')
   lines.append(f"{x['session']} & {name} & {x['layout']:.6f} & {x['economics']:.6f} & {x['aa']:.6f}"+r'\\')
  lines += [r'\bottomrule\end{tabular}\end{minipage}']
 lines += [r'\end{table*}','']
 result['tables/service_block_table.tex']='\n'.join(lines)
 result['anc/closure/derived_summary.json']=json.dumps(summary,indent=2)+'\n'
 return result
if __name__=='__main__':
 for name,text in outputs().items():
  (ROOT/name).write_text(text,encoding='utf-8')
 print('Generated two figures, two tables, and derived summary from frozen service blocks.')
