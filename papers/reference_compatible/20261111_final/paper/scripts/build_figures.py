"""Publication figures from immutable evidence projections.

Every statistical export has one axis. TeX places the two width panels together.
ASV colors and type are retained; hierarchy uses position, labels and marker fill.
No source values, estimands, confidence bounds or cohorts are changed here.
"""
from pathlib import Path
import json, math, hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, transforms
P=Path(__file__).resolve().parents[1]
D=json.loads((P/'generated/analysis.json').read_text())
ROOT_POINTS=json.loads((P/'data_added/application_root_ratios.json').read_text())['studies']
F=P/'figures'; F.mkdir(exist_ok=True)
B='#3F6C9B'; G='#4F7F5F'; O='#B8753B'; OT='#8C552A'
GRAY='#62696D'; RULE='#D4D7D9'; INK='#202326'; LIGHT='#A2A9AE'; PALE='#F4F5F5'
font=Path('/usr/share/fonts/opentype/urw-base35/P052-Roman.otf')
for weight in ['Roman','Italic','Bold','BoldItalic']:
    candidate=font.with_name('P052-'+weight+'.otf')
    if candidate.exists(): font_manager.fontManager.addfont(str(candidate))
family=font_manager.FontProperties(fname=str(font)).get_name() if font.exists() else 'STIXGeneral'
plt.rcParams.update({'font.family':family,'font.size':8.4,'axes.labelsize':8.5,
 'xtick.labelsize':8,'ytick.labelsize':8.3,'axes.linewidth':.55,'axes.edgecolor':GRAY,
 'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
 'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,
 'svg.fonttype':'none','figure.facecolor':'white','savefig.facecolor':'white',
 'mathtext.fontset':'stix','axes.unicode_minus':True})
manifest=[]; layout=[]

def canvas(w,h,l=.25,r=.85,b=.18,t=.88):
    fig=plt.figure(figsize=(w,h));ax=fig.add_axes([l,b,r-l,t-b]);return fig,ax

def base(ax):
    ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0)
    ax.grid(axis='x',color=RULE,lw=.45);ax.set_axisbelow(True)

def rowtext(fig,ax,x,y,text,**kw):
    tr=transforms.blended_transform_factory(fig.transFigure,ax.transData)
    return ax.text(x,y,text,transform=tr,clip_on=False,**kw)

def interval(ax,r,ci,y,color,marker='D',hollow=False):
    ax.plot(ci,[y,y],color=color,lw=1.35,zorder=3,solid_capstyle='round')
    for endpoint in ci: ax.plot([endpoint,endpoint],[y-.075,y+.075],color=color,lw=.7,zorder=3)
    ax.scatter(r,y,marker=marker,s=27,facecolors='white' if hollow else color,
               edgecolors=color,linewidths=.9,zorder=4)

def equal_line(ax,x=1):
    ax.axvline(x,color=GRAY,lw=.85,ls=(0,(3,2)),zorder=1)

def save(fig,name,desc):
    fig.canvas.draw();renderer=fig.canvas.get_renderer();fw,fh=fig.canvas.get_width_height()
    outside=[];boxes=[]
    for text in fig.findobj(matplotlib.text.Text):
        if not text.get_visible() or not text.get_text():continue
        bb=text.get_window_extent(renderer)
        # Empty tick labels can have coordinates outside the displayed axes; visible text cannot.
        boxes.append({'text':text.get_text(),'bbox_px':[float(bb.x0),float(bb.y0),float(bb.x1),float(bb.y1)]})
        if bb.x0<-.5 or bb.y0<-.5 or bb.x1>fw+.5 or bb.y1>fh+.5:outside.append(text.get_text())
    layout.append({'figure':name,'text_outside_canvas':outside,'text_boxes':boxes})
    for ext in ['pdf','svg','png']:
        if ext=='pdf':
            with matplotlib.rc_context({'pgf.texsystem':'pdflatex','pgf.rcfonts':False,
                 'pgf.preamble':r'\usepackage[T1]{fontenc}\usepackage{amssymb}\usepackage{mathpazo}'}):
                fig.savefig(F/(name+'.pdf'),backend='pgf')
        else:fig.savefig(F/(name+'.'+ext),dpi=260)
    manifest.append({'file':name,'size_in':[float(fig.get_figwidth()),float(fig.get_figheight())],
      'semantics':desc,'axis_count':len(fig.axes),
      'analysis_sha256':hashlib.sha256((P/'generated/analysis.json').read_bytes()).hexdigest(),
      'added_root_points_sha256':hashlib.sha256((P/'data_added/application_root_ratios.json').read_bytes()).hexdigest()})
    plt.close(fig)

