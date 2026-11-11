#!/usr/bin/env python3
"""Publication candidates at native MLSys widths. Matplotlib vector only."""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parents[1]
BLUE='#246488'; INK='#252A2D'; GREY='#6C7479'; LIGHT='#DCE2E5'; RULE='#CED3D6'
plt.rcParams.update({'font.family':'serif','font.serif':['STIXGeneral','DejaVu Serif'],
    'font.size':9,'axes.labelsize':9,'xtick.labelsize':8.5,'ytick.labelsize':9,
    'text.color':INK,'axes.labelcolor':INK,'axes.edgecolor':INK,
    'axes.linewidth':.65,'lines.linewidth':1.0,'pdf.fonttype':42,'ps.fonttype':42,
    'svg.fonttype':'path','svg.hashsalt':'heterospec-figures-v02','mathtext.fontset':'stix',
    'savefig.facecolor':'white','figure.facecolor':'white','hatch.linewidth':.45})

def df(name): return pd.read_csv(HERE/'data'/name,float_precision='round_trip')
def clean(ax):
    for s in ['top','right']: ax.spines[s].set_visible(False)
    ax.tick_params(width=.65,length=3,pad=3)
def canvas(w,h):
    f=plt.figure(figsize=(w,h));a=f.add_axes([0,0,1,1]);a.set(xlim=(0,w),ylim=(0,h));a.axis('off');return f,a
def text(ax,x,y,s,**kw): return ax.text(x,y,s,va='center',**kw)
def box(ax,x,y,w,h,**kw):
    p=Rectangle((x,y),w,h,linewidth=.7,edgecolor=INK,facecolor='white',**kw);ax.add_patch(p);return p
def arrow(ax,start,end,**kw):
    ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle='-|>',lw=.75,color=INK,shrinkA=1,shrinkB=1,**kw))

def save(f,i):
    for kind in ['pdf','svg','qa']: (HERE/kind).mkdir(exist_ok=True)
    f.canvas.draw(); renderer=f.canvas.get_renderer();bad=[]
    for obj in f.findobj(match=matplotlib.text.Text):
        if not obj.get_visible() or not obj.get_text():continue
        b=obj.get_window_extent(renderer)
        # Empty tick slots outside a trimmed axis are not drawn by Matplotlib.
        if b.width==0 or b.height==0:continue
        if b.x0 < -1 or b.y0 < -1 or b.x1>f.bbox.width+1 or b.y1>f.bbox.height+1:
            bad.append(obj.get_text())
    input_paths=sorted((HERE/'data').glob(f'figure{i}_*.csv'))
    if i==5: input_paths.append(HERE/'data/figure4_realized.csv')
    inputs={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in input_paths}
    receipt=dict(figure=i,width_in=float(f.get_figwidth()),height_in=float(f.get_figheight()),
        input_sha256=inputs,out_of_bounds_text=bad,font='STIXGeneral / STIX math (Times-compatible)' ,
        native_width='single column' if f.get_figwidth()<4 else 'double column',min_font_pt=8,
        render_backend='Matplotlib vector PDF/SVG')
    (HERE/f'qa/figure{i}_render.json').write_text(json.dumps(receipt,indent=2)+'\n')
    f.savefig(HERE/f'pdf/figure{i}.pdf',metadata={'Creator':'HeteroSpec reproducible figure scripts','CreationDate':None,'ModDate':None})
    f.savefig(HERE/f'svg/figure{i}.svg',metadata={'Date':None,'Creator':'HeteroSpec reproducible figure scripts'})
    plt.close(f)
    # Independent pass after EACH figure. No import of the extractor's numerical helpers.
    subprocess.run([sys.executable,str(HERE/'scripts/validate.py'),'--figure',str(i),'--require-outputs'],check=True)

