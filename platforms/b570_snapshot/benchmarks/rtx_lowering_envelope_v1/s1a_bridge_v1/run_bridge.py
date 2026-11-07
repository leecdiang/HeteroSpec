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
from bounded import State,Deadline,ByteLedger,BudgetStop,durable

def size(root,exclude_cas=False):
    total=0
    if not root.exists():return 0
    for p in root.rglob('*'):
        if p.is_file() and not (exclude_cas and p.relative_to(root).parts[0]=='cas'):total+=p.stat().st_size
    return total
def check(f0,plan):
    assert f0['run_id']==plan['run_id']==RUN and f0['stage']=='S1A_BRIDGE_V1' and not f0.get('CPU_fixture_only')
    assert f0['plan_sha256']==sha(V/'PLAN.json') and len(plan['descriptors'])==24 and len(plan['numerical_slots'])==240
    slots=plan['numerical_slots'];assert all(s['q']==1 for s in slots[:60]) and all(s['q']>1 for s in slots[60:])
    assert len({(s['descriptor'],s['layout'],s['repeat']) for s in slots})==240
    assert sum(s['registered_support_queries'] for s in slots)==3612
    assert f0['budget']==load(V/'BUDGET_FINAL.json')
    for p in f0['files']:assert sha(p['path'])==p['sha256'],p['path']
def approval_gate(stage,f0_path,approval):
    assert approval['stage']=={'census':'BRIDGE_CENSUS_ONLY','numerical':'BRIDGE_NUMERICAL_EXACT'}[stage]
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
    assert power.AC==1 and scheme==policy['power_scheme_guid'] and float(util)<=5 and float(temp)<=55 and float(total)-float(used)>=512,'readiness gate: no cooldown/retry'

