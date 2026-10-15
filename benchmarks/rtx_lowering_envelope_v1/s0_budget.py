"""S0 CPU-only Job Object watchdog, conservative complete descendant lifetime cap."""
import argparse,ctypes,json,os,subprocess,sys,time
from ctypes import wintypes as W
from pathlib import Path
ROOT=Path(__file__).parent
def derived_bytes():
    total=0
    for x in ROOT.rglob('*'):
        try:
            if x.is_file():total+=x.stat().st_size
        except FileNotFoundError:pass # CMake/compiler scratch file disappeared during sampling.
    return total
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2);f.write('\n')
class Basic(ctypes.Structure):
    _fields_=[('process_time',ctypes.c_longlong),('job_time',ctypes.c_longlong),('flags',W.DWORD),('min_ws',ctypes.c_size_t),('max_ws',ctypes.c_size_t),('active',W.DWORD),('affinity',ctypes.c_size_t),('priority',W.DWORD),('scheduling',W.DWORD)]
class IO(ctypes.Structure):_fields_=[(x,ctypes.c_ulonglong) for x in ('ro','wo','oo','rb','wb','ob')]
class Extended(ctypes.Structure):_fields_=[('basic',Basic),('io',IO),('process_memory',ctypes.c_size_t),('job_memory',ctypes.c_size_t),('peak_process',ctypes.c_size_t),('peak_job',ctypes.c_size_t)]
class Accounting(ctypes.Structure):
    _fields_=[(x,ctypes.c_longlong) for x in ('user','kernel','period_user','period_kernel')]+[(x,W.DWORD) for x in ('faults','total','active','terminated')]
def main():
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);p.add_argument('--parallel-bound',type=int,choices=(1,8),default=1);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
    ledger=ROOT/'s0_ledger';ledger.mkdir(exist_ok=True);old=list(ledger.glob('*-START.json'))
    for f in old:assert f.with_name(f.name.replace('-START','-EXIT')).exists(),'unresolved child'
    spent=sum(json.loads(f.read_bytes())['charged_child_seconds_upper_bound'] for f in ledger.glob('*-EXIT.json'));assert spent<3600
    lock=ROOT/'S0_JOB.lock';save(lock,dict(pid=os.getpid(),label=a.label));prefix=f'{len(old):03d}-{a.label}'
    save(ledger/(prefix+'-START.json'),dict(command=a.command,epoch=time.time(),parallel_process_bound=a.parallel_bound,prior_charged_seconds=spent))
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateJobObjectW.argtypes=[ctypes.c_void_p,W.LPCWSTR];k.CreateJobObjectW.restype=W.HANDLE
    k.SetInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD];k.AssignProcessToJobObject.argtypes=[W.HANDLE,W.HANDLE]
    k.QueryInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD,ctypes.c_void_p];k.CloseHandle.argtypes=[W.HANDLE]
    job=k.CreateJobObjectW(None,None);assert job
    info=Extended();info.basic.flags=0x2000|8|0x100;info.basic.active=a.parallel_bound;info.process_memory=8*1024**3
    assert k.SetInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info))
    begin=time.perf_counter();child=None;code=-1;error=None;reason=None;ac=Accounting()
    try:
        with (ledger/(prefix+'.stdout.log')).open('xb') as out,(ledger/(prefix+'.stderr.log')).open('xb') as err:
            child=subprocess.Popen(a.command,cwd=ROOT,stdout=out,stderr=err,creationflags=0x08000000|4)
            assert k.AssignProcessToJobObject(job,int(child._handle)),ctypes.get_last_error()
            save(ledger/(prefix+'-PID.json'),dict(pid=child.pid,epoch=time.time(),suspended_assigned_before_resume=True))
            resume=ctypes.WinDLL('ntdll').NtResumeProcess;resume.argtypes=[W.HANDLE];assert resume(int(child._handle))==0
            while child.poll() is None:
                elapsed=time.perf_counter()-begin
                if spent+elapsed*a.parallel_bound>=3600:reason='S0_CHILD_LIFETIME_CAP'
                if derived_bytes()>=1024**3:reason='S0_DERIVED_CAP'
                if reason:k.CloseHandle(job);job=None;break
                time.sleep(.1)
            code=child.wait(timeout=10)
        if job:
            assert k.QueryInformationJobObject(job,1,ctypes.byref(ac),ctypes.sizeof(ac),None)
            assert k.QueryInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info),None)
    except BaseException as exc:
        error=repr(exc)
        if job:k.CloseHandle(job);job=None
        if child and child.poll() is None:child.kill();child.wait()
    finally:
        elapsed=time.perf_counter()-begin
        receipt=dict(seconds=elapsed,charged_child_seconds_upper_bound=elapsed*a.parallel_bound,exit_code=code,error=error,stop_reason=reason,
            job_total_processes=ac.total,job_cpu_user_seconds=ac.user/1e7,job_cpu_kernel_seconds=ac.kernel/1e7,peak_process_commit_bytes=info.peak_process,
            job_active_process_limit=a.parallel_bound,lifetime_accounting='conservative bound=max simultaneous assigned processes times whole driver wall lifetime; descendants constrained by Windows Job Object',new_GPU_model_operator_device_queries=0)
        save(ledger/(prefix+'-EXIT.json'),receipt)
        if job:k.CloseHandle(job)
        lock.unlink()
    print(json.dumps(receipt));sys.exit(0 if code==0 and not error and not reason else 1)
if __name__=='__main__':main()
