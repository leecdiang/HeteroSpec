"""Single-worker RTX execution adapter. Each task is attempted at most once.

New UUID only; no old entrypoint is imported. Large replay analysis stays CPU-only.
"""
import argparse,collections,copy,ctypes,datetime,json,math,os,shutil,struct,subprocess,sys,time
from pathlib import Path
from common import V,load,save,sha
from lifecycle import Child
from prepare_rtx import root,ROLES,LAYOUTS
from identity_audit import exports,verify_record

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def git(*args):return subprocess.check_output(['git','-C',str(V.parents[1]),*args],text=True).strip()
def env(s,mode='OFF'):
    e=os.environ.copy();e.pop('GGML_CUDA_DISABLE_GRAPHS',None);e.update({'GGML_CUDA_DISABLE_GRAPHS':'1'} if mode=='OFF' else {});e['PATH']=s['runtime_directory']+';'+e['PATH'];e['PYTHONDONTWRITEBYTECODE']='1';return e
def helper():
    p=Path(os.environ['SystemRoot'])/'System32/conhost.exe';return dict(path=str(p),sha256=sha(p))
def guard(s):
    assert time.time()-s['start_epoch']<s['global_seconds']-s['delivery_reserve_seconds'],'delivery reserve'
    assert shutil.disk_usage(root()).free>=10*1024**3,'disk headroom'
def lock_runtime(s):
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];k.CreateFileW.restype=ctypes.c_void_p;k.CloseHandle.argtypes=[ctypes.c_void_p];handles=[]
    for name,digest in s['numerical_DLLs'].items():
        p=Path(s['runtime_directory'])/name;h=k.CreateFileW(str(p),0x80000000,1,None,3,0,None);assert h and h!=ctypes.c_void_p(-1).value;assert sha(p)==digest;handles.append(h)
    return k,handles

def telemetry(s,label):
    folder=root()/'environment';folder.mkdir(exist_ok=True);i=len(list(folder.glob('*.json')))
    cmd=[str(Path(os.environ['SystemRoot'])/'System32/nvidia-smi.exe'),'--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu,clocks.sm,power.draw','--format=csv,noheader,nounits']
    begin=time.monotonic();p=subprocess.run(cmd,capture_output=True,timeout=10,env=env(s));r=dict(label=label,utc=utc(),command=cmd,seconds=time.monotonic()-begin,exit=p.returncode,stdout=p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace'))
    class Power(ctypes.Structure):_fields_=[('AC',ctypes.c_ubyte),('flag',ctypes.c_ubyte),('percent',ctypes.c_ubyte),('reserved',ctypes.c_ubyte),('life',ctypes.c_uint32),('full',ctypes.c_uint32)]
    power=Power();assert ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(power));r['AC']=power.AC
    pp=subprocess.run(['powercfg','/getactivescheme'],capture_output=True,timeout=10);r['power_scheme']=pp.stdout.decode(errors='replace').strip()
    assert p.returncode==0,'telemetry unavailable'
    f=r['stdout'].strip().split(',');r.update(gpu=f[0].strip(),driver=f[1].strip(),total_MiB=float(f[2]),used_MiB=float(f[3]),utilization=float(f[4]),temperature=float(f[5]),SM_clock_MHz=f[6].strip(),power_W=f[7].strip())
    r['identity_ok']=r['gpu']=='NVIDIA GeForce RTX 5070 Ti Laptop GPU' and r['driver']=='616.92';r['safe_memory']=r['total_MiB']-r['used_MiB']>=max(1024,r['total_MiB']*.1);r['quiet']=r['identity_ok'] and r['safe_memory'] and r['utilization']<=5 and r['temperature']<=55 and r['AC']==1
    save(folder/f'{i:04d}.json',r);assert r['identity_ok'] and r['safe_memory'],'device identity or memory';return r

