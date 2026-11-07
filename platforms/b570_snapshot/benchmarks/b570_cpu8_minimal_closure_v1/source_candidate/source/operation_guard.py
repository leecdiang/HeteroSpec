"""Hard-bounded CPU operation guard; outside the candidate command Job."""
import sys,json,time,os,hashlib,threading
from pathlib import Path

# Pure, source-reviewable predicates; not a native B/C approval.
def _deadline_expired(rescue_fired, observed_ns, cutoff_ns):
 return bool(rescue_fired) or observed_ns>cutoff_ns

def _complete_member_inventory(job_total_starts, root_key, observed_keys):
 if type(job_total_starts) is not int or job_total_starts<0:
  return False
 members=set(observed_keys)
 if root_key is not None:
  members.add(root_key)
 return len(members)==job_total_starts

def _terminate_owned_root(job_assigned,child_alive,job_kill,root_kill):
 # When AssignProcessToJobObject fails, TerminateJobObject cannot reach
 # the CREATE_SUSPENDED root. TerminateProcess on the retained root handle
 # is mandatory; the caller still waits for its real OS exit before closing.
 if not child_alive:return 'ALREADY_EXITED'
 if job_assigned:
  job_kill();return 'ASSIGNED_JOB'
 root_kill();return 'UNASSIGNED_ROOT'

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'source'),str(ROOT/'src/rev2')]
from win import *
from budget_v6 import snapshot
p=__import__('argparse').ArgumentParser();p.add_argument('--intent',required=True);p.add_argument('--intent-sha256',required=True);a=p.parse_args()
fp=Path(a.intent).resolve();need(fp.parent==ROOT/'tools','intent confinement');need(sha(fp)==a.intent_sha256,'intent pin');x=json.loads(fp.read_bytes())
need(Path(x['root']).resolve()==ROOT and x['id'].replace('-','').isalnum(),'root/id')
need(x.get('stage') in ('B','C') and x.get('task_uuid')==json.loads((ROOT/'CAMPAIGN.json').read_bytes()).get('task_uuid'),'fresh task/stage operation binding')
# Consume the existing A2 operation-role map rather than inventing a second map.
from operation_roles_v7 import role_map,operation as verified_operation
roles=role_map(ROOT,x['stage'])['roles']
matches=[name for name,row in roles.items() if row.get('operation_id')==x['id']]
need(len(matches)==1,'unregistered current task operation role')
verified_id,verified=verified_operation(ROOT,matches[0],x['stage'])
need(verified_id==x['id'] and verified==x and sha(fp)==a.intent_sha256,
     'current task operation bytes or post-F0 template drift')
need(type(x['seconds']) is int and 0<x['seconds']<=1200 and x['cleanup_seconds']==5,'deadline')
need(type(x['max_job_processes']) is int and 1<=x['max_job_processes']<=128,'job cap')
from operation_pricing_v7 import envelope as price_operation
pricing=price_operation(x) # arithmetic only: provider proof still requires external native admission
state=snapshot(ROOT,x['stage'])
# snapshot already reserves every registered, unsettled operation at full ceiling.
# Do not add this quote twice, but refuse a missing or already settled operation.
need(state['open_operations'].count(x['id'])==1,'current operation not prospectively reserved')
from campaign_budget import storage_check
storage=storage_check(ROOT)
folder=ROOT/'operations'/x['id'];folder.mkdir(parents=True,exist_ok=False)
j=Journal(folder/'EVENTS.jsonl');r=Journal(folder/'RESOURCES.jsonl');job=make_job();lim=LIMIT();lim.basic.flags=0x2000|0x8;lim.basic.active=x['max_job_processes'];checked(job_set(job,9,C.byref(lim),C.sizeof(lim)),'kernel active process cap')

# A failed journal write cannot prevent root termination, OS wait or handle close.
cleanup_log_errors=[]
def _cleanup_emit(event,**fields):
 try:j.emit(event,**fields)
 except BaseException as logging_error:
  cleanup_log_errors.append(event+': '+repr(logging_error))

def limit_readback():
 q=LIMIT();checked(job_query(job,9,C.byref(q),C.sizeof(q),None),'Job limit readback')
 b=C.create_string_buffer(48);checked(job_query(job,1,b,48,None),'Job accounting readback')
 return dict(flags=int(q.basic.flags),active_limit=int(q.basic.active),total=C.c_uint32.from_buffer(b,36).value,active=C.c_uint32.from_buffer(b,40).value,terminated=C.c_uint32.from_buffer(b,44).value)
def _require_member_flag(in_job):
 need(in_job is True,'FOREIGN_OR_REUSED_JOB_PID')
 return True

