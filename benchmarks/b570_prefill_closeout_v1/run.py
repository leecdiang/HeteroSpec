"""One bounded worker per invocation, with durable accounting and kill-on-close job."""
from pathlib import Path
import argparse, ctypes as c, ctypes.wintypes as w, datetime, json, os, subprocess, sys, time
from prepare import ROOT, read, sha, write

K=c.WinDLL('kernel32',use_last_error=True)
K.CreateJobObjectW.argtypes=[c.c_void_p,w.LPCWSTR];K.CreateJobObjectW.restype=w.HANDLE
K.SetInformationJobObject.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD];K.SetInformationJobObject.restype=w.BOOL
K.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE];K.AssignProcessToJobObject.restype=w.BOOL
K.TerminateJobObject.argtypes=[w.HANDLE,w.UINT];K.TerminateJobObject.restype=w.BOOL
K.CloseHandle.argtypes=[w.HANDLE];K.CloseHandle.restype=w.BOOL

class Basic(c.Structure):
    _fields_=[('process_time',c.c_longlong),('job_time',c.c_longlong),('flags',w.DWORD),
              ('min_ws',c.c_size_t),('max_ws',c.c_size_t),('active',w.DWORD),
              ('affinity',c.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
class IO(c.Structure):
    _fields_=[(x,c.c_ulonglong) for x in ['ro','wo','other','rb','wb','ob']]
class Extended(c.Structure):
    _fields_=[('basic',Basic),('io',IO),('process_mem',c.c_size_t),('job_mem',c.c_size_t),
              ('peak_process',c.c_size_t),('peak_job',c.c_size_t)]
class Memory(c.Structure):
    _fields_=[('length',w.DWORD),('load',w.DWORD)]+[(x,c.c_ulonglong) for x in
             ['total_phys','avail_phys','total_page','avail_page','total_virtual','avail_virtual','avail_extended']]

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def check(test,msg):
    if not test: raise RuntimeError(msg)
def memory():
    m=Memory();m.length=c.sizeof(m);check(K.GlobalMemoryStatusEx(c.byref(m)),'memory query failed');return m.avail_phys

def main():
    a=argparse.ArgumentParser();a.add_argument('step',type=int,choices=range(9));a.add_argument('--freeze',required=True);args=a.parse_args()
    begun=time.monotonic();reg=read(ROOT/'REGISTRATION.json');budget=reg['budget']
    wt=Path(reg['worktree']);head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=wt,text=True).strip()
    check(head==args.freeze,'Execution freeze commit moved')
    check(not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=wt),'Tracked source changes')
    check(reg['status']=='FROZEN_FOR_HOST_REVIEW','Registration incomplete')
    check(sha(ROOT/'REGISTRATION.json')==sha(wt/reg['result_path']/'REGISTRATION.json'),'Registration drift')
    lp=ROOT/'BUDGET_LEDGER.json'
    ledger=read(lp) if lp.exists() else {'uuid':reg['study_uuid'],'sessions':[],'charged_worker_seconds':0.,'status':'READY','worker_starts':0}
    check(len(ledger['sessions'])==args.step and ledger['status'] in ['READY','PROCESS_COMPLETED'],'No retry/resume after incomplete or failed step')
    mode='E0' if args.step==0 else ('E1' if args.step<5 else 'E2');index=0 if args.step==0 else ((args.step-1)%4)
    if args.step>0:
        check(read(ROOT/'E0_AUDIT.json')['status']=='E0_FULL_PASS','Independent E0 gate absent')
    if mode=='E2':check(read(ROOT/'QUALIFICATION_AUDIT.json')['status']=='E1_FULL_PASS','Independent E1 gate absent')
    for row in read(ROOT/'FROZEN_FILES.json'):
        p=Path(row['path']);check(p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'Frozen bytes changed: '+str(p))
    limit={'E0':180,'E1':600,'E2':1200}[mode]
    elapsed=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(reg['owned_start_utc'])).total_seconds()
    check(elapsed+limit+budget['cleanup_seconds']<budget['owned_seconds'],'Owned resource reservation exhausted')
    import shutil
    check(shutil.disk_usage(ROOT).free>reg['minimum_free_storage_bytes'],'Storage pressure')
    check(memory()>reg['minimum_free_host_memory_bytes'],'Host memory pressure')
    procs=subprocess.check_output(['powershell','-NoProfile','-Command',
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(closeout|prefill_submit|formal|draft_cpu|llama.*|spec_bridge)\\.exe$' } | Select-Object ProcessId,Name | ConvertTo-Json -Compress"],text=True).strip()
    check(not procs,'Another model process exists: '+procs)
    dest=ROOT/f'{mode}-{index}';check(not dest.exists(),'Fresh output required')
    rc={'step':args.step,'mode':mode,'index':index,'freeze_commit':head,'started_utc':utc(),
        'deadline_seconds':limit,'status':'STARTING','preflight_seconds':time.monotonic()-begun,
        'minimum_available_host_bytes':memory(),'job_kill_on_close':False,'exit_observed':False}
    exe=ROOT/'build/Release/closeout.exe'
    argv=[str(exe),str(dest)]+[x['path'] for x in read(ROOT/'MODEL_RECHECK.json')]+[str(ROOT/'INPUT_PANEL.json'),mode,str(index),str(ROOT)]
    rc['argv']=argv
    job=K.CreateJobObjectW(None,None);check(job,'CreateJobObject failed')
    info=Extended();info.basic.flags=0x2000|0x100|0x8 # kill-on-close, process memory, active-process limit
    info.basic.active=1;info.process_mem=int(budget['memory_bytes'])
    check(K.SetInformationJobObject(job,9,c.byref(info),c.sizeof(info)),'SetInformationJobObject failed')
    env=os.environ.copy()
    for k in list(env):
        if k.startswith('GGML_VK_PERF_LOGGER') or k.startswith('HS_'):del env[k]
    ledger['status']='STARTING';ledger['sessions'].append(rc);write('BUDGET_LEDGER.json',ledger)
    p=None;start=time.monotonic()
    try:
        with (ROOT/f'{mode}-{index}.stdout.log').open('wb') as out,(ROOT/f'{mode}-{index}.stderr.log').open('wb') as err:
            p=subprocess.Popen(argv,cwd=exe.parent,stdout=out,stderr=err,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            rc.update(pid=p.pid,spawned_utc=utc());ledger['worker_starts']+=1
            check(K.AssignProcessToJobObject(job,w.HANDLE(int(p._handle))),'Could not contain owned native process')
            rc['job_kill_on_close']=True;rc['status']='RUNNING';write(f'{mode}-{index}.PROCESS_RECEIPT.json',rc);write('BUDGET_LEDGER.json',ledger)
            while p.poll() is None:
                check(time.monotonic()-start<limit,'Whole-process safety timeout')
                available=memory();rc['minimum_available_host_bytes']=min(rc['minimum_available_host_bytes'],available)
                check(available>reg['minimum_free_host_memory_bytes'],'Host memory pressure during native request')
                check(shutil.disk_usage(ROOT).free>reg['minimum_free_storage_bytes'],'Storage pressure during native request')
                time.sleep(.5)
            rc.update(exit_observed=True,exit_code=p.returncode,exit_observed_utc=utc())
        n=read(dest/'result.json')
        check(p.returncode==0 and n['status']==mode+'_PASS' and n.get('normal_cleanup_returned') is True,'Native contract failure: '+str(n.get('error',n['status'])))
        rc.update(status='PROCESS_COMPLETED',normal_cleanup_returned=True,capture_complete=True,
                  completed_requests=len(n['requests']))
    except BaseException as error:
        rc.update(status='STOPPED_FIRST_FAILURE',error=str(error))
        if p is not None:
            K.TerminateJobObject(job,2)
            if not rc['job_kill_on_close'] and p.poll() is None:p.kill()
            try:p.wait(timeout=10);rc.update(exit_observed=True,exit_code=p.returncode)
            except subprocess.TimeoutExpired:rc['cleanup_error']='Exit not observed after owned-process termination'
        raise
    finally:
        K.CloseHandle(job)
        rc.update(finished_utc=utc(),charged_seconds=time.monotonic()-start,
                  total_wrapper_seconds=time.monotonic()-begun)
        ledger['charged_worker_seconds']+=rc['charged_seconds'];ledger['status']=rc['status']
        write(f'{mode}-{index}.PROCESS_RECEIPT.json',rc);write('BUDGET_LEDGER.json',ledger)
        print(json.dumps(rc,indent=2))

if __name__=='__main__':main()
