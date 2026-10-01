#!/usr/bin/env python3
"""Anonymous study-separated exports; original evidence and prior ZIPs stay intact."""
import argparse,hashlib,json,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'paper/mlsys2027/evidence';OUT=ROOT/'paper/mlsys2027/manuscript/output'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def encoded(v):return (json.dumps(v,indent=2)+'\n').encode()
def package(work):
 data=read(work.parent/'FOLLOWUP_RAW_REPLAY_V086.json')['studies'];p=read(ROOT/'benchmarks/b570_mechanism_v08/RESERVED_PREDICTIONS.json');old=work/'b570_mechanism_v08/artifacts/b570_mechanism_v08/raw/reserved_outcomes/ids';rows=[]
 for x in p['predictions']:
  raw=read(old/(x['task_id'].replace('/','_')+f"-r{x['repetition']}.json"));cut=min(128,next((i+1 for i,v in enumerate(raw['eog']) if v),len(raw['ids'])));live=raw['ids'][:cut];assert len(live)==128 and live==x['predicted_ids'];rows.append({'task_id':x['task_id'],'repetition':x['repetition'],'arrays':{'reference':x['reference_ids'],'prediction':x['predicted_ids'],'live':live}})
 data['B570_original_H1']={'rows':rows,'endpoint':'All arrays reach 128 IDs; no earlier EOG observed','distinct_prompts':24,'repetitions':3}
 data['RTX_H2']['qualification_status']='BLOCKED';data['RTX_H2']['prediction_status']='MATCH'
 # These arrays/numeric records have no path, Git author, absolute time or host fields.
 files={'evidence/'+n+'.json':encoded(v) for n,v in data.items()}
 files['verify_original.py']=(ROOT/'paper/mlsys2027/scripts/verify_anonymous_v085.py').read_bytes()
 files['verify.py']=(ROOT/'paper/mlsys2027/scripts/verify_anonymous_v086.py').read_bytes()
 inputs=read(E/'DERIVED_INPUTS_V086.json');result=read(E/'DERIVED_ANALYSIS_V086.json');result={k:result[k] for k in ('post_study','B570','M4','358H','RTX')}
 files['derived/inputs.json']=encoded(inputs);files['derived/results.json']=encoded(result)
 analysis=(ROOT/'paper/mlsys2027/scripts/analyze_existing_records_v086.py').read_text().replace('ROOT = Path(__file__).resolve().parents[3]','ROOT = Path(__file__).resolve().parent')
 files['analysis.py']=analysis.encode()
 files['derived/H2_input_audit.json']=encoded({k:v for k,v in read(E/'H2_INPUT_AUDIT_V086.json').items() if k!='source_objects'})
 for name in ('B570_SCORE_ROWS_V086.csv','B570_LATER_CASES_V086.csv','M4_PROMPT_RATIOS_V086.csv','RTX_ABSOLUTE_LATENCY_V086.csv'):files['derived/'+name]=(E/name).read_bytes()
 files['derived/PLAN.md']=b'Existing-record post-study calculations; aggregate outcomes were known. No original endpoints or CI streams replaced. All 72 B570 forks/216 logits, all 540 M4 raw times and 60 medians, all 180 358H processed observations, all 180 RTX raw times are retained as exported inputs. Signed deltas alternate minus primary; linear descriptive percentiles. New secondary family-stratified seed2026100101, 10000 paired draws, HumanEval then Spec-Bench30/30. Original RTX seed2026093002 and ratio preserved. 358H bound is arithmetic fixed-progress/fixed-target-work/fixed-baseline with nonnegative draft/residual. No inference or deployment extrapolation. Missing logging-cost records are not imputed. Full original freeze/time/binary authentication outside scope.\n'
 capsule=next((ROOT/'artifacts/rtx_independent_proposal_replay_v2').glob('anonymous-*.tar.gz'));capsule_sha=hashlib.sha256(capsule.read_bytes()).hexdigest()
 files['INDEX.json']=encoded({'version':'v0.8.6','studies':list(data),'separate_capsule':{'filename':capsule.name,'sha256':capsule_sha,'bytes':capsule.stat().st_size,'entry':'python -B EXTRACTED/frozen_source/scripts/platform/rtx_independent_proposal_replay_v2/offline.py EXTRACTED'},'derived_analysis':{'status':'POST_STUDY','inputs':'derived/inputs.json','results':'derived/results.json','entry':'python3 -B verify.py'},'freeze_roles':{'B570_H1':['hypothesis before reserved inference','72 arrays before reserved live'],'B570_fork':['sampled policy before reserved','known-outcome post-study descriptors'],'RTX_H1':['failed discovery; no reserved freeze/live'],'RTX_H2':['F0 source/config','F1 selected program','F2 arrays/tapes before live'],'RTX_cost':['timer/config before qualification/formal'],'M4':['actual calibration-policy freeze; build-manifest wrong-field preserved'],'358H':['original processed complete-cost records; new conditional arithmetic']},'export_boundary':'Arrays are element-identical; exported file/tape hashes are derived. No absolute chronology, author or host identity. Content hashes may permit linkage; no unlinkability guarantee.'})
 files['README.md']=('''# Anonymous evidence index — v0.8.6

Extract this ZIP into a new empty directory, then run `python3 -B verify.py`.
Python 3.11+ standard library suffices; no hardware, models or network required.
Study-separated complete arrays, paired fork scores/actual decisions/continuations,
and condition latency times are included. Original B570 H1 uses 24×3 cap runs;
RTX H2 uses another 24×3 set with earlier EOG and cap endpoints. H2 prediction
matches 72/72 but reference qualification fails at 60/72. B570 immediate fork
decisions remain equal despite scores and some later trajectories changing.

The larger H2 tape/events capsule is separate: see INDEX.json for exact filename,
length and SHA256. Extract that tar.gz into another new directory and execute its
own offline.py as documented in INDEX.json. Its retained original digests may
link to original evidence; anonymity is not a guarantee of unlinkability.

The derived/ directory adds post-study inputs, distributions, conditional arithmetic and a new family-stratified sensitivity stream. verify.py executes both unchanged original scientific assertions and new derived calculations. Source ZIPs reconstruct PDFs; this index/capsule recomputes retained observations.
Arrays are compared element by element against the sealed original records.
Original raw evidence and earlier outputs remain unchanged. Host paths, author
metadata, identity and exact UTC records are excluded from these compact exports.
Derived file hashes do not equal the original file digests; ordinal chronology
cannot authenticate original remote freeze times. Omitted weight/runtime/compiler/
driver bytes and omitted full logits are not authenticated; no model execution,
new measurements or functional HumanEval pass@k. No online upload is implied.
''').encode()
 for n,b in files.items():
  t=b.decode();assert not any(v.casefold() in t.casefold() for v in ('leecdiang','/Users/','D:\\','C:\\','github.com/leecdiang','/home/')),n
 files['SHA256SUMS.json']=encoded({n:hashlib.sha256(b).hexdigest() for n,b in sorted(files.items())});out=OUT/'anonymous-evidence-index-v0.8.6.zip';out.parent.mkdir(exist_ok=True)
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for n,b in sorted(files.items()):
   info=zipfile.ZipInfo(n,(2026,10,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
 dest=Path(tempfile.mkdtemp(prefix='heterospec-v086-anonymous-'))
 with zipfile.ZipFile(out) as z:z.extractall(dest)
 p=subprocess.run([sys.executable,'-B',str(dest/'verify.py')],capture_output=True,check=True)
 receipt={'status':'RERUN_PASS','zip_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'element_identical_to_original':True,'verification':json.loads(p.stdout),'separate_capsule':{'path':str(capsule.relative_to(ROOT)),'filename':capsule.name,'sha256':capsule_sha},'prior_v084_zip':'UNAVAILABLE: no v084 sequence ZIP is retained in this checkout; old original 72 arrays exported without overwriting any prior package','anonymity':'No host/identity/absolute-time metadata in compact export; digests do not guarantee unlinkability.'}
 (E/'ANONYMOUS_EXPORT_V086_QA.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':'RERUN_PASS','zip_sha256':receipt['zip_sha256'],'studies':list(data)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);a=p.parse_args();package(a.work.resolve())
