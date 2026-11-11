"""Publication figures for the reference-preserving execution rewrite.

The rewrite adds mechanism, execution, geometry and width-cost panels.
PR220 colors and type are retained; hierarchy uses position, labels and marker fill.
No source values, estimands, confidence bounds or cohorts are changed here.
"""
from pathlib import Path
import json, math, hashlib, shutil, subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
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
 'mathtext.fontset':'stix','axes.unicode_minus':True,'hatch.linewidth':.42})
manifest=[]; layout=[]
# Data coverage is checked against actual scatter artists, independently of labels.
expected_markers={
 'service_controls':sum(len(row)+1 for study in ROOT_POINTS for row in study['ratios']),
 'factorial':sum(len(row['root_ratios'])+1 for study in D['factors'].values() for row in study['all_fixed_controls']),
 'mixed_q4':len(D['q32']['means'])*(len(D['q32']['root_sums'])+1),
 'geometry_opportunity':len(D['vulkan_geometry']),
 'width_tradeoff':sum(len(row['root_ratios'])+1 for row in D['equal_work'])+len(D['q8']['contrasts'][:4])+2*3,
}

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
    for ext in ['svg','png']:
        fig.savefig(F/(name+'.'+ext),dpi=300)
    # Matplotlib's directPDF embedding mislabels CFF/OpenType P052 in some versions.
    # Cairo's SVG->PDF path preserves the actual font as embedded Type1C.
    if shutil.which('inkscape'):
        subprocess.run(['inkscape',str(F/(name+'.svg')),'--export-type=pdf',
                        '--export-filename='+str(F/(name+'.pdf'))],
                       check=True,capture_output=True,text=True)
        pdf_exporter='Inkscape/Cairo from editable Matplotlib SVG'
    else:
        with matplotlib.rc_context({'pgf.texsystem':'pdflatex','pgf.rcfonts':False,
             'pgf.preamble':r'\usepackage[T1]{fontenc}\usepackage{amssymb}\usepackage{mathpazo}'}):
            fig.savefig(F/(name+'.pdf'),backend='pgf')
        pdf_exporter='Matplotlib PGF / pdflatex'

    plotted_markers=sum(len(c.get_offsets()) for ax in fig.axes for c in ax.collections
                        if isinstance(c,matplotlib.collections.PathCollection))
    clipped_markers=0
    for ax in fig.axes:
        xmin,xmax=sorted(ax.get_xlim());ymin,ymax=sorted(ax.get_ylim())
        for collection in ax.collections:
            if isinstance(collection,matplotlib.collections.PathCollection):
                for x,y in collection.get_offsets():
                    if not (xmin<=x<=xmax and ymin<=y<=ymax):clipped_markers+=1
    assert clipped_markers==0,(name,clipped_markers)
    expected=expected_markers.get(name)
    if expected is not None:assert plotted_markers==expected,(name,plotted_markers,expected)
    manifest.append({'file':name,'size_in':[float(fig.get_figwidth()),float(fig.get_figheight())],
      'semantics':desc,'axis_count':len(fig.axes),'pdf_exporter':pdf_exporter,'font_family':family,
      'plotted_marker_count':plotted_markers,'expected_marker_count':expected,
      'clipped_marker_count':clipped_markers,
      'analysis_sha256':hashlib.sha256((P/'generated/analysis.json').read_bytes()).hexdigest(),
      'added_root_points_sha256':hashlib.sha256((P/'data_added/application_root_ratios.json').read_bytes()).hexdigest()})
    plt.close(fig)

# Main Fig. 5: models form groups; fixed control, estimate and numeric reduction are separate columns.
fig,ax=canvas(6.875,3.35,.32,.835,.17,.875)
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
        rowtext(fig,ax,.065,y,labels[j],ha='left',va='center',fontsize=8.3,
                fontweight='bold' if ['W_L4_M','W_P_M','L_L4_M','L_P_M'][j]==a['best_fixed_M'] else 'normal')
        rowtext(fig,ax,.982,y,f'{100*(1-r):.1f}%',ha='right',va='center',fontsize=8.7,color=B)
