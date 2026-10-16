"""One owned child at a time; Windows Job Object and bounded raw streams.

No GPU or device-query API is imported or executed by this module. Actual GPU
commands can only be supplied by the separately gated stage controller.
"""
import ctypes,os,subprocess,threading,time,uuid,json,hashlib,sys
from monitor_contract import MAX_MONITOR_INTERVAL_NS,encode_sample
from ctypes import wintypes as W
from pathlib import Path
from common import save,sha
from cpu_job import Extended,Accounting
def process_commit():
    class Counters(ctypes.Structure):
        _fields_=[('cb',W.DWORD),('faults',W.DWORD)]+[(n,ctypes.c_size_t) for n in ('peak_ws','ws','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile','private')]
    c=Counters();c.cb=ctypes.sizeof(c);ps=ctypes.WinDLL('psapi');ps.GetProcessMemoryInfo.argtypes=[W.HANDLE,ctypes.c_void_p,W.DWORD]
    assert ps.GetProcessMemoryInfo(W.HANDLE(-1),ctypes.byref(c),ctypes.sizeof(c));return c.private
class StrictChild:
    def __init__(self,helper,contract):
        self.contract=contract
        assert contract["max_monitor_interval_ns"]==MAX_MONITOR_INTERVAL_NS
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
    def run(self,command,prefix,timeout,env,memory,guard=lambda:None,log_cap=32768,on_start=lambda pid:None,cpu_hooks=None):
        hooks=cpu_hooks or {}
        assert not hooks or (self.contract.get('CPU_fixture_only') is True and str(Path(command[0]).resolve()).lower()==str(Path(sys.executable).resolve()).lower()),'test hooks forbidden for GPU/native entry'
        prefix=Path(prefix);prefix.parent.mkdir(parents=True,exist_ok=True)
        k=self.k;job_name='Local\\HeteroSpecMonitor-'+uuid.uuid4().hex;job=k.CreateJobObjectW(None,job_name);assert job;self.job=job
        info=Extended();info.basic.flags=0x2000|8|0x100|0x200;info.basic.active=4;info.process_memory=memory;info.job_memory=memory+128*1024**2
        assert k.SetInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info))
        class Link(ctypes.Structure):_fields_=[('key',ctypes.c_void_p),('port',W.HANDLE)]
        port=k.CreateIoCompletionPort(W.HANDLE(-1),None,0,1);assert port
        link=Link(113,port);assert k.SetInformationJobObject(job,7,ctypes.byref(link),ctypes.sizeof(link))
        start=time.perf_counter();p=None;code=None;error=None;creation=None;threads=[];overflow=threading.Event();ac=Accounting()
        watch=None;watch_pid=None;monitor_stop=threading.Event();monitor_thread=None;resume_ns=None;exit_ns=None;post_start_ns=None;mon_paths={}
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
                        if pid.value not in {p.pid,watch_pid}:
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
            save(prefix.with_suffix('.PROCESS.json'),dict(pid=p.pid,creation_filetime_100ns=creation,command=command,epoch=time.time(),suspended_before_job_assignment=True,creation_flags=0x08000000|4,active_process_limit=4,commit_limit_bytes=memory,console_helper_cap=2,run_id=self.contract['run_id'],execution_id=self.contract['execution_id'],strict_monitor=True))
            on_start(p.pid)
            listener=threading.Thread(target=process_events,daemon=True);listener.start()
            assert k.AssignProcessToJobObject(job,int(p._handle)),'assign owned child job'
            for pipe,suffix in ((p.stdout,'.stdout'),(p.stderr,'.stderr')):
                t=threading.Thread(target=consume,args=(pipe,prefix.with_suffix(suffix)),daemon=True);t.start();threads.append(t)
            armed=time.monotonic_ns();token=uuid.uuid4().hex
            mon_paths={key:str(prefix.with_suffix('.'+suffix)) for key,suffix in [('samples_path','MONITOR_SAMPLES.jsonl'),('ready_path','MONITOR_READY.json'),('result_path','MONITOR.json'),('monitor_error_path','MONITOR_ERROR.json'),('resume_path','RESUME.json')]}
            config=dict(mon_paths,CPU_fixture_only=self.contract.get('CPU_fixture_only',False),test_hooks_enabled=bool(hooks),run_id=self.contract['run_id'],execution_id=self.contract['execution_id'],token=token,target_pid=p.pid,target_creation_filetime=creation,job_name=job_name,armed_ns=armed,native_timeout_ns=int(timeout*1e9),max_interval_ns=MAX_MONITOR_INTERVAL_NS,config_token_sha256=hashlib.sha256(token.encode()).hexdigest())
            config_path=prefix.with_suffix('.MONITOR_CONFIG.json');save(config_path,config)
            def alive():return k.WaitForSingleObject(int(p._handle),0)==258
            def collect():
                previous=config['config_token_sha256'];sequence=0
                try:
                    while not monitor_stop.is_set() and alive():
                        if hooks.get('stall_after')==sequence:time.sleep(hooks.get('stall_seconds',1.2))
                        if hooks.get('crash_after')==sequence:raise RuntimeError('CPU fixture monitor crash')
                        if hooks.get('kill_watchdog_after')==sequence:
                            assert watch is not None;watch.kill()
                        if monitor_stop.is_set() or not alive():break
                        guard()
                        assert not overflow.is_set() and not event_errors,'resource/log/process monitor failure'
                        class Counters(ctypes.Structure):
                            _fields_=[('cb',W.DWORD),('faults',W.DWORD)]+[(n,ctypes.c_size_t) for n in ('peak_ws','ws','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile','private')]
                        counters=Counters();counters.cb=ctypes.sizeof(counters);ps=ctypes.WinDLL('psapi');ps.GetProcessMemoryInfo.argtypes=[W.HANDLE,ctypes.c_void_p,W.DWORD]
                        assert ps.GetProcessMemoryInfo(int(p._handle),ctypes.byref(counters),ctypes.sizeof(counters))
                        assert counters.private<=memory
                        observed=Extended();assert k.QueryInformationJobObject(job,9,ctypes.byref(observed),ctypes.sizeof(observed),None)
                        assert observed.peak_job<=memory+128*1024**2
                        if not alive():break
                        stamp=time.monotonic_ns()
                        row=dict(run_id=config['run_id'],execution_id=config['execution_id'],token=token,target_pid=p.pid,sequence=sequence,monotonic_ns=stamp,target_alive=True,resource_valid=True,private_commit_bytes=counters.private,job_peak_commit_bytes=observed.peak_job)
                        line,previous=encode_sample(row,previous)
                        assert sequence<1500 and len(line)<2048
                        with Path(mon_paths['samples_path']).open('ab') as stream:stream.write(line);stream.flush();os.fsync(stream.fileno())
                        sequence+=1
                        if monitor_stop.wait(.05):break
                except BaseException as e:
                    if alive() and not Path(mon_paths['monitor_error_path']).exists():save(mon_paths['monitor_error_path'],dict(error=repr(e),monotonic_ns=time.monotonic_ns()))
            k.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD]
            monitor_thread=threading.Thread(target=collect,daemon=True);monitor_thread.start()
            worker=Path(self.contract['watchdog_path']);assert sha(worker)==self.contract['watchdog_sha256']
            py=self.contract['python'];assert sha(py['path'])==py['sha256']
            watch_command=[py['path'],'-B',str(worker),'--config',str(config_path)]
            watch=subprocess.Popen(watch_command,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000|4);watch_pid=watch.pid
            save(prefix.with_suffix('.WATCHDOG_PROCESS.json'),dict(pid=watch_pid,command=watch_command,script_sha256=sha(worker),python_sha256=py['sha256'],run_id=config['run_id'],execution_id=config['execution_id']))
            assert k.AssignProcessToJobObject(job,int(watch._handle))
            for pipe,suffix in ((watch.stdout,'.WATCHDOG.stdout'),(watch.stderr,'.WATCHDOG.stderr')):
                thread=threading.Thread(target=consume,args=(pipe,prefix.with_suffix(suffix)),daemon=True);thread.start();threads.append(thread)
            resume=ctypes.WinDLL('ntdll').NtResumeProcess;resume.argtypes=[W.HANDLE];assert resume(int(watch._handle))==0
            while not Path(mon_paths['ready_path']).exists() or not Path(mon_paths['samples_path']).exists():
                assert time.monotonic_ns()-armed<5_000_000_000,'monitor/watchdog startup deadline'
                assert watch.poll() is None,'watchdog died before admission'
                if Path(mon_paths['result_path']).exists():assert json.loads(Path(mon_paths['result_path']).read_bytes())['watchdog_decision']=='PASS'
                guard();time.sleep(.01)
            resume_ns=time.monotonic_ns();save(mon_paths['resume_path'],dict(monotonic_ns=resume_ns,run_id=config['run_id'],execution_id=config['execution_id']))
            assert resume(int(p._handle))==0
            while p.poll() is None:
                guard();assert not overflow.is_set(),'child log overflow';assert not event_errors,event_errors
                assert time.monotonic_ns()-resume_ns<int(timeout*1e9),'native running deadline'
                if Path(mon_paths['result_path']).exists():assert json.loads(Path(mon_paths['result_path']).read_bytes())['watchdog_decision']=='PASS','independent watchdog failed'
                assert watch.poll() is None,'watchdog terminated while target alive'
                time.sleep(.05)
            code=p.wait();monitor_stop.set()
            assert job_empty.wait(10),'owned helper closure deadline'
            assert not event_errors,event_errors
            monitor_record=json.loads(Path(mon_paths['result_path']).read_bytes());assert monitor_record['watchdog_decision']=='PASS',monitor_record
            assert watch.wait(timeout=1)==0
            exit_ns=monitor_record['exit_observed_monotonic_ns'];post_start_ns=time.monotonic_ns()
            if hooks.get('post_audit_sleep'):time.sleep(hooks['post_audit_sleep'])
            for t in threads:t.join(3);assert not t.is_alive(),'log completion deadline'
            assert not overflow.is_set(),'child log overflow'
            assert k.QueryInformationJobObject(job,1,ctypes.byref(ac),ctypes.sizeof(ac),None)
            assert k.QueryInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info),None)
            started={e['pid'] for e in events if e['message']==6}
            assert p.pid in started and len(started)<=4 and ac.total==len(started),'owned PID event/counter accounting failure'
            assert code==0,'owned child failed; no retry'
        except BaseException as exc:
            error=repr(exc);self.terminate()
            if p:code=p.wait(timeout=10)
            raise
        finally:
            elapsed=time.perf_counter()-start
            monitor_stop.set()
            if monitor_thread:monitor_thread.join(2)
            if self.active and self.active.poll() is None:self.terminate();self.active.wait(timeout=10)
            for t in threads:t.join(3)
            event_stop.set()
            if 'listener' in locals():listener.join(1)
            save(prefix.with_suffix('.JOB_EVENTS.json'),dict(events=events,errors=event_errors,registered_PID=p.pid if p else None,console_helper_pin=self.helper,started_unique_PIDs=sorted({e['pid'] for e in events if e['message']==6})))
            save(prefix.with_suffix('.LIFETIME.json'),dict(pid=p.pid if p else None,creation_filetime_100ns=creation,seconds=elapsed,exit_code=code,error=error,timeout_seconds=timeout,
                peak_process_commit_bytes=info.peak_process,peak_job_commit_bytes=info.peak_job,job_total_processes=ac.total,
                run_id=self.contract['run_id'],execution_id=self.contract['execution_id'],watchdog_pid=watch_pid,
                native_resume_monotonic_ns=resume_ns,native_exit_observed_monotonic_ns=exit_ns,
                native_runtime_seconds=(exit_ns-resume_ns)/1e9 if exit_ns is not None and resume_ns is not None else None,
                post_exit_audit_seconds=(time.monotonic_ns()-exit_ns)/1e9 if exit_ns is not None else None,
                monitor='Independent process;actual monotonic sample intervals and terminal coverage<=1000000000ns;no exit sample fabrication'))
            if self.job:k.CloseHandle(self.job)
            k.CloseHandle(port)
            self.job=None;self.active=None