def sample_members(ps):
 rows=[]
 for pid in ps:
  h=open_process(0x101000,False,pid)
  if not h:
   e=C.get_last_error();rows.append(dict(pid=pid,query_error=e));continue
  try:
   is_member=W.BOOL()
   checked(process_in_job(h,job,C.byref(is_member)),'IsProcessInJob')
   _require_member_flag(bool(is_member.value))
   ot=os_times(h);key=(pid,ot['created_filetime'])
   if key not in retained:
    retained[key]=h;h=None
    j.emit('MEMBER_IDENTITY',pid=pid,**identity(retained[key]))
   hh=retained[key];rows.append(dict(pid=pid,live=alive(hh),exit_code=exit_code(hh),**os_times(hh)))
  finally:
   if h:checked(close(h),'duplicate query handle close')
 return rows
retained={};member_exits_complete=True
readback=limit_readback();j.emit('JOB_LIMIT_READBACK',configured_active=x['max_job_processes'],actual=readback)
need(readback['active_limit']==x['max_job_processes'] and readback['flags']&0x2008==0x2008,'JOB_LIMIT_READBACK_MISMATCH')

child=None;job_assigned=False;error=None;code=None;root_key=None;begin=now();deadline=begin+x['seconds']*10**9;last=None;peak=0
done=threading.Event();deadline_fired=threading.Event()
def rescue_deadline():
 if not done.wait(x['seconds']):
  deadline_fired.set()
  try:
   if child and child.process and not job_assigned and alive(child.process):
    checked(terminate_process(child.process,125),'rescue unassigned suspended root')
   else:terminate_job(job)
  finally:
   if not done.wait(4):os._exit(125)
rescue=threading.Thread(target=rescue_deadline,name='V6_OPERATION_DEADLINE',daemon=True);rescue.start()
try:
 j.emit('GUARD_START',pid=os.getpid(),intent_sha256=a.intent_sha256,budget=state,storage=storage,**identity(current()))
 child=spawn_suspended(x['argv'],ROOT,folder/'stdout.log',folder/'stderr.log');ident=identity(child.process);root_key=(int(child.pid),ident['created_filetime']);j.emit('OP_CREATED_SUSPENDED',pid=int(child.pid),argv=x['argv'],**ident)
 checked(job_assign(job,child.process),'operation Job assignment');job_assigned=True
 need(resume(child.thread)!=0xffffffff,'resume');checked(close(child.thread),'thread close');child.thread=None
 while alive(child.process):
  start=now();need(start<=deadline,'OPERATION_DEADLINE');need(last is None or start-last<=10**9,'OPERATION_RESOURCE_GAP')
  ps=job_pids(job);peak=max(peak,len(ps));members=sample_members(ps)
  r.emit('READ_OBSERVATION',begin_ns=start,end_ns=now(),job_pids=ps,members=members,accounting=limit_readback())
  need(all('query_error' not in z for z in members),'MEMBER_QUERY_FAILURE')
  need(len(ps)<=x['max_job_processes'],'kernel cap')
  r.emit('SAMPLE',begin_ns=start,end_ns=now(),job_pids=ps,guard_rss=rss(current()))
  for n in ('stdout.log','stderr.log'):need((folder/n).stat().st_size<=16*1024**2,'operation log cap')
  last=now();time.sleep(.1)
 need(not deadline_fired.is_set() and now()<=deadline+1_000_000_000,'OPERATION_DEADLINE');code=exit_code(child.process);j.emit('OP_OS_EXIT',pid=int(child.pid),exit_code=code,**os_times(child.process))
 need(not job_pids(job),'OPERATION_DESCENDANTS_REMAIN')
except BaseException as e:
 error=repr(e)
 observed_ns=now()
 # An exception text containing OPERATION_DEADLINE is not enough.
 if _deadline_expired(deadline_fired.is_set(),observed_ns,deadline):
  _cleanup_emit('OPERATION_DEADLINE',source='GUARD_MONOTONIC_CHECK',
         deadline_ns=deadline,observed_ns=observed_ns,
         rescue_fired=deadline_fired.is_set(),original_error=error)
  error='OPERATION_DEADLINE: '+error
 _cleanup_emit('OPERATION_FAILURE',error=error)
 # An unassigned CREATE_SUSPENDED root is not reachable by this Job.
 # Let the mandatory retained-handle cleanup in finally terminate and wait
 # for it directly. An assigned Job is terminated here even when its root
 # has exited but descendants may remain.
 if job_assigned:
  terminate_job(job)
