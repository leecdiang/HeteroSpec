"""CPU task-command observer. Own Job + DEBUG_PROCESS, never self-certifies own OS exit."""
import argparse,sys,os,json,time,hashlib,subprocess,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from entry_bootstrap import bootstrap
DEPLOYED_ROOT=bootstrap(__file__)
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--id',required=True);p.add_argument('--seconds',type=float,required=True);p.add_argument('--kind',choices=['case','aux','review'],default='case');p.add_argument('argv',nargs=argparse.REMAINDER);a=p.parse_args()
ROOT=Path(a.root).resolve();sys.path.insert(0,str(ROOT/'src/rev2'));from win import *
need(ROOT==DEPLOYED_ROOT,'ENTRY_ROOT_MISMATCH')
need(ROOT.parent==Path('C:/hs/b570-capability-v1').resolve(),'fresh root')
need(a.id.replace('-','').replace('_','').isalnum(),'id')
from observer_policy import profile,violations
from job_census import census
from process_registry import Registry,key
from exception_policy import ExceptionPolicy
exceptions=ExceptionPolicy()
limits=profile(a.kind,a.seconds)
argv=a.argv[1:] if a.argv and a.argv[0]=='--' else a.argv;need(argv,'argv')
folder=ROOT/'processes'/a.id;folder.mkdir(parents=True,exist_ok=False);J=Journal(folder/'OS_EVENTS.jsonl');M=Journal(folder/'RESOURCES.jsonl')
job=make_job();proc=None;registry=Registry(sys.modules['win'],J);live=registry.live;observed=registry.observed;closed=registry.closed;root_seen=False;root_exited=False;failure=None;cutoff=now()+int(a.seconds*1e9);cleanup_at=None;last_sample=0;pending=None
def launch():
    sa=SA(C.sizeof(SA),None,True);hs=[];pi=PI();made=False
    try:
        for path,access,disp in [('NUL',0x80000000,3),(str(folder/'stdout.log'),0x40000000,1),(str(folder/'stderr.log'),0x40000000,1)]:
            h=create_file(path,access,1,C.byref(sa),disp,128,None);need(h not in (None,C.c_void_p(-1).value),'capture file');hs.append(h)
        si=SI();si.cb=C.sizeof(si);si.flags=0x100;si.stdin,si.stdout,si.stderr=hs
        s=C.create_unicode_buffer(subprocess.list2cmdline(argv))
        checked(create_process(argv[0],s,None,None,True,0x0000000d,None,str(ROOT),C.byref(si),C.byref(pi)),'debug suspended create');made=True
        ident=identity(pi.process);registry.root_key=key(int(pi.pid),ident);J.emit('ROOT_CREATED_SUSPENDED',pid=int(pi.pid),argv=argv,**ident)
        checked(job_assign(job,pi.process),'command Job assignment');J.emit('JOB_ASSIGNED',pid=int(pi.pid))
        need(resume(pi.thread)!=0xffffffff,'resume');checked(close(pi.thread),'close initial thread');pi.thread=None;J.emit('ROOT_RESUMED',pid=int(pi.pid));return pi
    except BaseException:
        if made:
            terminate_process(pi.process,125);wait_handle(pi.process,5000)
            J.emit('UNRETURNED_ROOT_EXIT',pid=int(pi.pid),exit_code=exit_code(pi.process),**os_times(pi.process))
            if pi.thread:close(pi.thread)
            close(pi.process)
        raise
    finally:
        for h in hs:checked(close(h),'capture duplicate close')
