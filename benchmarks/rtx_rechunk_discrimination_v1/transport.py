"""Bounded artifact-only transport. Does not execute scientific requests."""
from audit import *
import subprocess,time,sys,shutil
from concurrent.futures import ThreadPoolExecutor
TAG='rtx-rechunk-discrimination-v1-20261104'
def split(path):
    parts=[]
    with path.open('rb') as f:
        while b:=f.read(128*1024**2):
            name=path.name+f'.part{len(parts):03}';(path.parent/name).write_bytes(b);parts.append(dict(name=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    put(path.with_name(path.name+'.parts.json'),dict(archive=path.name,sha256=sha(path),bytes=path.stat().st_size,parts=parts));print(len(parts),'parts')
def transfer(manifest,direction,target):
    m=read(manifest);names=[x['name'] for x in m['parts']]+[manifest.name];target.mkdir(exist_ok=True)
    def one(name):
        history=[]
        for attempt in range(3):
            cmd=['gh','release','upload' if direction=='upload' else 'download',TAG,'--repo','leecdiang/HeteroSpec']
            if direction=='upload':cmd += [str(manifest.parent/name)]+(['--clobber'] if attempt else [])
            else:cmd += ['--pattern',name,'--dir',str(target),'--clobber']
            t=time.monotonic()
            try:
                r=subprocess.run(cmd,capture_output=True,text=True,timeout=600);row=dict(attempt=attempt,code=r.returncode,seconds=time.monotonic()-t,stdout=r.stdout,stderr=r.stderr)
            except subprocess.TimeoutExpired:row=dict(attempt=attempt,code=None,seconds=time.monotonic()-t,error='600s timeout')
            history.append(row);put(target/(name+f'.{direction}-{attempt}.json'),row)
            if row['code']==0:break
        assert history[-1]['code']==0,(name,history)
        if direction=='download':
            expected=next((x['sha256'] for x in m['parts'] if x['name']==name),sha(manifest));assert sha(target/name)==expected
        print(direction,name,'verified' if direction=='download' else 'uploaded',flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(one,names))
def join(manifest,out):
    m=read(manifest)
    with out.open('xb') as f:
        for x in m['parts']:
            p=manifest.parent/x['name'];assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256']
            with p.open('rb') as src:shutil.copyfileobj(src,f)
    assert sha(out)==m['sha256']
if __name__=='__main__':
    if sys.argv[1]=='split':split(Path(sys.argv[2]))
    elif sys.argv[1]=='join':join(Path(sys.argv[2]),Path(sys.argv[3]))
    else:transfer(Path(sys.argv[2]),sys.argv[1],Path(sys.argv[3]))