# Fig.3: models form groups; fixed control, estimate and numeric reduction are separate columns.
fig,ax=canvas(7.12,3.55,.32,.835,.17,.875)
rows=[[13.0,12.1,11.2,10.3],[8.45,7.55,6.65,5.75],[3.90,3.0,2.1,1.2]]
model_names=['Qwen3-8B','Qwen3-14B','Llama-8B']
labels=['Whole · loop4','Whole · packed','Local · loop4','Local · packed']
for i,a in enumerate(D['applications']):
    ys=rows[i];head=ys[0]+.72
    rowtext(fig,ax,.018,head,model_names[i]+'  /  '+str(a['roots'])+' roots',ha='left',va='center',fontsize=8.8,fontweight='bold')
    mean_m=a['means'][a['best_fixed_M']];mean_d=a['means']['L_P_D4']
    rowtext(fig,ax,.355,head,f'Fastest M {mean_m:.3f} s  →  D4 {mean_d:.3f} s',ha='left',va='center',fontsize=8.0,color=GRAY,bbox={'facecolor':'white','edgecolor':'none','pad':1.3})
    for j,y in enumerate(ys):
        r=a['reported_ratios'][j];ci=a['reported_intervals'][j]
        vals=np.asarray(ROOT_POINTS[i]['ratios'][j])
        ax.scatter(vals,y+np.linspace(-.16,.16,len(vals)),s=7,c=LIGHT,alpha=.85,zorder=2,linewidths=0)
        interval(ax,r,ci,y,B)
        rowtext(fig,ax,.065,y,labels[j],ha='left',va='center',fontsize=8.3)
        rowtext(fig,ax,.982,y,f'{100*(1-r):.1f}%',ha='right',va='center',fontsize=8.7,color=B)
for y in [9.55,5.00]:
    ax.plot([.54,1.055],[y,y],color=RULE,lw=.6)
equal_line(ax);ax.set(xlim=(.54,1.055),ylim=(.55,14.25),xticks=[.6,.7,.8,.9,1],yticks=[])
base(ax);ax.set_xlabel('LOCAL-packed D4 / fixed target-only service time',labelpad=5)
fig.text(.018,.963,'Complete resident requests · Linux / A5000',fontsize=9.2,fontweight='bold')
fig.text(.065,.902,'Fixed target-only control',fontsize=8,color=GRAY)
fig.text(.982,.902,'Time reduction',fontsize=8,color=GRAY,ha='right')
fig.text(.815,.902,'1 = equal time',fontsize=7.8,color=GRAY,ha='right')
fig.text(.32,.016,'Faint points: task-root ratios; lower values use less time',fontsize=8,color=GRAY)
save(fig,'service_controls','All12 fixed target-onlyM contrasts and all176 published root ratios across3 separate Linux deployments; same source99% adjusted intervals and total-ratio estimates. Rounded percentage reductions; all six absolute means in TableS1. No minimum-selection significance test.')