for y in [9.55,5.00]:
    ax.plot([.54,1.055],[y,y],color=RULE,lw=.6)
equal_line(ax);ax.set(xlim=(.54,1.055),ylim=(.55,14.25),xticks=[.6,.7,.8,.9,1],yticks=[])
base(ax);ax.set_xlabel('LOCAL-packed D4 / fixed target-only service time',labelpad=5)
fig.text(.018,.963,'Resident service against all target-only controls · A5000',fontsize=9.2,fontweight='bold')
fig.text(.065,.902,'Fixed target-only control',fontsize=8,color=GRAY)
fig.text(.982,.902,'Time reduction',fontsize=8,color=GRAY,ha='right')
fig.text(.815,.902,'1 = equal time',fontsize=7.8,color=GRAY,ha='right')
fig.text(.018,.016,'Faint points: roots. Lines: adjusted 99% intervals. Bold control: fastest measured M.',fontsize=8,color=GRAY)
save(fig,'service_controls','All 12 fixed target-only M contrasts and all 176 published root ratios across 3 separate Linux deployments; original 99% adjusted intervals and total-ratio estimates. Rounded percentage reductions; all six absolute means in Table S1. No minimum-selection significance test.')

# Main Fig. 3: the scientific factors are the hierarchy; uncertain local estimates are hollow/neutral.
fig,ax=canvas(6.875,3.28,.405,.835,.25,.875)
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
fig.text(.018,.966,'Separate effects of cut scope and projection · 16 roots per model',fontsize=9.2,fontweight='bold')
fig.text(.982,.906,'Time reduction',fontsize=8,color=GRAY,ha='right')
fig.text(.817,.906,'1 = equal time',fontsize=7.8,color=GRAY,ha='right')
fig.text(.018,.102,'Faint points: all roots. Lines: adjusted 99% intervals. Hollow: interval includes 1.',fontsize=8,color=GRAY)
fig.text(.018,.045,'Interaction: 8B 1.00070; 14B 1.00170 (mild attenuation; details in Supplement S3).',fontsize=8,color=GRAY)
save(fig,'factorial','All 8 direct factor contrasts and all 16 root ratios each. Original 99% family-adjusted intervals and total-ratio estimates; neutral hollow markers when the interval includes 1. Root-geometric interaction is separately identified and fully reported in Supplement S3.')

# Supplement: retain six arms and all root means, with direct fixed-scope reductions.
fig,ax=canvas(3.35,3.15,.37,.82,.18,.78)
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
save(fig,'mixed_q4','All 6 complete-service means and all 4 exposed-root means. Both fixed-scope group/graph-loop reductions are labelled. Grouped D4 versus fastest M is +14%; the graph-level control is distinct from a backend loop. No population interval.')




# The following panels reorganize existing evidence; no new numerical estimate is fitted.
MECH=json.loads((P/'data_added/rewrite_figure_sources.json').read_text())
BLUE_PALE='#EEF3F8'; OCHRE_PALE='#FBF3EB'; GREEN_PALE='#F0F5F1'

def diagram(w,h,ymax):
    fig=plt.figure(figsize=(w,h))
    ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,18),ylim=(0,ymax));ax.axis('off')
    return fig,ax

def txt(ax,x,y,s,fs=8.2,color=INK,ha='left',va='center',weight='normal',**kw):
    return ax.text(x,y,s,fontsize=fs,color=color,ha=ha,va=va,fontweight=weight,**kw)

