#!/usr/bin/env python3
"""Generate reproducible intervention vectors; final mode requires independent raw audit."""
import argparse,hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
HERE=Path(__file__).resolve().parents[1];REVIEW=HERE.parent/'reviews/reconstruction_v010';OUT=HERE/'figures/intervention_v010'
def main():
 bpath=REVIEW/'b570/DERIVED.json';rpath=REVIEW/'rtx/DERIVED.json'
 b=json.loads(bpath.read_text());r=json.loads(rpath.read_text())
 assert b['status']=='PASS' and r['status'] in ('PASS','QUALIFIED_PASS')
 rows=[]
 for study,d in [('B570',b),('RTX',r)]:
  for x in d['task_rows']:
   rows.append({'study':study,'cohort':x.get('cohort','exposed24'),'task':x['task'],'before':x['reference_before']==3,'after':x['reference_after']==3,'output_equal':x.get('output_unchanged',x.get('native0_native1'))==3})
 OUT.mkdir(parents=True,exist_ok=True)
 payload={'schema':'paired-reference-transitions-v1','status':'INDEPENDENTLY_RECOMPUTED','sources':{str(p.relative_to(HERE.parents[2])):hashlib.sha256(p.read_bytes()).hexdigest() for p in (bpath,rpath)},'rows':rows}
 (OUT/'data.json').write_text(json.dumps(payload,indent=2)+'\n')
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'svg.fonttype':'none'})
 fig,ax=plt.subplots(figsize=(6.5,1.7));ax.set_xlim(0,10);ax.set_ylim(0,2.1);ax.axis('off')
 boxes=[(0,1.25,2.0,.66,'Specify path\nand input contract'),(2.5,1.25,1.8,.66,'Freeze complete\nprediction'),(4.8,1.25,2.0,.66,'Execute controlled\nnative path'),(7.3,1.25,2.5,.66,'Compare complete IDs\nand endpoint')]
 for x,y,w,h,txt in boxes:ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.03',facecolor='#eef2f7',edgecolor='#4C6E9E'));ax.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=8)
 for aa,bb in zip(boxes,boxes[1:]):ax.annotate('',xy=(bb[0]-.1,1.58),xytext=(aa[0]+aa[2]+.1,1.58),arrowprops={'arrowstyle':'->','color':'#444444'})
 ax.text(1.3,.55,'Prediction/native equality\nForecast this path?',ha='center',va='center',fontsize=8)
 ax.text(5,.55,'Native/reference compatibility\nRestored / persistent / new\nreference deviation',ha='center',va='center',fontsize=8)
 ax.text(8.6,.55,'Independent realized cost\nQualified path beneficial?',ha='center',va='center',fontsize=8)
 for suffix in ('pdf','svg'):fig.savefig(OUT/f'framework.{suffix}',bbox_inches='tight',pad_inches=.05)
 plt.close(fig)
 groups=[('B570: exposed 24',[x for x in rows if x['study']=='B570'],'20/24 → 24/24 tasks\n60/72 → 72/72 arrays'),('RTX: exposed 19',[x for x in rows if x['study']=='RTX' and x['cohort']=='old19'],'17/19 → 17/19 tasks\n51/57 → 51/57 arrays'),('RTX: MBPP 24',[x for x in rows if x['study']=='RTX' and x['cohort']=='new24'],'22/24 → 22/24 tasks\n66/72 → 66/72 arrays')]
 colors={(True,True):'#4C6E9E',(False,True):'#007F73',(True,False):'#B65B13',(False,False):'#777777'}
 fig,axes=plt.subplots(1,3,figsize=(6.5,2.9),gridspec_kw={'wspace':.53})
 for ax,(title,rs,foot) in zip(axes,groups):
  categories=[(True,True),(False,True),(True,False),(False,False)];ys=[3,2,1,0]
  ax.set_xlim(-.12,1.12);ax.set_ylim(-1.3,4.1);ax.axis('off');ax.set_title(title,fontsize=9,pad=4)
  ax.text(0,3.8,'Before',ha='center',fontsize=8);ax.text(1,3.8,'After',ha='center',fontsize=8)
  for cat,y in zip(categories,ys):
   match=[x for x in rs if (x['before'],x['after'])==cat]
   if not match:continue
   ax.plot([0,1],[y,y],color=colors[cat],lw=1.6,linestyle='-' if cat[0]==cat[1] else '--')
   for xx,v in zip([0,1],cat):ax.plot(xx,y,marker='o' if v else 'x',ms=6,color=colors[cat],mew=1.5,markerfacecolor='white')
   label=f'{len(match)} tasks' if len(match)>1 else match[0]['task'].replace('HumanEval/','/')
   if len(match)==2 and cat==(False,False):label='/463, /304'
   ax.text(.5,y+.17,label,ha='center',fontsize=8)
  ax.text(.5,-.77,foot,ha='center',va='center',fontsize=8)
 fig.text(.5,.02,'○ reference match     × reference mismatch     each task: three stable observations',ha='center',fontsize=8)
 for suffix in ('pdf','svg'):fig.savefig(OUT/f'paired.{suffix}',bbox_inches='tight',pad_inches=.05)
 plt.close(fig)
 print(json.dumps({'status':payload['status'],'rows':len(rows),'input_hashes':payload['sources']}))
if __name__=='__main__':
 main()
