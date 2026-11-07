"""Persistent namespace guard + overlapping per-slot content guards.

Namespace guards watch name/security (not child directory metadata). Every file
action, including MODIFIED=3, remains guarded by its own content root. No grace
period, path exception, cancellation-as-completion, or notification writer claim.
"""
import base64,ctypes as C,queue,struct,threading
from ctypes import wintypes as W
from pathlib import Path
from common import Journal,now,MAX_GAP,need,file_id,sha,Reject
K=C.WinDLL('kernel32',use_last_error=True)
class OV(C.Structure):
    _fields_=[('Internal',C.c_size_t),('InternalHigh',C.c_size_t),('Offset',W.DWORD),('OffsetHigh',W.DWORD),('event',W.HANDLE)]
def api(n,a,r=W.BOOL):
    f=getattr(K,n);f.argtypes=a;f.restype=r;return f
create=api('CreateFileW',[W.LPCWSTR,W.DWORD,W.DWORD,C.c_void_p,W.DWORD,W.DWORD,W.HANDLE],W.HANDLE)
event=api('CreateEventW',[C.c_void_p,W.BOOL,W.BOOL,W.LPCWSTR],W.HANDLE)
read=api('ReadDirectoryChangesW',[W.HANDLE,C.c_void_p,W.DWORD,W.BOOL,W.DWORD,C.c_void_p,C.POINTER(OV),C.c_void_p])
wait=api('WaitForSingleObject',[W.HANDLE,W.DWORD],W.DWORD)
complete=api('GetOverlappedResult',[W.HANDLE,C.POINTER(OV),C.POINTER(W.DWORD),W.BOOL])
cancel=api('CancelIoEx',[W.HANDLE,C.POINTER(OV)])
close=api('CloseHandle',[W.HANDLE]); reset=api('ResetEvent',[W.HANDLE])
def parse(data):
    if not data:raise Reject('NOTIFICATION_LOSS_REJECTED','watcher',{'bytes':0})
    offset=0;rows=[]
    while True:
        need(offset+12<=len(data),'notification header incomplete')
        nxt,action,n=struct.unpack_from('<III',data,offset)
        need(action in range(1,6) and n%2==0 and n>0 and offset+12+n<=len(data),'notification fields invalid')
        rel=data[offset+12:offset+12+n].decode('utf-16-le');p=Path(rel)
        need(not p.is_absolute() and '..' not in p.parts and ':' not in rel,'notification path escape')
        rows.append((action,rel))
        if nxt==0:break
        need(nxt%4==0 and nxt>=12+n and offset+nxt<len(data),'notification linkage invalid');offset+=nxt
    return rows

class Handle:
    def __init__(self,engine,root,owner,kind,generation=0):
        self.e=engine;self.root=Path(root).resolve();self.owner=owner;self.kind=kind;self.generation=generation
        self.id=f'{owner}:{kind}:{generation}';self.pending=False;self.closed=False;self.armed_ns=now()
        self.h=create(str(self.root),1,7,None,3,0x42000000,None)
        need(self.h not in (None,C.c_void_p(-1).value),'directory handle failed')
        self.ev=event(None,True,False,None);need(self.ev,'directory event failed')
        self.ov=OV();self.ov.event=self.ev;self.buf=C.create_string_buffer(65536)
        self.arm();self.e.log.emit('WATCH_ARMED',watch_id=self.id,root=str(self.root),owner=owner,kind=kind,generation=generation,armed_ns=self.armed_ns)
    def arm(self):
        reset(self.ev)
        flags=(1|2|0x100) if self.kind=='namespace' else (1|2|4|8|0x10|0x100)
        need(read(self.h,self.buf,len(self.buf),self.kind!='namespace',flags,None,C.byref(self.ov),None),'RDCW arm failed')
        self.pending=True
    def consume(self,closing=False):
        n=W.DWORD();ok=complete(self.h,C.byref(self.ov),C.byref(n),False);err=C.get_last_error() if not ok else 0
        self.e.log.emit('IO_COMPLETION',watch_id=self.id,generation=self.generation,closing=closing,success=bool(ok),error=err,bytes=n.value)
        need(ok or (closing and err==995),'directory final completion failed')
        self.pending=False
        if ok:self.e.accept(self,self.buf.raw[:n.value])
    def shutdown(self,coordination=None):
        self.e.log.emit('WATCH_CLOSE_BEGIN',watch_id=self.id,pending=self.pending)
        if coordination:coordination(self)
        if self.pending:
            ok=cancel(self.h,C.byref(self.ov));err=C.get_last_error() if not ok else 0
            self.e.log.emit('CANCEL_ISSUED',watch_id=self.id,success=bool(ok),error=err)
            need(ok or err==1168,'cancel request failed')
            need(wait(self.ev,1000)==0,'cancellation completion timeout')
            self.consume(closing=True)
        a=close(self.h);b=close(self.ev);self.closed=True
        self.e.log.emit('WATCH_CLOSED',watch_id=self.id,directory_closed=bool(a),event_closed=bool(b),pending=False)
        need(a and b,'watch handle close failure')

