"""Recover logged original runtime artifact; no execution or environment mutation."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT=Path(__file__).parent
URL='https://persistent.oaistatic.com/codex-primary-runtime/26.1011.11113/codex-primary-runtime-win32-x64-26.1011.11113.tar.gz'
SIZE=503164921
SHA='81466ad85b7074e5694a3d45e8edae6387f09548cd2e8f144841951a329dd7c7'
CHUNK=4*1024*1024

def fetch(i):
    start=i*CHUNK;end=min(SIZE,start+CHUNK)-1
    req=urllib.request.Request(URL,headers={'Range':f'bytes={start}-{end}'})
    t=time.perf_counter()
    with urllib.request.urlopen(req,timeout=30) as r:
        assert r.status==206 and r.headers['Content-Range']==f'bytes {start}-{end}/{SIZE}'
        body=r.read();assert len(body)==end-start+1
    with (ROOT/f'part-{i:03d}.bin').open('xb') as f:f.write(body)
    return dict(index=i,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),seconds=time.perf_counter()-t)

def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(fetch,range((SIZE+CHUNK-1)//CHUNK)))
    h=hashlib.sha256()
    with (ROOT/'verified-original.tar.gz').open('xb') as out:
        for row in rows:
            body=(ROOT/f"part-{row['index']:03d}.bin").read_bytes();out.write(body);h.update(body)
    assert h.hexdigest()==SHA
    with (ROOT/'DOWNLOAD_RECEIPT.json').open('x') as f:
        json.dump(dict(url=URL,bytes=SIZE,sha256=SHA,source='2026-10-14 local installation log latest channel',chunks=rows),f,indent=2)
    print('Verified original artifact',SHA,flush=True)
if __name__=='__main__':main()
