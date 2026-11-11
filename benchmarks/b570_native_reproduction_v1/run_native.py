"""Bounded Windows native worker: suspend, contain, resume, record modules and exit."""
from pathlib import Path
import argparse, ctypes as c, ctypes.wintypes as w, datetime, hashlib, json, os, shutil, subprocess, time

K=c.WinDLL('kernel32',use_last_error=True);P=c.WinDLL('psapi',use_last_error=True);N=c.WinDLL('ntdll')
K.CreateJobObjectW.argtypes=[c.c_void_p,w.LPCWSTR];K.CreateJobObjectW.restype=w.HANDLE
K.SetInformationJobObject.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD];K.SetInformationJobObject.restype=w.BOOL
K.QueryInformationJobObject.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD,c.c_void_p];K.QueryInformationJobObject.restype=w.BOOL
K.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE];K.AssignProcessToJobObject.restype=w.BOOL
K.TerminateJobObject.argtypes=[w.HANDLE,w.UINT];K.TerminateJobObject.restype=w.BOOL
K.CloseHandle.argtypes=[w.HANDLE];K.CloseHandle.restype=w.BOOL
N.NtResumeProcess.argtypes=[w.HANDLE];N.NtResumeProcess.restype=c.c_long
P.EnumProcessModulesEx.argtypes=[w.HANDLE,c.c_void_p,w.DWORD,c.POINTER(w.DWORD),w.DWORD];P.EnumProcessModulesEx.restype=w.BOOL
P.GetModuleFileNameExW.argtypes=[w.HANDLE,w.HMODULE,w.LPWSTR,w.DWORD];P.GetModuleFileNameExW.restype=w.DWORD
class Basic(c.Structure):
    _fields_=[('process_time',c.c_longlong),('job_time',c.c_longlong),('flags',w.DWORD),('min_ws',c.c_size_t),('max_ws',c.c_size_t),('active',w.DWORD),('affinity',c.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
class IO(c.Structure):
    _fields_=[(x,c.c_ulonglong) for x in ['ro','wo','other','rb','wb','ob']]
class Extended(c.Structure):
    _fields_=[('basic',Basic),('io',IO),('process_mem',c.c_size_t),('job_mem',c.c_size_t),('peak_process',c.c_size_t),('peak_job',c.c_size_t)]
class Accounting(c.Structure):
    _fields_=[(x,c.c_longlong) for x in ['user','kernel','period_user','period_kernel']]+[(x,w.DWORD) for x in ['page_faults','total_processes','active_processes','terminated_processes']]
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,j):Path(p).write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8')
def check(ok,msg):
    if not ok:raise RuntimeError(msg)
def modules(handle):
    buf=(w.HMODULE*2048)();needed=w.DWORD();out=set()
    if P.EnumProcessModulesEx(handle,buf,c.sizeof(buf),c.byref(needed),3):
        for module in buf[:min(2048,needed.value//c.sizeof(w.HMODULE))]:
            text=c.create_unicode_buffer(32768)
            if P.GetModuleFileNameExW(handle,module,text,len(text)):out.add(text.value)
    return out
def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--capture',type=Path);p.add_argument('--limit',type=int,default=240);p.add_argument('argv',nargs=argparse.REMAINDER);a=p.parse_args()
    check(not a.receipt.exists(),'Existing receipt');check(a.argv,'Missing native command');check(0<a.limit<=240,'Native time bound')
    check(not a.capture or not a.capture.exists(),'Existing fixture capture')
    m=read(a.manifest)
    for row in m['files']:
        f=Path(row['path']);check(f.stat().st_size==row['bytes'] and sha(f)==row['sha256'],'Frozen file changed: '+str(f))
    check(shutil.disk_usage(a.receipt.parent).free>10*1024**3,'Less than 10 GiB free')
    env=os.environ.copy()
    for key in list(env):
        if key.startswith('HS_') or key.startswith('GGML_VK_PERF_LOGGER'):del env[key]
    if a.capture:env['HS_STAGE_CAPTURE']=str(a.capture.resolve())
    exe=Path(a.argv[0]).resolve();env['PATH']=str(exe.parent)+os.pathsep+os.environ.get('SystemRoot','C:/Windows')+'/System32'
    rc={'status':'pending','started_utc':utc(),'argv':a.argv,'manifest_sha256':sha(a.manifest),'limit_seconds':a.limit,'capture':str(a.capture) if a.capture else None,'module_paths':[],'model_performance_claim':False}
    write(a.receipt,rc);job=K.CreateJobObjectW(None,None);check(job,'CreateJobObject failed')
    info=Extended();info.basic.flags=0x2000|0x8;info.basic.active=1
    check(K.SetInformationJobObject(job,9,c.byref(info),c.sizeof(info)),'SetInformationJobObject failed')
    worker=None;seen=set();start=time.monotonic()
    try:
        with a.receipt.with_suffix('.stdout.log').open('xb') as out,a.receipt.with_suffix('.stderr.log').open('xb') as err:
            worker=subprocess.Popen(a.argv,cwd=exe.parent,stdout=out,stderr=err,env=env,creationflags=subprocess.CREATE_NO_WINDOW|0x4)
            handle=w.HANDLE(int(worker._handle));rc['pid']=worker.pid
            check(K.AssignProcessToJobObject(job,handle),'AssignProcessToJobObject failed')
            rc.update(status='running',assigned_before_resume=True,child_process_limit=1)
            write(a.receipt,rc);check(N.NtResumeProcess(handle)==0,'Resume failed')
            while worker.poll() is None:
                seen.update(modules(handle));check(time.monotonic()-start<a.limit,'Native timeout');time.sleep(.1)
            rc.update(exit_code=worker.returncode,exit_observed=True,status='complete' if worker.returncode==0 else 'failed')
        acct=Accounting();check(K.QueryInformationJobObject(job,1,c.byref(acct),c.sizeof(acct),None),'Job accounting failed')
        rc['job_accounting']={key:getattr(acct,key) for key,_ in Accounting._fields_}
        rc['main_process_count']=1
        rc['other_job_processes']=acct.total_processes-1
        rc['other_job_process_identity']='NOT_CAPTURED; cumulative Job count is authoritative, active limit is not a lifetime count'
        check(1<=acct.total_processes<=4 and acct.active_processes==0,'Job total bound or cleanup failure')
    except BaseException as e:
        rc.update(status='failed',error=str(e));K.TerminateJobObject(job,2)
        if worker is not None:
            if worker.poll() is None:worker.kill()
            worker.wait(timeout=10);rc.update(exit_observed=True,exit_code=worker.returncode)
    finally:
        K.CloseHandle(job);rc.update(finished_utc=utc(),charged_seconds=time.monotonic()-start)
        rc['module_paths']=sorted(seen)
        rc['loaded_module_hashes']=[{'path':x,'bytes':Path(x).stat().st_size,'sha256':sha(x)} for x in sorted(seen) if Path(x).is_file()]
        write(a.receipt,rc)
    print(json.dumps({k:rc.get(k) for k in ['status','pid','exit_code','charged_seconds','error','job_accounting']}))
    return 0 if rc['status']=='complete' else 1
if __name__=='__main__':raise SystemExit(main())