class Engine:
    def __init__(self,path,registry,roots,detector):
        self.registry=registry;self.roots=roots;self.detector=detector;self.log=Journal(path)
        self.commands=queue.Queue();self.handles={};self.fences={};self.lock=threading.RLock()
        self.stop=threading.Event();self.ready=threading.Event();self.error=None;self.last_begin=now();self.last_end=None;self.last_valid_begin=None
        self.stall=None;self.probe=None;self.thread=threading.Thread(target=self.run,name='RDCW_PERSISTENT',daemon=True);self.thread.start()
        need(self.ready.wait(10),'watch engine arm timeout');need(self.error is None,'watch setup '+str(self.error))
    def command(self,op,*args):
        ack=threading.Event();result={};self.commands.put((op,args,ack,result))
        need(ack.wait(5),'watch command timeout');need('error' not in result,result.get('error'));return result.get('value')
    def accept(self,h,data):
        raw=self.log.emit('RAW_NOTIFY',watch_id=h.id,generation=h.generation,root=str(h.root),raw_base64=base64.b64encode(data).decode(),bytes=len(data),writer_PID=None,operation_time=None)
        try:items=parse(data)
        except Reject as e:self.detector(e.code,e.target,dict(raw_seq=raw['seq']));return
        for action,rel in items:
            p=(h.root/rel).resolve();state=self.registry.get(h.owner,{}).get('state','FROZEN')
            canonical=str(p).lower()
            with self.lock:
                fence=self.fences.get(h.owner)
            is_fence=bool(fence and canonical==str(fence['path']).lower() and p.is_file() and p.read_bytes()==fence['token'])
            allowed=h.kind=='content' and state in ('ACTIVE','CLOSING')
            if state=='CLOSING' and allowed and not is_fence:
                frozen=self.registry[h.owner].get('closing_files',{})
                allowed=p.is_file() and str(p) in frozen and sha(p)==frozen[str(p)]
            if h.kind=='sealed':allowed=False
            ident=file_id(p) if p.exists() and p.is_file() else None
            row=self.log.emit('NOTIFY_DECISION',watch_id=h.id,raw_seq=raw['seq'],action=action,path=str(p),canonical=canonical,file_identity=ident,owner=h.owner,state=state,allowed=allowed,controller_fence=is_fence,writer_PID=None,operation_time=None)
            if is_fence and allowed:
                fence['seen'].set();self.log.emit('FENCE_OBSERVED',owner=h.owner,watch_id=h.id,token_hex=fence['token'].hex(),raw_seq=raw['seq'])
            if not allowed:self.detector('SEALED_WRITE_REJECTED',str(p),dict(watch_id=h.id,raw_seq=raw['seq'],decision_seq=row['seq'],file_identity=ident))
    def fence(self,owner):
        row=self.registry[owner];p=Path(row['path'])/'FENCE.bin';token=(owner+':'+str(now())).encode();seen=threading.Event()
        with self.lock:self.fences[owner]=dict(path=p,token=token,seen=seen)
        self.log.emit('FENCE_WRITE_BEGIN',owner=owner,path=str(p),token_hex=token.hex())
        with p.open('wb') as f:f.write(token);f.flush();__import__('os').fsync(f.fileno())
        self.log.emit('FENCE_WRITE_CLOSED',owner=owner,path=str(p),file_identity=file_id(p))
        need(seen.wait(2),'explicit file fence not observed')
    def rotate_sealed(self,owner):return self.command('seal',owner)
    def run(self):
        try:
            for root,owner,kind in self.roots:
                h=Handle(self,root,owner,kind);self.handles[h.id]=h
            self.last_begin=now();self.log.emit('WATCH_STREAM_ARMED',begin_ns=self.last_begin,handles=list(self.handles));self.ready.set()
            while not self.stop.is_set():
                begin=now();self.last_begin=begin;self.log.emit('WATCH_LOOP_BEGIN',begin_ns=begin)
                if self.stall:
                    gate,release=self.stall;self.log.emit('STALL_CONTROL_POINT',target='watcher');gate.set();need(release.wait(3),'watcher fault cleanup release timeout');self.stall=None
                try:op,args,ack,result=self.commands.get_nowait()
                except queue.Empty:op=None
                if op:
                    try:
                        if op=='seal':
                            owner=args[0];old=next(h for h in self.handles.values() if h.owner==owner and h.kind=='content')
                            new=Handle(self,old.root,owner,'sealed',old.generation+1);self.handles[new.id]=new
                            self.log.emit('HANDOFF_OVERLAP',owner=owner,old=old.id,new=new.id,new_armed_ns=new.armed_ns)
                            old.shutdown();del self.handles[old.id];result['value']=dict(old=old.id,new=new.id)
                        elif op=='loss':
                            self.log.emit('PARSER_LOSS_INJECTED',target='watcher',injected_base64='');self.accept(next(iter(self.handles.values())),b'')
                        elif op=='pending_close':
                            h=Handle(self,args[0],'pending_probe','sealed');self.handles[h.id]=h
                            self.log.emit('PENDING_PROBE_READY',watch_id=h.id)
                            args[1].set();need(args[2].wait(3),'injector pending completion coordination')
                            need(wait(h.ev,1000)==0,'actual completed notification not pending')
                            self.log.emit('PENDING_COMPLETION_SIGNALED',watch_id=h.id)
                            h.shutdown();del self.handles[h.id]
                        else:raise ValueError('unknown watch command')
                    except BaseException as e:result['error']=str(e);raise
                    finally:ack.set()
                for h in list(self.handles.values()):
                    if wait(h.ev,0)==0:h.consume();h.arm()
                end=now();self.last_end=end;self.last_valid_begin=begin;self.log.emit('WATCH_LOOP_END',begin_ns=begin,end_ns=end,handles=[h.id for h in self.handles.values()],pending=all(h.pending for h in self.handles.values()))
                self.stop.wait(.1)
        except BaseException as e:
            self.error=str(e)
            try:self.log.emit('WATCH_ENGINE_ERROR',error=self.error)
            except BaseException:pass
            self.ready.set()
        finally:
            for h in list(self.handles.values()):
                try:h.shutdown()
                except BaseException as e:
                    self.error=self.error or str(e)
                    try:self.log.emit('WATCH_CLOSE_ERROR',watch_id=h.id,error=str(e))
                    except BaseException:pass
            try:self.log.emit('WATCH_STREAM_CLOSED',error=self.error)
            finally:self.log.close()
    def check(self):
        if self.error:raise Reject('WATCH_ENGINE_REJECTED','watcher',self.error)
        if not self.thread.is_alive():raise Reject('WATCH_ENGINE_REJECTED','watcher','thread dead')
        if now()-(self.last_valid_begin if self.last_valid_begin is not None else self.last_begin)>MAX_GAP:
            raise Reject('WATCHER_GAP_REJECTED','watcher',{'last_begin_ns':self.last_begin,'last_end_ns':self.last_end,'observed_ns':now()})
    def shutdown(self):
        self.stop.set();self.thread.join(3);need(not self.thread.is_alive(),'watch thread cleanup timeout');need(self.error is None,'watch final close '+str(self.error))
