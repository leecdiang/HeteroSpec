"""Llama repair utilities. Importing this module does not launch native code."""
from __future__ import annotations
import hashlib, json, math, os, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
BASE = '38b3d3d3929dc958e6a2a7e0bdc8abd61ff38ab1'
HISTORY = '29511ed91eb9f3d9773cfdda53e3554b0f4ad08b'
STUDY = 'rtx_llama_repair_v1'
PARENT = 'scripts/experiments/rtx_reference_repair_v1'
DIAG = 'benchmarks/rtx_scope_transfer_v1/sidecar_execution/diagnostic/'
VOCAB = 128256
END_KEYS = ('ids','eog','length','terminal_id','stop_reason')

def need(ok, message):
    if not ok: raise ValueError(message)

def utc(): return datetime.now(timezone.utc).isoformat()
def sha(data): return hashlib.sha256(data).hexdigest()
def blob(data): return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def digest(x): return sha(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode())
def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()
def read(path):
    def pairs(items):
        d={}
        for k,v in items: need(k not in d,'duplicate JSON key '+k);d[k]=v
        return d
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=pairs,
      parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON '+x)))
def save(path,x,exclusive=False):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
    if exclusive:
        with p.open('x',encoding='utf-8',newline='\n') as f:f.write(text);f.flush();os.fsync(f.fileno())
    else:
        fd,tmp=tempfile.mkstemp(dir=p.parent,prefix=p.name+'.')
        try:
            with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:f.write(text);f.flush();os.fsync(f.fileno())
            os.replace(tmp,p)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
def confined(root,rel):
    root=Path(root).resolve();p=(root/rel).resolve()
    need(p!=root and p.is_relative_to(root),'unsafe relative path '+str(rel));return p
def git_read(repo,ref,path,expected=None):
    need(not path.startswith('/') and '..' not in Path(path).parts,'unsafe Git path')
    b=subprocess.check_output(['git','-C',str(repo),'show',ref+':'+path],timeout=60)
    if expected:need(blob(b)==expected,'pinned Git blob mismatch '+path)
    return b
def endpoint(r,cap=128):
    e=r.get('endpoint',r);need(all(k in e for k in END_KEYS),'incomplete endpoint')
    ids=e['ids'];flags=e['eog']
    need(isinstance(ids,list) and 0<len(ids)<=cap,'invalid output length')
    need(all(type(t) is int and 0<=t<VOCAB for t in ids),'not Llama token IDs')
    need(isinstance(flags,list) and len(flags)==len(ids) and all(type(v) is bool for v in flags),'invalid EOG flags')
    need(not any(flags[:-1]),'tokens after EOG')
    need(type(e['length']) is int and type(e['terminal_id']) is int and e['length']==len(ids) and e['terminal_id']==ids[-1],'endpoint bounds')
    need((flags[-1] and e['stop_reason']=='EOG') or (not flags[-1] and len(ids)==cap and e['stop_reason']=='CAP'),'stop rule')
    return {k:e[k] for k in END_KEYS}
def prompt_hash(ids):return sha(json.dumps(ids,separators=(',',':')).encode())
def input_check(x):
    ids=x['prompt_ids'];need(isinstance(ids,list) and 0<len(ids)<=892,'prompt size')
    need(all(type(t) is int and 0<=t<VOCAB for t in ids),'prompt vocabulary')
    need(prompt_hash(ids)==x['prompt_ids_sha256'],'prompt bytes')
    need(x['cap']==128 and bool(x['id']),'input identity/cap')
def gm(xs):
    a=list(xs);need(a and all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in a),'invalid geometric mean')
    return math.exp(math.fsum(math.log(v) for v in a)/len(a))
def once(text,a,b):need(text.count(a)==1,'source anchor changed '+a[:100]);return text.replace(a,b,1)
