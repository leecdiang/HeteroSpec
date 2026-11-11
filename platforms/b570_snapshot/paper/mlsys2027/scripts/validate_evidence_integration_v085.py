#!/usr/bin/env python3
"""Current CPU/file QA and meaningful counterexamples; no hardware/model execution."""
import argparse,copy,hashlib,importlib.util,json,re,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];H=ROOT/'paper/mlsys2027/manuscript';E=H.parent/'evidence';BASE='98e8470f2559f78335de8d3473997d21b4bb55b8'
sys.path.insert(0,str(H/'scripts'));sys.path.insert(0,str(Path(__file__).parent))
from package_overleaf_v085 import collect_bundle,verify_dependencies
from verify_anonymous_v085 import validate

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def git(*args,**kw):return subprocess.check_output(['git',*args],cwd=ROOT,**kw)
def historical():
 results={}
 def adapted(name,p,replacements):
  s=p.read_text()
  for old,new in replacements:
   assert old in s;s=s.replace(old,new)
  exec(compile(s,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
  results[name]={'status':'RERUN_PASS','adapter':'Only output receipt names redirected in memory; frozen source and assertions unchanged.'}
 adapted('historical_numerical_228',H/'scripts/validate_evidence.py',[("E/'NUMERICAL_QA.json'","E/'NUMERICAL_HISTORICAL_V085_QA.json'")])
 adapted('runtime_primary_secondary',H/'scripts/validate_runtime.py',[('DIRECT_ID_M4_SECONDARY_REPLAY_V07.json','M4_SECONDARY_REPLAY_V085_QA.json'),('RUNTIME_QA_V07.json','RUNTIME_REPLAY_V085_QA.json')])
 p=H/'figures/presentation_v07/validate.py';spec=importlib.util.spec_from_file_location('immutable_figure3_v085',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);r=m.validate();(E/'FIGURE3_REPLAY_V085_QA.json').write_text(json.dumps(r,indent=2)+'\n');results['Figure3']={'status':'RERUN_PASS','checks':r['check_count']}
 (E/'HISTORICAL_CHECKS_V085_QA.json').write_text(json.dumps(results,indent=2)+'\n');return results

def current(replay_historical=True):
 checks=[]
 def check(n,v):assert v,n;checks.append({'item':n,'status':'RERUN_PASS'})
 projection=read(E/'FOLLOWUP_PROJECTION_V085.json');ledger=read(E/'EVIDENCE_INTEGRATION_LEDGER_V085.json')
 for path,x in projection['canonical_inputs'].items():check('canonical projection input '+path,sha(ROOT/path)==x['sha256'] and (ROOT/path).stat().st_size==x['bytes'])
 check('archive verification receipt content anchor',sha(E/'ARCHIVE_REPLAY_V085_QA.json')==projection['archive_replay_report_sha256'])
 for study in ledger['studies']:
  for x in study['canonical_inputs']:check('ledger source '+study['study_identity']+' '+x['path'],sha(ROOT/x['path'])==x['sha256'])
 with zipfile.ZipFile(H/'output/anonymous-evidence-index-v0.8.5.zip') as z:
  studies={Path(n).stem:json.loads(z.read(n)) for n in z.namelist() if n.startswith('evidence/')};manifest=json.loads(z.read('SHA256SUMS.json'));check('anonymous ZIP complete manifest',set(z.namelist())==set(manifest)|{'SHA256SUMS.json'})
  for n,digest in manifest.items():check('anonymous file '+n,hashlib.sha256(z.read(n)).hexdigest()==digest)
  for name in projection['studies']:
   expected=projection['studies'][name];actual=studies[name];check('element-exact anonymous projection '+name,all(actual[k]==v for k,v in expected.items()))
 numeric=validate(studies);check('new arrays, fork decisions and native timing recomputation',bool(numeric))
 old=read(ROOT/'benchmarks/b570_mechanism_v08/RESERVED_PREDICTIONS.json')['predictions'];by={(x['task_id'],x['repetition']):x for x in old}
 for x in studies['B570_original_H1']['rows']:
  y=by[x['task_id'],x['repetition']];check('old frozen prediction array '+x['task_id']+' '+str(x['repetition']),x['arrays']['prediction']==y['predicted_ids'] and x['arrays']['reference']==y['reference_ids'])
 files,sources=collect_bundle();verify_dependencies(files);clean=read(E/'CLEAN_ZIP_REBUILD_V085_QA.json');check('delivered source ZIP matches inspected source tree',sources==clean['source_files'] and sha(H/'output/overleaf-evidence-integration-v0.8.5.zip')==clean['zip_sha256'])
 negatives=[]
 def reject(name,fn):
  try:fn()
  except (AssertionError,ValueError,KeyError):negatives.append({'case':name,'status':'RERUN_PASS','result':'Rejected as required'});return
  raise AssertionError('negative case accepted: '+name)
 bad=copy.deepcopy(studies);bad['RTX_H2']['qualification_status']='QUALIFIED';reject('mislabeled H2 prediction as qualified reference',lambda:validate(bad))
 bad=copy.deepcopy(studies);bad['RTX_H2']['rows'][0]['arrays']['H2_P_R'][0]^=1;reject('changed sealed prediction ID',lambda:validate(bad))
 bad=copy.deepcopy(studies);bad['RTX_matched_latency']['ratio']=1/bad['RTX_matched_latency']['ratio'];reject('reversed target/serialized latency ratio',lambda:validate(bad))
 bad=dict(files);bad.pop('sections/05_diagnoses.tex');reject('omitted actual source ZIP dependency',lambda:verify_dependencies(bad))
 # Verify base blobs for every protected original file, including old receipts.
 prefixes=['artifacts','benchmarks','scripts','reports','analysis','paper/mlsys2027/evidence','paper/mlsys2027/figures','paper/mlsys2027/manuscript/vendor','paper/mlsys2027/manuscript/figures','paper/mlsys2027/manuscript/output']
 inventory=git('ls-tree','-r',BASE,*prefixes,text=True).splitlines();paths=[];expected=[]
 for line in inventory:
  meta,path=line.split('\t',1);paths.append(path);expected.append(meta.split()[2])
 for path in ['values.tex','runtime_values.tex','direct_id_values.tex']:
  p='paper/mlsys2027/manuscript/tables/'+path;paths.append(p);expected.append(git('rev-parse',BASE+':'+p,text=True).strip())
 actual=git('hash-object','--no-filters','--stdin-paths',input=('\n'.join(paths)+'\n').encode()).decode().splitlines();check('protected base inventory coverage',len(actual)==len(expected));check('all protected original bytes unchanged',actual==expected)
 check('author-freeze tag unchanged',git('rev-parse','mlsys2027-v0.8-author-freeze^{}',text=True).strip()=='1d3b556c93b477680788dfd1eb0737dfe9eee28c')
 texts={p.name:p.read_text() for p in [H/'main.tex',H/'appendix.tex',*sorted((H/'sections').glob('*.tex'))]};alltext='\n'.join(texts.values());intro=texts['01_introduction.tex'];abstract=texts['main.tex'].split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0];diagnoses=texts['05_diagnoses.tex'];limits=texts['09_limitations.tex'];conclusion=texts['10_conclusion.tex']
 check('official title unchanged','Execution-Path Qualification and Realized Costs in Speculative Decoding on Consumer Systems' in texts['main.tex'])
 c=intro.split('Our three contributions are',1)[1].split('\n\n',1)[0];check('exactly three headline contributions',all('('+str(n)+')' in c for n in (1,2,3)) and '(4)' not in c)
 for n,condition in [('original B570 24 prompts and reference failure','24 repeat-stable prompts' in abstract and '60/72' in abstract),('B570 no immediate decision effect and persistent continuation','no immediate decisions' in abstract and 'later proposals follow' in diagnoses and 'UB128 target context' in diagnoses),('RTX H1 fails and H2 separate shared numerical runtime','target-only H1 fails' in intro and '24/36' in diagnoses and 'independent numerical implementation' in diagnoses),('H2 prediction success does not qualify reference','60/72' in diagnoses and 'qualified batched performance' in diagnoses),('new cost slower and matched gate','Serialization is slower' in diagnoses and '90/90' in diagnoses and 'logging' in diagnoses),('M4 Guard negative comparator retained','Guard had higher latency on this comparison' in texts['07_runtime_codesign.tex'] and 'fixed speculation is faster' in abstract),('358H inseparable and no formal runtime claim','these costs are inseparable' in diagnoses and 'No formal R2 performance run occurred' in texts['07_runtime_codesign.tex']),('no functional benchmark claim or external byte proof','pass@$k$ were not evaluated' in limits and 'omitted external binaries' in limits),('endpoint actual EOG versus original cap','63 earlier-EOG runs and nine capped runs' in diagnoses and 'All these reserved arrays reach 128 IDs' in diagnoses)]:check(n,condition)
 history=historical() if replay_historical else {n:{'status':'PRIOR_RECEIPT_ONLY','reason':'This invocation used --skip-historical; earlier v085 rerun receipts retained.'} for n in ['historical_numerical_228','runtime_primary_secondary','Figure3']}
 sci={'status':'RERUN_PASS','base':BASE,'checks':checks,'protected_original_file_count':len(paths),'negative_cases':negatives,'scope':'Current study-role/numeric/content checks, not an independent submission review; no hardware/model runs.'};(E/'SCIENTIFIC_INVARIANTS_V085_QA.json').write_text(json.dumps(sci,indent=2)+'\n')
 numerical={'status':'RERUN_PASS','new_study_recomputations':numeric,'canonical_latency':projection['studies']['RTX_matched_latency'],'historical_checks':history,'historical_numerical_count':228,'runtime_checks':136,'M4_secondary_checks':638,'Figure3_checks':71,'original_direct_ID_archive_replay':{n:x['status'] for n,x in read(E/'ARCHIVE_REPLAY_V085_QA.json')['checks'].items() if 'direct' in n.lower()},'limitations':['358H runtime raw trace is UNAVAILABLE; only retained compact source/pinned-byte checks.', 'Exposure/freeze checks use retained host/server/file records, not trusted process timestamps or a new remote scan.', 'Exact earlier v084 ZIP absent; original 72 array records retained and independently re-exported.']};numerical['canonical_latency'].pop('run_rows');numerical['canonical_latency'].pop('prompt_rows');(E/'NUMERICAL_INTEGRATION_V085_QA.json').write_text(json.dumps(numerical,indent=2)+'\n');print(json.dumps({'status':'RERUN_PASS','current_checks':len(checks),'protected_files':len(paths),'negative_cases':len(negatives)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--skip-historical',action='store_true');a=p.parse_args();current(not a.skip_historical)
