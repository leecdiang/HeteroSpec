"""Prospective third-family study; original PR80 evidence is read-only."""
import hashlib,json,os,subprocess,time,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
REPO=Path(__file__).resolve().parents[3]
PUB=REPO/'benchmarks/jsa_third_family_v1'
LOCAL=REPO.parent/'third-family'
OLD=REPO.parent/'HeteroSpec'
OLDLOCAL=REPO.parent/'jsa'
DESIGN=REPO/'docs/experiments/jsa_third_family_20261011'
DESIGN_SHA='a8a52eafaf0a64ddd7b14c7472d1b4f2d7c19e62'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def save(p,x):
    # Immutable unique records avoid Windows replace locks and shared mutable ledgers.
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise FileExistsError(p)
    q=p.with_name(p.name+'.writing')
    with q.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n');f.flush();os.fsync(f.fileno())
    q.rename(p)
def head():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
def clean_env(mask=0,capture=None):
    e={k:v for k,v in os.environ.items() if not k.startswith(('HS_','LLAMA_ARG_','LLAMA_BATCH_DEBUG','GGML_','CUDA_'))}
    e['HS_SCOPE_MASK']=str(mask)
    if capture:e['HS_NATIVE_CAPTURE']=str(capture)
    return e
