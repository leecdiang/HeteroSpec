"""Exclusive, source-bound native execution; historical assets are read-only."""
import hashlib,json,os,subprocess,time,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('E:/rtx172')
MODEL=Path('D:/HeteroSpec-PC/models/gguf/Qwen3-8B-Q8_0.gguf')
def read(p): return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
    with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def build(label,oracle=False):
    old=Path('E:/rtx170')/('oracle01' if oracle else 'new-driver')
    out=ROOT/label;out.mkdir()
    for p in old.glob('*.dll'):os.link(p,out/p.name)
    commands=read(old/'build.json')['commands']; actual=[]
    for i,cmd in enumerate(commands):
        cmd=[str(HERE/'worker.cpp') if s.endswith('driver.cpp') else s.replace(str(old),str(out)).replace('driver.obj','worker.obj').replace('driver.exe','worker.exe') for s in cmd]
        actual.append(cmd)
        with (out/f'build-{i}.log').open('xb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=600)
        put(out/f'build-{i}.json',dict(argv=cmd,code=r.returncode));r.check_returncode()
    put(out/'binding.json',dict(commands=actual,source=sha(HERE/'worker.cpp'),exe=sha(out/'worker.exe'),core=read(old/'build.json')['core'],modules={p.name:sha(p) for p in out.glob('*.dll')}))
def run(label,build,manifest,requests=0,admissions=0):
    assert requests>=0 and admissions>=0
    ledger=list(ROOT.glob('*/launch.json'))
    assert sum(read(p)['requests'] for p in ledger)+requests<=2048
    assert sum(read(p)['admissions'] for p in ledger)+admissions<=6
    assert shutil.disk_usage(ROOT).free>20*1024**3
    out=ROOT/label;out.mkdir();put(out/'input.json',manifest)
    lock=Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock')
    with lock.open('x') as f:json.dump(dict(pid=os.getpid(),job=label),f)
    start=time.monotonic()
    try:
        exe=ROOT/build/'worker.exe'
        put(out/'launch.json',dict(requests=requests,admissions=admissions,timeout_s=1800,exe=sha(exe),source=sha(HERE/'worker.cpp'),start_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
        env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','JSA_','HSC_'))}
        with (out/'native.log').open('xb') as f:r=subprocess.run([exe,MODEL,out/'input.json',out],stdout=f,stderr=subprocess.STDOUT,timeout=1800,env=env)
        put(out/'exit.json',dict(code=r.returncode,elapsed_s=time.monotonic()-start));r.check_returncode()
    except Exception as e:
        put(out/'failure.json',dict(error=repr(e),elapsed_s=time.monotonic()-start));raise
    finally:lock.unlink()
    return out
if __name__=='__main__':
    if sys.argv[1]=='build':build(sys.argv[2],len(sys.argv)>3)