# Fig.4: the scientific factors are the hierarchy; uncertain local estimates are hollow/neutral.
fig,ax=canvas(7.12,3.62,.405,.835,.20,.875)
ys=[[9.4,8.5],[7.2,6.3],[4.25,3.35],[2.05,1.15]]
fixed=['loop4 fixed','packed fixed','whole fixed','local fixed']
for j in range(4):
    for mi,model in enumerate(['8B','14B']):
        y=ys[j][mi];r=D['factors'][model]['all_fixed_controls'][j]
        vals=np.asarray(r['root_ratios']);ci=r['interval'];supported=ci[1]<1 or ci[0]>1
        color=(G if j<2 else B) if supported else GRAY
        ax.scatter(vals,y+np.linspace(-.17,.17,len(vals)),s=8,c=LIGHT,alpha=.85,zorder=2,linewidths=0)
        interval(ax,r['total_ratio'],ci,y,color,marker='D' if mi==0 else 's',hollow=not supported)
        rowtext(fig,ax,.298,y,model,ha='left',va='center',fontsize=8.3)
        rowtext(fig,ax,.982,y,f"{100*(1-r['total_ratio']):.2f}%",ha='right',va='center',fontsize=8.7,color=color)
    rowtext(fig,ax,.065,np.mean(ys[j]),fixed[j],ha='left',va='center',fontsize=8.4)
rowtext(fig,ax,.018,10.35,'CUT SCOPE   Local / whole',ha='left',va='center',fontsize=8.6,fontweight='bold')
rowtext(fig,ax,.018,5.20,'PROJECTION   Packed / loop4',ha='left',va='center',fontsize=8.6,fontweight='bold')
for y in [7.85,2.70]:ax.axhline(y,color=RULE,lw=.45)
equal_line(ax);ax.set(xlim=(.974,1.007),ylim=(.45,10.9),xticks=[.98,.99,1],yticks=[]);base(ax)
ax.set_xlabel('Service-time ratio at the fixed factor',labelpad=4)
fig.text(.018,.966,'Balanced attribution · 16 roots per model',fontsize=9.2,fontweight='bold')
fig.text(.982,.906,'Point reduction',fontsize=8,color=GRAY,ha='right')
fig.text(.817,.906,'1 = equal time',fontsize=7.8,color=GRAY,ha='right')
fig.text(.018,.102,'Faint points: all roots. Hollow markers: interval includes 1.',fontsize=8,color=GRAY)
fig.text(.018,.045,'Interaction: 8B 1.00070; 14B 1.00170 (mild attenuation; details in Supplement S3).',fontsize=8,color=GRAY)
save(fig,'factorial','All8 direct factor contrasts and all16 root ratios each. Source99% family-adjusted intervals and total-ratio point estimates; neutral hollow markers when CI includes1. Root-geometric interaction remains separately identified and fully reported in SupplementS3.')

# Fig.5: retain six arms and all root means, with direct fixed-scope reductions.
fig,ax=canvas(3.50,3.15,.37,.82,.18,.78)
q32=D['q32'];qa=['W_REF1L_M','W_REF1G_M','L_REF1L_M','L_REF1G_M','W_REF1L_D4','L_REF1G_D4']
ql=['Whole · loop','Whole · group','Local · loop','Local · group','Whole · loop','Local · group']
yvals=[5.35,4.45,3.55,2.65,.65,-.25]
for a,label,y in zip(qa,ql,yvals):
    v=q32['means'][a];col=B if 'REF1G' in a and a.endswith('_M') else (O if a.endswith('D4') else GRAY)
    rv=[r[a]/4 for r in q32['root_sums'].values()]
    ax.scatter(rv,[y+.13]*4,s=10,c=LIGHT,zorder=2,linewidths=0)
    ax.scatter(v,y,marker='s' if a.startswith('L') else 'o',s=27,color=col,zorder=3)
    rowtext(fig,ax,.018,y,label,ha='left',va='center',fontsize=8.0)
    rowtext(fig,ax,.985,y,f'{v:.3f}',ha='right',va='center',fontsize=8.3,color=col)
