"""Explicit content-bound imports; never searches sys.path for frozen study modules."""
import builtins,hashlib,json,types
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def unique_pairs(pairs):
 out={}
 for k,v in pairs:
  if k in out:raise ValueError('duplicate JSON key: '+k)
  out[k]=v
 return out
def loads(b):return json.loads(b,object_pairs_hook=unique_pairs)
def read(p):return loads(Path(p).read_text(encoding='utf-8-sig'))
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def encoded(v):return (json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def write(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(encoded(v))
def require(ok,msg):
 if not ok:raise ValueError(msg)
REFS=read(ROOT/'REFERENCES.json');CACHE={}
def load(name):
 filename=name+'.py';require(filename in REFS['source_modules'],'unbound frozen import: '+name)
 if name in CACHE:return CACHE[name]
 pin=REFS['source_modules'][filename];p=Path(pin['path']);body=p.read_bytes();require(digest(body)==pin['sha256'],'frozen module SHA changed: '+str(p));m=types.ModuleType('bound_'+name);m.__file__=str(p);CACHE[name]=m
 def importer(n,g=None,l=None,fromlist=(),level=0):
  if not level and n+'.py' in REFS['source_modules']:return load(n)
  return builtins.__import__(n,g,l,fromlist,level)
 m.__dict__['__builtins__']=dict(vars(builtins),__import__=importer)
 try:exec(compile(body,str(p),'exec'),m.__dict__)
 except BaseException:CACHE.pop(name,None);raise
 return m
