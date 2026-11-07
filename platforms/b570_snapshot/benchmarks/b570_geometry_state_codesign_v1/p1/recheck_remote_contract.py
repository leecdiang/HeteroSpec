"""Derive cadence failure again from remote CAS raw bytes, not a saved PASS/FAIL field."""
import pathlib,sys,json,zipfile,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'p1'))
from protocol import encode,write_new,file_sha
from contract_audit import evaluate
archive=ROOT/'_host/P1_REMOTE_COMPLETE_CAS.zip';rows=[]
with zipfile.ZipFile(archive) as z:
 m=json.loads(z.read('MANIFEST.json'));files={x['path']:x for x in m['files']}
 def value(path):
  x=files[path];data=z.read('objects/'+x['sha256']);assert hashlib.sha256(data).hexdigest()==x['sha256'];return json.loads(data)
 plan=value('p0/PLAN_P1.json');f0=value('p0/F0_EXECUTION.json')
 for s in plan['slots']:
  path='_host/run/'+s['slot']+'/'+s['slot']+('.trace.json' if s['mode']=='diagnostic' else '.memory.json')
  if path not in files:continue
  x=value(path);v=x['memory'] if s['mode']=='diagnostic' else x;rows.append(dict(slot=s['slot'],task=s['task'],arm=s['arm'],requested_period_ms=v['requested_period_ms'],max_observed_gap_ms=v['max_observed_gap_ms']))
 rebuilt=evaluate(f0,rows);prior=value('p1/EXECUTION_CONTRACT_AUDIT.json');assert rebuilt['status']=='VIOLATION_REQUIRES_STOP' and rebuilt['violations']==prior['violations']
 write_new(ROOT/'p1/REMOTE_CONTRACT_RECHECK.json',dict(status='PASS_INDEPENDENT_REMOTE_RAW_REDERIVATION_OF_FAILURE',scientific_status='F0_SAMPLING_CONTRACT_VIOLATED_NOT_REPAIRED',remote_archive_sha256=file_sha(archive),raw_receipts_reconstructed=len(rows),violations=rebuilt['violations'],native_starts_added=0))
 print('Remote raw cadence independently rederived:8 violations; scientific status remains failed')