def quiet(s,label):
    start=time.monotonic()
    while True:
        guard(s);a=telemetry(s,label+'/pre1');time.sleep(5);b=telemetry(s,label+'/pre2')
        if a['quiet'] and b['quiet']:return [a,b]
        if time.monotonic()-start+35>=600:return None
        time.sleep(30)

def occurrence(n,row):
    p=n/row['ordinary_file'];start=row['offset_bytes'];size=row['output_bytes']
    with p.open('rb') as f:f.seek(start);b=f.read(size)
    assert len(b)==size,'truncated ordinary';return b

def audit(n,c,job):
    rr=load(n/'RECORD.json');g=load(n/'GRAPH.json');spec=load(root()/'RUN_SPEC.json');verify_record(rr,Path(spec['runtime_directory'])/'ggml-base.dll',exports(Path(spec['runtime_directory'])/'ggml-base.dll'));assert rr['execution_id']==job['execution_id'] and rr['layout']==job['layout'] and rr['observer_method']==job['method']
    assert rr['input_after_equal'] and rr['host_input_unchanged'],'input mutation'
    for role in ROLES:
        source=(Path(c['root'])/(role+'.bin')).read_bytes()
        assert (n/f'input_{role}_before.bin').read_bytes()==source and (n/f'input_{role}_after.bin').read_bytes()==source,'independent input audit'
    assert all(x['CUDA_owned'] for x in g['addresses']) and g['actual_device']=='CUDA0' and len(rr['plugin_core_IAT'])==41
    assert all(x['CUDA_support'] for x in g['nodes']) and rr['modules']==rr['modules_end'],'support or module drift'
    cpu=load(root()/'CPU'/c['case_id']/(job['layout']+'.json'))['graph'] if not job['capture_reference'] else None
    if cpu is not None:
        clean=lambda node:{k:v for k,v in node.items() if k not in ['CUDA_support','placement']}
        assert [clean(x) for x in cpu['nodes']]==[clean(x) for x in g['nodes']] and cpu['output']==g['output'],'actual serialized graph drift'
    spec=load(root()/'RUN_SPEC.json');directory=Path(spec['runtime_directory']).resolve()
    for phase in ['modules','modules_end']:
        for path in rr[phase]:
            if Path(path).name in spec['numerical_DLLs']:assert Path(path).resolve()==directory/Path(path).name,'numerical module path drift'
    expected=None if job['capture_reference'] else Path(c['references'][job['layout']]['path']).read_bytes()
    size=c['metadata']['Q']['ne'][0]*32*c['q']*4;outputs=[]
    for row in rr['calls']:
        data=occurrence(n,row);assert len(data)==size and all(math.isfinite(x[0]) for x in struct.iter_unpack('<f',data)),'ordinary shape/finite'
        assert row['compute_status']==row['sync_status']==0 and row['begin']<=row['compute_return']<=row['sync_return']<=row['readback_return'] and row['sync_return']>row['begin'] and rr['QPC_frequency']>0,'completion/clock'
        actual_expected=Path(job['alternate_context']['reference']).read_bytes() if job.get('alternate_context') and row['index']%2 else expected
        if job.get('alternate_context'):
            current=Path(job['alternate_context']['root']) if row['index']%2 else Path(c['root'])
            for role in ROLES:assert (n/f"update_{row['index']}_{role}.bin").read_bytes()==(current/(role+'.bin')).read_bytes(),'alternate input readback'
        if actual_expected is not None:assert (data==actual_expected)==row['ordinary_exact'],'independent ordinary decision'
        outputs.append(data)
    expected_status='REFERENCE_CAPTURE' if job['capture_reference'] else 'QUALIFIED'
    qualified=rr['status']==expected_status and len(outputs)==job['warmups']+job['calls'] and (expected is None or all(x['ordinary_exact'] for x in rr['calls']))
    return rr,dict(status=rr['status'],numerical_qualified=qualified,output_occurrences=len(outputs),all_input_bytes_exact=True,all_placement_verified=True,all41_plugin_imports=True,all_graph_nodes_supported=True,graph_sha256=sha(n/'GRAPH.json'),record_sha256=sha(n/'RECORD.json'),observer_method=job['method'],output_sha256=[__import__('hashlib').sha256(x).hexdigest() for x in outputs])