# Keep the fastest measured M visible as a reference within the speculative group.
best=q32['means']['L_REF1G_M']
ax.plot([best,best],[-.68,1.20],color=GRAY,lw=.8,ls=(0,(2,2)),zorder=1)
rowtext(fig,ax,.018,6.10,'Ordinary generation (M)',ha='left',va='center',fontsize=8.4,fontweight='bold')
rowtext(fig,ax,.018,1.54,'Speculative (D4)',ha='left',va='center',fontsize=8.4,fontweight='bold')
rowtext(fig,ax,.985,1.54,f'Grouped D4: +{100*(q32["means"]["L_REF1G_D4"]/best-1):.2f}% vs M',ha='right',va='center',fontsize=7.4,color=OT)
ax.axhline(2.05,color=RULE,lw=.6)
ax.set(xlim=(6.2,11.25),ylim=(-.8,6.55),xticks=[7,9,11],yticks=[]);base(ax)
ax.set_xlabel('Resident service (s / request)',labelpad=2)
fig.text(.018,.967,'32B mixed Q4 · full request costs',fontsize=8.8,fontweight='bold')
fig.text(.018,.903,'Group versus graph-level column loop',fontsize=8.0,color=GRAY)
fig.text(.018,.846,f'Time saved: whole {100*(1-q32["means"]["W_REF1G_M"]/q32["means"]["W_REF1L_M"]):.2f}%  /  local {100*(1-q32["means"]["L_REF1G_M"]/q32["means"]["L_REF1L_M"]):.2f}%',fontsize=8.4,color=B)
fig.text(.985,.805,'Mean (s)',fontsize=7.8,color=GRAY,ha='right')
fig.text(.018,.022,'Faint points: four root means; descriptive.',fontsize=7.7,color=GRAY)
save(fig,'mixed_q4','All6 complete-service means and all4 exposed-root means. Both fixed-scope group/graph-loop reductions explicitly labelled. GroupedD4 versus fastestM +14% remains visible; graph-level control is not backend-loop. No population CI.')

# Fig.6: explicit equality reference, shape redundancy, all12 measured coordinates.
fig,ax=canvas(3.50,3.15,.255,.96,.20,.81)
coords={x['cell']:x for x in D['vulkan_geometry']}
for cap,ybase in [(1024,4.85),(4096,1.65)]:
    for qi,q in enumerate([2,4,32]):
        y=ybase-qi*.85
        for condition,dy,color,marker in [('crossing',-.13,G,'D'),('inside',.13,O,'o')]:
            r=coords[f'C{cap}-q{q}-{condition}'];lo,hi=min(r['paired_ratios']),max(r['paired_ratios'])
            ax.plot([lo,hi],[y+dy]*2,color=color,lw=1,zorder=2)
            ax.scatter(r['ratio'],y+dy,marker=marker,s=22,facecolor=color if condition=='crossing' else 'white',edgecolor=color,lw=.9,zorder=3)
        rowtext(fig,ax,.125,y,f'q{q}',ha='right',va='center',fontsize=8.2)
    head=ybase+.69
    rowtext(fig,ax,.018,head,f'C{cap} · prefix near {768 if cap==1024 else 3072}',ha='left',va='center',fontsize=8.2,fontweight='bold',bbox={'facecolor':'white','edgecolor':'none','pad':1})
equal_line(ax);ax.set(xlim=(.50,1.115),ylim=(-.55,6.0),xticks=[.6,.8,1.0],yticks=[]);base(ax)
ax.axhline(2.46,color=RULE,lw=.6)
ax.set_xlabel('LOCAL / whole append time',labelpad=4)
fig.text(.018,.966,'Boundary geometry changes the outcome',fontsize=8.7,fontweight='bold')
# Legend symbols are real artist markers; shape survives monochrome reproduction.
ax.scatter([],[],marker='D',s=22,c=G,label='Crossing')
ax.scatter([],[],marker='o',s=22,facecolors='white',edgecolors=O,label='Inside')
ax.legend(loc='lower left',bbox_to_anchor=(-.32,1.05),ncol=2,frameon=False,fontsize=8.2,handletextpad=.45,columnspacing=1.5,borderpad=0)
ax.text(1,1.045,'1 = equal time',transform=ax.get_xaxis_transform(),ha='center',va='bottom',fontsize=7.6,color=GRAY)
fig.text(.018,.044,'Segments: ranges across three paired repetitions.',fontsize=7.7,color=GRAY)
save(fig,'vulkan_geometry','All12 final Vulkan geometry cells. Filled diamonds crossing / hollow circles inside. Explicit ratio1 reference; segments are3-repeat paired ranges, not CI. Capacity and prefix region change together.')

