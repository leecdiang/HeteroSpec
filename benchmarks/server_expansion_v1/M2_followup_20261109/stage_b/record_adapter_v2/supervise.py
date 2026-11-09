"""Detached server supervisor: exact planned work, terminal archive and replay.

No SSH/client/session dependency after launch. No GitHub credentials. No new
scientific stages or blanket native retries. Only the record adapter's narrow
whitelist can continue unreserved, already frozen Stage B timing slots.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,signal,subprocess,time,traceback
def read(p):return json.loads(p.read_text())
def write(p,x):
 tmp=Path(str(p)+'.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');os.replace(tmp,p)
def alive(pid):
 try:
  raw=Path(f'/proc/{pid}/stat').read_text();return raw[raw.rfind(')')+2:].split()[0]!='Z'
 except OSError:return False
def workers(work):
 out=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   if(p/'comm').read_text().strip()!='transfer-worker':continue
   if str(work).encode()in(p/'cmdline').read_bytes():out.append(int(p.name))
  except OSError:pass
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--builds',type=Path,required=True);p.add_argument('--repo',type=Path,required=True);a=p.parse_args()
 r,w=a.root,a.work;here=Path(__file__).parent;py=str(r/'venv-03/bin/python');parent=read(w/'COORDINATOR_LAUNCH.private.json')['pid']
 stdout=(w/'record-adapter-v2.stdout.log').open('xb');stderr=(w/'record-adapter-v2.stderr.log').open('xb')
 cmd=['taskset','-c','32,33','nice','-n','10',py,'-B',str(here/'resume_timing.py'),'--root',str(r),'--work',str(w),'--source',str(a.source),'--builds',str(a.builds),'--repo',str(a.repo)]
 adapter=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,start_new_session=True,stdin=subprocess.DEVNULL)
 write(w/'RECORD_ADAPTER_V2_LAUNCH.private.json',dict(pid=adapter.pid,source_sha256=hashlib.sha256((here/'resume_timing.py').read_bytes()).hexdigest(),epoch=time.time()))
 deadline=datetime.datetime(2026,11,9,21,0,tzinfo=datetime.timezone(datetime.timedelta(hours=8))).timestamp()
 try:
  while True:
   active=workers(w);terminal=(w/'COMPLETE.json').exists()or bool(list(w.glob('STOPPED-*')));ar=adapter.poll()
   state=dict(epoch=time.time(),status='RUNNING',parent_alive=alive(parent),record_adapter_alive=ar is None,record_adapter_returncode=ar,active_native_workers=active,qualification_passed=(w/'QUALIFIED.json').exists(),timing_complete=(w/'RESULTS.json').exists(),complete=(w/'COMPLETE.json').exists(),pause=(w/'PAUSE.json').exists(),client_connection_required=False)
   write(w/'SUPERVISOR_STATUS.private.json',state)
   if terminal and not active and ar is not None:break
   if time.time()>deadline and active:
    # Recheck exact own command binding immediately before each signal.
    for pid in active:
     try:
      if str(w).encode()in Path(f'/proc/{pid}/cmdline').read_bytes():os.kill(pid,signal.SIGTERM)
     except ProcessLookupError:pass
    write(w/'OWN_TIMEOUT_BOUNDARY.private.json',dict(epoch=time.time(),reason='Declared hard shutdown boundary; only exact-study worker PIDs signalled',pids=active))
   if not alive(parent)and ar is not None and not active and not terminal:
    write(w/'STOPPED-SUPERVISOR.json',dict(status='STOPPED',reason='Coordinator disappeared without terminal evidence',automatic_retry=False));break
   time.sleep(5)
  stdout.close();stderr.close()
  (w/'GUARD_DONE_RECORD_RESUME02').touch(exist_ok=False)
  for _ in range(5):
   if(w/'GUARD_STOPPED_RECORD_RESUME02.private.json').exists()or(w/'PAUSE.json').exists():break
   time.sleep(3)
  if not(w/'GUARD_STOPPED_RECORD_RESUME02.private.json').exists()and not(w/'PAUSE.json').exists():write(w/'PAUSE.json',dict(reason='Observer did not acknowledge closeout',automatic_resume=False))
  export=r/'pr210-stage-b-export-02';replay=r/'pr210-stage-b-local-replay-02';env=dict(os.environ,CUDA_VISIBLE_DEVICES='')
  for script,args in [('archive.py',['--root',str(r),'--work',str(w),'--out',str(export)]),('replay_archive.py',['--bundle',str(export),'--out',str(replay)])]:
   with(w/(script+'.stdout.log')).open('xb')as so,(w/(script+'.stderr.log')).open('xb')as se:
    result=subprocess.run(['taskset','-c','32','nice','-n','19',py,'-B',str(here/script),*args],stdout=so,stderr=se,env=env,timeout=900)
   if result.returncode:raise RuntimeError(script+' failed; original data retained, no automatic retry')
  checked=read(replay/'CHECKED.json');assert checked['passed']
  terminal=dict(status='COMPLETE_LOCAL_ARCHIVE_AND_REPLAY'if(w/'COMPLETE.json').exists()else'STOPPED_EVIDENCE_ARCHIVED',epoch=time.time(),experiment_complete=(w/'COMPLETE.json').exists(),archive=str(export),replay=str(replay),archive_bundle=read(export/'BUNDLE.json'),replay_passed=True,public_GitHub_readback='PENDING_CONNECTED_CLIENT',native_jobs_queued=0,no_automatic_C_D_E_or_Q32=True)
  write(w/'SUPERVISOR_TERMINAL.private.json',terminal);write(export/'AUTOMATION_TERMINAL.json',{**terminal,'archive':'retained-host/export','replay':'retained-host/replay'})
  print(json.dumps(terminal),flush=True)
 except BaseException as e:
  write(w/'SUPERVISOR_FAILURE.private.json',dict(epoch=time.time(),error=str(e),traceback=traceback.format_exc(),data_retained=True,automatic_native_retry=False));raise
if __name__=='__main__':main()
