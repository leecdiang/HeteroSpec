"""CPU-only Win32 primitives; FILETIME is always serialized as decimal strings."""
import ctypes as C
from ctypes import wintypes as W
import hashlib,json,os,subprocess,time,sys
from pathlib import Path
K=C.WinDLL('kernel32',use_last_error=True)
N=C.WinDLL('ntdll',use_last_error=True)
P=C.WinDLL('psapi',use_last_error=True)
U=C.c_size_t
now=time.perf_counter_ns
class FT(C.Structure):_fields_=[('low',W.DWORD),('high',W.DWORD)]
class CPI(C.Structure):_fields_=[('file',W.HANDLE),('process',W.HANDLE),('thread',W.HANDLE),('base',C.c_void_p),('offset',W.DWORD),('size',W.DWORD),('tls',C.c_void_p),('start',C.c_void_p),('image',C.c_void_p),('unicode',W.WORD)]
class CTI(C.Structure):_fields_=[('thread',W.HANDLE),('tls',C.c_void_p),('start',C.c_void_p)]
class LDI(C.Structure):_fields_=[('file',W.HANDLE),('base',C.c_void_p),('offset',W.DWORD),('size',W.DWORD),('name',C.c_void_p),('unicode',W.WORD)]
class ER(C.Structure):_fields_=[('code',W.DWORD),('flags',W.DWORD),('record',C.c_void_p),('address',C.c_void_p),('count',W.DWORD),('information',U*15)]
class EI(C.Structure):_fields_=[('record',ER),('first_chance',W.DWORD)]
class DU(C.Union):_fields_=[('create',CPI),('thread',CTI),('dll',LDI),('exception',EI),('code',W.DWORD),('raw',C.c_ubyte*160)]
class DE(C.Structure):_fields_=[('event',W.DWORD),('pid',W.DWORD),('tid',W.DWORD),('u',DU)]
class PBI(C.Structure):_fields_=[('r1',C.c_void_p),('peb',C.c_void_p),('r2',C.c_void_p*2),('pid',U),('parent',U)]
class US(C.Structure):_fields_=[('length',W.USHORT),('maximum',W.USHORT),('buffer',C.c_void_p)]
class BASIC(C.Structure):_fields_=[('process_time',C.c_longlong),('job_time',C.c_longlong),('flags',W.DWORD),('min',U),('max',U),('active',W.DWORD),('affinity',U),('priority',W.DWORD),('scheduling',W.DWORD)]
class IO(C.Structure):_fields_=[('read_ops',C.c_ulonglong),('write_ops',C.c_ulonglong),('other_ops',C.c_ulonglong),('read_bytes',C.c_ulonglong),('write_bytes',C.c_ulonglong),('other_bytes',C.c_ulonglong)]
class LIMIT(C.Structure):_fields_=[('basic',BASIC),('io',IO),('process_memory',U),('job_memory',U),('peak_process',U),('peak_job',U)]
class SI(C.Structure):_fields_=[('cb',W.DWORD),('reserved',W.LPWSTR),('desktop',W.LPWSTR),('title',W.LPWSTR),('x',W.DWORD),('y',W.DWORD),('xs',W.DWORD),('ys',W.DWORD),('xc',W.DWORD),('yc',W.DWORD),('fill',W.DWORD),('flags',W.DWORD),('show',W.WORD),('reserved_size',W.WORD),('reserved_bytes',C.c_void_p),('stdin',W.HANDLE),('stdout',W.HANDLE),('stderr',W.HANDLE)]
class PI(C.Structure):_fields_=[('process',W.HANDLE),('thread',W.HANDLE),('pid',W.DWORD),('tid',W.DWORD)]
class SA(C.Structure):_fields_=[('length',W.DWORD),('descriptor',C.c_void_p),('inherit',W.BOOL)]
class MEMORY(C.Structure):_fields_=[('cb',W.DWORD),('faults',W.DWORD),('peak_ws',U),('working_set',U),('peak_paged',U),('paged',U),('peak_nonpaged',U),('nonpaged',U),('pagefile',U),('peak_pagefile',U),('private',U)]
def api(lib,name,args,result=W.BOOL):
    f=getattr(lib,name);f.argtypes=args;f.restype=result;return f
