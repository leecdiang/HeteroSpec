"""Continuous handoff only after a native worker returns; all-six requalification."""
from pathlib import Path
import argparse,json,os,signal,subprocess,sys,time
from build import read,sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();r,w=a.root,a.work;src=Path(__file__).parent
 assert read(r/'q32-q4-full-build-09/COMPLETE.json')['passed']and read(r/'q32-q4-full-operands-build-10/COMPLETE.json')['passed']
 # Retire just the idle data-only archive waiter before the handoff, so it
 # cannot take a terminal snapshot while the successor appends to the ledger.
 x=read(w/'FINAL_ARCHIVE_LAUNCH.private.json');proc=Path(f"/proc/{x['pid']}")
 if proc.exists():
  raw=(proc/'stat').read_text();assert raw[raw.rfind(')')+2:].split()[19]==x['start_ticks'];assert b'q32-q4-full-source-08/archive.py'in(proc/'cmdline').read_bytes();assert not(w/'export-07').exists();os.kill(x['pid'],signal.SIGTERM)
 save(w/'RECORDING_HANDOFF.private.json',dict(epoch=time.time(),reason='Full all-six source-identical numerical requalification with binary operator recording and same complete faster native SHA. User asked to distinguish/fix software failure before excluding loop.',numerical_archives_changed=False,native_requests_interrupted=False,old_partial_results_retained=True,remaining_cutoff_UTC='2026-11-09T21:00:00Z',archive_waiter_retired=x['pid']))
 hold=w/'qualification-05/control/PAUSE.json'
 if not hold.exists():save(hold,dict(status='CONTROLLED_HANDOFF_AFTER_CURRENT_WORKER',reason='Finish active native worker and its comparisons; successor automatically resumes all six arms. No active native signal.',epoch=time.time()))
 while not(w/'PIPELINE_COORDINATOR_CLOSED05.private.json').exists():time.sleep(2)
 assert time.time()<1794257040,'Preserve960s before05:00'
 save(w/'SOURCE10_LAUNCH_BINDING.private.json',dict(epoch=time.time(),sources={p.name:sha(p)for p in src.iterdir()if p.is_file()},compiled_frontend_build_sha256=sha(r/'q32-q4-full-build-09/COMPLETE.json'),unchanged_R_sha256=sha(w/'reference/REFERENCE_FREEZE.json'),scope='All six arms must qualify; no automatic loop exclusion; full binary descriptor reconstruction, full vector/KV and physical gates retained'))
 launched={};children={}
 for name,script,affinity,extra in [('qualification-06','qualification.py','32,33',['--builds',str(r/'q32-q4-full-build-09')]),('finish-06','finish.py','32,33',['--builds',str(r/'q32-q4-full-build-09'),'--operand-builds',str(r/'q32-q4-full-operands-build-10')]),('archive-06','archive.py','34,35',[])]:
  with(w/(name+'.stdout.log')).open('xb')as so,(w/(name+'.stderr.log')).open('xb')as se:child=subprocess.Popen(['taskset','-c',affinity,'nice','-n','10',sys.executable,'-B',str(src/script),'--root',str(r),'--work',str(w),*extra],stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
  raw=Path(f'/proc/{child.pid}/stat').read_text();launched[name]=dict(pid=child.pid,start_ticks=raw[raw.rfind(')')+2:].split()[19],script=script,detached=True);children[name]=child
 save(w/'PIPELINE_LAUNCH_06.private.json',dict(epoch=time.time(),client_required=False,processes=launched,all_six_arms_required=True));print('Q32_RECORDING_SUCCESSOR_ALL_SIX_LAUNCHED',flush=True)
 while True:
  states={n:c.poll()for n,c in children.items()if n!='archive-06'}
  for name,code in states.items():
   if code is None:continue
   phase='qualification-06'if name=='qualification-06'else'closure-06';failure=w/phase/'FAILURE.json';complete=(w/'qualification-06/CORE_GATES_COMPLETE.json').exists()if name=='qualification-06'else((w/'panel-01/COMPLETE.json').exists()or(w/'FINISH_NOT_ADMITTED-06.json').exists())
   if not complete and not failure.exists():save(failure,dict(error='All-six recording-successor controller exited without a successful terminal gate',controller=name,returncode=code,stderr_sha256=sha(w/(name+'.stderr.log')),epoch=time.time(),automatic_native_retry=False,no_performance_admission=True))
  f=w/'PIPELINE_HEARTBEAT06.private.json';tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(dict(epoch=time.time(),children=states),indent=2)+'\n');os.replace(tmp,f)
  if all(code is not None for code in states.values()):break
  time.sleep(5)
 save(w/'PIPELINE_COORDINATOR_CLOSED06.private.json',dict(epoch=time.time(),children=states,no_more_native_admissions=True))
if __name__=='__main__':main()
