"""Bounded operator launches charged to the same original-host ledger."""
from native_adapter import *
from build_operator_driver import ORIG
OP=Path('D:/rtx184-operator')
def bind():
    runtime=OP/'cuda-v2';assert (runtime/'RUNTIME_BUILD.json').exists()
    for arm in ('original','graph_tiles','backend_loop4','packed'):
        out=OP/(arm+'-driver-v4');binary=out/'bin';modules={}
        sources=list((ORIG/'bin').glob('*.dll')) if arm=='original' else list((runtime/'bin').glob('*.dll'))+list(Path('D:/rtx184-tools/cuda/bin').glob('*.dll'))+list(Path('D:/rtx184-tools/msvc/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64').glob('vcruntime*.dll'))+list(Path('D:/rtx184-tools/msvc/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64').glob('msvcp*.dll'))
        for src in sources:
            h=sha(src);assert src.name.lower() not in {k.lower() for k in modules};modules[src.name]=h
            if src.drive==binary.drive:os.link(src,binary/src.name)
            else:shutil.copy2(src,binary/src.name)
        put(out/'RUNTIME_BINDING.json',dict(exe=sha(binary/'driver.exe'),modules=modules,source='original authenticated kit' if arm=='original' else 'same newly compiled CUDA DLL for every candidate arm'))
def execute_operator(label,arm,manifest,model='8B',build_override=None):
    out=RUNS/label;out.mkdir();put(out/'input.json',manifest);build=Path(build_override) if build_override else OP/(arm+'-driver-v4');binding=json.loads((build/'RUNTIME_BINDING.json').read_bytes())
    assert sha(build/'bin/driver.exe')==binding['exe']
    for name,h in binding['modules'].items():assert sha(build/'bin'/name)==h
    if 'replay' in manifest:
        ops=json.loads((Path(manifest['replay'])/'receipt.json').read_bytes())['nodes'];n=sum((Path(manifest['replay'])/x['weight']['name']/'input.bin').exists() for x in ops)
        reservation=dict(requests=0,token_rows=0,operators=n*9*4)
    else:
        units=manifest['units'];reservation=dict(requests=len(units),token_rows=sum((u['pos'] if u['mode']=='prefix' else u['width']+1) for u in units),operators=0)
        expected={'8B':'408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6','0.6B':'9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031'}
        assert sha(Path('D:/HeteroSpec-PC/models/gguf/Qwen3-'+model+'-Q8_0.gguf'))==expected[model]
    ledger=Ledger(ROOT/'ledger.sqlite',LIMITS);ledger.reserve(label,reservation);put(out/'reservation.json',reservation)
    lock=Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock');p=None;owned=False;code=None;status='FAILED';start=time.monotonic()
    try:
        with lock.open('x') as f:json.dump(dict(pid=os.getpid(),job=label),f)
        owned=True;cmd=[str(build/'bin/driver.exe'),'D:/HeteroSpec-PC/models/gguf/Qwen3-'+model+'-Q8_0.gguf',str(out/'input.json'),str(out)]
        put(out/'launch.json',dict(argv=cmd,binding=binding,limits=dict(wall_s=1200,disk_free_bytes=20*1024**3,ram_free_bytes=4*1024**3,gpu_free_bytes=128*1024**2)))
        with (out/'native.log').open('xb') as log,(out/'resources.jsonl').open('x') as telemetry:
            p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','JSA_','HSC_'))},creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            while p.poll() is None:
                m=Memory();m.length=ctypes.sizeof(m);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m));gpu=int(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True,timeout=10).strip())*1024**2
                r=dict(seconds=time.monotonic()-start,disk_free=shutil.disk_usage(out).free,ram_free=m.available,gpu_free=gpu);telemetry.write(json.dumps(r)+'\n');telemetry.flush()
                assert r['seconds']<=1200 and r['disk_free']>=20*1024**3 and r['ram_free']>=4*1024**3 and gpu>=128*1024**2,'live resource limit'
                time.sleep(2)
            code=p.returncode;assert code==0,('native exit',code)
        modules={}
        for phase in ('before','after'):
            paths=json.loads((out/('modules-'+phase+'.json')).read_bytes());seen={};modules[phase]=[]
            for value in paths:
                module_path=Path(value);key=module_path.name.lower();assert key not in seen;seen[key]=value
                h=sha(module_path);modules[phase].append(dict(path=value,sha256=h))
                if module_path.name in binding['modules']:assert h==binding['modules'][module_path.name]
                elif key.startswith(('ggml','cublas','cudart')):raise RuntimeError('unbound numerical module '+value)
        put(out/'ACTUAL_MODULES.json',modules);status='COMPLETE';return out
    except BaseException as e:put(out/'failure.json',dict(error=repr(e)));raise
    finally:
        if p:kill_owned(p)
        if owned:lock.unlink()
        put(out/'exit.json',dict(status=status,code=code,seconds=time.monotonic()-start));ledger.finish(label,status,code);ledger.close()
if __name__=='__main__':bind()
