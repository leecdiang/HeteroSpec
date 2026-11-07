"""The same interval policy is used live, offline, and with a virtual CPU clock."""
import json
import pathlib
import time
import threading
import ctypes
import mmap

MAX_GAP_NS=1_000_000_000
PERIOD_NS=100_000_000

def need(x,message):
    if not x:raise ValueError(message)

class Clock:
    def __init__(self,job):
        self.path=job.get('virtual_clock')
        need(not self.path or job['purpose']=='CPU_TEST','virtual clock is CPU-test only')
        self.counter=VirtualCounter(self.path) if self.path else None
        self.last=-1
        self.lock=threading.Lock()
    def now(self):
        with self.lock:
            value=self.counter.read() if self.path else time.monotonic_ns()
            need(value>=self.last,'non-monotonic clock');self.last=value;return value

class VirtualCounter:
    """CPU-test only shared clock, serialized by a named Windows mutex."""
    def __init__(self,name):
        self.mapping=mmap.mmap(-1,8,tagname=name);self.value=ctypes.c_longlong.from_buffer(self.mapping)
        self.k=ctypes.WinDLL('kernel32',use_last_error=True)
        self.k.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p];self.k.CreateMutexW.restype=ctypes.c_void_p
        self.k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong];self.k.ReleaseMutex.argtypes=[ctypes.c_void_p]
        self.mutex=self.k.CreateMutexW(None,False,name+'-mutex');need(self.mutex,'virtual clock mutex')
    def access(self,value=None):
        need(self.k.WaitForSingleObject(self.mutex,1000)==0,'virtual clock mutex timeout')
        try:
            if value is not None:self.value.value=value
            return self.value.value
        finally:self.k.ReleaseMutex(self.mutex)
    def read(self):return self.access()
    def write(self,value):self.access(value)

class Coverage:
    """Conservative intervals, not instantaneous/fabricated resource samples.

    First completion-launch <=1s; each read <=1s; next completion-previous
    read START <=1s; live time/exit observation-last valid read START <=1s.
    Resource and directory reads are independent required streams.
    """
    def __init__(self,launch):
        self.launch=launch;self.streams={k:dict(last_begin=None,pending=None,completed=0) for k in ('resource','directory')}
    def event(self,row,exit_ns=None):
        kind=row.get('stream')
        if kind not in self.streams:return
        state=self.streams[kind];name=row['event']
        if name=='READ_BEGIN':
            need(state['pending'] is None,'overlapping '+kind+' read');state['pending']=row['begin_ns']
        elif name in ('READ_END','READ_DISCARDED','READ_ERROR'):
            begin,end=row['begin_ns'],row['end_ns'];need(state['pending']==begin and end>=begin,'read boundary identity')
            state['pending']=None
            if name=='READ_ERROR':raise ValueError(kind+' resource read failure: '+row['error'])
            if name=='READ_DISCARDED' or (exit_ns is not None and end>exit_ns):return
            need(end-begin<=MAX_GAP_NS,kind+' read duration >1s')
            anchor=state['last_begin'] if state['last_begin'] is not None else self.launch
            need(end-anchor<=MAX_GAP_NS,kind+' effective observation gap >1s')
            state['last_begin']=begin;state['completed']+=1
    def live(self,now):
        for kind,state in self.streams.items():
            anchor=state['last_begin'] if state['last_begin'] is not None else self.launch
            need(now-anchor<=MAX_GAP_NS,kind+' live observation gap >1s')
            if state['pending'] is not None:need(now-state['pending']<=MAX_GAP_NS,kind+' stalled read >1s')
    def terminal(self,exit_ns):
        for kind,state in self.streams.items():
            need(state['completed']>0,kind+' has no valid live sample')
            need(0<=exit_ns-state['last_begin']<=MAX_GAP_NS,kind+' terminal observation gap >1s')
        return {k:dict(valid_reads=s['completed'],last_read_begin_ns=s['last_begin'],terminal_gap_ns=exit_ns-s['last_begin']) for k,s in self.streams.items()}
