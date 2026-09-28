"""Presentation-only revision. All experimental values come from frozen inputs.
Run with Python, numpy, pandas, matplotlib and pymupdf installed.
"""
from pathlib import Path
import json, hashlib, re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
ROOT=Path(__file__).resolve().parent
DATA=ROOT.parents[2]/'figures/data'; OUT=ROOT/'pdf'
INK='#24313D'; BLUE='#366D95'; GRAY='#6C7680'; LIGHT='#E4E9EE'; RULE='#CCD3D9'
plt.rcParams.update({'font.family':'serif','font.serif':['STIXGeneral'],'mathtext.fontset':'stix',
 'font.size':8.5,'axes.labelsize':8.5,'xtick.labelsize':8,'ytick.labelsize':8.5,
 'text.color':INK,'axes.labelcolor':INK,'axes.edgecolor':INK,'axes.linewidth':.55,
 'pdf.fonttype':42,'svg.fonttype':'path','svg.hashsalt':'heterospec-review',
 'hatch.linewidth':.35,'savefig.facecolor':'white','figure.facecolor':'white'})
CHECKS=[]
def df(n):return pd.read_csv(DATA/n,float_precision='round_trip')
def check(label,a,b):
 assert np.allclose(a,b,rtol=1e-13,atol=1e-13),(label,a,b)
 CHECKS.append(label)
def clean(a):
 for s in ['top','right']:a.spines[s].set_visible(False)
 a.tick_params(length=2.5,width=.55)