def rect(ax,x,y,w,h,text='',edge=B,face=BLUE_PALE,hatch=None,fs=8.1):
    p=Rectangle((x,y),w,h,facecolor=face,edgecolor=edge,lw=.7,hatch=hatch)
    ax.add_patch(p)
    if text:txt(ax,x+w/2,y+h/2,text,fs=fs,ha='center',
                bbox={'facecolor':face,'edgecolor':'none','pad':.35} if hatch else None)
    return p

def arrow(ax,x1,y1,x2,y2,color=GRAY,lw=.7,style='-|>',connectionstyle='arc3'):
    p=FancyArrowPatch((x1,y1),(x2,y2),arrowstyle=style,mutation_scale=7,
                      color=color,lw=lw,connectionstyle=connectionstyle)
    ax.add_patch(p);return p

# Fig. 1: an observed counterexample and its crossed-extent intervention.
fig,ax=diagram(6.875,2.50,6.55)
txt(ax,.18,6.22,'(a) A measured four-query append',fs=9,weight='bold')
txt(ax,9.62,6.22,'(b) Native replay at two physical extents',fs=9,weight='bold')
ax.plot([9.26,9.26],[1.48,5.88],color=RULE,lw=.65)
xx=[3.70+i*1.34 for i in range(4)]
for y,label in [(5.30,'Query position'),(4.38,'Reference extent'),(3.46,'Wide-call extent')]:
    txt(ax,.25,y,label,fs=8.5)
for i,x in enumerate(xx):
    edge,face,hatch=(B,BLUE_PALE,None) if i<3 else (O,OCHRE_PALE,'///')
    rect(ax,x,5.02,1.15,.55,str(MECH['extent']['query_positions'][i]),edge,face,hatch)
    rect(ax,x,4.10,1.15,.55,str(MECH['extent']['reference_extents'][i]),edge,face,hatch)
    rect(ax,x,3.18,1.15,.55,'1024',O,OCHRE_PALE,'///')
    arrow(ax,x+.575,4.98,x+.575,4.68)
txt(ax,.25,2.45,'Extent groups',fs=8.5)
rect(ax,xx[0],2.15,3*1.34-.19,.58,'3 queries',B,BLUE_PALE)
rect(ax,xx[3],2.15,1.15,.58,'1 query',O,OCHRE_PALE,'///',fs=7.8)
txt(ax,3.70,1.74,'Keep the 768 / 1024 boundary.',fs=8.0,color=GRAY)
# Every cell names the output it reproduces; color is redundant.
txt(ax,12.73,5.45,'Extent 768',fs=8.6,ha='center',weight='bold')
txt(ax,16.05,5.45,'Extent 1024',fs=8.6,ha='center',weight='bold')
txt(ax,9.64,4.60,'Scalar\ncapture',fs=8.2)
txt(ax,9.64,3.34,'Wide\ncapture',fs=8.2)
rect(ax,11.40,4.10,2.66,1.00,'Reference AV\nown path',B,BLUE_PALE,fs=8.3)
rect(ax,14.72,4.10,2.66,1.00,'Wide AV\nzero-pad',O,OCHRE_PALE,'///',fs=8.3)
rect(ax,11.40,2.84,2.66,1.00,'Reference AV\ncrop',B,BLUE_PALE,fs=8.3)
rect(ax,14.72,2.84,2.66,1.00,'Wide AV\nown path',O,OCHRE_PALE,'///',fs=8.3)
arrow(ax,14.10,4.60,14.68,4.60)
arrow(ax,14.68,3.34,14.10,3.34)
txt(ax,9.64,2.20,'Same visible operands; exchange physical extent.',fs=8.1,color=GRAY)
txt(ax,9.64,1.74,'Zero-pad probabilities / crop probabilities and V.',fs=7.9,color=GRAY)
ax.plot([.18,17.75],[1.25,1.25],color=RULE,lw=.65)
txt(ax,.25,.90,'Visible Q, K, V, QK and probabilities match; the masked probability suffix is zero.',fs=8.4)
txt(ax,.25,.36,'First saved full-vector difference: output 29    →    First emitted-token difference: output 81',fs=8.4,weight='bold')
save(fig,'extent_intervention','RTX Llama measured positions 765--768 and scalar extents [768,768,768,1024]. Native AV replay on the first query exchanges physical extent: same visible operands, padding/cropping probabilities and V as in source. Exact output 29/81 indices are not elapsed-time coordinates. Matrix text and hatching are redundant with color.')

