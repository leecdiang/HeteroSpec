#!/usr/bin/env python3
"""Retrieve pinned archive parts, check Git/SHA256 identities, assemble and inventory ZIPs.
Author-side GitHub authentication is required. No archive code is executed.
"""
import concurrent.futures, hashlib, json, os, subprocess, time, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'output/raw_restore'

def digest(p, kind='sha256'):
    h=hashlib.new(kind)
    with p.open('rb') as f:
        if kind=='sha1': h.update(f'blob {p.stat().st_size}\0'.encode())
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def fetch(job):
    aid,r=job
    if r['bytes']>10*1024*1024:
        from recover_large_raw_parts import recover
        a=next(a for a in json.loads((ROOT/'review_access/RAW_ARCHIVE_ACCESS.json').read_text())['archives'] if a['id']==aid)
        return recover(a,r)
    p=STAGE/aid/'parts'/r['name']; p.parent.mkdir(parents=True,exist_ok=True)
    def valid(q): return q.exists() and q.stat().st_size==r['bytes'] and digest(q)==r['sha256'] and digest(q,'sha1')==r['git_blob_sha1']
    if valid(p): return aid,r['name'],'cached'
    tmp=p.with_name(p.name+f'.download.{os.getpid()}')
    for attempt in range(5):
        with tmp.open('wb') as f:
            try:
                result=subprocess.run(['gh','api','-H','Accept: application/vnd.github.raw+json',f"repos/leecdiang/HeteroSpec/git/blobs/{r['git_blob_sha1']}"],stdout=f,stderr=subprocess.PIPE,timeout=300)
                if result.returncode==0 and valid(tmp): tmp.replace(p);return aid,r['name'],'verified'
            except subprocess.TimeoutExpired: pass
        time.sleep(2*(attempt+1))
    raise RuntimeError(f'Failed retrieval or integrity: {aid}/{r["name"]}')

def main():
    data=json.loads((ROOT/'review_access/RAW_ARCHIVE_ACCESS.json').read_text())
    STAGE.mkdir(parents=True,exist_ok=True)
    jobs=[(a['id'],r) for a in data['archives'] for r in a['parts']]
    failures=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(fetch,j):j for j in jobs}
        for i,f in enumerate(concurrent.futures.as_completed(futures),1):
            try: f.result()
            except Exception as e: failures.append(str(e));print(str(e),flush=True)
            if i%20==0 or i==len(jobs):print(f'Parts checked {i}/{len(jobs)}, failures {len(failures)}',flush=True)
    if failures: raise RuntimeError(failures)
    rows=[]
    for a in data['archives']:
        dest=STAGE/a['id']/'archive.zip'
        if not dest.exists():
            subprocess.run(['python3',str(ROOT/'review_access/assemble_raw_archive.py'),'--archive',a['id'],'--parts-dir',str(dest.parent/'parts'),'--output',str(dest)],check=True)
        assert dest.stat().st_size==a['archive_bytes'] and digest(dest)==a['archive_sha256']
        with zipfile.ZipFile(dest) as z:
            entries=[dict(path=i.filename,bytes=i.file_size,compressed_bytes=i.compress_size) for i in z.infolist()]
            assert len(entries)==len({e['path'] for e in entries})
            for n in ['INDEX.json','MANIFEST.json']:
                if n in z.namelist(): (dest.parent/n).write_bytes(z.read(n))
        (dest.parent/'ZIP_MEMBERS.json').write_text(json.dumps(entries,indent=2)+'\n')
        row=dict(id=a['id'],parts=len(a['parts']),archive_bytes=dest.stat().st_size,archive_sha256=digest(dest),zip_members=len(entries),uncompressed_bytes=sum(e['bytes'] for e in entries),status='PARTS_AND_ARCHIVE_HASH_VERIFIED')
        rows.append(row);print(json.dumps(row),flush=True)
    (STAGE/'DOWNLOAD_VERIFICATION.json').write_text(json.dumps(dict(archives=rows),indent=2)+'\n')
if __name__=='__main__':main()