def figure1():
    d=df('figure1_overview.csv');f,a=canvas(6.75,3.63)
    text(a,.10,3.43,'Local opportunity does not ensure end-to-end gain',fontsize=12,fontweight='bold')
    text(a,.10,3.10,'Observed case',fontsize=10,fontweight='bold')
    text(a,2.06,3.10,'Favorable local measurement',fontsize=10,fontweight='bold')
    text(a,4.64,3.10,'Realized outcome',fontsize=10,fontweight='bold')
    a.plot([.10,6.65],[2.94,2.94],color=INK,lw=.7)
    for idx,(_,r) in enumerate(d.iterrows()):
        y=2.62-idx*.59
        qualified=r.status=='qualified';color=BLUE if qualified else GREY
        case=['M4 · HumanEval30','M4 · representative 24Q','RTX 5070 Ti Laptop','358H · NPU draft'][idx]
        sub=['Preregistered, fixed k = 2','Frozen representative study','CUDA batched verification','Qualified Phase-3 path'][idx]
        text(a,.10,y+.06,case,fontsize=10,fontweight='bold')
        text(a,.10,y-.13,sub,fontsize=8.7,color=GREY)
        if idx<3:
            text(a,2.06,y+.06,rf'$V_2^{{\mathrm{{micro}}}}$ = {r.local_low:.3f}–{r.local_high:.3f}',fontsize=10)
            text(a,2.06,y-.14,'Shared Metal path; separate micro study' if idx<2 else 'Near one target-decode step',fontsize=8.6,color=GREY)
        else:
            text(a,2.06,y+.06,f'{r.local_high:.2f} vs {r.local_low:.2f} tokens/s',fontsize=10)
            text(a,2.06,y-.14,'NPU vs CPU · isolated, 8,192 tokens',fontsize=8.6,color=GREY)
        arrow(a,(4.29,y+.015),(4.52,y+.015))
        a.plot(4.68,y+.06,marker='o' if qualified else 's',ms=5,
               mec=color,mfc=color if qualified else 'white',mew=1)
        outcome=['Exact + profitable','Exact + negative','Correctness blocked','Exact + negative'][idx]
        text(a,4.82,y+.06,outcome,fontsize=10,fontweight='bold',color=color)
        detail='No admissible speedup' if not qualified else f"{float(r.speedup):.3f}× · {r.exact} exact"
        text(a,4.82,y-.14,detail,fontsize=9)
        if idx<3:a.plot([.10,6.65],[y-.31,y-.31],color=RULE,lw=.5)
    a.plot([.10,6.65],[.50,.50],color=INK,lw=.6)
    text(a,.10,.34,'Categorical cases, not a hardware ranking. Filled = qualified; open = blocked. Details and CIs: Figures 2–4.',fontsize=8.6)
    text(a,.10,.13,r'Micro cost ≠ complete target work; isolated throughput ≠ stateful cost. Speedups cover post-prefill decode.',fontsize=8.6)
    save(f,1)

def figure2():
    d=df('figure2_micro_cells.csv');f=plt.figure(figsize=(6.75,3.58))
    ax=f.add_axes([.327,.29,.37,.59]);clean(ax)
    ax.spines['left'].set_visible(False);ax.set_yticks([])
    ax.set(xlim=(.85,2.6),ylim=(-.6,4.65),xticks=[1,1.5,2,2.5])
    ax.set_xlabel(r'$V_2^{\mathrm{micro}}$ (one target decode = 1)',labelpad=7)
    for x in [1,2]:ax.axvline(x,color=RULE,lw=.65,zorder=0)
    labels=[('M4 Metal','prefix 512 / 2,048 / 8,192'),
            ('RTX batched','CUDA · ubatch = 2 · depth 0 / 256'),
            ('RTX serialized','CUDA · ubatch = 1 · depth 0 / 256'),
            ('B570 fast','Vulkan · context 512 / 2,048'),
            ('B570 serialized','Vulkan · ubatch = 1 · 512 / 2,048')]
    status=[('Qualified','Exact in tested cells'),('Blocked','Frozen workload gate failed'),
            ('Qualified control','Exact secondary control'),('Diagnostic · blocked','45/90 pairs exact'),
            ('Diagnostic · blocked','60/90 exact; still inadmissible')]
    for idx,((path,context),(s,sub)) in enumerate(zip(labels,status)):
        y=4-idx;x=d[d.path==path];lo=x.v2_micro.min();hi=x.v2_micro.max()
        qualified=x.status.iloc[0]=='qualified';color=BLUE if qualified else GREY
        marker='s' if 'serialized' in path else 'o'
        ax.plot([lo,hi],[y,y],color=color,lw=1.3,ls='-' if qualified else '--',zorder=2)
        ax.plot(x.v2_micro,[y]*len(x),ls='',marker=marker,ms=4.5,mew=.9,
                mec=color,mfc=color if qualified else 'white',zorder=3)
        ax.text((lo+hi)/2,y+.23,f'{lo:.3f}–{hi:.3f}',ha='center',fontsize=9,color=INK)
        yy=.29+(y+.6)/5.25*.59
        main={'RTX batched':'RTX 5070 Ti Laptop · batched','RTX serialized':'RTX 5070 Ti Laptop · serialized',
              'B570 fast':'B570 Vulkan · fast','B570 serialized':'B570 Vulkan · serialized'}.get(path,path)
        f.text(.018,yy+.016,main,fontsize=9.2,fontweight='bold',va='center')
        f.text(.018,yy-.032,context,fontsize=8.1,va='center',color=GREY)
        f.text(.724,yy+.012,s,fontsize=9.1,fontweight='bold',color=color,va='center')
        f.text(.724,yy-.035,sub,fontsize=8.5,va='center')
    f.text(.018,.947,'Execution path',fontweight='bold',fontsize=10)
    f.text(.347,.947,'Measured target-forward cost',fontweight='bold',fontsize=10)
    f.text(.724,.947,'Correctness qualification',fontweight='bold',fontsize=10)
    f.text(.018,.092,'Filled = qualified; open = blocked/diagnostic. Circles = batched/fast; squares = serialized.',fontsize=8.5)
    f.text(.018,.04,r'Ranges span tested contexts (not CIs); contexts are not fully matched. $V_2^{\mathrm{micro}} \ne R_{\mathrm{target}}$.',fontsize=8.5)
    save(f,2)