# Fig. 2: physical cuts and arithmetic groups are intentionally separate rows.
fig,ax=diagram(6.875,3.72,9.65)
txt(ax,.18,9.31,'(a) Physical-range groups: choose where to cut',fs=9,weight='bold')
txt(ax,.32,8.77,'Whole: two ordered graph calls',fs=8.6,weight='bold')
txt(ax,9.38,8.77,'Local: one wider outer graph',fs=8.6,weight='bold')
for y,rows,extent,edge,face,hatch,seq in [(7.43,3,768,B,BLUE_PALE,None,'1'),
                                        (6.23,1,1024,O,OCHRE_PALE,'///','2')]:
    txt(ax,.43,y+.36,seq,ha='center',fs=8.6,weight='bold')
    rect(ax,.93,y,2.15,.73,f'Projection\n{rows} '+('query' if rows==1 else 'queries'),edge,face,hatch,fs=8.0)
    rect(ax,3.63,y,2.20,.73,f'Attention\nextent {extent}',edge,face,hatch,fs=8.0)
    rect(ax,6.38,y,2.15,.73,f'FFN\n{rows} '+('query' if rows==1 else 'queries'),edge,face,hatch,fs=8.0)
    arrow(ax,3.10,y+.365,3.61,y+.365)
    arrow(ax,5.85,y+.365,6.36,y+.365)
arrow(ax,.43,7.45,.43,7.00)
rect(ax,9.40,6.23,2.16,1.93,'Projection\nall 4 queries',GRAY,'white',fs=8.2)
rect(ax,12.34,7.43,2.34,.73,'Attention: 3 rows\nextent 768',B,BLUE_PALE,fs=8.0)
rect(ax,12.34,6.23,2.34,.73,'Attention: 1 row\nextent 1024',O,OCHRE_PALE,'///',fs=8.0)
rect(ax,15.46,6.23,2.16,1.93,'FFN\nall 4 queries',GRAY,'white',fs=8.2)
for y in [7.795,6.595]:
    ax.plot([11.56,11.95],[7.195,7.195],color=GRAY,lw=.65)
    ax.plot([11.95,11.95],[7.195,y],color=GRAY,lw=.65)
    arrow(ax,11.95,y,12.30,y)
    ax.plot([14.68,15.06],[y,y],color=GRAY,lw=.65)
    ax.plot([15.06,15.06],[y,7.195],color=GRAY,lw=.65)
arrow(ax,15.06,7.195,15.43,7.195)
# Small inner bars carry the same3+1 partition through the wider outside work.
for x in [9.65,15.71]:
    ax.plot([x,x+1.10],[7.94,7.94],color=B,lw=2.0)
    ax.plot([x+1.25,x+1.64],[7.94,7.94],color=O,lw=2.0)
