"""NOT authorized by CPU repair. Requires new human approval of authenticated F0.

One new independent14-attempt engineering run. Never reads old remaining budget
or writes old slots. No retry, alternative input, QH variant or auto continuation.
"""
import argparse,ctypes,hashlib,json,os,subprocess,threading,time
from ctypes import wintypes as W
from pathlib import Path
from audit_regression import load,sha,inspect
from run_cpu import Extended
R=Path(__file__).resolve().parent
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,indent=2);f.write('\n')
def size(root):return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
def check(f0):
    assert f0['run_id']=='pr113-timer-gpu-regression-v1' and len(f0['slots'])==14
    assert [s['group'] for s in f0['slots']]==['common_q1']*6+['q2_diagnostic']*8
    assert sum(s['graph_computes'] for s in f0['slots'])==14 and all(s['layout']!='QH_D' and s['warmups']==0 for s in f0['slots'])
    for p in f0['files']:assert sha(p['path'])==p['sha256'],p['path']
    assert sum(s['registered_support_queries'] for s in f0['slots'])==f0['limits']['support_API_queries']
def main():
    a=argparse.ArgumentParser();a.add_argument('--dry-check',action='store_true');a.add_argument('--approval');args=a.parse_args()
    begin=time.perf_counter();f0=load(R/'GPU14_F0.json');check(f0)
    if args.dry_check:print('CPU-only F0/14-wire check PASS; no backend, native host or device query');return
    assert args.approval,'separate explicit human GPU14 approval required'
    approval=load(args.approval);assert approval['stage']=='TIMER_REPAIR_GPU14' and approval['F0_sha256']==sha(R/'GPU14_F0.json')
    assert approval['author_message_sha256']==hashlib.sha256(approval['author_message'].encode()).hexdigest()
    authenticated=load(R/'AUTHENTICATED_GPU14_F0.json');assert authenticated['sha256']==approval['F0_sha256'] and authenticated['authenticated_remote_bytes']
    assert (R/'REMOTE_GPU14_F0_BYTES.json').read_bytes()==(R/'GPU14_F0.json').read_bytes()
    root=Path(f0['execution_root']);assert not root.exists(),'new immutable run root required; no retry'
    root.mkdir();save(root/'CONTROLLER_STARTED.json',dict(pid=os.getpid(),epoch=time.time(),F0_sha256=approval['F0_sha256'],approval=approval))
    active=None;job=None;terminal=None;records=[]
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateJobObjectW.argtypes=[ctypes.c_void_p,W.LPCWSTR];k.CreateJobObjectW.restype=W.HANDLE;k.SetInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD];k.AssignProcessToJobObject.argtypes=[W.HANDLE,W.HANDLE];k.CloseHandle.argtypes=[W.HANDLE]
    watchdog_stop=threading.Event()
    def watchdog():
        while not watchdog_stop.wait(.05):
            if (time.perf_counter()-begin)*2>=f0['limits']['owned_child_seconds'] or size(root)>=f0['limits']['raw_root_bytes']:
                save(root/'WATCHDOG_STOP.json',dict(epoch=time.time(),reason='independent wall/process or output ceiling',no_retry=True))
                if job:k.CloseHandle(job)
                os._exit(70)
    threading.Thread(target=watchdog,daemon=True).start()
    def child(argv,prefix,timeout,env):
        nonlocal active,job
        job=k.CreateJobObjectW(None,None);assert job
        info=Extended();info.basic.flags=0x2000|8;info.basic.active=1
        assert k.SetInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info))
        start=time.perf_counter()
        with prefix.with_suffix('.stdout').open('xb') as out,prefix.with_suffix('.stderr').open('xb') as err:
            active=subprocess.Popen(argv,env=env,stdout=out,stderr=err,creationflags=0x08000000|4)
            assert k.AssignProcessToJobObject(job,int(active._handle));pid=active.pid
            save(prefix.with_suffix('.PROCESS.json'),dict(pid=pid,command=argv,epoch=time.time(),job_active_limit=1))
            resume=ctypes.WinDLL('ntdll').NtResumeProcess;resume.argtypes=[W.HANDLE];assert resume(int(active._handle))==0
            try:
                while active.poll()is None:
                    assert time.perf_counter()-start<timeout,'owned child deadline'
                    assert size(prefix.parent)<f0['limits']['per_host_bytes'],'per-host output limit'
                    time.sleep(.05)
                code=active.wait()
            finally:
                elapsed=time.perf_counter()-start
                if active.poll()is None:k.CloseHandle(job);job=None;active.wait()
                if job:k.CloseHandle(job);job=None
                active=None
                save(prefix.with_suffix('.LIFETIME.json'),dict(pid=pid,seconds=elapsed,exit_code=locals().get('code'),timeout_seconds=timeout))
        assert code==0,'native/control child failed: terminal, no retry'
    env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','CUDA_','LLAMA_ARG_'))}
    env['PATH']=f0['runtime_directory']+os.pathsep+env.get('PATH','');env['GGML_CUDA_DISABLE_GRAPHS']='1' # identical inherited failed-run setting, not a workaround
    try:
        for i,slot in enumerate(f0['slots']):
            if i==6:assert len(records)==6 and all(r['module_input_placement_completion_controls']=='PASS' for r in records),'all common q1 controls first'
            d=root/f'{i:02d}';d.mkdir()
            save(d/'SLOT_PLANNED.json',slot)
            cmd=[f0['admission_policy']['nvidia_smi'],'--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu','--format=csv,noheader,nounits']
            save(d/'READINESS_STARTED.json',dict(epoch=time.time(),command=cmd))
            child(cmd,d/'readiness',10,env)
            fields=(d/'readiness.stdout').read_text().strip().split(',');assert len(fields)==6
            name,driver,total,used,util,temp=[s.strip() for s in fields];from safety import Power
            power=Power();assert ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(power))
            admission=dict(gpu=name,driver=driver,total_MiB=float(total),used_MiB=float(used),util=float(util),temp=float(temp),AC=power.AC)
            save(d/'ADMISSION.json',admission);policy=f0['admission_policy']
            assert (name,driver,float(total))==(policy['gpu'],policy['driver'],policy['total_MiB']) and power.AC==1 and float(util)<=5 and float(temp)<=55 and float(total)-float(used)>=512,'admission failed: no retry'
            for p in slot['input_files']:assert sha(p['path'])==p['sha256']
            wire=dict(slot,run_id=f0['run_id'],kind='numeric',approved_stage_F0=approval['F0_sha256'],runtime_directory=f0['runtime_directory'],core_sha256=f0['numerical_DLLs']['ggml-base.dll'],registry_sha256=f0['numerical_DLLs']['ggml.dll'],cuda_plugin_sha256=f0['numerical_DLLs']['ggml-cuda.dll'])
            save(d/'ADMITTED_JOB.json',wire);argv=[f0['executable'],'--gpu-run',str(d/'ADMITTED_JOB.json'),str(d/'native')]
            save(d/'BEFORE_START.json',dict(slot=slot['id'],epoch=time.time(),command=argv,reserved_graphs=1,warmups=0,wire_sha256=sha(d/'ADMITTED_JOB.json')))
            child(argv,d/'native_host',60,env)
            result=inspect(slot,d,f0,records)
            assert load(d/'native/RECORD.json')['pid']==load(d/'native_host.PROCESS.json')['pid']
            for p in slot['input_files']:assert sha(p['path'])==p['sha256']
            save(d/'AUDIT.json',result);records.append(result);save(d/'COMPLETED.json',dict(slot=slot['id'],qualified_engineering_controls=True))
        save(root/'COMPLETE.json',dict(records=records,graph_starts=14,model_requests=0,warmups=0,formal_panel_authorized=False))
    except BaseException as exc:
        terminal=repr(exc);
        if "d" in locals():save(d/"FAILED.json",dict(error=terminal,native_started=(d/"BEFORE_START.json").exists(),no_retry=True))
        save(root/'TERMINAL_STOP.json',dict(error=terminal,epoch=time.time(),completed=len(records),no_retry=True,old_run_untouched=True));raise
    finally:
        watchdog_stop.set()
        if job:k.CloseHandle(job)
        if active and active.poll()is None:active.kill();active.wait()
        save(root/'CONTROLLER_ENDED.json',dict(seconds=time.perf_counter()-begin,conservative_owned_bound_seconds=2*(time.perf_counter()-begin),terminal=terminal))
if __name__=='__main__':main()
