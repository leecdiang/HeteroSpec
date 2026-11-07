import ctypes,uuid,time
from ctypes import wintypes as W
from common import V,save,pin,env
from readiness_policy import validate_observation
import identity as analyzer

def owned_conflicts(f0):
    # Pure OS process metadata, not a device/backend query.
    ps=ctypes.WinDLL('psapi');k=ctypes.WinDLL('kernel32',use_last_error=True)
    ps.EnumProcesses.argtypes=[ctypes.POINTER(W.DWORD),W.DWORD,ctypes.POINTER(W.DWORD)]
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
    k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,ctypes.POINTER(W.DWORD)];k.CloseHandle.argtypes=[W.HANDLE]
    ids=(W.DWORD*16384)();needed=W.DWORD();assert ps.EnumProcesses(ids,ctypes.sizeof(ids),ctypes.byref(needed))
    assert needed.value<ctypes.sizeof(ids),'process inventory overflow'
    forbidden={analyzer.norm(p) for p in f0['conflicting_owned_executables']}
    for pid in ids[:needed.value//4]:
        h=k.OpenProcess(0x1000,False,pid)
        if not h:continue
        try:
            buf=ctypes.create_unicode_buffer(32768);n=W.DWORD(len(buf))
            if k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(n)):assert analyzer.norm(buf.value) not in forbidden,'conflicting owned native process'
        finally:k.CloseHandle(h)

def module_inventory(paths,f0):
    frozen={analyzer.norm(p['path']):p for p in f0['files']};rows=[]
    for path in sorted(set(paths)):
        p=pin(path);assert analyzer.norm(path) in frozen,'new unregistered loaded module: terminal, no runtime inheritance'
        assert p['sha256']==frozen[analyzer.norm(path)]['sha256'];rows.append(p)
    return rows

class Power(ctypes.Structure):
    _fields_=[('AC',ctypes.c_ubyte),('flags',ctypes.c_ubyte),('percent',ctypes.c_ubyte),('system',ctypes.c_ubyte),('life',W.DWORD),('full',W.DWORD)]

def readiness(worker,d,f0,guard,on_start=lambda pid:None):
    policy=f0['admission_policy'];command=[policy['nvidia_smi'],'--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu','--format=csv,noheader,nounits']
    save(d/'READINESS_STARTED.json',dict(command=command,epoch=time.time(),attempts=1))
    worker.run(command,d/'readiness',10,env(f0['runtime_directory']),f0['budget']['limits']['readiness_process_commit_bytes'],guard,on_start=on_start)
    lines=(d/'readiness.stdout').read_text().strip().splitlines();assert len(lines)==1
    fields=[s.strip() for s in lines[0].split(',')];assert len(fields)==6
    name,driver,total,used,util,temp=fields
    power=Power();assert ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(power))
    pp=ctypes.WinDLL('powrprof');pp.PowerGetActiveScheme.argtypes=[W.HANDLE,ctypes.POINTER(ctypes.c_void_p)];guid=ctypes.c_void_p()
    assert pp.PowerGetActiveScheme(None,ctypes.byref(guid))==0
    try:scheme=str(uuid.UUID(bytes_le=ctypes.string_at(guid,16)))
    finally:
        k=ctypes.WinDLL('kernel32');k.LocalFree.argtypes=[W.HLOCAL];k.LocalFree(guid)
    result=dict(gpu=name,driver=driver,total_MiB=float(total),used_MiB=float(used),util=float(util),temperature_C=float(temp),AC=power.AC,power_scheme_guid=scheme)
    save(d/'ADMISSION.json',result)
    assert (name,driver,float(total))==(policy['gpu'],policy['driver'],policy['total_MiB'])
    decision=validate_observation(result,policy)
    save(d/'READINESS_DECISION.json',decision)
