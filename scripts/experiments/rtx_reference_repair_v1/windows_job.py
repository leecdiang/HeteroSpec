"""Windows Job ownership; no work at import time. Derived from PR155, with wait-empty cleanup."""
import ctypes,time
from common import need

class Job:
    """Kill-on-close Windows Job; assigned while native waits for host RUN."""
    def __init__(self,process):
        from ctypes import wintypes as w
        self.k=ctypes.WinDLL('kernel32',use_last_error=True)
        self.k.CreateJobObjectW.restype=w.HANDLE;self.k.CreateJobObjectW.argtypes=[ctypes.c_void_p,w.LPCWSTR]
        self.k.SetInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD]
        self.k.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE]
        self.k.CloseHandle.argtypes=[w.HANDLE]
        self.k.TerminateJobObject.argtypes=[w.HANDLE,w.UINT]
        self.k.QueryInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD,ctypes.c_void_p]
        class BASIC(ctypes.Structure):
            _fields_=[('p',ctypes.c_longlong),('j',ctypes.c_longlong),('flags',w.DWORD),
                      ('minws',ctypes.c_size_t),('maxws',ctypes.c_size_t),('active',w.DWORD),
                      ('affinity',ctypes.c_size_t),('priority',w.DWORD),('sched',w.DWORD)]
        class IO(ctypes.Structure):_fields_=[(k,ctypes.c_ulonglong) for k in ('r','w','o','rb','wb','ob')]
        class EXT(ctypes.Structure):
            _fields_=[('basic',BASIC),('io',IO),('pm',ctypes.c_size_t),('jm',ctypes.c_size_t),('ppm',ctypes.c_size_t),('pjm',ctypes.c_size_t)]
        self.handle=self.k.CreateJobObjectW(None,None);need(self.handle,'CreateJobObject')
        x=EXT();x.basic.flags=0x2000
        try:
            need(self.k.SetInformationJobObject(self.handle,9,ctypes.byref(x),ctypes.sizeof(x)), 'SetInformationJobObject')
            need(self.k.AssignProcessToJobObject(self.handle,w.HANDLE(int(process._handle))), 'AssignProcessToJobObject')
        except BaseException:
            self.k.CloseHandle(self.handle);self.handle=None;raise
    def active(self):
        from ctypes import wintypes as w
        class ACCOUNT(ctypes.Structure):
            _fields_=[('u',ctypes.c_longlong),('k',ctypes.c_longlong),('pu',ctypes.c_longlong),('pk',ctypes.c_longlong),
                      ('faults',w.DWORD),('total',w.DWORD),('active',w.DWORD),('terminated',w.DWORD)]
        x=ACCOUNT();need(self.k.QueryInformationJobObject(self.handle,1,ctypes.byref(x),ctypes.sizeof(x),None),'Job accounting')
        return x.active
    def terminate(self):
        if self.handle:need(self.k.TerminateJobObject(self.handle,3),'job termination failed')
    def wait_empty(self,timeout=10):
        end=time.monotonic()+timeout
        while True:
            active=self.active()
            if active==0 or time.monotonic()>=end:return active
            time.sleep(.05)
    def close(self):
        if self.handle:self.k.CloseHandle(self.handle);self.handle=None

def available_ram():
    class MEM(ctypes.Structure):
        _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(x,ctypes.c_ulonglong) for x in ('total','available','page','apage','virtual','avirtual','extended')]
    m=MEM();m.length=ctypes.sizeof(m)
    need(ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)),'RAM query')
    return int(m.available)
