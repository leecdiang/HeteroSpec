"""Shard an experiment bundle and reopen every ZIP member. No upload or inference."""
from __future__ import annotations
import argparse, hashlib, zipfile
from pathlib import Path
from common import file_hash, need, save
EXCLUDE={'LOCAL_PATHS.json','CONFIG.json'}

def pack(bundle,out,limit=128*1024*1024):
    bundle=Path(bundle).resolve();out=Path(out).resolve()
    need(not out.exists() and not out.is_relative_to(bundle),'fresh separate archive directory')
    files=[]
    for p in sorted(bundle.rglob('*')):
        if not p.is_file() or p.name in EXCLUDE:continue
        need(not p.is_symlink(),'symlink in raw bundle')
        need(p.suffix.lower() not in ('.gguf','.dll','.exe','.key','.pem'),'runtime/weight/credential unexpectedly inside evidence root')
        files.append(p)
    need(files,'empty bundle');out.mkdir(parents=True);groups=[];group=[];size=0
    for p in files:
        if group and size+p.stat().st_size>limit:groups.append(group);group=[];size=0
        group.append(p);size+=p.stat().st_size
    if group:groups.append(group)
    entries=[];parts=[]
    for i,group in enumerate(groups):
        dest=out/f'evidence-{i:03d}.zip'
        with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
            for p in group:
                name=p.relative_to(bundle).as_posix();z.write(p,name)
                entries.append({'path':name,'part':dest.name,'bytes':p.stat().st_size,'sha256':file_hash(p)})
        with zipfile.ZipFile(dest) as z:
            need(z.testzip() is None,'ZIP CRC failure')
            for e in entries:
                if e['part']!=dest.name:continue
                h=hashlib.sha256();size=0
                with z.open(e['path']) as f:
                    for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk);size+=len(chunk)
                need(size==e['bytes'] and h.hexdigest()==e['sha256'],'archive member mismatch')
        parts.append({'name':dest.name,'bytes':dest.stat().st_size,'sha256':file_hash(dest)})
    report={'status':'LOCAL_ARCHIVE_READBACK_PASS','files':entries,'parts':parts,
            'remote_uploaded':False,'external_reader_verified':False,
            'privacy_note':'Review logs/prompt/state licenses and access permissions before uploading. Local configuration paths are excluded, but native logs may contain paths.'}
    save(out/'RAW_ACCESS.json',report,exclusive=True);return report

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--bundle',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();r=pack(a.bundle,a.out);print(f"Local readback: {len(r['files'])} files / {len(r['parts'])} parts; not uploaded")
