"""Single-worker RTX execution adapter. Each task is attempted at most once.

New UUID only; no old entrypoint is imported. Large replay analysis stays CPU-only.
"""
import argparse,collections,copy,ctypes,datetime,json,math,os,shutil,struct,subprocess,sys,time
from pathlib import Path
from common import V,load,save,sha
from lifecycle import Child
from prepare_rtx import root,ROLES,LAYOUTS
from plan import validate as validate_plan

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
    rr=load(n/'RECORD.json');g=load(n/'GRAPH.json');assert rr['execution_id']==job['execution_id'] and rr['layout']==job['layout'] and rr['observer_method']==job['method']
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
    job=dict(spec=str(root()/'RUN_SPEC.json'),execution_id=s['execution_id'],stage=t['stage'],context=context,layout=t['layout'],lifecycle='persistent_inputs',method=method,warmups=t['warmups'],calls=t['measured_calls'],capture_reference=capture,graph_mode=t["graph_mode"],integrated_q_update=t["stage"].startswith("producer"),producer_source=str(root()/"inputs"/f"q{c['q']}-k256-v{c['realization']}"/"Q.bin"))
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

def freeze():
    r=root();assert not git('status','--porcelain','--untracked-files=no','--',str(V)),'commit implementation before freeze'
    files=[p for p in V.iterdir() if p.suffix in ['.py','.h','.cpp','.txt']]+[V/'build/collector.exe',V/'build/address_cpu.exe']
    dest=r/'SOURCE';dest.mkdir()
    for p in files:shutil.copyfile(p,dest/p.name)
    s=load(r/'RUN_SPEC.json')
    save(r/'EXECUTION_POLICY.json',dict(run_id=s['run_id'],execution_id=s['execution_id'],graph_mode='DUAL;OFF env=1;ON requires successful actual CUPTI capture/end/instantiate/replay,all signatures and alternating updates',observer='H1 preallocated64 buffers/records;every call readback/finite/exact;files/JSON after loop',quiet='reported identity/free>=max1GiB10%/util<=5/temp<=55/AC;two samples5s apart up to10min30s spacing;wholeblock postcheck;clocks UNKNOWN',views=['resident_graph=(sync-begin)/QPC','resident_call=(readback-begin)/QPC','integrated_q_update=(readback-transaction_begin)/QPC;copy/transpose+Q upload+graph+sync+readback;KV/mask resident','first_use_phase_sum=CPU materialization+initial upload+first completedcall;not integrated'],capture='profiled qualification first two warmups;formal calls require no recapture and one graph launch each;clean hosts exclude CUPTI',warmups_qualification=2,qualification_calls=32,timed_warmups=8,timed_calls=30,timeout_seconds=120,host_RAM_bytes=8*1024**3,storage_bytes=8*1024**3,global_wall_seconds=21600,closure_reserve_seconds=2700,numerical='fresh two-host serial q1 exact complete ordinary',statistics='plan analyze.py descriptive bootstrap blocks within two actual sessions;both QB labels same implementation;2%+1us and matched AA guard',optional_producer='requires separate prospective producer decision before GPU tasks'))
    save(r/'MODE_EVIDENCE.json',dict(status='PENDING_ACTUAL_CUPTI_ADMISSION',OFF='GGML_CUDA_DISABLE_GRAPHS=1',ON='variable absent;requires actual successful capture/end/instantiate/launch and no formal recapture',cupti=s['cupti'],extra_capability_hosts=4,capability_calls_per_host=8,profile_qualification_hosts=21,profile_capability_hosts=2,scope='mode eligibility only after raw trace evidence, never flags alone'))
    save(r/'FREEZE.json',dict(commit=git('rev-parse','HEAD'),utc=utc(),files={p.name:sha(p) for p in files},plan_sha256=load(r/'plan.json')['plan_sha256'],plan_exact_sha256=sha(r/'plan.json'),spec_sha256=sha(r/'RUN_SPEC.json'),runtime_manifest_sha256=sha(r/'RUNTIME_MANIFEST.json'),input_index_sha256=sha(r/'INPUTS.json'),policy_sha256=sha(r/'EXECUTION_POLICY.json'),mode_sha256=sha(r/'MODE_EVIDENCE.json'),native_sha256=sha(V/'build/collector.exe')))
    print('FROZEN',sha(r/'FREEZE.json'),flush=True)

