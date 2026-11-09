"""Client-independent sequencing, wait for old worker; never signal foreign work."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
from build import read,sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();r,w=a.root,a.work;src=Path(__file__).parent
 while not(w/'qualification-01/control/GUARD_STOPPED.private.json').exists():
  assert time.time()<1794258000,'No admission after05:00 BJT';time.sleep(5)
 assert read(r/'q32-q4-full-build-03/FRONTENDS_COMPLETE.json')['passed'];assert read(r/'q32-q4-full-operands-build-03/COMPLETE.json')['passed']
 save(w/'SOURCE03_LAUNCH_BINDING.private.json',dict(epoch=time.time(),sources={p.name:sha(p)for p in sorted(src.iterdir())if p.is_file()},own_R_freeze_sha256=sha(w/'reference/REFERENCE_FREEZE.json'),old_qualification_failure=read(w/'qualification-01/FAILURE.json')if(w/'qualification-01/FAILURE.json').exists()else None,archive_scope='All source/build epochs and all native failures retained',common_candidate_output_reserve=32))
 launched={}
 for name,script,affinity,extra in [('qualification-02','qualification.py','32,33',['--builds',str(r/'q32-q4-full-build-03')]),('finish-02','finish.py','32,33',['--builds',str(r/'q32-q4-full-build-03'),'--operand-builds',str(r/'q32-q4-full-operands-build-03')]),('archive-02','archive.py','34,35',[])]:
  with(w/(name+'.stdout.log')).open('xb')as so,(w/(name+'.stderr.log')).open('xb')as se:
   child=subprocess.Popen(['taskset','-c',affinity,'nice','-n','10',sys.executable,'-B',str(src/script),'--root',str(r),'--work',str(w),*extra],stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
  raw=Path(f'/proc/{child.pid}/stat').read_text();ticks=raw[raw.rfind(')')+2:].split()[19];launched[name]=dict(pid=child.pid,start_ticks=ticks,detached=True,script=script)
 save(w/'PIPELINE_LAUNCH_02.private.json',dict(epoch=time.time(),client_required=False,processes=launched,source_binding_sha256=sha(w/'SOURCE03_LAUNCH_BINDING.private.json')));print('Q32_DETACHED_CONTINUATION_LAUNCHED',json.dumps(launched),flush=True)
if __name__=='__main__':main()