def cas(n):
    folder=root()/'cas';folder.mkdir(exist_ok=True);rows=[]
    for p in n.glob('*.bin'):
        digest=sha(p);dest=folder/(digest+'.bin')
        if not dest.exists():os.link(p,dest)
        else:
            assert sha(dest)==digest and dest.stat().st_size==p.stat().st_size
            temp=p.with_suffix('.verified_link')
            try:os.link(dest,temp)
            except OSError as e:
                if getattr(e,'winerror',None)!=1142:raise
            else:os.replace(temp,p)
        rows.append(dict(file=p.name,bytes=p.stat().st_size,sha256=digest,cas=dest.relative_to(root()).as_posix()))
    save(n/'BLOBS.json',rows)

def execute(t,c,method,session):
    s,f=verify_freeze();guard(s);attempt=root()/'attempts'/t['task_id'];attempt.mkdir(parents=True,exist_ok=False)
    for row in c['inputs']:assert sha(Path(c['root'])/row['name'])==row['sha256'],'input source drift'
    capture=t['stage']=='reference';context=copy.deepcopy(c)
    if not capture:
        ref=Path(c['references'][t['layout']]['path']);assert sha(ref)==c['references'][t['layout']]['sha256']
    job=dict(spec=str(root()/'RUN_SPEC.json'),execution_id=s['execution_id'],stage=t['stage'],context=context,layout=t['layout'],lifecycle='persistent_inputs',method=method,warmups=t['warmups'],calls=t['measured_calls'],capture_reference=capture,graph_mode=t["graph_mode"],integrated_q_update=t.get("panel")=="T0" and t["stage"] in ["qualification","timed"],producer_source=c.get("producer_source"))
    job.update(profile=t.get('profile',False),cupti_path=s['cupti']['path'],cupti_sha256=s['cupti']['sha256']);
    if t.get('alternating'):job['alternate_context']=t['alternate_context']
    save(attempt/'JOB.json',job);save(attempt/'STARTED.json',dict(utc=utc(),task=t,actual_session=session,epoch=time.time(),native_sha256=f['native_sha256']))
    w=Child(helper());error=None
    try:w.run([str(V/'build/collector.exe'),'--gpu',str(attempt/'JOB.json'),str(attempt/'native')],attempt/'host',120,env(s,t['graph_mode']),s['host_RAM_bytes'],lambda:guard(s),log_cap=65536)
    except BaseException as e:error=repr(e)
    finally:w.terminate()
    lifetime=load(attempt/'host.LIFETIME.json');assert not load(attempt/'host.JOB_EVENTS.json')['errors'],'uncertain cleanup;globalstop'
    n=attempt/'native'
    if not (n/'RECORD.json').exists():
        save(attempt/'ENDED.json',dict(status='EXECUTION_FAILED',error=error,exit=lifetime['exit_code'],actual_calls=None));raise RuntimeError('native execution failed; inspect preserved attempt; no retry')
    rr,receipt=audit(n,c,job);assert rr['graph_mode']==t['graph_mode'];
    if job['profile']:save(attempt/'MODE_AUDIT.json',trace_audit(n,job))
    save(attempt/'EVIDENCE.json',receipt);cas(n)
    result=dict(status=receipt['status'],numerical_qualified=receipt['numerical_qualified'],error=error,exit=lifetime['exit_code'],actual_calls=len(rr['calls']),seconds=lifetime['seconds'],peak_commit_bytes=lifetime['peak_job_commit_bytes'])
    save(attempt/'ENDED.json',result)
    return result,attempt