# Fig.7a: same work on both paths; origin-level observations remain visible.
fig,ax=canvas(3.50,2.56,.32,.78,.25,.75)
for y,r in zip([3,2,1,0],D['equal_work']):
    ax.scatter(r['root_ratios'],[y+.12]*4,s=10,c=LIGHT,zorder=2,linewidths=0)
    ax.scatter(r['ratio'],y,marker='D',s=27,c=G,zorder=3)
    rowtext(fig,ax,.985,y,f'{100*r["reduction"]:.2f}%',ha='right',va='center',fontsize=8.2,color=G)
equal_line(ax);ax.set(xlim=(.79,1.085),ylim=(-.45,3.55),xticks=[.8,.9,1.0],yticks=[3,2,1,0],yticklabels=['loop4 · inside','loop4 · crossing','packed · inside','packed · crossing']);base(ax)
ax.set_xlabel('One q8 / two q4 operation time',labelpad=4)
fig.text(.018,.965,'(a) Equal work: lower aggregate cost',fontsize=8.6,fontweight='bold')
fig.text(.018,.868,'Same state · 8 tokens · all 8 full outputs',fontsize=7.9,color=GRAY)
fig.text(.985,.79,'Less time',ha='right',fontsize=7.9,color=GRAY)
ax.text(1,1.045,'1 = equal',transform=ax.get_xaxis_transform(),ha='center',va='bottom',fontsize=7.6,color=GRAY)
fig.text(.018,.041,'Faint points: four fixed-origin ratios per cell.',fontsize=7.7,color=GRAY)
save(fig,'width_equal','All4 equal-work cells, all4 origin ratios each, same aggregate reductions. Explicit less-time percentage column; equality at1. Descriptive fixed-origin measurements.')
# Fig.7b: same method; more proposed work is included in complete service.
fig,ax=canvas(3.50,2.56,.30,.78,.25,.75)
for y,r in zip([3,2,1,0],D['q8']['contrasts'][:4]):
    interval(ax,r['ratio'],r['adjusted_interval'],y,O)
    rowtext(fig,ax,.985,y,f'{r["change_pct"]:.2f}%',ha='right',va='center',fontsize=8.2,color=OT)
equal_line(ax);ax.set(xlim=(.985,1.235),ylim=(-.45,3.55),xticks=[1,1.1,1.2],yticks=[3,2,1,0],yticklabels=['W · loop4','W · packed','L · loop4','L · packed']);base(ax)
ax.set_xlabel('k7 / k3 complete service time',labelpad=4)
fig.text(.018,.965,'(b) Live work: k7 costs more',fontsize=8.6,fontweight='bold')
fig.text(.018,.868,'Verification rows: 14,016 → 18,368 (+31.05%)',fontsize=7.9,color=GRAY)
fig.text(.985,.79,'More time',ha='right',fontsize=7.9,color=GRAY)
ax.text(1,1.045,'1 = equal',transform=ax.get_xaxis_transform(),ha='center',va='bottom',fontsize=7.6,color=GRAY)
fig.text(.018,.041,'16 task roots; 98.75% adjusted paired-root intervals.',fontsize=7.7,color=GRAY)
save(fig,'width_live','All4 registered live k7/k3 comparisons and original98.75% intervals; same-cut/projection comparisons. More-time column explicitly distinguishes increases from equal-work reductions; no timedM claim.')