def save(f,name,records,inputs):
 f.canvas.draw();ren=f.canvas.get_renderer();bad=[]
 for t in f.findobj(matplotlib.text.Text):
  if t.get_visible() and t.get_text():
   b=t.get_window_extent(ren)
   if b.width and b.height and (b.x0<-.5 or b.y0<-.5 or b.x1>f.bbox.width+.5 or b.y1>f.bbox.height+.5):bad.append(t.get_text())
 assert not bad,(name,bad)
 for ext in ['pdf','svg']:
  kwargs={'dpi':180} if ext=='png' else {'metadata':{'CreationDate':None,'ModDate':None} if ext=='pdf' else {'Date':None}}
  f.savefig(ROOT/ext/f'{name}.{ext}',**kwargs)
  if ext=='svg':
   p=ROOT/ext/f'{name}.{ext}'
   p.write_text('\n'.join(line.rstrip() for line in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
 receipt={'asset':name,'size_in':list(f.get_size_inches()),'inputs':{n:hashlib.sha256((DATA/n).read_bytes()).hexdigest() for n in inputs},'artists':records,'out_of_bounds_text':bad}
 (ROOT/f'qa/{name}.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
 plt.close(f)
def m4():
 d=df('figure3_workloads.csv');f=plt.figure(figsize=(3.25,1.55));a=f.add_axes([.37,.31,.60,.55]);clean(a);a.spines['left'].set_visible(False)
 a.set(xlim=(.74,1.49),ylim=(-.5,1.6),xticks=[.8,1,1.2,1.4],yticks=[1,0],yticklabels=['Representative\n24Q','HumanEval30\n(k = 2)'],xlabel='Decode speedup (×)')
 a.tick_params(axis='y',length=0,pad=6);a.axvline(1,color=GRAY,ls='--',lw=.65,zorder=0)
 f.text(.37,.95,'Independent studies · GM with 95% CI',fontsize=8,va='top')
 records=[]
 for y,r in zip([1,0],d.itertuples()):
  e=a.errorbar(r.speedup,y,xerr=[[r.speedup-r.ci_low],[r.ci_high-r.speedup]],fmt='o',ms=4,color=BLUE,capsize=2,elinewidth=.9)
  a.text(r.speedup,y+.25,f'{r.speedup:.3f}×',ha='center',fontsize=8)
  check(r.workload+' estimate',e.lines[0].get_xdata(),[r.speedup]);check(r.workload+' CI',e.lines[2][0].get_segments()[0][:,0],[r.ci_low,r.ci_high])
  records.append({'workload':r.workload,'estimate':r.speedup,'ci':[r.ci_low,r.ci_high]})
 save(f,'m4',records,['figure3_workloads.csv'])
def verification():
 d=df('figure2_micro_cells.csv');f=plt.figure(figsize=(6.75,2.12));a=f.add_axes([.26,.29,.43,.56]);clean(a);a.spines['left'].set_visible(False)
 labels=['M4 Metal','RTX 5070 Ti Laptop · batched','RTX 5070 Ti Laptop · serialized','B570 Vulkan · fast','B570 Vulkan · serialized']
 a.set(xlim=(.85,2.65),ylim=(4.5,-.5),xticks=[1,1.5,2,2.5],yticks=range(5),yticklabels=labels)
 a.tick_params(axis='y',length=0,pad=6,labelsize=8);a.axvline(1,color=GRAY,ls='--',lw=.65,zorder=0)
 a.set_xlabel(r'Target-forward proxy $V_2^{\mathrm{micro}}$ (baseline-step units)',labelpad=4)
 for y in [0.5,2.5]:a.axhline(y,color=RULE,lw=.5,zorder=0)
 f.text(.018,.965,'Target-forward work',fontsize=9,fontweight='bold',va='top')
 f.text(.72,.965,'Path status',fontsize=9,fontweight='bold',va='top')
 status=['Qualified','Blocked','Exact secondary control','Diagnostic; inadmissible','Diagnostic; inadmissible'];records=[]
 for y,(path,x) in enumerate(d.groupby('path',sort=False)):
  qualified=x.status.iloc[0]=='qualified';mark='s' if 'serialized' in path else 'o';color=BLUE if qualified else GRAY
  line,=a.plot([x.v2_micro.min(),x.v2_micro.max()],[y,y],color=color,lw=.7,ls='-' if qualified else '--')
  # Vertical offsets separate overlapping conditions; x values are untouched.
  offsets=np.linspace(-.17,.17,len(x));dots,=a.plot(x.v2_micro,y+offsets,ls='',marker=mark,ms=4,mec=color,mfc=color if qualified else 'white',mew=.8)
  a.text(1.07,y,status[y],transform=a.get_yaxis_transform(),va='center',fontsize=8.1)
  check(path+' points',dots.get_xdata(),x.v2_micro);check(path+' context range',line.get_xdata(),[x.v2_micro.min(),x.v2_micro.max()])
  records.append({'path':path,'points':list(dots.get_xdata()),'contexts':list(x.context),'vertical_offsets':list(offsets),'status':status[y]})
 f.text(.26,.035,'Points: tested conditions; horizontal spans: condition ranges, not CIs.',fontsize=7.9)
 save(f,'verification',records,['figure2_micro_cells.csv'])
def state():
 iso=df('figure4_isolated.csv');d=df('figure4_realized.csv');f=plt.figure(figsize=(6.75,2.65));records=[]
 f.text(.075,.975,'(a) Isolated draft throughput',fontsize=9,fontweight='bold',va='top')
 f.text(.075,.902,'Median + 95% CI · 5 repetitions/cell',fontsize=8,va='top',color=GRAY)
 f.text(.53,.975,'(b) Integrated runtime costs',fontsize=9,fontweight='bold',va='top')
 f.text(.53,.902,'Mean · 90 exact requests/path',fontsize=8,va='top',color=GRAY)
 a=f.add_axes([.075,.32,.31,.49]);clean(a)
 a.set(xlim=(-.3,2.3),ylim=(0,110),xticks=[0,1,2],xticklabels=['512','2,048','8,192'],yticks=[0,30,60,90],xlabel='Context tokens',ylabel='Draft tokens/s')
 for dev,mark,color,dx in [('CPU','o',INK,-.06),('NPU','D',BLUE,.06)]:
  x=iso[iso.device==dev].sort_values('context');obj=a.errorbar(np.arange(3)+dx,x.tokens_s,yerr=[x.tokens_s-x.ci_low,x.ci_high-x.tokens_s],fmt=mark,ms=3.8,color=color,capsize=2,elinewidth=.8,label=dev)
  check(dev+' throughput',obj.lines[0].get_ydata(),x.tokens_s)
  check(dev+' throughput CIs',np.array(obj.lines[2][0].get_segments())[:,:,1],x[['ci_low','ci_high']].values)
  records.append({'kind':'isolated','device':dev,'values':list(x.tokens_s),'cis':x[['ci_low','ci_high']].values.tolist()})
 a.legend(loc='upper right',ncol=2,frameon=False,fontsize=8,handletextpad=.2,columnspacing=.8,borderpad=0)
 b=f.add_axes([.53,.32,.425,.49]);clean(b);b.spines['left'].set_visible(False)
 b.set(xlim=(0,32),ylim=(-.5,1.75),xticks=[0,10,20,30],yticks=[1,0],yticklabels=['CPU','NPU'],xlabel='Post-prefill time (s/request)');b.tick_params(axis='y',length=0)
 ref=b.axvline(d.baseline_s.iloc[0],color=GRAY,ls='--',lw=.7,zorder=0)
 b.text(d.baseline_s.iloc[0]+.45,1.59,f'{d.baseline_s.iloc[0]:.2f} s baseline',fontsize=7.8,va='center')
 for y,r in zip([1,0],d.itertuples()):
  parts=[];left=0
  for v,c,h in [(r.draft_s,BLUE,None),(r.target_s,LIGHT,'///'),(r.residual_s,INK,None)]:
   p=b.barh(y,v,left=left,height=.36,color=c,hatch=h,edgecolor=INK if h else c,linewidth=.35 if h else 0)[0];parts.append(p.get_width());left+=v
  check(r.device+' stacked widths',parts,[r.draft_s,r.target_s,r.residual_s]);check(r.device+' stack total',left,r.total_s)
  b.text(r.total_s+.45,y,f'{r.total_s:.2f} s',fontsize=8,va='center')
  midpoint=r.draft_s+r.target_s/2 if r.device=='CPU' else r.draft_s/2
  pct=r.target_pct if r.device=='CPU' else r.draft_pct
  b.text(midpoint,y,f'{pct:.2f}%',ha='center',va='center',fontsize=8,color=INK if r.device=='CPU' else 'white',bbox=dict(facecolor=LIGHT,edgecolor='none',pad=.4) if r.device=='CPU' else None)
  records.append({'kind':'realized','device':r.device,'components':parts,'total':r.total_s,'headline_speedup':r.headline_speedup,'dominant_share':pct})
 f.legend([Patch(facecolor=BLUE),Patch(facecolor=LIGHT,edgecolor=INK,hatch='///',linewidth=.35)],['Replay + proposal','Complete target side'],loc='lower left',bbox_to_anchor=(.505,.079),frameon=False,ncol=2,fontsize=7.7,handlelength=1.1,columnspacing=.8)
 f.text(.075,.045,'Separate prompt-GM speedup: CPU '+f'{d.headline_speedup.iloc[0]:.3f}×'+', NPU '+f'{d.headline_speedup.iloc[1]:.3f}×'+'. Residuals <0.05%; true widths retained.',fontsize=8)
 check('shared baseline',ref.get_xdata(),[d.baseline_s.iloc[0]]*2)
 save(f,'state',records,['figure4_isolated.csv','figure4_realized.csv'])

if __name__=='__main__':
 for fn in [m4,verification,state]:fn()
 (ROOT/'qa/numeric-checks.json').write_text(json.dumps({'passed':len(CHECKS),'checks':CHECKS},indent=2)+'\n')
 print('Three approved plots generated;',len(CHECKS),'artist checks passed.')
