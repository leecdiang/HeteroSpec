"""Materialize the already-executed PR159 support package, without editing its branch."""
from __future__ import annotations
import argparse, importlib, sys
from pathlib import Path
from lr_common import *

def materialize(repo,out):
    out=Path(out).resolve();need(not out.exists(),'fresh parent snapshot directory')
    raw=subprocess.check_output(['git','-C',str(repo),'ls-tree','-rz',BASE,'--',PARENT],timeout=60)
    entries=[]
    for line in raw.split(b'\0'):
        if not line:continue
        meta,path=line.decode().split('\t',1);mode,kind,h=meta.split()
        need(kind=='blob' and mode in ('100644','100755'),'no symlinks/submodules in support snapshot')
        rel=Path(path).relative_to(PARENT).as_posix();entries.append((rel,path,h))
    need(entries,'pinned parent package unavailable; fetch PR159 history')
    out.mkdir(parents=True);manifest={}
    for rel,path,h in entries:
        b=git_read(repo,BASE,path,h);p=confined(out,rel);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);manifest[rel]=h
    save(out/'PARENT_SNAPSHOT.json',{'commit':BASE,'prefix':PARENT,'git_blobs':manifest},exclusive=True)
    return out

def verify(out):
    out=Path(out).resolve();m=read(out/'PARENT_SNAPSHOT.json');need(m['commit']==BASE and m['prefix']==PARENT,'parent identity')
    for rel,h in m['git_blobs'].items():need(blob(confined(out,rel).read_bytes())==h,'parent snapshot changed '+rel)
    return out

def load(out):
    out=verify(out)
    # Parent uses flat imports. A dedicated CLI process avoids mixing another
    # experiment's common/run/audit module into its namespace.
    for name in ('common','native','run','plan','audit'):
        if name in sys.modules:
            file=getattr(sys.modules[name],'__file__','')
            need(Path(file).resolve().parent==out,'foreign imported module '+name)
    sys.path.insert(0,str(out));return importlib.import_module('native'),importlib.import_module('run'),importlib.import_module('audit')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();print(materialize(a.repo,a.out))
