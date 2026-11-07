import sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from live_budget import anchor, elapsed, OuterBudget
from cold_state import initialize, ready_receipt
"""Outer CPU-only command broker. DEBUG_PROCESS observes every descendant at creation.

Process handles are duplicated before ContinueDebugEvent; OS exit times are read
only after the duplicate signals. The broker is directly observed by the existing Node tool service.
"""
import ctypes as C
from ctypes import wintypes as W
import hashlib, json, os, subprocess, sys, time, traceback
from pathlib import Path

BASE = Path('C:/hs/b570-supervision-fix-v2-20261016').resolve()
QUEUE = BASE / 'queue'
TASK = BASE / 'task'
K = C.WinDLL('kernel32', use_last_error=True)
N = C.WinDLL('ntdll', use_last_error=True)
U = C.c_size_t
class FT(C.Structure):
    _fields_ = [('low', W.DWORD), ('high', W.DWORD)]
class CPI(C.Structure):
    _fields_ = [('file',W.HANDLE),('process',W.HANDLE),('thread',W.HANDLE),('base',C.c_void_p),('offset',W.DWORD),('size',W.DWORD),('tls',C.c_void_p),('start',C.c_void_p),('image',C.c_void_p),('unicode',W.WORD)]
class CTI(C.Structure):
    _fields_ = [('thread',W.HANDLE),('tls',C.c_void_p),('start',C.c_void_p)]
class LDI(C.Structure):
    _fields_ = [('file',W.HANDLE),('base',C.c_void_p),('offset',W.DWORD),('size',W.DWORD),('name',C.c_void_p),('unicode',W.WORD)]
class DU(C.Union):
    _fields_ = [('create',CPI),('thread',CTI),('dll',LDI),('code',W.DWORD),('raw',C.c_ubyte*160)]
class DE(C.Structure):
    _fields_ = [('event',W.DWORD),('pid',W.DWORD),('tid',W.DWORD),('u',DU)]
class PBI(C.Structure):
    _fields_ = [('reserved1',C.c_void_p),('peb',C.c_void_p),('reserved2',C.c_void_p*2),('pid',U),('parent',U)]
class US(C.Structure):
    _fields_ = [('length',W.USHORT),('maximum',W.USHORT),('buffer',C.c_void_p)]
class BASIC(C.Structure):
    _fields_=[('per_process',C.c_longlong),('per_job',C.c_longlong),('flags',W.DWORD),('min',U),('max',U),('active',W.DWORD),('affinity',U),('priority',W.DWORD),('scheduling',W.DWORD)]
class IO(C.Structure):
    _fields_=[('read_ops',C.c_ulonglong),('write_ops',C.c_ulonglong),('other_ops',C.c_ulonglong),('read_bytes',C.c_ulonglong),('write_bytes',C.c_ulonglong),('other_bytes',C.c_ulonglong)]
class LIMIT(C.Structure):
    _fields_=[('basic',BASIC),('io',IO),('process_memory',U),('job_memory',U),('peak_process',U),('peak_job',U)]
def api(name, args, result=W.BOOL):
    f=getattr(K,name); f.argtypes=args; f.restype=result; return f
close=api('CloseHandle',[W.HANDLE]); current=api('GetCurrentProcess',[],W.HANDLE)
dup=api('DuplicateHandle',[W.HANDLE,W.HANDLE,W.HANDLE,C.POINTER(W.HANDLE),W.DWORD,W.BOOL,W.DWORD])
times=api('GetProcessTimes',[W.HANDLE,C.POINTER(FT),C.POINTER(FT),C.POINTER(FT),C.POINTER(FT)])
wait=api('WaitForDebugEvent',[C.POINTER(DE),W.DWORD]); cont=api('ContinueDebugEvent',[W.DWORD,W.DWORD,W.DWORD])
signal=api('WaitForSingleObject',[W.HANDLE,W.DWORD],W.DWORD)
image=api('QueryFullProcessImageNameW',[W.HANDLE,W.DWORD,W.LPWSTR,C.POINTER(W.DWORD)])
filepath=api('GetFinalPathNameByHandleW',[W.HANDLE,W.LPWSTR,W.DWORD,W.DWORD],W.DWORD)
jobcreate=api('CreateJobObjectW',[C.c_void_p,W.LPCWSTR],W.HANDLE)
jobassign=api('AssignProcessToJobObject',[W.HANDLE,W.HANDLE]); jobterminate=api('TerminateJobObject',[W.HANDLE,W.UINT])
jobset=api('SetInformationJobObject',[W.HANDLE,C.c_int,C.c_void_p,W.DWORD])
N.NtQueryInformationProcess.argtypes=[W.HANDLE,C.c_int,C.c_void_p,W.ULONG,C.POINTER(W.ULONG)]
N.NtQueryInformationProcess.restype=W.LONG
registry,J=initialize(TASK)
START=registry['task_begin_ns'];sequence=0;total_starts=0;lifetime_sum=0.0

def atomic_json(path,value):
    partial=path.with_name(path.name+'.partial')
    with partial.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    if path.exists():raise RuntimeError('receipt already exists')
    os.rename(partial,path)

