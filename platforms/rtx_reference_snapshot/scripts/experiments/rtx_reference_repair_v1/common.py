"""Small, standard-library-only utilities. Importing this module never launches a model."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

STUDY = 'rtx_reference_repair_v1'
BASE = '47c93985010d0f3c0c55f975f4cd7761e64bcae2'
UPSTREAM = '29511ed91eb9f3d9773cfdda53e3554b0f4ad08b'
TARGET = 'a0dfe649137410b7d82f06a209240508e218f32f5b6fd81b69d6932160cfcd9d'
DRAFT = '9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031'
PINS = {
 'worker.cpp': 'b38275fb41c9baa732adc02e40f6c9529b1b2fa6',
 'arm_spec.h': '2a654cee5ca6df5f26dd60c0beae0ee616c5fab6',
 'build_native.py': '2c287c9c71aef7f8b3af5b95da16544a381edff7',
 'study.py': 'f25daa3cfed6fd8e9f11d5859cc6d2c9308b1036',
}
END_KEYS = ('ids','eog','length','terminal_id','stop_reason')

def need(ok, message):
    if not ok: raise ValueError(message)

def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()

def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()

def digest(x): return hashlib.sha256(canonical(x)).hexdigest()

def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024), b''): h.update(b)
    return h.hexdigest()

def git_blob(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def read(path):
    def pairs(items):
        d={}
        for k,v in items:
            need(k not in d, 'duplicate JSON field: '+k); d[k]=v
        return d
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=pairs,
        parse_constant=lambda s: (_ for _ in ()).throw(ValueError('nonfinite JSON: '+s)))

def save(path, x, exclusive=False):
    p=Path(path);p.parent.mkdir(parents=True, exist_ok=True)
    body=json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    if exclusive:
        with p.open('x',encoding='utf-8',newline='\n') as f: f.write(body);f.flush();os.fsync(f.fileno())
        return
    fd,tmp=tempfile.mkstemp(dir=p.parent,prefix=p.name+'.')
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:f.write(body);f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def append(path, x):
    with Path(path).open('ab') as f:f.write(canonical(x)+b'\n');f.flush();os.fsync(f.fileno())

def confined(root, rel):
    root=Path(root).resolve();p=(root/rel).resolve()
    need(p!=root and p.is_relative_to(root), 'unsafe artifact path')
    return p

def git_read(repo, ref, path, expected=None):
    need(not path.startswith('/') and '..' not in Path(path).parts, 'unsafe Git path')
    b=subprocess.check_output(['git','-C',str(repo),'show',ref+':'+path],timeout=60)
    if expected:need(git_blob(b)==expected,'Git source identity differs: '+path)
    return b

def prompt_hash(ids): return hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()

def valid_input(x):
    p=x['prompt_ids'];need(isinstance(p,list) and 0<len(p)<=892,'prompt length')
    need(all(type(v) is int and 0<=v<151936 for v in p),'prompt token ID')
    need(x['prompt_ids_sha256']==prompt_hash(p),'prompt hash')
    need(x['cap']==128 and bool(x['id']), 'fixed cap or input identity differs')

def endpoint(r, cap=128):
    r=r.get('endpoint',r);need(all(k in r for k in END_KEYS),'incomplete endpoint')
    ids=r['ids'];eog=r['eog']
    need(isinstance(ids,list) and 0<len(ids)<=cap,'output length')
    need(all(type(i) is int and 0<=i<151936 for i in ids),'output token')
    need(isinstance(eog,list) and len(eog)==len(ids) and all(type(v) is bool for v in eog),'EOG flags')
    need(not any(eog[:-1]),'generation continued after EOG')
    need(type(r['length']) is int and type(r['terminal_id']) is int and r['length']==len(ids) and r['terminal_id']==ids[-1],'endpoint bounds')
    need((eog[-1] and r['stop_reason']=='EOG') or (not eog[-1] and len(ids)==cap and r['stop_reason']=='CAP'),'stop semantics')
    return {k:r[k] for k in END_KEYS}

def positive(x):
    need(type(x) in (int,float) and math.isfinite(x) and x>0,'expected positive finite value')
    return float(x)

def gm(values):
    a=list(values);need(bool(a),'empty geometric mean')
    return math.exp(math.fsum(math.log(positive(v)) for v in a)/len(a))
