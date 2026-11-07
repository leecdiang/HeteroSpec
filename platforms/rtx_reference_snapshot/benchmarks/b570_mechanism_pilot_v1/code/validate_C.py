"""Independent CPU parser for one frozen candidate, no execution imports."""
from pathlib import Path
import json,hashlib,sys
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def diff(a,b):
 for i,(x,y) in enumerate(zip(a,b)):
  if x!=y:return i
 return None if len(a)==len(b) else min(len(a),len(b))
checks=0;errors=[]
def ck(v,m):
 global checks;checks+=1
 if not v:errors.append(m)
def main():
 hist=load(R/'HISTORICAL_PARENTS.json');manifest=load(R/'C_MANIFEST.json');freeze=load(R/'C_FREEZE.json');eog=set(load(R/'dependencies/TOKENIZATION_PROOF.json')['runtime_eog_ids']);rows=[];group={};failed=False
 for u in manifest['units']:
  p=R/'raw'/hashlib.sha256(u['unit_id'].encode()).hexdigest()[:20]/'RESULT.json'
  if not p.exists():continue
  ck(not failed,'no candidate inference after scientific failure '+u['unit_id']);r=load(p)
  for f,h in r['files'].items():ck(sha(R/f)==h,'raw hash '+f)
  raw=load(R/next(f for f in r['files'] if f.endswith('/capture.json')));ref=hist[u['task']+'/R_reference']['endpoint'];ids=raw['ids'];flags=raw['eog']
  ck(flags==[t in eog for t in ids],'authentic all raw EOG '+u['unit_id']);n=min(128,next((i+1 for i,t in enumerate(ids) if t in eog),len(ids)))
  endpoint=dict(ids=ids[:n],eog=flags[:n],reason='EOG' if ids[n-1] in eog else 'CAP',raw_suffix=len(ids)-n)
  ck(endpoint==r['endpoint'],'full endpoint and suffix '+u['unit_id']);passed=endpoint['ids']==ref['ids'] and endpoint['eog']==ref['eog'] and endpoint['reason']==ref['reason'];failed=not passed
  ck(r['config']==u['config'],'fixed one configuration '+u['unit_id']);st=load(R/next(f for f in r['files'] if f.endswith('/START.json')));ck(st['utc']>freeze['utc'],'C source frozen before output '+u['unit_id'])
  phase=r['metrics']['phase_binding'];ck(phase['same_context'] and not phase['state_transfer'] and phase['source_ub']==128 and phase['destination_ub']==1 and phase['pending_id']==ids[0],'real in-place phase binding '+u['unit_id'])
  ck(raw['transfer'] is None,'no legacy state witness handoff '+u['unit_id'])
  if u['config']['capture']:
   before=next(f for f in r['files'] if f.endswith('.phase_before.kv'));after=next(f for f in r['files'] if f.endswith('.phase_after.kv'));ck(sha(R/before)==sha(R/after) and phase['capture_kv_equal'],'whole serialized state retained through binding '+u['unit_id'])
  else:ck(phase['capture_state_bytes']==0 and phase['capture_kv_equal'] is None,'off performs no state readback '+u['unit_id'])
  group.setdefault(u['task'],[]).append(raw)
  rows.append(dict(unit_id=u['unit_id'],task=u['task'],round=u['config']['round'],qualified=passed,first_difference=diff(endpoint['ids'],ref['ids']),complete_canonical_reference_length=len(ref['ids']),complete_candidate_length=n,raw_count=len(ids),raw_suffix=len(ids)-n,reason=endpoint['reason']))
 for task,v in group.items():
  if len(v)==2:ck(v[0]['ids']==v[1]['ids'] and v[0]['eog']==v[1]['eog'],'candidate full raw capture switch stable '+task)
 for f,h in freeze['binaries'].items():ck(sha(R/f)==h,'candidate unchanged binary '+f)
 source=(R/'candidate-front/native.cpp').read_text(encoding='utf8');ck(all(x not in source for x in ['HumanEval/','MBPP/','HISTORICAL_PARENTS','reference_ids','future_tape']),'no candidate answer/task routing')
 gate='FAIL' if failed else 'PASS' if len(rows)==12 else 'INCOMPLETE'
 result=dict(status='PASS' if not errors else 'FAIL',checks=checks,errors=errors,scientific_gate=gate,planned=12,complete=len(rows),rows=rows,one_family=True,scientific_reruns=0,qualification='All cap128 IDs and runtime EOG/length/endpoint versus immutable ordinary R; full untrimmed raw and native overshoot suffix retained and charged; capture on/off raw stability where both ran',paid_speed_result='NOT_MEASURED; C is diagnostic only')
 (R/'C_VERIFICATION.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print(result['status'],gate,len(rows),checks,errors[:10]);return result
if __name__=='__main__':main()
