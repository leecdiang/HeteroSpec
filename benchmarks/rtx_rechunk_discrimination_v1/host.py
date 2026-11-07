"""Exclusive bounded native execution for the single PR176 challenge."""
from audit import HERE,OLD,ROOT,read,sha,put
import os,subprocess,time,shutil,json
MODEL='D:/HeteroSpec-PC/models/gguf/Qwen3-8B-Q8_0.gguf'
def run(label,build,units,stage):
    assert stage in ('engineering','scientific')
    assert all(u['arm'] in ('R','QB','WB-cut','WB-rechunk') for u in units)
    ledger=[read(p) for p in ROOT.glob('*/launch.json')];n=len(units)
    assert sum(x['requests'] for x in ledger)+n<=200
    assert sum(x['requests'] for x in ledger if x['stage']==stage)+n<=(160 if stage=='scientific' else 40)
    assert shutil.disk_usage(ROOT).free>20*1024**3
    out=ROOT/label;out.mkdir();put(out/'input.json',dict(mode='requests',capacity=4096,units=units))
    exe=Path(build)/'worker.exe';binding=read(Path(build)/'binding.json');assert sha(exe)==binding['exe']
    lock=Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock');owned=False;start=time.monotonic()
    put(out/'launch.json',dict(requests=n,stage=stage,exe=sha(exe),source=binding['source'],build=str(build),timeout_s=1800,start_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
    try:
        with lock.open('x') as f:json.dump(dict(pid=os.getpid(),job=label,study='PR176'),f)
        owned=True
        env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','JSA_','HSC_'))}
        with (out/'native.log').open('xb') as f:r=subprocess.run([exe,MODEL,out/'input.json',out],stdout=f,stderr=subprocess.STDOUT,env=env,timeout=1800)
        put(out/'exit.json',dict(code=r.returncode,elapsed_s=time.monotonic()-start));r.check_returncode()
    except BaseException as e:
        put(out/'failure.json',dict(error=repr(e),elapsed_s=time.monotonic()-start));raise
    finally:
        if owned:lock.unlink()
    return out
from pathlib import Path