txt(ax,.32,5.70,'Same extent partition: queries 765–767 | query 768.  Local keeps the surrounding graph wide.',fs=8.3,color=GRAY)
ax.plot([.18,17.75],[5.26,5.26],color=RULE,lw=.65)
txt(ax,.18,4.91,'(b) Arithmetic groups: retain the inner recipe, parallelize independent groups',fs=9,weight='bold')
txt(ax,.40,4.37,'Q8_0 weights: four-column recipe (a = 4)',fs=8.5,weight='bold')
txt(ax,9.52,4.37,'Q4_K / Q6_K weights: scalar recipe (a = 1)',fs=8.5,weight='bold')
# One batch frame per numerical recipe; these groups are not the3+1 physical groups above.
rect(ax,.40,2.66,8.20,1.30,'',RULE,'white')
rect(ax,.70,2.89,3.30,.84,'4-column MMVQ\ncolumns 1–4',B,BLUE_PALE,fs=8.1)
rect(ax,4.98,2.89,3.30,.84,'4-column MMVQ\ncolumns 5–8',B,BLUE_PALE,fs=8.1)
txt(ax,4.50,2.21,'[K, 8] → [K, 4, 2]    ·    one batched operation',fs=8.3,ha='center')
rect(ax,9.52,2.66,8.10,1.30,'',RULE,'white')
for i in range(8):
    rect(ax,9.79+i*.95,2.89,.75,.84,f'col.\n{i+1}',G,GREEN_PALE,fs=7.8)
txt(ax,13.57,2.21,'[K, 8] → [K, 1, 8]    ·    one independent channel per column',fs=8.3,ha='center')
ax.plot([.18,17.75],[1.72,1.72],color=RULE,lw=.65)
txt(ax,.30,1.19,'(c) One resident owner',fs=8.6,weight='bold')
items=[(4.62,'Live KV state'),(8.00,'Execute groups'),(11.38,'Own outputs'),(14.76,'Commit / trim')]
for x,label in items:rect(ax,x,.86,2.84,.64,label,G,GREEN_PALE,fs=8.0)
for x,_ in items[:-1]:arrow(ax,x+2.87,1.18,x+3.34,1.18,color=G)
txt(ax,.30,.32,'Across prefill, continuation and verification: preserve the active prefix, frontier and pending token.',fs=8.2,color=GRAY)
save(fig,'execution_method','Diagram of two distinct axes: ordered physical-extent graph cuts and independent arithmetic-group packing. Measured 3+1 example for Whole/Local; illustrative 8-column packing at a=4 or a=1. Output ownership and the resident state connect stages. No physical-group concurrency or automatic fastest-strategy selection is implied.')

# Main Fig. 4: workload opportunity is a census; controlled append cost has its own unit.
fig=plt.figure(figsize=(6.875,3.02))
nat=MECH['natural_geometry'];n=nat['logical_cycles'];cross=nat['whole_extra_call_cycles']
fig.text(.018,.965,'(a) Natural opportunity',fontsize=9,fontweight='bold')
fig.text(.018,.893,'Qwen3-8B · Linux / A5000 · k=3',fontsize=8.3,color=GRAY)
fig.text(.018,.758,f'{cross:,} / {n:,}',fontsize=19,color=B,fontweight='bold')
fig.text(.018,.687,f'{100*cross/n:.2f}% of logical verification cycles',fontsize=8.2)
fig.text(.018,.628,'require an extra Whole call.',fontsize=8.2)
na=fig.add_axes([.025,.507,.275,.055])
na.barh(0,n-cross,left=0,height=.8,color='#DDE3E8',edgecolor=GRAY,lw=.5)
na.barh(0,cross,left=n-cross,height=.8,color=O,edgecolor=O,lw=.6,hatch='///')
na.set(xlim=(0,n),ylim=(-.5,.5));na.axis('off')
fig.text(.025,.449,f'{n-cross:,} without an extra call',fontsize=8,color=GRAY)
fig.text(.018,.350,f'Whole: {nat["whole_physical_calls"]:,} physical calls',fontsize=8.5)
fig.text(.018,.282,f'Local:  {nat["local_physical_calls"]:,} physical calls',fontsize=8.5)
fig.text(.018,.162,'Identical prefill width histograms.',fontsize=8.0,color=GRAY)
fig.text(.018,.107,'64 measured requests per arm.',fontsize=8.0,color=GRAY)
fig.add_artist(plt.Line2D([.345,.345],[.10,.93],transform=fig.transFigure,color=RULE,lw=.65))
fig.text(.377,.965,'(b) Controlled appends · Vulkan / B570',fontsize=9,fontweight='bold')
ax=fig.add_axes([.525,.22,.43,.60]);coords={x['cell']:x for x in D['vulkan_geometry']}
for cap,ybase in [(1024,4.85),(4096,1.65)]:
    for qi,q in enumerate([2,4,32]):
        y=ybase-qi*.85
        for condition,dy,color,marker in [('crossing',-.13,B,'D'),('inside',.13,O,'o')]:
            r=coords[f'C{cap}-q{q}-{condition}']
            ax.plot([min(r['paired_ratios']),max(r['paired_ratios'])],[y+dy]*2,color=color,lw=1,zorder=2)
            ax.scatter(r['ratio'],y+dy,marker=marker,s=23,facecolor=color if condition=='crossing' else 'white',edgecolor=color,lw=.9,zorder=3)
        rowtext(fig,ax,.484,y,f'q={q}',ha='right',va='center',fontsize=8.2)
    rowtext(fig,ax,.377,ybase+.64,f'C={cap}; boundary {768 if cap==1024 else 3072}',ha='left',va='center',fontsize=8.1,fontweight='bold',bbox={'facecolor':'white','edgecolor':'none','pad':.7})
