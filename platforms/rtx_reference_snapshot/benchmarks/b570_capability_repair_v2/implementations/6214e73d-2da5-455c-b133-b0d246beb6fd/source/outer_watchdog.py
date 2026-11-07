"""Independent CPU deadline/heartbeat/outer Job owner. Cannot attest its own OS exit."""
import argparse,datetime,json,os,shutil,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/rev2'))

p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--run',required=True);p.add_argument('--mode',choices=['development','cpu8'],required=True);p.add_argument('--phase-limit',type=float,default=15000);p.add_argument('--freeze-sha256');p.add_argument('--supervisor-script',required=True);a=p.parse_args()
ROOT=Path(a.root).resolve()
if a.mode=='cpu8':
    import hashlib
    raw=(ROOT/'CAPABILITY_FREEZE.json').read_bytes()
    if not a.freeze_sha256 or hashlib.sha256(raw).hexdigest()!=a.freeze_sha256:raise ValueError('INITIAL_FREEZE_DIGEST_MISMATCH')
    cold=json.loads(raw)
    for name,value in cold['files'].items():
        p=Path(name)
        if p.is_absolute() or '..' in p.parts or ':' in name or ROOT not in (ROOT/p).resolve().parents:raise ValueError('cold freeze path')
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=value:raise ValueError('COLD_SOURCE_DRIFT')
    prefixes=['source/','src/rev2/','legacy/repo/benchmarks/b570_supervision_fix_v2/host/']
    wanted={n for n in cold['files'] if any(n.startswith(t) for t in prefixes)}
    actual=set()
    for t in prefixes:
        for p in (ROOT/t).rglob('*'):
            if p.is_symlink() or p.is_junction():raise ValueError('cold source alias')
            if p.is_file():
                if '__pycache__' in p.parts or p.suffix in ['.dll','.pyd','.so','.pyc','.pyo']:raise ValueError('source import shadow')
                actual.add(p.relative_to(ROOT).as_posix())
    if actual!=wanted:raise ValueError('COLD_SOURCE_INVENTORY_DRIFT')
    if Path(a.supervisor_script).resolve()!=ROOT/'source/cpu8_supervisor.py':raise ValueError('unique CPU8 supervisor')
sys.path.insert(0,str(ROOT/'source'))
from win import *
from source_guard import check_sources

ROOT=check_root(a.root);RUN=(ROOT/a.run).resolve();need(ROOT in RUN.parents,'run confinement');RUN.mkdir(exist_ok=False)
os.environ['TEMP']=os.environ['TMP']=str(ROOT/'tmp')
started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
acq=json.loads((ROOT/'ACQUISITION.json').read_text());age=(datetime.datetime.fromisoformat(started_utc)-datetime.datetime.fromisoformat(acq['first_preparation_utc'].replace('Z','+00:00'))).total_seconds();need(age>=0,'TASK_CLOCK_REVERSED');task_remaining=21600-age
if a.mode=='development':need(age<5400,'D0_90_MINUTE_LIMIT')
begin=now();deadline=begin+int(min(a.phase_limit,task_remaining-1800,5400-age if a.mode=='development' else task_remaining-1800)*1e9)
need(deadline>begin,'TASK_DEADLINE');J=Journal(RUN/'WATCHDOG.jsonl');M=Journal(RUN/'WATCHDOG_SAMPLES.jsonl');job=make_job();child=None;registered=None;last_sample=None;last_heartbeat=None;error=None;closed=False;terminating=None;assigned=False;observed_residual=[];hb_offset=0;hb_pending=b'';hb_seq=0;latest_hb=None
progress_seq=0
watchdog_identity=identity(current())
def publish_progress():
    global progress_seq
    progress_seq+=1
    row=dict(pid=os.getpid(),created_filetime=watchdog_identity['created_filetime'],progress_seq=progress_seq,progress_ns=now())
    J.emit('WATCHDOG_PROGRESS',**row);atomic(RUN/'WATCHDOG_PROGRESS.json',row)
