"""Windows process identity/resource APIs only. No GPU API or loader."""
import ctypes
from ctypes import wintypes

K=ctypes.WinDLL('kernel32',use_last_error=True)
K.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];K.OpenProcess.restype=wintypes.HANDLE
K.CloseHandle.argtypes=[wintypes.HANDLE]
K.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
K.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.c_void_p]*4

class Target:
    def __init__(self,pid,handle=None):
        self.handle=handle if handle is not None else K.OpenProcess(0x1000|0x10,False,pid)
        self.owned=handle is None
        if not self.handle:raise ctypes.WinError(ctypes.get_last_error())
    def active(self):
        code=wintypes.DWORD()
        if not K.GetExitCodeProcess(self.handle,ctypes.byref(code)):raise ctypes.WinError(ctypes.get_last_error())
        # Production child returns0/50 or an OS failure, never STILL_ACTIVE259.
        return code.value==259
    def times(self):
        v=[ctypes.c_ulonglong() for _ in range(4)]
        if not K.GetProcessTimes(self.handle,*[ctypes.byref(x) for x in v]):raise ctypes.WinError(ctypes.get_last_error())
        return dict(creation_FILETIME=v[0].value,exit_FILETIME=v[1].value,kernel_100ns=v[2].value,user_100ns=v[3].value,
            scope='FILETIME evidence only; never used for monotonic monitor intervals')
    def rss(self):
        class Memory(ctypes.Structure):
            _fields_=[('cb',wintypes.DWORD),('faults',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ('peak_ws','ws','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile')]
        m=Memory();m.cb=ctypes.sizeof(m);K.K32GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD]
        if not K.K32GetProcessMemoryInfo(self.handle,ctypes.byref(m),ctypes.sizeof(m)):raise ctypes.WinError(ctypes.get_last_error())
        return m.ws
    def close(self):
        if self.owned:K.CloseHandle(self.handle);self.owned=False
