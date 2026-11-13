"""Detached all-six corrected recorder pipeline; fail closed and always export."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
from build import read,sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();r,w=a.root,a.work;src=Path(__file__).parent
 assert read(w/'PIPELINE_COORDINATOR_CLOSED06.private.json')['no_more_native_admissions']
 assert read(w/'diagnostic-02/COMPLETE.json')['passed']
 assert read(r/'q32-q4-full-build-10/COMPLETE.json')['passed']and read(r/'q32-q4-full-operands-build-11/COMPLETE.json')['passed']
 save(w/'SOURCE12_LAUNCH_BINDING.private.json',dict(epoch=time.time(),sources={p.name:sha(p)for p in src.glob('*.py')},build_sha256=sha(r/'q32-q4-full-build-10/COMPLETE.json'),R_sha256=sha(w/'reference/REFERENCE_FREEZE.json'),numerical_archives_changed=False,all_six_must_qualify=True,pre_panel_corrections=['Cache immutable device type per actual device, fresh tensor placement every callback','Fix all remaining direct reserve8 jobs to common reserve32','Exact full same-root warmup before each measurement;96warm+96measured, all charged'],native_requests_interrupted=False))
 children={};launched={}
 for name,script,cpu,extra in [('qualification-07','qualification.py','32,33',['--builds',str(r/'q32-q4-full-build-10')]),('finish-07','finish.py','32,33',['--builds',str(r/'q32-q4-full-build-10'),'--operand-builds',str(r/'q32-q4-full-operands-build-11')]),('archive-07','archive.py','34,35',[])]:
  with(w/(name+'.stdout.log')).open('xb')as so,(w/(name+'.stderr.log')).open('xb')as se:c=subprocess.Popen(['taskset','-c',cpu,'nice','-n','10',sys.executable,'-B',str(src/script),'--root',str(r),'--work',str(w),*extra],stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
  raw=Path(f'/proc/{c.pid}/stat').read_text();launched[name]=dict(pid=c.pid,start_ticks=raw[raw.rfind(')')+2:].split()[19],script=script,detached=True);children[name]=c
 save(w/'PIPELINE_LAUNCH_07.private.json',dict(epoch=time.time(),client_required=False,processes=launched,all_six_arms_required=True));print('Q32_CACHED_DEVICE_ALL_SIX_LAUNCHED',flush=True)
 while True:
  states={n:c.poll()for n,c in children.items()if n!='archive-07'}
  for name,code in states.items():
   if code is None:continue
   phase='qualification-07'if name=='qualification-07'else'closure-07';failure=w/phase/'FAILURE.json';complete=(w/'qualification-07/CORE_GATES_COMPLETE.json').exists()if name=='qualification-07'else((w/'panel-01/COMPLETE.json').exists()or(w/'FINISH_NOT_ADMITTED-07.json').exists())
   if not complete and not failure.exists():save(failure,dict(error='Corrected all-six controller exited without terminal gate',controller=name,returncode=code,stderr_sha256=sha(w/(name+'.stderr.log')),epoch=time.time(),automatic_native_retry=False,no_performance_admission=True))
  f=w/'PIPELINE_HEARTBEAT07.private.json';tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(dict(epoch=time.time(),children=states),indent=2)+'\n');os.replace(tmp,f)
  if all(code is not None for code in states.values()):break
  time.sleep(5)
 save(w/'PIPELINE_COORDINATOR_CLOSED07.private.json',dict(epoch=time.time(),children=states,no_more_native_admissions=True))
if __name__=='__main__':main()
