"""Pinned design/source/assets read receipts; zero forward load checks."""
from common import *
import ctypes,re
class Power(ctypes.Structure):
    _fields_=[('ACLineStatus',ctypes.c_ubyte),('BatteryFlag',ctypes.c_ubyte),('BatteryLifePercent',ctypes.c_ubyte),('SystemStatusFlag',ctypes.c_ubyte),('BatteryLifeTime',ctypes.c_uint32),('BatteryFullLifeTime',ctypes.c_uint32)]
def host():
    fields=subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu,power.draw','--format=csv,noheader,nounits'],text=True).strip().split(', ')
    p=Power();ok=ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(p))
    scheme=re.search(rb'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',subprocess.check_output(['powercfg','/getactivescheme']),re.I)
    return {'utc':now(),'gpu':fields[0],'driver':fields[1],'total_MiB':float(fields[2]),'used_MiB':float(fields[3]),'util':float(fields[4]),'temp':float(fields[5]),'power_W':fields[6],'AC':p.ACLineStatus if ok else None,'power_scheme_guid':scheme.group().decode().lower() if scheme else None}
def models():
    if (PUB/'MODEL_CONTRACT.json').exists():
        frozen=read(PUB/'MODEL_CONTRACT.json')['families'];assert set(frozen)=={'Qwen','SmolLM2','Llama'}
        return {family:entry['models'] for family,entry in frozen.items()}
    q=read(OLDLOCAL/'CONFIG.json')['models'];s=read(OLDLOCAL/'F_MODEL_CONFIG.json')['models']
    result={'Qwen':q,'SmolLM2':s,'Llama':{}}
    for a in read(DESIGN/'ASSETS.json')['families']['Llama']['models']:
        result['Llama'][a['role']]={'path':str(LOCAL/'models'/a['filename']),'sha256':a['sha256_publisher_claim'],'bytes':a['bytes'],'publisher':a['publisher'],'revision':a['revision']}
    return result
def command(pair,condition,port=18783,verbose=False):
    exe=LOCAL/'native/build/bin/llama-server.exe'
    cmd=[str(exe),'--model',pair['target']['path'],'--device','CUDA0','--n-gpu-layers','all','--fit','off','--ctx-size','1024','--batch-size','2048','--ubatch-size',str(condition['target_ub']),'--flash-attn','off','--parallel','1','--threads','24','--threads-batch','24','--cache-ram','0','--cache-type-k','f16','--cache-type-v','f16','--host','127.0.0.1','--port',str(port),'--no-webui','--no-warmup','--no-cache-prompt']
    if condition['spec']:cmd+=['--spec-type','draft-simple','--model-draft',pair['draft']['path'],'--spec-draft-device','CUDA0','--spec-draft-ngl','all','--spec-draft-n-max',str(condition['maximum_k']),'--spec-draft-n-min','0','--spec-draft-p-min','0','--spec-draft-threads','24','--spec-draft-threads-batch','24','--spec-draft-type-k','f16','--spec-draft-type-v','f16']
    if verbose:cmd+=['--verbose']
    return cmd
def static():
    PUB.mkdir(parents=True,exist_ok=True);LOCAL.mkdir(parents=True,exist_ok=True)
    receipts={}
    for p in DESIGN.iterdir():
        if p.suffix=='.json':value=read(p);keys=list(value)
        else:keys={'characters':len(p.read_text(encoding='utf-8'))}
        receipts[p.name]={'sha256':sha(p),'read':keys}
    bindings=read(DESIGN/'SOURCE_BINDINGS.json');rows=[]
    for a in bindings['RTX_result']['files']:
        b=subprocess.check_output(['git','show',bindings['RTX_result']['head']+':'+a['path']],cwd=OLD)
        assert hashlib.sha256(b).hexdigest()==a['sha256'];rows.append({'path':a['path'],'sha256':a['sha256'],'status':'MATCH_PINNED_GIT_BYTES'})
    save(PUB/'DESIGN_READ_RECEIPT.json',{'design_PR':83,'design_SHA':DESIGN_SHA,'design_documents':receipts,'RTX_source_bindings':rows,'model_forwards':0,'utc':now()})
    assets=read(DESIGN/'ASSETS.json')['families'];rows=[]
    for family,pair in models().items():
        for role,m in pair.items():
            p=Path(m['path']);complete=p.exists() and p.stat().st_size==m['bytes']
            actual=sha(p) if complete else None
            assert not complete or actual==m['sha256']
            rows.append({'family':family,'role':role,'path':str(p),'expected_bytes':m['bytes'],'expected_sha256':m['sha256'],'actual_bytes':p.stat().st_size if p.exists() else None,'actual_sha256':actual,'status':'PASS' if complete else 'ASSET_DOWNLOAD_PENDING'})
    save(PUB/'ASSET_CHECK_INITIAL.json',{'utc':now(),'models':rows,'forwards':0,'conversion_lineage':'Public publisher revision/hash binding only; official checkpoint conversion lineage not certified'})
    print('STATIC SOURCE CHECK PASS',len(receipts),'design documents;',len(rows),'assets inspected',flush=True)
def zero_load(family,tag=''):
    pair=models()[family]
    for m in pair.values():assert Path(m['path']).stat().st_size==m['bytes'] and sha(m['path'])==m['sha256']
    d=LOCAL/'zero-load'/(family+tag);d.mkdir(parents=True,exist_ok=False)
    cond=read(DESIGN/'DESIGN.json')['conditions'][3];cmd=command(pair,cond,verbose=True)
    save(d/'COMMAND.json',{'command':cmd,'condition':cond,'model_forwards':0,'binary_sha256':sha(cmd[0]),'utc':now()})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));start=time.perf_counter();error=None;loaded=None
    with (d/'server.log').open('wb') as log:
        p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=clean_env(3),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:
            deadline=time.monotonic()+240
            while True:
                if p.poll() is not None:raise RuntimeError('zero-forward loader exited '+str(p.returncode))
                try:
                    with opener.open('http://127.0.0.1:18783/health',timeout=2) as r:healthy=json.load(r).get('status')=='ok'
                    if healthy:loaded=host();break
                except (OSError,urllib.error.URLError):pass
                if time.monotonic()>deadline:raise TimeoutError('readiness')
                time.sleep(.5)
        except Exception as e:error={'type':type(e).__name__,'error':str(e)}
        finally:
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=10)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=10)
    text=(d/'server.log').read_text(encoding='utf-8',errors='replace');counts=re.findall(r'offloaded (\d+)/(\d+) layers to GPU',text)
    full=len(counts)==2 and all(a==b for a,b in counts)
    free=None if loaded is None else loaded['total_MiB']-loaded['used_MiB']
    result={'status':'PASS' if error is None and full and free>=512 else 'MEMORY_OR_ASSET_BLOCKED','family':family,'error':error,'actual_full_offload_counts':counts,'loaded_host':loaded,'free_MiB':free,'model_forwards':0,'warmup_requests':0,'lifetime_seconds':time.perf_counter()-start,'log_sha256':sha(d/'server.log'),'effective_parameters_from_native_log':[line for line in text.splitlines() if any(t in line for t in ['n_ctx','n_batch','n_ubatch','KV buffer size','compute buffer size'])]}
    result['binary_sha256']=sha(cmd[0]);result['tag']=tag
    save(PUB/('ZERO_LOAD_'+family+tag+'.json'),result);print('ZERO LOAD',family,result['status'],counts,'freeMiB',free,flush=True)
if __name__=='__main__':
    import sys
    static() if len(sys.argv)==1 else zero_load(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else '')
