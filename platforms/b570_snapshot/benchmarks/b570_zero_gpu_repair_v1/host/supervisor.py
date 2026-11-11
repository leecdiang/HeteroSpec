"""CPU production supervision, real pipes, strict independent live observers."""
import ctypes as C,json,os,queue,shutil,subprocess,sys,threading
from ctypes import wintypes as W
from pathlib import Path
from common import HERE,Journal,Reject,now,need,inventory,sha,file_id,write_new,MAX_GAP
from os_process import Target
from identity import modules

def available_ram():
    class M(C.Structure):
        _fields_=[('length',W.DWORD),('load',W.DWORD)]+[(n,C.c_ulonglong) for n in ('total','available','page','avail_page','virtual','avail_virtual','extended')]
    m=M();m.length=C.sizeof(m);need(C.windll.kernel32.GlobalMemoryStatusEx(C.byref(m)),'RAM read failed');return m.available

class Observers:
    def __init__(self,session,proc,slot,launch,work):
        self.s=session;self.proc=proc;self.slot=slot;self.launch=launch;self.work=work
        self.target=Target(proc.pid,int(proc._handle));self.stop=threading.Event();self.release=threading.Event();self.lock=threading.RLock()
        self.last={x:None for x in ('resource','directory')};self.pending={x:None for x in self.last}
        self.exit_ns=None;self.threads=[];self.injected=False
        for name in self.last:
            t=threading.Thread(target=self.run,args=(name,),name='CPU_'+name,daemon=True);self.threads.append(t);t.start()
    def exited(self):
        with self.lock:
            code=self.proc.poll()
            if code is not None and self.exit_ns is None:
                self.exit_ns=now();self.s.log.emit('EXIT_OBSERVED',slot=self.slot,pid_child=self.proc.pid,exit_observed_ns=self.exit_ns,exit_code=code)
            return self.exit_ns
    def read(self,stream):
        mode=self.s.case['id'];active=Path(self.s.registry[self.slot]['path'])
        if self.work.is_set() and not self.injected:
            if stream=='resource' and mode=='resource_read_failure':
                self.injected=True;self.s.trigger_begin('resource',mode)
                # The real resource API is invoked with an actually closed handle.
                t=Target(self.proc.pid);t.close()
                try:t.rss()
                except BaseException as e:
                    self.s.trigger_end('resource',dict(closed_handle=True,api='K32GetProcessMemoryInfo',error=str(e)));raise
                raise RuntimeError('closed resource handle unexpectedly succeeded')
            if stream=='directory' and mode=='directory_read_timeout':
                self.injected=True;self.s.trigger_begin('directory',mode)
                self.s.log.emit('DIRECTORY_STALL_CONTROL_POINT',slot=self.slot,reader='inventory')
                self.release.wait(3)
                self.s.trigger_end('directory',dict(released=True))
        if stream=='directory':
            v=inventory(active);need(v['files']<=32 and v['bytes']<=2*1024**2,'active output cap')
            return dict(**v,historical_files_scanned=0)
        rss=self.target.rss();ram=available_ram();disk=shutil.disk_usage(str(active)).free
        control=Target(os.getpid())
        try:control_rss=control.rss()
        finally:control.close()
        need(rss<=2*1024**3 and control_rss<=2*1024**3,'RSS budget exceeded')
        need(ram>=2*1024**3 and disk>=10*1024**3,'RAM/disk budget exceeded')
        return dict(RSS=rss,controller_RSS=control_rss,host_available=ram,disk_free=disk)
    def run(self,stream):
        journal=self.s.streams[stream]
        try:
            journal.emit('STREAM_ARMED',slot=self.slot,launch_ns=self.launch)
            while not self.stop.is_set():
                if self.exited() is not None:break
                begin=now()
                with self.lock:self.pending[stream]=begin
                journal.emit('READ_BEGIN',slot=self.slot,begin_ns=begin)
                try:value=self.read(stream);end=now()
                except BaseException as e:
                    end=now();exit_ns=self.exited()
                    journal.emit('READ_DISCARDED' if exit_ns is not None else 'READ_ERROR',slot=self.slot,begin_ns=begin,end_ns=end,error=str(e))
                    with self.lock:self.pending[stream]=None
                    if exit_ns is None:self.s.reject('RESOURCE_READ_REJECTED' if stream=='resource' else 'DIRECTORY_READ_REJECTED',stream,dict(error=str(e),begin_ns=begin,end_ns=end))
                    break
                exit_ns=self.exited()
                if exit_ns is not None:
                    journal.emit('READ_DISCARDED',slot=self.slot,begin_ns=begin,end_ns=end,reason='actual exit/read race; values excluded')
                    with self.lock:self.pending[stream]=None
                    break
                with self.lock:
                    prior=self.last[stream] if self.last[stream] is not None else self.launch
                    journal.emit('READ_END',slot=self.slot,begin_ns=begin,end_ns=end,values=value)
                    self.last[stream]=begin;self.pending[stream]=None
                if max(end-begin,end-prior)>MAX_GAP:self.s.reject('COVERAGE_GAP_REJECTED',stream,dict(begin_ns=begin,end_ns=end,previous_begin_ns=prior))
                self.stop.wait(.1)
        except BaseException as e:
            self.s.reject('JOURNAL_FAILURE_REJECTED',stream,dict(error=str(e),outer_record=True))
        finally:
            try:journal.emit('STREAM_CLOSED',slot=self.slot,terminal_ns=self.exited())
            except BaseException as e:self.s.reject('JOURNAL_FAILURE_REJECTED',stream,dict(error=str(e),outer_record=True))
    def check(self):
        t=now()
        with self.lock:
            for stream,begin in self.last.items():
                anchor=begin if begin is not None else self.launch
                if t-anchor>MAX_GAP:self.s.reject('COVERAGE_GAP_REJECTED',stream,dict(observed_ns=t,anchor_ns=anchor,pending_begin_ns=self.pending[stream]))
    def finish(self):
        self.release.set();self.stop.set()
        for t in self.threads:t.join(3)
        need(not any(t.is_alive() for t in self.threads),'observer cleanup timeout')