def verify_freeze():
    r=root();f=load(r/'FREEZE.json');s=load(r/'RUN_SPEC.json');assert s['run_id']=='rtx-mechanism-baselines-v1' and s['execution_id']==r.name
    for name,d in f['files'].items():assert sha(V/('build/'+name if name.endswith('.exe') else name))==d,'source drift '+name
    for key,name in [('plan_exact_sha256','plan.json'),('spec_sha256','RUN_SPEC.json'),('runtime_manifest_sha256','RUNTIME_MANIFEST.json'),('input_index_sha256','INPUTS.json'),('policy_sha256','EXECUTION_POLICY.json'),('mode_sha256','MODE_EVIDENCE.json')]:assert sha(r/name)==f[key],name+' drift'
    return s,f

def contexts():
    rows=load(root()/'INPUTS.json')
    for cid,ref in (load(root()/'REFERENCES.json') if (root()/'REFERENCES.json').exists() else {}).items():
        for layout in LAYOUTS:rows[cid]['references'][layout]=dict(path=ref['path'],sha256=ref['sha256'])
    return rows

def case_for(t,rows):
    if not t['case_id'].startswith('producer-'):return rows[t['case_id']]
    q=int(t['case_id'].split('-')[1][1:]);v=int(t['case_id'][-1]);storage=t.get('storage','permuted')
    source=rows[f'q{q}-'+('compact' if storage=='compact' else 'k256')+f'-v{v}'];c=copy.deepcopy(source)
    if t['stage']!='reference':
        ref=rows[f'q{q}-k256-v{v}']['references'];c['references']=copy.deepcopy(ref)
    return c

