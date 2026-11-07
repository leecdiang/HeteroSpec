"""Production native lifecycle, two independent observer streams, external logs."""
import ctypes
from ctypes import wintypes as W
import json
import msvcrt
import os
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import time
from common import need, Journal, write_new, inventory, MAX_GAP
from os_process import Target
from timing import Coverage
from storage import Lease

def available_ram():
    class M(ctypes.Structure):
        _fields_=[('length',W.DWORD),('load',W.DWORD)]+[(n,ctypes.c_ulonglong) for n in ('total','available','page','avail_page','virtual','avail_virtual','extended')]
    m=M();m.length=ctypes.sizeof(m)
    need(ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)),'memory API failed')
    return m.available

def pipe_capacity(stream):
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.GetNamedPipeInfo.argtypes=[W.HANDLE]+[ctypes.POINTER(W.DWORD)]*4
    a,b,c,d=(W.DWORD() for _ in range(4))
    need(k.GetNamedPipeInfo(msvcrt.get_osfhandle(stream.fileno()),ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d)),'pipe capacity unavailable')
    need(0<b.value+c.value<=65536,'unexpected pipe capacity')
    return b.value+c.value

class Observer:
    def __init__(self,process,begin,active,journal,cap_bytes,cap_files,read_resource=None,read_directory=None):
        self.process=process;self.target=Target(process.pid,int(process._handle));self.active=Path(active)
        self.journal=journal;self.cap_bytes=cap_bytes;self.cap_files=cap_files
        self.coverage=Coverage(begin);self.lock=threading.Lock();self.error=None;self.exit_ns=None;self.exit_code=None
        self.finish=threading.Event();self.threads=[]
        self.resource_reader=read_resource or self.resource;self.directory_reader=read_directory or self.directory
        for stream in ('resource','directory'):
            t=threading.Thread(target=self.run,args=(stream,),name='EXTERNAL_'+stream,daemon=True)
            self.threads.append(t);t.start()
    def observe_exit(self):
        with self.lock:
            code=self.process.poll()
            if code is not None and self.exit_ns is None:
                self.exit_ns=time.monotonic_ns();self.exit_code=code
                self.journal.emit('EXIT_OBSERVED',exit_observed_ns=self.exit_ns,returncode=code,PID=self.process.pid)
            return self.exit_ns
    def resource(self):
        rss=self.target.rss()
        value=dict(RSS=rss,host_available=available_ram(),disk_free=shutil.disk_usage(str(self.active)).free)
        controls=[]
        for pid in (os.getpid(),os.getppid()):
            target=Target(pid)
            try:controls.append(dict(PID=pid,RSS=target.rss()))
            finally:target.close()
        value['control_RSS']=controls
        need(rss<=8*1024**3 and all(x['RSS']<=8*1024**3 for x in controls),'RSS budget')
        need(value['host_available']>=2*1024**3 and value['disk_free']>=20*1024**3,'RAM/disk budget')
        return value
    def directory(self):
        value=inventory(self.active)
        need(value['bytes']<=self.cap_bytes and value['files']<=self.cap_files,'active output reservation exceeded')
        return dict(**value,historical_files_scanned=0)
    def run(self,stream):
        try:
            reader=self.resource_reader if stream=='resource' else self.directory_reader
            while not self.finish.is_set():
                if self.observe_exit() is not None:break
                begin=time.monotonic_ns();event=dict(event='READ_BEGIN',stream=stream,begin_ns=begin)
                with self.lock:self.coverage.event(event)
                self.journal.emit('READ_BEGIN',stream=stream,begin_ns=begin)
                try:
                    value=reader();end=time.monotonic_ns()
                except BaseException as e:
                    end=time.monotonic_ns();exited=self.observe_exit()
                    if exited is not None:
                        event=dict(event='READ_DISCARDED',stream=stream,begin_ns=begin,end_ns=end,reason='exit/read race',error=str(e))
                    else:
                        event=dict(event='READ_ERROR',stream=stream,begin_ns=begin,end_ns=end,error=str(e))
                    self.journal.emit(event['event'],**{k:v for k,v in event.items() if k!='event'})
                    with self.lock:self.coverage.event(event,exited)
                    if exited is not None:break
                    raise
                exited=self.observe_exit()
                event=dict(event='READ_END' if exited is None else 'READ_DISCARDED',stream=stream,begin_ns=begin,end_ns=end)
                if exited is None:event['values']=value
                else:event['reason']='exit/read race; no fabricated resource values'
                self.journal.emit(event['event'],**{k:v for k,v in event.items() if k!='event'})
                with self.lock:self.coverage.event(event,exited)
                self.finish.wait(.1)
        except BaseException as e:
            self.error=str(e)
            try:self.journal.emit('OBSERVER_ERROR',stream=stream,error=self.error)
            except BaseException:pass
    def check(self):
        need(self.error is None,'observer failure: '+str(self.error))
        with self.lock:
            if self.exit_ns is None:self.coverage.live(time.monotonic_ns())
    def close(self):
        self.finish.set()
        for t in self.threads:t.join(2)
        need(not any(t.is_alive() for t in self.threads),'observer cleanup failure')
        need(self.error is None,'observer rejected: '+str(self.error))
        with self.lock:return self.coverage.terminal(self.exit_ns)