equal_line(ax);ax.set(xlim=(.50,1.115),ylim=(-.55,6.0),xticks=[.6,.8,1.0],yticks=[]);base(ax)
ax.axhline(2.46,color=RULE,lw=.6);ax.set_xlabel('Local / Whole append time',labelpad=4)
ax.scatter([],[],marker='D',s=22,c=B,label='Crossing (1 + q−1)')
ax.scatter([],[],marker='o',s=22,facecolors='white',edgecolors=O,label='Inside')
ax.legend(loc='lower left',bbox_to_anchor=(-.37,1.075),ncol=2,frameon=False,fontsize=8.0,
          handletextpad=.45,columnspacing=1.3,borderpad=0)
fig.text(.377,.039,'Segments: min–max of three paired observations.',fontsize=7.8,color=GRAY)
save(fig,'geometry_opportunity','Left: exact PR204 census of 20/2224 logical verification cycles and physical calls 2244 versus 2224; bar length preserves the 0.899% fraction. Right: all 12 PR194 controlled Vulkan cells, original means and 3-repeat paired ranges. Platforms, units and cohorts remain separate; no natural-service speed is inferred from controlled appends.')

# Fig. 6: paired-operation efficiency, live service, and actual work have separate panels.
fig=plt.figure(figsize=(6.875,3.58))
fig.text(.018,.967,'(a) Equal eight-row work',fontsize=9,fontweight='bold')
fig.text(.522,.967,'(b) Complete speculative requests',fontsize=9,fontweight='bold')
fig.text(.018,.905,'4 fixed origins · same initial and final state',fontsize=8.0,color=GRAY)
fig.text(.522,.905,'16 task roots · k=7 versus k=3',fontsize=8.0,color=GRAY)
la=fig.add_axes([.174,.505,.235,.327])
for y,r in zip([3,2,1,0],D['equal_work']):
    la.scatter(r['root_ratios'],[y+.13]*4,s=9,c=LIGHT,zorder=2,linewidths=0)
    la.scatter(r['ratio'],y,marker='D',s=26,c=B,zorder=3)
    rowtext(fig,la,.488,y,f'−{100*r["reduction"]:.2f}%',ha='right',va='center',fontsize=8.1,color=B)
equal_line(la);la.set(xlim=(.79,1.085),ylim=(-.45,3.55),xticks=[.8,.9,1.0],yticks=[3,2,1,0],
                     yticklabels=['loop4 · inside','loop4 · crossing','packed · inside','packed · crossing'])
