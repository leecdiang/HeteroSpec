"""Single-worker RTX execution adapter. Each task is attempted at most once.

New UUID only; no old entrypoint is imported. Large replay analysis stays CPU-only.
"""
import argparse,collections,copy,ctypes,datetime,json,math,os,shutil,struct,subprocess,sys,time
from pathlib import Path
from common import V,load,save,sha
from lifecycle import Child
from prepare_rtx import root,ROLES,LAYOUTS
from study import validate_plan

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def git(*args):return subprocess.check_output(['git','-C',str(V.parents[1]),*args],text=True).strip()
def env(s):
    e=os.environ.copy();e['GGML_CUDA_DISABLE_GRAPHS']='1';e['PATH']=s['runtime_directory']+';'+e['PATH'];e['PYTHONDONTWRITEBYTECODE']='1';return e
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

def freeze():
    r=root();assert not git('status','--porcelain','--untracked-files=no','--',str(V)),'commit implementation before freeze'
    files=[p for p in V.iterdir() if p.suffix in ['.py','.h','.cpp']]+[V/'build/collector.exe',V/'build/address_cpu.exe']
    dest=r/'SOURCE';dest.mkdir()
    for p in files:shutil.copyfile(p,dest/p.name)
    s=load(r/'RUN_SPEC.json');save(r/'EXECUTION_POLICY.json',dict(run_id=s['run_id'],execution_id=s['execution_id'],H0='legacy checked replay;per-call STARTED JSON and output allocation/file write',H1='preallocated <=64 output buffers and native samples;all file/JSON flush after replay',views=['resident_graph=(c-a)/QPC','resident_call=(d-a)/QPC','input-inclusive first-warmup materialize+upload+completedcall phase sum'],warmups_qualification=2,qualification_calls=32,timed_warmups=8,timed_calls=30,timeout_seconds=120,host_RAM_bytes=8*1024**3,storage_bytes=8*1024**3,quiet='two<=5%<=55C AC samples5s apart;wait up to10min with30s spacing;wholeblock postcheck;no latency-based exclusion',clock='QPC monotonic strict positive completedgraph;no kernel time claims',numerical='independent serial q1 exact ordinary;all full bytes input pre/post;placement/module/IAT/support checks',observer_checks='every call readback and exact/finite checks after completed graph;all occurrences retained',global_wall_seconds=28800,closure_reserve_seconds=3600,optional_holdout='unopened before prediction freeze'))
    save(r/'FREEZE.json',dict(commit=git('rev-parse','HEAD'),utc=utc(),files={p.name:sha(p) for p in files},plan_sha256=load(r/'plan.json')['plan_sha256'],plan_exact_sha256=sha(r/'plan.json'),spec_sha256=sha(r/'RUN_SPEC.json'),runtime_manifest_sha256=sha(r/'RUNTIME_MANIFEST.json'),input_index_sha256=sha(r/'INPUTS.json'),policy_sha256=sha(r/'EXECUTION_POLICY.json'),native_sha256=sha(V/'build/collector.exe')))
    print('Execution freeze',sha(r/'FREEZE.json'),flush=True)