def trace_audit(n,job):
    tr=load(n/'CUDA_TRACE.json');assert not tr['overflow'] and tr['dropped']==0 and tr['flush_status']==0,'trace loss'
    assert tr['module_sha256']==job['cupti_sha256'] and Path(tr['module_path']).resolve()==Path(job['cupti_path']).resolve()
    events=[e for e in tr['API_events'] if e['domain']==2 and e['site']==1]
    launches=[e for e in events if e['name'].startswith('cudaGraphLaunch') and e['status']==0]
    captures=[e for e in events if e['name'].startswith('cudaStreamBeginCapture') and e['status']==0]
    inst=[e for e in events if e['name'].startswith('cudaGraphInstantiate') and e['status']==0]
    end=[e for e in events if e['name'].startswith('cudaStreamEndCapture') and e['status']==0]
    steady=range(job['warmups'],job['warmups']+job['calls'])
    on=bool(captures and end and inst) and all(sum(e['call']==i for e in launches)==1 for i in steady) and not any(e['call'] in steady for e in captures+inst+end)
    off=not launches and not captures and not inst
    verified=on if job['graph_mode']=='ON' else off
    return dict(mode=job['graph_mode'],verified=verified,trace_sha256=sha(n/'CUDA_TRACE.json'),graph_sha256=sha(n/'GRAPH.json'),launch_count=len(launches),capture_count=len(captures),instantiate_count=len(inst),end_capture_count=len(end),formal_calls=list(steady),actual_kernel_records=sum(x['kind']==10 for x in tr['activities']),activity_enable=tr['activity_enable'],scope='CUPTI actual successful runtime API exits and every formal replay;profile timing excluded')

