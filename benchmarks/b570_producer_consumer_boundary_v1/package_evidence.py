"""Package immutable evidence, split below GitHub's per-asset size, and rehash it.

Models and numerical DLLs are never included. Original PR148/150 reference
payloads are external dependencies, identified by their existing release pins.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
import work_package as wp

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--include',action='append',required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    members=[]
    for name in a.include:
        root=a.root/name
        assert root.exists(),root
        for p in sorted(root.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                assert p.suffix.lower() not in {'.dll','.exe','.gguf'},p
                members.append(dict(path=p.relative_to(a.root).as_posix(),bytes=p.stat().st_size,sha256=wp.sha_file(p)))
    assert len({m['path'] for m in members})==len(members)
    manifest=dict(schema=1,members=members,total_bytes=sum(m['bytes'] for m in members),
        models='external exact dependencies; excluded',numerical_libraries='external PR148/150 dependencies; excluded')
    wp.write_new(a.out/'MANIFEST.json',manifest)
    groups=[];group=[];size=0
    for m in members:
        if group and size+m['bytes']>1400*1024**2:groups.append(group);group=[];size=0
        group.append(m);size+=m['bytes']
    if group:groups.append(group)
    archives=[]
    for i,group in enumerate(groups):
        path=a.out/f'B570_BOUNDARY_EVIDENCE_{i+1:02d}.zip'
        with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
            z.write(a.out/'MANIFEST.json','MANIFEST.json')
            for m in group:z.write(a.root/m['path'],m['path'])
        with zipfile.ZipFile(path) as z:
            for m in group:
                with z.open(m['path']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==m['sha256'],m['path']
        archives.append(dict(name=path.name,bytes=path.stat().st_size,sha256=wp.sha_file(path),members=len(group),readback_verified=True))
        print('verified',path.name,path.stat().st_size,'bytes',flush=True)
    wp.write_new(a.out/'PACKAGE_RECEIPT.json',dict(manifest_sha256=wp.sha_file(a.out/'MANIFEST.json'),archives=archives,
        member_count=len(members),raw_bytes=manifest['total_bytes'],models_or_dlls_included=False))

if __name__=='__main__':main()
