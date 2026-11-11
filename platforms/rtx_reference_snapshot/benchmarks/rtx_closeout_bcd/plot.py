"""Publication-ready static figures from derived retained evidence only."""
from close_base import HERE,EOG,read,save,sha
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

OUT=HERE.parent.parent/'outputs'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'path'})
def finish(fig,name):
    fig.savefig(OUT/('HeteroSpec_RTX_闭环_'+name+'.png'),dpi=180,bbox_inches='tight',facecolor='white')
    fig.savefig(OUT/('HeteroSpec_RTX_闭环_'+name+'.svg'),bbox_inches='tight',facecolor='white');plt.close(fig)

def main():
    c=read(HERE/'generated/C_RESULTS.json');b=read(HERE/'generated/B_RESULTS.json');d=read(HERE/'generated/D_RESULTS.json');diag=read(HERE/'generated/C_BOUNDARY_DIAGNOSTICS.json')
    fig,axes=plt.subplots(1,2,figsize=(10.6,4.5),layout='constrained')
    for ax,cohort,title in zip(axes,['primary_unused_MBPP','exposed_long_supplement'],['Previously unused MBPP (8 tasks)','Exposed long-output supplement (3 tasks)']):
        a=np.zeros((4,3));labels={}
        for yi,k in enumerate([1,3,5,7]):
            for xi,cap in enumerate([128,256,512]):
                cfg=next(x for x in c['configurations'] if x['k']==k and x['cap']==cap);p=cfg['cohorts'][cohort];n=len(p['tasks'])
                yes=sum(x['full_equal'] for x in cfg['details'] if x['condition']=='selected_speculation' and x['task'] in p['tasks']);a[yi,xi]=int(yes==n and p['qualification']['matched_target']);labels[yi,xi]=f'{yes}/{n}'
        ax.imshow(a,cmap=ListedColormap(['#e7b9ac','#8bc5ac']),vmin=0,vmax=1,aspect='auto')
        for (yi,xi),label in labels.items():ax.text(xi,yi,label,ha='center',va='center',fontsize=17,fontweight='bold',color='#183b39')
        ax.set_xticks(range(3),['128','256','512']);ax.set_yticks(range(4),['1 / 2','3 / 4','5 / 6','7 / 8']);ax.set_xlabel('Requested token cap');ax.set_ylabel('Draft width k / UB');ax.set_title(title,pad=14)
    fig.suptitle('Target-scope reference qualification across width and length',fontsize=14)
    fig.supxlabel('Full token arrays + EOS/cap must agree in both repetitions.\nFormal 11-task panel: matched target passes; actual reference lengths reach 261 tokens.\nOutside this panel, topology probe HumanEval/18 target-alone fails at UB6/8.',fontsize=10)
    finish(fig,'适用范围')
    comparisons=b['costs']+[d['panels']['d']['costs']];labels=['B: target scopes / target','B: all scopes / target','B: target scopes / all scopes','D: target scopes / target']
    fig,ax=plt.subplots(figsize=(10.2,4.9),layout='constrained');y=np.arange(len(comparisons));height=.31
    for offset,key,color,title in [(-height/2,'generation','#196b68','Generation'),(height/2,'wall','#87b5b3','Whole request')]:
        v=[x[key]['task_median_geomean_speedup'] for x in comparisons];ax.barh(y+offset,v,height,color=color,label=title)
        for yi,vi in zip(y+offset,v):ax.text(vi+.006,yi,f'{vi:.3f}x',va='center',fontsize=10)
    ax.axvline(1,color='#59636b',lw=1,ls='--');ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlim(.96,1.27);ax.set_xlabel('Baseline time / candidate time; per-task medians, geometric mean');ax.set_title('Qualified resident-request costs',pad=48);ax.legend(loc='lower right',bbox_to_anchor=(1,1.02),ncol=2,frameon=False)
    fig.supxlabel('B: 24 tasks x 4 repetitions. D: 24 tasks x 2 persistent cycles.\nCapture-enabled qualification is excluded from speed measurements.',fontsize=10)
    finish(fig,'实际速度')
    observed=[]
    for crossing in diag['crossings']:
        lookup={(x['donor'],x['current_query_batch']):int(any(t in EOG for t in x['sampled_ids'])) for x in crossing['decisions']}
        observed.append(np.array([[lookup[label,active] for active in [False,True]] for label in ['on','off']]))
    assert all(np.array_equal(observed[0],m) for m in observed);matrix=observed[0]
    fig,ax=plt.subplots(figsize=(9.3,4.8),layout='constrained')
    ax.imshow(matrix,cmap=ListedColormap(['#e7b9ac','#8bc5ac']),vmin=0,vmax=1,aspect='auto')
    for yi in range(2):
        for xi in range(2):ax.text(xi,yi,'Non-EOS\nreference differs' if matrix[yi,xi]==0 else 'EOS\nreference matches',ha='center',va='center',fontsize=14,color='#183b39',fontweight='bold')
    ax.set_xticks([0,1],['Ordinary current query layout','Constrained current query layout']);ax.set_yticks([0,1],['State from constrained trajectory','State from ordinary trajectory']);ax.set_xlabel('Same actual UB6 caller and naturally matching prefix');ax.set_ylabel('Actual captured past state');ax.set_title('MBPP/229: past state changes the local EOS decision',pad=14)
    fig.supxlabel('Natural cut: 47 committed tokens; caps 128 and 256.\n8 paid auxiliary decodes; both same-path shams and source-unchanged checks pass.\nLocal decision evidence, not a unique operator or full-continuation root-cause proof.',fontsize=10)
    finish(fig,'状态交叉诊断')
    if read(HERE/'generated/C4_SELECTION.json')['status']=='RUN':
        four=read(HERE/'generated/C4_RESULTS.json');pilot=read(HERE/'generated/C4_PILOT_RESULTS.json')
        fig,axes=plt.subplots(1,2,figsize=(12.2,5.3),gridspec_kw={'width_ratios':[1,2.2]},layout='constrained')
        a=np.array([[int(v) for v in pilot['qualification'].values()]])
        axes[0].imshow(a,cmap=ListedColormap(['#e7b9ac','#8bc5ac']),vmin=0,vmax=1,aspect='auto')
        for xi,(k,q) in enumerate(pilot['qualification'].items()):axes[0].text(xi,0,'28/28' if q else 'FAIL',ha='center',va='center',fontweight='bold',fontsize=13)
        axes[0].set_xticks(range(3),['3','5','7']);axes[0].set_yticks([0],['UB = 4']);axes[0].set_xlabel('Logical draft lookahead k');axes[0].set_title('Full-reference pilot',pad=16)
        chosen=[four['costs'][i] for i in [0,1,3]];labels=['k7 / original k3','k7 / matched target','k7 / ordinary k7'];ax=axes[1];y=np.arange(3);height=.30
        for offset,key,title in [(-height/2,'generation','Generation'),(height/2,'wall','Whole request')]:
            values=[x[key]['task_median_geomean_speedup'] for x in chosen]
            colors=[('#196b68' if key=='generation' else '#87b5b3') if x['qualified'] else '#c5c7c9' for x in chosen]
            ax.barh(y+offset,values,height,color=colors,label=title)
            for yi,vi in zip(y+offset,values):ax.text(vi+.006,yi,f'{vi:.3f}x',va='center',fontsize=10)
        ax.axvline(1,color='#59636b',lw=1,ls='--');ax.set_yticks(y,[name+(' [diagnostic]' if not x['qualified'] else '') for name,x in zip(labels,chosen)])
        ax.invert_yaxis();ax.set_xlim(min(.94,min(x[key]['task_median_geomean_speedup'] for x in chosen for key in ['generation','wall'])-.06),max(x[key]['task_median_geomean_speedup'] for x in chosen for key in ['generation','wall'])+.13)
        ax.set_xlabel('Baseline time / candidate time');ax.set_title('Independent costs at fixed UB4',pad=48);ax.legend(loc='lower right',bbox_to_anchor=(1,1.02),ncol=2,frameon=False)
        fig.suptitle('Separate logical lookahead from numerical microbatch width',fontsize=14)
        fig.supxlabel('28 reused tasks, cap 128; pilot: 2 repeats, separate costs: 4 balanced repeats.\nLogical caller up to 8; occupied microqueries stay at most 4.\nGray costs are diagnostic when the baseline fails full-reference qualification.',fontsize=10)
        finish(fig,'固定UB速度')
    save(HERE/'generated/FIGURE_IDENTITIES.json',{p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name.startswith('HeteroSpec_RTX_闭环_') and p.suffix in ['.png','.svg']})
    print('Scientific figures written from final retained evidence.',flush=True)

if __name__=='__main__':main()
