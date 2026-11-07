"""Read-only inventory by default; explicit single-GPU authorization for execution.

Never resets a device or signals someone else's process. Local flock is only
cooperative exclusion for this user; allocation policy is separately required.
"""
from __future__ import annotations
import argparse, csv, fcntl, hashlib, io, json, os, re, shutil, signal, subprocess, time, threading
from pathlib import Path
from common import need, read, save, sha
HERE=Path(__file__).resolve().parent

def query(argv):
    try:
        r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=15)
        return {'ok':r.returncode==0,'returncode':r.returncode,'stdout':r.stdout.strip(),'error':r.stderr.strip()[:1000]}
    except (OSError,subprocess.TimeoutExpired) as e:return {'ok':False,'stdout':'','error':str(e)}

def csv_rows(text):return [[x.strip() for x in r] for r in csv.reader(io.StringIO(text)) if r]

def gpu_rows():
    fields=['index','uuid','name','compute_cap','memory.total','memory.free','utilization.gpu']
    r=query(['nvidia-smi','--query-gpu='+','.join(fields),'--format=csv,noheader,nounits'])
    if not r['ok']:return [],r
    rows=csv_rows(r['stdout']);need(all(len(x)==len(fields) for x in rows),'Unexpected nvidia-smi GPU schema')
    return [dict(zip(fields,x)) for x in rows],None

