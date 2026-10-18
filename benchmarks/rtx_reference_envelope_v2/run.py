"""Single-worker PR120 entry: new development and independently frozen blocks."""
import argparse,ctypes,datetime,hashlib,itertools,json,math,os,random,shutil,subprocess,sys,time
from pathlib import Path
from common import V,load,save,sha
from lifecycle import Child

LAYOUTS=['PQ','QB','QH_C']
def root():return Path(os.environ.get('HETEROSPEC_RUN_ROOT',load(V/'LOCAL_RUN.json')['root']))
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def env(spec):
    e=os.environ.copy();e['GGML_CUDA_DISABLE_GRAPHS']='1';e['PATH']=spec['runtime_directory']+';'+e['PATH'];e['PYTHONDONTWRITEBYTECODE']='1';return e
def git(*args):return subprocess.check_output(['git','-C',str(V.parents[1]),*args]).decode().strip()
def guard(spec):
    assert time.time()-spec['start_epoch']<spec['global_seconds']-spec['delivery_reserve_seconds'],'delivery reserve reached'
    assert shutil.disk_usage(root()).free>=10*1024**3,'disk headroom'
def runtime_locks(spec):
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];k.CreateFileW.restype=ctypes.c_void_p
    handles=[]
    for name,digest in spec['numerical_DLLs'].items():
        p=Path(spec['runtime_directory'])/name;h=k.CreateFileW(str(p),0x80000000,1,None,3,0,None);assert h and h!=ctypes.c_void_p(-1).value;assert sha(p)==digest;handles.append(h)
    return handles
def helper():
    p=Path(os.environ['SystemRoot'])/'System32/conhost.exe';return dict(path=str(p),sha256=sha(p))
def telemetry(spec,label):
    dest=root()/'environment';dest.mkdir(exist_ok=True);i=len(list(dest.glob('*.json')))
    cmd=[str(Path(os.environ['SystemRoot'])/'System32/nvidia-smi.exe'),'--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu,clocks.sm,power.draw','--format=csv,noheader,nounits']
    begin=time.perf_counter();p=subprocess.run(cmd,capture_output=True,timeout=10,env=env(spec));r=dict(label=label,utc=now(),command=cmd,seconds=time.perf_counter()-begin,exit=p.returncode,stdout=p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace'))
    class Power(ctypes.Structure):_fields_=[('AC',ctypes.c_ubyte),('flag',ctypes.c_ubyte),('percent',ctypes.c_ubyte),('reserved',ctypes.c_ubyte),('life',ctypes.c_uint32),('full',ctypes.c_uint32)]
    power=Power();r['power_observed']=bool(ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(power)));r['AC']=power.AC
    if p.returncode==0:
        fields=r['stdout'].strip().split(',');r.update(gpu=fields[0].strip(),driver=fields[1].strip(),total_MiB=float(fields[2]),used_MiB=float(fields[3]),utilization=float(fields[4]),temperature=float(fields[5]));r['safe_memory']=r['total_MiB']-r['used_MiB']>=max(1024,r['total_MiB']*.1);r['quiet']=r['safe_memory'] and r['utilization']<=5 and r['temperature']<=55 and r['AC']==1
    save(dest/f'{i:04d}.json',r);return r
def quiet(spec,block):
    begin=time.monotonic()
    while True:
        guard(spec);a=telemetry(spec,f'T1/{block}/pre1');time.sleep(5);b=telemetry(spec,f'T1/{block}/pre2')
        assert a['exit']==b['exit']==0,'timing environment telemetry unavailable'
        if a['quiet'] and b['quiet']:return [a,b]
        if time.monotonic()-begin+30>=600:raise RuntimeError('quiet window unavailable in10min')
        time.sleep(30)
