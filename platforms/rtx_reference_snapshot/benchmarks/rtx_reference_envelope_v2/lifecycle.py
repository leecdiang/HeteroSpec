"""One owned child at a time; Windows Job Object and bounded raw streams.

No GPU or device-query API is imported or executed by this module. Actual GPU
commands can only be supplied by the separately gated stage controller.
"""
import ctypes,os,subprocess,threading,time
from ctypes import wintypes as W
from pathlib import Path
from common import save,sha
from cpu_job import Extended,Accounting
def process_commit():
    class Counters(ctypes.Structure):
        _fields_=[('cb',W.DWORD),('faults',W.DWORD)]+[(n,ctypes.c_size_t) for n in ('peak_ws','ws','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile','private')]
    c=Counters();c.cb=ctypes.sizeof(c);ps=ctypes.WinDLL('psapi');ps.GetProcessMemoryInfo.argtypes=[W.HANDLE,ctypes.c_void_p,W.DWORD]
    assert ps.GetProcessMemoryInfo(W.HANDLE(-1),ctypes.byref(c),ctypes.sizeof(c));return c.private
class Child:
    def __init__(self,helper):
        self.k=ctypes.WinDLL('kernel32',use_last_error=True);k=self.k
        k.CreateJobObjectW.argtypes=[ctypes.c_void_p,W.LPCWSTR];k.CreateJobObjectW.restype=W.HANDLE
        k.SetInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD]
        k.AssignProcessToJobObject.argtypes=[W.HANDLE,W.HANDLE];k.CloseHandle.argtypes=[W.HANDLE]
        k.QueryInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD,ctypes.c_void_p]
        k.TerminateJobObject.argtypes=[W.HANDLE,W.UINT]
        k.CreateIoCompletionPort.argtypes=[W.HANDLE,W.HANDLE,ctypes.c_size_t,W.DWORD];k.CreateIoCompletionPort.restype=W.HANDLE
        k.GetQueuedCompletionStatus.argtypes=[W.HANDLE,ctypes.POINTER(W.DWORD),ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_void_p),W.DWORD]
        k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE;k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,ctypes.POINTER(W.DWORD)]
        k.GetProcessTimes.argtypes=[W.HANDLE,ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME)]
        self.job=None;self.active=None;self.helper=helper
        assert sha(helper['path'])==helper['sha256']
    def terminate(self):
        if self.job:self.k.TerminateJobObject(self.job,70)
        if self.active and self.active.poll() is None:self.active.kill()
    def run(self,command,prefix,timeout,env,memory,guard=lambda:None,log_cap=32768,on_start=lambda pid:None):
        prefix=Path(prefix);prefix.parent.mkdir(parents=True,exist_ok=True)
        k=self.k;job=k.CreateJobObjectW(None,None);assert job;self.job=job
        info=Extended();info.basic.flags=0x2000|8|0x100|0x200;info.basic.active=2;info.process_memory=memory;info.job_memory=memory
        assert k.SetInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info))
        class Link(ctypes.Structure):_fields_=[('key',ctypes.c_void_p),('port',W.HANDLE)]
        port=k.CreateIoCompletionPort(W.HANDLE(-1),None,0,1);assert port
        link=Link(113,port);assert k.SetInformationJobObject(job,7,ctypes.byref(link),ctypes.sizeof(link))
        start=time.perf_counter();p=None;code=None;error=None;creation=None;threads=[];overflow=threading.Event();ac=Accounting()
        events=[];event_errors=[];event_stop=threading.Event();job_empty=threading.Event()
        def process_events():
            try:
                while not event_stop.is_set():
                    message=W.DWORD();key=ctypes.c_size_t();pid=ctypes.c_void_p()
                    if not k.GetQueuedCompletionStatus(port,ctypes.byref(message),ctypes.byref(key),ctypes.byref(pid),25):continue
                    event=dict(message=message.value,pid=pid.value,key=key.value)
                    if message.value==6:
                        h=k.OpenProcess(0x1000,False,pid.value);assert h,'new assigned process identity unavailable'
                        try:
                            b=ctypes.create_unicode_buffer(32768);n=W.DWORD(len(b));assert k.QueryFullProcessImageNameW(h,0,b,ctypes.byref(n))
                            event['image']=b.value
                        finally:k.CloseHandle(h)
                        if pid.value!=p.pid:
                            assert str(Path(event['image']).resolve()).lower()==str(Path(self.helper['path']).resolve()).lower(),'unexpected owned descendant'
                            assert sha(event['image'])==self.helper['sha256'],'console helper identity drift'
                    events.append(event)
                    if message.value==4:job_empty.set()
            except BaseException as exc:event_errors.append(repr(exc))
        def consume(pipe,destination):
            total=0
            with destination.open('xb') as out:
                while True:
                    block=pipe.read(4096)
                    if not block:break
                    remaining=max(0,log_cap-total);out.write(block[:remaining]);total+=len(block)
                    if total>log_cap:
                        save(destination.with_suffix(destination.suffix+'.OVERFLOW.json'),dict(reason='hard stream byte ceiling',received_at_least=total,retained=log_cap,no_retry=True));overflow.set();break
            pipe.close()
        try:
            p=subprocess.Popen(command,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000|4);self.active=p
            created=W.FILETIME();exited=W.FILETIME();kernel=W.FILETIME();user=W.FILETIME();assert k.GetProcessTimes(int(p._handle),ctypes.byref(created),ctypes.byref(exited),ctypes.byref(kernel),ctypes.byref(user))
            creation=(created.dwHighDateTime<<32)|created.dwLowDateTime
            save(prefix.with_suffix('.PROCESS.json'),dict(pid=p.pid,creation_filetime_100ns=creation,command=command,epoch=time.time(),suspended_before_job_assignment=True,creation_flags=0x08000000|4,active_process_limit=2,commit_limit_bytes=memory,console_helper_cap=1))
            on_start(p.pid)
            listener=threading.Thread(target=process_events,daemon=True);listener.start()
            assert k.AssignProcessToJobObject(job,int(p._handle)),'assign owned child job'
            for pipe,suffix in ((p.stdout,'.stdout'),(p.stderr,'.stderr')):
                t=threading.Thread(target=consume,args=(pipe,prefix.with_suffix(suffix)),daemon=True);t.start();threads.append(t)
            resume=ctypes.WinDLL('ntdll').NtResumeProcess;resume.argtypes=[W.HANDLE];assert resume(int(p._handle))==0
            while p.poll() is None:
                guard();assert not overflow.is_set(),'child log overflow';assert not event_errors,event_errors
                assert time.perf_counter()-start<timeout,'owned child deadline'
                time.sleep(.05)
            code=p.wait()
            assert job_empty.wait(max(0,timeout-(time.perf_counter()-start))),'owned helper closure deadline'
            assert not event_errors,event_errors
            for t in threads:t.join(3);assert not t.is_alive(),'log completion deadline'
            assert not overflow.is_set(),'child log overflow'
            assert k.QueryInformationJobObject(job,1,ctypes.byref(ac),ctypes.sizeof(ac),None)
            assert k.QueryInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info),None)
            started={e['pid'] for e in events if e['message']==6}
            assert p.pid in started and len(started)<=2 and ac.total==len(started),'owned PID event/counter accounting failure'
            assert code==0,'owned child failed; no retry'
        except BaseException as exc:
            error=repr(exc);self.terminate()
            if p:code=p.wait(timeout=10)
            raise
        finally:
            elapsed=time.perf_counter()-start
            if self.active and self.active.poll() is None:self.terminate();self.active.wait(timeout=10)
            for t in threads:t.join(3)
            event_stop.set()
            if 'listener' in locals():listener.join(1)
            save(prefix.with_suffix('.JOB_EVENTS.json'),dict(events=events,errors=event_errors,registered_PID=p.pid if p else None,console_helper_pin=self.helper,started_unique_PIDs=sorted({e['pid'] for e in events if e['message']==6})))
            save(prefix.with_suffix('.LIFETIME.json'),dict(pid=p.pid if p else None,creation_filetime_100ns=creation,seconds=elapsed,exit_code=code,error=error,timeout_seconds=timeout,
                peak_process_commit_bytes=info.peak_process,peak_job_commit_bytes=info.peak_job,job_total_processes=ac.total,
                monitor='Job Object commit/active-process constraints; elapsed/output polling requested50ms, actual max sampling gaps not certified'))
            if self.job:k.CloseHandle(self.job)
            k.CloseHandle(port)
            self.job=None;self.active=None