finally:
 if child and child.process:
  if alive(child.process):
   # CRITICAL: do not write to the journal until the suspended root has been
   # terminated or a termination failure has been captured.
   try:
    cleanup_route=_terminate_owned_root(job_assigned,True,
        lambda:terminate_job(job),
        lambda:checked(terminate_process(child.process,125),'terminate unassigned suspended root'))
   except BaseException as kill_error:
    cleanup_route='TERMINATE_REQUEST_FAILED'
    error=(error+'; ' if error else '')+'DIRECT_OR_JOB_TERMINATION_FAILED:'+repr(kill_error)
   if not job_assigned:
    _cleanup_emit('UNASSIGNED_SUSPENDED_ROOT_TERMINATION',pid=int(child.pid),
          created_filetime=root_key[1] if root_key else os_times(child.process)['created_filetime'])
  else:cleanup_route='ALREADY_EXITED'
  stop=now()+5_000_000_000
  while job_pids(job) and now()<stop:time.sleep(.01)
  empty=not job_pids(job)

  remaining=max(0,(stop-now())//1_000_000)
  wr=wait_handle(child.process,int(remaining))
  if wr==0:
   code=exit_code(child.process);_cleanup_emit('OP_TERMINAL_OS',pid=int(child.pid),exit_code=code,**os_times(child.process))
  else:
   member_exits_complete=False;_cleanup_emit('ROOT_EXIT_UNCONFIRMED',pid=int(child.pid),wait_result=int(wr))
  for (pid,created),h in retained.items():
   wr=wait_handle(h,max(0,int((stop-now())//1_000_000)))
   if wr==0:_cleanup_emit('MEMBER_TERMINAL_OS',pid=pid,exit_code=exit_code(h),**os_times(h))
   else:member_exits_complete=False;_cleanup_emit('MEMBER_EXIT_UNCONFIRMED',pid=pid,created_filetime=created,wait_result=int(wr))
   checked(close(h),'retained member handle close')
  _cleanup_emit('MEMBER_HANDLES_CLOSED',complete=member_exits_complete,count=len(retained))
  if child.thread:close(child.thread)
  checked(close(child.process),'root handle close')
 else:empty=not job_pids(job)
 acct=C.create_string_buffer(48);checked(job_query(job,1,acct,48,None),'job accounting');total_job_processes=C.c_uint32.from_buffer(acct,36).value
 # Bounds discovered at closeout must FAIL the operation, not raise before
 # the Job handle and retained evidence can be closed.
 bound_errors=[]
 # Polling may miss short-lived children. A successful closeout must account
 # for every cumulative Job start using preserved native identities.
 if not _complete_member_inventory(total_job_processes,root_key,retained.keys()):
  observed_keys=set(retained)
  if root_key is not None:observed_keys.add(root_key)
  bound_errors.append('OPERATION_MEMBER_CENSUS_GAP')
  _cleanup_emit('OPERATION_MEMBER_CENSUS_GAP',job_total=total_job_processes,
         observed_identity_count=len(observed_keys))
 if total_job_processes>pricing['owned_job_starts_limit']:
  bound_errors.append('OPERATION_OWNED_START_BOUND')
 if total_job_processes+pricing['owned_outer_starts_limit']>x['starts_bound']:
  bound_errors.append('OPERATION_TOTAL_START_BOUND')
 if bound_errors:
  error=(error+'; ' if error else '')+'; '.join(bound_errors)
  _cleanup_emit('OPERATION_FAILURE',error=error)
 done.set();rescue.join(timeout=1)
 if rescue.is_alive():
  error=(error+'; ' if error else '')+'DEADLINE_THREAD_NOT_CLOSED'
  _cleanup_emit('OPERATION_FAILURE',error=error)
 checked(close(job),'operation job close');_cleanup_emit('OP_JOB_HANDLE_CLOSED',job_empty=empty)
 if cleanup_log_errors:
  error=(error+'; ' if error else '')+'CLEANUP_JOURNAL_FAILURE:'+'|'.join(cleanup_log_errors)
 receipt=dict(job_assignment_confirmed=job_assigned,cleanup_route=cleanup_route if child and child.process else 'NO_CHILD',status='CLOSED' if error is None and empty and member_exits_complete and code==0 else 'FAILED',member_exits_complete=member_exits_complete,error=error,job_empty=empty,begin_ns=begin,end_ns=now(),peak_job_processes=peak,total_job_processes=total_job_processes,guard_own_exit='UNKNOWN',child_exit_code=code,intent_sha256=a.intent_sha256)
 dump_new(folder/'RECEIPT.json',receipt);_cleanup_emit('GUARD_END',receipt=receipt);j.end();r.end()
print(json.dumps(dict(operation=x['id'],status=receipt['status'],error=error,job_empty=empty,child_exit_code=receipt['child_exit_code'])),flush=True)
sys.exit(0 if error is None and not cleanup_log_errors and empty and member_exits_complete and receipt['child_exit_code']==0 else 1)
