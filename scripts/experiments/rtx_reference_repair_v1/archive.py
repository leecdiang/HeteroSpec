"""Seal evidence without models/DLLs, then independently reopen every ZIP member."""
from __future__ import annotations
import argparse, hashlib, zipfile
from pathlib import Path
from common import *


def pack(root,out,part_bytes=256*1024**2):
    root=Path(root).resolve();out=Path(out).resolve();need(not out.exists(),'fresh delivery directory required')
    need(not out.is_relative_to(root),'archive destination must be outside evidence root')
    integer(part_bytes,1,4*1024**3,'part target');files=[]
    for p in sorted(root.rglob('*')):
        need(not p.is_symlink(),'symlink in evidence')
        if not p.is_file():continue
        need(p.suffix.lower() not in ('.gguf','.dll','.exe','.lib','.a'),'do not redistribute model/runtime binaries')
        files.append(p)
    need(files,'empty evidence');out.mkdir(parents=True);parts=[];index={};z=None;used=0
    try:
        for p in files:
            size=p.stat().st_size
            if z is None or used+size>part_bytes:
                if z:z.close()
                name=f'part-{len(parts):03d}.zip';parts.append(name);z=zipfile.ZipFile(out/name,'x',zipfile.ZIP_DEFLATED,allowZip64=True);used=0
            name=p.relative_to(root).as_posix();z.write(p,name);used+=size
            index[name]={'bytes':size,'sha256':sha(p),'part':parts[-1]}
    finally:
        if z:z.close()
    verified=0
    for name in parts:
        with zipfile.ZipFile(out/name) as z:
            need(z.testzip() is None,'zip CRC failure')
            names=z.namelist();need(len(names)==len(set(names)),'duplicate archive member')
            for member in names:
                h=hashlib.sha256();length=0
                with z.open(member) as f:
                    for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b);length+=len(b)
                pin=index[member];need(length==pin['bytes'] and h.hexdigest()==pin['sha256'] and pin['part']==name,'member verification failed');verified+=1
    result={'status':'LOCAL_READBACK_PASS','members':index,'parts':[{ 'name':n,'sha256':sha(out/n),'bytes':(out/n).stat().st_size} for n in parts],
        'verified_members':verified,'remote_readback':False,'independent_native_reproduction':False}
    save(out/'RAW_ACCESS.json',result,True);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--part-bytes',type=int,default=256*1024**2)
    a=p.parse_args();x=pack(a.root,a.out,a.part_bytes);print(json.dumps({'status':x['status'],'members':x['verified_members'],'parts':len(x['parts'])}))
