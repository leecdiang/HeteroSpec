"""Resume corrected all-output native jobs after immutable predecessor archives."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
from build import read,sha,save
def alive(x):
 try:
  raw=Path(f"/proc/{x['pid']}/stat").read_text();s=raw[raw.rfind(')')+2:].split();return s[19]==x['start_ticks']and s[0]!='Z'
 except FileNotFoundError:return False
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();r,w=a.root,a.work;src=Path(__file__).parent
 while not(w/'PIPELINE_COORDINATOR_CLOSED04.private.json').exists():time.sleep(5)
 old=w/'qualification-04/runs/geometry-W_REF1G_M-0';assert read(old/'HOST.json')['status']=='COMPLETE';meta=read(old/'native/result.json');assert meta['status']=='COMPLETE';verify=[z for z in meta['cases'][1]['executions']if z['phase']=='VERIFY'];assert len(verify)==1 and verify[0]['requested_rows']==[3]and verify[0]['width']==4
 for x in[read(w/'PIPELINE_LAUNCH_04.private.json')['processes']['archive-04'],read(w/'ARCHIVE_PRIVACY_SUCCESSOR_LAUNCH.private.json')]:
  while alive(x):time.sleep(10)
 assert time.time()<1794257040,'No960s worker margin before05:00'
 save(w/'SOURCE07_LAUNCH_BINDING.private.json',dict(epoch=time.time(),sources={p.name:sha(p)for p in src.iterdir()if p.is_file()},predecessor_failure_sha256=sha(w/'qualification-04/FAILURE.json'),native_predecessor_completed=True,scope='Explicit corrected all-output mask, same packed numerical/native ELF; full supported gates; no six-arm performance claim',native_ELF_sha256=read(r/'q32-q4-full-build-04/packed/BUILD.json')['executable_sha256']))
 launched={};children={}
 for name,script,affinity,extra in [('qualification-05','qualification.py','32,33',['--builds',str(r/'q32-q4-full-build-04')]),('finish-05','finish.py','32,33',['--builds',str(r/'q32-q4-full-build-04'),'--operand-builds',str(r/'q32-q4-full-operands-build-04')]),('archive-05','archive.py','34,35',[])]:
  with(w/(name+'.stdout.log')).open('xb')as so,(w/(name+'.stderr.log')).open('xb')as se:child=subprocess.Popen(['taskset','-c',affinity,'nice','-n','10',sys.executable,'-B',str(src/script),'--root',str(r),'--work',str(w),*extra],stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
  raw=Path(f'/proc/{child.pid}/stat').read_text();launched[name]=dict(pid=child.pid,start_ticks=raw[raw.rfind(')')+2:].split()[19],script=script,detached=True);children[name]=child
 save(w/'PIPELINE_LAUNCH_05.private.json',dict(epoch=time.time(),client_required=False,processes=launched,full_six_arm_eligibility=False));print('Q32_ALL_OUTPUT_MASK_CONTINUATION_LAUNCHED',flush=True)
 while True:
  states={n:c.poll()for n,c in children.items()if n!='archive-05'}
  for name,code in states.items():
   if code is None:continue
   phase='qualification-05'if name=='qualification-05'else'closure-05';failure=w/phase/'FAILURE.json';complete=(w/'qualification-05/CORE_GATES_COMPLETE.json').exists()if name=='qualification-05'else((w/'closure-05/QUALIFICATION_COMPLETE.json').exists()or(w/'FINISH_NOT_ADMITTED-05.json').exists())
   if not complete and not failure.exists():save(failure,dict(error='Corrected-mask controller exited without successful terminal gate',controller=name,returncode=code,stderr_sha256=sha(w/(name+'.stderr.log')),epoch=time.time(),no_performance_admission=True,automatic_native_retry=False))
  f=w/'PIPELINE_HEARTBEAT05.private.json';tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(dict(epoch=time.time(),children=states),indent=2)+'\n');os.replace(tmp,f)
  if all(c is not None for c in states.values()):break
  time.sleep(10)
 save(w/'PIPELINE_COORDINATOR_CLOSED05.private.json',dict(epoch=time.time(),children=states,no_more_native_admissions=True,no_six_arm_performance_claim=True))
if __name__=='__main__':main()
