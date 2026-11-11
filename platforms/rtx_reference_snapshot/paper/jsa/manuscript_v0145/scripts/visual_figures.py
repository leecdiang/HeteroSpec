"""ASV-inspired scientific figures; all quantitative inputs come from frozen exports.

Color is redundant with labels/shapes. Categorical token IDs are never subtracted.
Comparison ratios are not component costs. No model/runtime is invoked.
"""
from pathlib import Path
import hashlib, json, re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
BLUE='#426b8b'; OCHRE='#b07b43'; GREEN='#3e725e'; INK='#202629'; GRAY='#72787c'; LIGHT='#d9dfe1'
PALE_BLUE='#f1f5f8'; PALE_OCHRE='#fbf5ee'; PALE_GREEN='#f0f6f2'
plt.rcParams.update({'font.family':'STIXGeneral','mathtext.fontset':'stix','font.size':9,
 'axes.titlesize':10,'axes.labelsize':9,'xtick.labelsize':8.5,'ytick.labelsize':8.5,
 'axes.linewidth':.6,'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
 'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','svg.hashsalt':'HeteroSpec-v0142',
 'savefig.facecolor':'white','lines.linewidth':.9})

def canvas(h):
    fig=plt.figure(figsize=(7.2,h));return fig

def panel(fig,rect,title):
    ax=fig.add_axes(rect);ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    ax.text(0,1.035,title,weight='bold',fontsize=10,va='bottom',clip_on=False)
    return ax

def text(ax,x,y,s,**kw):
    return ax.text(x,y,s,ha=kw.pop('ha','center'),va=kw.pop('va','center'),fontsize=kw.pop('fontsize',9),**kw)

def arrow(ax,a,b,color=GRAY,**kw):
    ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',color=color,lw=.85,shrinkA=2,shrinkB=2,**kw))

def box(ax,x,y,w,h,s,color=GRAY,fill='white',fs=9):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.009,rounding_size=0.012',
                  edgecolor=color,facecolor=fill,linewidth=.7,clip_on=False))
    text(ax,x+w/2,y+h/2,s,fontsize=fs)

def divider(fig,x0,y0,x1,y1):
    fig.add_artist(Line2D([x0,x1],[y0,y1],transform=fig.transFigure,color=LIGHT,lw=.5))

def clean(ax):
    ax.spines[['top','right','left']].set_visible(False)
    ax.tick_params(axis='y',length=0)
    ax.grid(axis='x',color=LIGHT,lw=.45,zorder=0)
    ax.set_axisbelow(True)

def source(path):
    return dict(path=path,sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest())