def figure3():
    d=df('figure3_workloads.csv');f=plt.figure(figsize=(3.25,2.4))
    ax=f.add_axes([.13,.245,.81,.55]);clean(ax);ax.spines['left'].set_visible(False)
    ax.set(xlim=(.72,1.50),ylim=(-.4,1.45),xticks=[.8,1,1.2,1.4]);ax.set_yticks([])
    ax.plot([1,1],[-.35,1.12],color=GREY,ls='--',lw=.8,zorder=0)
    for y,(_,r) in zip([1,0],d.iterrows()):
        ax.errorbar(r.speedup,y,xerr=[[r.speedup-r.ci_low],[r.ci_high-r.speedup]],
                    fmt='o',color=BLUE,ms=5,capsize=3,elinewidth=1.15)
        ax.text(.73,y+.3,'Representative 24Q' if y else 'Preregistered HumanEval30 · k = 2',fontsize=9.3,fontweight='bold',bbox=dict(facecolor='white',edgecolor='none',pad=.1))
        ax.text(.73,y-.23,f'{r.speedup:.3f}× [{r.ci_low:.3f}, {r.ci_high:.3f}]',fontsize=9,bbox=dict(facecolor='white',edgecolor='none',pad=.1))
        ax.text(1.485,y-.23,f'{int(r.exact_pairs)}/{int(r.pairs)} exact',ha='right',fontsize=8.5)
    ax.set_xlabel('Decode speedup (baseline / speculative)',labelpad=7)
    f.text(.025,.948,'M4 Metal: two frozen workload studies',fontweight='bold',fontsize=10)
    f.text(.025,.029,'95% prompt-bootstrap CIs; separate workload studies.',fontsize=8.5)
    save(f,3)

