#!/usr/bin/env python3
"""Style-only views of immutable validated plotting tables. No extraction/analysis."""
from pathlib import Path
import json,hashlib,subprocess,sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE=Path(__file__).resolve().parents[1];SOURCE=HERE.parent/'data'
INK='#222222';ACCENT='#4C6E9E';GRAY='#777777';LIGHT='#D9DDE2';RULE='#D0D3D6'
plt.rcParams.update({'font.family':'serif','font.serif':['STIXGeneral'],'font.size':9,
 'mathtext.fontset':'stix','axes.labelsize':9,'xtick.labelsize':8.5,'ytick.labelsize':9,
 'text.color':INK,'axes.labelcolor':INK,'axes.edgecolor':INK,'axes.linewidth':.6,
 'pdf.fonttype':42,'svg.fonttype':'path','svg.hashsalt':'heterospec-style-v04',
 'hatch.linewidth':.35,'savefig.facecolor':'white'})
def data(name):return pd.read_csv(SOURCE/name,float_precision='round_trip')
def clean(a):
 for s in ['top','right']:a.spines[s].set_visible(False)
 a.tick_params(width=.6,length=3)
def save(f,name,records,inputs):
 f.canvas.draw();renderer=f.canvas.get_renderer();bad=[]
 for obj in f.findobj(match=matplotlib.text.Text):
  if not obj.get_visible() or not obj.get_text():continue
  b=obj.get_window_extent(renderer)
  if b.width and b.height and (b.x0 < -1 or b.y0 < -1 or b.x1>f.bbox.width+1 or b.y1>f.bbox.height+1):bad.append(obj.get_text())
 assert not bad,bad
 for ext in ['pdf','svg']:
  meta={'CreationDate':None,'ModDate':None} if ext=='pdf' else {'Date':None}
  f.savefig(HERE/f'{ext}/{name}.{ext}',metadata=meta)
 receipt=dict(asset=name,width_in=f.get_figwidth(),height_in=f.get_figheight(),artists=records,
  inputs={str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE/x for x in inputs]},
  output_sha256={ext:hashlib.sha256((HERE/f'{ext}/{name}.{ext}').read_bytes()).hexdigest() for ext in ['pdf','svg']},out_of_bounds_text=bad)
 (HERE/f'qa/{name}_render.json').write_text(json.dumps(receipt,indent=2)+'\n');plt.close(f)

def overview():
 d=data('figure1_overview.csv');f=plt.figure(figsize=(6.75,1.60));a=f.add_axes([0,0,1,1]);a.set(xlim=(0,6.75),ylim=(0,1.60));a.axis('off')
 for x,s in [(0.06,'Case'),(2.0,'Local indicator'),(4.65,'Realized outcome')]:a.text(x,1.39,s,fontsize=9.5)
 for y,lw in [(1.55,.8),(1.29,.5),(.07,.8)]:a.plot([.06,6.67],[y,y],color=INK,lw=lw)
 names=['M4 HumanEval30, k = 2','M4 representative 24Q','RTX 5070 Ti Laptop, batched','358H NPU draft'];records=[]
 for idx,(_,r) in enumerate(d.iterrows()):
  y=1.09-.29*idx;a.text(.06,y,names[idx],va='center')
  signal=(rf'$V_2^{{\mathrm{{micro}}}}$: {r.local_low:.3f}–{r.local_high:.3f}' if idx<3 else f'NPU/CPU: {r.local_high:.2f} vs {r.local_low:.2f} tokens/s')
  t=a.text(2,y,signal,va='center')
  outcome='Blocked; no admissible speedup' if r.status=='blocked' else f"{'Profitable' if float(r.speedup)>1 else 'Negative'}: {float(r.speedup):.3f}×; {r.exact} exact"
  q=a.text(4.65,y,outcome,va='center')
  records.append(dict(case=r['case'],signal_text=t.get_text(),outcome_text=q.get_text()))
 save(f,'figure1A',records,['figure1_overview.csv'])

def verification():
 d=data('figure2_micro_cells.csv');f=plt.figure(figsize=(6.75,2.12));a=f.add_axes([.272,.25,.43,.68]);clean(a);a.spines['left'].set_visible(False)
 paths=list(dict.fromkeys(d.path));labels=['M4 Metal','RTX 5070 Ti Laptop, batched','RTX 5070 Ti Laptop, serialized','B570 Vulkan, fast','B570 Vulkan, serialized']
 a.set(xlim=(.85,2.65),ylim=(-.5,4.5),xticks=[1,1.5,2,2.5],yticks=list(range(5)),yticklabels=labels)
 a.tick_params(axis='y',length=0,pad=6);a.invert_yaxis();a.axvline(1,color=GRAY,ls='--',lw=.7,zorder=0)
 a.set_xlabel(r'Target-forward proxy $V_2^{\mathrm{micro}}$ (baseline-step units)',labelpad=5)
 status=['Qualified','Blocked','Exact secondary control','Diagnostic; inadmissible','Diagnostic; inadmissible'];records=[]
 for y,path in enumerate(paths):
  x=d[d.path==path];qualified=x.status.iloc[0]=='qualified';marker='s' if 'serialized' in path else 'o';color=ACCENT if qualified else INK
  seg,=a.plot([x.v2_micro.min(),x.v2_micro.max()],[y,y],color=color,lw=.8,ls='-' if qualified else '--')
  dots,=a.plot(x.v2_micro,[y]*len(x),ls='',marker=marker,ms=4,mew=.8,mec=color,mfc=color if qualified else 'white')
  a.text(1.06,y,status[y],transform=a.get_yaxis_transform(),va='center',fontsize=8.5)
  records.append(dict(path=path,points=list(map(float,dots.get_xdata())),range=list(map(float,seg.get_xdata())),marker=dots.get_marker(),filled=dots.get_markerfacecolor()!='white',status=status[y]))
 save(f,'verification',records,['figure2_micro_cells.csv'])