try:
    observed_begin=now();J.emit('OBSERVER_START',pid=os.getpid(),argv=argv,seconds=a.seconds,observer_os_exit_filetime=None,process_kind=a.kind,limits=limits)
    proc=launch()
    while not root_seen or live:
        t=now()
        if cleanup_at is None and t>cutoff:failure='COMMAND_TIMEOUT';terminate_job(job);cleanup_at=t;J.emit('JOB_TERMINATE',reason=failure)
        if cleanup_at is not None and t-cleanup_at>5e9:raise RuntimeError('COMMAND_CLEANUP_UNCONFIRMED')
        if t-last_sample>=1e9:
            snapshot=census(job,sys.modules['win']);vals=snapshot['members']
            own=rss(current());M.emit('READ_OBSERVATION',begin_ns=t,end_ns=now(),**snapshot,observer_rss=own,kind=a.kind)
            bad=violations(limits,vals,own,len(snapshot['job_pids']))
            M.emit('LIMIT_DECISION',limits=limits,violations=bad,**snapshot,observer_rss=own)
            need(not bad,'COMMAND_RESOURCE_LIMIT:'+','.join(bad))
            M.emit('SAMPLE',begin_ns=t,end_ns=now(),members=vals,observer_rss=own)
            for n in ['stdout.log','stderr.log']:need((folder/n).stat().st_size<=16*1024**2,'command output cap')
            last_sample=now()
        ev=DE()
        if not wait_debug(C.byref(ev),20):
            need(C.get_last_error() in (0,121),'debug wait');continue
        pending=(ev.pid,ev.tid,0x80010001 if ev.event==1 else 0x00010002)
        code=0x00010002;exiting=None
        if ev.event==3:
            registered=registry.create(int(ev.pid),ev.u.create.process,ev.u.create.file)
            exceptions.created(registered);root_seen|=registered==registry.root_key
        elif ev.event==6 and ev.u.dll.file:
            b=C.create_unicode_buffer(32768);n=query_path(ev.u.dll.file,b,len(b),0)
            if n and any(x in b.value.lower() for x in ['vulkan','nvcuda','cudart','ggml','igvk']):
                failure='FORBIDDEN_MODULE';terminate_job(job);cleanup_at=now();J.emit('FORBIDDEN_MODULE',pid=int(ev.pid),path=b.value)
            checked(close(ev.u.dll.file),'DLL debug file close')
        elif ev.event==5:
            exiting=registry.exit_observed(int(ev.pid),int(ev.u.code))
        elif ev.event==1:
            code=exceptions.decide(registry.live.get(int(ev.pid)),int(ev.u.code),int(ev.u.exception.first_chance))
            J.emit('EXCEPTION',pid=int(ev.pid),code=int(ev.u.code),first_chance=int(ev.u.exception.first_chance),continuation=code)
        checked(continue_debug(ev.pid,ev.tid,code),'continue command debug');pending=None
        if exiting:
            registry.complete_exit(exiting,int(ev.u.code))
            if exiting==registry.root_key:root_exited=True
    need(root_exited and registry.complete() and not job_pids(job),'observed Job not empty');J.emit('JOB_EMPTY',active_pids=[])
    actual=exit_code(proc.process);need(wait_handle(proc.process,0)==0,'root actual exit');checked(close(proc.process),'root process close');proc.process=None;J.emit('HANDLE_CLOSED',handle_kind='root_process')
    checked(close(job),'command Job close');job=None;J.emit('HANDLE_CLOSED',handle_kind='command_job')
    receipt=dict(status='CLOSED' if failure is None else 'FAILED',root_exit_code=actual,error=failure,all_observed_closed=registry.complete(),observed=len(observed),closed=len(closed),lifetime_seconds=sum(x['lifetime_seconds'] for x in closed.values()),begin_ns=observed_begin,end_ns=now(),observer_pid=os.getpid(),observer_os_exit_filetime=None)
    dump_new(folder/'RECEIPT.json',receipt);J.emit('OBSERVER_END',receipt=receipt)
except BaseException as e:
    failure=repr(e);cleanup_error=None
    def safe(event,**kw):
        try:J.emit(event,**kw)
        except BaseException:pass
    safe('OBSERVER_FAILURE',error=failure,traceback=traceback.format_exc(),unclosed=registry.unresolved(),identity_coverage_errors=registry.coverage_errors)
    try:
        if job:terminate_job(job)
        if pending:
            checked(continue_debug(*pending),'continue pending debug during cleanup');pending=None
        stop=now()+5_000_000_000
        while (not root_seen or live or registry.handles or registry.orphans or job_pids(job)) and now()<stop:
            de=DE()
            if not wait_debug(C.byref(de),20):
                need(C.get_last_error() in (0,121),'cleanup debug wait');continue
            closing=None;cleanup_status=0x80010001 if de.event==1 else 0x00010002
            try:
                if de.event==3:
                    registered=registry.create(int(de.pid),de.u.create.process,de.u.create.file)
                    exceptions.created(registered);root_seen|=registered==registry.root_key
                elif de.event==6 and de.u.dll.file:close(de.u.dll.file)
                elif de.event==5:closing=registry.exit_observed(int(de.pid),int(de.u.code))
                elif de.event==1:
                    cleanup_status=exceptions.decide(registry.live.get(int(de.pid)),int(de.u.code),int(de.u.exception.first_chance))
                    J.emit('EXCEPTION',pid=int(de.pid),code=int(de.u.code),first_chance=int(de.u.exception.first_chance),continuation=cleanup_status)
            except BaseException as event_error:
                safe('CLEANUP_EVENT_ERROR',error=repr(event_error),pid=int(de.pid))
            finally:
                checked(continue_debug(de.pid,de.tid,cleanup_status),'continue cleanup debug')
            if closing:registry.complete_exit(closing,int(de.u.code))
        registry.finish_signalled()
        need(root_seen and registry.complete() and not job_pids(job),'COMMAND_CLEANUP_UNCONFIRMED')
        if proc and proc.process:need(wait_handle(proc.process,0)==0,'root cleanup');safe('ROOT_OS_EXIT_AFTER_FAILURE',pid=int(proc.pid),exit_code=exit_code(proc.process),**os_times(proc.process))
        safe('FAILURE_JOB_EMPTY',active_pids=[])
    except BaseException as ce:cleanup_error=repr(ce);safe('CLEANUP_ERROR',error=cleanup_error)
    dump_new(folder/'INCOMPLETE.json',dict(error=failure,unclosed=registry.unresolved(),identity_coverage_errors=registry.coverage_errors,cleanup_confirmed=cleanup_error is None,cleanup_error=cleanup_error))

finally:
    registry.release_remaining()
    if job:close(job)
    if proc and proc.process:close(proc.process)
    J.end();M.end()
print(json.dumps(dict(command=a.id,error=failure,root_exit_code=actual if 'actual' in globals() else None)),flush=True)
sys.exit(0 if failure is None and actual==0 else 1)
