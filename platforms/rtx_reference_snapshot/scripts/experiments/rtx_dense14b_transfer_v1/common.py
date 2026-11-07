"""Shared standard-library primitives. No model/network work at import time."""
from __future__ import annotations
import hashlib, json, math, os, re, subprocess, tempfile
from pathlib import Path

STUDY = 'rtx_dense14b_transfer_v1'
UPSTREAM = '29511ed91eb9f3d9773cfdda53e3554b0f4ad08b'
NATIVE_DIR = 'scripts/experiments/rtx_scope_transfer_v1'
PINS = {
    'worker.cpp': 'b38275fb41c9baa732adc02e40f6c9529b1b2fa6',
    'arm_spec.h': '2a654cee5ca6df5f26dd60c0beae0ee616c5fab6',
    'build_native.py': '2c287c9c71aef7f8b3af5b95da16544a381edff7',
    'study.py': 'f25daa3cfed6fd8e9f11d5859cc6d2c9308b1036',
}
TARGET_SHA256 = 'a0dfe649137410b7d82f06a209240508e218f32f5b6fd81b69d6932160cfcd9d'
END_KEYS = ('ids', 'eog', 'length', 'terminal_id', 'stop_reason')
ARMS = ('R', 'M_PQ', 'M_QB', 'C_PQ_A', 'C_PQ_B', 'C_QB')
UNIQUE_ARMS = ('R', 'M_PQ', 'M_QB', 'C_PQ', 'C_QB')

def need(ok, why):
    if not ok: raise ValueError(why)

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')

def digest(value): return hashlib.sha256(canonical(value)).hexdigest()

def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(4*1024*1024), b''): h.update(b)
    return h.hexdigest()

def git_blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def read(path):
    def pairs(items):
        out={}
        for k,v in items:
            need(k not in out, 'duplicate JSON key: '+k); out[k]=v
        return out
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))

def save(path, value, exclusive=False):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    body=json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    if exclusive:
        with path.open('x', encoding='utf-8', newline='\n') as f:
            f.write(body); f.flush(); os.fsync(f.fileno())
    else:
        fd,tmp=tempfile.mkstemp(prefix=path.name+'.', dir=path.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:
                f.write(body); f.flush(); os.fsync(f.fileno())
            os.replace(tmp,path)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)

def append(path, value):
    """Single-writer fsync ledger. Caller owns the study lock."""
    with Path(path).open('ab') as f:
        f.write(canonical(value)+b'\n'); f.flush(); os.fsync(f.fileno())

def positive(v, name):
    need(type(v) in (int,float) and math.isfinite(v) and v>0, 'invalid '+name)
    return v

def exact_int(v, low, high, name):
    need(type(v) is int and low<=v<=high, 'invalid '+name); return v

def confined(root, rel):
    root=Path(root).resolve(); p=(root/rel).resolve()
    need(p.is_relative_to(root) and p!=root, 'unsafe artifact path')
    return p

def upstream_bytes(repo, name):
    need(name in PINS, 'unregistered upstream member')
    b=subprocess.check_output(['git','-C',str(repo),'show',f'{UPSTREAM}:{NATIVE_DIR}/{name}'],timeout=60)
    need(git_blob(b)==PINS[name], 'pinned source mismatch: '+name)
    return b

def prompt_hash(ids):
    # Matches nlohmann JSON integer-array .dump(), not whitespace-rich JSON.
    return hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()

def endpoint(record):
    e=record.get('endpoint',record)
    need(all(k in e for k in END_KEYS),'incomplete endpoint')
    ids=e['ids']; flags=e['eog']
    need(isinstance(ids,list) and ids and len(ids)<=128,'invalid output IDs')
    need(all(type(x) is int and 0<=x<151936 for x in ids),'invalid token')
    need(isinstance(flags,list) and all(type(x) is bool for x in flags),'invalid EOG flags')
    need(type(e['length']) is int and type(e['terminal_id']) is int,'endpoint integer fields')
    need(len(flags)==len(ids)==e['length'] and e['terminal_id']==ids[-1],'endpoint length/terminal mismatch')
    need(not any(flags[:-1]), 'tokens after EOG')
    need((flags[-1] and e['stop_reason']=='EOG') or
         (not flags[-1] and len(ids)==128 and e['stop_reason']=='CAP'),'stop contract')
    return {k:e[k] for k in END_KEYS}

def geomean(values):
    v=list(values); need(v,'empty mean')
    for x in v: positive(x,'ratio')
    return math.exp(math.fsum(math.log(x) for x in v)/len(v))
