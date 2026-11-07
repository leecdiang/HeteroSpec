import base64,hashlib,json,os,subprocess,sys,time,zipfile,math
from pathlib import Path
from datetime import datetime,timezone
REPO=Path(__file__).resolve().parents[3]
LOCAL=Path('D:/hsc95')
PUB=REPO/'benchmarks/rtx_querylayout_mechanism_v1'
DESIGN_HEAD='215644b704dc13e589d9f7b6bda02b8b6449f4ba'
AUDIT_HEAD='f8f3572f8f55041337a7352cc676783f9f4e1cb3'
PARENT_HEAD='810407c9423cac925d38a976403e23c81bb1704b'
PYTHON=Path('D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe')
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(o):return hashlib.sha256(json.dumps(o,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def save(p,o):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
def status(stage,**values):
    LOCAL.mkdir(exist_ok=True);p=LOCAL/'STATUS.json';tmp=p.with_suffix('.next')
    tmp.write_text(json.dumps(dict(utc=now(),stage=stage,**values),ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,p)
    print(stage,json.dumps(values,ensure_ascii=False),flush=True)
def retry(fn,label):
    start=time.monotonic();attempt=0
    while True:
        try:return fn()
        except (subprocess.CalledProcessError,OSError) as e:
            attempt+=1
            if time.monotonic()-start>3600:raise
            status('NETWORK_RETRY',operation=label,attempt=attempt,error=repr(e));time.sleep(min(60,attempt*5))
def api(path,raw=False):
    args=['gh','api','repos/leecdiang/HeteroSpec/'+path]
    if raw:args+=['-H','Accept: application/vnd.github.raw+json']
    b=retry(lambda:subprocess.check_output(args),path)
    return b if raw else json.loads(b)
def git(*args):return subprocess.check_output(['git',*args],cwd=REPO).decode().strip()
def verified_blob(oid):
    b=api('git/blobs/'+oid,raw=True)
    assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid
    return b
def compare_parent_audit(actual,expected):
    differences=[]
    def walk(a,b,path):
        assert type(a)==type(b),path
        if isinstance(a,dict):
            assert set(a)==set(b),path
            for k in a:walk(a[k],b[k],path+'/'+k)
        elif isinstance(a,list):
            assert len(a)==len(b),path
            for i,(x,y) in enumerate(zip(a,b)):walk(x,y,path+'/'+str(i))
        elif a!=b:
            assert isinstance(a,float) and path.endswith('/ratio') and math.isclose(a,b,rel_tol=1e-12,abs_tol=0),path
            differences.append(dict(path=path,local=a,archived=b,absolute_difference=abs(a-b),ULPs=abs(a-b)/math.ulp(b)))
    walk(actual,expected,'');return differences
