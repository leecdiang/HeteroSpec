"""Read-only Toolhelp process and lock/ledger evidence; no CUDA calls."""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import json,hashlib,datetime,subprocess,os

HERE=Path(__file__).resolve().parent
K=C.WinDLL('kernel32',use_last_error=True)
class PE(C.Structure):
    _fields_=[('dwSize',W.DWORD),('cntUsage',W.DWORD),('pid',W.DWORD),('heap',C.c_size_t),('module',W.DWORD),('threads',W.DWORD),('ppid',W.DWORD),('priority',W.LONG),('flags',W.DWORD),('name',W.WCHAR*260)]
K.CreateToolhelp32Snapshot.argtypes=[W.DWORD,W.DWORD];K.CreateToolhelp32Snapshot.restype=W.HANDLE
K.Process32FirstW.argtypes=[W.HANDLE,C.POINTER(PE)];K.Process32FirstW.restype=W.BOOL
K.Process32NextW.argtypes=[W.HANDLE,C.POINTER(PE)];K.Process32NextW.restype=W.BOOL
K.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];K.OpenProcess.restype=W.HANDLE
K.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,C.POINTER(W.DWORD)];K.QueryFullProcessImageNameW.restype=W.BOOL
K.CloseHandle.argtypes=[W.HANDLE];K.CloseHandle.restype=W.BOOL
K.GetProcessTimes.argtypes=[W.HANDLE,C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME)];K.GetProcessTimes.restype=W.BOOL

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def process_inventory():
    result={'observed_utc':now(),'method':'Windows Toolhelp32 snapshot + QueryFullProcessImageNameW + GetProcessTimes','pid':os.getpid(),'rows':[]}
    snap=K.CreateToolhelp32Snapshot(2,0)
    if snap==C.c_void_p(-1).value or not snap:
        result['snapshot_error']=C.get_last_error();return result
    try:
        e=PE();e.dwSize=C.sizeof(e)
        ok=K.Process32FirstW(snap,C.byref(e))
        result['first_error']=None if ok else C.get_last_error()
        while ok:
            item={'pid':e.pid,'ppid':e.ppid,'name':e.name,'threads':e.threads}
            h=K.OpenProcess(0x1000,False,e.pid)
            if h:
                try:
                    buff=C.create_unicode_buffer(32768);n=W.DWORD(len(buff))
                    if K.QueryFullProcessImageNameW(h,0,buff,C.byref(n)):item['image']=buff.value
                    else:item['image_error']=C.get_last_error()
                    ft=[W.FILETIME() for _ in range(4)]
                    if K.GetProcessTimes(h,*[C.byref(t) for t in ft]):
                        t=((ft[0].dwHighDateTime<<32)+ft[0].dwLowDateTime)/10000000-11644473600
                        item['created_utc']=datetime.datetime.fromtimestamp(t,datetime.timezone.utc).isoformat()
                finally:K.CloseHandle(h)
            else:item['open_error']=C.get_last_error()
            result['rows'].append(item)
            ok=K.Process32NextW(snap,C.byref(e))
        result['last_error']=C.get_last_error()
    finally:K.CloseHandle(snap)
    return result

inv=process_inventory();(HERE/'private/TOOLHELP_PROCESSES.json').write_text(json.dumps(inv,indent=2),encoding='utf8')
keys=('worker','llama','nvcc','python','zig','codex','opencode','cmake','ninja')
rel=[r for r in inv.get('rows',[]) if any(k in r['name'].lower() for k in keys)]
locks=[Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock'),HERE.parents[2]/'rtx221-round1-20261112/resources/WINDOWS_RTX_EPOCH.lock']
lock_records=[]
for p in locks:
    r={'path':str(p),'exists':p.exists()}
    if p.exists():r.update(bytes=p.stat().st_size,mtime_utc=datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),sha256=sha(p));r['contents']=p.read_text(encoding='utf8',errors='replace')[:4096]
    lock_records.append(r)
ledgers=[Path('D:/rtx192-review-v2/ledger.sqlite'),Path('D:/rtx211-q8-20261109/ledger.sqlite'),HERE.parents[2]/'q8rtx213-supplement-runtime-20261109/ledger.sqlite',HERE.parents[2]/'rtx221-round1-20261112/resources/ledger.sqlite']
receipt={'observed_utc':now(),'process_probe':{'snapshot_error':inv.get('snapshot_error'),'first_error':inv.get('first_error'),'total_processes':len(inv.get('rows',[])),'relevant':rel},'locks':lock_records,'ledger_hashes':[{'path':str(p),'exists':p.exists(),'sha256':sha(p) if p.exists() else None} for p in ledgers],'nvidia_smi':[],'new_GPU_work':0,'gpu_idle_is_not_thread_completion':True}
for args in (['nvidia-smi','--query-gpu=index,uuid,name,memory.total,memory.used,driver_version','--format=csv'],['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv']):
    r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    receipt['nvidia_smi'].append({'argv':args,'code':r.returncode,'stdout':r.stdout.decode('utf8',errors='replace')})
(HERE/'PROCESS_LOCK_LEDGER.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps(receipt,indent=2,ensure_ascii=True))
