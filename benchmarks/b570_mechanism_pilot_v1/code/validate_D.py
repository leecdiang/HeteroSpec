"""Independent full exposed qualification parser; no executor imports."""
from pathlib import Path
import json,hashlib,sys
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 m=load(R/'D_MANIFEST.json');refs=load(R/'D_REFERENCES.json');eog=set(load(R/'dependencies/TOKENIZATION_PROOF.json')['runtime_eog_ids']);rows=[];errors=[];checks=0;groups={};failed=False
 def ck(v,t):
  nonlocal checks;checks+=1
  if not v:errors.append(t)
 for u in m['units']:
  p=R/'raw'/hashlib.sha256(u['unit_id'].encode()).hexdigest()[:20]/'RESULT.json'
  if not p.exists():rows.append(dict(**u,status='NOT_RUN_GATED' if failed else 'NOT_RUN'));continue
  ck(not failed,'no continuation after failure '+u['unit_id']);r=load(p)
  for f,h in r['files'].items():ck(sha(R/f)==h,'raw SHA '+f)
  x=load(R/next(f for f in r['files'] if f.endswith('/capture.json')));ids=x['ids'];flags=x['eog'];ck(flags==[t in eog for t in ids],'complete raw EOG '+u['unit_id']);n=min(128,next((i+1 for i,t in enumerate(ids) if t in eog),len(ids)));ref=refs[u['task']]
  ep=dict(ids=ids[:n],eog=flags[:n],reason='EOG' if ids[n-1] in eog else 'CAP',raw_suffix=len(ids)-n);ck(ep==r['endpoint'],'complete endpoint/suffix '+u['unit_id']);passed=all(ep[k]==ref[k] for k in ['ids','eog','reason']);failed=not passed
  d=next((i for i,(a,b) in enumerate(zip(ids[:n],ref['ids'])) if a!=b),None)
  if d is None and n!=len(ref['ids']):d=min(n,len(ref['ids']))
  groups.setdefault(u['task'],[]).append(x)
  rows.append(dict(**u,status='PASS' if passed else 'FAIL',qualified=passed,first_difference=d,raw_count=len(ids),raw_suffix=len(ids)-n,endpoint_count=n,reason=ep['reason']))
 for task,rs in groups.items():
  if len(rs)==2:ck(rs[0]['ids']==rs[1]['ids'] and rs[0]['eog']==rs[1]['eog'],'full raw repeat stability '+task)
 complete=sum(v['status'] in ['PASS','FAIL'] for v in rows);gate='FAIL' if failed else 'PASS' if complete==112 and all(v['status']=='PASS' for v in rows) else 'INCOMPLETE'
 result=dict(status='PASS' if not errors else 'FAIL',checks=checks,errors=errors,scientific_gate=gate,planned=112,complete=complete,qualified=sum(v['status']=='PASS' for v in rows),matrix=rows,all_inputs_exposed=True)
 (R/'D_VERIFICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(result['status'],gate,complete,checks,errors[:10]);return result
if __name__=='__main__':main()