def stage(name):
    s,f=verify_freeze();r=root();p=load(r/'plan.json');validate_plan(p);assert not (r/'WORKER.lock').exists(),'one worker'
    assert not (r/(name+'_STARTED.json')).exists(),'permanent attempt;no retry'
    optional=name.startswith('producer')
    if optional:assert (r/'PRODUCER_DECISION.json').exists(),'prospective producer freeze'
    save(r/'WORKER.lock',dict(pid=os.getpid(),stage=name,utc=utc()));save(r/(name+'_STARTED.json'),dict(pid=os.getpid(),epoch=time.time(),utc=utc(),commit=git('rev-parse','HEAD')))
    k,handles=lock_runtime(s);started=time.monotonic();done=[];status='COMPLETE';rows=contexts();session=name+'-'+str(os.getpid())+'-'+utc()
    try:
        if name in ['reference','producer_reference']:
            telemetry(s,name+'/pre');refs=load(r/'REFERENCES.json') if (r/'REFERENCES.json').exists() else {};selected=[t for t in p['tasks'] if t['stage']=='reference' and t['optional']==optional];parts={}
            for t in selected:
                base=case_for(t,rows);one=copy.deepcopy(base);sub=base['serial_roots'][t['query_index']];one.update(id=base['id']+'/serial'+str(t['query_index']),q=1,root=sub,metadata=load(Path(sub)/'snapshot.json'));one['inputs']=[dict(name=a.name,bytes=a.stat().st_size,sha256=sha(a)) for a in sorted(Path(sub).iterdir()) if a.is_file()]
                result,a=execute(t,one,'H1',session);assert result['numerical_qualified'],'serial capture';done.append(t['task_id']);data=occurrence(a/'native',load(a/'native/RECORD.json')['calls'][0]);key=(base['case_id'],t['query_index']);parts.setdefault(key,[]).append(data);assert all(x==data for x in parts[key]),'serial independent mismatch'
            for cid in sorted({x[0] for x in parts}):
                c=rows[cid];pieces=[parts[cid,j] for j in range(c['q'])];assert all(len(x)==2 for x in pieces);dest=Path(c['root'])/'ordinary_reference.bin'
                with dest.open('xb') as file:file.write(b''.join(x[0] for x in pieces))
                refs[cid]=dict(path=str(dest),sha256=sha(dest),bytes=dest.stat().st_size,independent_hosts=2*c['q'])
            save(r/('PRODUCER_REFERENCES.json' if optional else 'REFERENCES.json'),refs)
        elif name=='capability':
            telemetry(s,'capability/pre');outcomes=[]
            for mode in ['OFF','ON']:
                for layout in ['QB','QH_C']:
                    c=rows['q2-k256-v0'];alt=rows['q2-k256-v1'];t=dict(task_id='capability-'+mode+'-'+layout,stage='capability',graph_mode=mode,case_id=c['case_id'],layout=layout,warmups=2,measured_calls=6,profile=mode=='ON',alternating=True,alternate_context=dict(root=alt['root'],reference=alt['references'][layout]['path']))
                    result,a=execute(t,c,'H1',session);done.append(t['task_id']);assert result['numerical_qualified'],'alternating value control failed'
                    if mode=='ON':assert load(a/'MODE_AUDIT.json')['verified'],'actual ON capability not established'
                    outcomes.append(dict(mode=mode,layout=layout,qualified=True,attempt=t['task_id']))
            save(r/'CAPABILITY_ADMISSION.json',dict(outcomes=outcomes,status='PASS',profile_hosts=2,native_hosts=4,graph_calls=32))
        elif name in ['qualification','producer_qualification']:
            assert load(r/'CAPABILITY_ADMISSION.json')['status']=='PASS','capability first'
            if optional:
                extra=load(r/'PRODUCER_REFERENCES.json')
                for cid,ref in extra.items():
                    if cid in rows:
                        for l in LAYOUTS:rows[cid]['references'][l]=dict(path=ref['path'],sha256=ref['sha256'])
            telemetry(s,name+'/pre');eligible={}
            for t in [t for t in p['tasks'] if t['stage']==name and t['optional']==optional]:
                c=case_for(t,rows);key=t['case_id']+'|'+t['arm']+'|'+t['graph_mode']
                t=copy.deepcopy(t);t['profile']=not optional and t['block']==0 and (t['graph_mode']=='ON' and t['case_id'].endswith('v0') or t['graph_mode']=='OFF' and t['layout']=='QB' and t['case_id'] in ['q2-k1023-v0','q2-k1024-v0','q2-k1025-v0'])
                result,a=execute(t,c,'H1',session);done.append(t['task_id']);eligible.setdefault(key,[]).append(result['numerical_qualified']);print(name,len(done),t['task_id'],result['status'],flush=True)
                assert result['numerical_qualified'],'affected cell numerical failure;stop no retry'
                if t['profile']:assert load(a/'MODE_AUDIT.json')['verified'],'requested graph mode not verified'
            save(r/(name.upper()+'.json'),eligible)
        else:
            st='producer' if optional else 'confirm';eligible=load(r/('PRODUCER_QUALIFICATION.json' if optional else 'QUALIFICATION.json'));blocks=range(0,4) if name.endswith('0') else range(4,8)
            if optional:
                for cid,ref in load(r/'PRODUCER_REFERENCES.json').items():
                    if cid in rows:
                        for l in LAYOUTS:rows[cid]['references'][l]=dict(path=ref['path'],sha256=ref['sha256'])
            save(r/(name+'_SESSION.json'),dict(session_id=session,blocks=list(blocks),utc=utc()))
            for b in blocks:
                pre=quiet(s,name+'/'+str(b))
                if not pre:status='QUIET_WINDOW_UNAVAILABLE';break
                completed=[]
                for t in [t for t in p['tasks'] if t['stage']==st and t['block']==b]:
                    key=t['case_id']+'|'+(t['arm'] if optional else t['layout'])+'|'+t['graph_mode'];assert eligible.get(key)==[True,True],'two independent qualified hosts required'
                    result,a=execute(t,case_for(t,rows),'H1',session);done.append(t['task_id']);completed.append(t['task_id']);print(name,b,len(done),t['task_id'],result['status'],flush=True);assert result['numerical_qualified'],'timed failure;no retry'
                post=telemetry(s,name+'/'+str(b)+'/post');save(r/f'{name}_BLOCK_{b}.json',dict(pre=pre,post=post,environment_qualified=post['quiet'],tasks=completed,session_id=session))
        save(r/(name+'_ENDED.json'),dict(status=status,tasks=done,hosts=len(done),seconds=time.monotonic()-started,utc=utc()))
    except BaseException as e:
        save(r/(name+'_FAILED.json'),dict(reason=repr(e),completed_tasks=done,seconds=time.monotonic()-started,utc=utc()));raise
    finally:
        for h in handles:k.CloseHandle(h)
        (r/'WORKER.lock').rename(r/(name+'_WORKER_CLOSED.json'))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze','reference','capability','qualification','confirm0','confirm1','producer_reference','producer_qualification','producer0','producer1']);a=ap.parse_args();freeze() if a.action=='freeze' else stage(a.action)