def verify_freeze():
    r=root();f=load(r/'FREEZE.json');s=load(r/'RUN_SPEC.json');assert s['run_id']=='rtx-boundary-confirmation-v1' and s['execution_id']==r.name
    for name,digest in f['files'].items():assert sha(V/('build/'+name if name.endswith('.exe') else name))==digest,'source/host drift '+name
    for key,name in [('plan_exact_sha256','plan.json'),('spec_sha256','RUN_SPEC.json'),('runtime_manifest_sha256','RUNTIME_MANIFEST.json'),('input_index_sha256','INPUTS.json'),('policy_sha256','EXECUTION_POLICY.json')]:assert sha(r/name)==f[key],name+' drift'
    return s,f

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
        if expected is not None:assert (data==expected)==row['ordinary_exact'],'independent ordinary decision'
        outputs.append(data)
    expected_status='REFERENCE_CAPTURE' if job['capture_reference'] else 'QUALIFIED'
    qualified=rr['status']==expected_status and len(outputs)==job['warmups']+job['calls'] and (expected is None or all(x==expected for x in outputs))
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
    job=dict(spec=str(root()/'RUN_SPEC.json'),execution_id=s['execution_id'],stage=t['stage'],context=context,layout=t['layout'],lifecycle='persistent_inputs',method=method,warmups=t['warmups'],calls=t['measured_calls'],capture_reference=capture)
    save(attempt/'JOB.json',job);save(attempt/'STARTED.json',dict(utc=utc(),task=t,actual_session=session,epoch=time.time(),native_sha256=f['native_sha256']))
    w=Child(helper());error=None
    try:w.run([str(V/'build/collector.exe'),'--gpu',str(attempt/'JOB.json'),str(attempt/'native')],attempt/'host',120,env(s),s['host_RAM_bytes'],lambda:guard(s),log_cap=65536)
    except BaseException as e:error=repr(e)
    finally:w.terminate()
    lifetime=load(attempt/'host.LIFETIME.json');assert not load(attempt/'host.JOB_EVENTS.json')['errors'],'uncertain cleanup;globalstop'
    n=attempt/'native'
    if not (n/'RECORD.json').exists():
        save(attempt/'ENDED.json',dict(status='EXECUTION_FAILED',error=error,exit=lifetime['exit_code'],actual_calls=None));raise RuntimeError('native execution failed; inspect preserved attempt; no retry')
    rr,receipt=audit(n,c,job);save(attempt/'EVIDENCE.json',receipt);cas(n)
    result=dict(status=receipt['status'],numerical_qualified=receipt['numerical_qualified'],error=error,exit=lifetime['exit_code'],actual_calls=len(rr['calls']),seconds=lifetime['seconds'],peak_commit_bytes=lifetime['peak_job_commit_bytes'])
    save(attempt/'ENDED.json',result)
    if t['stage'] in ['aa_pilot','confirm','holdout']:
        row=dict(task_id=t['task_id'],attempt_id=str(attempt.name),plan_sha256=f['plan_sha256'],observed_layout=rr['layout'],method=method,cost_view='resident_graph',status='QUALIFIED' if receipt['numerical_qualified'] else 'NUMERICAL_FAILURE',numerical_qualified=receipt['numerical_qualified'],environment_qualified=True,session_id=session,measured_us=[(x['sync_return']-x['begin'])*1e6/rr['QPC_frequency'] for x in rr['calls'] if not x['warmup']],host_binary_sha256=f['native_sha256'],runtime_manifest_sha256=f['runtime_manifest_sha256'],execution_policy_sha256=f['policy_sha256'],input_sha256=c['input_sha256'],reference_sha256=c['references'][t['layout']]['sha256'],evidence_receipt_sha256=sha(attempt/'EVIDENCE.json'),failure_reason=None if receipt['numerical_qualified'] else 'ordinary/input/placement/control')
        save(attempt/'OBSERVATION.json',row)
    return result,attempt

def referenced_inputs():
    c=load(root()/'INPUTS.json');refs=load(root()/'REFERENCES.json')
    for cid,row in refs.items():
        for l in LAYOUTS:c[cid]['references'][l]=dict(path=row['path'],sha256=row['sha256'])
    return c