def figure4():
    iso=df('figure4_isolated.csv');real=df('figure4_realized.csv')
    f=plt.figure(figsize=(6.75,3.75))
    a=f.add_axes([.082,.285,.31,.56]);clean(a)
    xs=np.arange(3)
    for dev,marker,color,offset in [('CPU','o',INK,-.075),('NPU','D',BLUE,.075)]:
        d=iso[iso.device==dev].sort_values('context')
        a.errorbar(xs+offset,d.tokens_s,yerr=[d.tokens_s-d.ci_low,d.ci_high-d.tokens_s],
                   fmt=marker,color=color,ms=4,capsize=2,elinewidth=.8,label=dev)
        for x,(_,r) in zip(xs+offset,d.iterrows()):
            a.annotate(f'{r.tokens_s:.2f}',(x,r.tokens_s),xytext=(0,11 if dev=='NPU' else -14),
                       textcoords='offset points',ha='center',fontsize=8.5,color=color)
    a.set(xlim=(-.42,2.42),ylim=(0,109),xticks=xs,xticklabels=['512','2,048','8,192'],yticks=[0,30,60,90])
    a.set_ylabel('Steady-state draft tokens/s',labelpad=4);a.set_xlabel('Context tokens',labelpad=5)
    a.legend(loc='lower left',bbox_to_anchor=(.0,.015),frameon=False,ncol=2,fontsize=8.5,
             handletextpad=.35,columnspacing=1,borderpad=0)
    f.text(.04,.955,'A  Isolated drafting · Phase 1',fontweight='bold',fontsize=10.2)
    f.text(.04,.897,'Median, 5 repetitions; 95% bootstrap CI',fontsize=8.5)
    b=f.add_axes([.502,.285,.474,.56]);clean(b);b.spines['left'].set_visible(False)
    b.set(xlim=(0,33),ylim=(-.38,2.08),xticks=[0,10,20,30],yticks=[])
    b.set_xlabel('Post-prefill seconds per request',labelpad=5)
    # Shared baseline is an arithmetic mean, not a fabricated third speculative path.
    base=real.baseline_s.iloc[0]
    b.plot([0,base],[1.84,1.84],color=INK,lw=1.8)
    b.text(base+.5,1.84,f'{base:.2f} s baseline',va='center',fontsize=8.5)
    for y,(_,r) in zip([1.05,0],real.iterrows()):
        b.barh(y,r.draft_s,height=.39,color=BLUE,edgecolor=INK,lw=.5)
        b.barh(y,r.target_s,left=r.draft_s,height=.39,color=LIGHT,edgecolor=INK,lw=.5,hatch='///')
        b.barh(y,r.residual_s,left=r.draft_s+r.target_s,height=.39,color=INK,lw=0)
        b.text(0,y+.34,f'{r.device}  ·  GM speedup {r.headline_speedup:.3f}×',fontsize=9.2,fontweight='bold')
        b.text(r.total_s+.5,y,f'{r.total_s:.2f} s',fontsize=9,va='center',fontweight='bold')
        b.text(r.draft_s+r.target_s/2,y,f'{r.target_s:.2f} s\n{r.target_pct:.2f}%',ha='center',va='center',fontsize=8.5)
        if r.device=='NPU':
            b.text(r.draft_s/2,y,f'{r.draft_s:.2f} s\n{r.draft_pct:.2f}%',ha='center',va='center',fontsize=8.5,color='white')
        else:
            b.annotate(f'{r.draft_s:.2f} s · {r.draft_pct:.2f}%',xy=(r.draft_s/2,y-.2),xytext=(0,y-.49),
                       fontsize=8.3,ha='left',arrowprops=dict(arrowstyle='-',lw=.5,color=INK),annotation_clip=False)
    f.text(.485,.955,'B  Realized cost · Phase 3',fontweight='bold',fontsize=10.2)
    f.text(.485,.897,'90 requests/path; 90/90 exact on each path',fontsize=8.5)
    handles=[Rectangle((0,0),1,1,facecolor=BLUE,edgecolor=INK,lw=.5),
             Rectangle((0,0),1,1,facecolor=LIGHT,edgecolor=INK,lw=.5,hatch='///')]
    f.legend(handles,['Replay + proposal','Complete target side'],loc='center',bbox_to_anchor=(.718,.167),
             frameon=False,ncol=2,fontsize=8.5,handlelength=1.2,columnspacing=1.2)
    cpu,npu=real.iloc[0],real.iloc[1]
    f.text(.018,.109,f'Residual: CPU {cpu.residual_s*1000:.2f} ms ({cpu.residual_pct:.2f}%); NPU {npu.residual_s*1000:.2f} ms ({npu.residual_pct:.2f}%). Bars: arithmetic means; speedups: prompt GMs.',fontsize=8.3)
    f.text(.018,.061,'Replay and proposal share one timed call. Phase-1 steady-state throughput excludes the full-prefix state cost.',fontsize=8.3)
    f.text(.018,.014,f'Speedup 95% CIs: CPU [{cpu.ci_low:.3f}, {cpu.ci_high:.3f}]; NPU [{npu.ci_low:.3f}, {npu.ci_high:.3f}]. Initial prompt prefill is excluded from Phase 3.',fontsize=8.3)
    save(f,4)

