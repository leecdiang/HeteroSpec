"""Eight prepaid bridge diagnoses plus balanced new-input four-mode confirmation."""
from pathlib import Path
import json,uuid,traceback,hashlib
import formal_runner as r
R=Path(__file__).parent
def main():
 assert r.read(R/'D_VERIFICATION.json')['scientific_gate']=='PASS'
 freeze=r.read(R/'E_FREEZE.json')
 for n,h in freeze['files'].items():assert r.sha(R/n)==h
 manifest=r.read(R/'E_MANIFEST.json');dev={p['id']:p for p in r.read(R/'DEV_INPUTS.json')};refs=r.read(R/'HISTORICAL_PARENTS.json');new={p['id']:p for p in r.read(R/'E_INPUTS.json')};results=[];bridge=[]
 r.acquire();r.STAGE='E'
 try:
  for group in manifest['bridge_sessions']:
   s=r.Session('E-bridge-'+str(group['config']['round'])+'-'+uuid.uuid4().hex[:6],group['config'])
   try:
    s.request('E/BRIDGE/WARM/'+s.name,dev['HumanEval/134'],True)
    for u in group['units']:
     inp=dict(dev[u['task']]);inp.pop('checkpoint_window',None);result=s.request(u['unit_id'],inp);reference=refs[u['task']+'/R_reference']['endpoint'];ep=result['endpoint'];passed=all(ep[k]==reference[k] for k in ['ids','eog','reason'])
     bridge.append(dict(unit_id=u['unit_id'],task=u['task'],round=group['config']['round'],qualified=passed))
     r.save(R/'E_BRIDGE_QUALIFICATION.json',dict(status='FAIL' if not passed else 'PASS' if len(bridge)==8 else 'IN_PROGRESS',planned=8,complete=len(bridge),rows=bridge))
     if not passed:r.save(R/'E_RUN_GATE.json',dict(status='BLOCKED_MATCHED_TARGET_BRIDGE',new_input_requests=0));return
   finally:s.close()
  # Bridge stability must be independently validated before any new paid reference.
  import subprocess,sys
  subprocess.run([sys.executable,str(R/'validate_E_bridge.py'),str(R)],check=True)
  assert r.read(R/'E_BRIDGE_VERIFICATION.json')['scientific_gate']=='PASS'
  for group in manifest['formal_sessions']:
   s=r.Session('E-'+str(group['config']['round'])+'-'+group['config']['label']+'-'+uuid.uuid4().hex[:6],group['config'])
   try:
    s.request('E/FORMAL/WARM/'+s.name,dev['HumanEval/134'],True)
    for u in group['units']:
     result=s.request(u['unit_id'],new[u['task']]);results.append(dict(unit_id=u['unit_id'],task=u['task'],label=group['config']['label'],round=group['config']['round']))
     r.save(R/'E_RUN_PROGRESS.json',dict(planned=len(new)*8,complete=len(results),rows=results,qualified_speed_decision='independent CPU rederive after fixed matrix',no_candidate_changes=True))
   finally:s.close()
  r.save(R/'E_RUN_GATE.json',dict(status='COMPLETE_PREDEFINED_MATRIX',formal_complete=len(results),bridge_complete=len(bridge)))
 except BaseException:r.save(R/'E_WORKER_FAILURE.json',dict(traceback=traceback.format_exc()));raise
 finally:r.release()
 print('E finished fixed four-mode two-round matrix',len(results),flush=True)
if __name__=='__main__':main()
