"""OS read locks for own e04 inputs; old project/toolchain paths are never locked."""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import hashlib,json

ROOT=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx223-round1-resume-20261112-e04').resolve()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
class FreezeRefusal(RuntimeError):pass
def need(ok,message):
    if not ok:raise FreezeRefusal(message)
class ReadFreeze:
    def __init__(self,entries):self.entries=entries;self.handles=[]
    def __enter__(self):
        self.kernel=C.WinDLL('kernel32',use_last_error=True)
        self.kernel.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,C.c_void_p,W.DWORD,W.DWORD,W.HANDLE];self.kernel.CreateFileW.restype=W.HANDLE
        self.kernel.CloseHandle.argtypes=[W.HANDLE];self.kernel.CloseHandle.restype=W.BOOL
        try:
            for entry in self.entries:
                path=Path(entry['path']).resolve();need(path.is_relative_to(ROOT),'never lock old/outside-e04 input: '+str(path))
                handle=self.kernel.CreateFileW(str(path),0x80000000,0x1,None,3,0x80,None)
                need(handle not in (None,C.c_void_p(-1).value),'cannot read-freeze '+str(path)+' error '+str(C.get_last_error()))
                self.handles.append(handle)
                need(sha(path)==entry['sha256'],'input differs before locked freeze: '+str(path))
            return self
        except BaseException:self.__exit__(None,None,None);raise
    def __exit__(self,*args):
        for h in reversed(self.handles):self.kernel.CloseHandle(h)
        self.handles=[]
    def add(self,entry):
        path=Path(entry['path']).resolve();need(path.is_relative_to(ROOT),'generated input outside e04')
        h=self.kernel.CreateFileW(str(path),0x80000000,0x1,None,3,0x80,None);need(h not in (None,C.c_void_p(-1).value),'cannot freeze generated input')
        self.handles.append(h);need(sha(path)==entry['sha256'],'generated input hash differs')

def snapshot(paths):
    return [{'path':str(Path(p).resolve()),'bytes':Path(p).stat().st_size,'mtime_ns':Path(p).stat().st_mtime_ns,'sha256':sha(p)} for p in sorted(set(map(Path,paths)))]
def verify(entries):
    for e in entries:
        p=Path(e['path']);need(p.is_file() and p.stat().st_size==e['bytes'] and p.stat().st_mtime_ns==e['mtime_ns'] and sha(p)==e['sha256'],'frozen input changed: '+str(p))
def verify_manifest_identity(path,expected_sha256):
    need(isinstance(expected_sha256,str) and len(expected_sha256)==64 and all(c in '0123456789abcdef' for c in expected_sha256),'independent prepared-manifest SHA required')
    need(sha(path)==expected_sha256,'prepared manifest identity differs')
    value=json.loads(Path(path).read_bytes());verify(value['entries']);return value