def figure5():
    d=df('figure5_regimes.csv');real=df('figure4_realized.csv').set_index('device');f,a=canvas(6.75,4.1)
    # Aligned categorical matrix: no continuous coordinates and no inferred blocked speedups.
    cols=[1.59,3.33,5.18];ends=[3.18,5.03,6.68]
    text(a,.08,3.68,'Mechanism',fontweight='bold',fontsize=10)
    text(a,2.34,3.68,'Not admissible',ha='center',fontweight='bold',fontsize=10)
    text(a,4.92,3.68,'Correctness-qualified',ha='center',fontweight='bold',fontsize=10,color=BLUE)
    a.plot([3.33,6.66],[3.51,3.51],color=BLUE,lw=.8)
    text(a,2.34,3.33,'No admissible speed claim',ha='center',fontsize=9)
    text(a,4.15,3.33,r'Negative ($S<1$)',ha='center',fontsize=9)
    text(a,5.93,3.33,r'Profitable ($S>1$)',ha='center',fontsize=9)
    a.plot([.08,6.67],[3.12,3.12],color=INK,lw=.7)
    rows=[('Workload-conditioned',2.8),('Verification-constrained',2.22),
          ('Correctness-blocked',1.60),('Target-side dominated',.97),('State-interface bound',.42)]
    for mech,y in rows:
        label={'Workload-conditioned':'Workload\nconditioning','Verification-constrained':'Verification\nconstraint',
               'Correctness-blocked':'Correctness\nbarrier','Target-side dominated':'Target-side\ncost',
               'State-interface bound':'State-interface\ncost'}[mech]
        text(a,.08,y,label,fontsize=9.3,fontweight='bold',bbox=dict(facecolor='white',edgecolor='none',pad=.1))
        items=d[d.mechanism==mech]
        for _,r in items.iterrows():
            col=0 if r.admissibility=='blocked' else (1 if r.profitability=='negative' else 2)
            y0=y
            if mech=='Correctness-blocked': y0=y+(.135 if r['case']=='B570 fast' else -.135)
            x=cols[col];qualified=r.admissibility=='qualified'
            a.plot(x+.04,y0+.07 if mech!='Correctness-blocked' else y0,marker='o',ms=4.3,
                   mec=BLUE if qualified else GREY,mfc=BLUE if qualified else 'white',mew=.9)
            case={'M4 representative 24Q':'M4 representative 24Q [P]','M4 HumanEval30':'M4 HumanEval30 [P]',
                  'RTX batched':'RTX batched [M]','RTX serialized controls':'RTX serialized [S]',
                  'B570 fast':f"B570 fast: {r['exact']} [D]",'B570 serialized':f"B570 serialized: {r['exact']} [D]",
                  '358H CPU':'358H CPU [P/M]','358H NPU':'358H NPU [P/M]'}[r['case']]
            if mech=='Correctness-blocked':
                text(a,x+.14,y0,case,fontsize=8.6)
            else:
                text(a,x+.14,y0+.07,case,fontsize=9.1,fontweight='bold')
                sub={'M4 representative 24Q':f"{r['exact']} exact",'M4 HumanEval30':f"{r['exact']} exact",
                     'RTX batched':'Cheap micro path; gate fails','RTX serialized controls':'CPU→RTX / RTX→RTX; exact',
                     '358H CPU':f"{r['exact']}; target side {real.loc['CPU','target_pct']:.2f}%",
                     '358H NPU':f"{r['exact']}; replay + proposal {real.loc['NPU','draft_pct']:.2f}%"}[r['case']]
                text(a,x+.14,y0-.105,sub,fontsize=8.3)
        if y>.5: a.plot([.08,6.67],[y-.295,y-.295],color=RULE,lw=.5)
    text(a,.08,.11,'P primary · S secondary · M mechanism · D diagnostic. Fractions count exact token-ID pairs.',fontsize=8.2)
    text(a,.08,3.965,'Categorical regimes under the frozen correctness contract',fontsize=10.2,fontweight='bold')
    save(f,5)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--figure',type=int,choices=range(1,6));args=ap.parse_args()
    for i in ([args.figure] if args.figure else [2,4,5,1,3]): globals()[f'figure{i}']()
