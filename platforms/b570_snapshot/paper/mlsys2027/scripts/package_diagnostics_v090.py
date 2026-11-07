#!/usr/bin/env python3
"""Extend immutable v088 members; run only the new independent diagnostics."""
from pathlib import Path
import hashlib,json,zipfile,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[3]
P=ROOT/'paper/mlsys2027';OUT=P/'manuscript/output';E=P/'evidence'
R=P/'reviews/acceptance_reassessment_v089'
sha=lambda b:hashlib.sha256(b).hexdigest()
def package():
 prior=OUT/'anonymous-evidence-index-v0.8.8.zip'
 with zipfile.ZipFile(prior) as z:old={n:z.read(n) for n in z.namelist()}
 source=(R/'acceptance_diagnostic.py').read_text()
 start=source.index('REPO=HERE.parents[3]');end=source.index('def gm(values):')
 source=source[:start]+"def bytes_for(name): return (HERE/name).read_bytes()\ndef read(name): return json.loads(bytes_for(name))\n"+source[end:]
 source=source.replace("canonical=REPO/'analysis/358h_phase3_prompt_summary.csv'", "canonical=HERE/'derived/358h_phase3_prompt_summary.csv'")
 source=source.replace("(HERE/'acceptance_diagnostic.json').write_text(json.dumps(result,indent=2)+'\\n')", "expected=json.loads((HERE/'derived/ACCEPTANCE_DIAGNOSTIC_V090.json').read_text())\nassert result==expected, 'diagnostic result mismatch'")
 source=source.replace('import collections, csv, hashlib, json, math, statistics, zipfile','import collections, csv, hashlib, json, math, statistics')
 marker="HERE=Path(__file__).resolve().parent\n"
 checks="""manifest=json.loads((HERE/'SHA256SUMS_V090.json').read_text())
for name,digest in manifest.items():
 assert not Path(name).is_absolute() and '..' not in Path(name).parts
 assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest, name
"""
 source=source.replace(marker,marker+checks)
 source=source[:source.index('print(json.dumps(')]+"print(json.dumps({'status':'PASS','scope':'New post-study diagnostics only; original denominators; no model execution or bootstrap','358H_prompt_ceiling':{k:v['new_prompt_gm_upper_bound'] for k,v in result['358H'].items()},'B570_nonreference_positions':result['B570']['distinct_nonreference_predicted_positions'],'RTX_hindsight_two_array_coverage':result['RTX']['retrospective_two_target_only_array_oracle_prompts'],'M4_fixed_mode_oracle_ratio':result['M4']['always_over_two_fixed_mode_oracle_gm']}))\n"
 new={'verify_v090.py':source.encode(),'derived/ACCEPTANCE_DIAGNOSTIC_V090.json':(R/'acceptance_diagnostic.json').read_bytes(),'derived/358h_phase3_prompt_summary.csv':(ROOT/'analysis/358h_phase3_prompt_summary.csv').read_bytes()}
 new['README_V090.txt']=b'''V0.9.0 EXTENSION -- POST-STUDY DIAGNOSTICS
Run python3 -B verify_v090.py for new retained-record analysis.
It checks the extended manifest and calculates trajectory extents,
358H prompt-estimator ceilings and M4 two-fixed-mode opportunity.
All 30 prior v0.8.8 members retain their original bytes. Their verify.py
is available for full prior replay, but was not rerun in this revision.
Outcomes were known. No new inference, samples, bootstrap or intervals.
Positions/repeats are correlated. 358H budgets fix baseline/work/progress
and assume zero other cost; no optimization is achieved.
RTX hindsight array selection is not a predictor; the M4 two-mode
comparison does not bound arbitrary within-request switching.
No raw KV/sampler, omitted binaries or trusted time are authenticated.
The old README/INDEX/hash list identify prior scope; this extension uses
INDEX_V090.json and SHA256SUMS_V090.json.
'''
 new['INDEX_V090.json']=(json.dumps({'version':'v0.9.0','kind':'known-outcome retained-record extension','prior_package':{'filename':prior.name,'bytes':prior.stat().st_size,'sha256':sha(prior.read_bytes()),'members':{n:sha(b) for n,b in old.items()}},'canonical_358H_csv_sha256':sha(new['derived/358h_phase3_prompt_summary.csv']),'verification':'python3 -B verify_v090.py','limits':['No original asset/state/absolute chronology authentication','No new experiments or confidence intervals','Original cohorts and comparators retained']},indent=2)+'\n').encode()
 assert not set(new)&set(old)
 files=old|new
 files['SHA256SUMS_V090.json']=(json.dumps({n:sha(b) for n,b in sorted(files.items())},indent=2)+'\n').encode()
 target=OUT/'anonymous-evidence-index-v0.9.0.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
  for n,b in sorted(files.items()):
   i=zipfile.ZipInfo(n,(2026,10,3,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;z.writestr(i,b)
 runs=[]
 for _ in range(2):
  with tempfile.TemporaryDirectory(prefix='diagnostic-v090-') as d:
   with zipfile.ZipFile(target) as z:z.extractall(d)
   r=subprocess.run([sys.executable,'-B','verify_v090.py'],cwd=d,check=True,text=True,capture_output=True)
   runs.append(json.loads(r.stdout))
 assert runs[0]==runs[1]
 with zipfile.ZipFile(target) as z:assert all(z.read(n)==b for n,b in old.items())
 diagnostic=json.loads(new['derived/ACCEPTANCE_DIAGNOSTIC_V090.json'])
 (E/'ACCEPTANCE_DIAGNOSTICS_V090.json').write_bytes(new['derived/ACCEPTANCE_DIAGNOSTIC_V090.json'])
 report={'status':'PASS','scope':'Only new diagnostic calculator executed twice in fresh extractions; old verifiers/bootstrap not executed','new_package':{'path':str(target.relative_to(ROOT)),'bytes':target.stat().st_size,'sha256':sha(target.read_bytes())},'prior_package':{'path':str(prior.relative_to(ROOT)),'bytes':prior.stat().st_size,'sha256':sha(prior.read_bytes())},'prior_members_byte_identical':len(old),'new_members':sorted(set(files)-set(old)),'two_clean_calculations':runs,'canonical_csv_sha256':sha(new['derived/358h_phase3_prompt_summary.csv']),'diagnostic_JSON_sha256':sha(new['derived/ACCEPTANCE_DIAGNOSTIC_V090.json']),'manuscript_values':{'CPU_ceiling':f"{diagnostic['358H']['CPU']['new_prompt_gm_upper_bound']:.4f}",'NPU_ceiling':f"{diagnostic['358H']['NPU']['new_prompt_gm_upper_bound']:.4f}",'CPU_target_work_reduction_percent':f"{100*(1-diagnostic['358H']['CPU']['new_prompt_gm_upper_bound']):.2f}",'NPU_target_work_reduction_percent':f"{100*(1-diagnostic['358H']['NPU']['new_prompt_gm_upper_bound']):.2f}"},'model_execution':False}
 (E/'DIAGNOSTIC_PACKAGE_V090_QA.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'status':'PASS','old_members_unchanged':len(old),'new_members':len(files)-len(old),'two_fresh_runs':len(runs),'bytes':target.stat().st_size}))
 return report
if __name__=='__main__':package()