def make_figures(d):
    results={}
    def save(fig,name,data):
        for ext in ['pdf','svg']:
            meta={'CreationDate':None,'ModDate':None} if ext=='pdf' else {'Date':None}
            fig.savefig(ROOT/'figures'/f'{name}.{ext}',metadata=meta)
        plt.close(fig);results[name]=data

    # FIGURE 1: distinguish state ownership, actual graph change, and topology guard.
    fig=canvas(4.2)
    a=panel(fig,[.025,.49,.43,.42],'(A) Preserve the stateful transaction')
    box(a,.02,.68,.40,.18,'Target KV +\npending state',BLUE,PALE_BLUE,8.8)
    box(a,.56,.68,.40,.18,'Draft KV +\nsampler state',OCHRE,PALE_OCHRE,8.8)
    box(a,.62,.37,.30,.17,'Propose',OCHRE)
    box(a,.05,.37,.39,.17,'Target verification',BLUE)
    arrow(a,(.76,.68),(.76,.54),OCHRE);arrow(a,(.22,.68),(.22,.54),BLUE)
    arrow(a,(.62,.455),(.44,.455),OCHRE)
    box(a,.16,.07,.66,.16,'Accept / correct / commit / rollback',GRAY,fs=8.8)
    arrow(a,(.245,.37),(.35,.23),BLUE)
    a.plot([.16,.0,.0,.20],[.15,.15,.96,.96],color=BLUE,lw=.7)
    arrow(a,(.20,.96),(.20,.86),BLUE)
    a.plot([.82,1,1,.77],[.15,.15,.96,.96],color=OCHRE,lw=.7)
    arrow(a,(.77,.96),(.77,.86),OCHRE)
    text(a,.50,-.07,'Separate target and draft ownership; no state transplant\nin the measured RTX candidate.',fontsize=8.5,color=GRAY)
    divider(fig,.48,.44,.48,.93)
    b=panel(fig,[.51,.49,.465,.42],'(B) Move query columns into the batch axis')
    text(b,.22,.88,'Ordinary query view',color=BLUE)
    text(b,.78,.88,'Constrained view',color=GREEN)
    for i in range(4):
        b.add_patch(Rectangle((.08+i*.065,.49),.057,.22,facecolor=PALE_BLUE,edgecolor=BLUE,lw=.65))
        text(b,.108+i*.065,.60,str(i+1),fontsize=8,color=BLUE)
    text(b,.20,.35,r'$(d,q,h,1)$',fontsize=11)
    arrow(b,(.38,.60),(.59,.60),GREEN)
    text(b,.48,.75,'view',fontsize=8.5,color=GREEN)
    for i in range(4):
        x=.66+i*.058;y=.47+i*.047
        b.add_patch(Rectangle((x,y),.048,.22,facecolor=PALE_GREEN,edgecolor=GREEN,lw=.65))
        text(b,x+.024,y+.11,str(i+1),fontsize=8,color=GREEN)
    text(b,.78,.35,r'$(d,1,h,q)$',fontsize=11)
    text(b,.5,.12,'K/V broadcast across query batches',fontsize=9)
    text(b,.5,-.04,r'Mask: $(n_{\rm KV},q,1,1)\;\rightarrow\;(n_{\rm KV},1,1,q)$',fontsize=9)
    text(b,.5,-.19,'Projection, output projection and FFN remain batched.',fontsize=8.5,color=GRAY)
    divider(fig,.025,.375,.975,.375)
    c=panel(fig,[.025,.075,.95,.23],'(C) Select the graph by role and phase')
    for x,y,s,col in [(.005,.48,'Target prefill\nbit 1',BLUE),(.185,.48,'Target continuation\nbit 2',BLUE),
                       (.005,.02,'Draft prefill\nbit 4',OCHRE),(.185,.02,'Draft continuation\nbit 8',OCHRE)]:
        box(c,x,y,.16,.36,s,col,fs=8.6)
    box(c,.41,.20,.15,.44,'Scope\nguard',GRAY)
    arrow(c,(.355,.65),(.41,.52));arrow(c,(.355,.20),(.41,.38))
    box(c,.63,.20,.15,.44,'Graph flag\nactive / inactive',GREEN,PALE_GREEN,8.6)
    arrow(c,(.56,.42),(.63,.42),GREEN)
    box(c,.85,.20,.14,.44,'Reuse only if\nflag matches',GRAY,fs=8.6)
    arrow(c,(.78,.42),(.85,.42),GREEN)
    fig.text(.50,.018,'Implemented scope: Qwen3, non-flash attention, one KV stream; see Section 5 for guards.',ha='center',fontsize=8.5,color=GRAY)
    save(fig,'figure_1_architecture',dict(kind='implementation schematic; numbered query tiles illustrative',
        sources=[source('source_records/benchmarks/rtx_consistency_contract_v1/query_batch_patch.py'),source('source_records/benchmarks/rtx_consistency_phase2/scope_patch.py')],
        query_before=['d','q','h',1],query_after=['d',1,'h','q'],no_generated_observations=True))

    # FIGURE 2: observed categorical decisions, not numeric effect sizes.
    fig=canvas(4.15)
    fig.text(.025,.965,'Hold the committed prefix fixed; cross natural donor state with the current recipe.',fontsize=9,color=GRAY)
    order=[0,1,4,2,3]
    titles=['(A) Current-path effect','(B) State-path interaction','(C) Retained-state effect',
            '(D) Whole-recipe interaction','(E) Whole-recipe interaction']
    for idx,j in enumerate(order):
        row,col=divmod(idx,3);x=.035+col*.325;y=.55 if row==0 else .105
        a=panel(fig,[x,y,.29,.32],titles[idx]);c=d['crosses'][j];m=c['matrix']
        text(a,.55,.91,c['platform']+' '+c['task'].replace('HumanEval/','HE/'),fontsize=9,color=GRAY)
        for r in range(2):
            for k in range(2):
                xx=.30+k*.40;yy=.30+(1-r)*.30
                same=m[r][k]==m[0][0];color=BLUE if same else OCHRE
                a.add_patch(Rectangle((xx-.13,yy-.09),.26,.18,facecolor='white',edgecolor=color,lw=.8))
                text(a,xx,yy,str(m[r][k]),fontsize=10,color=color)
            text(a,.105,.30+(1-r)*.30,c['rows'][r],fontsize=9)
        labels=c['columns']
        for k in range(2):text(a,.30+k*.40,.065,labels[k].replace(' recipe','\nrecipe'),fontsize=8.5)
        if idx==0:
            for yy in [.30,.60]:arrow(a,(.44,yy),(.56,yy),OCHRE)
        elif idx==2:
            for xx in [.30,.70]:arrow(a,(xx,.50),(xx,.405),OCHRE)
        else:
            rr=next(r for r in range(2) if m[r][0]!=m[r][1]);yy=.30+(1-rr)*.30
            arrow(a,(.44,yy),(.56,yy),OCHRE)
        text(a,.005,.75,'Donor',fontsize=8,color=GRAY,ha='left')
    f=panel(fig,[.685,.105,.285,.32],'(F) Continue beyond a local check')
    text(f,.5,.91,'B570: same-state forks',color=GRAY)
    box(f,.05,.49,.90,.22,'Immediate decision changes: 0 / 72',BLUE,fs=8.7)
    arrow(f,(.5,.49),(.5,.34),GRAY)
    box(f,.05,.08,.90,.22,'Downstream changes: 18 / 72',OCHRE,fs=8.7)
    text(f,.50,-.075,'Later alternate blocks remain UB128.',fontsize=8.3,color=GRAY)
    divider(fig,.345,.095,.345,.90);divider(fig,.67,.095,.67,.90);divider(fig,.035,.50,.97,.50)
    fig.text(.5,.015,'IDs are categorical; colors indicate equality within a case only. Own-path shams reproduce native decisions.',ha='center',fontsize=8.5)
    report='source_records/benchmarks/b570_partition_intervention_v1/DELIVERY_REPORT.md'
    rs=(ROOT/report).read_text();assert '72 eligible forks' in rs and '18 executions on 6 prompts' in rs
    save(fig,'figure_2_natural_crosses',dict(cases=[d['crosses'][j] for j in order],immediate_changed=0,downstream_changed=18,forks=72,
        downstream_scope='frozen continuation policy; later alternate target blocks remain UB128, not isolated-block aftereffect',report=source(report)))

    # FIGURE 3: full factorial alongside independently measured geometry boundary.
    fig=canvas(3.85)
    a=fig.add_axes([.065,.16,.57,.67])
    fig.text(.025,.94,'(A) Locate a sufficient phase scope',weight='bold',fontsize=10)
    fig.text(.33,.88,'Constraints enabled                  Full-response match',ha='center',fontsize=8.5,color=GRAY)
    maskdata=[]
    for c0 in d['a1']:
        r=c0['mask'];bits=[bool(r&bit) for bit in [1,2,4,8]];passes=[c0['task_matches'][p] for p in d['probes']]
        if r==3:a.add_patch(Rectangle((-.52,r-.48),8.13,.96,facecolor=PALE_GREEN,edgecolor=GREEN,lw=.9,zorder=0))
        for j,v in enumerate(bits):
            a.scatter(j,r,marker='s',s=20,facecolors=(BLUE if v else 'white'),edgecolors=(BLUE if v else LIGHT),linewidths=.6)
        for j,v in enumerate(passes,4):
            a.scatter(j,r,marker='o' if v else 'x',s=19 if v else 21,color=GREEN if v else OCHRE,linewidths=.75)
        if c0['qualifies']:a.text(7.52,r,'*' if r==3 else '+',color=GREEN,va='center',ha='center',weight='bold',fontsize=11)
        maskdata.append(dict(mask=r,bits=bits,probe_passes=passes,qualifies=c0['qualifies']))
    a.axvline(3.5,color=LIGHT,lw=.6)
    a.set(xlim=(-.5,7.8),ylim=(15.6,-.7));a.set_xticks(range(8),['T-P','T-C','D-P','D-C','/15','/18','/25','/31'])
    a.xaxis.tick_top();a.tick_params(length=0,pad=4);a.set_yticks(range(16),[f'{i:02}' for i in range(16)],fontsize=8)
    a.set_ylabel('Phase mask',fontsize=9,labelpad=7)
    for s in a.spines.values():s.set_visible(False)
    fig.text(.065,.075,'T / D: target / draft; P / C: prefill / continuation',fontsize=8.3)
    fig.text(.065,.035,'Filled square: enabled.  * minimal mask 3; + passing supersets',fontsize=8.3,color=GREEN)
    divider(fig,.645,.075,.645,.95)
    b=panel(fig,[.68,.14,.29,.72],'(B) Recheck wider geometry')
    text(b,.52,.88,'Full-panel output qualification',fontsize=8.5,color=GRAY)
    caps=[128,256,512];ks=[1,3,5,7];ubs=[2,4,6,8]
    report='source_records/benchmarks/rtx_closeout_bcd/REPORT.md';content=(ROOT/report).read_text()
    geometry=[]
    for i,(k,ub) in enumerate(zip(ks,ubs)):
        text(b,.01,.64-i*.135,f'{k} / {ub}',fontsize=9,ha='left')
        for j,cap in enumerate(caps):
            pattern=rf'^\| {k} / {ub} \| {cap} \| (.*?) \| (.*?) \| (通过|失败) \|$'
            match=re.search(pattern,content,re.M);assert match,(k,cap)
            ok=match[3]=='通过';geometry.append(dict(k=k,UB=ub,cap=cap,qualifies=ok,source='source-bound report table'))
            b.scatter(.40+j*.25,.64-i*.135,marker='o' if ok else 'x',s=30,color=GREEN if ok else OCHRE,linewidths=.9)
    text(b,.01,.79,r'$k$ / UB',fontsize=9,ha='left')
    for j,cap in enumerate(caps):text(b,.40+j*.25,.79,str(cap),fontsize=9)
    b.plot([0,.97],[.73,.73],color=LIGHT,lw=.6)
    text(b,.49,.08,'11 inputs; fresh references at each cap.\nMBPP/229 fails at UB6 and UB8.',fontsize=8.5)
    text(b,.49,-.045,'Cap 512 is a limit; observed length ≤ 261.',fontsize=8.1,color=GRAY)
    fig.text(.68,.025,'● match     × failure     (two repeats)',fontsize=8.2,color=GRAY)
    save(fig,'figure_3_phase_matrix',dict(factorial=maskdata,geometry=geometry,geometry_source=source(report),
        scope='geometry changes k and UB jointly; not the fixed-UB width cost experiment'))

    # FIGURE 4: comparator construction, then measured ratios. Never additive costs.
    fig=canvas(3.7)
    a=panel(fig,[.03,.69,.94,.22],'(A) Separate the two design decisions')
    box(a,.015,.15,.245,.57,'R: ordinary target only\nmask 0 / UB1',GRAY,fs=9)
    box(a,.385,.15,.245,.57,'M: constrained target only\nmask 3 / UB4',BLUE,PALE_BLUE,9)
    box(a,.755,.15,.23,.57,'C: constrained speculation\nmask 3 / UB4 / k = 3',OCHRE,PALE_OCHRE,8.8)
    arrow(a,(.265,.42),(.38,.42),BLUE);arrow(a,(.635,.42),(.75,.42),OCHRE)
    text(a,.322,.87,'Change target path',fontsize=8.2,color=BLUE)
    text(a,.695,.87,'Add draft',fontsize=8.2,color=OCHRE)
    comps=[('scalar_reference','target_scopes','Deployment  R/C',GRAY,'D'),
           ('scalar_reference','matched_target','Target path  R/M',BLUE,'s'),
           ('matched_target','target_scopes','Draft increment  M/C',OCHRE,'o')]
    costdata=[]
    for rect,t,ttl in [([.24,.245,.29,.335],'generation','(B) Generation'),([.66,.245,.30,.335],'whole','(C) Resident request')]:
        ax=fig.add_axes(rect);clean(ax);ax.axvline(1,color=GRAY,lw=.75,ls='--')
        for y,(base,cand,label,col,marker) in enumerate(comps):
            s=next(s for s in d['summaries'] if s['timer']==t and s['baseline']==base and s['candidate']==cand)
            v=s['task_median_gm'];lo,hi=s['descriptive_task_bootstrap_95_linear']
            ax.errorbar(v,y,xerr=[[v-lo],[hi-v]],fmt=marker,ms=4.7,capsize=2,color=col,lw=.8,zorder=4)
            ax.annotate(f'{v:.3f}×',(v,y),xytext=(0,9),textcoords='offset points',ha='center',fontsize=9,color=col)
            costdata.append(dict(timer=t,baseline=base,candidate=cand,ratio=v,interval=[lo,hi]))
        ax.set_ylim(2.6,-.65);ax.set_title(ttl,loc='left',weight='bold',fontsize=10,pad=12)
        ax.set_xlim((.975,1.255) if t=='generation' else (.95,1.91))
        ax.set_yticks(range(3),[r[2] for r in comps] if t=='generation' else ['R/C','R/M','M/C'])
        ax.set_xlabel('Baseline / compared-path time',fontsize=8.5)
    divider(fig,.59,.17,.59,.61)
    fig.text(.5,.073,r'Request ratios: $1.742 \simeq 1.683 \times 1.035$; most deployment gain exists without a draft.',ha='center',fontsize=9)
    fig.text(.5,.025,'Different timer intervals and x-axis ranges; ratios are multiplicative comparisons, not component costs.',ha='center',fontsize=8.5,color=GRAY)
    save(fig,'figure_4_paid_cost',dict(comparisons=costdata,estimator='GM of 24 task ratios from four-repetition absolute-time medians',
        intervals='descriptive task-bootstrap 95%, linear quantiles',path_settings={'R':[0,1],'M':[3,4],'C':[3,4,3]}))

    # FIGURE 5: all task pairs and all rounds; shapes encode direction per timer.
    vals={t:{task:d['med'][t,task,'matched_target']/d['med'][t,task,'target_scopes'] for task in d['tasks']} for t in ['generation','whole']}
    order=sorted(d['tasks'],key=lambda task:(vals['whole'][task],task))
    fig=canvas(4.65)
    for rect,t,ttl,col in [([.07,.23,.28,.62],'generation','(A) Generation',BLUE),([.405,.23,.28,.62],'whole','(B) Resident request',OCHRE)]:
        ax=fig.add_axes(rect);clean(ax);ax.axvline(1,color=GRAY,lw=.75,ls='--')
        v=[vals[t][task] for task in order];g=float(np.exp(np.mean(np.log(v))))
        for i,value in enumerate(v):
            ax.scatter(value,i,marker='o' if value>1 else '<',s=18,facecolors=col if value>1 else 'white',edgecolors=col,lw=.8,zorder=3)
        ax.axvline(g,color=col,lw=.6,ls=':')
        ax.set(xlim=(.80,1.48),ylim=(23.7,-.7));ax.set_xticks([.8,1,1.2,1.4])
        ax.set_yticks(range(24),[task.split('/')[-1] for task in order] if t=='generation' else ['']*24,fontsize=8)
        ax.set_title(ttl,loc='left',weight='bold',fontsize=10,pad=23)
        ax.text(.5,1.03,f'{sum(x>1 for x in v)}/24 faster; GM {g:.3f}',ha='center',transform=ax.transAxes,fontsize=9,color=col)
        ax.set_xlabel('Matched / speculative time',fontsize=8.5)
        if t=='generation':ax.set_ylabel('MBPP task (shared request-sorted order)',fontsize=8.5)
    divider(fig,.715,.14,.715,.94)
    ax=fig.add_axes([.80,.51,.17,.34]);clean(ax);ax.axvline(1,color=GRAY,lw=.75,ls='--')
    s=next(s for s in d['summaries'] if s['timer']=='whole' and s['baseline']=='matched_target' and s['candidate']=='target_scopes')
    rounds=s['rounds']
    for i,r in enumerate(rounds):
        v=r['gm'];ax.scatter(v,i,marker='o' if v>1 else '<',s=25,facecolors=OCHRE if v>1 else 'white',edgecolors=OCHRE,lw=.9,zorder=3)
        ax.annotate(f'{v:.3f}',(v,i),xytext=(0,10),textcoords='offset points',ha='center',fontsize=8.5)
    ax.set(xlim=(.91,1.075),ylim=(3.6,-.65));ax.set_yticks(range(4),['1','2','3','4']);ax.set_xticks([.94,1,1.06]);ax.set_ylabel('Round',fontsize=8.5)
    ax.set_title('(C) Request rounds',weight='bold',fontsize=10,pad=23,loc='center');ax.set_xlabel('Matched / speculative',fontsize=8)
    fig.text(.875,.32,'Round 2 reverses\nthe aggregate direction.',ha='center',fontsize=9,color=OCHRE)
    fig.text(.875,.21,'24 task pairs per round;\nno session-level interval\nis inferred.',ha='center',fontsize=8.5,color=GRAY)
    fig.text(.50,.075,'Filled circles: faster     Open left triangles: slower     Dashed: parity     Dotted: task-median GM',ha='center',fontsize=8.5)
    fig.text(.50,.022,'A and B share the same x-axis scale and task order; C reports round GMs, not task-median aggregation.',ha='center',fontsize=8.4,color=GRAY)
    save(fig,'figure_5_task_variation',dict(order=order,ratios=vals,rounds=rounds,
        direction_encoding='independently per timer: filled circle if >1, open left triangle if <1',
        task_panels_same_scale=True,rounds_have_no_fabricated_intervals=True))
    return results
