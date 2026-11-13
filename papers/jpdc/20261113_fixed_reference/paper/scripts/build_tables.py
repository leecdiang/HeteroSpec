#!/usr/bin/env python3
"""Create editable supplementary tables from the included public records."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
OUT=ROOT/'generated'
OUT.mkdir(exist_ok=True)

def read(p): return json.loads((DATA/p).read_text())
def esc(x): return str(x).replace('_',r'\_')

apps=read('pr222/applications.json')
lines=[]
arms=['W_L4_M','W_P_M','L_L4_M','L_P_M','W_L4_D4','L_P_D4']
for label, record in zip(['Qwen3-8B','Qwen3-14B','Llama-8B'],apps):
    lines.append(label+' & '+' & '.join(f"{record['totals'][a]/record['formal_per_arm']:.6f}" for a in arms)+r' \\')
(OUT/'table_application_means.tex').write_text('\\newcommand{\\SuppApplicationRows}{%\n'+'\n'.join(lines)+'\n}\n')

lines=[]
for pr,model in [('pr204','8B'),('pr208','14B')]:
    r=read(f'closeout/{pr}/ORIGINAL_RESULTS.json')
    for c in r['all_fixed_controls']:
        ratio=c['total_ratio']; lo,hi=c['interval']
        lines.append(model+' & '+esc(c['numerator']+'/'+c['denominator'])+
                     f' & {ratio:.6f} & [{lo:.6f}, {hi:.6f}]'+r' \\')
    c=r['interaction']; lo,hi=c['interval']
    lines.append(model+' & Interaction'+f" & {c['ratio']:.6f} & [{lo:.6f}, {hi:.6f}]"+r' \\')
(OUT/'table_factorials.tex').write_text('\\newcommand{\\SuppFactorRows}{%\n'+'\n'.join(lines)+'\n}\n')

r=read('pr222/q32_recomputed.json')
lines=[]
for arm,val in r['totals'].items():
    lines.append(esc(arm)+f" & {val:.6f} & {r['mean'][arm]:.6f}"+r' \\')
(OUT/'table_prior32b.tex').write_text('\\newcommand{\\SuppPriorRows}{%\n'+'\n'.join(lines)+'\n}\n')

r=read('pr222/a5000_pilot_source_projection.json')['live']
lines=[]
for a in ['W_L4','W_P','L_L4','L_P']:
    lines.append(esc(a)+f" & {r[a+'_K3']['service_s']:.6f} & {r[a+'_K7']['service_s']:.6f}"+r' \\')
(OUT/'table_ampere_width.tex').write_text('\\newcommand{\\SuppAmpereRows}{%\n'+'\n'.join(lines)+'\n}\n')

r=read('pr222/b2_matched_history_public_stats.json')
lines=[]
for c in r['contrasts']:
    lines.append(c['core']+f" & {c['boundary']} & {c['geometric_B_over_A']:.6f} & [{c['minimum']:.6f}, {c['maximum']:.6f}]"+r' \\')
(OUT/'table_matched_width.tex').write_text('\\newcommand{\\SuppMatchedRows}{%\n'+'\n'.join(lines)+'\n}\n')

r=read('pr222/strong_s2_source_projection.json')
cb=next(c for c in r['contrasts'] if c['candidate']=='C' and c['baseline']=='B')
bg=next(c for c in r['contrasts'] if c['candidate']=='B' and c['baseline']=='G')
lines=[]
for i,cell in enumerate(r['cells']):
    values=cb['block_ratios'][i]
    lines.append(esc(cell)+f" & {bg['geometric_ratios'][i]:.6f} & {cb['geometric_ratios'][i]:.6f} & [{min(values):.6f}, {max(values):.6f}]"+r' \\')
(OUT/'table_strong_operators.tex').write_text('\\newcommand{\\SuppOperatorRows}{%\n'+'\n'.join(lines)+'\n}\n')
print('Generated six editable tables from public data; no model execution.')
