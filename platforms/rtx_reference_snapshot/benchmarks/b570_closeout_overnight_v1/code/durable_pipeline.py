"""Detached orchestration; each inference stage has one PID+creation lock."""
from pathlib import Path
import json,os,sys,subprocess,time,traceback,ctypes
from datetime import datetime,timezone
ROOT=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(name,data):
 p=ROOT/name;q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\n');os.replace(q,p)
def stamp():return datetime.now(timezone.utc).isoformat()
def run(script,*args):
 save('PIPELINE_STATUS.json',{'utc':stamp(),'pid':os.getpid(),'script':script,'args':list(args),'state':'RUNNING'})
 with (ROOT/'recovery'/(script.replace('.py','')+'.pipeline.stdout.log')).open('a',encoding='utf-8') as out,(ROOT/'recovery'/(script.replace('.py','')+'.pipeline.stderr.log')).open('a',encoding='utf-8') as err:
  subprocess.run([sys.executable,str(ROOT/script),*args],stdout=out,stderr=err,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
def wait_external_g0():
 import runner
 lock=ROOT/'LOCK.json'
 if lock.exists():
  owner=read(lock)
  while runner.identity(owner['pid'])==owner['creation_identity']:
   save('PIPELINE_STATUS.json',{'utc':stamp(),'pid':os.getpid(),'state':'WAIT_EXISTING_G0','owned_controller':owner})
   if runner.stopped():raise RuntimeError('Experiment cutoff while waiting G0')
   time.sleep(5)
 if not (ROOT/'G0.json').exists():raise RuntimeError('G0 controller ended without qualification receipt; preserve failure, no blind retry')
 assert read(ROOT/'G0.json')['status']=='PASS','Original reference gate failed'
if __name__=='__main__':
 import runner
 lock=ROOT/'PIPELINE_LOCK.json'
 if lock.exists():
  previous=read(lock)
  if runner.identity(previous['pid'])==previous['creation_identity']:raise RuntimeError('Another live pipeline owns this study')
  lock.rename(ROOT/('PIPELINE_LOCK.stale-'+str(time.time_ns())+'.json'))
 save('PIPELINE_LOCK.json',dict(pid=os.getpid(),creation_identity=runner.identity(os.getpid()),utc=stamp()))
 ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
 try:
  wait_external_g0()
  run('prepare_final_control.py')
  run('qualify_rebuilt_bridge.py')
  run('qualify_sham.py');assert read(ROOT/'G0_SHAM.json')['status']=='PASS','New-wrapper sham failed'
  run('qualify_width.py')
  run('budget_probe.py')
  run('campaign.py','freeze')
  run('campaign.py','core')
  run('efficiency.py')
  run('mechanism.py')
  run('independent_verify.py')
  run('audit_assets.py','ASSET_POST.json')
  run('generate_report.py')
  run('seal_archive.py')
  run('publish_evidence.py')
  save('PIPELINE_DONE.json',{'utc':stamp(),'state':'ARCHIVED_RESTORED_AND_REMOTE_READBACK_VERIFIED'})
 except BaseException:
  save('PIPELINE_FAILURE-'+str(time.time_ns())+'.json',{'utc':stamp(),'traceback':traceback.format_exc(),'state':'PARTIAL_PENDING_PRESERVATION'})
  # Time/infrastructure omissions are sealed as PARTIAL; never labelled COMPLETE.
  try:
   run('independent_verify.py',str(ROOT),'--allow-partial')
   if not (ROOT/'ASSET_POST.json').exists():run('audit_assets.py','ASSET_POST.json')
   run('generate_report.py')
   run('seal_archive.py')
   run('publish_evidence.py')
  except BaseException:save('PARTIAL_PRESERVATION_FAILURE-'+str(time.time_ns())+'.json',{'utc':stamp(),'traceback':traceback.format_exc()})
  raise
 finally:
  ctypes.windll.kernel32.SetThreadExecutionState(0x80000000);lock.unlink(missing_ok=True)