def supervise(command,active,roots,journal_dir,timeout,on_event,cap_bytes=256*1024**2,cap_files=4096,
              read_resource=None,read_directory=None,post_audit=None,log_soft=16*1024**2):
    """No CPU-purpose exception in the storage/coverage policy. Caller owns fixed wire."""
    active=Path(active);journal_dir=Path(journal_dir)
    active.mkdir(parents=True,exist_ok=False);journal_dir.mkdir(parents=True,exist_ok=False)
    need(all(Path(p).resolve()!=journal_dir.resolve() and Path(p).resolve() not in journal_dir.resolve().parents for p in roots),'journals must be outside every protected root')
    lifecycle=Journal(journal_dir/'LIFECYCLE.jsonl');monitor=Journal(journal_dir/'MONITOR.jsonl')
    proc=observer=lease=None;error=None;values=None;threads=[];hold=threading.Event();drain=threading.Event();pump_error=[];messages=queue.Queue();counts={};caps={};post_begin=post_end=None
    started=time.monotonic_ns();spawn_ns=exit_ns=None;times=None;boundaries=None
    def pump(name,stream):
        count=0;pending=b''
        try:
            with (journal_dir/(name+'.log')).open('xb') as f:
                while True:
                    if hold.is_set():need(drain.wait(30),'log overflow cleanup did not drain')
                    data=os.read(stream.fileno(),4096)
                    if not data:break
                    need(count+len(data)<=log_soft+131072,'log hard reservation exceeded')
                    f.write(data);f.flush();count+=len(data);counts[name]=count
                    if count>log_soft:hold.set()
                    if name=='stdout':
                        pending+=data
                        while b'\n' in pending:
                            line,pending=pending.split(b'\n',1)
                            messages.put(line)
                need(not pending,'truncated stdout record')
                f.flush();os.fsync(f.fileno())
        except BaseException as e:pump_error.append(str(e));hold.set()
    try:
        lease=Lease(roots,active,journal_dir)
        lifecycle.emit('LEASE_ADMITTED',baseline=lease.baseline,prelaunch_begin_ns=lease.started,prelaunch_ready_ns=lease.ready)
        spawn_ns=time.monotonic_ns();proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        target=Target(proc.pid,int(proc._handle));times=target.times()
        lifecycle.emit('SPAWN_RETURNED',PID=proc.pid,spawn_begin_ns=spawn_ns,creation_FILETIME=times['creation_FILETIME'],command=command)
        observer=Observer(proc,spawn_ns,active,monitor,cap_bytes,cap_files,read_resource,read_directory)
        for name,stream in [('stdout',proc.stdout),('stderr',proc.stderr)]:
            caps[name]=pipe_capacity(stream);counts[name]=0
            t=threading.Thread(target=pump,args=(name,stream),name='BOUNDED_'+name,daemon=True);threads.append(t);t.start()
        lifecycle.emit('PIPE_CAPACITY',capacities=caps,soft_bytes=log_soft,hard_bytes=log_soft+131072)
        while True:
            exit_ns=observer.observe_exit() # Before any parse, audit or hash.
            lease.check();observer.check()
            need(not hold.is_set() and not pump_error,'bounded log capture failed/exceeded: '+str(pump_error))
            need(time.monotonic_ns()-spawn_ns<=timeout*10**9,'native timeout')
            while True:
                try:line=messages.get_nowait()
                except queue.Empty:break
                if line:
                    item=json.loads(line.decode('utf-8'));response=on_event(item,proc)
                    if response is not None:
                        need(exit_ns is None,'child exited before registered input send')
                        lease.check();observer.check()
                        need(observer.observe_exit() is None,'child exited during input gate')
                        data=response if isinstance(response,bytes) else (json.dumps(response,separators=(',',':'))+'\n').encode('utf-8')
                        proc.stdin.write(data);proc.stdin.flush();lifecycle.emit('INPUT_SENT',bytes=len(data),sha256=__import__('hashlib').sha256(data).hexdigest())
            if exit_ns is not None:break
            time.sleep(.01)
        need(proc.returncode==0,'native abnormal exit '+str(proc.returncode))
    except BaseException as e:error=str(e)
    finally:
        if proc is not None:
            if proc.poll() is None:
                lifecycle.emit('TERMINATION_REQUESTED',error=error);proc.terminate()
                try:proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    proc.kill();proc.wait(timeout=5);error=error or 'cleanup exceeded30s'
            if observer is not None:
                exit_ns=observer.observe_exit()
                try:boundaries=observer.close()
                except BaseException as e:error=error or str(e)
            times=Target(proc.pid,int(proc._handle)).times();drain.set()
            for t in threads:
                t.join(5)
                if t.is_alive():error=error or 'log reader cleanup failed'
            if pump_error:error=error or '; '.join(pump_error)
            for stream in (proc.stdin,proc.stdout,proc.stderr):
                try:stream.close()
                except OSError as e:error=error or str(e)
        if lease is not None:
            try:lease.close()
            except BaseException as e:error=error or str(e)
        if error is None and post_audit is not None:
            post_begin=time.monotonic_ns();lifecycle.emit('POST_EXIT_AUDIT_BEGIN',ns=post_begin)
            try:values=post_audit()
            except BaseException as e:error=str(e)
            post_end=time.monotonic_ns();lifecycle.emit('POST_EXIT_AUDIT_END',ns=post_end,error=error)
        result=dict(status='ADMITTED' if error is None else 'FAILED',error=error,PID=proc.pid if proc else None,
            spawn_begin_ns=spawn_ns,exit_observed_ns=exit_ns,process_times=times,
            native_observed_seconds=(exit_ns-spawn_ns)/1e9 if spawn_ns is not None and exit_ns is not None else None,
            coverage=boundaries,post_exit_audit_begin_ns=post_begin,post_exit_audit_end_ns=post_end,
            post_exit_audit_seconds=(post_end-post_begin)/1e9 if post_end else None,
            complete_slot_seconds=(time.monotonic_ns()-started)/1e9,log_bytes=counts,pipe_capacities=caps,post_audit=values)
        lifecycle.emit('LIFECYCLE_COMMITTED',result=result);monitor.close();lifecycle.close()
        write_new(journal_dir/'LIFECYCLE.json',result)
    return result
