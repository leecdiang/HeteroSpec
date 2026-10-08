from pathlib import Path
import json,uuid,traceback
import candidate_runner as r
R=Path(__file__).parent
def diff(a,b):
 for i,(x,y) in enumerate(zip(a,b)):
  if x!=y:return i
 return None if len(a)==len(b) else min(len(a),len(b))
def main():
 freeze=r.read(R/'C_FREEZE.json')
 for f,h in freeze['sources'].items():assert r.sha(R/f)==h
 for f,h in freeze['binaries'].items():assert r.sha(R/f)==h
 r.acquire();r.STAGE='C';results=[];failed=False
 try:
  inputs={i['id']:i for i in r.read(R/'DEV_INPUTS.json')};hist=r.read(R/'HISTORICAL_PARENTS.json');manifest=r.read(R/'C_MANIFEST.json')
  for round in [1,2]:
   group=[u for u in manifest['units'] if u['config']['round']==round]
   s=r.Session('C-'+str(round)+'-'+uuid.uuid4().hex[:6],group[0]['config'])
   try:
    s.request('C/'+str(round)+'/WARM/'+s.name,inputs['HumanEval/134'],True)
    for unit in group:
     inp=dict(inputs[unit['task']]);inp.pop('checkpoint_window',None)
     result=s.request(unit['unit_id'],inp);ref=hist[unit['task']+'/R_reference']['endpoint'];ep=result['endpoint']
     passed=ep['ids']==ref['ids'] and ep['eog']==ref['eog'] and ep['reason']==ref['reason']
     row=dict(unit_id=unit['unit_id'],task=unit['task'],round=round,qualified=passed,first_difference=diff(ep['ids'],ref['ids']),reference_endpoint=ref,candidate_endpoint=ep,result_unit=result['unit_id']);results.append(row)
     r.save(R/'C_QUALIFICATION.json',dict(status='PASS' if len(results)==12 and all(x['qualified'] for x in results) else 'FAIL' if not passed else 'IN_PROGRESS',rows=results,planned=12,complete=len(results),one_family=True,scientific_reruns=0))
     if not passed:failed=True;break
   finally:s.close()
   if failed:break
 except BaseException:
  r.save(R/'C_WORKER_FAILURE.json',dict(traceback=traceback.format_exc()));raise
 finally:r.release()
 print('C finished',len(results),'/',12,'FAIL' if failed else 'PASS',flush=True)
if __name__=='__main__':main()