_last_storage=0
def guard(s):
    from lifecycle import process_commit
    global _last_storage
    assert time.time()-s['start_epoch']<s['global_seconds']-s['delivery_reserve_seconds'],'delivery reserve'
    assert process_commit()<s['host_RAM_bytes'],'controller memory'
    assert shutil.disk_usage(root()).free>=10*1024**3,'disk headroom'
    if time.monotonic()-_last_storage>30:
        identities={}
        for p in root().rglob('*'):
            if p.is_file():
                st=p.stat();identities[st.st_dev,st.st_ino]=((st.st_size+4095)//4096)*4096+4096
        assert sum(identities.values())<8*1024**3-512*1024**2,'bounded storage reserve'
        _last_storage=time.monotonic()

def verify_freeze():
    r=root();f=load(r/('FREEZE_REPAIR1.json' if (r/'FREEZE_REPAIR1.json').exists() else 'FREEZE.json'));s=load(r/'RUN_SPEC.json');assert s['run_id']=='rtx-dispatch-intervention-v1' and s['execution_id']==r.name
    for name,d in f['files'].items():assert sha(V/('build/'+name if (V/'build'/name).exists() else name))==d,'source drift '+name
    for key,name in [('plan_exact_sha256','plan.json'),('spec_sha256','RUN_SPEC.json'),('runtime_manifest_sha256','RUNTIME_MANIFEST.json'),('input_index_sha256','INPUTS.json'),('policy_sha256','EXECUTION_POLICY.json')]:assert sha(r/name)==f[key],name+' drift'
    return s,f

def freeze():
    r=root();assert not git('status','--porcelain','--untracked-files=no','--',str(V)),'commit before freeze'
    files=[p for p in V.iterdir() if p.suffix in ['.py','.h','.cpp','.md','.json'] and p.name not in ['LOCAL_RUN.json']]+list((V/'build').glob('*'))
    snap=r/'SOURCE';snap.mkdir()
    for p in files:shutil.copyfile(p,snap/p.name)
    s=load(r/'RUN_SPEC.json');external={}
    for folder in [Path(s['ggml_include']),Path(s['vendor_include'])/'nlohmann',Path(s['tool_root'])/'nvidia-cuda-cupti-cu12/nvidia/cuda_cupti/include',Path(s['tool_root'])/'nvidia-cuda-runtime-cu12/nvidia/cuda_runtime/include',Path(s['tool_root'])/'nvcc-headers-only/nvidia/cuda_nvcc/include']:
        for p in folder.rglob('*'):
            if p.is_file():external[str(p)]=sha(p)
    for p in [Path(s['compiler']['path']),Path(s['python']),Path(s['cupti']['path'])]:external[str(p)]=sha(p)
    save(r/'BUILD_DEPENDENCIES.json',external)
    save(r/'EXECUTION_POLICY.json',dict(run_id=s['run_id'],execution_id=s['execution_id'],mode='ON only;CUPTI qualification + alternating checks;clean hosts no tracer',observer='H1 preallocated outputs;every call full ordinary exact/finite;full input before/after',bounds=dict(native_hosts=358,graph_calls=11732,profile_attempts=24,native_timeout=120,memory=8*1024**3,raw=8*1024**3,total_seconds=21600,delivery_reserve=2700),reference='fresh two independent original unpadded serial captures/query;all padding matches same unpadded reference',qualification='2warm+32calls;two fresh hosts per unique cell/arm;failed arms retained not timed;no retry',statistics='paired host means;block bootstrap within two actual sessions;values equal weights;both controls;8 complete blocks for practical label;max(2%,1us,AA)',quiet='two endpoint samples5s apart/util<=5/temp<=55/AC/free>=max1GiB10%;up to10min fixed waits;whole block postcheck;clocks UNKNOWN',costs=dict(B0='completed graph sync-begin;resident_call secondary;KV materialization/upload/allocation separate',T0='single QPC readback-transaction_begin;copy/transpose+Q upload/completion+graph/full sync+ordinary readback;resident KV/mask;source Q production UNKNOWN')))
    save(r/'FREEZE.json',dict(commit=git('rev-parse','HEAD'),utc=utc(),files={p.name:sha(p) for p in files},plan_exact_sha256=sha(r/'plan.json'),spec_sha256=sha(r/'RUN_SPEC.json'),runtime_manifest_sha256=sha(r/'RUNTIME_MANIFEST.json'),input_index_sha256=sha(r/'INPUTS.json'),policy_sha256=sha(r/'EXECUTION_POLICY.json'),build_dependencies_sha256=sha(r/'BUILD_DEPENDENCIES.json'),native_sha256=sha(V/'build/collector.exe')))
    print('FROZEN',sha(r/'FREEZE.json'),flush=True)

def contexts():
    rows=load(root()/'INPUTS.json')
    if (root()/'REFERENCES.json').exists():
        refs=load(root()/'REFERENCES.json')
        for c in rows.values():
            for l in c['layouts']:c['references'][l]=refs[c['cell']]
    return rows

def task(cid,arm,stage,rep=0):
    p=load(root()/'plan.json');cell=next(c for c in p['cells'] if c['id']==cid);a=next(a for a in cell['arms'] if a['name']==arm)
    return dict(task_id=f'{stage}-{cid}-{arm}-r{rep}',cell=cid,panel=cell['panel'],arm=arm,stage=stage,layout=a['layout'],graph_mode='ON',warmups=2,measured_calls=32,rep=rep)

def stage(name):
    r=root();s,f=verify_freeze();assert not (r/'GPU_EXECUTION_CLOSED.json').exists(),'permanently closed';assert not (r/'WORKER.lock').exists(),'one worker';assert not (r/(name+'_STARTED.json')).exists(),'permanent start;no retry'
    # Exact build/runtime files reviewed before every phase. DLLs then held read-only.
    assert sha(r/'BUILD_DEPENDENCIES.json')==f['build_dependencies_sha256']
    for path,h in load(r/'BUILD_DEPENDENCIES.json').items():assert sha(path)==h,'build dependency identity'
    save(r/'WORKER.lock',dict(pid=os.getpid(),stage=name,utc=utc()));save(r/(name+'_STARTED.json'),dict(pid=os.getpid(),epoch=time.time(),utc=utc(),commit=git('rev-parse','HEAD'),freeze_sha256=sha(r/'FREEZE.json')))
    k,handles=lock_runtime(s);started=time.monotonic();done=[];rows=contexts();p=load(r/'plan.json');session=name+'-'+str(os.getpid())+'-'+utc();status='COMPLETE'
    def run(t,c):
        assert len(list((r/'attempts').glob('*/STARTED.json')))<358
        starts=[load(x)['task'] for x in (r/'attempts').glob('*/STARTED.json')]
        assert sum(x['warmups']+x['measured_calls'] for x in starts)+t['warmups']+t['measured_calls']<=11732
        assert sum(bool(x.get('profile')) for x in starts)+bool(t.get('profile'))<=24
        result,a=execute(t,c,'H1',session);done.append(t['task_id']);print(name,len(done),t['task_id'],result['status'],flush=True);return result,a
    try:
        if name=='reference':
            telemetry(s,name+'/pre');refs={};(r/'references').mkdir()
            for cell in p['cells']:
                parts=[]
                for j,one in enumerate(load(r/'serial'/cell['id']/'INDEX.json')):
                    pair=[]
                    for rep in [0,1]:
                        t=dict(task_id=f"reference-{cell['id']}-q{j}-r{rep}",stage='reference',panel=cell['panel'],layout='PQ',graph_mode='OFF',warmups=0,measured_calls=1)
                        result,a=run(t,one);assert result['numerical_qualified'];pair.append(occurrence(a/'native',load(a/'native/RECORD.json')['calls'][0]))
                    assert pair[0]==pair[1],'independent serial mismatch';parts.append(pair[0])
                dest=r/'references'/(cell['id']+'.bin');dest.write_bytes(b''.join(parts));refs[cell['id']]=dict(path=str(dest),sha256=sha(dest),bytes=dest.stat().st_size,independent_reference_hosts=cell['q']*2)
            save(r/'REFERENCES.json',refs)
        elif name=='qualification':
            assert load(r/'reference_ENDED.json')['status']=='COMPLETE';telemetry(s,name+'/pre');admit={}
            for cell in p['cells']:
                for ai in [0,2,3]:
                    arm=cell['arms'][ai]['name'];c=rows[cell['id']+'/'+arm];key=c['case_id'];results=[];attempts=[];proof=[]
                    for rep in [0,1]:
                        t=task(cell['id'],arm,'qualification',rep);t['profile']=cell['value']==0 and (cell['panel']=='B0' or rep==0)
                        result,a=run(t,c);results.append(result['numerical_qualified']);attempts.append(a.name)
                        if t['profile']:proof.append(load(a/'MODE_AUDIT.json')['verified'])
                    admit[key]=dict(numerical=all(results),hosts=results,attempts=attempts,direct_mode_proofs=proof)
            save(r/'QUALIFICATION.json',admit)
        elif name=='capability':
            telemetry(s,name+'/pre');eligible=load(r/'QUALIFICATION.json');out=[]
            for cell in p['cells']:
                if cell['panel']!='T0' or cell['value']!=0:continue
                alt=cell['id'][:-1]+'1'
                for ai in [0,2,3]:
                    arm=cell['arms'][ai]['name'];key=cell['id']+'/'+arm
                    if not eligible[key]['numerical']:continue
                    t=task(cell['id'],arm,'capability');t.update(profile=True,alternating=True,measured_calls=6,alternate_context=dict(root=rows[alt+'/'+arm]['root'],reference=rows[alt+'/'+arm]['references'][t['layout']]['path']))
                    result,a=run(t,rows[key]);mode=load(a/'MODE_AUDIT.json')['verified'];out.append(dict(case=key,numerical=result['numerical_qualified'],mode_verified=mode,attempt=a.name))
            save(r/'CAPABILITY.json',out)
        else:
            admission=load(r/'ADMISSION.json');assert git('merge-base',admission['commit'],'HEAD')==admission['commit'],'admission commit ancestry';assert sha(r/'QUALIFICATION.json')==admission['qualification_sha256'] and sha(r/'CAPABILITY.json')==admission['capability_sha256']
            selected=[t for t in p['timed_jobs'] if t['session']==int(name[-1])];save(r/(name+'_SESSION.json'),dict(session_id=session,planned_session=int(name[-1]),utc=utc(),blocks=sorted({t['block'] for t in selected})))
            for b in sorted({t['block'] for t in selected}):
                pre=quiet(s,name+'/'+str(b))
                if not pre:status='QUIET_WINDOW_UNAVAILABLE';break
                completed=[];failed=[]
                for planned in [t for t in selected if t['block']==b]:
                    cell=next(c for c in p['cells'] if c['id']==planned['cell']);arm=next(a for a in cell['arms'] if a['name']==planned['arm']);canonical=cell['arms'][0]['name'] if planned['arm']==cell['arms'][1]['name'] else planned['arm'];key=cell['id']+'/'+canonical
                    if not admission['arms'][key]['eligible']:continue
                    t=dict(planned,stage='timed',layout=arm['layout'],graph_mode='ON',measured_calls=planned['calls']);result,a=run(t,rows[key]);completed.append(t['task_id'])
                    if not result['numerical_qualified']:failed.append(t['task_id'])
                post=telemetry(s,name+'/'+str(b)+'/post');save(r/f'{name}_BLOCK_{b}.json',dict(pre=pre,post=post,environment_qualified=post['quiet'],completed=completed,failed=failed,session_id=session))
                if failed:status='FORMAL_FAILURE_NO_REPLACEMENT';break
        save(r/(name+'_ENDED.json'),dict(status=status,tasks=done,hosts=len(done),seconds=time.monotonic()-started,utc=utc()))
    except BaseException as e:
        save(r/(name+'_FAILED.json'),dict(reason=repr(e),completed=done,seconds=time.monotonic()-started,utc=utc()));raise
    finally:
        for h in handles:k.CloseHandle(h)
        (r/'WORKER.lock').rename(r/(name+'_WORKER_CLOSED.json'))

def admission():
    r=root();q=load(r/'QUALIFICATION.json');cap=load(r/'CAPABILITY.json');p=load(r/'plan.json');arms={}
    for key,row in q.items():
        cell=next(c for c in p['cells'] if key.startswith(c['id']+'/'));v0key=key.replace('-v1/','-v0/');mode=bool(q[v0key]['direct_mode_proofs']) and all(q[v0key]['direct_mode_proofs']);alternating=True if cell['panel']=='B0' else any(x['case']==v0key and x['numerical'] and x['mode_verified'] for x in cap)
        arms[key]=dict(eligible=row['numerical'] and mode and alternating,numerical=row['numerical'],mode_verified=mode,alternating_verified=alternating,reason='PASS' if row['numerical'] and mode and alternating else 'INFEASIBLE_EXACT_REFERENCE' if not row['numerical'] else 'MODE_UNVERIFIED')
    assert not git('status','--porcelain','--untracked-files=no','--',str(V));save(r/'ADMISSION.json',dict(commit=git('rev-parse','HEAD'),utc=utc(),arms=arms,qualification_sha256=sha(r/'QUALIFICATION.json'),capability_sha256=sha(r/'CAPABILITY.json'),schedule_sha256=sha(r/'plan.json'),reference_sha256=sha(r/'REFERENCES.json'),failure_replacement=False))
    print('ADMISSION',sha(r/'ADMISSION.json'))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze','reference','qualification','capability','admission','collect0','collect1']);a=ap.parse_args();freeze() if a.action=='freeze' else admission() if a.action=='admission' else stage(a.action)
