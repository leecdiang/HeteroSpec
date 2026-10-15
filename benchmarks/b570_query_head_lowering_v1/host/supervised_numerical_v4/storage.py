"""CPU-only storage lease: snapshot before spawn, bounded active scans, fail-closed watches.

No claim of filesystem immutability: a write notification to a sealed area invalidates
the lease. Notification loss/overflow, links, stalled readers and API failures also fail.
The active reservation is charged in full even while its files are empty.
"""
import ctypes
from ctypes import wintypes as W
import os
import pathlib
import struct
import json
import threading
import time

ACTIVE_BYTES=32*1024**2
ACTIVE_FILES=256
MAX_GAP_NS=1_000_000_000

def need(x,s):
    if not x:raise ValueError(s)

def inventory(root):
    total=count=0
    if not root.exists():return dict(bytes=0,files=0)
    for parent,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:
            p=pathlib.Path(parent)/name
            need(not p.is_symlink() and not p.is_junction(),'storage links/reparse paths forbidden: '+str(p))
        for name in files:
            st=(pathlib.Path(parent)/name).stat();need(st.st_nlink==1,'storage hard links forbidden')
            total+=st.st_size;count+=1
    return dict(bytes=total,files=count)

class OVERLAPPED(ctypes.Structure):
    _fields_=[('Internal',ctypes.c_size_t),('InternalHigh',ctypes.c_size_t),('Offset',W.DWORD),('OffsetHigh',W.DWORD),('hEvent',W.HANDLE)]

class Watch:
    def __init__(self,root,allowed,job):
        self.root=pathlib.Path(root);self.allowed=allowed;self.job=job;self.ready=threading.Event();self.stop=threading.Event()
        self.error=None;self.beat=0;self.events=0;self.max_interval_ns=0;self.last=None
        self.log=pathlib.Path(job['folder'])/('WATCH_'+str(job['storage_roots'].index(str(root)))+'.jsonl')
        self.thread=threading.Thread(target=self.run,name='SEALED_STORAGE_WATCH',daemon=True);self.thread.start()
        need(self.ready.wait(5),'storage watcher setup timeout');self.check()
    def check(self):
        need(self.error is None,'storage watch failure: '+str(self.error))
        need(self.thread.is_alive(),'storage watcher exited')
        need(time.monotonic_ns()-self.beat<=MAX_GAP_NS,'storage watcher effective gap >1s')
    def accept(self,data):
        # Also directly fault-tested with malformed/overflow and sealed paths.
        need(data,'storage notification overflow/loss')
        pos=0
        while True:
            need(pos+12<=len(data),'truncated storage notification')
            nxt,action,n=struct.unpack_from('<III',data,pos)
            need(action in range(1,6) and n%2==0 and pos+12+n<=len(data),'invalid storage notification')
            rel=data[pos+12:pos+12+n].decode('utf-16-le');path=self.root/rel
            need(self.allowed(path),'sealed storage changed: '+str(path));self.events+=1
            if not nxt:break
            need(nxt>=12+n and pos+nxt<len(data),'invalid notification next offset');pos+=nxt
    def run(self):
        k=ctypes.WinDLL('kernel32',use_last_error=True);h=event=None;pending=False
        k.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,ctypes.c_void_p,W.DWORD,W.DWORD,W.HANDLE];k.CreateFileW.restype=W.HANDLE
        k.CreateEventW.argtypes=[ctypes.c_void_p,W.BOOL,W.BOOL,W.LPCWSTR];k.CreateEventW.restype=W.HANDLE
        k.ReadDirectoryChangesW.argtypes=[W.HANDLE,ctypes.c_void_p,W.DWORD,W.BOOL,W.DWORD,ctypes.c_void_p,ctypes.POINTER(OVERLAPPED),ctypes.c_void_p]
        k.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD];k.GetOverlappedResult.argtypes=[W.HANDLE,ctypes.POINTER(OVERLAPPED),ctypes.POINTER(W.DWORD),W.BOOL]
        k.CancelIoEx.argtypes=[W.HANDLE,ctypes.POINTER(OVERLAPPED)];k.CloseHandle.argtypes=[W.HANDLE];k.ResetEvent.argtypes=[W.HANDLE]
        try:
            h=k.CreateFileW(str(self.root),1,7,None,3,0x42000000,None)
            need(h not in (None,ctypes.c_void_p(-1).value),'storage directory handle '+str(ctypes.get_last_error()))
            event=k.CreateEventW(None,True,False,None);need(event,'storage event handle')
            ov=OVERLAPPED();ov.hEvent=event;buf=ctypes.create_string_buffer(65536)
            while not self.stop.is_set():
                if not pending:
                    k.ResetEvent(event)
                    need(k.ReadDirectoryChangesW(h,buf,len(buf),True,0x1|0x2|0x4|0x8|0x10|0x100,None,ctypes.byref(ov),None),'ReadDirectoryChangesW '+str(ctypes.get_last_error()))
                    pending=True
                now=time.monotonic_ns()
                if not self.ready.is_set():self.beat=now;self.ready.set()
                barrier=self.job.get('faults',{}).get('watch_stall')
                if barrier:
                    need(self.job['purpose']=='CPU_TEST','watch fault CPU only');p=pathlib.Path(barrier);p.with_suffix('.entered').write_text('entered')
                    while not p.exists() and not self.stop.is_set():time.sleep(.005)
                result=k.WaitForSingleObject(event,50)
                need(result in (0,258),'storage event wait failed')
                if result==0:
                    n=W.DWORD();need(k.GetOverlappedResult(h,ctypes.byref(ov),ctypes.byref(n),False),'storage completion failed')
                    pending=False;self.accept(buf.raw[:n.value])
                end=time.monotonic_ns();anchor=self.last if self.last is not None else now
                gap=end-anchor;self.max_interval_ns=max(self.max_interval_ns,gap)
                need(gap<=MAX_GAP_NS,'storage watcher effective interval >1s')
                self.last=now;self.beat=now
                with self.log.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(begin_ns=now,end_ns=end,previous_begin_ns=anchor,events_seen=self.events))+'\n')
                self.stop.wait(.05) # Also bounds notification feedback from this journal.
        except BaseException as e:self.error=str(e);self.ready.set()
        finally:
            if h not in (None,ctypes.c_void_p(-1).value):
                if pending:
                    k.CancelIoEx(h,ctypes.byref(ov));k.WaitForSingleObject(event,1000)
                k.CloseHandle(h)
            if event:k.CloseHandle(event)
    def close(self):
        self.stop.set();self.thread.join(timeout=2);need(not self.thread.is_alive(),'storage watcher cleanup timeout')

