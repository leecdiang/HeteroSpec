from pathlib import Path
import argparse,json,time,sys,types,fcntl,subprocess,traceback,hashlib
import finish as f
from build import read,save,sha
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--builds',type=Path,required=True);p.add_argument('--operand-builds',type=Path,required=True);a=p.parse_args();w=a.work;f.a=a;guard=None;s=None
 try:
  while not(w/'PIPELINE_COORDINATOR_CLOSED09.private.json').exists():time.sleep(3)
  if(w/'panel-01').exists():
   assert(w/'panel-01/COMPLETE.json').exists();save(w/'PANEL_CONTINUATION18_TERMINAL.json',dict(passed=True,scope='Original complete panel reused; no new native requests'));return
  assert read(w/'closure-09/QUALIFICATION_COMPLETE.json')['passed']
  fail=read(w/'closure-09/FAILURE.json');assert fail['error']=='Insufficient whole-panel conservative runtime',fail['error']
  assert read(w/'closure-09/control/GUARD_STOPPED.private.json')['status']=='CLOSED'
  while not(w/'PANEL_COST_CORRECTION_PUBLIC_BINDING.json').exists():
   assert f.now()<f.ADMIT;time.sleep(3)
  original=(Path(__file__).parent/'qualification.py').read_text();adapted=original.replace("self.w/'qualification-08'","self.w/'panel-continuation-10'",1);q=types.ModuleType('_qualified_q32_panel18');q.__file__=str(Path(__file__).parent/'qualification.py');exec(compile(adapted,q.__file__,'exec'),q.__dict__);s=q.Study(a);s.guard.mkdir();save(s.guard/'config.private.json',read(w/'config.private.json'))
  with(s.guard/'stdout.log').open('xb')as so,(s.guard/'stderr.log').open('xb')as se:guard=subprocess.Popen(['taskset','-c','36',sys.executable,'-B',str(Path(__file__).parent/'resource_guard.py'),'--work',str(s.guard)],stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
  for _ in range(30):
   if(s.guard/'RESOURCE_GUARD_LATEST.private.json').exists():break
   assert guard.poll()is None;time.sleep(.5)
  s.out=w/'closure-09'
  registered=read(s.out/'PRIMERS_REGISTERED.json')['inputs'];eps={x['name']:s.native.endpoint(read(s.out/'runs/primer-independent-R/native'/x['name']/'receipt.json'))for x in registered}
  with(a.root/'STUDY_SCHEDULING.lock').open('a+')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);f.panel(s,q,registered,eps)
  save(w/'PANEL_CONTINUATION18_SUCCESS.json',dict(passed=True,qualifications_reused_with_same_binary=True,no_qualification_weakened=True))
 except BaseException as e:
  save(w/'PANEL_CONTINUATION18_FAILURE.json',dict(error=str(e),traceback=traceback.format_exc(),native_auto_retry=False))
 finally:
  if guard is not None:
   (s.guard/'GUARD_DONE').touch(exist_ok=False)
   try:guard.wait(timeout=20)
   except subprocess.TimeoutExpired:pass
  save(w/'PANEL_CONTINUATION18_TERMINAL.json',dict(passed=(w/'panel-01/COMPLETE.json').exists(),epoch=time.time(),native_more_admissions=False))
if __name__=='__main__':main()