def monitor():
    global last_sample,last_heartbeat,hb_offset,hb_pending,hb_seq,latest_hb
    t=now();need(last_sample is None or t-last_sample<=5_000_000_000,'WATCHDOG_MONITOR_GAP')
    if last_sample is not None and t-last_sample<1_000_000_000:return
    ready=RUN/'HEARTBEATS.jsonl';hb=latest_hb
    if ready.exists():
        with ready.open('rb') as f:f.seek(hb_offset);block=f.read(65536)
        need(len(block)<65536,'HEARTBEAT_BACKLOG');hb_offset+=len(block);hb_pending+=block
        chunks=hb_pending.split(b'\n');hb_pending=chunks.pop()
        for line in chunks:
            row=json.loads(line);need(row['event']=='HEARTBEAT' and row['seq']==hb_seq+1,'heartbeat stream');hb_seq=row['seq'];latest_hb=hb=row
        if hb is not None:
            need(hb['pid']==child.pid,'heartbeat identity');need(hb['at_ns']<=now(),'heartbeat clock');last_heartbeat=hb['at_ns']
    age_ns=now()-(last_heartbeat if last_heartbeat is not None else begin);need(age_ns<=10_000_000_000,'SUPERVISOR_HEARTBEAT_TIMEOUT')
    members=job_pids(job);rows=[]
    for pid in members:
        h=open_process(0x100410,False,pid)
        if not h:
            need(pid not in job_pids(job),'resource open failed while still in job');rows.append(dict(pid=pid,exit_race=True,rss_bytes=None));continue
        try:
            ts=os_times(h)
            if alive(h):
                try:rows.append(dict(pid=pid,created_filetime=ts['created_filetime'],rss_bytes=rss(h)))
                except OSError:
                    if alive(h):raise
                    rows.append(dict(pid=pid,created_filetime=ts['created_filetime'],exit_race=True,rss_bytes=None))
            else:rows.append(dict(pid=pid,created_filetime=ts['created_filetime'],exit_race=True,rss_bytes=None))
        finally:checked(close(h),'Close resource process handle')
    own=rss(current());need(own<=512*1024**2,'WATCHDOG_RSS')
    sup=[r for r in rows if r['pid']==child.pid and r['rss_bytes'] is not None];actors=[r for r in rows if r['pid']!=child.pid and r['rss_bytes'] is not None]
    need(all(r['rss_bytes']<=512*1024**2 for r in sup) and len(actors)<=8 and all(r['rss_bytes']<=256*1024**2 for r in actors),'JOB_PROCESS_MEMORY')
    total=own+sum(r['rss_bytes'] or 0 for r in rows);need(total<=1536*1024**2,'AGGREGATE_MEMORY')
    free=shutil.disk_usage(ROOT).free;need(free>=10*1024**3,'DISK_FREE')
    storage=hb.get('storage_upper_bytes') if hb else None
    if storage is not None:need(storage<=1024**3,'STORAGE_LIMIT')
    end=now();need(last_sample is None or end-last_sample<=5_000_000_000,'WATCHDOG_MONITOR_GAP')
    M.emit('SAMPLE',begin_ns=t,end_ns=end,gap_ns=None if last_sample is None else end-last_sample,job_active=len(members),job_members=rows,watchdog_rss=own,total_observed_rss=total,heartbeat_age_ns=age_ns,storage_upper_bytes=storage,disk_free_bytes=free)
    last_sample=end
    publish_progress()
def capture_residual():
    for pid in job_pids(job):
        if child and pid==child.pid:continue
        h=open_process(0x100410,False,pid)
        if h:
            ident=identity(h);observed_residual.append((pid,h,ident));J.emit('RESIDUAL_RETAINED',pid=pid,**ident)