close=api(K,'CloseHandle',[W.HANDLE])
current=api(K,'GetCurrentProcess',[],W.HANDLE)
times=api(K,'GetProcessTimes',[W.HANDLE,C.POINTER(FT),C.POINTER(FT),C.POINTER(FT),C.POINTER(FT)])
wait_handle=api(K,'WaitForSingleObject',[W.HANDLE,W.DWORD],W.DWORD)
duplicate=api(K,'DuplicateHandle',[W.HANDLE,W.HANDLE,W.HANDLE,C.POINTER(W.HANDLE),W.DWORD,W.BOOL,W.DWORD])
wait_debug=api(K,'WaitForDebugEvent',[C.POINTER(DE),W.DWORD])
continue_debug=api(K,'ContinueDebugEvent',[W.DWORD,W.DWORD,W.DWORD])
query_image=api(K,'QueryFullProcessImageNameW',[W.HANDLE,W.DWORD,W.LPWSTR,C.POINTER(W.DWORD)])
query_path=api(K,'GetFinalPathNameByHandleW',[W.HANDLE,W.LPWSTR,W.DWORD,W.DWORD],W.DWORD)
job_create=api(K,'CreateJobObjectW',[C.c_void_p,W.LPCWSTR],W.HANDLE)
job_set=api(K,'SetInformationJobObject',[W.HANDLE,C.c_int,C.c_void_p,W.DWORD])
job_query=api(K,'QueryInformationJobObject',[W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.POINTER(W.DWORD)])
job_assign=api(K,'AssignProcessToJobObject',[W.HANDLE,W.HANDLE])
job_kill=api(K,'TerminateJobObject',[W.HANDLE,W.UINT])
terminate_process=api(K,'TerminateProcess',[W.HANDLE,W.UINT])
open_process=api(K,'OpenProcess',[W.DWORD,W.BOOL,W.DWORD],W.HANDLE)
get_exit=api(K,'GetExitCodeProcess',[W.HANDLE,C.POINTER(W.DWORD)])
resume=api(K,'ResumeThread',[W.HANDLE],W.DWORD)
create_process=api(K,'CreateProcessW',[W.LPCWSTR,W.LPWSTR,C.c_void_p,C.c_void_p,W.BOOL,W.DWORD,C.c_void_p,W.LPCWSTR,C.POINTER(SI),C.POINTER(PI)])
create_file=api(K,'CreateFileW',[W.LPCWSTR,W.DWORD,W.DWORD,C.POINTER(SA),W.DWORD,W.DWORD,W.HANDLE],W.HANDLE)
memory_info=api(P,'GetProcessMemoryInfo',[W.HANDLE,C.POINTER(MEMORY),W.DWORD])
N.NtQueryInformationProcess.argtypes=[W.HANDLE,C.c_int,C.c_void_p,W.ULONG,C.POINTER(W.ULONG)];N.NtQueryInformationProcess.restype=W.LONG
assert C.sizeof(ER)==152 and EI.first_chance.offset==152 and C.sizeof(EI)==160
assert C.sizeof(DE)==176 and C.sizeof(SI)==104 and C.sizeof(PI)==24
def need(value,message):
    if not value:raise RuntimeError(message)
def checked(value,name):
    if not value:raise C.WinError(C.get_last_error())
    return value
def os_times(h):
    a,b,c,d=FT(),FT(),FT(),FT();checked(times(h,C.byref(a),C.byref(b),C.byref(c),C.byref(d)),'GetProcessTimes')
    return dict(created_filetime=str((a.high<<32)|a.low),exit_filetime=str((b.high<<32)|b.low),kernel_100ns=str((c.high<<32)|c.low),user_100ns=str((d.high<<32)|d.low))
