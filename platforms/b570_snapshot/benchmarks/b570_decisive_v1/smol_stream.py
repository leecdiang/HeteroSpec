"""Bounded offline state packing; never read a writer's unfinished snapshot."""
from pathlib import Path
import ctypes as c,ctypes.wintypes as w,struct,threading,time,json

K=c.WinDLL('kernel32',use_last_error=True)
K.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE];K.CreateFileW.restype=w.HANDLE
K.CloseHandle.argtypes=[w.HANDLE];K.CloseHandle.restype=w.BOOL

def complete_closed(p):
 # Denying write sharing conflicts with an existing native writer handle.
 h=K.CreateFileW(str(p),0x80000000,1,None,3,0,None)
 if h==c.c_void_p(-1).value:return False
 K.CloseHandle(h)
 with p.open('rb') as f:header=f.read(16)
 if len(header)!=16:return False
 magic,seq,streams,n=struct.unpack('<IiII',header)
 return magic==0xaf143cd8 and seq==0 and streams==1 and 0<n<=1024 and p.stat().st_size==600+196620*n

class StateStream:
 def __init__(self,folder,pack):
  self.folder=Path(folder);self.pack=pack;self.stop=threading.Event();self.error=None;self.count=0;self.seconds=0
  self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
 def scan(self):
  for p in sorted(self.folder.glob('*.json.states/*.bin')):
   if complete_closed(p):
    t=time.monotonic();self.pack(p);self.seconds+=time.monotonic()-t;self.count+=1
 def run(self):
  try:
   while not self.stop.is_set():self.scan();self.stop.wait(.1)
   self.scan()
  except BaseException as e:self.error=type(e).__name__+': '+str(e)
 def finish(self):
  started=time.monotonic();self.stop.set();self.thread.join(timeout=300)
  result=dict(complete_states_packed=self.count,packing_seconds=self.seconds,post_native_drain_seconds=time.monotonic()-started,overlaps_diagnostic_native=True,additive_to_native_wall=False,thread_stopped=not self.thread.is_alive(),error=self.error,incomplete_files_never_packed=True)
  with (self.folder/'STREAM_STORAGE.json').open('x') as f:json.dump(result,f,indent=2)
  if self.thread.is_alive() or self.error:raise RuntimeError('Offline streaming storage did not complete: '+str(result))
