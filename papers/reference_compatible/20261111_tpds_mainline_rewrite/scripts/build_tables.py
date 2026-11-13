from pathlib import Path
import json
P=Path(__file__).resolve().parents[1];D=json.loads((P/'generated/analysis.json').read_text())
arms=['W_L4_M','W_P_M','L_L4_M','L_P_M','W_L4_D4','L_P_D4']
rows=[]
for name,a in zip(['Qwen3-8B','Qwen3-14B','Llama-8B'],D['applications']):rows.append(name+' & '+' & '.join(f"{a['means'][k]:.4f}" for k in arms)+r' \\')
(P/'generated/application_rows.tex').write_text('\n'.join(rows)+'\n')
rows=[]
labels=['L/W; loop4 fixed','L/W; packed fixed','P/L4; W fixed','P/L4; L fixed']
for model in ['8B','14B']:
 for name,c in zip(labels,D['factors'][model]['all_fixed_controls']):
  lo,hi=c['interval'];rows.append(f"{model} & {name} & {c['total_ratio']:.6f} & [{lo:.6f}, {hi:.6f}]"+r' \\')
(P/'generated/factor_rows.tex').write_text('\n'.join(rows)+'\n')
rows=[]
for arm,t in D['q8']['totals'].items():
 rows.append(arm.replace('loop4','L4').replace('packed','P')+f" & {t:.6f} & {t/128:.6f}"+r' \\')
(P/'generated/q8_rows.tex').write_text('\n'.join(rows)+'\n')
rows=[]
for c in D['q8']['contrasts'][4:]:
 lo,hi=c['adjusted_interval'];label=(c['numerator']+' / '+c['denominator']).replace('loop4','L4').replace('packed','P')
 rows.append(label+f" & {c['ratio']:.6f} & [{lo:.6f}, {hi:.6f}]"+r' \\')
(P/'generated/q8_secondary_rows.tex').write_text('\n'.join(rows)+'\n')
print('Complete numerical table inputs written.')
names={'application_rows':'ApplicationRows','factor_rows':'FactorRows','q32_rows':'QThreeTwoRows','q8_rows':'QEightRows','q8_secondary_rows':'QEightSecondaryRows'}
(P/'generated/table_macros.tex').write_text(''.join('\\newcommand{\\'+cmd+'}{%\n'+(P/'generated'/f'{f}.tex').read_text()+'}\n' for f,cmd in names.items()))

