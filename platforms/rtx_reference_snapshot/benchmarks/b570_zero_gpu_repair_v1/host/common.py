"""Task-local CPU evidence I/O; no scientific entry points or legacy defaults."""
import datetime,hashlib,json,os,sys,threading,time
from pathlib import Path
sys.dont_write_bytecode=True
os.environ['PYTHONDONTWRITEBYTECODE']='1'
HERE=Path(__file__).resolve().parent
DESIGN=HERE.parent
BASE=Path('C:/hs/b570-zero-gpu-repair-v1-20261016').resolve()
MAX_GAP=1_000_000_000
PERIOD=100_000_000
now=time.perf_counter_ns
def need(ok,reason):
    if not ok: raise ValueError(reason)
def owned(p):
    p=Path(p).resolve()
    need(p!=BASE and BASE in p.parents,'new task root required')
    need('b570-paper-support' not in str(p).lower(),'legacy task forbidden')
    return p
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()
def load(p):
    def pairs(items):
        d={}
        for k,v in items:
            need(k not in d,'duplicate JSON key');d[k]=v
        return d
    return json.loads(Path(p).read_text(encoding='utf-8'),object_pairs_hook=pairs,parse_constant=lambda x:need(False,'nonfinite JSON'))
def write_new(p,data):
    with owned(p).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(data,f,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def file_id(p):
    p=Path(p).resolve();s=p.stat()
    need(not p.is_symlink() and not p.is_junction() and s.st_nlink==1,'alias/reparse/hardlink forbidden')
    return dict(path=str(p),volume=s.st_dev,file_id=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns)
def inventory(p):
    p=Path(p);size=count=0
    for parent,dirs,files in os.walk(p,followlinks=False):
        for n in dirs+files:
            q=Path(parent,n);need(not q.is_symlink() and not q.is_junction(),'reparse directory')
        for n in files:
            s=file_id(Path(parent,n));size+=s['bytes'];count+=1
    return dict(bytes=size,files=count,root=str(p.resolve()))
def task_storage(projected=0,reserve=268435456):
    used=files=directories=0
    for parent,dirs,names in os.walk(BASE,followlinks=False):
        directories+=len(dirs);used+=4096*len(dirs)
        for name in names:
            p=Path(parent,name);s=p.stat();used+=((s.st_size+4095)//4096)*4096+1024;files+=1
    need(used+projected+reserve<=1073741824,'new task storage/evidence reserve exhausted')
    return dict(allocation_upper_bytes=used,files=files,directories=directories,projected_bytes=projected,evidence_reserve_bytes=reserve,method='4KiB rounded files +1KiB per-file metadata +4KiB per directory, conservatively added across checkout/Git/temp/evidence/restore')
class Journal:
    def __init__(self,path,cap=64*1024**2):
        self.path=owned(path);self.cap=cap;self.size=0;self.seq=0;self.lock=threading.RLock();self.closed=False
        self.f=self.path.open('xb',buffering=0)
    def emit(self,event,**kw):
        with self.lock:
            self.seq+=1
            row=dict(event=event,seq=self.seq,at_ns=now(),pid=os.getpid(),native_thread_id=threading.get_native_id(),thread_name=threading.current_thread().name,**kw)
            b=(json.dumps(row,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n').encode()
            need(self.size+len(b)<=self.cap,'journal reserved bytes exceeded')
            self.f.write(b);os.fsync(self.f.fileno());self.size+=len(b);return row
    def close(self):
        with self.lock:
            if not self.closed:self.f.flush();os.fsync(self.f.fileno());self.f.close();self.closed=True

class Reject(Exception):
    def __init__(self,code,target,detail=None):
        super().__init__(code);self.code=code;self.target=target;self.detail=detail
