"""Standalone descriptive figure of all preregistered live contrasts."""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from admission import ROOT,HERE

def main():
    data=json.loads((ROOT/'LIVE_RESULTS.json').read_bytes())
    fig,axes=plt.subplots(2,1,figsize=(10,7),layout='constrained')
    for ax,key,title in zip(axes,('primary','secondary'),('Four primary width comparisons','Separate four-comparison secondary family')):
        rows=data[key]
        for i,r in enumerate(rows):
            lo,hi=r['adjusted_interval_change_pct'];point=r['change_pct']
            ax.hlines(i,lo,hi,color='#204e75',linewidth=2)
            ax.plot(point,i,'o',color='#204e75',markersize=6)
            ax.annotate(f'{point:+.2f}% [{lo:+.2f}, {hi:+.2f}]',(hi,i),xytext=(6,0),textcoords='offset points',va='center',fontsize=9)
        bounds=[0]+[v for r in rows for v in r['adjusted_interval_change_pct']]
        span=max(bounds)-min(bounds);span=max(span,1)
        ax.set_xlim(min(bounds)-.12*span,max(bounds)+.75*span)
        ax.set_yticks(range(4),[r['name'] for r in rows]);ax.invert_yaxis();ax.axvline(0,color='#777777',linestyle='--',linewidth=1)
        ax.set_ylim(3.6,-.6);ax.set_title(title,loc='left',fontsize=12)
        ax.set_xlabel('Service-time change (%)  |  positive = slower numerator')
        ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.15)
    fig.suptitle('RTX 5070 Ti Laptop / native Windows / cap96\n16 paired root clusters, 8 order blocks, 98.75% intervals within each family',fontsize=12)
    fig.savefig(HERE/'WIDTH_EFFECTS.png',dpi=180);fig.savefig(HERE/'WIDTH_EFFECTS.svg');plt.close(fig)
    print('Saved all-eight-contrast standalone figure; no selected-arm filtering',flush=True)

if __name__=='__main__':main()
