"""Finish CPU-only validation, sealing and publication after numerical closure."""
import json,subprocess,sys,os,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).parent
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def save(name,value):(ROOT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
assert not (ROOT/'LOCK.json').exists(),'Inference still active'
assert read('INDEPENDENT_VERIFICATION.json')['status']=='PASS'
assert read('E_DECISION.json')['status']=='NO_GO_PILOT'
assert read('STAGE_COUNTS.json')['core_complete_measured']
freeze=read('CONTINUATION_FREEZE.json')
for name,digest in freeze['current_sources'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
assert hashlib.sha256((ROOT/'efficiency.py').read_bytes()).hexdigest()==freeze['efficiency_source_sha256']
save('FINAL_CPU_CONTINUATION.json',{'utc':datetime.now(timezone.utc).isoformat(),'user_instruction':'继续完成任务，顺便和我讲一下b570平台上的效果怎么样','scope':'CPU-only final audit, restoration and PR delivery after all numerical work completed; original inference cutoff retained','original_experiment_stop_utc':freeze['new_experiment_stop_utc'],'additional_model_requests':0,'earlier_complete_restore':'engineering-cpu-final-review/ARCHIVE_RESTORE.json','final_offline_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()})
(ROOT/'STOP').write_text('Numerical batch complete. CPU validation and delivery only. New inference requires a new authorized batch.\n',encoding='utf-8')
for script in ['generate_work_accounting.py','generate_report.py','seal_archive.py','publish_evidence.py']:
 save('PIPELINE_STATUS.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'script':script,'state':'FINAL_CPU_ONLY_NO_NEW_INFERENCE'})
 with (ROOT/'recovery'/('final-'+script+'.log')).open('a',encoding='utf-8') as log:
  subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,stdout=log,stderr=log,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
save('PIPELINE_STATUS.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'state':'COMPLETE_FINITE_SCOPE','model_forwards_in_delivery':0})
(ROOT/'PIPELINE_LOCK.json').unlink(missing_ok=True)
print('CPU-only final delivery complete',flush=True)
