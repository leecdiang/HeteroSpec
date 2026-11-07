#!/usr/bin/env python3
"""Prepare neutral full-array exports, raw-derived tables and author provenance."""
import hashlib,json,shutil,zipfile
from pathlib import Path
from verify_v010 import compute
HERE=Path(__file__).resolve().parents[1];REV=HERE.parent/'reviews/reconstruction_v010';OUT=HERE/'output'
def main():
 records=[]
 native_raw=json.loads((REV/'b570/NATIVE_UNTRUNCATED_ARRAYS.json').read_text())['units']
 raw_by={(a['task'],a['condition'],a['repetition']):a for a in native_raw}
 for study,fn,key,mapping in [('B570','b570/RAW_OUTPUT_ARRAYS.json','units',{'T0':'P0','T1':'P1'}),('RTX','rtx/FORMAL_ARRAYS_NEUTRAL.json','records',{'H0':'P0','H1':'P1'})]:
  source=json.loads((REV/fn).read_text())
  for a in source[key]:
   records.append(dict(study=study,cohort='exposed24' if study=='B570' else 'old19' if a['task'].startswith('HumanEval') else 'new24',task=a['task'],condition=mapping.get(a['condition'],a['condition']),rep=a.get('rep',a.get('repetition')),ids=a['ids'],endpoint=a['endpoint'],cap=128,inclusive_eog=True,raw_overshoot=raw_by[(a['task'],a['condition'],a.get('rep',a.get('repetition')))]['raw_overshoot'] if study=='B570' and a['condition'] in ('N0','N1') else a.get('overshoot',0)))
 result=compute(records);(REV/'UNIFIED_DERIVED.json').write_text(json.dumps(result,indent=2)+'\n')
 tables=HERE/'tables';header=r'''\begin{longtable}{@{}llrrrrr@{}}
\caption{Full task-level intervention comparisons. Counts are out of three stable observations. Equality uses all IDs within the specified endpoint and that endpoint; raw post-cap native suffixes are audited separately.}\\
\toprule Study & Task & $P_0/N_0$ & $P_1/N_1$ & $N_0/R$ & $N_1/R$ & $N_0/N_1$\\\midrule\endfirsthead
\toprule Study & Task & $P_0/N_0$ & $P_1/N_1$ & $N_0/R$ & $N_1/R$ & $N_0/N_1$\\\midrule\endhead
'''
 lines=[f"{x['study']} & {x['task']} & "+' & '.join(f"{x[k]}/3" for k in ['prediction_before','prediction_after','reference_before','reference_after','output_unchanged'])+r' \\' for x in result['task_rows']]
 (tables/'intervention_tasks_v010.tex').write_text(header+'\n'.join(lines)+'\n'+r'\bottomrule\end{longtable}'+'\n')
 header=r'''\begin{longtable}{@{}lllrrll@{}}
\caption{Complete before/after native witnesses for every task. Lengths are within the specified endpoint, including EOS where specified; B570 post-cap native suffixes are excluded from equality and retained separately. First difference is zero-based; an endpoint-only change would also count as unequal. All three observations give the listed result.}\\
\toprule Study & Task & $N_0/N_1$ & IDs$_0$ & IDs$_1$ & Endpoints$_0/{}_1$ & First diff. (IDs)\\\midrule\endfirsthead
\toprule Study & Task & $N_0/N_1$ & IDs$_0$ & IDs$_1$ & Endpoints$_0/{}_1$ & First diff. (IDs)\\\midrule\endhead
'''
 lines=[]
 for x in result['task_rows']:
  c=x['comparisons']['output_unchanged'][0];first='--' if c['first_difference_zero_based'] is None else str(c['first_difference_zero_based'])+' ('+str(c['left_id'])+r'$\to$'+str(c['right_id'])+')'
  lines.append(f"{x['study']} & {x['task']} & "+('equal' if c['equal'] else 'changed')+f" & {c['left_length']} & {c['right_length']} & {c['left_endpoint']}/{c['right_endpoint']} & {first}"+r' \\')
 (tables/'intervention_witnesses_v010.tex').write_text(header+'\n'.join(lines)+'\n'+r'\bottomrule\end{longtable}'+'\n')
 # Also full N0/R and N1/R first-difference details in neutral DERIVED.json.
 d=OUT/'anonymous-evidence-v0.10.0';d.mkdir(parents=True,exist_ok=True)
 (d/'FORMAL_ARRAYS.json').write_text(json.dumps(dict(schema='neutral-generated-id-arrays-v1',scope='Full endpoint-bounded committed outputs; no internal-state prediction',records=records),separators=(',',':'))+'\n')
 (d/'DERIVED.json').write_text(json.dumps(result,indent=2)+'\n')
 neutral_raw=[{k:a[k] for k in ['task','condition','repetition','ids','eog','contract_ids','contract_eog','endpoint','raw_overshoot','capture_sha256','result_sha256']} for a in native_raw]
 (d/'B570_UNTRUNCATED_NATIVE.json').write_text(json.dumps({'units':neutral_raw,'scope':'Raw committed suffix beyond cap is retained for audit; comparison uses contract_ids and endpoint','total_raw_overshoot':{'N0':60,'N1':63}},separators=(',',':'))+'\n')
 shutil.copy2(HERE/'scripts/verify_v010.py',d/'verify_v010.py')
 shutil.copy2(OUT/'anonymous-evidence-index-v0.9.0.zip',d/'historical-v0.9.0.zip')
 (d/'README.md').write_text('''# Anonymous intervention evidence v0.10.0
Run `python -B verify_v010.py`. Requires Python standard library only, no models or GPU.
All 1005 formal complete generated-ID arrays from 67 task units, three repeats and five conditions are exported. P0/P1 map to B570 T0/T1 and RTX H0/H1; original scientific records retain their labels. R is each study reference. EOS includes EOG; CAP128 compares the entire endpoint-bounded array. B570_UNTRUNCATED_NATIVE retains all144 native captures including1–2 committed post-cap IDs; suffix totals N0=60/N1=63 are metadata, not part of agreement. RTX limit preserves its actual stop contract. DERIVED contains all five full-array comparisons, endpoints, first differences and repeat stability.
This package validates export arithmetic, not independent runtime execution, binary identity or absolute clock certification. Separate author-side reports describe raw audits and limitations. B570 local seals and RTX remote readback have different strengths. RTX's frozen reference-restoration/no-new-regression goal failed despite prediction/native equality. Reference equality does not establish functional program correctness.
Historical v0.9.0 evidence ZIP is preserved byte-for-byte. The verifier checks its immutable base projection under the original exact-file-set manifest, then its separate v090 extensions. An initial direct base-verifier run on the extended historical package rejected its extra extension files; projection resolves packaging scope without changing any scientific bytes or old helper.
No timing or energy measurements were added for these interventions. Historical cost estimates retain their original estimator and measurement boundaries.
''')
 hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.iterdir()) if p.is_file() and p.name!='SHA256SUMS.json'};(d/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2)+'\n')
 zpath=OUT/'anonymous-intervention-evidence-v0.10.0.zip'
 with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(d.iterdir()):z.write(p,p.name)
 provenance={fn:hashlib.sha256((REV/fn).read_bytes()).hexdigest() for fn in ['b570/RAW_OUTPUT_ARRAYS.json','rtx/FORMAL_ARRAYS_NEUTRAL.json','b570/RAW_OUTPUT_PROVENANCE.json','rtx/SELECTED_ATTEMPTS.json']}
 (REV/'UNIFIED_RECOMPUTATION_RECEIPT.json').write_text(json.dumps(dict(status='PASS',sources=provenance,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),anonymous_zip_sha256=hashlib.sha256(zpath.read_bytes()).hexdigest(),groups=result['groups']),indent=2)+'\n')
 print(json.dumps({'status':'PASS','arrays':len(records),'tasks':len(result['task_rows']),'zip':str(zpath)}))
if __name__=='__main__':main()
