"""One identical production notification policy for CPU and scientific children."""
import base64
import ctypes
from ctypes import wintypes as W
from pathlib import Path
import struct
import threading
import time
from common import need, inventory, Journal, MAX_GAP

class OVERLAPPED(ctypes.Structure):
    _fields_=[('Internal',ctypes.c_size_t),('InternalHigh',ctypes.c_size_t),
        ('Offset',W.DWORD),('OffsetHigh',W.DWORD),('hEvent',W.HANDLE)]

def production_allowed(path,active):
    p=Path(path).resolve();a=Path(active).resolve()
    return p==a or a in p.parents

def parse_notifications(data):
    need(bool(data),'notification loss/overflow')
    pos=0;result=[]
    while True:
        need(pos+12<=len(data),'truncated notification header')
        nxt,action,size=struct.unpack_from('<III',data,pos)
        need(action in range(1,6) and size%2==0 and pos+12+size<=len(data),'invalid notification fields')
        rel=data[pos+12:pos+12+size].decode('utf-16-le')
        need(not Path(rel).is_absolute() and '..' not in Path(rel).parts,'notification traversal')
        result.append((action,rel))
        if not nxt:break
        need(nxt>=12+size and pos+nxt<len(data),'invalid notification link')
        pos+=nxt
    return result

class Watch:
    def __init__(self,root,active,journal):
        self.root=Path(root).resolve();self.active=Path(active).resolve();self.journal=journal
        self.error=None;self.ready=threading.Event();self.stop=threading.Event()
        self.beat=time.monotonic_ns();self.events=0;self.max_gap=0
        self.thread=threading.Thread(target=self.run,name='PRODUCTION_DIRECTORY_WATCH',daemon=True)
        self.thread.start();need(self.ready.wait(5),'watch setup timeout');self.check()
    def accept(self,data):
        # The complete rejected buffer is durable before parsing or policy checks.
        self.journal.emit('RAW_NOTIFY',watch=str(self.root),raw_base64=base64.b64encode(data).decode('ascii'),bytes=len(data),
            writing_PID=None,operation_timestamp=None)
        for action,rel in parse_notifications(data):
            path=self.root/rel;allowed=production_allowed(path,self.active)
            self.journal.emit('NOTIFY_DECISION',watch=str(self.root),action=action,relative_path=rel,
                resolved_path=str(path.resolve()),allowed=allowed,writing_PID=None,operation_timestamp=None)
            need(allowed,'sealed storage changed: '+str(path));self.events+=1
    def check(self):
        need(self.error is None,'watch integrity failure: '+str(self.error))
        need(self.thread.is_alive(),'watch thread stopped')
        need(time.monotonic_ns()-self.beat<=MAX_GAP,'watch effective gap >1s')
    def run(self):
        k=ctypes.WinDLL('kernel32',use_last_error=True);h=event=None;pending=False
        k.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,ctypes.c_void_p,W.DWORD,W.DWORD,W.HANDLE];k.CreateFileW.restype=W.HANDLE
        k.CreateEventW.argtypes=[ctypes.c_void_p,W.BOOL,W.BOOL,W.LPCWSTR];k.CreateEventW.restype=W.HANDLE
        k.ReadDirectoryChangesW.argtypes=[W.HANDLE,ctypes.c_void_p,W.DWORD,W.BOOL,W.DWORD,ctypes.c_void_p,ctypes.POINTER(OVERLAPPED),ctypes.c_void_p]
        k.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD]
        k.GetOverlappedResult.argtypes=[W.HANDLE,ctypes.POINTER(OVERLAPPED),ctypes.POINTER(W.DWORD),W.BOOL]
        k.CancelIoEx.argtypes=[W.HANDLE,ctypes.POINTER(OVERLAPPED)];k.CloseHandle.argtypes=[W.HANDLE];k.ResetEvent.argtypes=[W.HANDLE]
        try:
            h=k.CreateFileW(str(self.root),1,7,None,3,0x42000000,None)
            need(h not in (None,ctypes.c_void_p(-1).value),'directory handle error '+str(ctypes.get_last_error()))
            event=k.CreateEventW(None,True,False,None);need(event,'watch event handle')
            ov=OVERLAPPED();ov.hEvent=event;buf=ctypes.create_string_buffer(65536)
            previous=time.monotonic_ns()
            while not self.stop.is_set():
                if not pending:
                    k.ResetEvent(event)
                    need(k.ReadDirectoryChangesW(h,buf,len(buf),True,0x1|0x2|0x4|0x8|0x10|0x100,None,ctypes.byref(ov),None),'ReadDirectoryChangesW failure')
                    pending=True
                now=time.monotonic_ns()
                if not self.ready.is_set():
                    self.journal.emit('WATCH_ARMED',watch=str(self.root),active=str(self.active))
                    self.beat=time.monotonic_ns();self.ready.set();previous=now
                result=k.WaitForSingleObject(event,50);need(result in (0,258),'directory wait failure')
                if result==0:
                    n=W.DWORD();need(k.GetOverlappedResult(h,ctypes.byref(ov),ctypes.byref(n),False),'directory completion failure')
                    pending=False;self.accept(buf.raw[:n.value])
                end=time.monotonic_ns();gap=end-previous;self.max_gap=max(self.max_gap,gap)
                need(gap<=MAX_GAP,'watch effective interval >1s')
                self.beat=now;previous=now
        except BaseException as e:
            self.error=str(e)
            try:self.journal.emit('WATCH_ERROR',watch=str(self.root),error=self.error)
            except BaseException:pass # check() still fails; no integrity PASS is emitted.
            self.ready.set()
        finally:
            if h not in (None,ctypes.c_void_p(-1).value):
                if pending:
                    self.journal.emit('CANCEL_BEGIN',pending=True)
                    cancelled=k.CancelIoEx(h,ctypes.byref(ov))
                    error=ctypes.get_last_error()
                    if not cancelled and error!=1168:self.error=self.error or 'CancelIoEx cleanup error '+str(error)
                    waited=k.WaitForSingleObject(event,1000)
                    if waited!=0:self.error=self.error or 'pending notification cleanup incomplete'
                    else:
                        n=W.DWORD()
                        completed=k.GetOverlappedResult(h,ctypes.byref(ov),ctypes.byref(n),False)
                        completion_error=ctypes.get_last_error()
                        self.journal.emit('CANCEL_COMPLETION',completed=bool(completed),error=completion_error,bytes=n.value)
                        if completed:
                            try:self.accept(buf.raw[:n.value])
                            except BaseException as e:self.error=self.error or str(e)
                        elif completion_error!=995:
                            self.error=self.error or 'terminal completion error '+str(completion_error)
                if not k.CloseHandle(h):self.error=self.error or 'watch directory close failure'
            if event and not k.CloseHandle(event):self.error=self.error or 'watch event close failure'
            self.journal.emit('HANDLE_CLOSE_END',error=self.error)
    def close(self):
        self.stop.set();self.thread.join(timeout=2)
        need(not self.thread.is_alive(),'watch cleanup timeout')
        need(self.error is None,'watch rejected/cleanup failure: '+str(self.error))