base(la);la.tick_params(axis='y',labelsize=7.8);la.set_xlabel('One q=8 / two q=4 time',labelpad=3,fontsize=8.0)
fig.text(.488,.849,'Change',ha='right',fontsize=7.8,color=GRAY)
ra=fig.add_axes([.684,.505,.235,.327])
for y,r in zip([3,2,1,0],D['q8']['contrasts'][:4]):
    interval(ra,r['ratio'],r['adjusted_interval'],y,O,marker='s')
    rowtext(fig,ra,.988,y,f'+{r["change_pct"]:.2f}%',ha='right',va='center',fontsize=8.1,color=OT)
equal_line(ra);ra.set(xlim=(.985,1.235),ylim=(-.45,3.55),xticks=[1,1.1,1.2],yticks=[3,2,1,0],
                     yticklabels=['Whole · loop4','Whole · packed','Local · loop4','Local · packed'])
base(ra);ra.tick_params(axis='y',labelsize=7.8);ra.set_xlabel('k=7 / k=3 service time',labelpad=3,fontsize=8.0)
fig.text(.988,.849,'Change',ha='right',fontsize=7.8,color=GRAY)
fig.add_artist(plt.Line2D([.507,.507],[.427,.948],transform=fig.transFigure,color=RULE,lw=.65))
fig.text(.018,.375,'Faint points: four origin ratios.  Right intervals: 98.75% paired-root bootstrap.',fontsize=7.8,color=GRAY)
fig.add_artist(plt.Line2D([.018,.985],[.340,.340],transform=fig.transFigure,color=RULE,lw=.65))
work3=D['q8_work']['3'];work7=D['q8_work']['7']
assert work3['output_tokens']==work7['output_tokens']
fig.text(.018,.294,f'(c) Same {work3["output_tokens"]:,} emitted tokens, different work',fontsize=8.8,fontweight='bold')
wa=fig.add_axes([.535,.112,.385,.130])
for y,key,label in [(2,'cycles','Verification cycles'),(1,'verify_rows','Verified rows'),(0,'proposed','Draft proposals')]:
    ratio=work7[key]/work3[key];col=B if ratio<1 else O
    wa.plot([1,ratio],[y,y],color=col,lw=1.4,zorder=2)
    wa.scatter(1,y,facecolors='white',edgecolors=GRAY,marker='o',s=17,zorder=3,linewidths=.7)
    wa.scatter(ratio,y,facecolors=col,edgecolors=col,marker='s',s=24,zorder=4)
    rowtext(fig,wa,.018,y,label,ha='left',va='center',fontsize=8.1)
    rowtext(fig,wa,.475,y,f'{work3[key]:,} → {work7[key]:,}',ha='right',va='center',fontsize=8.0,color=GRAY)
    rowtext(fig,wa,.988,y,f'{100*(ratio-1):+.2f}%',ha='right',va='center',fontsize=8.0,color=col if col==B else OT)
equal_line(wa);wa.set(xlim=(.55,1.70),ylim=(-.45,2.45),xticks=[.6,1,1.4,1.6],yticks=[]);base(wa)
wa.tick_params(axis='x',labelsize=7.7,pad=2)
fig.text(.535,.017,'k=7 / k=3 work count  (open circle = k=3)',fontsize=7.7,color=GRAY)
save(fig,'width_tradeoff','Windows RTX: all 4 equal-work cells and 16 origin ratios; all 4 registered live k7/k3 contrasts with original 98.75% intervals, on separate cohorts. Exact work counts for the same 11472 emitted tokens: cycles 3504->2296, verified rows 14016->18368, proposals 10512->16072. q is physical width; weights remain Q8_0. No confidence interval is invented for work counts.')