# Fig.S1: separate fixed numeric column prevents negative-label/row-label collision.
ph=D['q8_phases'];p3=ph[6]['phases'];p7=ph[7]['phases'];tot=D['q8']['totals'];delta=list(tot.values())[7]-list(tot.values())[6]
values=[p7['target_verify_s']-p3['target_verify_s'],p7['draft_propose_s']-p3['draft_propose_s'],p7['draft_sync_s']-p3['draft_sync_s']]
values += [delta-sum(values),delta]
fig,ax=canvas(3.50,2.48,.35,.78,.24,.80)
for y,v in zip([4,3,2,1,0],values):
    color=G if v<0 else (B if y==0 else O)
    ax.barh(y,v,height=.4,color='white' if y==0 else color,edgecolor=color,lw=.9,zorder=2)
    rowtext(fig,ax,.985,y,f'{v:+.3f}',ha='right',va='center',fontsize=8.3,color=INK)
ax.axvline(0,color=GRAY,lw=.8);ax.axhline(.5,color=RULE,lw=.6)
ax.set(xlim=(-5,27),ylim=(-.5,4.6),xticks=[0,10,20],yticks=[4,3,2,1,0],yticklabels=['Target verify','Draft proposals','Draft sync','Other costs','Net service'])
base(ax);ax.set_xlabel('k7 − k3 (s over 128 requests)',labelpad=4)
fig.text(.018,.965,'Measured host-cost balance',fontsize=8.8,fontweight='bold')
fig.text(.985,.856,'Delta (s)',ha='right',fontsize=8,color=GRAY)
fig.text(.018,.05,'Negative values save time; the total includes all costs.',fontsize=7.7,color=GRAY)
save(fig,'supp_width_cost','Unchanged exact host-phase delta. All signed values in a dedicated right column; negative draft-sync value cannot collide with its row label. Reconciled residual and net retained; no pure-kernel attribution.')

# Earlier structural matrix retained as a companion asset, outside the paper's numbered figures.
h=D['historical']['vulkan_width'];fig,ax=canvas(7.12,2.45,.27,.98,.20,.88)
models=list(dict.fromkeys(r['deployment'] for r in h));qs=[2,4,8,16,32]
for j,model in enumerate(models):
    for i,q in enumerate(qs):
        rows=[r for r in h if r['deployment']==model and r['q']==q]
        if not rows:ax.text(i,2-j,'Not measured',ha='center',va='center',fontsize=8,color=GRAY);continue
        r=rows[0];cross=1/r['cross'];inside=1/r['inside'];color=G if cross<1 else OT
        ax.text(i,2-j+.13,f'{cross:.3f}',ha='center',va='center',fontsize=10,color=color)
        ax.text(i,2-j-.16,f'inside {inside:.3f}',ha='center',va='center',fontsize=7.8,color=GRAY)
for y in [.5,1.5]:ax.axhline(y,color=RULE,lw=.5)
ax.set(xlim=(-.5,4.5),ylim=(-.5,2.5),xticks=range(5),xticklabels=['q2','q4','q8','q16','q32'],yticks=[2,1,0],yticklabels=['Qwen C1024\ndual resident','Qwen C4096\ntarget only','Smol C4096\ndual resident'])
ax.tick_params(length=0,pad=6)
for s in ax.spines.values():s.set_visible(False)
fig.text(.27,.955,'Earlier fixed-work study: local / whole-cut time',fontsize=9)
fig.text(.27,.04,'Different cuts and deployments from Fig. 6; all observed cells and the unmeasured cell retained.',fontsize=8,color=GRAY)
save(fig,'supp_historical_geometry','All14 historical Vulkan cells, distinct from final interface. Exact inverse ratios retained, with the unmeasured cell explicit.')
(P/'FIGURE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
(P/'generated/FIGURE_LAYOUT_CHECK.json').write_text(json.dumps(layout,indent=2)+'\n')
print(f'Built {len(manifest)} one-axis statistical figures; original numerical evidence is unchanged.')
for item in layout:
    if item['text_outside_canvas']:print('REVIEW',item['figure'],item['text_outside_canvas'])
