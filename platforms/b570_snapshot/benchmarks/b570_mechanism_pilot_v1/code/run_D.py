"""Fixed exposed qualification expansion; no new baseline or candidate tuning."""
from pathlib import Path
import uuid,traceback,hashlib
import candidate_runner as r
R=Path(__file__).parent
def first_difference(a,b):
 for i,(x,y) in enumerate(zip(a,b)):
  if x!=y:return i
 return None if len(a)==len(b) else min(len(a),len(b))
def main():
 assert r.read(R/'C_VERIFICATION.json')['scientific_gate']=='PASS'
 f=r.read(R/'D_FREEZE.json')
 for name,h in f['files'].items():assert r.sha(R/name)==h
 manifest=r.read(R/'D_MANIFEST.json');panel={i['id']:i for i in r.read(R/'D_INPUTS.json')};refs=r.read(R/'D_REFERENCES.json');rows=[];failed=False
 r.acquire();r.STAGE='D'
 try:
  for round in [1,2]:
   units=[u for u in manifest['units'] if u['round']==round];conf=manifest['config'];conf=dict(conf,round=round)
   s=r.Session('D-'+str(round)+'-'+uuid.uuid4().hex[:6],conf)
   try:
    s.request(f'D/{round}/WARM/'+s.name,panel['HumanEval/134'],True)
    for unit in units:
     p=R/'raw'/hashlib.sha256(unit['unit_id'].encode()).hexdigest()[:20]/'RESULT.json'
     if p.exists():result=r.read(p);assert all(r.sha(R/n)==h for n,h in result['files'].items())
     else:result=s.request(unit['unit_id'],panel[unit['task']])
     ref=refs[unit['task']];ep=result['endpoint'];passed=ep['ids']==ref['ids'] and ep['eog']==ref['eog'] and ep['reason']==ref['reason'];failed=not passed
     rows.append(dict(unit_id=unit['unit_id'],task=unit['task'],round=round,qualified=passed,first_difference=first_difference(ep['ids'],ref['ids']),endpoint_count=len(ep['ids']),raw_count=result['metrics']['raw_count'],reason=ep['reason']))
     r.save(R/'D_QUALIFICATION.json',dict(status='FAIL' if failed else 'PASS' if len(rows)==112 else 'IN_PROGRESS',planned=112,complete=len(rows),rows=rows,all_tasks_exposed=True,no_speed_baseline=True))
     if failed:break
   finally:s.close()
   if failed:break
 except BaseException:r.save(R/'D_WORKER_FAILURE.json',dict(traceback=traceback.format_exc()));raise
 finally:r.release()
 print('D finished',len(rows),'/112','FAIL' if failed else 'PASS',flush=True)
if __name__=='__main__':main()
