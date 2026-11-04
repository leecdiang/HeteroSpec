"""Bounded, authenticated asset parts; no scientific data is discarded."""
from host import *
from concurrent.futures import ThreadPoolExecutor,as_completed
def split(path,chunk_mib=128):
    parts=[]
    with path.open('rb') as f:
        i=0
        while b:=f.read(chunk_mib*1024**2):
            p=path.with_name(path.name+f'.part{i:03}');p.write_bytes(b);parts.append(dict(name=p.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()));i+=1
    put(path.with_name(path.name+'.parts.json'),dict(archive=path.name,sha256=sha(path),bytes=path.stat().st_size,parts=parts));print(len(parts),'parts')
def upload(manifest):
    m=read(manifest);paths=[manifest.parent/x['name'] for x in m['parts']]+[manifest]
    def one(p):
        attempts=[]
        for attempt in range(3):
            t=time.monotonic();command=['gh','release','upload','rtx-prefix-reuse-v1-20261104','--repo','leecdiang/HeteroSpec',str(p)]
            if attempt:command.append('--clobber') # only this task's identical generated asset
            try:
                r=subprocess.run(command,capture_output=True,text=True,timeout=600)
                current=dict(attempt=attempt,code=r.returncode,seconds=time.monotonic()-t,stdout=r.stdout,stderr=r.stderr)
            except subprocess.TimeoutExpired:
                current=dict(attempt=attempt,code=None,seconds=time.monotonic()-t,error='600s transfer timeout')
            attempts.append(current)
            put(ROOT/(p.name+f'.upload-attempt{attempt}.json'),current)
            if current['code']==0:break
        record=dict(file=p.name,code=attempts[-1]['code'],attempts=attempts,seconds=sum(x['seconds'] for x in attempts))
        put(ROOT/(p.name+'.upload.json'),record);print(p.name,record['code'],flush=True);return record
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=[f.result() for f in as_completed([pool.submit(one,p) for p in paths])]
    assert all(r['code']==0 for r in results)
def join(manifest,out):
    m=read(manifest)
    with out.open('xb') as target:
        for x in m['parts']:
            p=manifest.parent/x['name'];assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256']
            with p.open('rb') as f:shutil.copyfileobj(f,target)
    assert out.stat().st_size==m['bytes'] and sha(out)==m['sha256'];print('verified reconstructed',out)
if __name__=='__main__':
    if sys.argv[1]=='split':split(Path(sys.argv[2]))
    elif sys.argv[1]=='upload':upload(Path(sys.argv[2]))
    else:join(Path(sys.argv[2]),Path(sys.argv[3]))
