"""Restore explicit hash-bound numerical dependency roles into a fresh directory."""
from pathlib import Path
import argparse,hashlib,json,os,shutil

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(manifest,out):
    root=manifest.resolve().parent;data=json.loads(manifest.read_bytes());out=out.resolve()
    assert not out.exists() and not out.is_relative_to(root)
    out.mkdir(parents=True)
    for role,files in data['roles'].items():
        assert role and Path(role).name==role
        dest=out/role/'bin';dest.mkdir(parents=True)
        for name,h in files.items():
            assert Path(name).name==name and len(h)==64 and all(c in '0123456789abcdef' for c in h)
            p=root/'blobs'/h;q=dest/name;assert p.is_file() and sha(p)==h
            if p.stat().st_dev==dest.stat().st_dev:os.link(p,q)
            else:shutil.copy2(p,q)
            assert sha(q)==h
    print('Verified numerical dependency roles restored; no model executed')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('out',type=Path);a=p.parse_args();main(a.manifest,a.out)
