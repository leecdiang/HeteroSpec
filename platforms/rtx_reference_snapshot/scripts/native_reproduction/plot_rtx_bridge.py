import json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import argparse
p=argparse.ArgumentParser();p.add_argument('--out',type=pathlib.Path,required=True);args=p.parse_args()
repo=pathlib.Path(__file__).resolve().parents[2];out=args.out;out.mkdir(parents=True,exist_ok=True);a=json.loads((repo/'benchmarks/rtx_native_bridge_20261026/results/ANALYSIS.json').read_bytes())
fig,ax=plt.subplots(figsize=(10,5.8));fig.patch.set_facecolor('white');fig.subplots_adjust(left=.20,right=.98,bottom=.22,top=.85)
for i,c in enumerate(a['cells']):
 lo,hi=c['simultaneous_family95_interval'];r=c['ratio'];color='#15803d' if c['practical_gain_established'] else '#c2410c'
 ax.errorbar(r,3-i,xerr=[[r-lo],[hi-r]],fmt='o',color=color,capsize=5,linewidth=2,markersize=7)
 ax.annotate(f'{r:.4f}  [{lo:.4f}, {hi:.4f}]',(hi,3-i),xytext=(9,0),textcoords='offset points',va='center',fontsize=10,bbox=dict(facecolor='white',edgecolor='none',alpha=.9,pad=1))
ax.axvline(1,color='#64748b',linewidth=1,label='Equal service time')
ax.axvline(.98,color='#2563eb',linestyle='--',linewidth=1.2,label='2% practical reduction')
ax.set_yticks([3,2,1,0],[f"k={c['k']} / {c['lifecycle']}" for c in a['cells']]);ax.set_ylim(-.7,3.7)
lo=min(c['simultaneous_family95_interval'][0] for c in a['cells']);hi=max(c['simultaneous_family95_interval'][1] for c in a['cells']);span=max(.04,hi-lo)
ax.set_xlim(min(lo-.015,.96),max(hi+span*.85,1.035));ax.set_xlabel('Complete service ratio: QB / mean(PQ_A, PQ_B)  (lower is better)')
ax.set_title('RTX matched deployment bridge',loc='left',fontsize=16,pad=20,fontweight='bold')
ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',alpha=.15);ax.tick_params(axis='y',length=0)
ax.legend(loc='lower right',frameon=False,fontsize=9)
fig.text(.02,.025,'6 process sessions · 12 fixed exposed inputs · 864 measurements · one device/date\nFour primary intervals: Bonferroni-adjusted session bootstrap, nominal 95% family coverage.',fontsize=8,color='#475569')
fig.savefig(out/'RTX四组对照.png',dpi=180,bbox_inches='tight');print('PLOT_WRITTEN')