def identity(h):
    b=C.create_unicode_buffer(32768);n=W.DWORD(len(b));checked(query_image(h,0,b,C.byref(n)),'QueryFullProcessImageNameW')
    p=PBI();needed=W.ULONG();need(N.NtQueryInformationProcess(h,0,C.byref(p),C.sizeof(p),C.byref(needed))>=0,'parent query')
    N.NtQueryInformationProcess(h,60,None,0,C.byref(needed));buf=C.create_string_buffer(max(needed.value,1024))
    need(N.NtQueryInformationProcess(h,60,buf,len(buf),C.byref(needed))>=0,'command query')
    s=US.from_buffer(buf);command=C.wstring_at(s.buffer,s.length//2) if s.buffer else ''
    return dict(image=b.value,parent_pid=int(p.parent),command=command,command_sha256=hashlib.sha256(command.encode()).hexdigest(),**os_times(h))
def retain(h):
    out=W.HANDLE();checked(duplicate(current(),h,current(),C.byref(out),0,False,2),'DuplicateHandle');return out
def alive(h):
    r=wait_handle(h,0);need(r in (0,258),'process wait failure');return r==258
def exit_code(h):
    out=W.DWORD();checked(get_exit(h,C.byref(out)),'GetExitCodeProcess');return out.value
def rss(h):
    out=MEMORY();out.cb=C.sizeof(out);checked(memory_info(h,C.byref(out),C.sizeof(out)),'GetProcessMemoryInfo');return int(out.working_set)
def make_job():
    j=checked(job_create(None,None),'CreateJobObject');lim=LIMIT();lim.basic.flags=0x2000
    try:checked(job_set(j,9,C.byref(lim),C.sizeof(lim)),'SetInformationJobObject');return j
    except BaseException:close(j);raise
def job_pids(j):
    buf=C.create_string_buffer(16+4096*8);checked(job_query(j,3,buf,len(buf),None),'QueryInformationJobObject(PIDs)')
    count=C.c_uint32.from_buffer(buf,4).value;need(count<=4096,'job PID capacity')
    return list((U*count).from_buffer(buf,8))
def terminate_job(j):checked(job_kill(j,124),'TerminateJobObject')
def spawn_suspended(argv,cwd,stdout,stderr):
    sa=SA(C.sizeof(SA),None,True);handles=[];p=PI();failure=None;created=False
    try:
        for name,access,disposition in [('NUL',0x80000000,3),(str(stdout),0x40000000,1),(str(stderr),0x40000000,1)]:
            h=create_file(name,access,1,C.byref(sa),disposition,128,None);need(h not in (None,C.c_void_p(-1).value),'CreateFileW');handles.append(h)
        si=SI();si.cb=C.sizeof(si);si.flags=0x100;si.stdin,si.stdout,si.stderr=handles
        command=C.create_unicode_buffer(subprocess.list2cmdline(argv))
        checked(create_process(argv[0],command,None,None,True,0x0000000c,None,str(cwd),C.byref(si),C.byref(p)),'CreateProcessW');created=True
    except BaseException as e:failure=repr(e)
    finally:
        for h in handles:
            if not close(h):failure=(failure or '')+' stdio CloseHandle failure '+str(C.get_last_error())
    if failure:
        disposition=None
        if created:
            if alive(p.process):checked(terminate_process(p.process,125),'cleanup unreturned process')
            need(wait_handle(p.process,5000)==0,'UNRETURNED_CHILD_CLEANUP_UNCONFIRMED');disposition=dict(pid=int(p.pid),exit_code=exit_code(p.process),**os_times(p.process));need(int(disposition['exit_filetime'])>0,'unreturned child exit time')
            checked(close(p.thread),'close unreturned child thread');checked(close(p.process),'close unreturned child process')
        raise RuntimeError(json.dumps(dict(error=failure,created_child_cleanup=disposition)))
    return p

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump_new(path,data):
    path=Path(path)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def atomic(path,data):
    path=Path(path);temp=path.with_name(path.name+'.tmp')
    with temp.open('w',encoding='utf-8',newline='\n') as f:json.dump(data,f,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(temp,path)
class Journal:
    def __init__(self,path,cap=128*1024**2):self.path=Path(path);self.f=self.path.open('xb',buffering=0);self.seq=0;self.bytes=0;self.cap=cap
    def emit(self,event,**kw):
        self.seq+=1;r=dict(event=event,seq=self.seq,at_ns=now(),writer_pid=os.getpid(),**kw);b=(json.dumps(r,sort_keys=True,allow_nan=False)+'\n').encode();need(self.bytes+len(b)<=self.cap,'journal limit');need(self.f.write(b)==len(b),'short journal write');os.fsync(self.f.fileno());self.bytes+=len(b);return r
    def end(self):self.f.flush();os.fsync(self.f.fileno());self.f.close()
def inventory(root):
    result=dict(files=0,directories=0,logical_bytes=0,allocation_upper_bytes=0)
    def fail_scan(error):raise error
    for parent,dirs,files in os.walk(root,followlinks=False,onerror=fail_scan):
        result['directories']+=len(dirs);result['allocation_upper_bytes']+=len(dirs)*4096
        for name in dirs+files:
            p=Path(parent,name);need(not p.is_symlink() and not p.is_junction(),'task alias')
        for name in files:
            n=Path(parent,name).stat().st_size;result['files']+=1;result['logical_bytes']+=n;result['allocation_upper_bytes']+=((n+4095)//4096)*4096+1024
    return result
def check_root(root):
    root=Path(root).resolve();need(root.parent==Path('C:/hs/b570-capability-v1').resolve(),'explicit fresh capability root');return root
from guards import FrozenBaseline
_FREEZE = None
def freeze_check(root, expected):
    global _FREEZE
    if _FREEZE is None:_FREEZE=FrozenBaseline(root,expected)
    need(_FREEZE.root==Path(root).resolve() and _FREEZE.expected==expected,"FREEZE_BASELINE_CHANGED")
    _FREEZE.check()
    f=json.loads((root/'CAPABILITY_FREEZE.json').read_text());source='src/rev2'
    required={source+'/'+n for n in ['win.py','actor.py','supervisor.py','watchdog.py','verify.py','history.py','guards.py','exception_policy.py']}|{'CONFIG.json'}|{'acquisition/'+n for n in ['PROTOCOL.md','B570_PROMPT.md','REVIEW_BINDING.json','review/REPORT.json','review/STATUS.json']}
    need(f.get('source_relative')==source and required<=set(f.get('files',{})),'INCOMPLETE_FREEZE_INVENTORY')
    need(Path(__file__).resolve().parent==(root/source).resolve(),'RUNTIME_SOURCE_PATH')
    for p,h in f['files'].items():
        need(not Path(p).is_absolute() and '..' not in Path(p).parts and ':' not in p,'freeze member path');need(sha(root/p)==h,'SOURCE_DRIFT')
    approved=Path('C:/Users/DIANG/AppData/Local/Programs/Python/Python312/python.exe').resolve()
    need(Path(f['python']).resolve()==approved==Path(sys.executable).resolve(),'EXECUTING_PYTHON_PATH');need(sha(approved)==f['python_sha256'],'PYTHON_DRIFT');return f
