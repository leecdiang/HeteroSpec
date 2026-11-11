"""Reader-only continuation: retain/recheck native-complete R00, never rerun it."""
import os,sqlite3,time,traceback
from pathlib import Path
import run_supplement as base
from common import HERE,RUNTIME,LOCK,ORIGINAL,read,put,sha,now,inherit,source_check,reader_class
from check_output import Check

def modules(j,meta):
    expected={n.lower():h for n,h in read(j['build'])['modules'].items()};drivers=read(ORIGINAL/'DRIVER_MODULE_PINS.json')['pins'];result={}
    for phase in ('modules_before','modules_after'):
        normalized=[]
        for item in meta[phase]:
            if isinstance(item,str):path=item;recorded=None
            else:path=item['path'];recorded=item['sha256']
            current=sha(path);name=Path(path).name.lower();want=expected.get(name)
            if name in drivers:want=drivers[name]['sha256']
            if name=='worker.exe':want=j['exe_sha256']
            if recorded is not None:assert current==recorded,('Native module hash changed',path)
            if want is not None:assert current==want,('Pinned numerical module changed',path)
            normalized.append(dict(path=path,sha256=current,native_hash_available=recorded is not None,
                hash_scope='Native hash plus current bytes' if recorded is not None else 'Native reports loaded path; host hashes current file after run, bracketed by prelaunch frozen-file identity'))
        result[phase]=normalized
    assert meta['GPU_device']=='NVIDIA GeForce RTX 5070 Ti Laptop GPU'
    assert any(Path(x['path']).name.lower()=='ggml-cuda.dll' for x in result['modules_after'])
    return result

def prepare_recovery():
    p=read(HERE/'EXECUTION_PLAN.json');j=p['jobs'][0];folder=RUNTIME/'runs'/j['id'];meta=read(folder/'native/result.json');host=read(folder/'HOST.json')
    assert host['status']=='FAILED' and host['code']==0 and meta['status']=='COMPLETE' and meta['trajectories']==4 and meta['token_rows']==792
    assert read(folder/'JOB.json')==j and read(folder/'JOB_NATIVE.json')==j['job'];inherit();source_check();base.identity(j)
    before={x.relative_to(folder).as_posix():sha(x) for x in sorted(folder.rglob('*')) if x.is_file()}
    checked=[];reader=reader_class()()
    for case in j['job']['cases']:
        for n in case['observe_positions']:
            d=folder/'native'/case['name']/'captures'/str(n);v=reader.vector(d/'frontier.f32');r=dict(case=case['name'],position=n,vector_sha256=v['sha256'])
            if n in case['state_positions']:r['active_state']=reader.state(d/'sequence.bin',n)
            checked.append(r)
    loaded=modules(j,meta)
    put(HERE/'READER_REPAIR_ADMISSION.json',dict(error='Native R module_inventory returns path strings; original supervisor indexed them as objects. Error occurred only after native exit0/COMPLETE.',
        initial_frozen_commit='b1a41dc0fe60012a331552510dd6156d58391ba5',failed_controller_sha256=sha(HERE/'run_supplement.py'),
        job=j['id'],original_files=before,raw_vectors_and_states_reread=checked,numerical_modules=loaded,
        actual_requests=4,actual_rows=792,original_host_failed_marker_preserved=True,original_ledger_failed_status_preserved=True,
        reference_job_reruns=0,refunds=0,remaining_planned_requests=33,source_or_input_or_comparison_tolerance_changed=False,
        boundary='Only module record schema normalization changes. No native code, inputs, numerical comparison, order or data changed. Publish full amendment before remaining GPU outputs.'))
    put(folder/'RECOVERED_NATIVE_COMPLETE.json',dict(passed_offline_recheck=True,actual_requests=4,actual_rows=792,native_exit_code=0,
        raw_complete_status=meta['status'],postprocessor_failed=True,old_failed_record_not_overwritten=True,reruns=0,refunds=0,
        source_repair_admission=str(HERE/'READER_REPAIR_ADMISSION.json')))
    put(folder/'ACTUAL_MODULES_RECHECKED.json',loaded)
    put(HERE/'READER_REPAIR_SOURCE_BINDINGS.json',dict(files={str(x):sha(x) for x in (HERE/'continue_reader_v2.py',HERE/'READER_REPAIR_ADMISSION.json',HERE/'EXECUTION_SOURCE_BINDINGS.json')},
        original_execution_source_binding_sha256=sha(HERE/'EXECUTION_SOURCE_BINDINGS.json'),new_model_requests=0))
    print('Offline R00 recovery passed; original4-request charge/data/failure preserved,0 reruns',flush=True)

