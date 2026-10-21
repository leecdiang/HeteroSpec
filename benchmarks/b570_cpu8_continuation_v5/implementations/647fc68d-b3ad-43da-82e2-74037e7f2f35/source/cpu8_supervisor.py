"""CPU8-specific supervisor. No capability measured mode and no synthetic role reuse."""
import argparse,sys,os,json,time,subprocess,traceback,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--run',required=True);p.add_argument('--mode',choices=['cpu8'],required=True);p.add_argument('--watchdog-pid',type=int,required=True);p.add_argument('--deadline-ns',type=int,required=True);p.add_argument('--freeze-sha256',required=True);a=p.parse_args()
ROOT=Path(a.root).resolve();sys.path.insert(0,str(ROOT/'src/rev2'));sys.path.insert(0,str(ROOT/'source'));from win import *
from guards import ProgressGuard
from source_guard import check_sources
import cpu8_audit
from campaign_budget import process_check,storage_check
RUN=ROOT/a.run;need(ROOT in RUN.resolve().parents,'run confinement')
J=Journal(RUN/'SUPERVISOR.jsonl');H=Journal(RUN/'HEARTBEATS.jsonl');S=Journal(RUN/'SAMPLES.jsonl');begin=now();wd=checked(open_process(0x100410,False,a.watchdog_pid),'watchdog handle');guard=ProgressGuard(a.watchdog_pid,os_times(wd)['created_filetime']);last_hb=0;last_budget=0;budget_state=None;last_sample=None;active=None
frozen=freeze_check(ROOT,a.freeze_sha256);check_sources(ROOT,frozen)
plan=json.loads((ROOT/'CPU8_PLAN.json').read_text());need(len(plan['cases'])==8,'eight cases only');out=[];error=None
def tick(force=False):
    global last_hb,last_sample,last_budget,budget_state
    t=now();need(t<a.deadline_ns,'CPU8_SUPERVISOR_DEADLINE');need(alive(wd),'WATCHDOG_EXITED');prog=json.loads((RUN/'WATCHDOG_PROGRESS.json').read_text());fields=guard.check(prog,t)
    if last_sample is not None:need(t-last_sample<=5e9,'CPU8_OUTER_MONITOR_GAP')
    if t-last_budget>=1_000_000_000 or force:
        budget_state=dict(process=process_check(ROOT),storage=storage_check(ROOT));last_budget=now()
    if t-last_hb>=250_000_000 or force:
        storage=budget_state['storage']['allocation_upper_bytes']
        H.emit('HEARTBEAT',pid=os.getpid(),actor_starts=budget_state['process']['known_identities'],actor_lifetime_seconds=budget_state['process']['actual_covered_lifetime_seconds'],campaign_budget=budget_state,storage_upper_bytes=storage,current_case=active);last_hb=t
    if last_sample is None or t-last_sample>=1e9 or force:
        own=rss(current());outer=rss(wd);free=shutil.disk_usage(ROOT).free;need(own<=512*1024**2 and outer<=512*1024**2 and free>=10*1024**3,'CPU8_OUTER_RESOURCES')
        end=now();fields=guard.check(prog,end);need(last_sample is None or end-last_sample<=5e9,'CPU8_OUTER_MONITOR_GAP')
        S.emit('SAMPLE',begin_ns=t,end_ns=end,supervisor_rss=own,watchdog_rss=outer,disk_free_bytes=free,**fields);last_sample=end
try:
    J.emit('SUPERVISOR_START',pid=os.getpid(),freeze_sha256=a.freeze_sha256,**identity(current()));tick(True)
    gates=json.loads((ROOT/'D0_GATE_INDEX.json').read_text());need(gates['all_required_passed'] is True,'D0_NATIVE_GATES_NOT_QUALIFIED')
    for i,spec in enumerate(plan['cases']):
        check_sources(ROOT,freeze_check(ROOT,a.freeze_sha256));tick(True);active=spec['id'];runid=spec['run_id'];name='formal-'+str(i)
        intent=dict(run_id=runid,case_id=active,target=spec['target'],fault_id=spec['fault_id'],detector=spec['detector'],freeze_sha256=a.freeze_sha256)
        admission_budget=process_check(ROOT,reserve_starts=40);storage_check(ROOT)
        J.emit('CPU8_CASE_ADMISSION',campaign_budget=admission_budget,**intent)
        argv=[sys.executable,'-B',str(ROOT/'source/observe.py'),'--root',str(ROOT),'--id',name,'--seconds',str(spec['case_seconds']+30),'--',sys.executable,'-B',str(ROOT/'source/bridge.py'),'--root',str(ROOT),'--run',runid,'--case',active,'--phase','FORMAL','--freeze-sha256',a.freeze_sha256]
        job=make_job();child=None
        try:
            child=spawn_suspended(argv,ROOT,RUN/(name+'.stdout.log'),RUN/(name+'.stderr.log'));ident=identity(child.process);J.emit('AUX_CREATED_SUSPENDED',pid=int(child.pid),argv=argv,freeze_sha256=a.freeze_sha256,**ident)
            checked(job_assign(job,child.process),'CPU8 case Job assignment');need(resume(child.thread)!=0xffffffff,'resume auxiliary');close(child.thread);child.thread=None
            t0=now()
            while alive(child.process):
                tick();need(now()-t0<=(spec['case_seconds']+30)*1e9,'CPU8_SLOT_HARD_DEADLINE');time.sleep(.02)
            times_=os_times(child.process);code=exit_code(child.process);J.emit('AUX_OS_EXIT',pid=int(child.pid),exit_code=code,**times_)
            need(code==0 and int(times_['exit_filetime'])>0 and not job_pids(job),'CPU8_SLOT_EXECUTION_OR_CLEANUP')
        finally:
            if child and child.process and alive(child.process):terminate_job(job);need(wait_handle(child.process,5000)==0,'auxiliary cleanup unknown')
            need(not job_pids(job),'case Job not empty')
            if child:
                if child.thread:close(child.thread)
                if child.process:close(child.process)
            close(job);J.emit('CASE_JOB_HANDLES_CLOSED',run_id=runid)
        tick(True);result=cpu8_audit.audit(ROOT,runid,active,'FORMAL',ROOT/'reports');tick(True);out.append(result);J.emit('CPU8_CASE_AUDITED',case_id=active,run_id=runid,result=result);active=None
    summary=dict(status='CPU8_WORKER_PENDING_DELIVERY',cases=out,unstarted=[],error=None)
except BaseException as e:
    error=repr(e);J.emit('CPU8_STOP',case_id=active,error=error,traceback=traceback.format_exc());summary=dict(status='ENGINEERING_BLOCKED',cases=out,failed_case=active,unstarted=[s['id'] for s in plan['cases'][len(out)+(1 if active else 0):]],error=error)
finally:
    summary.update(begin_ns=begin,end_ns=now(),freeze_sha256=a.freeze_sha256,task_total_ledger='UNKNOWN')
    close(wd);J.emit('HANDLE_CLOSED',handle_kind='watchdog_monitor');J.emit('SUPERVISOR_END',summary=summary);H.end();S.end();J.end();dump_new(RUN/'SUMMARY.json',summary)
print(json.dumps(summary,sort_keys=True),flush=True);sys.exit(0 if error is None else 1)