def freeze(spec,stage,extra):
    assert not git('status','--porcelain','--untracked-files=no','--','benchmarks/rtx_reference_envelope_v2'),'commit implementation before formal blocks'
    files=[p for p in V.iterdir() if p.suffix in ['.py','.cpp','.h']]+[V/'build/native.exe']
    r=dict(stage=stage,UTC=now(),git=git('rev-parse','HEAD'),files={p.name:sha(p) for p in files},spec_sha256=sha(root()/'RUN_SPEC.json'),lifecycle='persistent_inputs',reference='PR116 exact ordinary bytes;exposed fixed24',cost_views=['resident_graph','resident_call','input_inclusive_first_call_phase_sum'],practical_ratio=1.02,practical_us=1.0,**extra)
    save(root()/(stage+'_FREEZE.json'),r);return r
def dedup(directory):
    cas=root()/'cas';cas.mkdir(exist_ok=True);rows=[]
    for p in directory.glob('*.bin'):
        digest=sha(p);target=cas/(digest+'.bin')
        if not target.exists():os.link(p,target)
        else:
            assert target.stat().st_size==p.stat().st_size and sha(target)==digest
            if not os.path.samefile(p,target):
                temporary=p.with_suffix('.verified_link')
                try:os.link(target,temporary)
                except OSError as exc:
                    if getattr(exc,'winerror',None)!=1142:raise
                    # NTFS hardlink ceiling:keep this already verified occurrence
                    # as an ordinary file. No GPU/re-execution or byte change.
                else:os.replace(temporary,p)
        rows.append(dict(name=p.name,bytes=p.stat().st_size,sha256=digest,cas=target.relative_to(root()).as_posix()))
    save(directory/'BLOBS.json',rows)
