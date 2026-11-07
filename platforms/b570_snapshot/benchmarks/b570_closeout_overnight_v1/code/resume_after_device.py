"""Resume only platform-rejected or incomplete units; original cutoff retained."""
from pathlib import Path
import json,subprocess,sys,os,traceback
from datetime import datetime,timezone
import runner
from campaign import R,T,N1,stage,eq,read,save
ROOT=Path(__file__).parent
def run(name,*args):
 save(ROOT/'PIPELINE_STATUS.json',dict(utc=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),script=name,args=list(args),state='RUNNING_DEVICE_RECOVERY'))
 with (ROOT/'recovery'/('device-'+name+'.log')).open('a',encoding='utf-8') as log:subprocess.run([sys.executable,str(ROOT/name),*args],stdout=log,stderr=log,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
if __name__=='__main__':
 save(ROOT/'PIPELINE_LOCK.json',dict(pid=os.getpid(),creation_identity=runner.identity(os.getpid()),utc=datetime.now(timezone.utc).isoformat()))
 try:
  old=read(ROOT/'dependencies/B570/HISTORICAL_EXPECTED.json')
  tasks=['HumanEval/58','HumanEval/134','HumanEval/42','HumanEval/145','HumanEval/138']
  source=read(Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/INPUTS.json'))
  inputs=[dict(id=t,prompt_ids=read(source[t]['ids'])) for t in tasks]
  schedule=[dict(config=dict(mode,cap=128,capture=True,repetition=rep),inputs=inputs) for rep in [1,2] for mode in [R,T,N1]]
  save(ROOT/'G0_DEVICE_REQUALIFICATION_SCHEDULE.json',schedule)
  run('runner.py','schedule','G0_DEVICE_REQUALIFICATION',str(ROOT/'G0_DEVICE_REQUALIFICATION_SCHEDULE.json'))
  rows=[r for r in read(ROOT/'G0_DEVICE_REQUALIFICATION_RESULTS.json') if not r['warm']]
  failures=[]
  for row in rows:
   expected=old[row['task']+'/R/1'];expected=dict(expected,reason='EOG' if expected['endpoint']=='EOG' else 'CAP')
   if not eq(row['endpoint'],expected):failures.append(row['unit_id'])
  save(ROOT/'G0_DEVICE_REQUALIFICATION.json',dict(status='PASS' if not failures else 'COMPLETED_SCIENTIFIC_FAIL',requests=len(rows),failed=failures,source_commit=runner.source()))
  assert not failures,'Device recovery old-reference requalification failed'
  run('campaign.py','core')
  run('efficiency.py');run('mechanism.py')
 except BaseException:
  save(ROOT/('DEVICE_RECOVERY_FAILURE.json'),dict(utc=datetime.now(timezone.utc).isoformat(),traceback=traceback.format_exc(),status='PARTIAL_PENDING_PRESERVATION'))
 finally:
  run('independent_verify.py',str(ROOT),'--allow-partial')
  if not (ROOT/'ASSET_POST.json').exists():run('audit_assets.py','ASSET_POST.json')
  run('generate_report.py');run('seal_archive.py');run('publish_evidence.py')
  (ROOT/'PIPELINE_LOCK.json').unlink(missing_ok=True)
