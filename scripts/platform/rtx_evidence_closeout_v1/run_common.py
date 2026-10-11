"""Closeout execution paths, immutable publication and actual host identity."""
import base64, ctypes, hashlib, json, os, re, subprocess, sys, time
from pathlib import Path
from datetime import datetime, timezone
import closeout

REPO = Path(__file__).resolve().parents[3]
PRIMARY = REPO.parent.parent
LOCAL = Path('D:/hsc89')
PUB = REPO/'benchmarks/rtx_evidence_closeout_v1'
DESIGN = REPO/'docs/experiments/rtx_evidence_closeout_20261011'
OLD = REPO.parent/'HeteroSpec-third'
OLDPUB = OLD/'benchmarks/jsa_third_family_v1'
DESIGN_HEAD = 'e2d5dcbc224c086d1d6804de8ed925182bfa1404'
BASE_HEAD = '59b0f87a7011dad15f5e1146591ae83d9556d0e7'
PORT = 18789
digest = closeout.digest

def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def save(p, value):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists(): raise FileExistsError(p)
    tmp=p.with_name(p.name+'.writing')
    with tmp.open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    os.rename(tmp,p)
def status(stage, **extra):
    p=LOCAL/'STATUS.json';tmp=p.with_suffix('.next')
    tmp.write_text(json.dumps({'utc':now(),'stage':stage,**extra},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(tmp,p);print(stage,json.dumps(extra,ensure_ascii=False),flush=True)
def git(*args): return subprocess.check_output(['git',*args],cwd=REPO).decode('utf-8').strip()
def api(route): return json.loads(subprocess.check_output(['gh','api','repos/leecdiang/HeteroSpec/'+route]))
def models(): return {f:v['models'] for f,v in read(OLDPUB/'MODEL_CONTRACT.json')['families'].items()}
def clean_env(mask, trace):
    e={k:v for k,v in os.environ.items() if not k.startswith(('HS_','LLAMA_ARG_','GGML_','CUDA_'))}
    e['HS_SCOPE_MASK']=str(mask)
    # The inherited observer is enabled only for per-request heavy mode.
    e['HS_NATIVE_CAPTURE']=str(trace)
    return e
class Power(ctypes.Structure):
    _fields_=[('ACLineStatus',ctypes.c_ubyte),('BatteryFlag',ctypes.c_ubyte),('BatteryLifePercent',ctypes.c_ubyte),('SystemStatusFlag',ctypes.c_ubyte),('BatteryLifeTime',ctypes.c_uint32),('BatteryFullLifeTime',ctypes.c_uint32)]
def host():
    a=subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu,power.draw','--format=csv,noheader,nounits']).decode().strip().split(', ')
    p=Power();ok=ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(p))
    scheme=re.search(rb'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',subprocess.check_output(['powercfg','/getactivescheme']),re.I)
    return dict(utc=now(),gpu=a[0],driver=a[1],total_MiB=float(a[2]),used_MiB=float(a[3]),util=float(a[4]),temp=float(a[5]),power_W=a[6],AC=p.ACLineStatus if ok else None,power_scheme_guid=scheme.group().decode().lower() if scheme else None)
