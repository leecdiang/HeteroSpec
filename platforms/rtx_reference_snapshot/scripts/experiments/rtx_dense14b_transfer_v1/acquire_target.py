"""Explicit, resumable download of the pinned official 14B Q8_0 file only."""
from __future__ import annotations
import argparse, os, shutil, urllib.request
from pathlib import Path
from common import need,file_hash,TARGET_SHA256
SIZE=15698533728
URL='https://huggingface.co/Qwen/Qwen3-14B-GGUF/resolve/c75e7b2d0234068f674a1bacf548ea32e27ccd29/Qwen3-14B-Q8_0.gguf'

def acquire(out):
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():
        need(out.stat().st_size==SIZE and file_hash(out)==TARGET_SHA256,'existing target differs; never overwrite');return
    part=out.with_name(out.name+'.part');offset=part.stat().st_size if part.exists() else 0
    need(0<=offset<=SIZE,'invalid partial download size')
    need(shutil.disk_usage(out.parent).free>SIZE-offset+20*1024**3,'download disk reserve')
    if offset<SIZE:
        headers={'User-Agent':'HeteroSpec-fixed-artifact/1.0'}
        if offset:headers['Range']=f'bytes={offset}-'
        req=urllib.request.Request(URL,headers=headers)
        with urllib.request.urlopen(req,timeout=120) as response:
            if offset:need(response.status==206 and response.headers.get('Content-Range','').startswith(f'bytes {offset}-'),'server did not resume exact range')
            with part.open('ab' if offset else 'xb') as f:
                while chunk:=response.read(4*1024*1024):
                    offset+=len(chunk);need(offset<=SIZE,'download exceeds pinned size');f.write(chunk)
                f.flush();os.fsync(f.fileno())
    need(part.stat().st_size==SIZE and file_hash(part)==TARGET_SHA256,'download size/hash mismatch; retain .part for diagnosis')
    part.rename(out)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();acquire(a.out);print('Pinned weight file verified; no model execution')
