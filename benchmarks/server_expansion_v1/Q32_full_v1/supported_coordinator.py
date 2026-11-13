"""After a timed-out loop gate, continue real packed-model gates, no performance."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
from build import read,sha,save
def alive(x):
 try:
  raw=Path(f"/proc/{x['pid']}/stat").read_text();s=raw[raw.rfind(')')+2:].split();return s[19]==x['start_ticks']and s[0]!='Z'
 except FileNotFoundError:return False
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();r,w=a.root,a.work;src=Path(__file__).parent
 while not(w/'PIPELINE_COORDINATOR_CLOSED03.private.json').exists():time.sleep(5)
 failure=w/'qualification-03/FAILURE.json'
 if not failure.exists()or read(failure).get('error')!='Owned worker timeout':
  save(w/'SUPPORTED_CONTINUATION_NOT_NEEDED.json',dict(reason='No preceding long-loop worker timeout; retain the original complete pipeline or its actual blocking reason',no_native_work=True));return
 # Finish the old terminal archive first. Never race its raw ledger snapshot.
 old=read(w/'PIPELINE_LAUNCH_03.private.json')['processes']['archive-03']
 while alive(old):time.sleep(10)
 assert time.time()<1794257040,'No960s worker margin before05:00'
 save(w/'SOURCE05_LAUNCH_BINDING.private.json',dict(epoch=time.time(),sources={p.name:sha(p)for p in src.iterdir()if p.is_file()},preceding_loop_failure_sha256=sha(failure),compiled_build_epoch='Unmodified source04 reserve32, CUDA graphs disabled, REF1-group; no numerical/frontend relink',scope='Complete supported W_REF1G_M,L_REF1G_M,L_REF1G_D4 gates only; no six-arm eligibility/performance claim',prior_archive_completed=(w/'export-03/EXPORT_COMPLETE.json').exists()))
 launched={};children={}
 for name,script,affinity,extra in [('qualification-04','qualification.py','32,33',['--builds',str(r/'q32-q4-full-build-04')]),('finish-04','finish.py','32,33',['--builds',str(r/'q32-q4-full-build-04'),'--operand-builds',str(r/'q32-q4-full-operands-build-04')]),('archive-04','archive.py','34,35',[])]:
  with(w/(name+'.stdout.log')).open('xb')as so,(w/(name+'.stderr.log')).open('xb')as se:child=subprocess.Popen(['taskset','-c',affinity,'nice','-n','10',sys.executable,'-B',str(src/script),'--root',str(r),'--work',str(w),*extra],stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
  raw=Path(f'/proc/{child.pid}/stat').read_text();launched[name]=dict(pid=child.pid,start_ticks=raw[raw.rfind(')')+2:].split()[19],script=script,detached=True);children[name]=child
 save(w/'PIPELINE_LAUNCH_04.private.json',dict(epoch=time.time(),client_required=False,processes=launched,full_six_arm_eligibility=False));print('Q32_SUPPORTED_NATIVE_CONTINUATION_LAUNCHED',flush=True)
 while True:
  states={n:c.poll()for n,c in children.items()if n!='archive-04'}
  for name,code in states.items():
   if code is None:continue
   phase='qualification-04'if name=='qualification-04'else'closure-04';failure=w/phase/'FAILURE.json';complete=(w/'qualification-04/CORE_GATES_COMPLETE.json').exists()if name=='qualification-04'else((w/'closure-04/QUALIFICATION_COMPLETE.json').exists()or(w/'FINISH_NOT_ADMITTED-04.json').exists())
   if not complete and not failure.exists():save(failure,dict(error='Supported-path controller exited without successful terminal gate',controller=name,returncode=code,stderr_sha256=sha(w/(name+'.stderr.log')),epoch=time.time(),no_performance_admission=True,automatic_native_retry=False))
  f=w/'PIPELINE_HEARTBEAT04.private.json';tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(dict(epoch=time.time(),children=states),indent=2)+'\n');os.replace(tmp,f)
  if all(c is not None for c in states.values()):break
  time.sleep(10)
 save(w/'PIPELINE_COORDINATOR_CLOSED04.private.json',dict(epoch=time.time(),children=states,no_more_native_admissions=True,no_six_arm_performance_claim=True))
if __name__=='__main__':main()
