"""Retain process creation/exit times for ongoing calibration, without reruns."""
from native_host import *
import ctypes as ct,ctypes.wintypes as wt

def watch(pid,label):
 k=ct.WinDLL('kernel32',use_last_error=True)
 k.OpenProcess.argtypes=[wt.DWORD,wt.BOOL,wt.DWORD];k.OpenProcess.restype=wt.HANDLE
 k.WaitForSingleObject.argtypes=[wt.HANDLE,wt.DWORD];k.WaitForSingleObject.restype=wt.DWORD
 k.GetProcessTimes.argtypes=[wt.HANDLE,*([ct.POINTER(wt.FILETIME)]*4)];k.GetProcessTimes.restype=wt.BOOL
 k.CloseHandle.argtypes=[wt.HANDLE]
 h=k.OpenProcess(0x101000,False,pid);assert h,'Expected live study process'
 try:
  while k.WaitForSingleObject(h,1000)==258:pass
  values=[wt.FILETIME() for _ in range(4)];assert k.GetProcessTimes(h,*[ct.byref(v) for v in values])
  a,b,kernel,user=[(v.dwHighDateTime<<32)|v.dwLowDateTime for v in values]
  stamp=lambda x:datetime.datetime.fromtimestamp((x-116444736000000000)/1e7,datetime.timezone.utc).isoformat()
  write(ROOT/'driver-costs'/(label+'.json'),dict(pid=pid,creation_utc=stamp(a),exit_utc=stamp(b),wall_seconds=(b-a)/1e7,parent_kernel_seconds=kernel/1e7,parent_user_seconds=user/1e7,children_charged_in_supervisor_receipts=True,model_requests=0,method='Windows process lifetime; opened live process object before exit',waiting_intervals_may_overlap=True))
 finally:k.CloseHandle(h)

if __name__=='__main__':watch(int(sys.argv[1]),sys.argv[2])
