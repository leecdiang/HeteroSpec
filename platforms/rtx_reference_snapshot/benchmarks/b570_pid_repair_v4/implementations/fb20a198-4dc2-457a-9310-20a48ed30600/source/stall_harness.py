"""Native stalled-watchdog gate; independent 20s rescue thread, honest non-rescue result."""
import sys,os,json,time,threading,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from entry_bootstrap import bootstrap
DEPLOYED_ROOT=bootstrap(__file__)
ROOT=Path(sys.argv[1]).resolve();sys.path.insert(0,str(ROOT/'src/rev2'));from win import *
need(ROOT==DEPLOYED_ROOT,'ENTRY_ROOT_MISMATCH')
RUN=ROOT/'development/stall-r2-a1'
out=ROOT/'development/stall_harness_r2';out.mkdir(exist_ok=False);log=Journal(out/'EVENTS.jsonl');job=make_job();wd=None;sup=None;rescued=threading.Event();done=threading.Event();suspended=False;error=None
nt_suspend=api(N,'NtSuspendProcess',[W.HANDLE],W.LONG);nt_resume=api(N,'NtResumeProcess',[W.HANDLE],W.LONG)
def rescue():
    if not done.wait(20):
        rescued.set()
        try:
            log.emit('INDEPENDENT_RESCUE_FIRED',deadline_seconds=20)
            if wd:nt_resume(wd.process)
            terminate_job(job)
        except BaseException as e:
            try:log.emit('RESCUE_ERROR',error=repr(e))
            except BaseException:pass
thread=threading.Thread(target=rescue,name='INDEPENDENT_20S_RESCUE');thread.start()
try:
    log.emit('HARNESS_START',pid=os.getpid(),rescue_seconds=20,own_os_exit_filetime=None)
    argv=[sys.executable,'-B',str(ROOT/'source/outer_watchdog.py'),'--root',str(ROOT),'--run','development/stall-r2-a1','--mode','development','--phase-limit','30','--supervisor-script',str(ROOT/'source/stall_supervisor.py')]
    wd=spawn_suspended(argv,ROOT,out/'watchdog.stdout.log',out/'watchdog.stderr.log')
    wid=identity(wd.process);log.emit('WATCHDOG_CREATED_SUSPENDED',pid=int(wd.pid),**wid)
    checked(job_assign(job,wd.process),'rescue Job');need(resume(wd.thread)!=0xffffffff,'resume watchdog');close(wd.thread);wd.thread=None
    cut=now()+10_000_000_000
    while not (RUN/'STALL_READY.json').exists():
        need(now()<cut and alive(wd.process),'gate readiness');time.sleep(.01)
    raw=[json.loads(s) for s in (RUN/'WATCHDOG.jsonl').read_text().splitlines()]
    created=next(x for x in raw if x['event']=='SUPERVISOR_CREATED_SUSPENDED')
    sup=checked(open_process(0x100410,False,created['pid']),'retained supervisor')
    need(os_times(sup)['created_filetime']==created['created_filetime'],'supervisor identity')
    progress=json.loads((RUN/'WATCHDOG_PROGRESS.json').read_text());need(progress['pid']==wd.pid and progress['created_filetime']==wid['created_filetime'],'progress identity')
    need(nt_suspend(wd.process)>=0,'NtSuspendProcess');suspended=True
    # Pin the final published progress after suspension, not a racing pre-suspend read.
    progress=json.loads((RUN/'WATCHDOG_PROGRESS.json').read_text())
    need(progress['pid']==wd.pid and progress['created_filetime']==wid['created_filetime'],'suspended progress identity')
    log.emit('WATCHDOG_ACTUALLY_SUSPENDED',pid=int(wd.pid),created_filetime=wid['created_filetime'],progress=progress,alive=alive(wd.process),rss_bytes=rss(wd.process))
    while alive(sup):
        need(not rescued.is_set(),'rescue instead of supervisor cleanup');need(alive(wd.process),'watchdog disappeared');time.sleep(.01)
    sts=os_times(sup);log.emit('SUPERVISOR_OS_EXIT_WHILE_WATCHDOG_SUSPENDED',exit_code=exit_code(sup),**sts)
    same=identity(wd.process);log.emit('WATCHDOG_STILL_IDENTITY_RSS_READABLE',pid=int(wd.pid),created_filetime=same['created_filetime'],alive=alive(wd.process),rss_bytes=rss(wd.process))
    need(same['created_filetime']==wid['created_filetime'] and alive(wd.process),'watchdog retained identity')
    need(nt_resume(wd.process)>=0,'NtResumeProcess');suspended=False;log.emit('WATCHDOG_RESUMED')
    need(wait_handle(wd.process,5000)==0,'watchdog closure');wts=os_times(wd.process);log.emit('WATCHDOG_OS_EXIT',pid=int(wd.pid),exit_code=exit_code(wd.process),**wts)
    need(not job_pids(job),'rescue Job not empty')
    rows=[json.loads(s) for s in (RUN/'SUPERVISOR.jsonl').read_text().splitlines()]
    fail=[x for x in rows if x['event']=='SUPERVISOR_FAILURE'];need(len(fail)==1 and 'WATCHDOG_PROGRESS_STALE' in fail[0]['error'],'wrong stale detector')
    delay=fail[0]['at_ns']-progress['progress_ns'];need(5e9<delay<6e9,'stale detection bound')
    need(not (RUN/'MUST_NOT_START').exists(),'second case admitted')
    from verify import verify_case
    actual=verify_case(RUN/'D0_C1')
    receipt=json.loads((RUN/'WATCHDOG_RECEIPT.json').read_text())
    need(receipt['outer_job_empty'] and receipt['owned_handles_closed'] and receipt['supervisor_exit_code']==1,'stale cleanup receipt')
    need(not rescued.is_set(),'rescue cannot qualify')
    dump_new(out/'RESULT.json',dict(status='NATIVE_STALE_GATE_PASS',actual_detection_age_ns=delay,rescue_fired=False,case_before_stall=actual,supervisor_os_times=sts,watchdog_os_times=wts,watchdog_identity_rss_readable_while_stalled=True,next_case_started=False,job_empty=True))
except BaseException as e:
    error=repr(e);log.emit('HARNESS_FAILURE',error=error,traceback=traceback.format_exc())
finally:
    if wd and suspended:nt_resume(wd.process)
    if wd and alive(wd.process):terminate_job(job);need(wait_handle(wd.process,5000)==0,'harness cleanup unknown')
    if wd:log.emit('FINAL_WATCHDOG_OS_TIMES',pid=int(wd.pid),exit_code=exit_code(wd.process),**os_times(wd.process))
    need(not job_pids(job),'final rescue Job nonempty');log.emit('HARNESS_JOB_EMPTY',active_pids=[])
    if sup:checked(close(sup),'supervisor handle close')
    if wd:
        if wd.thread:close(wd.thread)
        checked(close(wd.process),'watchdog handle close')
    checked(close(job),'rescue Job close');done.set();thread.join(2);need(not thread.is_alive(),'rescue thread close');log.emit('HARNESS_CLOSED',error=error,rescue_fired=rescued.is_set());log.end()
print(json.dumps(dict(status='NATIVE_STALE_GATE_PASS' if error is None else 'FAIL',error=error)),flush=True)
sys.exit(0 if error is None else 1)