class Lease:
    def __init__(self,roots,active,journal_dir):
        self.roots=[Path(p).resolve() for p in roots];self.active=Path(active).resolve();self.watches=[];self.journals=[]
        need(self.active.is_dir(),'active directory must exist before lease')
        need(sum(self.active.parent==p for p in self.roots)==1,'active output must be a direct child of one registered root; no mutable ancestor')
        self.started=time.monotonic_ns();self.baseline=None
        try:
            for i,root in enumerate(self.roots):
                need(root.is_dir(),'sealed/output root missing')
                need(not any(a==root or a in root.parents or root in a.parents for a in self.roots[:i]),'overlapping lease roots')
                j=Journal(Path(journal_dir)/('WATCH_'+str(i)+'.jsonl'))
                self.journals.append(j);self.watches.append(Watch(root,self.active,j))
            self.baseline=[dict(root=str(p),**inventory(p)) for p in self.roots]
            self.check();self.ready=time.monotonic_ns()
        except BaseException:
            self.close();raise
    def check(self):
        for w in self.watches:w.check()
    def close(self):
        errors=[]
        for w in self.watches:
            try:w.close()
            except BaseException as e:errors.append(str(e))
        for j in self.journals:
            try:j.close()
            except BaseException as e:errors.append(str(e))
        need(not errors,'; '.join(errors))