try:
    J.emit('WATCHDOG_START',pid=os.getpid(),begin_ns=begin,deadline_ns=deadline,unobserved_own_exit=True,started_utc=started_utc,freeze_sha256=a.freeze_sha256,**watchdog_identity)
    if a.mode=='cpu8':
        frozen=freeze_check(ROOT,a.freeze_sha256);check_sources(ROOT,frozen)
        from guards import wall_budget
        registrations=[json.loads(p.read_text()) for p in (ROOT/'development').glob('REVISION_*.json') if 'run' in json.loads(p.read_text())]
        wall_budget(acq,frozen,registrations,dict(started_utc=started_utc,begin_ns=begin),dict(task_elapsed_before_watchdog_seconds=age,begin_ns=begin,end_ns=begin))
    argv=[sys.executable,'-B',str(Path(a.supervisor_script).resolve()),'--root',str(ROOT),'--run',a.run,'--mode',a.mode,'--watchdog-pid',str(os.getpid()),'--deadline-ns',str(deadline)]
    if a.mode=='cpu8':argv += ['--freeze-sha256',a.freeze_sha256]
    need(ROOT in Path(a.supervisor_script).resolve().parents,'supervisor script confinement')
    child=spawn_suspended(argv,ROOT,RUN/'SUPERVISOR.stdout.log',RUN/'SUPERVISOR.stderr.log');registered=identity(child.process)
    J.emit('SUPERVISOR_CREATED_SUSPENDED',pid=int(child.pid),argv=argv,**registered)
    checked(job_assign(job,child.process),'Assign supervisor outer Job');assigned=True;J.emit('OUTER_JOB_ASSIGNED',pid=int(child.pid))
    publish_progress()
    need(resume(child.thread)!=0xffffffff,'ResumeThread');J.emit('SUPERVISOR_RESUMED',pid=int(child.pid));checked(close(child.thread),'Close supervisor thread');child.thread=None;J.emit('HANDLE_CLOSED',handle_kind='supervisor_primary_thread')
    while alive(child.process):
        try:
            need(now()<deadline,'WATCHDOG_HARD_DEADLINE');monitor()
            if a.mode=='cpu8':check_sources(ROOT,freeze_check(ROOT,a.freeze_sha256))
        except BaseException as e:
            if error is None:error=repr(e);J.emit('WATCHDOG_FAILURE',error=error);capture_residual();terminate_job(job);terminating=now();J.emit('OUTER_JOB_TERMINATE',reason=error)
        if terminating is not None and now()-terminating>5_000_000_000:raise RuntimeError('SUPERVISOR_CLEANUP_UNCONFIRMED')
        time.sleep(.02)
    J.emit('SUPERVISOR_EXIT_OBSERVED',pid=int(child.pid));ts=os_times(child.process);code=exit_code(child.process)
    need(ts['created_filetime']==registered['created_filetime'] and int(ts['exit_filetime'])>int(ts['created_filetime']),'SUPERVISOR_OS_EXIT')
    J.emit('SUPERVISOR_OS_EXIT',pid=int(child.pid),exit_code=code,**ts)
    remaining=job_pids(job)
    if remaining:
        if error is None:error='SUPERVISOR_EXIT_WITH_LIVE_DESCENDANTS'
        capture_residual();terminate_job(job);cutoff=now()+5_000_000_000
        while job_pids(job) and now()<cutoff:time.sleep(.01)
    need(not job_pids(job),'OUTER_JOB_NOT_EMPTY');J.emit('OUTER_JOB_EMPTY',active_pids=[])
    for pid,h,ident in observed_residual:
        need(not alive(h),'RESIDUAL_STILL_LIVE');end=os_times(h);J.emit('RESIDUAL_OS_EXIT',pid=pid,exit_code=exit_code(h),**end);checked(close(h),'Close residual');J.emit('HANDLE_CLOSED',pid=pid,handle_kind='residual_process')
    checked(close(child.process),'Close supervisor process');child.process=None;J.emit('HANDLE_CLOSED',handle_kind='supervisor_process')
    checked(close(job),'Close outer Job');job=None;J.emit('HANDLE_CLOSED',handle_kind='outer_job');closed=True
    summary=json.loads((RUN/'SUMMARY.json').read_text()) if (RUN/'SUMMARY.json').exists() else None
    if code!=0 and error is None:error='SUPERVISOR_NONZERO_EXIT'
    receipt=dict(status='WATCHDOG_CLOSED' if closed and error is None else 'WATCHDOG_FAILED',supervisor_pid=int(child.pid),supervisor_exit_code=code,supervisor_os_times=ts,outer_job_empty=True,owned_handles_closed=True,error=error,begin_ns=begin,end_ns=now(),task_elapsed_before_watchdog_seconds=age,summary_status=summary.get('status') if summary else None,watchdog_pid=os.getpid(),watchdog_os_exit_time=None,command_shell_os_lifetime=None,tool_host_os_lifetime=None,scope='Watchdog independently observes supervisor exit and outer Job; watchdog/shell/tool host own closure is outside this boundary')
    J.emit('WATCHDOG_END',receipt=receipt);dump_new(RUN/'WATCHDOG_RECEIPT.json',receipt)
except BaseException as e:
    error=repr(e);failure_trace=traceback.format_exc()
    # Cleanup must not depend on the same journal that just failed.
    def emergency_emit(event,**kw):
        try:J.emit(event,**kw)
        except BaseException:pass
    if child and child.process:
        try:
            if assigned:terminate_job(job)
            else:checked(terminate_process(child.process,125),'Terminate unassigned suspended supervisor')
            need(wait_handle(child.process,5000)==0,'EXCEPTION_EXIT_UNCONFIRMED');ts=os_times(child.process);need(int(ts['exit_filetime'])>0,'EXCEPTION_EXIT_TIME');emergency_emit('EXCEPTION_SUPERVISOR_OS_EXIT',pid=int(child.pid),exit_code=exit_code(child.process),assigned=assigned,**ts)
            if job:need(not job_pids(job),'EXCEPTION_JOB_NOT_EMPTY');emergency_emit('EXCEPTION_JOB_EMPTY',active_pids=[])
        except BaseException as cleanup:emergency_emit('CLEANUP_ERROR',error=repr(cleanup))
    elif job:
        try:terminate_job(job);emergency_emit('OUTER_JOB_EMERGENCY_TERMINATE')
        except BaseException as cleanup:emergency_emit('CLEANUP_ERROR',error=repr(cleanup))
    emergency_emit('WATCHDOG_EXCEPTION',error=error,traceback=failure_trace)
    dump_new(RUN/'WATCHDOG_INCOMPLETE.json',dict(error=error,cleanup_confirmed=False,supervisor_pid=int(child.pid) if child else None,at_ns=now()))
finally:
    if job:close(job)
    if child:
        if child.thread:close(child.thread)
        if child.process:close(child.process)
    J.end();M.end()
print(json.dumps(dict(watchdog_closed=closed,error=error,run=a.run)),flush=True)
sys.exit(0 if closed and error is None else 1)
