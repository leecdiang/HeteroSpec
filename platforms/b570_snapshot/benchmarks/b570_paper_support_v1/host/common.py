"""Bounded study I/O. No GPU imports or device discovery."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
HERE = Path(__file__).resolve().parent
DESIGN = HERE.parent
BASE = Path('C:/hs/b570-paper-support-v1-20261016')
JOURNALS = BASE/'journals'
OUTPUTS = BASE/'outputs'
MAX_GAP = 1_000_000_000

def need(value, reason):
    if not value:
        raise ValueError(reason)

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2), b''):
            h.update(block)
    return h.hexdigest()

def load(path):
    def pairs(items):
        d={}
        for k,v in items:
            need(k not in d, 'duplicate JSON key '+k)
            d[k]=v
        return d
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs,
        parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))

def write_new(path, value):
    path=Path(path)
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)
        f.write('\n');f.flush();os.fsync(f.fileno())

class Journal:
    """External exclusive journal; full bytes cap, durable writes, no truncation."""
    def __init__(self,path,cap=64*1024**2):
        self.path=Path(path);self.cap=cap;self.count=0;self.lock=threading.Lock()
        self.f=self.path.open('xb')
    def emit(self,event,**kw):
        data=(json.dumps(dict(event=event,received_ns=time.monotonic_ns(),utc=utc(),**kw),
            ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')
        with self.lock:
            need(self.count+len(data)<=self.cap,'external journal capacity')
            self.f.write(data);self.f.flush();os.fsync(self.f.fileno());self.count+=len(data)
    def close(self):
        with self.lock:
            self.f.flush();os.fsync(self.f.fileno());self.f.close()

def inventory(root):
    root=Path(root);size=count=0
    for parent,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:
            p=Path(parent)/name
            need(not p.is_symlink() and not p.is_junction(),'reparse storage '+str(p))
        for name in files:
            p=Path(parent)/name;s=p.stat()
            need(s.st_nlink==1,'hard-link storage '+str(p))
            size+=s.st_size;count+=1
    return dict(bytes=size,files=count)
