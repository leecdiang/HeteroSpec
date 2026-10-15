"""Only GPU execution entry: separately approved census, then approved numerics.

Default/missing approval refuses. Preparation may use --dry-check only: no child,
backend load, device query, run root or scientific ledger is created by that path.
"""
import argparse,ctypes,hashlib,json,os,shutil,threading,time,uuid
from ctypes import wintypes as W
from pathlib import Path
from common import V,RUN,load,save,sha,wire,env,pin
from lifecycle import Child,process_commit
import analyzer

def size(root,exclude_cas=False):
    total=0
    if not root.exists():return 0
    for p in root.rglob('*'):
        if p.is_file() and not (exclude_cas and p.relative_to(root).parts[0]=='cas'):total+=p.stat().st_size
    return total
def check(f0,plan):
    assert f0['run_id']==plan['run_id']==RUN and f0['stage']=='FORMAL_NUMERICAL_V2' and not f0.get('CPU_fixture_only')
    assert f0['plan_sha256']==sha(V/'PLAN.json') and len(plan['descriptors'])==72 and len(plan['numerical_slots'])==720
    slots=plan['numerical_slots'];assert all(s['q']==1 for s in slots[:180]) and all(s['q']>1 for s in slots[180:])
    assert len({(s['descriptor'],s['layout'],s['repeat']) for s in slots})==720
    assert sum(s['registered_support_queries'] for s in slots)==10836
    assert f0['budget']==load(V/'BUDGET.json')
    for p in f0['files']:assert sha(p['path'])==p['sha256'],p['path']
def approval_gate(stage,f0_path,approval):
    assert approval['stage']=={'census':'FORMAL_V2_CENSUS_ONLY','numerical':'FORMAL_V2_NUMERICAL_EXACT'}[stage]
    assert approval['F0_sha256']==sha(f0_path) and approval['run_id']==RUN
    assert approval['author_message'] and approval['author_message_sha256']==hashlib.sha256(approval['author_message'].encode()).hexdigest()
    authenticated=load(V/'AUTHENTICATED_F0.json')
    assert authenticated['authenticated_remote_bytes'] and authenticated['sha256']==sha(f0_path)
    assert (V/'REMOTE_F0_BYTES.json').read_bytes()==Path(f0_path).read_bytes()
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
def readiness(worker,d,f0,guard):
    policy=f0['admission_policy'];command=[policy['nvidia_smi'],'--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu','--format=csv,noheader,nounits']
    save(d/'READINESS_STARTED.json',dict(command=command,epoch=time.time(),attempts=1))
    worker.run(command,d/'readiness',10,env(f0['runtime_directory']),f0['budget']['limits']['readiness_process_commit_bytes'],guard)
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
    assert power.AC==1 and scheme==policy['power_scheme_guid'] and float(util)<=5 and float(temp)<=55 and float(total)-float(used)>=512,'readiness gate: no cooldown/retry'
