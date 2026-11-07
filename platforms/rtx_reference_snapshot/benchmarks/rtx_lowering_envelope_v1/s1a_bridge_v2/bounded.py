"""CPU-only execution state, conservative storage reservations and durable stops.

The deadline watcher never walks an output tree or performs numerical analysis.
Filesystem/memory checks are sampled, not claims of instantaneous containment.
Windows Job Objects independently enforce child commit/process limits.
"""
import hashlib,json,os,threading,time
from pathlib import Path

class BudgetStop(RuntimeError):pass

def durable(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(value,separators=(',',':'))+'\n').encode()
    assert len(data)<=65536,'minimum receipt bound'
    # Exclusive temporary and final name: never overwrite an earlier receipt.
    tmp=path.with_name(path.name+'.pending')
    with tmp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    assert not path.exists();os.rename(tmp,path)

class State:
    def __init__(self,root,stage,clock=time.perf_counter):
        self.root=Path(root);self.stage=stage;self.clock=clock;self.start=clock()
        self.current=None;self.completed=0;self.started=0;self.last_completed=None
        self.reason=None;self.peak_commit=0;self.active_pid=None;self.ended=False;self.accounting=None
        self.lock=threading.RLock();self.interrupt=threading.Event()
    def snapshot(self,status):
        with self.lock:
            return dict(stage=self.stage,status=status,pid=os.getpid(),epoch=time.time(),
                seconds=self.clock()-self.start,conservative_owned_seconds=3*(self.clock()-self.start),
                completed=self.completed,native_started=self.started,current=self.current,
                last_completed=self.last_completed,active_pid=self.active_pid,reason=self.reason,
                sampled_controller_peak_private_commit_bytes=self.peak_commit,
                last_settled_storage_accounting=self.accounting,
                analysis_deferred=True,no_retry=True)
    def reserve_start(self,slot,remaining,required):
        with self.lock:
            assert self.current is None,'previous slot must be settled'
            if remaining<=required:
                self.reason='BUDGET_STOP_BEFORE_NEXT_SLOT';raise BudgetStop(self.reason)
            self.current=dict(id=slot['id'],state='RESERVED_NO_NATIVE_START')
    def native_start(self,pid):
        with self.lock:
            assert self.current is not None
            self.current['state']='NATIVE_STARTED';self.started+=1;self.active_pid=pid
    def complete(self):
        with self.lock:
            assert self.current is not None
            self.last_completed=self.current['id'];self.completed+=1;self.current=None;self.active_pid=None
    def minimum_stop(self,reason):
        with self.lock:
            self.reason=self.reason or reason;self.interrupt.set()
            p=self.root/(self.stage+'_MINIMUM_STOP.json')
            if not p.exists():durable(p,self.snapshot('STOP_REQUESTED'))
    def finish(self,status):
        with self.lock:
            if self.ended:return
            if status=='COMPLETE' and self.reason:status='INCOMPLETE_STOPPED'
            durable(self.root/(self.stage+'_ENDED.json'),self.snapshot(status));self.ended=True

class Deadline:
    def __init__(self,state,wall,terminate,grace=5,hard_exit=os._exit,monitor=lambda:None):
        assert 0<grace<wall
        self.state=state;self.wall=wall;self.grace=grace;self.terminate=terminate
        self.hard_exit=hard_exit;self.monitor=monitor;self.done=threading.Event();self.thread=None
    def remaining(self):return self.wall-(self.state.clock()-self.state.start)
    def guard(self):
        if self.state.interrupt.is_set():raise BudgetStop(self.state.reason)
        if self.remaining()<=self.grace:
            self.state.minimum_stop('STAGE_LIFETIME_FINALIZATION_RESERVE');raise BudgetStop(self.state.reason)
    def watch(self):
        while not self.done.wait(.025):
            try:self.monitor()
            except BaseException as exc:
                self.state.minimum_stop('RESOURCE_MONITOR: '+repr(exc));self.terminate()
            if self.remaining()<=self.grace:
                self.state.minimum_stop('STAGE_LIFETIME_FINALIZATION_RESERVE');self.terminate()
            # Leave 250ms before the approved ceiling. No dependency on finally.
            if self.remaining()<=.25:
                self.state.finish('HARD_TERMINATION_INCOMPLETE');self.terminate();self.hard_exit(70);return
    def start(self):
        self.thread=threading.Thread(target=self.watch,daemon=True);self.thread.start();return self
    def close(self):self.done.set();self.thread.join(1)

class ByteLedger:
    """Reservations precede a producer. Reconcile at each slot, full every30.

    The settled manifest includes sizes and SHA256. Already settled bytes cannot
    shrink/change; new files must be explicitly adopted from the active producer
    or the controller. An unregistered file anywhere fails full reconciliation.
    Reconciliation wall time is charged to the same stage. The independent
    deadline thread remains responsive during a scan.
    """
    def __init__(self,root,cap,journal,clock=time.perf_counter):
        self.root=Path(root);self.cap=cap;self.journal=Path(journal);self.clock=clock
        self.files={};self.reserved=0;self.scan_seconds=0;self.events=0
    def path(self,p):
        p=Path(p).resolve();p.relative_to(self.root.resolve());assert not p.is_symlink();return p
    def append(self,event):
        self.events+=1;assert self.events<=4096,'bounded accounting journal'
        data=(json.dumps(dict(sequence=self.events,**event),separators=(',',':'))+'\n').encode()
        assert len(data)<=1024
        with self.journal.open('ab') as f:f.write(data);f.flush();os.fsync(f.fileno())
    def reserve(self,amount):
        assert amount>=0 and not self.reserved
        assert sum(v[0] for v in self.files.values())+amount+4*1024**2<=self.cap,'raw capacity reservation failed'
        self.reserved=amount;self.append(dict(action='RESERVE',bytes=amount))
    @staticmethod
    def signature(p):
        h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
        return (p.stat().st_size,h.hexdigest())
    def adopt(self,paths):
        delta=0;t=self.clock()
        for item in paths:
            p=self.path(item)
            if p==self.journal.resolve():continue
            sig=self.signature(p);key=p.relative_to(self.root.resolve()).as_posix()
            if key in self.files:assert self.files[key]==sig,'settled evidence changed'
            else:self.files[key]=sig;delta+=sig[0]
        self.scan_seconds+=self.clock()-t
        assert delta<=self.reserved,'producer exceeded conservative byte reservation'
        assert sum(v[0] for v in self.files.values())+self.journal.stat().st_size<=self.cap
        self.append(dict(action='SETTLE',bytes=delta,reservation=self.reserved));self.reserved=0
    def reconcile(self):
        t=self.clock();seen=set();total=0
        for p in self.root.rglob('*'):
            assert not p.is_symlink(),'unregistered link'
            if not p.is_file() or p.resolve()==self.journal.resolve():continue
            key=p.relative_to(self.root).as_posix();seen.add(key)
            assert key in self.files,'unregistered output outside active producer'
            assert self.signature(p)==self.files[key],'settled evidence missing/truncated/changed'
            total+=self.files[key][0]
        assert seen==set(self.files),'settled evidence removed'
        assert total+self.journal.stat().st_size<=self.cap
        self.scan_seconds+=self.clock()-t;self.append(dict(action='FULL_RECONCILE',bytes=total,files=len(seen)))
