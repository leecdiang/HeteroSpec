"""Hard-bounded CPU operation guard; outside the candidate command Job."""
import sys,json,time,os,hashlib,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'source'),str(ROOT/'src/rev2')]
from win import *
from budget_v6 import snapshot
p=__import__('argparse').ArgumentParser();p.add_argument('--intent',required=True);p.add_argument('--intent-sha256',required=True);a=p.parse_args()
fp=Path(a.intent).resolve();need(fp.parent==ROOT/'tools','intent confinement');need(sha(fp)==a.intent_sha256,'intent pin');x=json.loads(fp.read_bytes())
need(Path(x['root']).resolve()==ROOT and x['id'].replace('-','').isalnum(),'root/id')
need(type(x['seconds']) is int and 0<x['seconds']<=1200 and x['cleanup_seconds']==5,'deadline')
need(type(x['max_job_processes']) is int and 1<=x['max_job_processes']<=128,'job cap')
need(x['lifetime_bound_seconds']==(x['max_job_processes']+2)*(x['seconds']+5),'whole operation envelope')
state=snapshot(ROOT,x['stage'])
from campaign_budget import storage_check
storage=storage_check(ROOT)
folder=ROOT/'operations'/x['id'];folder.mkdir(parents=True,exist_ok=False)
j=Journal(folder/'EVENTS.jsonl');r=Journal(folder/'RESOURCES.jsonl');job=make_job();lim=LIMIT();lim.basic.flags=0x2000|0x8;lim.basic.active=x['max_job_processes'];checked(job_set(job,9,C.byref(lim),C.sizeof(lim)),'kernel active process cap')
child=None;error=None;begin=now();deadline=begin+x['seconds']*10**9;last=None;peak=0
done=threading.Event();deadline_fired=threading.Event()
def rescue_deadline():
 if not done.wait(x['seconds']):
  deadline_fired.set()
  try:terminate_job(job)
  finally:
   if not done.wait(4):os._exit(125)
rescue=threading.Thread(target=rescue_deadline,name='V6_OPERATION_DEADLINE',daemon=True);rescue.start()
try:
 j.emit('GUARD_START',pid=os.getpid(),intent_sha256=a.intent_sha256,budget=state,storage=storage,**identity(current()))
 child=spawn_suspended(x['argv'],ROOT,folder/'stdout.log',folder/'stderr.log');ident=identity(child.process);j.emit('OP_CREATED_SUSPENDED',pid=int(child.pid),argv=x['argv'],**ident)
 checked(job_assign(job,child.process),'operation Job assignment');need(resume(child.thread)!=0xffffffff,'resume');checked(close(child.thread),'thread close');child.thread=None
 while alive(child.process):
  start=now();need(start<=deadline,'OPERATION_DEADLINE');need(last is None or start-last<=10**9,'OPERATION_RESOURCE_GAP')
  ps=job_pids(job);peak=max(peak,len(ps));need(len(ps)<=x['max_job_processes'],'kernel cap')
  r.emit('SAMPLE',begin_ns=start,end_ns=now(),job_pids=ps,guard_rss=rss(current()))
  for n in ('stdout.log','stderr.log'):need((folder/n).stat().st_size<=16*1024**2,'operation log cap')
  last=now();time.sleep(.1)
 need(not deadline_fired.is_set() and now()<=deadline+1_000_000_000,'exit deadline');code=exit_code(child.process);j.emit('OP_OS_EXIT',pid=int(child.pid),exit_code=code,**os_times(child.process))
 need(not job_pids(job),'OPERATION_DESCENDANTS_REMAIN')
except BaseException as e:
 error=repr(e);j.emit('OPERATION_FAILURE',error=error);terminate_job(job)
finally:
 if child and child.process:
  if alive(child.process):terminate_job(job)
  stop=now()+5_000_000_000
  while job_pids(job) and now()<stop:time.sleep(.01)
  empty=not job_pids(job)
  if wait_handle(child.process,0)==0:j.emit('OP_TERMINAL_OS',pid=int(child.pid),exit_code=exit_code(child.process),**os_times(child.process))
  if child.thread:close(child.thread)
  checked(close(child.process),'root handle close')
 else:empty=not job_pids(job)
 acct=C.create_string_buffer(48);checked(job_query(job,1,acct,48,None),'job accounting');total_job_processes=C.c_uint32.from_buffer(acct,36).value
 need(total_job_processes+2<=x['starts_bound'],'OPERATION_START_BOUND')
 done.set();rescue.join(timeout=1);need(not rescue.is_alive(),'deadline thread not closed')
 checked(close(job),'operation job close')
 receipt=dict(status='CLOSED' if error is None and empty else 'FAILED',error=error,job_empty=empty,begin_ns=begin,end_ns=now(),peak_job_processes=peak,total_job_processes=total_job_processes,guard_own_exit='UNKNOWN',child_exit_code=code if 'code' in globals() else None,intent_sha256=a.intent_sha256)
 dump_new(folder/'RECEIPT.json',receipt);j.emit('GUARD_END',receipt=receipt);j.end();r.end()
print(json.dumps(dict(operation=x['id'],status=receipt['status'],error=error,job_empty=empty,child_exit_code=receipt['child_exit_code'])),flush=True)
sys.exit(0 if error is None and empty and receipt['child_exit_code']==0 else 1)
