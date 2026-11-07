"""One real CPU-only host; reconcile Job accounting using actual PID events.

No GPU mode, plugin, device query or computation is invoked.
"""
import argparse,ctypes,subprocess,time
from ctypes import wintypes as W
from common import V,load,save,env
from cpu_job import Extended,Accounting
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--name',required=True);ap.add_argument('--detached',action='store_true');args=ap.parse_args()
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateJobObjectW.argtypes=[ctypes.c_void_p,W.LPCWSTR];k.CreateJobObjectW.restype=W.HANDLE
    k.CreateIoCompletionPort.argtypes=[W.HANDLE,W.HANDLE,ctypes.c_size_t,W.DWORD];k.CreateIoCompletionPort.restype=W.HANDLE
    k.SetInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD];k.AssignProcessToJobObject.argtypes=[W.HANDLE,W.HANDLE]
    k.QueryInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD,ctypes.c_void_p];k.CloseHandle.argtypes=[W.HANDLE]
    k.GetQueuedCompletionStatus.argtypes=[W.HANDLE,ctypes.POINTER(W.DWORD),ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_void_p),W.DWORD]
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE;k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,ctypes.POINTER(W.DWORD)]
    class Link(ctypes.Structure):_fields_=[('key',ctypes.c_void_p),('port',W.HANDLE)]
    job=k.CreateJobObjectW(None,None);port=k.CreateIoCompletionPort(W.HANDLE(-1),None,0,1);assert job and port
    link=Link(113,port);assert k.SetInformationJobObject(job,7,ctypes.byref(link),ctypes.sizeof(link))
    info=Extended();info.basic.flags=0x2000|8;info.basic.active=1;assert k.SetInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info))
    d=V/args.name;d.mkdir(exist_ok=False)
    command=[str(V/'lowering113_formal.exe'),'--cpu-one-wire',str(V/'CPU_FIXTURE/wires/000.json'),str(d/'NATIVE.json')]
    with (d/'stdout').open('xb') as out,(d/'stderr').open('xb') as err:
        flags=(8 if args.detached else 0x08000000)|4
        p=subprocess.Popen(command,env=env(load(V/'PLAN.json')['census_wire']['runtime_directory']),stdout=out,stderr=err,creationflags=flags)
        assert k.AssignProcessToJobObject(job,int(p._handle))
        n=ctypes.WinDLL('ntdll').NtResumeProcess;n.argtypes=[W.HANDLE];assert n(int(p._handle))==0
        events=[];begin=time.perf_counter()
        while time.perf_counter()-begin<5:
            msg=W.DWORD();key=ctypes.c_size_t();pid=ctypes.c_void_p()
            if k.GetQueuedCompletionStatus(port,ctypes.byref(msg),ctypes.byref(key),ctypes.byref(pid),100):
                event=dict(message=msg.value,key=key.value,pid=pid.value)
                if msg.value==6:
                    h=k.OpenProcess(0x1000,False,pid.value)
                    if h:
                        b=ctypes.create_unicode_buffer(32768);n=W.DWORD(len(b))
                        if k.QueryFullProcessImageNameW(h,0,b,ctypes.byref(n)):event['image']=b.value
                        k.CloseHandle(h)
                events.append(event)
                if msg.value==4 and p.poll() is not None:break
            if p.poll() is not None and time.perf_counter()-begin>.5:break
        code=p.wait(timeout=1);account=Accounting();assert k.QueryInformationJobObject(job,1,ctypes.byref(account),ctypes.sizeof(account),None)
    save(d/'ACCOUNTING.json',dict(command=command,creation_flags=flags,registered_PID=p.pid,exit_code=code,total_counter=account.total,active_counter=account.active,terminated_counter=account.terminated,
        events=events,NEW_PROCESS_unique_PIDs=sorted({e['pid'] for e in events if e['message']==6}),GPU_queries=0,CUDA_loads=0,graph_computes=0))
    k.CloseHandle(job);k.CloseHandle(port);assert code==0
    print('CPU PID/accounting receipt saved; no GPU work')
if __name__=='__main__':main()
