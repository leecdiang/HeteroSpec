"""Actual loaded-module evidence; hashing never executes or initializes a backend."""
import ctypes
from ctypes import wintypes as W
from pathlib import Path
from common import need, sha

def modules(pid):
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
    k.CloseHandle.argtypes=[W.HANDLE]
    k.K32EnumProcessModules.argtypes=[W.HANDLE,ctypes.c_void_p,W.DWORD,ctypes.POINTER(W.DWORD)]
    k.K32GetModuleFileNameExW.argtypes=[W.HANDLE,W.HMODULE,W.LPWSTR,W.DWORD]
    h=k.OpenProcess(0x400|0x10,False,pid);need(h,'module process handle')
    try:
        a=(W.HMODULE*4096)();count=W.DWORD()
        need(k.K32EnumProcessModules(h,a,ctypes.sizeof(a),ctypes.byref(count)) and count.value<=ctypes.sizeof(a),'complete module enumeration')
        result=[]
        for entry in a[:count.value//ctypes.sizeof(W.HMODULE)]:
            path=ctypes.create_unicode_buffer(32768)
            size=k.K32GetModuleFileNameExW(h,entry,path,len(path));need(0<size<len(path)-1,'module path')
            p=Path(path.value).resolve();result.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
        return result
    finally:k.CloseHandle(h)

def verify_loaded(pid,expected,strict=True):
    actual=modules(pid);wanted={str(Path(x['path']).resolve()).lower():x['sha256'] for x in expected}
    found={x['path'].lower():x['sha256'] for x in actual}
    need(all(found.get(path)==value for path,value in wanted.items()),'required loaded module identity mismatch')
    if strict:need(set(found)==set(wanted),'unregistered loaded module')
    return dict(PID=pid,modules=actual,strict_complete_module_set=strict)
