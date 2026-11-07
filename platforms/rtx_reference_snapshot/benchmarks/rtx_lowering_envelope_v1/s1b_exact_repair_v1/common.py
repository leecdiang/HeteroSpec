"""Shared wire/CAS/file primitives; importing this module never loads a backend."""
import hashlib,json,os
from pathlib import Path
V=Path(__file__).resolve().parent
RUN='pr116-s1b-cost-v1'
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def save(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,separators=(',',':'));f.write('\n')
def pin(p):
    p=Path(p);return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def retain(root,data):
    h=hashlib.sha256(data).hexdigest();p=Path(root)/(h+'.bin');p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==data
    else:
        with p.open('xb') as f:f.write(data)
    assert sha(p)==h;return dict(sha256=h,bytes=len(data))
def blob(root,ref):
    p=Path(root)/(ref['sha256']+'.bin');assert p.stat().st_size==ref['bytes'] and sha(p)==ref['sha256'];return p.read_bytes()
def wire(slot,f0_path):return dict(slot,F0_path=str(Path(f0_path).resolve()),approved_stage_F0=sha(f0_path))
def stage_sizes(meta):
    product=lambda x: x[0]*x[1]*x[2]*x[3]*4
    return {s:product(meta['native_'+s]['ne']) for s in ('QK','softmax','AV')}|dict(ordinary=product(meta['native_AV']['ne']))
def env(runtime):
    e={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','CUDA_','LLAMA_ARG_'))}
    e['GGML_CUDA_DISABLE_GRAPHS']='1';e['PATH']=str(runtime)+os.pathsep+e.get('PATH','');return e
