"""Resumable pinned GGUF download. Range transport never executes a model."""
from common import *
import concurrent.futures,shutil
ROOT=LOCAL/'models'
def segment(job):
    m,start,end,p=job
    if p.exists() and p.stat().st_size==end-start+1:return p
    for attempt in range(1,9):
        tmp=p.with_suffix('.tmp')
        try:
            prior=tmp.stat().st_size if tmp.exists() else 0
            assert prior<=end-start+1
            if prior==end-start+1:tmp.replace(p);return p
            cursor=start+prior
            url=m['url']+f'?download=true&third-family-range={start}-{end}&attempt={attempt}&transport_nonce={time.time_ns()}'
            q=urllib.request.Request(url,headers={'Range':f'bytes={cursor}-{end}','User-Agent':'HeteroSpec/third-family-assets'})
            with urllib.request.urlopen(q,timeout=90) as r:
                assert r.status==206 and r.headers.get('Content-Range')==f'bytes {cursor}-{end}/{m["bytes"]}','range response mismatch'
                with tmp.open('ab') as f:
                    remaining=end-cursor+1
                    while remaining:
                        b=r.read(min(4*1024**2,remaining))
                        if not b:raise EOFError('range body truncated')
                        f.write(b);remaining-=len(b)
                assert tmp.stat().st_size==end-start+1
            tmp.replace(p);return p
        except Exception as e:
            reason=getattr(e,'reason',e)
            print('RANGE ATTEMPT FAILED',m['role'],start,attempt,type(e).__name__,type(reason).__name__,getattr(reason,'errno',None),flush=True)
            if attempt==8:raise RuntimeError('range transport blocked') from None
def main():
    assets=read(DESIGN/'ASSETS.json')['families']['Llama']['models'];jobs=[];profiles=[]
    for m in assets:
        final=ROOT/m['filename']
        if final.exists():assert final.stat().st_size==m['bytes'] and sha(final)==m['sha256_publisher_claim'];continue
        prefix=ROOT/(m['role']+'-stream-attempt-prefix.bin')
        if not prefix.exists():
            part=final.with_suffix('.partial')
            if part.exists():part.rename(prefix)
            else:prefix.write_bytes(b'')
        size=prefix.stat().st_size;parts=[]
        d=ROOT/(m['role']+'-segments');d.mkdir(exist_ok=True)
        for start in range(size,m['bytes'],32*1024**2):
            end=min(start+32*1024**2,m['bytes'])-1;p=d/f'{start}-{end}.bin'
            jobs.append((m,start,end,p));parts.append(p)
        profiles.append((m,final,prefix,parts))
    completed=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for p in pool.map(segment,jobs):
            completed+=1
            if completed%12==0:print('ASSET RANGES COMPLETE',completed,'/',len(jobs),flush=True)
    for m,final,prefix,parts in profiles:
        with final.with_suffix('.assembling').open('wb') as f:
            for p in [prefix]+parts:
                with p.open('rb') as src:shutil.copyfileobj(src,f,4*1024**2)
        p=final.with_suffix('.assembling');actual=sha(p)
        assert p.stat().st_size==m['bytes'] and actual==m['sha256_publisher_claim'],'full pinned file hash mismatch'
        p.rename(final)
        save(ROOT/(m['role']+'-DOWNLOAD.json'),{'status':'PASS','path':str(final),'url':m['url'],'revision':m['revision'],'bytes':final.stat().st_size,'sha256':actual,'utc':now(),'model_forwards':0,'transport':'preserved interrupted streaming prefix + checked HTTP206 ranges; full assembled hash checked','prefix_bytes':prefix.stat().st_size,'prefix_sha256':sha(prefix),'ranges':[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in parts]})
        print('ASSET FULL HASH PASS',m['role'],flush=True)
if __name__=='__main__':main()