def m4():
 d=data('figure3_workloads.csv');f=plt.figure(figsize=(3.25,1.55));a=f.add_axes([.37,.33,.59,.60]);clean(a);a.spines['left'].set_visible(False)
 a.set(xlim=(.74,1.49),ylim=(-.5,1.5),xticks=[.8,1,1.2,1.4],yticks=[1,0],yticklabels=['Representative\n24Q','HumanEval30\n(k = 2)'])
 a.tick_params(axis='y',length=0,pad=7);a.axvline(1,color=GRAY,ls='--',lw=.7)
 a.set_xlabel('Decode speedup (×)',labelpad=5);records=[]
 for y,(_,r) in zip([1,0],d.iterrows()):
  obj=a.errorbar(r.speedup,y,xerr=[[r.speedup-r.ci_low],[r.ci_high-r.speedup]],fmt='o',ms=4,color=ACCENT,capsize=2,elinewidth=.75,capthick=.65)
  records.append(dict(workload=r.workload,estimate=float(obj.lines[0].get_xdata()[0]),ci=[float(v[0]) for v in obj.lines[2][0].get_segments()[0]]))
 save(f,'m4',records,['figure3_workloads.csv'])

def state():
 iso=data('figure4_isolated.csv');d=data('figure4_realized.csv');f=plt.figure(figsize=(6.75,2.65))
 a=f.add_axes([.075,.25,.31,.66]);clean(a);a.set(xlim=(-.3,2.3),ylim=(0,110),xticks=[0,1,2],xticklabels=['512','2,048','8,192'],yticks=[0,30,60,90])
 a.set(xlabel='Context tokens',ylabel='Steady-state draft tokens/s');a.xaxis.labelpad=5
 records=[]
 for dev,mark,color,dx in [('CPU','o',INK,-.06),('NPU','D',ACCENT,.06)]:
  x=iso[iso.device==dev].sort_values('context');obj=a.errorbar(np.arange(3)+dx,x.tokens_s,yerr=[x.tokens_s-x.ci_low,x.ci_high-x.tokens_s],fmt=mark,ms=3.8,color=color,capsize=2,elinewidth=.7,capthick=.6,label=dev)
  records.append(dict(kind='isolated',device=dev,values=list(map(float,obj.lines[0].get_ydata())),cis=[[float(v[1]) for v in seg] for seg in obj.lines[2][0].get_segments()],marker=mark))
 a.legend(loc='upper right',frameon=False,ncol=2,fontsize=8.5,handletextpad=.3,columnspacing=.8,borderpad=0)
 b=f.add_axes([.535,.25,.425,.66]);clean(b);b.spines['left'].set_visible(False);b.set(xlim=(0,32),ylim=(-.45,1.85),xticks=[0,10,20,30],yticks=[1,0],yticklabels=['CPU','NPU'])
 b.tick_params(axis='y',length=0);b.set_xlabel('Post-prefill time (s/request)',labelpad=5)
 assert d.baseline_s.nunique()==1
 ref=b.axvline(d.baseline_s.iloc[0],color=GRAY,lw=.8,ls='--',zorder=0)
 b.text(d.baseline_s.iloc[0]+.45,1.69,f'{d.baseline_s.iloc[0]:.2f} s baseline',fontsize=8,va='center')
 for y,(_,r) in zip([1,0],d.iterrows()):
  ps=[];left=0
  for value,color,hatch in [(r.draft_s,ACCENT,None),(r.target_s,LIGHT,'///'),(r.residual_s,INK,None)]:
   p=b.barh(y,value,left=left,height=.37,color=color,edgecolor=INK if hatch else color,hatch=hatch,linewidth=.45 if hatch else 0)[0];ps.append(dict(x=float(p.get_x()),width=float(p.get_width())));left+=value
  label=b.text(r.total_s,y+.31,f'{r.total_s:.2f} s; {r.headline_speedup:.3f}× GM',ha='right',fontsize=8.5,bbox=dict(facecolor='white',edgecolor='none',pad=.3),zorder=5)
  records.append(dict(kind='realized',device=r.device,components=ps,label=label.get_text()))
 records.append(dict(kind='baseline',x=float(ref.get_xdata()[0])))
 f.text(.016,.948,'(a)',fontsize=9);f.text(.455,.948,'(b)',fontsize=9)
 f.legend([Patch(facecolor=ACCENT),Patch(facecolor=LIGHT,edgecolor=INK,hatch='///',linewidth=.45)],['Replay + proposal','Complete target side'],loc='lower center',bbox_to_anchor=(.73,.005),frameon=False,ncol=2,fontsize=8,handlelength=1.3,columnspacing=1.0)
 save(f,'state',records,['figure4_isolated.csv','figure4_realized.csv'])

if __name__=='__main__':
 for fn in [overview,verification,m4,state]:fn()
 print('Four style-only vector plots generated from unchanged plotting tables.')
