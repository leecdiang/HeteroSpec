"""One owned child at a time; Windows Job Object and bounded raw streams.

No GPU or device-query API is imported or executed by this module. Actual GPU
commands can only be supplied by the separately gated stage controller.
"""
import ctypes,os,subprocess,threading,time
from ctypes import wintypes as W
from pathlib import Path
from common import save
from cpu_job import Extended,Accounting
def process_commit():
    class Counters(ctypes.Structure):
        _fields_=[('cb',W.DWORD),('faults',W.DWORD)]+[(n,ctypes.c_size_t) for n in ('peak_ws','ws','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile','private')]
    c=Counters();c.cb=ctypes.sizeof(c);ps=ctypes.WinDLL('psapi');ps.GetProcessMemoryInfo.argtypes=[W.HANDLE,ctypes.c_void_p,W.DWORD]
    assert ps.GetProcessMemoryInfo(W.HANDLE(-1),ctypes.byref(c),ctypes.sizeof(c));return c.private
class Child:
    def __init__(self):
        self.k=ctypes.WinDLL('kernel32',use_last_error=True);k=self.k
        k.CreateJobObjectW.argtypes=[ctypes.c_void_p,W.LPCWSTR];k.CreateJobObjectW.restype=W.HANDLE
        k.SetInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD]
        k.AssignProcessToJobObject.argtypes=[W.HANDLE,W.HANDLE];k.CloseHandle.argtypes=[W.HANDLE]
        k.QueryInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD,ctypes.c_void_p]
        k.TerminateJobObject.argtypes=[W.HANDLE,W.UINT];self.job=None;self.active=None
    def terminate(self):
        if self.job:self.k.TerminateJobObject(self.job,70)
        if self.active and self.active.poll() is None:self.active.kill()
    def run(self,command,prefix,timeout,env,memory,guard=lambda:None,log_cap=32768):
        prefix=Path(prefix);prefix.parent.mkdir(parents=True,exist_ok=True)
        k=self.k;job=k.CreateJobObjectW(None,None);assert job;self.job=job
        info=Extended();info.basic.flags=0x2000|8|0x100|0x200;info.basic.active=1;info.process_memory=memory;info.job_memory=memory
        assert k.SetInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info))
        start=time.perf_counter();p=None;code=None;error=None;threads=[];overflow=threading.Event();ac=Accounting()
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
            save(prefix.with_suffix('.PROCESS.json'),dict(pid=p.pid,command=command,epoch=time.time(),suspended_before_job_assignment=True,active_process_limit=1,commit_limit_bytes=memory))
            assert k.AssignProcessToJobObject(job,int(p._handle)),'assign owned child job'
            for pipe,suffix in ((p.stdout,'.stdout'),(p.stderr,'.stderr')):
                t=threading.Thread(target=consume,args=(pipe,prefix.with_suffix(suffix)),daemon=True);t.start();threads.append(t)
            resume=ctypes.WinDLL('ntdll').NtResumeProcess;resume.argtypes=[W.HANDLE];assert resume(int(p._handle))==0
            while p.poll() is None:
                guard();assert not overflow.is_set(),'child log overflow'
                assert time.perf_counter()-start<timeout,'owned child deadline'
                time.sleep(.05)
            code=p.wait()
            for t in threads:t.join(3);assert not t.is_alive(),'log completion deadline'
            assert not overflow.is_set(),'child log overflow'
            assert k.QueryInformationJobObject(job,1,ctypes.byref(ac),ctypes.sizeof(ac),None)
            assert k.QueryInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info),None)
            assert ac.total==1,'unexpected descendant/extra process; terminal accounting failure'
            assert code==0,'owned child failed; no retry'
        except BaseException as exc:
            error=repr(exc);self.terminate()
            if p:code=p.wait(timeout=10)
            raise
        finally:
            elapsed=time.perf_counter()-start
            if self.active and self.active.poll() is None:self.terminate();self.active.wait(timeout=10)
            for t in threads:t.join(3)
            save(prefix.with_suffix('.LIFETIME.json'),dict(pid=p.pid if p else None,seconds=elapsed,exit_code=code,error=error,timeout_seconds=timeout,
                peak_process_commit_bytes=info.peak_process,peak_job_commit_bytes=info.peak_job,job_total_processes=ac.total,
                monitor='Job Object commit/active-process constraints; elapsed/output polling requested50ms, actual max sampling gaps not certified'))
            if self.job:k.CloseHandle(self.job)
            self.job=None;self.active=None
