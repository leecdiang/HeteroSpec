"""Serial development continuation; a failure preserves receipts and stops dependents."""
from native_host import *
import ctypes as ct

def main(pid):
 k=ct.WinDLL('kernel32',use_last_error=True)
 k.OpenProcess.argtypes=[ct.c_ulong,ct.c_int,ct.c_ulong];k.OpenProcess.restype=ct.c_void_p
 k.WaitForSingleObject.argtypes=[ct.c_void_p,ct.c_ulong];k.WaitForSingleObject.restype=ct.c_ulong
 k.CloseHandle.argtypes=[ct.c_void_p]
 h=k.OpenProcess(0x100000,False,pid)
 if h:
  try:
   while k.WaitForSingleObject(h,1000)==258:
    if (ROOT/'RESIDENT_QUALIFIED.json').exists():break
  finally:k.CloseHandle(h)
 assert (ROOT/'RESIDENT_QUALIFIED.json').exists(),'Resident qualification failed; no dependent work'
 from resident_campaign import qualification,diagnostics,synchronized,pilot
 from probe_host import known,caps,branches
 from decision_host import decide
 steps=[('RESIDENT_COST_AND_WORK',diagnostics,('resident',)),('RESIDENT_BLOCKING',synchronized,('resident',)),('RESIDENT_CLEAN_PILOT',pilot,('resident',)),('PARALLEL_QUALIFICATION',qualification,('parallel',)),('KNOWN_TOKEN_MECHANISMS',known,()),('CAP1_CONTRACT',caps,()),('K3_PROTOCOL_ONLY',branches,()),('PARALLEL_COST_AND_WORK',diagnostics,('parallel',)),('PARALLEL_BLOCKING',synchronized,('parallel',)),('PARALLEL_CLEAN_PILOT',pilot,('parallel',)),('DEVELOPMENT_GATE',decide,())]
 for label,fn,args in steps:
  print('DEVELOPMENT_STEP_START',label,flush=True);fn(*args);print('DEVELOPMENT_STEP_PASS',label,flush=True)
 print('DEVELOPMENT_COMPLETE_NO_BLIND_OUTPUTS_STARTED',flush=True)

if __name__=='__main__':main(int(sys.argv[1]))
