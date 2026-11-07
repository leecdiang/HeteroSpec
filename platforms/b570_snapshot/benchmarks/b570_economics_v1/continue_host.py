"""Serial continuation of the already-running A1 qualification, no GPU overlap."""
from native_host import *
import ctypes as ct

def main(pid):
 k=ct.WinDLL('kernel32',use_last_error=True)
 k.OpenProcess.argtypes=[ct.c_ulong,ct.c_int,ct.c_ulong];k.OpenProcess.restype=ct.c_void_p
 k.WaitForSingleObject.argtypes=[ct.c_void_p,ct.c_ulong];k.WaitForSingleObject.restype=ct.c_ulong
 k.CloseHandle.argtypes=[ct.c_void_p]
 handle=k.OpenProcess(0x100000,False,pid);assert handle,'Running A1 owner required'
 try:
  while k.WaitForSingleObject(handle,1000)==258:
   if (ROOT/'A1_QUALIFIED.json').exists():break
 finally:k.CloseHandle(handle)
 assert (ROOT/'A1_QUALIFIED.json').exists(),'A1 failed; retained failure, no dependent experiment started'
 assert not LOCK.exists()
 for epoch in ('resident03','parallel02'):
  for arm in ('M','H1','C4U4','C4U1'):
   for mode in (0,1):assert (ROOT/epoch/f'{arm}-mode{mode}'/'FILES.json').exists()
 from campaign_host import a1_timing
 from costs_host import a1
 from resident_campaign import qualification
 print('START_FIXED_A1_TIMING',flush=True);a1_timing();a1()
 print('START_RESIDENT_QUALIFICATION',flush=True);qualification('resident')
 print('A1_AND_RESIDENT_QUALIFICATION_FINISHED',flush=True)

if __name__=='__main__':main(int(sys.argv[1]))
