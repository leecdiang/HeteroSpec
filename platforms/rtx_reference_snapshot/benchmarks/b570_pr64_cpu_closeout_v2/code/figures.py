from evidence import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main():
    begin('figures'); plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','svg.hashsalt':'HeteroSpecCPUCloseoutV2','pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    cases=json.loads((OUT/'CAUSAL_RECHECK.json').read_text())['cases'];folder=OUT/'figures';folder.mkdir(exist_ok=True)
    fig,axes=plt.subplots(3,2,figsize=(13,10))
    for ax,c in zip(axes.flat,cases):
        ax.axis('off');mat=c['focus']['decisions'];recipe=[f"UB{r['ub']} / reserve {r['outputs_max']}" for r in c['recipes']]
        tb=ax.table(cellText=mat,rowLabels=c['donor_labels'],colLabels=recipe,loc='center',cellLoc='center',bbox=[.33,.28,.62,.48]);tb.auto_set_font_size(False);tb.set_fontsize(11)
        for (i,j),cell in tb.get_celld().items():
            cell.set_edgecolor('#c5cdd6');cell.set_facecolor('#e6f0f6' if i==0 else '#f6f8fa')
        ax.set_title(f"{c['task']} | round {c['round']} | {c['focus']['classification']}",fontweight='bold',fontsize=11,pad=10)
        ax.text(.05,.12,f"Prefix {c['committed_length']} | focus row {c['focus_row']} (0-based)\n"+('Identical current recipes: state control' if c['current_columns_identical'] else 'Whole-recipe intervention; donor state held fixed per row'),transform=ax.transAxes,fontsize=9)
    fig.suptitle('B570: six natural-state × current-recipe argmax tables',fontsize=16,y=.97)
    fig.text(.5,.025,'3 tasks × 2 rounds; cap128. Each entry is a token ID. All batch-row scores accompany this figure.\n12 full own-path shams; /72 columns are duplicate controls. No full counterfactual trajectory claim.',ha='center',fontsize=10)
    fig.subplots_adjust(top=.90,bottom=.11,hspace=.45,wspace=.30)
    for ext in ['svg','pdf']:fig.savefig(folder/f'argmax_cross.{ext}',metadata={'Creator':'HeteroSpec CPU raw recheck',**({'CreationDate':None,'ModDate':None} if ext=='pdf' else {'Date':None})})
    plt.close(fig)
    ps=list(csv.DictReader((OUT/'COST_TASK_PAIRS.csv').open()));tasks=sorted({p['task'] for p in ps if p['baseline']=='ordinary_R' and p['candidate']=='candidate'},key=lambda s:int(s.split('/')[1]));data=[]
    fig,axes=plt.subplots(2,1,figsize=(12,8),sharex=True)
    for ax,m,title in zip(axes,['generation_ms','whole_ms'],['Generation','Whole request']):
        for baseline,color,marker in [('ordinary_R','#185e91','o'),('matched_target','#bd5723','s')]:
            ys=[float(next(p for p in ps if p['task']==t and p['baseline']==baseline and p['candidate']=='candidate')['speed_'+m]) for t in tasks]
            ax.plot(range(len(tasks)),ys,label=f'{baseline} / candidate',color=color,marker=marker,markersize=5,linewidth=1.4)
            data.append(dict(timer=m,baseline=baseline,tasks=tasks,values=ys))
        ax.axhline(1,color='#555',linestyle='--',linewidth=1,label='Equal cost (1.0)');ax.set_ylim(0,1.06);ax.set_ylabel('Baseline ms / candidate ms');ax.set_title(title,loc='left',fontweight='bold');ax.grid(axis='y',alpha=.20);ax.legend(loc='upper right',fontsize=9,ncol=3)
    axes[-1].set_xticks(range(len(tasks)),[t.replace('MBPP/','') for t in tasks],rotation=45);axes[-1].set_xlabel('MBPP task ID')
    fig.suptitle('B570 qualified candidate: below ordinary R and matched target',fontsize=15)
    fig.text(.5,.015,'N=15 tasks; two paid repeats, task medians; cap128. >1 means candidate faster.\nE formal: 119/120 complete. Missing old N1 / MBPP400 / round1; old-N1 paired denominator N=14.',ha='center',fontsize=10)
    fig.tight_layout(rect=[0,.09,1,.95])
    for ext in ['svg','pdf']:fig.savefig(folder/f'qualified_speed.{ext}',metadata={'Creator':'HeteroSpec CPU raw recheck',**({'CreationDate':None,'ModDate':None} if ext=='pdf' else {'Date':None})})
    plt.close(fig)
    # Matplotlib's SVG path serialization leaves insignificant trailing spaces.
    for p in folder.glob('*.svg'):p.write_text('\n'.join(line.rstrip() for line in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    write('FIGURE_DATA.json',dict(argmax=[dict(case=c['case'],focus=c['focus']) for c in cases],speed=data))
    finish('figures');print('Rendered two exact SVG/PDF figures')
if __name__=='__main__':main()