def processes(uuid):
    r=query(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'])
    need(r['ok'],'Cannot establish compute occupancy; do not guess idle')
    out=[]
    for row in csv_rows(r['stdout']):
        need(len(row)==3,'Unexpected compute-app schema')
        if row[0]==uuid:out.append({'pid':int(row[1]),'memory_MiB':row[2]})
    return out

def available_ram():
    m=dict((s.split(':')[0],s.split(':')[1].strip()) for s in Path('/proc/meminfo').read_text().splitlines())
    return int(m['MemAvailable'].split()[0])*1024

def inspect(out):
    g,error=gpu_rows(); tools={}
    for tool in ('nvidia-smi','nvcc','c++','cmake','ninja','git','gh'):
        p=shutil.which(tool);tools[tool]={'path':p,'version':query([p,'--version']) if p else None}
    p=Path(out);p.parent.mkdir(parents=True,exist_ok=True);save(p,{'schema':'linux-transfer.inventory.v1','read_only':True,'model_requests':0,
         'platform':os.uname().sysname+' '+os.uname().release,'gpus':g,'gpu_query_error':error,
         'gpu_processes':{r['uuid']:processes(r['uuid']) for r in g},'tools':tools,
         'available_RAM_bytes':available_ram(),'disk_free_bytes':shutil.disk_usage(p.parent).free,
         'cpu_affinity':sorted(os.sched_getaffinity(0)),
         'authorization':'NOT_GRANTED_BY_INVENTORY','no_environment_or_credentials_dumped':True})
    print(p)

def check_resources(config,group=None):
    rows,error=gpu_rows();need(error is None,'GPU inventory unavailable')
    visible=os.environ.get('CUDA_VISIBLE_DEVICES')
    if visible is not None:
        allowed={token.strip() for token in visible.split(',')}
        selected_ids={r['index'] for r in rows if r['uuid']==config['gpu_uuid']}
        need(config['gpu_uuid'] in allowed or bool(selected_ids & allowed),'Requested UUID is outside inherited CUDA_VISIBLE_DEVICES; obtain correct scheduler allocation, do not unmask')
    selected=[r for r in rows if r['uuid']==config['gpu_uuid']];need(len(selected)==1,'Approved GPU UUID disappeared')
    r=selected[0];need(int(r['index']) not in config.get('protected_gpu_indices',[0]),'Protected GPU index; use another approved GPU')
    foreign=[]
    for p in processes(config['gpu_uuid']):
        try:owned=group is not None and os.getpgid(p['pid'])==group
        except ProcessLookupError:owned=False
        if not owned:foreign.append(p)
    need(not foreign,'Selected GPU has another compute process; stop own work, never kill it')
    need(float(r['memory.free'])*1024**2>=config['gpu_reserve_bytes'],'GPU reserve violated')
    need(available_ram()>=config['ram_reserve_bytes'],'RAM reserve violated')
    need(shutil.disk_usage(config['work_root']).free>=config['disk_reserve_bytes'],'Disk reserve violated')
    return {'gpu':r,'available_RAM_bytes':available_ram(),'disk_free_bytes':shutil.disk_usage(config['work_root']).free}

def reservation(job):
    if 'inputs' in job:
        rows=0
        for entry in job['inputs']:
            x=entry['input'];p=len(x['prompt_ids']);cap=int(x['cap']);need(0<cap<=128,'cap bounds')
            rows+=2*p+16*cap # conservative upper bound, also charged for ordinary/reference
        return len(job['inputs']),rows
    cases=job.get('cases',[job] if 'forced' in job else [])
    if cases:return len(cases),sum(len(c['ids']) for case in cases for c in case['forced'])
    probes=job.get('append_probes',[])
    need(probes,'No supported native work reservation')
    return len(probes),sum(len(p['prefix'])+len(p['ids']) for p in probes)

def environment(uuid):
    env={k:v for k,v in os.environ.items() if not (k.startswith(('HS_','GGML_','HSC_','JSA_')) or any(s in k.upper() for s in ('TOKEN','SECRET','PASSWORD','API_KEY')) or k=='LD_PRELOAD')}
    env['CUDA_VISIBLE_DEVICES']=uuid;env['CUDA_DEVICE_ORDER']='PCI_BUS_ID'
    return env

def modules_from_result(path):
    data=read(path); names=set()
    def visit(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in ('modules_before','modules_after') and isinstance(v,list):names.update(str(p) for p in v)
                else:visit(v)
        elif isinstance(x,list):
            for v in x:visit(v)
    visit(data);need(names,'Native actual module inventory missing')
    output={}
    for name in sorted(names):
        if name.startswith('linux-vdso'):output[name]={'sha256':None,'kind':'kernel_virtual_DSO'}
        else:
            p=Path(name);need(p.is_absolute() and p.is_file(),'Loaded module path unresolved: '+name)
            output[name]={'sha256':sha(p),'kind':'ELF_file'}
    return output

def run(config_path,build_path,job_path,out,phase):
    config=read(config_path);build=read(build_path);job=read(job_path);out=Path(out).resolve()
    need(config.get('approved_by_user') is True and config.get('allocation_id'),'User/scheduler GPU allocation required')
    need(re.fullmatch(r'GPU-[A-Za-z0-9-]+',config.get('gpu_uuid','')),'Full GPU UUID, not ordinal/all')
    work=Path(config['work_root']).resolve();need(out.is_relative_to(work) and not out.exists(),'Fresh output under private work_root')
    need(config['gpu_reserve_bytes']>=1024**3 and config['ram_reserve_bytes']>=4*1024**3 and config['disk_reserve_bytes']>=20*1024**3,'Do not reduce reserves to force admission')
    need(build.get('cuda') is True and build.get('dependency_closure_complete') is True,'Full CUDA build/dependency receipt required')
    exe=Path(build['executable']);need(sha(exe)==build['executable_sha256'],'Executable changed')
    deps=read(Path(build_path).parent/'DEPENDENCIES.json')
    for p,h in deps['files'].items():need(sha(p)==h,'Compiled dependency changed: '+p)
    for role in ('target','draft'):
        if role+'_model' in job and job[role+'_model']:
            need(sha(job[role+'_model'])==job[role+'_sha256'],'Model hash mismatch: '+role)
    allowed=read(HERE/'pins.json')['models'];family=job['family'];need(family in allowed,'Existing model family only')
    for role in ('target','draft'):
        if job.get(role+'_model'):need(job.get(role+'_sha256')==allowed[family][role],'Different weights require a separately designed deployment')
    freeze=None
    if build['role']!='reference':
        ref_file=config.get('reference_freeze');need(ref_file,'Freeze independent R before candidate forwards')
        need(sha(ref_file)==config.get('reference_freeze_sha256'),'Independent reference freeze changed')
        need(read(ref_file)['status']=='REFERENCE_FROZEN','Independent reference not frozen')
    if phase=='confirmation':
        freeze=read(config['freeze']);need(freeze['status']=='QUALIFIED_AND_FROZEN','No formal run before native qualification/freeze')
        need(sha(config['freeze'])==config['freeze_sha256'],'Freeze changed')
        need(build['executable_sha256'] in freeze['executables'],'Executable not in frozen native set')
        need(sha(job_path) in freeze['job_sha256'],'Unregistered confirmation job')
    work.mkdir(parents=True,exist_ok=True)
    lockdir=Path.home()/'.cache/reference-compatible-gpu-locks';lockdir.mkdir(parents=True,exist_ok=True,mode=0o700)
    lockpath=lockdir/(config['gpu_uuid']+'.lock')
    with lockpath.open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        initial=check_resources(config);out.mkdir(parents=True)
        req,rows=reservation(job);ledger=work/'ledger.jsonl'
        prior=[json.loads(x) for x in ledger.read_text().splitlines()] if ledger.exists() else []
        reserved=[r for r in prior if r.get('event')=='RESERVE']
        if phase=='confirmation':need(not any(r.get('phase')=='confirmation' and r.get('job_sha256')==sha(job_path) for r in reserved),'Frozen confirmation job already reserved; retain failed/finished slot, no selective retry')
        need(sum(r['requests'] for r in reserved)+req<=2048 and sum(r['rows'] for r in reserved)+rows<=4000000,'Study budget exhausted; no automatic extension')
        with ledger.open('a') as f:f.write(json.dumps({'event':'RESERVE','out':str(out),'requests':req,'rows':rows,'phase':phase,'job_sha256':sha(job_path)})+'\n');f.flush();os.fsync(f.fileno())
        save(out/'launch.json',{'job_sha256':sha(job_path),'build_sha256':sha(build_path),'phase':phase,'requests_reserved':req,'rows_reserved':rows,'initial':initial,'allocation_id':config['allocation_id'],'gpu_uuid':config['gpu_uuid']})
        start=time.monotonic();launch_clock=None;exit_clock=None;p=None;status='FAILED';code=None;markers=[];drain_errors=[];thread=None
        try:
            with (out/'stdout.log').open('xb') as so,(out/'stderr.log').open('xb') as se,(out/'resources.jsonl').open('x') as log:
                launch_clock=time.monotonic()
                p=subprocess.Popen([str(exe),str(Path(job_path).resolve()),str(out/'native')],stdout=subprocess.PIPE,stderr=se,env=environment(config['gpu_uuid']),start_new_session=True)
                def drain():
                    try:
                        for line in iter(p.stdout.readline,b''):
                            received=time.monotonic();so.write(line);so.flush()
                            if line.startswith((b'PHASE1_RESULT_READY ',b'LINUX_RESULT_READY ')):
                                words=line.decode('utf8').strip().split()
                                markers.append({'name':words[1],'seconds_after_launch':received-launch_clock})
                    except BaseException as e:drain_errors.append(repr(e))
                thread=threading.Thread(target=drain,daemon=True);thread.start()
                while p.poll() is None:
                    need(time.monotonic()-start<=config.get('worker_timeout_s',900),'Owned worker timeout')
                    r=check_resources(config,p.pid);r['seconds']=time.monotonic()-start;log.write(json.dumps(r)+'\n');log.flush()
                    try:p.wait(timeout=2)
                    except subprocess.TimeoutExpired:pass
                code=p.returncode;exit_clock=time.monotonic();need(code==0,'Native failure retained')
                thread.join(timeout=10);need(not thread.is_alive() and not drain_errors,'Marker/log drain failure')
            modules=modules_from_result(out/'native/result.json');save(out/'LOADED_MODULES.json',modules)
            if freeze:
                known=freeze['executables'][build['executable_sha256']]['loaded_modules']
                need(modules==known,'Actual loaded modules differ from qualified freeze; keep result, no performance claim')
            if 'inputs' in job:
                need([m['name'] for m in markers]==[x['name'] for x in job['inputs']],'Missing/reordered real result markers')
                save(out/'CLOCKS.json',{'markers':markers,'launch_to_first_result_s':markers[0]['seconds_after_launch'],
                    'launch_to_first_test_result_s':markers[2]['seconds_after_launch'] if len(markers)>=3 else None,
                    'test_burst_wall_s':markers[-1]['seconds_after_launch']-markers[1]['seconds_after_launch'] if len(markers)>=3 else None,
                    'boundary':'Second primer marker to final request marker for registered burst; ordinary development marker arrays have no population meaning',
                    'first_result_is_complete_request_not_TTFT':True})
            status='COMPLETE'
        finally:
            if p and p.poll() is None:
                os.killpg(p.pid,signal.SIGTERM)
                try:p.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=10)
            if p and exit_clock is None:exit_clock=time.monotonic()
            if thread:thread.join(timeout=10)
            save(out/'HOST.json',{'status':status,'returncode':code,'worker_wall_s':exit_clock-launch_clock if exit_clock is not None and launch_clock is not None else None,'wrapper_wall_s':time.monotonic()-start,'no_reservation_refund':True,'native_numeric_qualification':'NOT_INFERRED_FROM_EXIT_CODE'})
            with ledger.open('a') as f:f.write(json.dumps({'event':status,'out':str(out)})+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='action',required=True)
    i=s.add_parser('inspect');i.add_argument('--out',type=Path,required=True)
    r=s.add_parser('run');r.add_argument('--config',type=Path,required=True);r.add_argument('--build',type=Path,required=True);r.add_argument('--job',type=Path,required=True);r.add_argument('--out',type=Path,required=True);r.add_argument('--phase',choices=['reference','development','confirmation'],required=True)
    a=p.parse_args();inspect(a.out) if a.action=='inspect' else run(a.config,a.build,a.job,a.out,a.phase)