def run_slot(s,slot,mode=None,post_delay=0):
    spec=s.case;mode=mode or spec['id'];active=Path(s.registry[slot]['path']);external=s.external/spec['id']/slot
    external.mkdir();producer=external/'PRODUCER.jsonl';cfg=external/'CONFIG.json'
    write_new(cfg,dict(case_id=mode,active=str(active),producer_journal=str(producer)))
    s.transition(slot,'ACTIVE');launch=now();proc=subprocess.Popen([sys.executable,'-B',str(HERE/'cpu_child.py'),str(cfg)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
    target=Target(proc.pid,int(proc._handle));s.log.emit('CHILD_SPAWNED',slot=slot,pid_child=proc.pid,launch_ns=launch,os_times=target.times(),mode=mode)
    work=threading.Event();obs=Observers(s,proc,slot,launch,work);s.current_observer=obs;q=queue.Queue();hold=threading.Event();drain=threading.Event();counts={};tails={};pump_errors=[];threads=[]
    soft=32768 if mode=='log_overflow' else 16777216
    def pump(name,pipe):
        pending=b'';count=0
        try:
            with (external/(name+'.log')).open('xb',buffering=0) as out:
                while True:
                    if hold.is_set():need(drain.wait(5),'pipe drain deadline')
                    b=os.read(pipe.fileno(),4096)
                    if not b:break
                    need(count+len(b)<=soft+131072,'pipe hard reservation exceeded')
                    out.write(b);count+=len(b);counts[name]=count
                    if count>soft:hold.set()
                    if name=='stdout':
                        pending+=b
                        while b'\n' in pending:
                            line,pending=pending.split(b'\n',1);q.put(line)
                os.fsync(out.fileno());tails[name]=pending
        except BaseException as e:pump_errors.append(dict(stream=name,error=str(e)));hold.set()
    for name,pipe in (('stdout',proc.stdout),('stderr',proc.stderr)):
        t=threading.Thread(target=pump,args=(name,pipe),name='PIPE_'+name,daemon=True);threads.append(t);t.start()
    ready=False;go=False;continued=False;complete=False;fault_armed=False;terminated=False
    try:
        deadline=launch+(1_500_000_000 if mode=='child_timeout' else 10_000_000_000)
        while True:
            exit_ns=obs.exited()
            s.engine.check();obs.check()
            if hold.is_set():
                if counts.get('stdout',0)>soft or counts.get('stderr',0)>soft:
                    s.trigger_local('log',dict(stdout=counts.get('stdout',0),stderr=counts.get('stderr',0),soft=soft,hard=soft+131072))
                    s.reject('LOG_LIMIT_REJECTED','log',dict(counts=dict(counts),soft=soft,hard=soft+131072))
                else:s.reject('PIPE_CAPTURE_REJECTED','log',dict(errors=pump_errors))
            if now()>deadline and exit_ns is None:
                s.reject('CHILD_TIMEOUT_REJECTED','child',dict(deadline_ns=deadline,observed_ns=now(),alive=True))
            if s.rejections:break
            for _ in range(256):
                try:line=q.get_nowait()
                except queue.Empty:break
                row=json.loads(line);s.log.emit('CHILD_RECORD',slot=slot,record=row)
                if row['event']=='READY':
                    ready=True
                    actual=modules(proc.pid);expected=sha(sys.executable)
                    if mode=='wrong_module':
                        s.trigger_begin(str(Path(sys.executable).resolve()),mode);expected='0'*64
                    found=[x for x in actual if Path(x['path']).resolve()==Path(sys.executable).resolve()]
                    write_new(external/'MODULE_GATE.json',dict(actual=actual,expected_python_sha256=expected,matched=bool(found and found[0]['sha256']==expected)))
                    if not found or found[0]['sha256']!=expected:
                        if mode=='wrong_module':s.trigger_end(str(Path(sys.executable).resolve()),dict(actual_sha256=found[0]['sha256'] if found else None,expected_sha256=expected))
                        s.reject('IDENTITY_REJECTED',str(Path(sys.executable).resolve()),dict(module_gate=str(external/'MODULE_GATE.json')));break
                    if mode=='journal_write_failure':
                        critical=Journal(external/'CRITICAL.jsonl');critical.emit('PRE_GO_CRITICAL_READY');s.trigger_begin('journal',mode);critical.f.close()
                        try:critical.emit('PRE_GO_IDENTITY_PASSED')
                        except BaseException as e:
                            s.trigger_end('journal',dict(actual_write_failed=True,error=str(e)));s.reject('JOURNAL_FAILURE_REJECTED','journal',dict(outer_record=True,error=str(e)));break
                        raise RuntimeError('journal closed-file write unexpectedly succeeded')
                    if s.rejections:break
                    proc.stdin.write(b'GO\n');proc.stdin.flush();go=True;s.log.emit('GO_SENT',slot=slot,pid_child=proc.pid)
                elif row['event']=='WORKING':
                    work.set();s.log.emit('CONTROL_POINT',slot=slot,point='WORKING')
                    if mode=='child_timeout':s.trigger_begin('child',mode);fault_armed=True
                    elif mode in ('resource_read_failure','directory_read_timeout'):fault_armed=True
                    elif mode=='watcher_stall':
                        s.trigger_begin('watcher',mode);started=threading.Event();release=threading.Event();s.stall_release=release;s.engine.stall=(started,release);fault_armed=True
                    elif mode=='notification_loss':
                        s.trigger_begin('watcher',mode);s.engine.command('loss');s.trigger_end('watcher',dict(empty_buffer=True,production_parser=True));fault_armed=True
                    elif mode==spec['id'] and s.target_path is not None:
                        s.inject_filesystem(mode);fault_armed=True
                    else:
                        if not s.rejections:
                            proc.stdin.write(b'CONTINUE\n');proc.stdin.flush();continued=True;s.log.emit('CONTINUE_SENT',slot=slot)
                elif row['event']=='COMPLETE':complete=True
            if s.rejections:break
            if exit_ns is not None:break
            threading.Event().wait(.01)
    except Reject as e:s.reject(e.code,e.target,e.detail)
    except BaseException as e:s.reject('HOST_EXCEPTION_REJECTED','host',dict(error=repr(e)))
    finally:
        if s.stall_release:s.stall_release.set()
        obs.release.set()
        if proc.poll() is None:
            terminated=True;s.log.emit('CHILD_TERMINATE_BEGIN',slot=slot,pid_child=proc.pid);proc.kill()
        proc.wait(timeout=3);exit_ns=obs.exited();drain.set()
        for t in threads:t.join(3)
        if any(t.is_alive() for t in threads):s.reject('CLEANUP_REJECTED','pipes',dict(alive=True))
        obs.finish()
        s.current_observer=None
        for p in (proc.stdin,proc.stdout,proc.stderr):
            try:p.close()
            except OSError:pass
        os_times=target.times();s.log.emit('CHILD_CLOSED',slot=slot,pid_child=proc.pid,exit_ns=exit_ns,exit_code=proc.returncode,os_times=os_times,terminated=terminated,pumps_closed=not any(t.is_alive() for t in threads),observers_closed=True,counts=counts,tails_hex={k:v.hex() for k,v in tails.items()})
    audit_begin=now();s.log.emit('POST_AUDIT_BEGIN',slot=slot,begin_ns=audit_begin,exit_ns=exit_ns)
    if post_delay:threading.Event().wait(post_delay)
    if mode=='quick_exit':
        s.trigger_from_producer(producer,'child');s.reject('HANDSHAKE_INCOMPLETE_REJECTED','child',dict(ready=ready,go=go,actual_exit_code=proc.returncode))
    elif mode=='abnormal_exit' and proc.returncode==23 and not s.rejections:
        s.trigger_from_producer(producer,'child');s.reject('ABNORMAL_EXIT_REJECTED','child',dict(actual_exit_code=23))
    elif mode=='truncated_stdout' and tails.get('stdout') and not s.rejections:
        s.trigger_from_producer(producer,'stdout');s.reject('TRUNCATED_OUTPUT_REJECTED','stdout',dict(tail_hex=tails['stdout'].hex()))
    elif not s.rejections:
        if not (ready and go and continued and complete and proc.returncode==0 and not tails.get('stdout') and not pump_errors):s.reject('OUTPUT_AUDIT_REJECTED','output',dict(ready=ready,go=go,continued=continued,complete=complete,exit_code=proc.returncode))
        else:
            need((active/'DATA.bin').read_bytes()==b''.join(bytes([i])*64 for i in range(4)),'CPU data byte mismatch')
    s.log.emit('POST_AUDIT_END',slot=slot,begin_ns=audit_begin,end_ns=now(),files={p.name:dict(**file_id(p),sha256=sha(p)) for p in active.iterdir() if p.is_file()})
    # Failed producers have the same real closure obligations as successful ones.
    # A kill is not proof that every directory completion has already arrived.
    failed=bool(s.rejections)
    s.registry[slot]['closing_files']={str(p):sha(p) for p in active.iterdir() if p.is_file()}
    s.transition(slot,'CLOSING');s.engine.fence(slot);handoff=s.engine.rotate_sealed(slot)
    s.transition(slot,'FAILED' if failed else 'SEALED',handoff=handoff)
    return dict(slot=slot,pid=proc.pid,ready=ready,go=go,continued=continued,complete=complete,exit_code=proc.returncode,exit_ns=exit_ns,post_audit_begin_ns=audit_begin,post_audit_end_ns=now(),external=str(external))
