"""Repair study primitives; importing this module performs no execution."""
from __future__ import annotations
import hashlib, json, math, os, subprocess, tempfile
from pathlib import Path

STUDY = 'rtx_reference_repair_v1'
BASE = '47c93985010d0f3c0c55f975f4cd7761e64bcae2'
UPSTREAM = '29511ed91eb9f3d9773cfdda53e3554b0f4ad08b'
TARGET = 'a0dfe649137410b7d82f06a209240508e218f32f5b6fd81b69d6932160cfcd9d'
DRAFT = '9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031'
SOURCE = '62086688fc095be2654ae25aad2c7780c94db8617db5a6a9f71504f49897bf7e'
HISTORICAL_WORKER = 'e1c1d77994ae1ec9b403f7699013ce17f00344621f85cbceb0b917abc256a533'
ENDPOINT_KEYS = ('ids','eog','length','terminal_id','stop_reason')

def need(ok, message):
    if not ok: raise ValueError(message)

def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def digest(x): return hashlib.sha256(canonical(x)).hexdigest()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
def blob(data): return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def read(path):
    def pairs(items):
        out={}
        for k,v in items:
            need(k not in out,'duplicate JSON key: '+k);out[k]=v
        return out
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=pairs,
                      parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def save(path,x,exclusive=False):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
    if exclusive:
        with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text);f.flush();os.fsync(f.fileno())
        return
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=path.name+'.')
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:f.write(text);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def append(path,x):
    with Path(path).open('ab') as f:f.write(canonical(x)+b'\n');f.flush();os.fsync(f.fileno())
def safe(root,rel):
    root=Path(root).resolve();p=(root/rel).resolve()
    need(p.is_relative_to(root) and p!=root,'unsafe artifact path');return p
def pos(x,label):
    need(type(x) in (int,float) and math.isfinite(x) and x>0,'invalid '+label);return x
def integer(x,lo,hi,label):
    need(type(x) is int and lo<=x<=hi,'invalid '+label);return x
def gm(values):
    a=list(values);need(a,'empty estimate');return math.exp(math.fsum(math.log(pos(x,'ratio')) for x in a)/len(a))
def git_bytes(repo,path,ref=BASE):
    return subprocess.check_output(['git','-C',str(repo),'show',f'{ref}:{path}'],timeout=60)
def endpoint(record,cap=128):
    e=record.get('endpoint',record);need(all(k in e for k in ENDPOINT_KEYS),'endpoint incomplete')
    ids,flags=e['ids'],e['eog'];need(isinstance(ids,list) and 0<len(ids)<=cap,'invalid IDs')
    need(all(type(x) is int and 0<=x<151936 for x in ids),'invalid token ID')
    need(isinstance(flags,list) and all(type(x) is bool for x in flags),'invalid EOG')
    need(type(e['length']) is int and type(e['terminal_id']) is int,'endpoint integer types')
    need(len(flags)==len(ids)==e['length'] and e['terminal_id']==ids[-1],'endpoint lengths')
    need(not any(flags[:-1]),'tokens after EOG')
    need((flags[-1] and e['stop_reason']=='EOG') or (not flags[-1] and len(ids)==cap and e['stop_reason']=='CAP'),'stop mismatch')
    return {k:e[k] for k in ENDPOINT_KEYS}
def code_pins():return {p.name:sha(p) for p in Path(__file__).parent.iterdir() if p.suffix in ('.py','.h')}
