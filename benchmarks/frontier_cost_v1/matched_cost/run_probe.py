"""Build and run a bounded M2 LOCAL matched-operation diagnostic on a fresh output path."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
NATIVE_TIMEOUT_SECONDS=1800
KILL_REAP_SECONDS=5
SOURCE_MANIFEST_SHA='8d37214bb699565c535b52d3fd4439786f3e45c2d40a1aaff6db948c27366a1f'
PUBLIC_TARGET_SHA='408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6'
PUBLIC_TOKENIZER_METADATA_SHA='6a5d5b777059e82fb664b418fb59cd2526d1cf65f4b7846892745c84a5124912'
FRONTEND={
    'resident_context.hpp':'02b361035da2baa586e7c2192ca05a87036ef4336a478f954ee1a006fa6b8647',
    'phase_plan.hpp':'d379ba5518dd03c6d6439ad5024a957af0f1b71d92f062688bc8cc1de52935b5',
}


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def identity(path):
    p=Path(path).resolve()
    return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)}


def now():return datetime.now(timezone.utc).isoformat()


def write(path,value):
    temp=path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)


def schedules(q):
    result=[]
    for width in (1,4,8):
        v=[width]*(q//width)+([q%width] if q%width else [])
        if v not in result:result.append(v)
    return result


def validate_inputs(data):
    if data.get('schema')!='heterospec.matched-local-inputs.v1':raise ValueError('input schema')
    qs=data['q_values'];cases=data['cases']
    if not isinstance(qs,list) or qs!=sorted(set(qs)) or any(type(q)!=int or q<1 or q>8 for q in qs) or not qs:raise ValueError('q values')
    if type(data['repeats'])!=int or data['repeats']!=2:raise ValueError('fixed two repetitions required')
    if type(data['threads'])!=int or not 1<=data['threads']<=2:raise ValueError('thread budget')
    if not isinstance(cases,list) or not 1<=len(cases)<=2:raise ValueError('one or two fixed histories required')
    names=set()
    for case in cases:
        if not isinstance(case['name'],str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',case['name']) or case['name'] in names:raise ValueError('unique safe case names required')
        names.add(case['name'])
        if not 1<=len(case['history'])<=512 or len(case['rows'])!=8:raise ValueError('history/row scope')
        if any(type(x)!=int or x<0 for x in case['history']+case['rows']+[case['continuation']]):raise ValueError('token IDs must be nonnegative integers')
    budget={'contexts':0,'native_calls':0,'target_rows':0}
    phases={'qualification':{'contexts':0,'native_calls':0,'target_rows':0},'measurement':{'contexts':0,'native_calls':0,'target_rows':0}}
    for case in cases:
        p=len(case['history']);prefill_calls=(p+31)//32
        for q in qs:
            for schedule in schedules(q):
                one={'contexts':1,'native_calls':prefill_calls+len(schedule)+1,'target_rows':p+q+1}
                for k,v in one.items():phases['qualification'][k]+=v
                # Two first-use runs and two runs with one complete same-shape warmup/reset.
                for k,v in one.items():phases['measurement'][k]+=4*v
                phases['measurement']['native_calls']+=2*(prefill_calls+len(schedule))
                phases['measurement']['target_rows']+=2*(p+q)
    for phase in phases.values():
        for k,v in phase.items():budget[k]+=v
    return {'budget':budget,'phases':phases,'input_cases':len(cases),'q_values':qs,
            'qualification_rule':'Any mismatch stops the job; no candidate selection or timing after a failed qualification.',
            'order':'q ascending; q1, max4, wide schedules deduplicated; second timing repeat reverses schedule order.',
            'timing_modes':['first_after_fresh_context','one_shape_warmup_then_reset'],
            'native_wall_time_limit_seconds':NATIVE_TIMEOUT_SECONDS,
            'timeout_policy':'Kill and reap only the native child created by this wrapper; preserve all partial output; no retry or GPU reset.',
            'timing_is_full_service':False,'historical_GPU_reference_qualification':'NOT_ESTABLISHED'}


def clean_environment(lib_dir,backend,gpu_index):
    if os.environ.get('LD_PRELOAD') or os.environ.get('LD_AUDIT'):raise ValueError('LD_PRELOAD/LD_AUDIT must be absent')
    env={k:v for k,v in os.environ.items() if not k.startswith(('GGML_','LLAMA_','HS_','OMP_','CUDA_')) and k not in ('LD_LIBRARY_PATH','LD_PRELOAD','LD_AUDIT')}
    env['LD_LIBRARY_PATH']=str(lib_dir);env['OMP_NUM_THREADS']='1';env['CUDA_VISIBLE_DEVICES']='' if backend=='cpu' else str(gpu_index)
    env['CUDA_DEVICE_ORDER']='PCI_BUS_ID'
    return env


def pci_address(value):
    match=re.fullmatch(r'([0-9a-fA-F]+):([0-9a-fA-F]{2}):([0-9a-fA-F]{2})\.([0-7])',value)
    if not match:raise ValueError('unexpected PCI bus address')
    return tuple(int(x,16) for x in match.groups())


def physical_gpu_binding(inventory,index):
    if type(index)!=int or index<=0:raise ValueError('physical GPU0 is excluded')
    devices={};buses=set()
    for row in csv.reader(io.StringIO(inventory)):
        if len(row)!=3:raise ValueError('ambiguous physical GPU inventory')
        number,bus,mig=(x.strip() for x in row)
        if not re.fullmatch(r'[0-9]+',number):raise ValueError('invalid physical GPU index')
        number=int(number);address=pci_address(bus)
        if number in devices or address in buses:raise ValueError('physical GPU index/PCI address is not unique')
        devices[number]={'pci_bus_id':bus,'mig_mode':mig};buses.add(address)
    if 0 not in devices or index not in devices:raise ValueError('physical GPU0 and requested index must be identifiable')
    chosen=devices[index];mode=chosen['mig_mode'].strip('[]').lower()
    if mode not in ('disabled','n/a','not supported'):raise ValueError('MIG enabled or mode unknown; physical-device admission refused')
    if pci_address(chosen['pci_bus_id'])==pci_address(devices[0]['pci_bus_id']):raise ValueError('requested device aliases physical GPU0')
    pci_order=sorted(devices,key=lambda number:pci_address(devices[number]['pci_bus_id']))
    return {'physical_index':index,'pci_bus_id':chosen['pci_bus_id'],'mig_mode':chosen['mig_mode'],
            'CUDA_PCI_order_ordinal':pci_order.index(index),
            'excluded_physical_GPU0_pci_bus_id':devices[0]['pci_bus_id'],'physical_inventory_size':len(devices)}


def verify_cuda_visible_device(expected_pci,env):
    # CUDA driver device enumeration only: no context, model, allocation, UUID or kernel call.
    source='''import ctypes,json
d=ctypes.CDLL("libcuda.so.1")
def ok(code):
    if code:raise RuntimeError("CUDA driver query failed: "+str(code))
ok(d.cuInit(0));count=ctypes.c_int();ok(d.cuDeviceGetCount(ctypes.byref(count)))
if count.value!=1:raise RuntimeError("expected one visible CUDA device")
dev=ctypes.c_int();ok(d.cuDeviceGet(ctypes.byref(dev),0))
bus=ctypes.create_string_buffer(64);ok(d.cuDeviceGetPCIBusId(bus,len(bus),dev))
print(json.dumps({"visible_device_count":count.value,"pci_bus_id":bus.value.decode("ascii"),"model_forwards":0}))
'''
    query=subprocess.run([sys.executable,'-c',source],env=env,capture_output=True,text=True,check=True,timeout=15)
    value=json.loads(query.stdout)
    if value.get('visible_device_count')!=1:raise ValueError('ambiguous visible CUDA device count')
    if pci_address(value['pci_bus_id'])!=pci_address(expected_pci):raise ValueError('CUDA ordinal does not map to the requested physical GPU; stop before model loading')
    return value


def validate_model_binding(data,model_sha,declared_sha=None):
    if declared_sha and declared_sha!=model_sha:raise ValueError('target model SHA mismatch')
    binding=data.get('model_binding',{})
    if binding.get('kind')=='original_Qwen3_8B_target_required':
        if model_sha!=PUBLIC_TARGET_SHA or binding.get('expected_sha256')!=PUBLIC_TARGET_SHA:raise ValueError('public inputs require the authenticated original PR213 target GGUF')
        if binding.get('tokenizer_metadata_receipt_sha256')!=PUBLIC_TOKENIZER_METADATA_SHA or binding.get('expected_vocab')!=151936:raise ValueError('public tokenizer metadata binding differs')
        return {'status':'ORIGINAL_PR213_TARGET_SHA_MATCHED','whole_GGUF_sha256':PUBLIC_TARGET_SHA,
                'tokenizer_binding':'Embedded tokenizer is bound by the entire GGUF SHA; metadata receipt SHA is not a standalone vocabulary digest.'}
    return {'status':'LOCAL_DECLARED_MODEL_ONLY','whole_GGUF_sha256':model_sha,'historical_original_model_identity':False}


def command(argv,out,env):
    with out.with_suffix('.stdout').open('xb') as stdout,out.with_suffix('.stderr').open('xb') as stderr:
        process=subprocess.run([str(x) for x in argv],stdout=stdout,stderr=stderr,env=env,check=False)
    record={'argv':[str(x) for x in argv],'returncode':process.returncode,
            'stdout':identity(out.with_suffix('.stdout')),'stderr':identity(out.with_suffix('.stderr'))}
    if process.returncode:raise RuntimeError('command failed: '+json.dumps(record))
    return record


def run_owned_native(argv,out,env,timeout=NATIVE_TIMEOUT_SECONDS):
    """The executable has no child workers; never signal an unrelated PID or GPU."""
    started=time.monotonic();timed_out=False;reaped=False
    with out.with_suffix('.stdout').open('xb') as stdout,out.with_suffix('.stderr').open('xb') as stderr:
        child=subprocess.Popen([str(x) for x in argv],stdout=stdout,stderr=stderr,env=env)
        try:
            child.wait(timeout=timeout);reaped=True
        except subprocess.TimeoutExpired:
            timed_out=True;child.kill()
            try:child.wait(timeout=KILL_REAP_SECONDS);reaped=True
            except subprocess.TimeoutExpired:pass
        except BaseException:
            child.kill()
            try:child.wait(timeout=KILL_REAP_SECONDS)
            except subprocess.TimeoutExpired:pass
            raise
    return {'argv':[str(x) for x in argv],'owned_pid':child.pid,'returncode':child.returncode,
            'timed_out':timed_out,'child_reaped':reaped,'timeout_seconds':timeout,
            'kill_reap_limit_seconds':KILL_REAP_SECONDS,'wall_seconds':time.monotonic()-started,
            'stdout':identity(out.with_suffix('.stdout')),'stderr':identity(out.with_suffix('.stderr'))}


def partial_result_snapshot(path):
    if not path.exists():return {'partial_result':'ABSENT'}
    data=path.read_bytes()
    result={'partial_result':{'path':str(path.resolve()),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}}
    try:
        parsed=json.loads(data)
        result.update(partial_work_snapshot=parsed.get('work'),partial_native_status=parsed.get('status'))
    except (ValueError,AttributeError) as error:result['partial_result_parse_error']=str(error)
    return result


def git_identity(explicit_repo=None):
    start=explicit_repo.resolve() if explicit_repo else HERE
    found=subprocess.run(['git','-C',str(start),'rev-parse','--show-toplevel'],capture_output=True,text=True,check=False)
    if found.returncode:return {'status':'NOT_IN_GIT'}
    repo=Path(found.stdout.strip()).resolve()
    try:relative=HERE.parent.relative_to(repo).as_posix()
    except ValueError:raise ValueError('runner must reside in the declared repository experiment subtree')
    def git(*args):return subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True,check=True).stdout.strip()
    head=git('rev-parse','HEAD')
    tree_result=subprocess.run(['git','-C',str(repo),'rev-parse','HEAD:'+relative],capture_output=True,text=True,check=False)
    tree=tree_result.stdout.strip() if tree_result.returncode==0 else None
    status=git('status','--porcelain','--untracked-files=normal','--',relative)
    required=[HERE.relative_to(repo).as_posix()+'/'+name for name in ('run_probe.py','matched_cost_probe.cpp','inputs_public.json')]
    tracked=git('ls-files','--',*required)
    clean=not status and tree is not None and sorted(tracked.splitlines())==sorted(required)
    return {'status':'CLEAN_COMMITTED_SUBTREE' if clean else 'DIRTY_OR_UNCOMMITTED_SUBTREE','repo':str(repo),
            'HEAD':head,'experiment_subtree':relative,'subtree_tree_sha':tree,'subtree_status_porcelain':status,
            'tracked_compiled_inputs':tracked.splitlines()}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('core','frontend','lib-dir','model'):p.add_argument('--'+name,type=Path)
    p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--backend',choices=['cpu','cuda'],default='cpu');p.add_argument('--gpu-index',type=int)
    p.add_argument('--expected-model-sha256');p.add_argument('--plan-only',action='store_true')
    p.add_argument('--repo',type=Path,help='Repository root for recorded formal-experiment commit; runner must be inside its experiment subtree')
    a=p.parse_args()
    if a.output.is_symlink():raise ValueError('output must not be a symlink')
    out=a.output.resolve()
    if out.exists():raise ValueError('fresh output required: '+str(out))
    data=json.loads(a.inputs.read_text());plan=validate_inputs(data)
    out.mkdir(parents=True);write(out/'PLAN.json',plan)
    receipt={'schema':'heterospec.matched-operation.bound-run.v1','status':'STARTED','started_utc':now(),
             'inputs':identity(a.inputs),'runner':identity(__file__),'probe_source':identity(HERE/'matched_cost_probe.cpp'),
             'plan':plan,'backend':a.backend,'historical_GPU_reference_qualification':'NOT_ESTABLISHED',
             'full_service_performance_claim':False}
    write(out/'RUN.json',receipt)
    try:
        if a.plan_only:
            receipt['status']='PLAN_ONLY';write(out/'RUN.json',receipt);print(json.dumps(plan,indent=2));return
        if any(getattr(a,k) is None for k in ('core','frontend','lib_dir','model')):raise ValueError('core, frontend, lib-dir and model are required for execution')
        core=a.core.resolve();frontend=a.frontend.resolve();lib_dir=a.lib_dir.resolve();model=a.model.resolve()
        env=clean_environment(lib_dir,a.backend,a.gpu_index)
        git_before=git_identity(a.repo);receipt['git_before']=git_before
        if a.backend=='cuda':
            if git_before['status']!='CLEAN_COMMITTED_SUBTREE':raise ValueError('CUDA requires a committed, clean experiment subtree; CPU checks may run outside git')
            if digest(a.inputs)!=digest(HERE/'inputs_public.json'):raise ValueError('CUDA input bytes differ from the committed fixed public profile')
            if a.gpu_index is None or a.gpu_index<=0:raise ValueError('explicit allocated nonzero physical GPU index required; GPU0 is excluded')
            if data.get('model_binding',{}).get('kind')!='original_Qwen3_8B_target_required':raise ValueError('CUDA requires the fixed public target-input profile')
            smi=shutil.which('nvidia-smi')
            if not smi:raise RuntimeError('UNAVAILABLE: nvidia-smi is absent; no GPU request was made')
            inventory=subprocess.run([smi,'--query-gpu=index,pci.bus_id,mig.mode.current','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=15)
            physical=physical_gpu_binding(inventory.stdout,a.gpu_index)
            env['CUDA_VISIBLE_DEVICES']=str(physical['CUDA_PCI_order_ordinal'])
            probe=subprocess.run([smi,'-i',str(a.gpu_index),'--query-gpu=index,name,memory.free,memory.total,pci.bus_id','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True)
            apps=subprocess.run([smi,'-i',str(a.gpu_index),'--query-compute-apps=pid','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True)
            if apps.stdout.strip():raise ValueError('allocated GPU already has a compute process; do not disturb it')
            fields=[s.strip() for s in probe.stdout.strip().split(',')]
            if len(fields)!=5 or int(fields[0])!=a.gpu_index:raise ValueError('unexpected GPU inventory')
            if pci_address(fields[4])!=pci_address(physical['pci_bus_id']):raise ValueError('physical device identity changed during preflight')
            required_mib=(model.stat().st_size+1024**2-1)//1024**2+4096
            if int(fields[2])<required_mib:raise ValueError('insufficient pre-load free memory for model bytes plus declared 4096 MiB reserve')
            receipt['GPU_preflight']={'physical_index':a.gpu_index,'name':fields[1],'free_mib':int(fields[2]),'total_mib':int(fields[3]),'existing_compute_pids':[],
                                      'physical_binding':physical,'visible_CUDA_device':verify_cuda_visible_device(fields[4],env),
                                      'reserve_note':'Pre-load screen only; not a continuous peak-memory proof. No UUID is queried or recorded.'}
        elif a.gpu_index is not None:raise ValueError('GPU index is invalid for CPU mode')
        model_id=identity(model)
        receipt['model_qualification']=validate_model_binding(data,model_id['sha256'],a.expected_model_sha256)
        kit=core.parents[2];manifest_path=kit/'SOURCE_ASSET_MANIFEST.json'
        if digest(manifest_path)!=SOURCE_MANIFEST_SHA:raise ValueError('authenticated source manifest SHA mismatch')
        manifest=json.loads(manifest_path.read_text())['files']
        expected={k:v for k,v in manifest.items() if k.startswith('native/cores/loop4/')}
        actual={x.relative_to(kit).as_posix():x for x in core.rglob('*') if x.is_file()}
        if set(actual)!=set(expected):raise ValueError('numerical source membership differs; use a fresh authenticated source tree')
        for name,path in actual.items():
            if path.is_symlink() or path.stat().st_size!=expected[name]['bytes'] or digest(path)!=expected[name]['sha256']:raise ValueError('numerical source changed: '+name)
        bound_headers={}
        for name,sha256 in FRONTEND.items():
            value=identity(frontend/name)
            if value['sha256']!=sha256:raise ValueError('M2 frontend header identity mismatch: '+name)
            bound_headers[name]=value
        libs={str(x.resolve()):identity(x) for x in lib_dir.glob('*.so*') if x.name.startswith(('libllama','libggml')) and x.is_file()}
        if not libs or not any('libllama.so' in x for x in libs):raise ValueError('native shared libraries missing')
        receipt.update(model=model_id,frontend_headers=bound_headers,source_manifest=identity(manifest_path),
                       checked_numerical_source_members=len(expected),libraries_before=libs,
                       selected_environment={k:env[k] for k in ('LD_LIBRARY_PATH','CUDA_VISIBLE_DEVICES','CUDA_DEVICE_ORDER','OMP_NUM_THREADS')},
                       platform=platform.platform(),python=sys.version)
        build=out/'build';build.mkdir();cc=shutil.which('cc');cxx=shutil.which('c++')
        if not cc or not cxx:raise ValueError('C and C++17 compilers are required')
        object_path=build/'sha256.o';binary=build/'matched_cost_probe'
        stages=[command([cc,'-O2','-I'+str(core/'vendor'),'-I'+str(core/'vendor/hash'),'-c',core/'vendor/hash/sha256/sha256.c','-o',object_path],build/'sha_compile',env)]
        cmd=[cxx,'-std=c++17','-O2','-Wall','-Wextra']+['-I'+str(core/x) for x in ('include','src','ggml/include','vendor')]
        cmd+=['-I'+str(frontend),str(HERE/'matched_cost_probe.cpp'),str(object_path),'-L'+str(lib_dir),'-Wl,-rpath,'+str(lib_dir),'-lllama','-lggml','-lggml-base','-o',str(binary)]
        stages.append(command(cmd,build/'probe_compile',env));receipt['build_stages']=stages;receipt['binary']=identity(binary)
        link=subprocess.run(['ldd',str(binary)],env=env,capture_output=True,text=True,check=True)
        receipt['ldd']=link.stdout
        for line in link.stdout.splitlines():
            if 'libllama' not in line and 'libggml' not in line:continue
            match=re.search(r'=>\s+(\S+)\s+\(',line)
            if not match or str(Path(match.group(1)).resolve()) not in libs:raise ValueError('dynamic native library resolved outside frozen lib-dir')
        job={k:data[k] for k in ('cases','q_values','repeats','threads')}
        job.update(model=str(model),lib_dir=str(lib_dir),backend=a.backend,budget=plan['budget'],raw_byte_limit=2*1024**3,
                   expected_native_libraries={Path(k).name:v['sha256'] for k,v in libs.items()})
        if 'expected_vocab' in data.get('model_binding',{}):job['expected_vocab']=data['model_binding']['expected_vocab']
        write(out/'JOB.json',job);receipt['job']=identity(out/'JOB.json');write(out/'RUN.json',receipt)
        native=run_owned_native([binary,out/'JOB.json',out/'native'],out/'native',env)
        receipt['native_process']=native;receipt['returncode']=native['returncode']
        receipt['git_after']=git_identity(a.repo)
        if a.backend=='cuda' and (receipt['git_after']['status']!='CLEAN_COMMITTED_SUBTREE' or receipt['git_after']['subtree_tree_sha']!=git_before['subtree_tree_sha']):raise ValueError('experiment subtree changed during CUDA execution')
        receipt['libraries_after']={key:identity(key) for key in libs}
        if receipt['libraries_after']!=libs or identity(model)!=model_id:raise ValueError('library/model identities changed during run')
        result_path=out/'native/RESULT.json'
        if native['timed_out']:
            receipt.update(partial_result_snapshot(result_path))
            receipt['status']='TIMEOUT_OWNED_NATIVE_CHILD'
            receipt['finished_utc']=now();write(out/'RUN.json',receipt)
            print(json.dumps({'status':receipt['status'],'child_reaped':native['child_reaped'],'retry':False}))
            sys.exit(124)
        if not result_path.exists():raise ValueError('native result is absent')
        result=json.loads(result_path.read_text());receipt['result']=identity(result_path);receipt['work']=result.get('work');receipt['native_status']=result['status']
        receipt['status']='PASS' if native['returncode']==0 and result['status']=='PASS' else 'STOPPED_'+result['status']
        receipt['finished_utc']=now();write(out/'RUN.json',receipt)
        print(json.dumps({k:receipt.get(k) for k in ('status','backend','work','historical_GPU_reference_qualification','full_service_performance_claim')},indent=2))
        if native['returncode']:sys.exit(native['returncode'])
    except Exception as error:
        receipt['status']='FAILED';receipt['error']=str(error);receipt['finished_utc']=now();write(out/'RUN.json',receipt);raise


if __name__=='__main__':main()
