"""Only download pinned assets; no model context or forward."""
from common import *
import concurrent.futures
def get(m):
    root=LOCAL/'models';root.mkdir(parents=True,exist_ok=True)
    p=root/m['filename'];part=p.with_suffix('.partial');wanted=m['sha256_publisher_claim']
    if p.exists():assert p.stat().st_size==m['bytes'] and sha(p)==wanted;return
    for attempt in range(1,5):
        offset=part.stat().st_size if part.exists() else 0
        try:
            # Fresh original URL per attempt; signed redirect URLs are never persisted.
            url=m['url']+'?download=true&study=third-family-v1&attempt='+str(attempt)
            headers={'User-Agent':'HeteroSpec-scientific-asset-check/1'}
            if offset:headers['Range']='bytes='+str(offset)+'-'
            with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=90) as r:
                if offset and r.status!=206:offset=0
                if offset:assert r.headers.get('Content-Range','').startswith('bytes '+str(offset)+'-')
                with part.open('ab' if offset else 'wb') as f:
                    last=time.monotonic()
                    while True:
                        b=r.read(4*1024**2)
                        if not b:break
                        f.write(b)
                        if time.monotonic()-last>20:print(m['role'],'downloaded',f.tell(),'/',m['bytes'],flush=True);last=time.monotonic()
            assert part.stat().st_size==m['bytes']
            actual=sha(part);assert actual==wanted,'complete asset SHA mismatch'
            part.rename(p)
            save(root/(m['role']+'-DOWNLOAD.json'),{'status':'PASS','path':str(p),'url':m['url'],'revision':m['revision'],'bytes':p.stat().st_size,'sha256':actual,'utc':now(),'model_forwards':0})
            print(m['role'],'COMPLETE HASH PASS',flush=True);return
        except Exception as e:
            save(root/(m['role']+f'-DOWNLOAD-ATTEMPT-{attempt}.json'),{'status':'FAILED','type':type(e).__name__,'bytes_present':part.stat().st_size if part.exists() else 0,'utc':now(),'signed_url_redacted':True})
            print(m['role'],'download attempt',attempt,'failed',type(e).__name__,flush=True)
            if attempt==4:raise RuntimeError('pinned asset download blocked') from None
def main():
    assets=read(DESIGN/'ASSETS.json')['families']['Llama']['models']
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(get,assets))
if __name__=='__main__':main()
