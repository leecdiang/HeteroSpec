"""Owned coordinator: exact models -> R freeze -> native checks -> fixed panel.

No automatic retry of model jobs. Every run uses host.py's single-UUID admission,
shared cost ledger and own-process-group cleanup. Transfer retries are separate.
"""
from pathlib import Path
import argparse, datetime, json, subprocess, sys, time
from common import need, read, save, sha
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--repo',type=Path,required=True);p.add_argument('--resume-input-wait',action='store_true');a=p.parse_args()
 w=a.work.resolve();repo=a.repo.resolve();marker=w/'PIPELINE_START.json'
 if marker.exists():
  need(a.resume_input_wait,'Use explicit new epochs after diagnosing retained failures')
  previous=[json.loads(x) for x in (w/'pipeline-events.jsonl').read_text().splitlines()]
  need(previous[-1]['phase']=='WAIT_EXACT_INPUTS' and not (w/'EXACT_MODEL_BINDINGS.json').exists(),'Resume only an input wait, never an implicit model-job retry')
  save(w/'PIPELINE_INPUT_WAIT_RESUME.json',{'original_start_sha256':sha(marker),'new_coordinator_sha256':sha(Path(__file__)),'model_jobs_retried':0})
 else:save(marker,{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'coordinator_sha256':sha(Path(__file__)),'no_automatic_model_job_retries':True})
 events=w/'pipeline-events.jsonl';phase='WAIT_EXACT_INPUTS';code=None
 def event(name,**fields):
  row={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':name,**fields}
  with events.open('a') as f:f.write(json.dumps(row)+'\n');f.flush()
  print(json.dumps(row),flush=True)
 def launch(script,args,label):
  with (w/(label+'.log')).open('xb') as f:
   r=subprocess.run([sys.executable,str(HERE/script),*map(str,args)],stdout=f,stderr=subprocess.STDOUT)
  need(r.returncode==0,'Retained phase failure: '+label);return r.returncode
 try:
  models=read(w/'inputs-01/MODELS.json');source=w.parent/'models-ms-01';event(phase)
  keys=[('Qwen','target'),('Qwen','draft'),('Smol','target'),('Smol','draft')]
  while True:
   ready=[]
   for family,role in keys:
    receipt=source/(family+'-'+role+'-VERIFIED.json');file=source/Path(models[family][role+'_model']).name
    if receipt.exists() and file.exists():
     r=read(receipt);need(r['verified'] and r['sha256']==models[family][role+'_sha256'] and r['bytes']==file.stat().st_size,'Acquisition identity mismatch');ready.append((family,role,file,receipt))
   if len(ready)==4:break
   time.sleep(15)
  destination=w.parent/'models-final';destination.mkdir(mode=0o700,exist_ok=True)
  bound=[]
  for family,role,file,receipt in ready:
   need(sha(file)==models[family][role+'_sha256'],'Actual full model bytes changed')
   path=destination/file.name
   if path.exists():need(path.resolve()==file.resolve(),'Previously bound exact model points elsewhere')
   else:path.symlink_to(file)
   bound.append({'family':family,'role':role,'file':file.name,'sha256':sha(file),'acquisition_receipt_sha256':sha(receipt)})
  save(w/'EXACT_MODEL_BINDINGS.json',{'models':bound,'no_requantization':True})
  phase='PREDECLARE_FIXED_PANEL';event(phase)
  launch('panel_native.py',['prepare','--work',w,'--repo',repo],'prepare-panel-01')
  phase='REFERENCE_REPEAT_AND_FREEZE';event(phase)
  launch('run_reference.py',['--work',w,'--config',w/'config-01.json','--build',w/'build-R-01/BUILD.json'],'reference-phase-01')
  phase='WAIT_SOURCE_BUILDS';event(phase)
  while not all((w/f'build-{role}-01/BUILD.json').is_file() for role in ('loop4','packed')):time.sleep(10)
  phase='FINITE_NATIVE_QUALIFICATION';event(phase)
  launch('qualify_native.py',['--work',w,'--repo',repo,'--epoch','qualification-01'],'qualification-phase-01')
  phase='FIXED_SIX_ARM_CONFIRMATION';event(phase)
  launch('panel_native.py',['run','--work',w,'--repo',repo,'--qualification',w/'qualification-01'],'confirmation-phase-01')
  phase='COMPLETE';code=0;event(phase,results_sha256=sha(w/'panel-01/RESULTS.json'))
 finally:
  if code!=0:
   event('FAILED_RETAINED',failed_phase=phase)
   plan=w/'panel-01/PLAN.json';status=w/'panel-01/ALL_SLOT_STATUS.json'
   if plan.exists() and not status.exists():save(status,{'slots':{x['id']:'NOT_RUN_UNQUALIFIED' for x in read(plan)['workers']},'inference_open':False,'failed_phase':phase,'no_selective_retries':True})
  save(w/'PIPELINE_STATUS.json',{'status':'COMPLETE' if code==0 else 'FAILED_RETAINED','last_phase':phase,'no_automatic_merge':True,'no_manuscript_changes':True})

if __name__=='__main__':main()
