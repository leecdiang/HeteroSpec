import argparse,datetime,json,os,secrets,shutil,subprocess,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from entry_bootstrap import bootstrap
DEPLOYED_ROOT=bootstrap(__file__)
from win import *
from exception_policy import ExceptionPolicy
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--run',required=True);p.add_argument('--mode',choices=['development','measured'],required=True);p.add_argument('--watchdog-pid',type=int,required=True);p.add_argument('--deadline-ns',type=int,required=True);p.add_argument('--freeze-sha256');a=p.parse_args()
ROOT=check_root(a.root);need(ROOT==DEPLOYED_ROOT,'ENTRY_ROOT_MISMATCH');RUN=(ROOT/a.run).resolve();need(ROOT in RUN.parents,'run confinement');SRC=ROOT/'src/rev2'
J=Journal(RUN/'SUPERVISOR.jsonl');S=Journal(RUN/'SAMPLES.jsonl');H=Journal(RUN/'HEARTBEATS.jsonl',64*1024**2);start=now();last_sample=None;last_heartbeat=0
baseline=inventory(ROOT);baseline_j=0;baseline_s=0;actor_starts=0;actor_life=0.;historical_starts=0;historical_life=0.;current_case=None;watchdog_h=None
from guards import ProgressGuard, admit_development_case
progress_guard=None
development_cases_started=0
from history import development_budget
history_budget=development_budget(ROOT,RUN);historical_starts=history_budget['starts'];historical_life=history_budget['lifetime_seconds'];J.emit('HISTORICAL_BUDGET_GATE',**history_budget)

def full_inventory():
    global baseline,baseline_j,baseline_s
    baseline=inventory(ROOT);baseline_j=J.bytes;baseline_s=S.bytes
    need(baseline['allocation_upper_bytes']<=1024**3,'STORAGE_LIMIT')
def storage_upper():return baseline['allocation_upper_bytes']+(J.bytes-baseline_j)+(S.bytes-baseline_s)+2*1024**2
def tick(live=None,job=None,force=False):
    global last_sample,last_heartbeat
    t=now();need(t<a.deadline_ns,'SUPERVISOR_DEADLINE')
    need(alive(watchdog_h),'WATCHDOG_EXITED')
    progress=json.loads((RUN/'WATCHDOG_PROGRESS.json').read_text())
    progress_fields=progress_guard.check(progress,now())
    if last_sample is not None:need(t-last_sample<=5_000_000_000,'MONITOR_GAP')
    if t-last_heartbeat>=250_000_000 or force:
        H.emit('HEARTBEAT',pid=os.getpid(),actor_starts=actor_starts,actor_lifetime_seconds=actor_life,storage_upper_bytes=storage_upper(),current_case=current_case);last_heartbeat=t
    if not force and last_sample is not None and t-last_sample<1_000_000_000:return
    begin=t;rows=[]
    for pid,h in (live or {}).items():
        if alive(h):
            try:rows.append(dict(pid=pid,created_filetime=os_times(h)['created_filetime'],rss_bytes=rss(h)))
            except OSError:
                if alive(h):raise
                S.emit('RESOURCE_EXIT_RACE',pid=pid,actual_resource_value=None)
    own=rss(current());outer=rss(watchdog_h);need(own<=512*1024**2 and outer<=512*1024**2,'SUPERVISOR_RSS')
    need(len(rows)<=8 and all(r['rss_bytes']<=256*1024**2 for r in rows),'ACTOR_RESOURCE_LIMIT')
    total=own+outer+sum(r['rss_bytes'] for r in rows);need(total<=1536*1024**2,'AGGREGATE_RSS')
    free=shutil.disk_usage(ROOT).free;need(free>=10*1024**3,'DISK_FREE')
    upper=storage_upper();need(upper<=1024**3,'STORAGE_LIMIT');active=len(job_pids(job)) if job else 0
    end=now();need(end-begin<=5_000_000_000,'SAMPLE_READ_GAP')
    progress_fields=progress_guard.check(progress,end)
    S.emit('SAMPLE',**progress_fields,begin_ns=begin,end_ns=end,gap_ns=None if last_sample is None else end-last_sample,live_identities=rows,job_active=active,supervisor_rss=own,watchdog_rss=outer,total_observed_rss=total,heartbeat_age_ns=end-last_heartbeat,storage_upper_bytes=upper,storage_method='full between-cycle allocation + current journal deltas + bounded 2MiB current-cycle reserve',disk_free_bytes=free)
    need(last_sample is None or end-last_sample<=5_000_000_000,'MONITOR_GAP');last_sample=end