def stage(name):
    s,f=verify_freeze();r=root();plan=load(r/'plan.json');validate_plan(plan);assert not (r/'WORKER.lock').exists(),'oneGPUworker';save(r/'WORKER.lock',dict(pid=os.getpid(),stage=name,utc=utc()));save(r/(name+'_STARTED.json'),dict(pid=os.getpid(),utc=utc(),epoch=time.time(),commit=git('rev-parse','HEAD')));k,handles=lock_runtime(s);begin=time.monotonic();status='COMPLETE';rows=[]
    try:
        c=load(r/'INPUTS.json') if name=='reference' else referenced_inputs()
        if name=='reference':
            telemetry(s,'reference/pre');refs={}
            for cid,context in c.items():
                parts=[]
                for j,serialroot in enumerate(context['serial_roots']):
                    one=copy.deepcopy(context);one.update(id=cid+f'/serial{j}',q=1,root=serialroot,metadata=load(Path(serialroot)/'snapshot.json'));one['inputs']=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(Path(serialroot).iterdir()) if p.is_file()];values=[]
                    for t in [t for t in plan['tasks'] if t['stage']=='reference' and t['case_id']==cid and t['query_index']==j]:
                        result,a=execute(t,one,'H1','reference-'+str(os.getpid()));assert result['numerical_qualified'],'reference capture failed';values.append(occurrence(a/'native',load(a/'native/RECORD.json')['calls'][0]));rows.append(t['task_id'])
                    assert len(values)==2 and values[0]==values[1],'independent reference mismatch';parts.append(values[0])
                data=b''.join(parts);p=Path(context['root'])/'ordinary_reference.bin'
                with p.open('xb') as file:file.write(data)
                if context['mask']=='single_visible':
                    import numpy as np
                    d,S,g,q=context['d'],context['keys'],context['Hkv'],context['q'];vv=np.fromfile(Path(context['root'])/'V.bin',dtype='<f2').reshape(g,d,S);out=[]
                    for j in range(q):
                        acc=np.zeros((32,d),dtype='<f4');sel=(S-q+j)%S
                        for index in range(S):acc=np.float32(acc+np.float32(vv[np.arange(32)//(32//g),:,index].astype('<f4')*np.float32(index==sel)))
                        out.append(acc)
                    assert np.stack(out).tobytes()==data,'full single-visible oracle'
                refs[cid]=dict(path=str(p),sha256=sha(p),bytes=len(data),independent_reference_hosts=2*context['q']);print('reference',cid,len(rows),flush=True)
            save(r/'REFERENCES.json',refs)
        elif name=='qualification':
            telemetry(s,'qualification/pre');eligible={}
            for t in [t for t in plan['tasks'] if t['stage']=='qualification' and not t['optional']]:
                key=(t['case_id'],t['layout'],t['method'])
                if eligible.get('|'.join(key)) is False:continue
                result,a=execute(t,c[t['case_id']],t['method'],'qualification-'+str(os.getpid()));rows.append(t['task_id']);eligible['|'.join(key)]=result['numerical_qualified'];print('qualification',t['task_id'],len(rows),result['status'],flush=True)
            save(r/'QUALIFICATION.json',eligible)
        else:
            stage_name='aa_pilot' if name=='aa_pilot' else 'confirm';selected='H1' if name=='aa_pilot' else load(r/'METHOD_DECISION.json')['selected_method'];eligible=load(r/'QUALIFICATION.json');session=name+'-'+str(os.getpid())+'-'+utc();blocks=range(6) if name=='aa_pilot' else range(0,4) if name=='confirm0' else range(4,8)
            save(r/(name+'_SESSION.json'),dict(session_id=session,utc_start=utc(),pid=os.getpid(),blocks=list(blocks),method=selected))
            for b in blocks:
                pre=quiet(s,name+'/'+str(b))
                if not pre:status='QUIET_WINDOW_UNAVAILABLE';break
                blockrows=[]
                for t in [t for t in plan['tasks'] if t['stage']==stage_name and not t['optional'] and t['block']==b]:
                    method=t['method'] if stage_name=='aa_pilot' else selected
                    if not eligible.get('|'.join([t['case_id'],t['layout'],method]),False):continue
                    result,a=execute(t,c[t['case_id']],method,session);rows.append(t['task_id']);blockrows.append(t['task_id']);print(name,b,t['task_id'],len(rows),result['status'],flush=True)
                    if not result['numerical_qualified']:eligible['|'.join([t['case_id'],t['layout'],method])]=False
                post=telemetry(s,name+'/'+str(b)+'/post');save(r/f'{name}_BLOCK_{b}.json',dict(pre=pre,post=post,environment_qualified=post['quiet'],tasks=blockrows,session_id=session))
        save(r/(name+'_ENDED.json'),dict(status=status,hosts=len(rows),tasks=rows,seconds=time.monotonic()-begin,utc=utc()))
    except BaseException as e:
        save(r/(name+'_FAILED.json'),dict(reason=repr(e),completed_tasks=rows,seconds=time.monotonic()-begin,utc=utc()));raise
    finally:
        for h in handles:k.CloseHandle(h)
        (r/'WORKER.lock').rename(r/(name+'_WORKER_CLOSED.json'))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze','reference','qualification','aa_pilot','confirm0','confirm1']);args=ap.parse_args();freeze() if args.action=='freeze' else stage(args.action)
