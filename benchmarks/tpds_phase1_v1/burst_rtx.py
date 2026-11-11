"""Persistent-worker host clocks layered on the unchanged owned PR190 launcher."""
from qualify_rtx import *
import threading
from analyze import analyze_burst
from receipts import normalize_receipt
from measure_r1_rtx import verify_freezes,verify_observed_modules

R2_ARMS={
 'W_M_TARGET_ONLY':('W_L4',True,False),
 'W_P_M_TARGET_ONLY':('W_P',True,False),
 'L_L4_M_TARGET_ONLY':('L_L4',True,False),
 'L_M_TARGET_ONLY':('L_P',True,False),
 'L_M_MATCHED':('L_P',False,False),
 'L_D4':('L_P',False,True)}

def clocked(label,recipe,payload,reservation):
    # Only intercept the one owned native Popen. All safety, ledger, resource,
    # byte/module checks and descendant cleanup remain in prior.execute.
    expected=str(ROOT/f'runtime-v{VERSION}-{recipe}'/'bin/worker.exe')
    original=prior.subprocess.Popen;clock={};markers=[];errors=[];thread=None
    def launch(args,*a,**kw):
        nonlocal thread
        if str(args[0]).casefold()!=expected.casefold():return original(args,*a,**kw)
        assert 'launch' not in clock
        output=kw['stdout'];kw['stdout']=subprocess.PIPE
        clock['launch']=time.perf_counter();process=original(args,*a,**kw)
        def drain():
            try:
                for line in iter(process.stdout.readline,b''):
                    received=time.perf_counter();output.write(line);output.flush()
                    if line.startswith(b'PHASE1_RESULT_READY '):
                        _,name,native=line.decode('utf8').strip().split(' ',2)
                        markers.append(dict(name=name,seconds_after_launch=received-clock['launch'],native_main_to_result_s=float(native)))
            except BaseException as e:errors.append(repr(e))
        thread=threading.Thread(target=drain,daemon=True);thread.start();poll=process.poll
        def finished_poll():
            code=poll()
            if code is not None:
                thread.join(timeout=10);assert not thread.is_alive(),'stdout drain did not finish'
                clock.setdefault('exit',time.perf_counter())
            return code
        process.poll=finished_poll
        return process
    total=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.total','--format=csv,noheader,nounits'],text=True).strip())*1024**2
    prior.subprocess.Popen=launch
    try:out=execute(label,recipe,'Qwen',payload,reservation)
    finally:
        prior.subprocess.Popen=original
        if thread:thread.join(timeout=10)
    verify_observed_modules(recipe,out)
    assert not errors and len(markers)==len(payload['inputs']) and [r['name'] for r in markers]==[x['name'] for x in payload['inputs']]
    assert all(b['seconds_after_launch']>a['seconds_after_launch'] for a,b in zip(markers,markers[1:]))
    for m in markers:
        r=read(out/'native'/m['name']/'receipt.json');assert abs(r['phase1_main_to_result_s']-m['native_main_to_result_s'])<1e-6
        assert m['seconds_after_launch']>=m['native_main_to_result_s']
    telemetry=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()];assert telemetry
    result=dict(markers=markers,launch_to_first_result_s=markers[0]['seconds_after_launch'],launch_to_first_test_result_s=markers[2]['seconds_after_launch'],test_burst_wall_s=markers[-1]['seconds_after_launch']-markers[1]['seconds_after_launch'],worker_wall_s=clock['exit']-clock['launch'],peak_device_bytes=max(total-r['gpu_free'] for r in telemetry),peak_device_scope='Observed peak device-global used bytes from original2s nvidia-smi samples; includes desktop/context and is a lower bound on the true peak, not a per-process high-water counter.',burst_boundary='Second exposed primer result marker through final test result marker; no setup/N extrapolation',wrapper_wall_s=read(out/'exit.json')['seconds'],actual_processes=1)
    put(out/'HOST_CLOCKS.json',result);return out,result

def payload(arm,inputs):
    strategy,target_only,draft=R2_ARMS[arm];recipe,lowering=ARMS[strategy]
    job=dict(lowering=lowering,residency='target_only' if target_only else 'matched',draft=draft,draft_width=4 if draft else 1,inputs=inputs)
    rows=sum(2*len(x['input']['prompt_ids'])+8*(x['input']['cap']-1) if draft else len(x['input']['prompt_ids'])+x['input']['cap']-1 for x in inputs)
    return recipe,job,dict(requests=len(inputs),token_rows=rows,operators=0)

