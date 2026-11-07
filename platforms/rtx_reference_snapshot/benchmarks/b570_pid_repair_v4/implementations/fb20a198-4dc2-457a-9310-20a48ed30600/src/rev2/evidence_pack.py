"""Post-worker evidence frontier and bounded CPU ZIP; no old roots or credentials."""
import argparse,hashlib,json,os,sys,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--mode',choices=['manifest','archive'],required=True);a=p.parse_args();root=Path(a.root).resolve();assert root.parent==Path('C:/hs/b570-capability-v1').resolve();manifest=root/'delivery/EVIDENCE_MANIFEST.json';post=root/'delivery/post_manifest'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
if a.mode=='manifest':
    files=[]
    def walk(parent):
        for p in sorted(parent.iterdir()):
            assert not p.is_symlink() and not p.is_junction(),'alias in evidence'
            if p==post or p==manifest:continue
            if p.is_dir():walk(p)
            else:files.append(dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    walk(root);record=dict(schema=1,root_uuid=root.name,files=files,explicit_exclusions=['delivery/EVIDENCE_MANIFEST.json','delivery/post_manifest/'],scope='Immutable worker/acquisition/source/tool frontier; bounded final verification/delivery tail separately authenticated')
    with manifest.open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    print(json.dumps(dict(manifest_sha256=sha(manifest),members=len(files),logical_bytes=sum(r['bytes'] for r in files))))
else:
    post.mkdir(exist_ok=True);out=post/'RAW_EVIDENCE.zip';assert not out.exists();m=json.loads(manifest.read_text());total=sum(r['bytes'] for r in m['files']);assert total<512*1024**2
    with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for r in m['files']:
            f=root/r['path'];assert f.stat().st_size==r['bytes'] and sha(f)==r['sha256'];z.write(f,r['path'])
        z.write(manifest,'delivery/EVIDENCE_MANIFEST.json')
    receipt=dict(bytes=out.stat().st_size,sha256=sha(out),members=len(m['files'])+1,manifest_sha256=sha(manifest));(post/'ARCHIVE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
