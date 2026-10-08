"""Independent capture bridge of the new target frontend; CPU only."""
from pathlib import Path
import sys,json,hashlib
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 manifest=load(R/'E_MANIFEST.json');hist=load(R/'HISTORICAL_PARENTS.json');eog=set(load(R/'dependencies/TOKENIZATION_PROOF.json')['runtime_eog_ids']);checks=0;errors=[];rows=[];groups={}
 def ck(v,s):
  nonlocal checks;checks+=1
  if not v:errors.append(s)
 for session in manifest['bridge_sessions']:
  for u in session['units']:
   p=R/'raw'/hashlib.sha256(u['unit_id'].encode()).hexdigest()[:20]/'RESULT.json';ck(p.exists(),'bridge missing '+u['unit_id'])
   if not p.exists():continue
   r=load(p)
   for f,h in r['files'].items():ck(sha(R/f)==h,'raw SHA '+f)
   x=load(R/next(f for f in r['files'] if f.endswith('/capture.json')));ids=x['ids'];flags=x['eog'];ck(flags==[t in eog for t in ids],'full EOG '+u['unit_id']);n=min(128,next((i+1 for i,t in enumerate(ids) if t in eog),len(ids)));ref=hist[u['task']+'/R_reference']['endpoint'];reason='EOG' if ids[n-1] in eog else 'CAP';passed=ids[:n]==ref['ids'] and flags[:n]==ref['eog'] and reason==ref['reason'];phase=r['metrics']['phase_binding'];ck(phase['same_context'] and phase['source_ub']==128 and phase['destination_ub']==1 and phase['pending_id']==ids[0] and not phase['state_transfer'],'real live phase binding '+u['unit_id'])
   if session['config']['capture']:
    before=next(f for f in r['files'] if f.endswith('.phase_before.kv'));after=next(f for f in r['files'] if f.endswith('.phase_after.kv'));ck(sha(R/before)==sha(R/after) and phase['capture_kv_equal'],'live serialized state unchanged '+u['unit_id'])
   else:ck(phase['capture_state_bytes']==0 and phase['capture_kv_equal'] is None,'no off state reads '+u['unit_id'])
   groups.setdefault(u['task'],[]).append(x);rows.append(dict(**u,qualified=passed,round=session['config']['round']))
 for task,x in groups.items():
  if len(x)==2:ck(x[0]['ids']==x[1]['ids'] and x[0]['eog']==x[1]['eog'],'full raw capture switch '+task)
 gate='PASS' if len(rows)==8 and all(x['qualified'] for x in rows) and not errors else 'FAIL'
 result=dict(status='PASS' if not errors else 'FAIL',scientific_gate=gate,checks=checks,errors=errors,planned=8,complete=len(rows),rows=rows)
 (R/'E_BRIDGE_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(result['status'],gate,checks,errors[:8]);return result
if __name__=='__main__':main()