def main():
    begin=time.perf_counter()
    a=argparse.ArgumentParser();a.add_argument('--stage',choices=('census','numerical'));a.add_argument('--approval',type=Path);a.add_argument('--dry-check',action='store_true');args=a.parse_args()
    f0=load(V/'F0.json');plan=load(V/'PLAN.json')
    if args.dry_check:check(f0,plan);print('PASS CPU-only formal F0/matrix/identities;0 new processes/devices/backends/graphs');return
    assert args.stage and args.approval,'explicit stage and separate human approval required'
    approval=load(args.approval);approval_gate(args.stage,V/'F0.json',approval)
    root=Path(f0['execution_root']);ledger=V/'execution_ledger';ledger.mkdir(exist_ok=True)
    start=begin;phase=args.stage.upper();limits=f0['budget']['limits'];stage=f0['budget']['stages'][args.stage]
    assert not (ledger/(phase+'_CONTROLLER_STARTED.json')).exists(),'stage already attempted; never restart'
    if args.stage=='census':assert not root.exists(),'new run root required'
    else:
        assert (root/'CENSUS_SUCCESS.json').exists() and (root/'CENSUS_ENDED.json').exists()
        assert load(root/'CENSUS_ENDED.json')['error'] is None and load(root/'CENSUS_DECISION.json')['numerical_admitted']
        auth=load(root/'CENSUS_AUTHENTICATED.json');assert auth['authenticated_remote_bytes'] and auth['F0_sha256']==sha(V/'F0.json')
        assert auth['census_sha256']==sha(root/'census/native/CENSUS.json') and auth['decision_sha256']==sha(root/'CENSUS_DECISION.json')
        assert approval['census_sha256']==auth['census_sha256'] and approval['decision_sha256']==auth['decision_sha256']
    save(ledger/(phase+'_CONTROLLER_STARTED.json'),dict(pid=os.getpid(),epoch=time.time(),F0_sha256=sha(V/'F0.json'),approval=approval))
    worker=Child(f0['console_helper']);failure=None;stop=threading.Event();prior={};lock=None;current=None;controller_peak=[0]
    def guard():
        assert time.perf_counter()-start<stage['wall_seconds'],'whole-controller wall/owned ceiling'
        commit=process_commit();controller_peak[0]=max(controller_peak[0],commit)
        assert commit<=limits['controller_commit_bytes'],'sampled controller private-commit ceiling'
        assert size(root)<=limits['raw_root_bytes'],'raw disk ceiling'
        assert shutil.disk_usage(root.anchor).free>=limits['minimum_volume_free_during_stage_bytes'],'physical volume headroom gate'
        if current:
            cap=limits['census_nonCAS_bytes'] if args.stage=='census' else limits['numeric_nonCAS_bytes_per_slot']
            assert size(current)<=cap,'slot metadata/log byte ceiling'
    def watchdog():
        while not stop.wait(.05):
            try:guard()
            except BaseException as exc:
                save(root/(phase+'_WATCHDOG_STOP.json'),dict(reason=repr(exc),epoch=time.time(),no_retry=True));worker.terminate();os._exit(70)
    try:
        if args.stage=='census':
            root.mkdir(exist_ok=False);(root/'cas').mkdir()
        lock=root/'ACTIVE_CONTROLLER.lock';save(lock,dict(pid=os.getpid(),stage=args.stage))
        threading.Thread(target=watchdog,daemon=True).start()
        check(f0,plan);owned_conflicts(f0)
        assert shutil.disk_usage(root.anchor).free>=limits['minimum_volume_free_before_start_bytes'],'physical volume admission headroom'
        if args.stage=='census':
            for p in (V/'reference_cas').glob('*.bin'):
                assert sha(p)==p.stem;shutil.copyfile(p,root/'cas'/p.name);assert sha(root/'cas'/p.name)==p.stem
        expected={(r['descriptor_id'],r['layout']):r for r in load(V/'CPU_GRAPH_EXPECTED.json')};refs=load(V/'REFERENCE_INDEX.json')
        denied=set(load(root/'CENSUS_DECISION.json')['denied_slots']) if args.stage=='numerical' else set()
        slots=[plan['census_wire']] if args.stage=='census' else plan['numerical_slots']
        for slot in slots:
            if slot['id'] in denied:continue # explicit NOT_SUPPORTED preserved by complete-plan analysis
            if args.stage=='numerical' and slot['index']==180:assert len(prior)==180,'all five-layout q1 controls and fresh repeats must pass first'
            reserve=250 if args.stage=='census' else 70
            assert stage['wall_seconds']-(time.perf_counter()-start)>reserve+1,'insufficient remaining frozen lifetime: terminal, no next start'
            current=root/'census' if args.stage=='census' else root/'numerical'/('%03d'%slot['index']);current.mkdir(parents=True,exist_ok=False)
            save(current/'SLOT_PLANNED.json',slot);guard();readiness(worker,current,f0,guard)
            job=wire(slot,V/'F0.json');save(current/'ADMITTED_JOB.json',job)
            mode='--gpu-census' if args.stage=='census' else '--gpu-run';command=[f0['executable'],mode,str(current/'ADMITTED_JOB.json'),slot['native_output']]
            save(current/'BEFORE_START.json',dict(slot=slot['id'],epoch=time.time(),command=command,graph_cap=slot['graph_computes'],warmups=0,wire_sha256=sha(current/'ADMITTED_JOB.json')))
            worker.run(command,current/'native',240 if args.stage=='census' else 60,env(f0['runtime_directory']),limits['native_process_commit_bytes'],guard)
            n=current/'native';r=load(n/('CENSUS.json' if args.stage=='census' else 'RECORD.json'))
            inventory=module_inventory(r['modules'],f0);save(current/'MODULE_FILES.json',inventory)
            if args.stage=='census':
                assert r['pid']==load(current/'native.PROCESS.json')['pid'];analyzer.verify_modules(n,r,f0,inventory)
                decision=analyzer.census_decision(r,expected,plan);save(root/'CENSUS_DECISION.json',decision)
                save(root/'CENSUS_SUCCESS.json',dict(completed_census=True,numerical_admitted=decision['numerical_admitted'],primary_QH='QH_C',graph_calls=0,requires_commit_authenticated_readback_and_new_numerical_authorization=True))
            else:
                result=analyzer.inspect(slot,current,f0,plan,refs,expected[slot['descriptor'],slot['layout']],prior,root)
                assert tuple(result['process_identity']) not in {tuple(r['process_identity']) for r in prior.values()},'new native process generation required; numeric PID reuse alone is not a failure'
                save(current/'AUDIT.json',result);prior[slot['descriptor'],slot['layout'],slot['repeat']]=result;save(current/'COMPLETED.json',dict(slot=slot['id'],qualified=True))
        if args.stage=='numerical':save(root/'NUMERICAL_SUCCESS.json',dict(qualified_completions=len(prior),not_supported=len(denied),no_next_stage_authorization=True))
    except BaseException as exc:
        failure=repr(exc);worker.terminate();root.mkdir(parents=True,exist_ok=True)
        if current:save(current/'FAILED.json',dict(error=failure,no_retry=True,epoch=time.time()))
        save(root/(phase+'_FAILED.json'),dict(error=failure,no_retry=True,epoch=time.time(),completed=len(prior)))
        raise
    finally:
        worker.terminate()
        if args.stage=='numerical':
            try:save(root/'ANALYSIS.json',analyzer.analyze(root,f0,plan,load(V/'REFERENCE_INDEX.json'),{(r['descriptor_id'],r['layout']):r for r in load(V/'CPU_GRAPH_EXPECTED.json')}))
            except BaseException as exc:
                failure=failure or repr(exc);save(root/'ANALYSIS_FAILED.json',dict(error=repr(exc),no_retry=True))
        stop.set()
        elapsed=time.perf_counter()-start
        save(root/(phase+'_ENDED.json'),dict(seconds=elapsed,conservative_owned_bound_seconds=3*elapsed,error=failure,pid=os.getpid(),budget_not_reset=True,sampled_controller_peak_private_commit_bytes=controller_peak[0]))
        if lock and lock.exists() and load(lock)['pid']==os.getpid():lock.unlink()
    if failure:raise RuntimeError(failure)
    print('Stage ended. Preserve all starts. No automatic timing/actor/S2/S3 or stage restart.')
if __name__=='__main__':main()
