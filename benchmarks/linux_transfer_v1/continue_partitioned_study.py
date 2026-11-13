"""One explicit qualification epoch after the retained heavy-matrix timeout.

This is not a retry loop. It cannot run after any confirmation reservation or a
numerical mismatch. Original attempt/status/budget remain intact. The complete
prospectively fixed panel is used unchanged only after all new checks pass.
"""
from pathlib import Path
import argparse, datetime, json, subprocess, sys
from common import need, read, save, sha
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--repo',type=Path,required=True);a=p.parse_args()
 w=a.work.resolve();repo=a.repo.resolve();phase='CHECK_RETAINED_TIMEOUT';complete=False
 previous=read(w/'PIPELINE_STATUS.json')
 need(previous['status']=='FAILED_RETAINED' and previous['last_phase']=='FINITE_NATIVE_QUALIFICATION','Original qualification must have closed first')
 need('Owned worker timeout' in (w/'qualification-phase-01.log').read_text(),'This explicit continuation repairs only the observed heavy-matrix timeout')
 old=w/'qualification-01/runs/Qwen-matrix-W_L4_M';host=read(old/'HOST.json')
 need(host['status']=='FAILED' and host['worker_wall_s']>=900,'Different retained failure')
 ledger=[json.loads(x) for x in (w/'ledger.jsonl').read_text().splitlines()]
 need(not any(x.get('phase')=='confirmation' for x in ledger),'Never continue a partially observed formal panel')
 status=w/'panel-01/ALL_SLOT_STATUS.json';need(all(v=='NOT_RUN_UNQUALIFIED' for v in read(status)['slots'].values()),'Existing formal slots must be entirely unopened')
 plan=w/'panel-01/PLAN.json';plan_sha=sha(plan);jobs={x['job']:sha(w/'panel-01'/x['job']) for x in read(plan)['workers']}
 save(w/'CONTINUATION-02.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':sha(Path(__file__)),
  'old_pipeline_status_sha256':sha(w/'PIPELINE_STATUS.json'),'old_failure_log_sha256':sha(w/'qualification-phase-01.log'),'old_failed_HOST_sha256':sha(old/'HOST.json'),
  'reference_freeze_sha256':sha(w/'reference-01/REFERENCE_FREEZE.json'),'old_ledger_sha256':sha(w/'ledger.jsonl'),
  'change':'All fixed geometry cases grouped3 per candidate worker, uniformly for both model families; same900s ceiling, numerical binaries, R and exact comparison rules',
  'candidate_geometry_reused_from_failed_worker':False,'complete_fixed_panel_plan_sha256':plan_sha,'confirmation_reservations_before_change':0})
 def launch(script,args,label):
  with (w/(label+'.log')).open('xb') as f:r=subprocess.run([sys.executable,str(HERE/script),*map(str,args)],stdout=f,stderr=subprocess.STDOUT)
  need(r.returncode==0,'Retained continuation failure: '+label)
 try:
  phase='PARTITIONED_NATIVE_QUALIFICATION'
  launch('qualify_partitioned.py',['--work',w,'--repo',repo,'--epoch','qualification-02','--reuse-reference-matrices',w/'qualification-01'],'qualification-phase-02')
  need(sha(plan)==plan_sha and all(sha(w/'panel-01'/name)==h for name,h in jobs.items()),'Fixed formal plan changed')
  need(not any(json.loads(x).get('phase')=='confirmation' for x in (w/'ledger.jsonl').read_text().splitlines()),'Formal work appeared during qualification')
  # Retain the old unopened-slot record rather than overwrite its bytes. This
  # opens no new population and changes no fixed request or arm identity.
  status.rename(status.with_name('ALL_SLOT_STATUS-qualification-01.json'))
  phase='FIXED_SIX_ARM_CONFIRMATION'
  launch('panel_native.py',['run','--work',w,'--repo',repo,'--qualification',w/'qualification-02'],'confirmation-phase-02')
  phase='COMPLETE';complete=True
 finally:
  save(w/'PIPELINE_STATUS-02.json',{'status':'COMPLETE' if complete else 'FAILED_RETAINED','last_phase':phase,
       'original_pipeline_status_preserved':True,'no_automatic_model_job_retries':True,'no_formal_panel_retries':True})
  if not status.exists():save(status,{'slots':{x['id']:'NOT_RUN_UNQUALIFIED' for x in read(plan)['workers']},'inference_open':False,'failed_phase':phase,'no_selective_retries':True})

if __name__=='__main__':main()