def main():
    begin=time.perf_counter()
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=('census','numerical'))
    p.add_argument('--approval',type=Path);p.add_argument('--dry-check',action='store_true');a=p.parse_args()
    f0=load(V/'F0.json');plan=load(V/'PLAN.json')
    if a.dry_check:
        check(f0,plan);print('PASS CPU identity/matrix check; no device activity');return
    assert a.stage and a.approval,'separate human stage approval required'
    approval=load(a.approval);approval_gate(a.stage,V/'F0.json',approval)
    assert approval.get('prospective_24_context_amendment_accepted') is True
    root=Path(f0['execution_root']);phase=a.stage.upper();budget=f0['budget'];limits=budget['limits'];stage=budget['stages'][a.stage]
    ledger=V/'execution_ledger';ledger.mkdir(exist_ok=True)
    assert not (ledger/(phase+'_CONTROLLER_STARTED.json')).exists(),'immutable stage already attempted'
    assert not (root/(phase+'_ENDED.json')).exists()
    if a.stage=='census':assert not root.exists(),'new root required'
    else:
        auth=load(root/'CENSUS_AUTHENTICATED.json');decision=load(root/'CENSUS_DECISION.json')
        assert load(root/'CENSUS_ENDED.json')['status']=='COMPLETE'
        assert auth['authenticated_remote_bytes'] and auth['F0_sha256']==sha(V/'F0.json')
        assert auth['census_sha256']==sha(root/'census/native/CENSUS.json')==approval['census_sha256']
        assert auth['decision_sha256']==sha(root/'CENSUS_DECISION.json')==approval['decision_sha256']
        assert decision['numerical_admitted'],'technical gate is not execution authority'
    assert shutil.disk_usage(root.anchor).free>=limits['minimum_volume_free_before_start_bytes']
    # From this point all setup/validation/audit work is within the new stage wall.
    root.mkdir(exist_ok=a.stage=='numerical');state=State(root,phase);state.start=begin
    start_receipt=dict(pid=os.getpid(),epoch=time.time(),F0_sha256=sha(V/'F0.json'),approval=approval,approval_file_sha256=sha(a.approval))
    durable(ledger/(phase+'_CONTROLLER_STARTED.json'),start_receipt)
    durable(root/(phase+'_CONTROLLER_STARTED.json'),start_receipt)
    durable(root/(phase+'_ACTIVE_CONTROLLER.lock'),dict(pid=os.getpid(),epoch=time.time(),never_restart=True))
    worker=Child(f0['console_helper']);prior={};current_dir=None;error=None
    def monitor():
        commit=process_commit();state.peak_commit=max(state.peak_commit,commit)
        assert commit<=limits['controller_commit_bytes'],'controller commit ceiling'
        assert shutil.disk_usage(root.anchor).free>=limits['minimum_volume_free_during_stage_bytes'],'volume headroom'
    deadline=Deadline(state,stage['wall_seconds'],worker.terminate,grace=limits['finalization_reserve_seconds'],monitor=monitor).start()
    account=ByteLedger(root,limits['raw_root_bytes'],root/(phase+'_BYTES.jsonl'))
    def paths(p):return [x for x in p.rglob('*') if x.is_file()] if p.exists() else []
    def settle(producer,initial=False):
        # New/unchanged blobs must have content-addressed names. Full bytes are
        # verified again here, in addition to native retain and online inspector.
        new_blobs=[b for b in (root/'cas').glob('*') if b.relative_to(root).as_posix() not in account.files]
        for b in new_blobs:
            assert b.suffix=='.bin' and b.stem==sha(b) and b.stat().st_size<=limits['single_blob_bytes']
        account.adopt(paths(producer)+new_blobs+([x for x in root.iterdir() if x.is_file()] if initial else []))
        state.accounting=dict(known_file_bytes=sum(x[0] for x in account.files.values()),settled_files=len(account.files),journal_events=account.events,reconciliation_CPU_wall_seconds=account.scan_seconds)
    try:
        check(f0,plan);owned_conflicts(f0);deadline.guard()
        account.reserve(limits['raw_root_bytes']-8*1024**2)
        (root/'cas').mkdir(exist_ok=True)
        if a.stage=='census':
            for b in (V/'reference_cas').glob('*.bin'):
                deadline.guard();assert sha(b)==b.stem;shutil.copyfile(b,root/'cas'/b.name)
        settle(root,True);account.reconcile()
        expected={(r['descriptor_id'],r['layout']):r for r in load(V/'CPU_GRAPH_EXPECTED.json')};refs=load(V/'REFERENCE_INDEX.json')
        denied=set(load(root/'CENSUS_DECISION.json')['denied_slots']) if a.stage=='numerical' else set()
        slots=[plan['census_wire']] if a.stage=='census' else plan['numerical_slots']
        for slot in slots:
            if slot['id'] in denied:continue
            deadline.guard()
            if a.stage=='numerical' and slot['index']==60:assert len(prior)==60,'q1 controls precede q>1'
            native_timeout=240 if a.stage=='census' else 60
            # Full readiness + child + bounded qualification allowance + receipt reserve.
            state.reserve_start(slot,deadline.remaining(),native_timeout+10+limits['qualification_reserve_seconds']+limits['finalization_reserve_seconds'])
            current_dir=root/'census' if a.stage=='census' else root/'numerical'/('%03d'%slot['index'])
            current_dir.mkdir(parents=True,exist_ok=False)
            account.reserve(limits['census_nonCAS_bytes'] if a.stage=='census' else limits['numeric_producer_reservation_bytes'])
            save(current_dir/'SLOT_PLANNED.json',slot);readiness(worker,current_dir,f0,deadline.guard,on_start=lambda pid:setattr(state,'active_pid',pid))
            job=wire(slot,V/'F0.json');save(current_dir/'ADMITTED_JOB.json',job)
            command=[f0['executable'],'--gpu-census' if a.stage=='census' else '--gpu-run',str(current_dir/'ADMITTED_JOB.json'),slot['native_output']]
            save(current_dir/'BEFORE_START.json',dict(slot=slot['id'],command=command,epoch=time.time(),graph_cap=slot['graph_computes'],warmups=0,wire_sha256=sha(current_dir/'ADMITTED_JOB.json')))
            worker.run(command,current_dir/'native',native_timeout,env(f0['runtime_directory']),limits['native_process_commit_bytes'],deadline.guard,on_start=state.native_start)
            deadline.guard();n=current_dir/'native';record=load(n/('CENSUS.json' if a.stage=='census' else 'RECORD.json'))
            inventory=module_inventory(record['modules'],f0);save(current_dir/'MODULE_FILES.json',inventory)
            if a.stage=='census':
                assert record['pid']==load(current_dir/'native.PROCESS.json')['pid'];analyzer.verify_modules(n,record,f0,inventory)
                decision=analyzer.census_decision(record,expected,plan);save(root/'CENSUS_DECISION.json',decision)
                save(root/'CENSUS_SUCCESS.json',dict(completed_census=True,numerical_admitted=decision['numerical_admitted'],graph_calls=0,new_authorization_required=True))
            else:
                result=analyzer.inspect(slot,current_dir,f0,plan,refs,expected[slot['descriptor'],slot['layout']],prior,root,control_only=True)
                assert tuple(result['process_identity']) not in {tuple(r['process_identity']) for r in prior.values()}
                save(current_dir/'AUDIT.json',result);prior[slot['descriptor'],slot['layout'],slot['repeat']]=result
            deadline.guard()
            assert size(current_dir)<= (limits['census_nonCAS_bytes'] if a.stage=='census' else limits['numeric_nonCAS_bytes_per_slot'])
            save(current_dir/'COMPLETED.json',dict(slot=slot['id'],qualified=True))
            # Settle storage before admitting completion; any accounting failure
            # remains a stage/control failure, never a scientific retry.
            finished=current_dir;state.complete();current_dir=None;settle(finished)
            if state.completed%30==0:account.reconcile()
        account.reserve(1024**2);account.adopt([x for x in root.iterdir() if x.is_file()]);account.reconcile()
        deadline.guard()
    except BaseException as exc:
        error=repr(exc);state.minimum_stop(error);worker.terminate()
        if current_dir is not None and not (current_dir/'COMPLETED.json').exists():
            durable(current_dir/'FAILED.json',dict(reason=error,state=state.current,no_retry=True))
    finally:
        # No analyzer/tree reconstruction here. Watchdog independently seals a
        # minimum stop and terminal capsule if this bounded finalizer stalls.
        worker.terminate();state.finish('COMPLETE' if error is None else 'INCOMPLETE_STOPPED')
        deadline.close()
    if error:raise RuntimeError(error)
    print('Stage sealed. Offline analysis is separate. No next stage authorized.')

if __name__=='__main__':main()