def read_actor(folder,name,nonce,observed):
    f=folder/name
    if not f.exists():return None
    need(f.stat().st_size<=2048,'actor receipt oversized')
    try:d=json.loads(f.read_text())
    except json.JSONDecodeError:return None
    need(d.get('nonce')==nonce and d.get('pid') in observed,'actor nonce/identity');return d
def actor_argv(folder,cid,nonce,role='root'):
    return [sys.executable,'-B',str(SRC/'actor.py'),'--root',str(folder),'--case',cid,'--role',role,'--nonce',nonce]
def case(cid,label):
    global actor_starts,actor_life,current_case,development_cases_started
    if a.mode=='measured':freeze_check(ROOT,a.freeze_sha256)
    need(historical_starts+actor_starts+({'C3':3}.get(cid,1))<=6000,'ACTOR_START_BUDGET')
    need(historical_life+actor_life<21600,'ACTOR_LIFETIME_BUDGET')
    tick(force=True)
    if a.mode=='development':development_cases_started=admit_development_case(development_cases_started,history_budget['current_case_reservation'])
    folder=RUN/label;folder.mkdir();nonce=secrets.token_hex(16);current_case=label
    log=Journal(folder/'EVENTS.jsonl');begin=now();j=make_job();proc=None;live={};observed={};closed={};root_seen=False;ready_at=None;termination=None;terminate_at=None;crash_go=None;root_exit=None;errors=[];job_empty=False;handles_closed=[];exceptions=ExceptionPolicy()
    log.emit('CASE_BEGIN',case=cid,label=label,nonce=nonce,begin_ns=begin)
    fo=(folder/'stdout.log').open('xb');fe=(folder/'stderr.log').open('xb')
    try:
        proc=subprocess.Popen(actor_argv(folder,cid,nonce),stdin=subprocess.DEVNULL,stdout=fo,stderr=fe,cwd=folder,creationflags=0x00000009)
        log.emit('ROOT_CREATED_BY_API',pid=proc.pid,argv=actor_argv(folder,cid,nonce),debug_process=True)
        checked(job_assign(j,int(proc._handle)),'AssignProcessToJobObject(case)');log.emit('JOB_ASSIGNED',pid=proc.pid)
        while not root_seen or live:
            t=now()
            try:
                tick(live,j)
                live_life=sum(observed[pid]['age_at_registration_seconds']+(t-observed[pid]['registered_ns'])/1e9 for pid in live)
                need(historical_life+actor_life+live_life<=21600,'ACTOR_LIFETIME_BUDGET')
                need(t-begin<= (5 if cid=='C1' else 10)*10**9,'CASE_DEADLINE')
                if ready_at is None:
                    d=read_actor(folder,'root.ready.json',nonce,observed)
                    if d:ready_at=log.emit('READY_OBSERVED',pid=d['pid'],nonce=nonce)['at_ns']
                    need(t-begin<=(3 if cid=='C2' else 5)*10**9,'READY_DEADLINE')
                if cid=='C2' and ready_at is not None and termination is None and t-ready_at>=2_100_000_000:
                    need(proc.pid in live and alive(live[proc.pid]),'C2_NOT_ALIVE_AT_TIMEOUT')
                    terminate_at=now();log.emit('TIMEOUT_CONTROL',pid=proc.pid,ready_ns=ready_at,delta_ns=terminate_at-ready_at,actor_alive=True)
                    need(2_000_000_000<=terminate_at-ready_at<=3_000_000_000,'TIMEOUT_TRIGGER_WINDOW')
                    terminate_job(j);termination='EXPECTED_TIMEOUT';log.emit('JOB_TERMINATE',reason=termination,trigger_ns=terminate_at)
                if cid=='C3' and crash_go is None:
                    need(now()-begin<=5_000_000_000,'COMPLETE_TREE_READY_DEADLINE')
                    child=read_actor(folder,'child.ready.json',nonce,observed);grand=read_actor(folder,'grandchild.ready.json',nonce,observed)
                    if child and grand and ready_at and len(observed)==3:
                        need(observed[child['pid']]['parent_pid']==proc.pid and observed[grand['pid']]['parent_pid']==child['pid'],'TREE_PARENT_LINKS')
                        need(set(live)==set(observed) and all(alive(h) for h in live.values()),'TREE_NOT_ALIVE_AT_GO')
                        tree_ready=log.emit('TREE_READY_COMPLETE',root_pid=proc.pid,child_pid=child['pid'],grandchild_pid=grand['pid']);need(tree_ready['at_ns']-begin<=5_000_000_000,'COMPLETE_TREE_READY_DEADLINE')
                        crash_go=now();log.emit('CRASH_GO_CONTROL',nonce=nonce,root_pid=proc.pid,child_pid=child['pid'],grandchild_pid=grand['pid'],all_alive=True)
                        atomic(folder/'CRASH_GO.json',dict(nonce=nonce,at_ns=crash_go));log.emit('CRASH_GO_SENT',nonce=nonce)
                if terminate_at is not None:need(now()-terminate_at<=5_000_000_000,'TERMINATION_CLEANUP_DEADLINE')
                for n in ['stdout.log','stderr.log']:
                    need((folder/n).stat().st_size<=65536,'ACTOR_LOG_LIMIT')
            except BaseException as e:
                if not errors:errors.append(str(e));log.emit('REAL_FAILURE',error=repr(e))
                if termination not in ('FAILURE_CLEANUP',):
                    terminate_job(j);termination='FAILURE_CLEANUP';terminate_at=now();log.emit('JOB_TERMINATE',reason=termination)
                if now()-terminate_at>5_000_000_000:raise RuntimeError('CLEANUP_UNCONFIRMED')
            event=DE()
            if not wait_debug(C.byref(event),20):
                code=C.get_last_error();need(code in (0,121),'DEBUG_WAIT_FAILURE');continue
            status=0x00010002;exiting=None;exit_event=None
            if event.event==3:
                h=retain(event.u.create.process);ident=identity(h);pid=int(event.pid)
                role='root' if pid==proc.pid else 'child' if ident['parent_pid']==proc.pid else 'grandchild'
                need(pid not in observed,'duplicate actor PID');ident.update(registered_ns=now(),age_at_registration_seconds=max(0,(time.time_ns()//100+116444736000000000-int(ident['created_filetime']))/1e7));observed[pid]=ident;live[pid]=h;actor_starts+=1;root_seen|=pid==proc.pid
                log.emit('PROCESS_CREATE',pid=pid,role=role,**ident);exceptions.created((pid,ident['created_filetime']))
                if event.u.create.file:checked(close(event.u.create.file),'Close debug executable file')
                expected=subprocess.list2cmdline(actor_argv(folder,cid,nonce,role))
                if ident['command_sha256']!=hashlib.sha256(expected.encode()).hexdigest() or Path(ident['image']).resolve()!=Path(sys.executable).resolve():
                    errors.append('ACTOR_COMMAND_IDENTITY');terminate_job(j);termination='FAILURE_CLEANUP';terminate_at=now()
            elif event.event==6:
                if event.u.dll.file:
                    b=C.create_unicode_buffer(32768);n=query_path(event.u.dll.file,b,len(b),0)
                    if n and any(s in b.value.lower() for s in ['vulkan','nvcuda','cudart','ggml']):
                        log.emit('FORBIDDEN_MODULE',pid=int(event.pid),path=b.value);errors.append('FORBIDDEN_MODULE');terminate_job(j);termination='FAILURE_CLEANUP';terminate_at=now()
                    checked(close(event.u.dll.file),'Close DLL debug file')
            elif event.event==5:
                pid=int(event.pid);need(pid in live,'EXIT_WITHOUT_CREATE');exiting=live.pop(pid);exit_event=log.emit('EXIT_OBSERVED',pid=pid,exit_code=int(event.u.code))
            elif event.event==1:
                pid=int(event.pid);ident=(pid,observed[pid]['created_filetime']) if pid in live else None
                status=exceptions.decide(ident,int(event.u.code),int(event.u.exception.first_chance))
                log.emit('DEBUG_EXCEPTION',pid=pid,code=int(event.u.code),first_chance=int(event.u.exception.first_chance),continuation=status)
            checked(continue_debug(event.pid,event.tid,status),'ContinueDebugEvent')
            if exiting:
                checked(wait_handle(exiting,5000)==0,'exit signal');ts=os_times(exiting);pid=int(event.pid)
                need(ts['created_filetime']==observed[pid]['created_filetime'] and int(ts['exit_filetime'])>=int(ts['created_filetime']),'EXIT_IDENTITY')
                life=(int(ts['exit_filetime'])-int(ts['created_filetime']))/1e7;actor_life+=life
                record=log.emit('PROCESS_EXIT',pid=pid,exit_code=exit_event['exit_code'],exit_observed_ns=exit_event['at_ns'],lifetime_seconds=life,**ts);closed[pid]=record
                checked(close(exiting),'Close retained actor');handles_closed.append(pid);log.emit('HANDLE_CLOSED',pid=pid,handle_kind='retained_actor')
                if pid==proc.pid:
                    root_exit=record
                    if cid=='C3':
                        if crash_go is None or record['exit_code']!=7:errors.append('ABNORMAL_CONTROL_OR_EXIT')
                        terminate_at=root_exit['exit_observed_ns'];terminate_job(j);termination='EXPECTED_ABNORMAL_TREE' if not errors else 'FAILURE_CLEANUP';log.emit('JOB_TERMINATE',reason=termination,root_exit_ns=root_exit['exit_observed_ns'])
                    elif cid=='C2' and termination!='EXPECTED_TIMEOUT':errors.append('SPONTANEOUS_TIMEOUT_ACTOR_EXIT')
        job_empty=not job_pids(j);log.emit('JOB_EMPTY',active_pids=job_pids(j));need(job_empty,'CASE_JOB_NOT_EMPTY')
        proc.wait(timeout=5);proc._handle.Close();log.emit('HANDLE_CLOSED',handle_kind='popen_root')
        need(root_exit is not None and len(closed)==len(observed)==(3 if cid=='C3' else 1),'PROCESS_SET')
        if cid=='C1':
            need(root_exit['exit_code']==0 and ready_at is not None,'NORMAL_EXIT');need(now()-begin<=5_000_000_000,'NORMAL_DEADLINE')
            complete=read_actor(folder,'COMPLETE.json',nonce,observed);need(complete and complete.get('event')=='COMPLETE','NORMAL_COMPLETION_NONCE')
        if cid=='C2':need(termination=='EXPECTED_TIMEOUT' and root_exit['exit_code']!=0 and not (folder/'LATE_WORK.json').exists(),'TIMEOUT_OUTCOME')
        if cid=='C3':need(crash_go is not None and root_exit['exit_code']==7 and all(r['exit_code']!=0 for pid,r in closed.items() if pid!=proc.pid),'TREE_OUTCOME')
        if terminate_at is not None:need(now()-terminate_at<=5_000_000_000,'FINAL_CLEANUP_DEADLINE')
        need(not errors,';'.join(errors))
    except BaseException as e:
        errors.append(str(e));log.emit('CASE_ERROR',error=repr(e),traceback=traceback.format_exc())
        if live:
            # Fail closed. Never declare successful cleanup from job termination alone.
            terminate_job(j);log.emit('EMERGENCY_TERMINATE',unclosed=list(live))
    finally:
        fo.close();fe.close();log.emit('STDIO_CLOSED')
        empty=not job_pids(j);log.emit('FINAL_JOB_COUNT',active_pids=job_pids(j));checked(close(j),'Close case Job');log.emit('HANDLE_CLOSED',handle_kind='case_job')
        clean=empty and not live and len(handles_closed)==len(observed) and proc is not None and proc.returncode is not None
        result=dict(case=cid,label=label,status='PASS' if not errors and clean else 'FAIL',errors=errors,begin_ns=begin,end_ns=now(),observed=len(observed),closed=len(closed),job_empty=empty,cleanup_confirmed=clean,nonce=nonce)
        log.emit('CASE_CLOSED',**result);log.end();dump_new(folder/'RESULT.json',result);J.emit('CASE_RESULT',**result);current_case=None
    need(result['status']=='PASS','CASE_FAIL '+label+' '+str(errors));return result
summary=dict(mode=a.mode,status='INCOMPLETE',cases=[],cycles_completed=0,actor_starts=0,actor_lifetime_seconds=0)
try:
    watchdog_h=checked(open_process(0x100410,False,a.watchdog_pid),'Open watchdog for monitoring')
    progress_guard=ProgressGuard(a.watchdog_pid,os_times(watchdog_h)['created_filetime'])
    J.emit('SUPERVISOR_START',pid=os.getpid(),freeze_sha256=a.freeze_sha256,**identity(current()));tick(force=True)
    summary['cases']=[case('C1','D0_C1')]
    atomic(RUN/'STALL_READY.json',dict(pid=os.getpid(),at_ns=now(),after_case='D0_C1'))
    J.emit('BETWEEN_CASE_TICK_CONTROL',next_case='MUST_NOT_START',seconds=9)
    stop=now()+9_000_000_000
    while now()<stop:tick();time.sleep(.02)
    case('C2','MUST_NOT_START')
    summary['status']='UNEXPECTED_STALE_GATE_ADMISSION'
except BaseException as e:
    summary['status']='EXPECTED_GATE_REJECTION_CANDIDATE';summary['error']=repr(e);J.emit('SUPERVISOR_FAILURE',error=repr(e))
finally:
    summary.update(actor_starts=actor_starts,actor_lifetime_seconds=actor_life,historical_actor_starts=historical_starts,historical_actor_lifetime_seconds=historical_life,end_ns=now(),begin_ns=start)
    if watchdog_h:checked(close(watchdog_h),'Close watchdog monitoring handle');J.emit('HANDLE_CLOSED',handle_kind='watchdog_monitor')
    J.emit('SUPERVISOR_END',summary=summary);S.end();J.end();H.end();dump_new(RUN/'SUMMARY.json',summary)
sys.exit(1)
