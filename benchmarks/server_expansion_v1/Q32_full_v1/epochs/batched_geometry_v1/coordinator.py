"""Finish current request, then resume all checks with bounded case batching."""
from pathlib import Path
import argparse,json,os,signal,subprocess,sys,time
from build import read,sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();r,w=a.root,a.work;src=Path(__file__).parent
 assert read(r/'q32-q4-full-build-10/COMPLETE.json')['passed']and read(r/'q32-q4-full-operands-build-11/COMPLETE.json')['passed']
 x=read(w/'PIPELINE_LAUNCH_07.private.json')['processes']['archive-07'];proc=Path(f"/proc/{x['pid']}")
 if proc.exists():
  raw=(proc/'stat').read_text();assert raw[raw.rfind(')')+2:].split()[19]==x['start_ticks'];assert b'q32-q4-full-source-12/archive.py'in(proc/'cmdline').read_bytes();assert not(w/'export-09').exists();os.kill(x['pid'],signal.SIGTERM)
 hold=w/'qualification-07/control/PAUSE.json'
 if not hold.exists():save(hold,dict(status='CONTROLLED_HANDOFF_AFTER_CURRENT_WORKER',reason='All original checks continue with same ELF/R; combine at most3 independently reset qualification cases per new worker after observed long-case success; exact completed jobs rechecked, no native signal',epoch=time.time()))
 while not(w/'PIPELINE_COORDINATOR_CLOSED07.private.json').exists():time.sleep(2)
 assert time.time()<1794257040
 save(w/'SOURCE13_LAUNCH_BINDING.private.json',dict(epoch=time.time(),sources={p.name:sha(p)for p in src.glob('*.py')},build_sha256=sha(r/'q32-q4-full-build-10/COMPLETE.json'),R_sha256=sha(w/'reference/REFERENCE_FREEZE.json'),native_ELF_changed=False,all_cases_checks_and_counters_retained=True,native_requests_interrupted=False,formal_panel_changed=False))
 children={};launched={}
 for name,script,cpu,extra in [('qualification-08','qualification.py','32,33',['--builds',str(r/'q32-q4-full-build-10')]),('finish-08','finish.py','32,33',['--builds',str(r/'q32-q4-full-build-10'),'--operand-builds',str(r/'q32-q4-full-operands-build-11')]),('archive-08','archive.py','34,35',[])]:
  with(w/(name+'.stdout.log')).open('xb')as so,(w/(name+'.stderr.log')).open('xb')as se:c=subprocess.Popen(['taskset','-c',cpu,'nice','-n','10',sys.executable,'-B',str(src/script),'--root',str(r),'--work',str(w),*extra],stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
  raw=Path(f'/proc/{c.pid}/stat').read_text();launched[name]=dict(pid=c.pid,start_ticks=raw[raw.rfind(')')+2:].split()[19],script=script,detached=True);children[name]=c
 save(w/'PIPELINE_LAUNCH_08.private.json',dict(epoch=time.time(),client_required=False,processes=launched,all_six_arms_required=True));print('Q32_BOUNDED_QUALIFICATION_BATCHES_LAUNCHED',flush=True)
 while True:
  states={n:c.poll()for n,c in children.items()if n!='archive-08'}
  for name,code in states.items():
   if code is None:continue
   phase='qualification-08'if name=='qualification-08'else'closure-08';failure=w/phase/'FAILURE.json';complete=(w/'qualification-08/CORE_GATES_COMPLETE.json').exists()if name=='qualification-08'else((w/'panel-01/COMPLETE.json').exists()or(w/'FINISH_NOT_ADMITTED-08.json').exists())
   if not complete and not failure.exists():save(failure,dict(error='Bounded qualification controller exited without terminal gate',controller=name,returncode=code,stderr_sha256=sha(w/(name+'.stderr.log')),epoch=time.time(),automatic_native_retry=False,no_performance_admission=True))
  f=w/'PIPELINE_HEARTBEAT08.private.json';tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(dict(epoch=time.time(),children=states),indent=2)+'\n');os.replace(tmp,f)
  if all(code is not None for code in states.values()):break
  time.sleep(5)
 save(w/'PIPELINE_COORDINATOR_CLOSED08.private.json',dict(epoch=time.time(),children=states,no_more_native_admissions=True))
if __name__=='__main__':main()
