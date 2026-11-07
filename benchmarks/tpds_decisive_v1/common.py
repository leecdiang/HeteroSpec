"""Small shared utilities. Checks stay enabled under python -O."""
from __future__ import annotations
import hashlib, json, math, os, tempfile
from pathlib import Path
from typing import Any

class Invalid(ValueError):
    pass

def shared_blob(path: Path, raw: bytes) -> None:
    """Optional same-volume CAS; hard links retain every original logical path."""
    pool=os.environ.get('TPDS_EVIDENCE_CAS')
    if not pool:path.write_bytes(raw);return
    h=hashlib.sha256(raw).hexdigest();p=Path(pool)/h[:2]/h;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():need(p.read_bytes()==raw,'shared CAS collision')
    else:
        with p.open('xb') as f:f.write(raw)
    os.link(p,path)

def need(ok: bool, message: str) -> None:
    if not ok:
        raise Invalid(message)

def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def file_sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def read(path: Path) -> Any:
    def invalid_constant(s: str): raise Invalid('nonfinite JSON: '+s)
    def unique(pairs):
        out={}
        for k,v in pairs:
            need(k not in out,'duplicate JSON key: '+k);out[k]=v
        return out
    return json.loads(path.read_text(encoding='utf-8'),parse_constant=invalid_constant,
                      object_pairs_hook=unique)

def write_new(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n').encode()
    with path.open('xb') as f: f.write(raw);f.flush();os.fsync(f.fileno())

def hexsha(s: Any, label='sha256') -> str:
    need(isinstance(s,str) and len(s)==64 and all(c in '0123456789abcdef' for c in s),label)
    return s

def positive(x: Any, label: str) -> float:
    need(type(x) in (int,float) and math.isfinite(x) and x>0,label)
    return float(x)

def contained(base: Path, value: str) -> Path:
    need(isinstance(value,str) and bool(value),'empty payload path')
    p=Path(value)
    need(not p.is_absolute() and '..' not in p.parts,'payload path escape')
    dest=(base/p).resolve();root=base.resolve()
    need(dest!=root and root in dest.parents,'payload outside root')
    cur=base
    for part in p.parts:
        cur=cur/part;need(not cur.is_symlink(),'payload symlink')
    return dest

def check_blob(base: Path, spec: dict, *, expected: int | None=None) -> Path:
    p=contained(base,spec['path']);need(p.is_file(),'missing raw payload')
    n=spec['bytes'];need(type(n) is int and n>0,'bad raw length')
    if expected is not None: need(n==expected,'unexpected raw extent')
    need(p.stat().st_size==n,'truncated raw payload')
    need(file_sha(p)==hexsha(spec['sha256']),'raw hash mismatch')
    return p

def equal_files(a: Path, b: Path) -> bool:
    if a.stat().st_size!=b.stat().st_size:return False
    with a.open('rb') as x,b.open('rb') as y:
        while True:
            u=x.read(1024*1024);v=y.read(1024*1024)
            if u!=v:return False
            if not u:return True
