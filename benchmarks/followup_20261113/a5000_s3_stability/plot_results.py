"""Plot complete saved panels only; no new measurements or fitted exclusions."""
import argparse
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot(analysis, out):
    data = json.loads(analysis.read_text())
    available = [p for p in ('R1','R2','H1') if 'estimate' in data[p]]
    if not available:
        raise ValueError('No complete panel to plot')
    out.mkdir(parents=True, exist_ok=False)
    has_r = any(p.startswith('R') for p in available)
    has_h = 'H1' in available
    count = int(has_r) + int(has_h)
    fig, axes = plt.subplots(1, count, figsize=(10.5*count,8), squeeze=False)
    csv_rows = []
    all_effects = [0]
    for p in available:
        e = data[p]['estimate']
        all_effects.extend(100*(1-x['CB']) for x in e['roots'])
        all_effects.extend(100*(1-v) for v in e['CI95'])
        for root in e['roots']:
            csv_rows.append(dict(panel=p,slot=root['slot'],root_id=root['root_id'],domain=root['domain'],CB=root['CB'],
                                 reduction_percent=100*(1-root['CB'])))
    low = min(all_effects)-.15; high = max(all_effects)+.15
    column = 0
    if has_r:
        ax = axes[0,column]; column += 1
        dates = [p for p in ('R1','R2') if p in available]
        roots = data[dates[0]]['estimate']['roots']
        for j,p in enumerate(dates):
            shift = -.12 if len(dates)==2 and j==0 else .12 if len(dates)==2 else 0
            values = [100*(1-r['CB']) for r in data[p]['estimate']['roots']]
            ax.scatter(values,[i+shift for i in range(12)],s=36,label='R date '+str(j+1),zorder=3)
        if len(dates)==2:
            for i in range(12):
                values = [100*(1-data[p]['estimate']['roots'][i]['CB']) for p in dates]
                ax.plot(values,[i-.12,i+.12],color='.7',lw=.8,zorder=1)
            summary = data['R_combined']['estimate']
            summary_label = 'Combined R (these two dates)'
        else:
            summary = data[dates[0]]['estimate']; summary_label = 'R date 1; date 2 pending'
        ax.set_title('R: original 12 inputs',loc='left',fontweight='bold')
        ax.legend(loc='lower right',frameon=False)
        labels = [r['root_id'] for r in roots]
        summary_plot(ax,summary,summary_label,labels)
    if has_h:
        ax = axes[0,column]; e = data['H1']['estimate']
        values = [100*(1-r['CB']) for r in e['roots']]
        ax.scatter(values,list(range(12)),s=36,color='#257e72',zorder=3)
        ax.set_title('H: new workload, exposure unknown',loc='left',fontweight='bold')
        summary_plot(ax,e,'H equal-root estimate',[r['root_id'] for r in e['roots']])
    for ax in axes.flat:
        ax.axvline(0,color='.45',ls='--',lw=1)
        ax.axhline(5.5,color='.88',lw=.8)
        ax.set_xlim(low,high); ax.set_ylim(14,-.7)
        ax.grid(axis='x',alpha=.18)
        ax.set_xlabel('Resident-service reduction vs B (%) — positive means C faster')
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Qwen3-32B Q4_K_M · A5000 · greedy target-only · C1024 · a=1',fontsize=13)
    fig.text(.01,.025,'Native reset-inclusive request interval; load/context construction and post-service export excluded.\n'
             'Root points retain both rounds. Summary bars: 95% stratified paired-root bootstrap; R conditional on tested dates.',fontsize=9)
    fig.tight_layout(rect=(0,.07,1,.95))
    fig.savefig(out/'ROOT_POINTS.svg')
    fig.savefig(out/'ROOT_POINTS.png',dpi=150)
    with (out/'PER_ROOT.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(csv_rows[0]));writer.writeheader();writer.writerows(csv_rows)
    plt.close(fig)


def summary_plot(ax, estimate, label, labels):
    value=100*(1-estimate['CB']); lower=100*(1-estimate['CI95'][1]); upper=100*(1-estimate['CI95'][0])
    ax.errorbar(value,13,xerr=[[value-lower],[upper-value]],fmt='D',color='black',capsize=4,zorder=4)
    ax.set_yticks(list(range(12))+[13],labels=labels+[label],fontsize=9)
    ax.text(value,13.65,f'{value:.3f}%  [{lower:.3f}, {upper:.3f}]',ha='center',fontsize=9)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();plot(args.analysis,args.out)
