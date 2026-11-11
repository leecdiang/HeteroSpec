"""Versioned Figure 3: historical physical proxies and prospective qualification."""
from pathlib import Path
import csv, hashlib, json, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
MAN=HERE.parents[1]; REPO=MAN.parents[2]
sys.path.insert(0,str(MAN/'scripts'))
from direct_id_values import records
INK='#24313D'; ACCENT='#366D95'; GRAY='#6C7680'
plt.rcParams.update({'font.family':'serif','font.serif':['STIXGeneral'],'font.size':8,
    'axes.labelsize':8,'xtick.labelsize':7.5,'ytick.labelsize':8,'text.color':INK,
    'axes.labelcolor':INK,'axes.edgecolor':INK,'axes.linewidth':.55,
    'pdf.fonttype':42,'svg.fonttype':'path','svg.hashsalt':'heterospec-v07',
    'figure.facecolor':'white','savefig.facecolor':'white'})

def main():
    source=REPO/'paper/mlsys2027/figures/data/figure2_micro_cells.csv'
    cells=list(csv.DictReader(source.read_text().splitlines()))
    f=plt.figure(figsize=(6.75,2.12))
    a=f.add_axes([.18,.28,.285,.51]);b=f.add_axes([.64,.28,.205,.51])
    for ax in (a,b):
        for side in ('top','right','left'):ax.spines[side].set_visible(False)
        ax.tick_params(length=2,width=.55);ax.tick_params(axis='y',length=0,pad=5)
    f.text(.015,.97,'A  Historical target-forward proxy',va='top',fontsize=9)
    f.text(.525,.97,'B  Fresh direct-ID qualification',va='top',fontsize=9)
    f.text(.015,.86,'Different runs / contexts',fontsize=7.5,color=GRAY)
    f.text(.525,.86,'No matching fresh latency endpoint',fontsize=7.5,color=GRAY)
    paths=['M4 Metal','RTX batched','RTX serialized','B570 fast','B570 serialized']
    a.set(xlim=(.85,2.6),ylim=(4.5,-.5),yticks=range(5),yticklabels=paths,
          xticks=[1,1.5,2,2.5],xlabel=r'Target-forward $V_2^{\mathrm{micro}}$')
    a.axvline(1,color=GRAY,ls='--',lw=.6,zorder=0)
    artists=[]
    for y,path in enumerate(paths):
        rows=[r for r in cells if r['path']==path]
        values=[float(r['v2_micro']) for r in rows]
        marker='D' if path=='M4 Metal' else ('s' if 'serialized' in path else 'o')
        offsets=np.linspace(-.15,.15,len(values))
        a.plot([min(values),max(values)],[y,y],lw=.7,color=GRAY,zorder=1)
        a.scatter(values,y+offsets,marker=marker,s=19,c=INK,edgecolors=INK,linewidths=.5,zorder=3)
        artists.append({'path':path,'points':values,'contexts':[int(r['context']) for r in rows],
                        'marker':marker,'encoding':'path type only','filled':True})
    data=records()
    b.set(xlim=(0,90),ylim=(3.5,-.5),yticks=range(4),
          yticklabels=['RTX batched','RTX serialized','B570 fast','B570 serialized'],
          xticks=[0,30,60,90],xlabel='Direct-ID equal pairs (of 90)')
    b.axvline(90,color=GRAY,ls='--',lw=.8,clip_on=False,zorder=0)
    f.text(.845,.81,'90/90 gate',ha='center',fontsize=7)
    for y,row in enumerate(data):
        qualified=row['status']=='QUALIFIED';marker='s' if qualified else 'o'
        b.scatter([row['exact_pairs']],[y],marker=marker,s=25,
                  facecolors=ACCENT if qualified else 'white',edgecolors=INK,
                  linewidths=.85,clip_on=False,zorder=3)
        b.text(row['exact_pairs']-9,y,f"{row['exact_pairs']}/90",
               ha='right',va='center',fontsize=7.5,bbox={'facecolor':'white','edgecolor':'none','pad':.6})
        b.text(1.09,y,row['status'],transform=b.get_yaxis_transform(),va='center',fontsize=7)
    f.text(.015,.025,'A: path shapes only; all 11 measured cells.   B: open = BLOCKED; filled square = QUALIFIED.',fontsize=7.5)
    f.canvas.draw();renderer=f.canvas.get_renderer();bad=[]
    for t in f.findobj(matplotlib.text.Text):
        if t.get_visible() and t.get_text():
            box=t.get_window_extent(renderer)
            if box.x0<-.5 or box.y0<-.5 or box.x1>f.bbox.width+.5 or box.y1>f.bbox.height+.5:bad.append(t.get_text())
    assert not bad,bad
    for folder in ('pdf','svg','qa'):(HERE/folder).mkdir(parents=True,exist_ok=True)
    f.savefig(HERE/'pdf/verification.pdf',metadata={'CreationDate':None,'ModDate':None})
    f.savefig(HERE/'svg/verification.svg',metadata={'Date':None})
    svg=HERE/'svg/verification.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    for dpi in (96,200):
        path=HERE/f'qa/verification_color_{dpi}.png';f.savefig(path,dpi=dpi)
        Image.open(path).convert('L').save(HERE/f'qa/verification_grayscale_{dpi}.png')
    inputs=[source]+[REPO/r['source'] for r in data]
    receipt={'size_in':[6.75,2.12],'panel_a':artists,'panel_b':data,'threshold':90,
             'out_of_bounds_text':bad,'inputs':{p.relative_to(REPO).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
             'scope':'Separate studies, not same-run cost versus correctness; no performance ranking.'}
    (HERE/'qa/verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('Figure 3 generated: 11 physical cells; 4 separately frozen qualification rows.')

if __name__=='__main__':main()