def emit(kind, **kw):
    global sequence
    sequence+=1
    row=dict(seq=sequence,kind=kind,at_ns=time.perf_counter_ns(),utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**kw)
    J.write((json.dumps(row,sort_keys=True,separators=(',',':'))+'\n').encode()); os.fsync(J.fileno()); return row
def os_times(h):
    a,b,c,d=FT(),FT(),FT(),FT()
    if not times(h,C.byref(a),C.byref(b),C.byref(c),C.byref(d)): raise C.WinError(C.get_last_error())
    return dict(created_filetime=(a.high<<32)|a.low,exit_filetime=(b.high<<32)|b.low,kernel_100ns=(c.high<<32)|c.low,user_100ns=(d.high<<32)|d.low)
def identity(h):
    n=W.DWORD(32768); b=C.create_unicode_buffer(n.value)
    if not image(h,0,b,C.byref(n)): raise C.WinError(C.get_last_error())
    p=PBI(); needed=W.ULONG()
    if N.NtQueryInformationProcess(h,0,C.byref(p),C.sizeof(p),C.byref(needed))<0: raise RuntimeError('parent identity unavailable')
    N.NtQueryInformationProcess(h,60,None,0,C.byref(needed))
    buf=C.create_string_buffer(max(needed.value,1024))
    status=N.NtQueryInformationProcess(h,60,buf,len(buf),C.byref(needed))
    command=None
    if status>=0:
        s=US.from_buffer(buf); command=C.wstring_at(s.buffer,s.length//2) if s.buffer else ''
    return dict(image=b.value,parent_pid=int(p.parent),command=command,command_sha256=hashlib.sha256(command.encode()).hexdigest() if command is not None else None,**os_times(h))
def allocated():
    # Full task inventory between commands only, never in a case supervision loop.
    size=0
    for root,dirs,files in os.walk(BASE):
        for name in files:
            try: size+=((Path(root,name).stat().st_size+4095)//4096)*4096
            except FileNotFoundError: raise RuntimeError('inventory race between commands')
    return size
def run(req):
    global total_starts,lifetime_sum
    rid=req['id']; argv=req['argv']; timeout=min(float(req.get('timeout',900)),900)
    if outer_budget.exceeded(total_starts,lifetime_sum,0,time.perf_counter_ns()): raise RuntimeError('TASK_PROCESS_BUDGET')
    physical=allocated()
    if physical>1073741824-268435456: raise RuntimeError('EVIDENCE_RESERVE_UNAVAILABLE')
    emit('COMMAND_BEGIN',request=req,inventory_allocation_upper_bytes=physical)
    out=TASK/(rid+'.stdout.log'); err=TASK/(rid+'.stderr.log')
    start=time.perf_counter_ns(); processes={}; live={}; root_pid=None; termination=None; missing=[]
    job=jobcreate(None,None)
    if not job: raise C.WinError(C.get_last_error())
    lim=LIMIT(); lim.basic.flags=0x2000
    if not jobset(job,9,C.byref(lim),C.sizeof(lim)): raise C.WinError(C.get_last_error())
    try:
        with out.open('xb') as fo,err.open('xb') as fe:
            inp=Path(req['stdin']).open('rb') if req.get('stdin') else subprocess.DEVNULL
            try:
                proc=subprocess.Popen(argv,cwd=req.get('cwd',str(BASE)),stdin=inp,stdout=fo,stderr=fe,creationflags=0x08000001,env={**os.environ,**req.get('env',{})})
            finally:
                if inp!=subprocess.DEVNULL: inp.close()
            root_pid=proc.pid
            emit('ROOT_LAUNCHED',request_id=rid,pid=root_pid,launch_ns=start,argv=argv,stdout=str(out),stderr=str(err))
            if not jobassign(job,int(proc._handle)): raise C.WinError(C.get_last_error())
            root_seen=False
            while not root_seen or live:
                now=time.perf_counter_ns()
                if (now-start)/1e9>timeout and termination is None:
                    termination='COMMAND_TIMEOUT'; emit('TERMINATE_JOB',request_id=rid,reason=termination); jobterminate(job,124)
                live_seconds=sum(elapsed(processes[pid]['live_anchor'],now) for pid in live)
                if outer_budget.exceeded(total_starts,lifetime_sum,live_seconds,now):
                    termination='TASK_PROCESS_BUDGET'; jobterminate(job,125)
                e=DE()
                if not wait(C.byref(e),50):
                    code=C.get_last_error()
                    if code not in (121,0): raise C.WinError(code)
                    if termination and (now-start)/1e9>timeout+30: raise RuntimeError('DEBUG_CLEANUP_TIMEOUT')
                    continue
                keep=0x00010002; exit_handle=None; exit_row=None
                if e.event==3:
                    h=W.HANDLE()
                    if not dup(current(),e.u.create.process,current(),C.byref(h),0,False,2): raise C.WinError(C.get_last_error())
                    ident=identity(h); total_starts+=1
                    if (int(e.pid),ident['created_filetime']) in outer_budget.keys:raise RuntimeError('outer/child accounting overlap')
                    row=emit('PROCESS_CREATE',request_id=rid,task='b570_supervision_fix_v2',role=req.get('role','command') if e.pid==root_pid else 'descendant',pid=int(e.pid),thread=int(e.tid),launch_ns=start if e.pid==root_pid else None,**ident)
                    processes[e.pid]=dict(create=row,live_anchor=anchor(ident['created_filetime'],time.time_ns(),time.perf_counter_ns())); live[e.pid]=h
                    if e.u.create.file: close(e.u.create.file)
                    root_seen=root_seen or e.pid==root_pid
                elif e.event==2:
                    pass # System closes thread handles at EXIT_THREAD/ContinueDebugEvent.
                elif e.event==6:
                    if e.u.dll.file:
                        name=C.create_unicode_buffer(32768); n=filepath(e.u.dll.file,name,len(name),0)
                        if n and any(x in name.value.lower() for x in ('vulkan-1.dll','ggml-vulkan.dll','nvcuda.dll','cudart')):
                            emit('FORBIDDEN_MODULE',pid=int(e.pid),path=name.value); termination='FORBIDDEN_MODULE'; jobterminate(job,126)
                        close(e.u.dll.file)
                elif e.event==5:
                    exit_handle=live.pop(e.pid,None)
                    if exit_handle is None: missing.append({'pid':int(e.pid),'reason':'EXIT_WITHOUT_CREATE'})
                    exit_row=emit('PROCESS_EXIT_OBSERVED',request_id=rid,pid=int(e.pid),exit_code=int(e.u.code),termination=termination)
                elif e.event==1:
                    if int(e.u.code) not in (0x80000003,0x80000004):
                        keep=0x80010001
                        emit('DEBUG_EXCEPTION',request_id=rid,pid=int(e.pid),exception_code=int(e.u.code))
                if not cont(e.pid,e.tid,keep): raise C.WinError(C.get_last_error())
                if exit_handle:
                    if signal(exit_handle,30000)!=0: raise RuntimeError('EXIT_HANDLE_NOT_SIGNALED')
                    ts=os_times(exit_handle); created=processes[e.pid]['create']['created_filetime']
                    life=(ts['exit_filetime']-created)/1e7; lifetime_sum+=life
                    final=emit('PROCESS_CLOSED',request_id=rid,pid=int(e.pid),exit_code=exit_row['exit_code'],lifetime_seconds=life,exit_observed_ns=exit_row['at_ns'],**ts)
                    processes[e.pid]['exit']=final; close(exit_handle)
            rc=proc.wait(timeout=30)
        result=dict(id=rid,status='COMPLETE' if not missing and termination is None else 'FAILED',root_pid=root_pid,exit_code=rc,termination=termination,processes=processes,missing=missing,start_ns=start,end_ns=time.perf_counter_ns(),task_child_starts=total_starts,task_child_lifetime_sum_seconds=lifetime_sum,stdout=str(out),stderr=str(err),inventory_allocation_upper_bytes=allocated())
        emit('COMMAND_END',request_id=rid,summary={k:v for k,v in result.items() if k!='processes'})
        return result
    finally:
        close(job)
        for h in live.values(): close(h)

if __name__=='__main__':
    outer_budget=OuterBudget(registry,os.getpid(),os_times(current())['created_filetime'],time.time_ns(),time.perf_counter_ns())
    emit('BROKER_ARMED',generation=1,mode='cold-win32-v1',no_predecessor=True,pid=os.getpid(),python=sys.executable,identity=identity(current()),source_path=str(Path(__file__).resolve()),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Every command and descendant; broker itself charged once by existing Node observer',bootstrap='Direct suspended creation by existing Node observer; actual outer OS exit retained externally')
    if registry['broker_source_sha256']!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest():raise RuntimeError('broker source differs from bootstrap binding')
    atomic_json(TASK/'READY.json',ready_receipt(os.getpid(),os_times(current())['created_filetime'],START,str(Path(__file__).resolve()),hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),str(TASK/'PROCESS_LEDGER.jsonl')))
    while time.perf_counter_ns()-START<28800*10**9:
        if outer_budget.exceeded(total_starts,lifetime_sum,0,time.perf_counter_ns()):
            emit('BROKER_STOP',reason='task budget exhausted');raise SystemExit(125)
        for p in sorted(QUEUE.glob('*.request.json')):
            done=p.with_name(p.name.replace('.request.json','.result.json'))
            if done.exists(): continue
            try: result=run(json.loads(p.read_text(encoding='utf-8')))
            except BaseException:
                result={'status':'BROKER_ERROR','traceback':traceback.format_exc()}; emit('BROKER_ERROR',result=result)
            atomic_json(done,result)
            if result.get('status')=='BROKER_ERROR':
                emit('BROKER_STOP',reason='command observation failed'); sys.exit(2)
        if (TASK/'STOP').exists(): break
        time.sleep(.05)
    emit('BROKER_CLOSING',task_child_starts=total_starts,task_child_lifetime_sum_seconds=lifetime_sum,active_wall_seconds=(time.perf_counter_ns()-START)/1e9,identity=identity(current()))
    J.close()