def resume():
    patch=read(HERE/'READER_REPAIR_SOURCE_BINDINGS.json');receipt=read(HERE/'READER_REPAIR_READBACK.json');assert receipt['passed'] and receipt['binding_sha256']==sha(HERE/'READER_REPAIR_SOURCE_BINDINGS.json')
    for path,h in patch['files'].items():assert sha(path)==h
    source_check();inherit();assert not LOCK.exists();base.power_mode();base.resource(base.sample());base.competing()
    recovery=read(HERE/'READER_REPAIR_ADMISSION.json');plan=read(HERE/'EXECUTION_PLAN.json');first=plan['jobs'][0];folder=RUNTIME/'runs'/first['id']
    for name,h in recovery['original_files'].items():assert sha(folder/name)==h,'Original completed reference changed'
    assert {x.name for x in (RUNTIME/'runs').iterdir() if x.is_dir()}=={first['id']}
    db=sqlite3.connect(RUNTIME/'ledger.sqlite');rows=db.execute('SELECT id,requests,rows,status FROM attempts').fetchall();assert rows==[(first['id'],4,792,'FAILED')]
    assert read(folder/'RECOVERED_NATIVE_COMPLETE.json')['passed_offline_recheck']
    base.module_check=modules;owned=False;started=time.monotonic()
    try:
        with LOCK.open('x',encoding='utf8') as f:__import__('json').dump(dict(pid=os.getpid(),epoch='rtx213-supplement-s1-reader-continuation-v2',work=str(RUNTIME)),f)
        owned=True;put(RUNTIME/'CONTINUATION_ADMISSION.json',dict(utc=now(),reused_native_complete_requests=4,remaining_requests=33,reference_reruns=0,repair_readback=receipt))
        check=Check()
        for j in plan['jobs'][1:8]:base.execute(db,j);print('REFERENCE_WORKER_COMPLETE',j['id'],flush=True)
        check.bank_ready();print('REFERENCE_BANK_COMPLETE vectors257 states40',flush=True)
        proofs=[]
        for j in plan['jobs'][8:]:
            base.execute(db,j);q=check.candidate(j);proofs.append(q);print('CANDIDATE_CHECKED',j['id'],'boundary_cycles',len(q['boundary_cycles']),flush=True)
        assert len(proofs)==8
        put(RUNTIME/'COMPLETE_QUALIFICATION.json',dict(passed=True,new_reference_cases=29,new_heavy_requests=8,new_logical_requests=37,
            all_eight_arms=True,all_prebound_vectors_and_states=True,counts=dict(check.counts),continuation_wall_seconds=time.monotonic()-started,
            original_performance_data_unchanged=True,old_clean_state_recovered=False,blind_confirmation=False,
            native_reruns=0,postprocessor_failure_preserved=True,first4_requests_reused_without_refund=True))
        put(RUNTIME/'RAW_FILES_READ.json',check.reader.seen);print('SUPPLEMENT_COMPLETE37 all8 native/state checks passed',flush=True)
    except BaseException as e:
        put(RUNTIME/'CONTINUATION_STOPPED.json',dict(utc=now(),error=repr(e),traceback=traceback.format_exc(),no_automatic_retry=True));raise
    finally:
        db.close()
        if owned:assert read(LOCK)['pid']==os.getpid();LOCK.unlink()

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--prepare-recovery',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args()
    assert a.prepare_recovery!=a.resume
    if a.prepare_recovery:prepare_recovery()
    else:resume()