def invoke(spec,stage,context,layout,life,warm,calls,block=None,diagnostic=False):
    guard(spec)
    if stage in ['N1','T1']:
        frozen=load(root()/(stage+'_FREEZE.json'))
        repair=load(root()/'T1_RETENTION_AMENDMENT.json') if stage=='T1' and (root()/'T1_RETENTION_AMENDMENT.json').exists() else None
        for name,digest in frozen['files'].items():
            if repair and name=='run.py':
                assert repair['old_run_py_sha256']==digest and repair['native_sha256']==frozen['files']['native.exe'];digest=repair['new_run_py_sha256']
            assert sha(V/('build/'+name if name=='native.exe' else name))==digest,'formal source drift'
        assert sha(root()/'RUN_SPEC.json')==frozen['spec_sha256']
    for item in context['inputs']:assert sha(item['path'])==item['sha256'],'input identity drift'
    folder=root()/'attempts';folder.mkdir(exist_ok=True);i=len(list(folder.iterdir()));attempt=folder/f'{i:04d}';attempt.mkdir()
    job=dict(spec=str(root()/'RUN_SPEC.json'),execution_id=spec['execution_id'],stage=stage,context=context,layout=layout,lifecycle=life,warmups=warm,calls=calls,block=block,diagnostic=diagnostic);save(attempt/'JOB.json',job)
    cmd=[str(V/'build/native.exe'),'--gpu',str(attempt/'JOB.json'),str(attempt/'native')];record=dict(attempt=i,job=job,command=cmd,cwd=str(V),start_utc=now(),start_epoch=time.time(),source_revision=git('rev-parse','HEAD'),native_sha256=sha(V/'build/native.exe'))
    save(attempt/'START.json',record);worker=Child(helper());begin=time.perf_counter();error=None
    try:worker.run(cmd,attempt/'host',120,env(spec),spec['host_RAM_bytes'],lambda:guard(spec),log_cap=65536)
    except BaseException as exc:error=repr(exc)
    finally:worker.terminate()
    life_record=load(attempt/'host.LIFETIME.json');events=load(attempt/'host.JOB_EVENTS.json');assert not events['errors'],'unknown owned process lifecycle;global GPU stop'
    native=attempt/'native';r=load(native/'RECORD.json') if (native/'RECORD.json').exists() else None
    # An exit3 with retained bytes is a numerical/lifecycle boundary,not a retry.
    if life_record['exit_code'] not in [0,3]:raise RuntimeError('native execution error;inspect retained attempt before continuing')
    dedup(native)
    if r:
        reference=Path(context['references'][layout]['path']).read_bytes()
        assert sha(context['references'][layout]['path'])==context['references'][layout]['sha256']
        for call in r['calls']:assert ((native/f'ordinary_{call["index"]}.bin').read_bytes()==reference)==call['ordinary_exact']
        assert (r['status']=='QUALIFIED')==(all(c['ordinary_exact'] and c['finite'] for c in r['calls']) and r['input_after_equal'] and r['host_input_unchanged'])
    record.update(end_utc=now(),wall_seconds=time.perf_counter()-begin,exit=life_record['exit_code'],error=error,native_status=r['status'] if r else 'MISSING',actual_calls=len(r['calls']) if r else None,eligible=bool(r and r['status']=='QUALIFIED' and len(r['calls'])==warm+calls));save(attempt/'ENDED.json',record)
    with (root()/'ATTEMPTS.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record,separators=(',',':'))+'\n')
    return record
def diagnose(spec):
    save(root()/'D0_STARTED.json',dict(UTC=now(),pid=os.getpid()));d=next(c for c in spec['contexts'] if c['id']=='Qwen_l00_prefill_q1');results=[];budget_begin=time.monotonic()
    environment=telemetry(spec,'D0/anchor');assert environment.get('safe_memory',True),'device memory reserve'
    # A/B/C + reversal: identify input aliasing without requiring diagnostic graph success.
    for arm,life,calls in [('A','original_resident',2),('B','reupload',34),('C','persistent_inputs',34),('A_reversal','original_resident',2)]:
        for rep in range(3):
            assert len(results)<48 and sum(r['actual_calls'] or 0 for r in results)+calls<=1600 and time.monotonic()-budget_begin<7200
            results.append(invoke(spec,'D0',d,'PQ',life,0,calls,block=arm))
        print(arm,[(r['native_status'],r['actual_calls']) for r in results[-3:]],flush=True)
    chosen=all(r['eligible'] for r in results if r['job']['lifecycle']=='persistent_inputs')
    save(root()/'D0_ENDED.json',dict(status='STABLE_PERSISTENT_INPUT_LIFECYCLE' if chosen else 'BLOCKED',attempts=len(results),calls=sum(r['actual_calls'] or 0 for r in results),seconds=time.monotonic()-budget_begin,persistent_inputs_checkpoint=chosen,root_cause='requires byte/address intervention analysis;not inferred from names'))
def qualify(spec):
    assert load(root()/'D0_ENDED.json')['persistent_inputs_checkpoint'];freeze(spec,'N1',dict(hosts=216,warmups=2,calls=32));save(root()/'N1_STARTED.json',dict(UTC=now(),pid=os.getpid()));begin=time.monotonic();rows=[];failed=set()
    for d in sorted(spec['contexts'],key=lambda c:(c['q']!=1,c['id'])):
        envrow=telemetry(spec,'N1/'+d['id']);assert envrow.get('safe_memory',True),'device memory headroom'
        for layout in LAYOUTS:
            for rep in range(3):
                if (d['id'],layout) in failed:continue
                assert time.monotonic()-begin<3600
                r=invoke(spec,'N1',d,layout,'persistent_inputs',2,32,block=rep);rows.append(r)
                if not r['eligible']:failed.add((d['id'],layout))
        print('N1',d['id'],len(rows),'hosts;failed_cells',len(failed),flush=True)
    eligible=[[d['id'],l] for d in spec['contexts'] for l in LAYOUTS if sum(r['eligible'] and r['job']['context']['id']==d['id'] and r['job']['layout']==l for r in rows)==3]
    save(root()/'N1_ENDED.json',dict(status='COMPLETE' if len(eligible)==72 else 'PARTIAL',hosts=len(rows),calls=sum(r['actual_calls'] or 0 for r in rows),eligible_cells=eligible,failed_cells=sorted(failed),seconds=time.monotonic()-begin))
def timing(spec):
    n=load(root()/'N1_ENDED.json');eligible={tuple(x) for x in n['eligible_cells']};orders=list(itertools.permutations(LAYOUTS));begin=time.monotonic();results=[]
    freeze(spec,'T1',dict(blocks=6,hosts=432,warmups=8,calls=30,orders=orders,context_order_seed=20261018,quiet_policy='two samples5s apart;<=5%;<=55C;AC;retry>=30s up to600s;whole block invalid on environmental failure',bootstrap_unit='block',sessions='single machine session;two acquisition segments,not independent days'))
    for block in range(6):
        assert time.monotonic()-begin<7200;quiet(spec,block);save(root()/f'T1_BLOCK_{block}_STARTED.json',dict(UTC=now(),pid=os.getpid()));rows=[];contexts=spec['contexts'].copy();random.Random(20261018+block).shuffle(contexts);pre_fail=set()
        for ci,d in enumerate(contexts):
            for l in orders[(block+next(i for i,c in enumerate(spec['contexts']) if c['id']==d['id']))%6]:
                if (d['id'],l) not in eligible:continue
                r=invoke(spec,'T1',d,l,'persistent_inputs',8,30,block);rows.append(r)
                if not r['eligible']:eligible.discard((d['id'],l));pre_fail.add((d['id'],l))
            print('T1',block,d['id'],len(rows),flush=True)
        endenv=telemetry(spec,'T1/'+str(block)+'/post');valid=endenv.get('quiet',False)
        end=dict(status='COMPLETE' if len(rows)==72 and not pre_fail and valid else 'PARTIAL_OR_INVALID',environment_qualified=valid,hosts=len(rows),calls=sum(r['actual_calls'] or 0 for r in rows),failed_cells=sorted(pre_fail),UTC=now());save(root()/f'T1_BLOCK_{block}_ENDED.json',end);results+=rows
    save(root()/'T1_ENDED.json',dict(status='COMPLETE' if len(results)==432 and all(r['eligible'] for r in results) else 'PARTIAL',hosts=len(results),calls=sum(r['actual_calls'] or 0 for r in results),seconds=time.monotonic()-begin))
def cpu(spec):
    directory=root()/'CPU';directory.mkdir(exist_ok=False);worker=Child(helper());rows=[]
    for d in spec['contexts']:
        for layout in LAYOUTS:
            job=dict(spec=str(root()/'RUN_SPEC.json'),execution_id=spec['execution_id'],context=d,layout=layout,lifecycle='persistent_inputs');i=len(rows);save(directory/f'{i:03d}.json',job);cmd=[str(V/'build/native.exe'),'--cpu',str(directory/f'{i:03d}.json'),str(directory/f'{i:03d}')];worker.run(cmd,directory/f'host{i:03d}',120,env(spec),spec['host_RAM_bytes']);rows.append(load(directory/f'{i:03d}/CPU_GRAPH.json'))
    save(V/'CPU_GRAPHS.json',dict(status='PASS',graphs=len(rows),nodes=sum(len(r['graph']['nodes']) for r in rows),GPU_calls=0,claim='actual native graph construction,not GPU correctness'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['cpu','diagnose','qualify','time','analyze','status']);a=ap.parse_args();s=load(root()/'RUN_SPEC.json')
    if a.action=='analyze':
        import analyze;analyze.main();return
    if a.action=='status':print(root());return
    lock=root()/'WORKER.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    try:
        guard(s);handles=runtime_locks(s)
        {'cpu':cpu,'diagnose':diagnose,'qualify':qualify,'time':timing}[a.action](s)
    finally:lock.unlink()
if __name__=='__main__':main()
