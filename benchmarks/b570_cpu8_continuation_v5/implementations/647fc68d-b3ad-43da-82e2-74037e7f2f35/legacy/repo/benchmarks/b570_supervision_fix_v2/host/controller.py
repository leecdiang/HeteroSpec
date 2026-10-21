"""One fresh round controller, one shared registered protected tree per round."""
import sys
sys.dont_write_bytecode=True
if __name__=='__main__' and sys.stdin.readline()!='LAUNCH_GO\n':raise SystemExit('owned CPU launcher gate required')
import hashlib,json,os,subprocess,threading
from pathlib import Path
from common import HERE,DESIGN,BASE,Journal,load,write_new,now,need,sha,file_id,owned
from watch import Engine
from supervisor import run_slot
from admission import Admission

class Session:
    def __init__(self,cfg):
        self.cfg=cfg;self.root=owned(cfg['root']);self.protected=self.root/'protected';self.external=self.root/'external'
        self.registry=cfg['registry'];self.log=Journal(self.external/'ROUND.jsonl');self.streams={}
        for entry in self.registry.values():need(owned(entry['path']).parent==(self.protected/'slots').resolve(),'registered slot escaped new protected catalog')
        self.admission=Admission();self.lock=self.admission.lock;self.case=None;self.rejections=[];self.target_path=None;self.stall_release=None;self.open_trigger=None
        self.closed_cases=set();self.log.on_failure=self.journal_failure
        self.log.emit('ROUND_STARTED',config=cfg,host_hashes={p.name:sha(p) for p in HERE.glob('*') if p.is_file()},controller_pid=os.getpid())
        roots=[(self.protected,'protected_namespace','namespace'),(self.protected/'slots','slots_namespace','namespace'),(self.protected/'inputs','inputs','sealed'),(self.protected/'sealed','results','sealed'),(self.protected/'history','history','sealed'),(DESIGN,'real_source','sealed')]
        roots.extend((Path(row['path']),key,'content') for key,row in self.registry.items())
        self.engine=Engine(self.external/'WATCH.jsonl',self.registry,roots,self.reject,state_lock=self.lock,journal_failure=self.journal_failure)
        self.guard_stop=threading.Event();self.current_observer=None
        self.guard=threading.Thread(target=self.guard_loop,name='INDEPENDENT_WATCHDOG',daemon=True);self.guard.start()
    def guard_loop(self):
        while not self.guard_stop.is_set():
            try:
                if not (self.engine.stop.is_set() and not self.engine.thread.is_alive()):self.engine.check()
                observer=self.current_observer
                if observer is not None and observer.exit_ns is None:observer.check()
            except BaseException as e:
                self.reject(getattr(e,'code','WATCHDOG_REJECTED'),getattr(e,'target','watcher'),getattr(e,'detail',repr(e)))
                if self.stall_release:self.stall_release.set()
            self.guard_stop.wait(.1)
    def journal_failure(self,path,error):
        # Independent launcher captures this stderr channel in its own files.
        # It is not an outer_record boolean in the failing journal.
        self.admission.reject(fatal=path==str(self.log.path))
        signal=dict(event='EMERGENCY_JOURNAL_FAILURE',path=path,error=repr(error),
                    case_id=self.case['id'] if self.case else None,at_ns=now(),pid=os.getpid())
        raw=(json.dumps(signal,sort_keys=True)+'\n').encode()
        try:need(os.write(2,raw)==len(raw),'emergency stderr short write')
        except BaseException:
            self.admission.reject(fatal=True)
        if path!=str(self.log.path):
            self.reject('JOURNAL_FAILURE_REJECTED','journal',dict(failed_path=path))
    def reject(self,code,target,detail=None):
        with self.lock:
            # No attribution of new events to a completed fault by equal hash.
            self.admission.reject()
            target=str(Path(target).absolute()) if ':' in str(target) else str(target)
            planned=self.case['target'] if self.case else None
            same=planned is not None and target.lower()==planned.lower()
            row=dict(case_id=self.case['id'] if self.case else None,code=code,target=target,detail=detail,
                     fault_id=self.case['fault_id'] if self.case and same else None)
            try:row=self.log.emit('DETECTOR',**row)
            except BaseException:
                self.admission.reject(fatal=True)
            self.rejections.append(row)
    def send(self,proc,payload,event,slot):
        return self.admission.send(proc.stdin,payload,
            lambda:self.log.emit(event,slot=slot,pid_child=proc.pid))
    def transition(self,slot,state,**kw):
        with self.lock:
            previous=self.registry[slot]['state'];self.registry[slot]['state']=state
            self.log.emit('SLOT_STATE',slot=slot,previous=previous,state=state,**kw)
    def trigger_begin(self,target,mode):
        with self.lock:
            if self.open_trigger is not None:return
            self.open_trigger=self.log.emit('INJECTION_BEGIN',case_id=self.case['id'],code=self.case['trigger'],target=str(target),fault_id=self.case['fault_id'],mode=mode)
    def trigger_end(self,target,effect):
        with self.lock:
            if self.open_trigger is None:return
            self.log.emit('INJECTION_END',case_id=self.case['id'],code=self.case['trigger'],target=str(target),fault_id=self.case['fault_id'],begin_ns=self.open_trigger['at_ns'],effect=effect);self.open_trigger=None
    def trigger_local(self,target,effect):
        if self.open_trigger is None:self.trigger_begin(target,self.case['id'])
        self.trigger_end(target,effect)
    def trigger_from_producer(self,path,target):
        rows=[json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines()]
        actual=[r for r in rows if r['event']=='FAULT_CONTROL']
        if actual:
            self.log.emit('PRODUCER_FAULT_LINK',case_id=self.case['id'],fault_id=self.case['fault_id'],target=target,producer_event=actual[-1],producer_journal=str(path))
    def inject_filesystem(self,mode):
        folder=self.external/self.case['id'];config=folder/'INJECT.json';receipt=folder/'INJECTION.json'
        write_new(config,dict(target=str(self.target_path),fixture_root=str(self.protected),token='CPU_FAULT:'+self.case['fault_id'],fault_id=self.case['fault_id'],trigger=self.case['trigger'],receipt=str(receipt)))
        self.trigger_begin(str(self.target_path),mode)
        ready=threading.Event();done=threading.Event();thread=None;error=[]
        if mode=='terminal_pending_completion':
            def closing():
                try:self.engine.command('pending_close',self.target_path.parent,ready,done)
                except BaseException as e:error.append(str(e))
            thread=threading.Thread(target=closing,name='PENDING_CLOSE_COORDINATOR');thread.start();need(ready.wait(3),'pending watch not armed')
        with (folder/'INJECTOR.stdout.log').open('xb') as fo,(folder/'INJECTOR.stderr.log').open('xb') as fe:
            p=subprocess.Popen([sys.executable,'-B',str(HERE/'injector.py'),str(config)],stdout=fo,stderr=fe)
            self.log.emit('INJECTOR_SPAWNED',case_id=mode,pid_child=p.pid,target=str(self.target_path));code=p.wait(timeout=5)
        done.set()
        if thread:thread.join(5);need(not thread.is_alive() and not error,'pending close failed '+str(error))
        need(code==0 and receipt.is_file(),'actual filesystem injector failed')
        actual=load(receipt);self.trigger_end(str(self.target_path),dict(injection_receipt=str(receipt),after_sha256=actual['after_sha256'],file_identity=file_id(self.target_path)))
    def run_case(self,spec):
        with self.lock:
            self.admission.begin()
            self.case=dict(spec,fault_id=f"{self.cfg['round']}:{spec['id']}");self.rejections=[]
        self.streams={name:Journal(self.external/spec['id']/(name.upper()+'.jsonl')) for name in ('resource','directory')}
        for journal in self.streams.values():journal.on_failure=self.journal_failure
        self.stall_release=None;self.open_trigger=None
        self.target_path=Path(spec['target']) if spec.get('filesystem') else None
        self.log.emit('CASE_BEGIN',case_id=spec['id'],spec=self.case)
        rows=[]
        try:
            if spec['id']=='normal_transition':
                for pair in range(8):
                    a,b=spec['slots'][2*pair:2*pair+2]
                    rows.append(run_slot(self,a,mode='normal_single'))
                    if self.rejections:break
                    need(self.registry[a]['state']=='SEALED','A must be sealed before B')
                    self.log.emit('PAIR_A_SEALED_BEFORE_B',pair=pair,a=a,b=b)
                    rows.append(run_slot(self,b,mode='normal_single'))
                    if self.rejections:break
            elif spec['id']=='late_closed_slot_write':
                a,b=spec['slots'];rows.append(run_slot(self,a,mode='normal_single'))
                if not self.rejections:
                    need(self.registry[a]['state']=='SEALED','late write requires sealed A')
                    self.log.emit('LATE_WRITE_A_SEALED',a=a,b=b);rows.append(run_slot(self,b))
            else:rows.append(run_slot(self,spec['slots'][0],post_delay=1.1 if spec['id']=='normal_single' else 0))
        except BaseException as e:self.reject('CASE_EXCEPTION_REJECTED','host',dict(error=repr(e)))
        if self.open_trigger is not None:self.trigger_end(spec['target'],dict(cleanup_boundary=True))
        if not self.rejections and spec['kind']=='positive':self.log.emit('POSITIVE_COMPLETE',case_id=spec['id'],code=spec['detector'])
        self.log.emit('CASE_CLOSED',case_id=spec['id'],children=rows,rejection_count=len(self.rejections),states={k:self.registry[k]['state'] for k in spec['slots']},cleanup_complete=all(r.get('exit_ns') is not None for r in rows))
        for journal in self.streams.values():
            try:journal.close()
            except BaseException:
                if not journal.failed:raise
        self.closed_cases.add(spec['id'])
        write_new(self.external/spec['id']/'EXECUTION.json',dict(case_id=spec['id'],children=rows,rejections=self.rejections))
        # A wrong/early rejection must not be relabelled as an expected fault.
        unexpected=any(r['code']!=spec['detector'] or str(r['target']).lower()!=str(spec['target']).lower() for r in self.rejections)
        if spec['kind']=='positive' and self.rejections:unexpected=True
        closed=all(r.get('exit_ns') is not None for r in rows) and bool(rows)
        with self.lock:
            self.admission.end(not unexpected and closed)
            self.case=None
        if unexpected or self.admission.fatal:raise RuntimeError('GLOBAL_WRONG_FAILURE '+spec['id'])
    def close(self):
        self.log.emit('ROUND_CLOSE_BEGIN')
        try:self.engine.shutdown()
        finally:
            self.guard_stop.set();self.guard.join(3)
            for j in self.streams.values():
                try:j.close()
                except BaseException:
                    if not j.failed:raise
            need(not self.admission.fatal,'late/global rejection during round close')
            self.log.emit('ROUND_CLOSED');self.log.close()

if __name__=='__main__':
    cfg=load(sys.argv[1]);s=Session(cfg);error=None
    try:
        for spec in cfg['cases']:s.run_case(spec)
    except BaseException as e:error=repr(e);s.log.emit('ROUND_STOP',error=error)
    finally:s.close()
    write_new(Path(cfg['root'])/'external/CONTROLLER_END.json',dict(error=error,finished_ns=now(),CPU_only=True))
    raise SystemExit(0 if error is None else 1)
