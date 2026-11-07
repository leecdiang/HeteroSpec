"""Serialize independently bounded GPU stages; never overlap native workers."""
import ctypes,time,sys,traceback
from build_host import ROOT,put
def main():
    kernel=ctypes.windll.kernel32;kernel.OpenProcess.restype=ctypes.c_void_p
    handle=kernel.OpenProcess(0x100000,False,int(sys.argv[1]))
    if handle:
        try:
            while kernel.WaitForSingleObject(ctypes.c_void_p(handle),2000)==258:pass
        finally:kernel.CloseHandle(ctypes.c_void_p(handle))
    import operator_matrix_host
    operator_matrix_host.main()
    import priming_host
    priming_host.main()
if __name__=='__main__':
    try:main()
    except BaseException as e:
        put(ROOT/('QUEUE_FAILURE-'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc()));raise
