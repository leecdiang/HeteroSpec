"""Client-independent sequencing, wait for old worker; never signal foreign work."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
from build import read,sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();r,w=a.root,a.work;src=Path(__file__).parent
 while not(w/'qualification-02/control/GUARD_STOPPED.private.json').exists():
  assert time.time()<1794258000,'No admission after05:00 BJT';time.sleep(5)
 assert read(r/'q32-q4-full-build-04/FRONTENDS_COMPLETE.json')['passed'];assert read(r/'q32-q4-full-operands-build-04/COMPLETE.json')['passed']
 save(w/'SOURCE04_LAUNCH_BINDING.private.json',dict(epoch=time.time(),sources={p.name:sha(p)for p in sorted(src.iterdir())if p.is_file()},own_R_freeze_sha256=sha(w/'reference/REFERENCE_FREEZE.json'),old_qualification_failure=read(w/'qualification-01/FAILURE.json')if(w/'qualification-01/FAILURE.json').exists()else None,archive_scope='All source/build epochs and all native failures retained',common_candidate_output_reserve=32,candidate_cuda_graphs=False))
 launched={};children={}
 for name,script,affinity,extra in [('qualification-03','qualification.py','32,33',['--builds',str(r/'q32-q4-full-build-04')]),('finish-03','finish.py','32,33',['--builds',str(r/'q32-q4-full-build-04'),'--operand-builds',str(r/'q32-q4-full-operands-build-04')]),('archive-03','archive.py','34,35',[])]:
  with(w/(name+'.stdout.log')).open('xb')as so,(w/(name+'.stderr.log')).open('xb')as se:
   child=subprocess.Popen(['taskset','-c',affinity,'nice','-n','10',sys.executable,'-B',str(src/script),'--root',str(r),'--work',str(w),*extra],stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
  raw=Path(f'/proc/{child.pid}/stat').read_text();ticks=raw[raw.rfind(')')+2:].split()[19];launched[name]=dict(pid=child.pid,start_ticks=ticks,detached=True,script=script)
  children[name]=child
 save(w/'PIPELINE_LAUNCH_03.private.json',dict(epoch=time.time(),client_required=False,processes=launched,source_binding_sha256=sha(w/'SOURCE04_LAUNCH_BINDING.private.json')));print('Q32_DETACHED_CONTINUATION_LAUNCHED',json.dumps(launched),flush=True)
 while True:
  states={n:p.poll()for n,p in children.items()if n!='archive-03'}
  for name,code in states.items():
   if code is None:continue
   phase='qualification-03'if name=='qualification-03'else'closure-03';failure=w/phase/'FAILURE.json'
   complete=(w/'qualification-03/CORE_GATES_COMPLETE.json').exists()if name=='qualification-03'else((w/'panel-01/COMPLETE.json').exists()or(w/'FINISH_NOT_ADMITTED-03.json').exists())
   if not complete and not failure.exists():
    save(failure,dict(error='Detached controller exited without a successful terminal gate',controller=name,returncode=code,stderr_sha256=sha(w/(name+'.stderr.log')),epoch=time.time(),automatic_native_retry=False,timing_admitted=False))
  ledger=[json.loads(x)for x in(w/'ledger.jsonl').read_text().splitlines()];reserved=[x for x in ledger if x['event']=='RESERVE'];inherited=read(w/'INHERITED_ACCOUNTING.json')
  heartbeat=dict(epoch=time.time(),children=states,cumulative_requests=inherited['requests']+sum(x['requests']for x in reserved),cumulative_reserved_rows=inherited['rows']+sum(x['rows']for x in reserved),last_native_outputs=[str(p.parent.relative_to(w))for p in sorted(w.glob('qualification-03/runs/*/HOST.json'),key=lambda p:p.stat().st_mtime)[-3:]])
  f=w/'PIPELINE_HEARTBEAT03.private.json';tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(heartbeat,indent=2)+'\n');os.replace(tmp,f)
  if all(code is not None for code in states.values()):break
  time.sleep(10)
 save(w/'PIPELINE_COORDINATOR_CLOSED03.private.json',dict(epoch=time.time(),children=states,no_more_native_admissions=True,archive_PID=launched['archive-03']['pid']))
if __name__=='__main__':main()