def smoke():
    # New clocks are tested on exposed inputs before ANY R2 test outputs.
    rs=roots('Qwen');inputs=[dict(name='primer-'+str(i),capture=False,input=rs[i]) for i in range(2)]+[dict(name='test-'+str(i),capture=False,input=r) for i,r in enumerate(rs)]
    records=[]
    for arm in ('W_M_TARGET_ONLY','L_D4'):
        recipe,job,reserve=payload(arm,inputs);out,clocks=clocked('R2-clock-development-'+arm,recipe,job,reserve)
        meta=prior.native_fields(out/'native/result.json',['total_observed_API_calls','model_load_s','pool_setup_s'])
        assert meta['total_observed_API_calls']['context_creates']==(1 if arm=='W_M_TARGET_ONLY' else 2)
        for x in inputs:
            r=read(out/'native'/x['name']/'receipt.json');assert r['endpoint']==read(P190/'runs/Qwen-old-free/native'/f'r{rs.index(x["input"])}-heavy/receipt.json')['endpoint']
            assert all(v==0 for v in r['observed_API_calls_within_service'].values())
        records.append(dict(arm=arm,attempt=str(out),actual_host_clocks=clocks,actual_native_setup=meta,same_original_R_endpoints=True))
    put(ROOT/'R2-CLOCK-QUALIFICATION.json',dict(passed=True,inputs='Two fixed exposed primers plus all four exposed development requests',records=records,no_R2_test_outputs=True))

def references():
    rs=read(ROOT/'R2/NATIVE_INPUTS.json')['inputs'];inputs=[dict(name='reference-'+str(i),capture=False,input=r) for i,r in enumerate(rs)]
    return finished('R2-original-R-free','R-Qwen','Qwen',dict(lowering='SIMPLE',inputs=inputs),dict(requests=16,token_rows=sum(len(r['prompt_ids'])+127 for r in rs),operators=0))

def main():
    assert read(ROOT/'R2/PUBLISHED.json')['independent_readback_passed']
    assert read(ROOT/'R2-CLOCK-QUALIFICATION.json')['passed']
    plan=read(ROOT/'R2/WORKERS.json');rs=read(ROOT/'R2/NATIVE_INPUTS.json')['inputs'];lookup={r['id']:r for r in rs};exposed=roots('Qwen');lookup.update({r['id']:r for r in exposed});started=time.monotonic();verify_freezes()
    reference=references();endpoints={r['id']:read(reference/'native'/('reference-'+str(i))/'receipt.json')['endpoint'] for i,r in enumerate(rs)};endpoints.update({r['id']:read(P190/'runs/Qwen-old-free/native'/f'r{i}-heavy/receipt.json')['endpoint'] for i,r in enumerate(exposed)})
    metadata=prior.native_fields(reference/'native/result.json',['vocab','eog_ids']);records=[]
    for worker in plan:
        inputs=[dict(name='request-'+str(i),capture=False,input=lookup[r['root']]) for i,r in enumerate(worker['requests'])]
        recipe,job,reserve=payload(worker['arm'],inputs);out,clocks=clocked(worker['worker_id'],recipe,job,reserve)
        meta=prior.native_fields(out/'native/result.json',['model_load_s','pool_setup_s','total_observed_API_calls']);assert meta['total_observed_API_calls']['context_creates']==(1 if worker['residency']=='target_only' else 2)
        calls=[]
        for wanted,x in zip(worker['requests'],inputs):
            p=out/'native'/x['name']/'receipt.json';r=read(p);assert r['endpoint']==endpoints[wanted['root']];assert all(v==0 for v in r['observed_API_calls_within_service'].values())
            # Independent producer/pending/trim/termination reconstruction.
            r['study_cap']=x['input']['cap'];_,trace=trace_from_row(r,r['prompt_ids'],metadata['vocab'],metadata['eog_ids'],'rtx')
            calls.append(dict(root=wanted['root'],kind=wanted['kind'],status='COMPLETE',qualified=True,service_s=r['service_seconds'],reference_id='Qwen-immutable-original-R-C1024',native_receipt=str(p),native_receipt_sha256=sha(p),independent_trace_valid=True))
        record=dict(worker_id=worker['worker_id'],status='COMPLETE',provision_count=1,process_count=1,requests=calls,model_setup_s=meta['model_load_s']+meta['pool_setup_s'],**clocks)
        put(out/'CHECKED.json',record);records.append(record);print('Persistent R2 worker complete',len(records),'/',len(plan),worker['worker_id'],flush=True)
    verify_freezes();put(ROOT/'R2/RECORDS.json',records);put(ROOT/'R2/RESULTS.json',analyze_burst(plan,records));put(ROOT/'R2/COMPLETE.json',dict(workers=len(plan),measurements=16*len(plan),primers=2*len(plan),separate_original_R_requests=16,coordinator_wall_s=time.monotonic()-started,no_replaced_or_extra_slots=True))

if __name__=='__main__':
    if '--smoke' in sys.argv:smoke()
    else:main()
