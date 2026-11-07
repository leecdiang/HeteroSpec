"""Standalone scientific figures; run after resident measurement stops."""
import csv,json,shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
OUT=HERE.parent.parent/'outputs'
PUB=HERE.parent/'continuity-public/benchmarks/rtx_consistency_contract_v1'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})

def read(p):return json.loads(p.read_text())
def save(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=180,bbox_inches='tight')
    fig.savefig(OUT/(name+'.svg'),bbox_inches='tight')
    (PUB/'figures').mkdir(exist_ok=True)
    shutil.copyfile(OUT/(name+'.svg'),PUB/'figures'/(name+'.svg'))
    plt.close(fig)

effects=read(HERE/'generated/analysis/EFFECTS.json')
fig,axes=plt.subplots(1,2,figsize=(11.8,4.5))
for ax,task,cut in zip(axes,[15,25],[13,4]):
    e=next(x for x in effects if x['task']==task and x['repetition']==1)
    for row,n in enumerate(['N0','N1']):
        for col,u in enumerate(['2','1']):
            ids=e['matrix'][n][u]['sampled_ids']
            blue=(u=='2' if task==15 else not(n=='N1' and u=='1'))
            ax.add_patch(plt.Rectangle((col,row),1,1,facecolor='#e1edf7' if blue else '#f9e4cc',edgecolor='white',lw=3))
            ax.text(col+.5,row+.5,', '.join(map(str,ids)),ha='center',va='center',fontsize=12)
    ax.set(xlim=(0,2),ylim=(2,0),xticks=[.5,1.5],xticklabels=['Current UB2','Current UB1'],
           yticks=[.5,1.5],yticklabels=['Native N0 state','Native N1 state'],
           title=f'HumanEval/{task}: committed prefix = {cut}')
    ax.tick_params(length=0);ax.xaxis.tick_top()
    for spine in ax.spines.values():spine.set_visible(False)
fig.suptitle('Same actual prefix / pending token / proposal input / sampler; cross state and call path',fontsize=13,y=.98)
fig.text(.5,.025,'Cell values: committed verification IDs. All three repeats agree. Colors denote decisions, not reference correctness.\nControls /18 and /31: no decision effect at their fixed checkpoints. Finite checkpoint results only.',ha='center',fontsize=10)
fig.tight_layout(w_pad=2,rect=(0,.14,1,.91))
save(fig,'HeteroSpec_状态路径交叉')

fig=plt.figure(figsize=(14,9));grid=fig.add_gridspec(2,3,height_ratios=[1,1.1])
panels=[('cost-v2',['serialized','attention'],['Global serial\nk2','Per-query\nk2'],'k2 / original target UB1'),
        ('cost-wide',['ordinary_k3','attention_k3','query_batch_k3'],['Ordinary k3\nBLOCKED','Per-query\nk3','Query-batch\nk3'],'k3 / original target UB1'),
        ('cost-matched',['query_batch_k3'],['Query-batch\nk3'],'Primary: matched prefill / observer bypass')]
for i,(panel,conditions,labels,title) in enumerate(panels):
    ax=fig.add_subplot(grid[0,i]);summary=read(HERE/f'generated/analysis/{panel}_VALIDATION.json')['summary']
    x=np.arange(len(conditions));width=.33
    for j,c in enumerate(conditions):
        r=next(r for r in summary if r['condition']==c)
        if not r['qualifies_whole_panel']:
            ax.text(j,.68,'68/76 match\nno qualified\nspeedup',ha='center',fontsize=9,color='#a44132')
            continue
        for shift,key,color in [(-width/2,'wall_speedup_gm','#4c78a8'),(width/2,'generation_speedup_gm','#f2a34a')]:
            v=r[key];ax.bar(j+shift,v,width,color=color,label=('Whole request' if shift<0 else 'Generation') if j==0 else None)
            ax.text(j+shift,v+.035,f'{v:.3f}',ha='center',fontsize=9)
    ax.axhline(1,color='#4b5563',ls='--',lw=1)
    ax.set(xticks=x,xticklabels=labels,xlim=(-.65,len(conditions)-.35),ylim=(.48,2.0),title=title,ylabel='Speedup vs panel-specific target')
    ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    if i==0:ax.legend(frameon=False,fontsize=9,loc='upper left')
ax=fig.add_subplot(grid[1,:])
rows=list(csv.DictReader((HERE/'generated/analysis/cost-matched_PAIRED.csv').open()))
rows=[r for r in rows if r['condition']=='query_batch_k3'];assert len(rows)==19
x=np.arange(19)
ax.scatter(x-.10,[float(r['wall_speedup']) for r in rows],s=44,color='#4c78a8',label='Whole request')
ax.scatter(x+.10,[float(r['generation_speedup']) for r in rows],s=44,color='#f2a34a',label='Generation')
ax.axhline(1,color='#4b5563',ls='--',lw=1)
ax.set(xticks=x,xticklabels=[r['task'].split('/')[-1] for r in rows],ylim=(.86,1.5),
       title='Primary matched-prefill panel: every task, four repetitions, original complete-output references',
       xlabel='HumanEval task ID (fixed input order)',ylabel='Task-median speedup')
ax.grid(axis='y',alpha=.2);ax.legend(frameon=False,loc='upper left',ncol=2)
fig.suptitle('Diagnosis-guided local attention constraints: output gates and costs',fontsize=15,y=.985)
fig.text(.5,.015,'All 19 tasks are exposed; Qwen3 Q8_0, RTX 5070 Ti Laptop, FA off, single request, greedy, cap128.\nGeometric means of per-task median ratios; no confidence intervals or cross-panel timing substitution. Initial panels retain observer-wrapper costs.',ha='center',fontsize=10)
fig.subplots_adjust(top=.90,bottom=.13,hspace=.43,wspace=.30)
save(fig,'HeteroSpec_速度对照')
print('Saved two PNG/SVG figures and copied public SVGs.',flush=True)