class Lease:
    def __init__(self,job):
        self.job=job;self.started=time.monotonic_ns();self.watches=[];folder=pathlib.Path(job['folder']).resolve()
        roots=[pathlib.Path(p).resolve() for p in job['storage_roots']]
        need(all(not (a==b or a in b.parents or b in a.parents) for i,a in enumerate(roots) for b in roots[i+1:]),'nonoverlapping storage roots')
        def allowed(path):
            p=path.resolve()
            return p==folder or folder in p.parents or (job['purpose']=='CPU_TEST' and p.parent in roots)
        try:
            # Arm notifications BEFORE snapshot. Never clear/drop pending changes.
            for root in roots:self.watches.append(Watch(root,allowed,job))
            all_rows=[inventory(p) for p in roots];run=inventory(pathlib.Path(job['run_root']))
            self.baseline=dict(actual_bytes=sum(r['bytes'] for r in all_rows),actual_files=sum(r['files'] for r in all_rows),run_bytes=run['bytes'],run_files=run['files'],active_bytes_cap=ACTIVE_BYTES,active_files_cap=ACTIVE_FILES)
            self.check();self.ready_ns=time.monotonic_ns()
        except BaseException:
            self.close();raise
    def check(self):
        for w in self.watches:w.check()
    def close(self):
        for w in self.watches:w.close()
        if self.job.get('faults',{}).get('raise_watch_cleanup'):
            need(self.job['purpose']=='CPU_TEST','cleanup injection CPU only');raise ValueError('injected storage cleanup failure')
    def receipt(self):
        return dict(preflight_begin_ns=self.started,preflight_ready_ns=self.ready_ns,baseline=self.baseline,
            watches=[dict(root=str(w.root),events=w.events,error=w.error,max_loop_interval_ns=w.max_interval_ns,journal=w.log.name,thread_alive_after_cleanup=w.thread.is_alive()) for w in self.watches],
            clock='SYSTEM_MONOTONIC_NS',snapshot_outside_native_lifetime=True)

def bounded_usage(job):
    b=job['storage_baseline'];active=inventory(pathlib.Path(job['folder']))
    need(active['bytes']<=b['active_bytes_cap'] and active['files']<=b['active_files_cap'],'active storage reservation exceeded')
    # Full reserved bytes, not a lagging sum of observed growth. Duplicate
    # baseline active bytes are intentionally charged conservatively.
    output=b['actual_bytes']+b['active_bytes_cap']
    reserve=b['run_bytes']+b['active_bytes_cap']+(b['run_files']+b['active_files_cap'])*1024+1024**2
    return dict(output_bytes=output,archive_reserve_bytes=reserve,active_observed_bytes=active['bytes'],active_observed_files=active['files'],accounting='BASELINE_PLUS_FULL_ACTIVE_RESERVATION',historical_files_scanned=0)
