"""Explicit one-file download by fixed public identity; no automatic model runs."""
from __future__ import annotations
import argparse, os, shutil, urllib.request
from pathlib import Path
from experiment import require, read, sha


def acquire(spec,out):
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    require(isinstance(spec.get('url'),str) and spec['url'].startswith('https://huggingface.co/'),'Resolved approved HTTPS model host required')
    size=spec['bytes'];digest=spec['sha256'];require(len(digest)==64 and size>0,'Exact model identity')
    if out.exists():
        require(out.stat().st_size==size and sha(out)==digest,'Existing model differs; never overwrite')
        return
    part=out.with_name(out.name+'.part');offset=part.stat().st_size if part.exists() else 0
    require(0<=offset<=size,'Partial length')
    require(shutil.disk_usage(out.parent).free>=size-offset+20*1024**3,'Preserve20GiB disk margin')
    if offset<size:
        headers={'User-Agent':'ReferenceCompatible-ModelAcquire/1.0'}
        if offset:headers['Range']=f'bytes={offset}-'
        with urllib.request.urlopen(urllib.request.Request(spec['url'],headers=headers),timeout=120) as response:
            require(response.url.startswith('https://'),'No insecure redirects')
            if offset:require(response.status==206 and response.headers.get('Content-Range','').startswith(f'bytes {offset}-'),'Exact resume unsupported; partial retained')
            with part.open('ab' if offset else 'xb') as f:
                while b:=response.read(4*1024**2):
                    offset+=len(b);require(offset<=size,'Download exceeds pinned size');f.write(b)
                f.flush();os.fsync(f.fileno())
    require(part.stat().st_size==size and sha(part)==digest,'Model bytes differ; retain partial for diagnosis')
    # Do not replace an existing destination created during this long download.
    os.link(part,out);part.unlink()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('role');p.add_argument('out');a=p.parse_args()
    acquire(read(a.manifest)[a.role],a.out);print('Exact model bytes verified; zero GPU requests')