# Keep historical and cost companion graphics reproducible for the supplement.
# These remain supplementary, outside the rewritten main-panel set.
ph=D['q8_phases'];p3=ph[6]['phases'];p7=ph[7]['phases'];tot=D['q8']['totals']
delta=tot['L-packed-k7']-tot['L-packed-k3']
values=[p7['target_verify_s']-p3['target_verify_s'],p7['draft_propose_s']-p3['draft_propose_s'],p7['draft_sync_s']-p3['draft_sync_s']]
values += [delta-sum(values),delta]
fig,ax=canvas(3.35,2.48,.35,.78,.24,.80)
for y,v in zip([4,3,2,1,0],values):
    color=B if v<0 else (GRAY if y==0 else O)
    ax.barh(y,v,height=.4,color='white' if y==0 else color,edgecolor=color,lw=.9,zorder=2,
            hatch='///' if y==0 else None)
    rowtext(fig,ax,.985,y,f'{v:+.3f}',ha='right',va='center',fontsize=8.2)
ax.axvline(0,color=GRAY,lw=.8);ax.axhline(.5,color=RULE,lw=.6)
ax.set(xlim=(-5,27),ylim=(-.5,4.6),xticks=[0,10,20],yticks=[4,3,2,1,0],
       yticklabels=['Target verify','Draft proposals','Draft sync','Other costs','Net service'])
base(ax);ax.set_xlabel('k=7 − k=3 (s over 128 requests)',labelpad=4,fontsize=8.0)
fig.text(.018,.965,'Measured host-cost balance',fontsize=8.8,fontweight='bold')
fig.text(.985,.856,'Delta (s)',ha='right',fontsize=8,color=GRAY)
fig.text(.018,.05,'Signed deltas; total includes all costs.',fontsize=7.7,color=GRAY)
save(fig,'supp_width_cost','Exact inherited host-phase deltas for Local-packed, all signed values and residual retained. Nested timing categories are not attributed to unique GPU kernels.')

h=D['historical']['vulkan_width'];fig,ax=canvas(6.875,2.45,.27,.98,.20,.88)
models=list(dict.fromkeys(r['deployment'] for r in h));qs=[2,4,8,16,32]
for j,model in enumerate(models):
    for i,q in enumerate(qs):
        rows=[r for r in h if r['deployment']==model and r['q']==q]
        if not rows:
            ax.text(i,2-j,'Not measured',ha='center',va='center',fontsize=8,color=GRAY);continue
        r=rows[0];cross=1/r['cross'];inside=1/r['inside'];color=B if cross<1 else OT
        ax.text(i,2-j+.13,f'{cross:.3f}',ha='center',va='center',fontsize=10,color=color)
        ax.text(i,2-j-.16,f'inside {inside:.3f}',ha='center',va='center',fontsize=7.8,color=GRAY)
for y in [.5,1.5]:ax.axhline(y,color=RULE,lw=.5)
ax.set(xlim=(-.5,4.5),ylim=(-.5,2.5),xticks=range(5),xticklabels=['q2','q4','q8','q16','q32'],
       yticks=[2,1,0],yticklabels=['Qwen C1024\ndual resident','Qwen C4096\ntarget only','Smol C4096\ndual resident'])
ax.tick_params(length=0,pad=6)
for s in ax.spines.values():s.set_visible(False)
fig.text(.27,.955,'Earlier fixed-work study: Local / Whole-cut time',fontsize=9)
fig.text(.27,.04,'Separate deployments; all observed cells and the unmeasured cell retained.',fontsize=7.8,color=GRAY)
save(fig,'supp_historical_geometry','All 14 inherited historical Vulkan cells; exact inverse ratios and explicit unmeasured cell. Separate from the final interface and natural-opportunity census.')

for item in manifest:
    item['rewrite_source_projection_sha256']=hashlib.sha256((P/'data_added/rewrite_figure_sources.json').read_bytes()).hexdigest()
(P/'FIGURE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
(P/'generated/FIGURE_LAYOUT_CHECK.json').write_text(json.dumps(layout,indent=2)+'\n')
print(f'Built {len(manifest)} vector figure sets; original numerical evidence unchanged.')
for item in layout:
    if item['text_outside_canvas']:
        print('REVIEW',item['figure'],item['text_outside_canvas'])

