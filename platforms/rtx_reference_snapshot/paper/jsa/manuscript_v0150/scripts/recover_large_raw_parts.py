#!/usr/bin/env python3
"""Recover large pinned GitHub blobs through ranged CDN reads after API stream errors.
Temporary signed URLs stay in memory and are never written to a receipt or log.
"""
import concurrent.futures,hashlib,json,subprocess,time,urllib.request
from pathlib import Path
from restore_raw_archives import ROOT,STAGE,digest
BLOCK=4*1024*1024

def recover(a,r):
    dest=STAGE/a['id']/'parts'/r['name'];dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and dest.stat().st_size==r['bytes'] and digest(dest)==r['sha256'] and digest(dest,'sha1')==r['git_blob_sha1']:return a['id'],r['name'],'cached'
    info=subprocess.run(['gh','api',f"repos/leecdiang/HeteroSpec/contents/{r['repository_path']}?ref={a['commit']}"],capture_output=True,check=True,timeout=120)
    url=json.loads(info.stdout)['download_url'];assert url.startswith('https://raw.githubusercontent.com/')
    cache=dest.parent/(r['name']+'.ranges');cache.mkdir(exist_ok=True)
    for begin in range(0,r['bytes'],BLOCK):
        end=min(begin+BLOCK,r['bytes'])-1;p=cache/str(begin)
        if p.exists() and p.stat().st_size==end-begin+1:continue
        for attempt in range(5):
            try:
                req=urllib.request.Request(url,headers={'Range':f'bytes={begin}-{end}'})
                with urllib.request.urlopen(req,timeout=90) as resp:
                    assert resp.status==206 and resp.headers['Content-Range']==f"bytes {begin}-{end}/{r['bytes']}"
                    b=resp.read();assert len(b)==end-begin+1
                p.write_bytes(b);break
            except Exception as error:
                print("Range retry",a["id"],r["name"],begin,type(error).__name__,getattr(error,"code",None),flush=True)
                fresh=subprocess.run(["gh","api",f"repos/leecdiang/HeteroSpec/contents/{r['repository_path']}?ref={a['commit']}"],capture_output=True,check=True,timeout=120)
                url=json.loads(fresh.stdout)["download_url"];assert url.startswith("https://raw.githubusercontent.com/")
                if attempt==4:raise RuntimeError(f'Ranged recovery failed: {a["id"]}/{r["name"]}, offset {begin}') from None
                time.sleep(2)
    tmp=dest.with_name(dest.name+'.cdn-complete')
    with tmp.open('wb') as f:
        for begin in range(0,r['bytes'],BLOCK):f.write((cache/str(begin)).read_bytes())
    assert tmp.stat().st_size==r['bytes'] and digest(tmp)==r['sha256'] and digest(tmp,'sha1')==r['git_blob_sha1']
    tmp.replace(dest)
    for p in cache.iterdir():p.unlink()
    cache.rmdir()
    return a['id'],r['name'],'verified_range_recovery'

def main():
    j=json.loads((ROOT/'review_access/RAW_ARCHIVE_ACCESS.json').read_text())
    jobs=[(a,r) for a in j['archives'] for r in a['parts'] if r['bytes']>10*1024*1024]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        fs=[pool.submit(recover,a,r) for a,r in jobs]
        for f in concurrent.futures.as_completed(fs):print(f.result(),flush=True)
if __name__=='__main__':main()
