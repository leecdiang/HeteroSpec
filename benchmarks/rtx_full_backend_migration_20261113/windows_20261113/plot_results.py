from pathlib import Path
import json,csv,math,statistics,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent;e=p/'evidence';o=e/'figures';o.mkdir(exist_ok=False)
rows=list(csv.DictReader((e/'ALL_PAIRED_SAMPLES.csv').open(encoding='utf8')));a=json.loads((e/'P_ANALYSIS.json').read_bytes());panel=json.loads((e/'prepared/panel.json').read_bytes());records=json.loads((e/'ALL_RECORDS.json').read_bytes())
fig,(ax,bx)=plt.subplots(1,2,figsize=(11.5,6.7),gridspec_kw={'width_ratios':[1.3,1]});colors={'R':'#617a9b','M':'#df8739'}
for i,x in enumerate(panel):
 values=[float(r['M_over_R']) for r in rows if r['mode']=='P' and r['root']==x['root']]
 ax.scatter(values,[i+(b-1.5)*.07 for b in range(4)],s=15,color='#8c9bb0',alpha=.8)
 ax.scatter([a['root_ratios'][x['root']]],[i],marker='D',s=30,color='#203e5a',zorder=3)
ax.set_yticks(range(16),[f"{x['root']}  ({len(x['prompt_ids'])} prompt tokens)" for x in panel],fontsize=8);ax.invert_yaxis();ax.axvline(1,color='.5',ls='--',lw=1)
ax.axvspan(*a['ci95'],color='#4b9caf',alpha=.14);ax.axvline(a['ratio_M_over_R'],color='#187b91',lw=1)
ax.set_xlim(.45,1.03);ax.set_xlabel('P: M / R host request time');ax.set_title('Fixed work: all 16 roots, four paired blocks',fontsize=11);ax.grid(axis='x',alpha=.2)
labels=[];pref=[];cont=[]
for mode in ['P','G']:
 for arm in ['R','M']:
  xs=[r for r in records if r['mode']==mode and r['arm']==arm and not r['warmup']];labels.append(f'{mode} / {arm}');pref.append(statistics.mean(r['prefill_s'] for r in xs));cont.append(statistics.mean(r['continuation_s'] for r in xs))
bx.barh(labels,pref,color='#6484a1',label='Reset + input delivery + prefill');bx.barh(labels,cont,left=pref,color='#deb17a',label='Continuation + bookkeeping');bx.invert_yaxis();bx.set_xlabel('Mean host request seconds');bx.set_title('Measured request boundaries',fontsize=11);bx.legend(fontsize=8,loc='lower right');bx.grid(axis='x',alpha=.2)
fig.suptitle(f"Complete R / pinned M deployment migration\nP root-weighted ratio {a['ratio_M_over_R']:.4f}; 95% paired-root interval [{a['ci95'][0]:.4f}, {a['ci95'][1]:.4f}]",fontsize=12)
fig.text(.5,.015,'Single device/window; formal prompts 26-161 tokens; R ubatch1, M ubatch32. Different numerical contracts.\nG: all responses hit cap128; only20/32 token trajectories identical. No quality-equivalence claim.',ha='center',fontsize=8)
fig.tight_layout(rect=[0,.07,1,.92])
for ext in ['png','svg','pdf']:fig.savefig(o/('P_roots_and_phases.'+ext),dpi=160)
plt.close(fig)
manifest=dict(data=[dict(path=n,sha256=hashlib.sha256((e/n).read_bytes()).hexdigest()) for n in ['ALL_PAIRED_SAMPLES.csv','P_ANALYSIS.json','ALL_RECORDS.json']],root_points='all4 P pair ratios perroot;diamond=root geomean;shade=global root bootstrap interval,not individual rootCI',phases='within same host request timer;prefill includes reset,continuation includes bookkeeping;not kernel-only causal decomposition')
(o/'MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('Created standalone PNG/SVG/PDF with all16 roots and actual phase boundaries')
