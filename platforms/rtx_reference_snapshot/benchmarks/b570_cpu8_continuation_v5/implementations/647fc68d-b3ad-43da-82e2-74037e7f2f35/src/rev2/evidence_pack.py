"""Exact sealed-tree manifest and external CPU evidence archive. No mutation after sealing."""
import argparse,hashlib,json,os,zipfile
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def new_json(p,value):
    with Path(p).open('x',encoding='utf8',newline='\n') as out:
        json.dump(value,out,sort_keys=True,indent=2);out.write('\n');out.flush();os.fsync(out.fileno())
def write_manifest(root):
    root=Path(root).resolve();manifest=root/'delivery/EVIDENCE_MANIFEST.json';manifest.parent.mkdir(parents=True,exist_ok=True)
    files=[]
    def walk(parent):
        for p in sorted(parent.iterdir()):
            if p.is_symlink() or p.is_junction():raise ValueError('alias in sealed evidence')
            if p==manifest:continue
            if p.is_dir():walk(p)
            else:
                if p.stat().st_nlink!=1:raise ValueError('hardlink in sealed evidence')
                files.append(dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    walk(root);new_json(manifest,dict(schema=1,root_uuid=root.name,files=files,explicit_exclusions=['delivery/EVIDENCE_MANIFEST.json'],scope='Exact entire sealed task tree; delivery output is external'))
    return dict(manifest_sha256=sha(manifest),members=len(files),logical_bytes=sum(x['bytes'] for x in files))
def archive(root,external):
    root=Path(root).resolve();external=Path(external).resolve()
    if external==root or root in external.parents:raise ValueError('archive must be outside sealed root')
    from evidence_contract import manifest_check
    manifest=root/'delivery/EVIDENCE_MANIFEST.json';manifest_check(root,'delivery/EVIDENCE_MANIFEST.json')
    m=json.loads(manifest.read_bytes());total=sum(r['bytes'] for r in m['files'])
    if total>=512*1024**2:raise ValueError('archive logical budget')
    from campaign_budget import archive_reservation
    reservation=archive_reservation(root,external,total,len(m['files'])+1)
    external.mkdir(parents=True,exist_ok=True);out=external/'RAW_EVIDENCE.zip'
    with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for r in m['files']:
            p=root/r['path']
            if p.stat().st_size!=r['bytes'] or sha(p)!=r['sha256']:raise ValueError('sealed member drift')
            z.write(p,r['path'])
        z.write(manifest,'delivery/EVIDENCE_MANIFEST.json')
    result=dict(bytes=out.stat().st_size,sha256=sha(out),members=len(m['files'])+1,manifest_sha256=sha(manifest),storage_reservation=reservation)
    new_json(external/'ARCHIVE_RECEIPT.json',result);return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--mode',choices=['manifest','archive'],required=True);p.add_argument('--output-dir');a=p.parse_args();root=Path(a.root).resolve()
    if root.parent!=Path('C:/hs/b570-capability-v1').resolve():raise ValueError('task root namespace')
    if a.mode=='manifest':result=write_manifest(root)
    else:
        if not a.output_dir:raise ValueError('external output-dir required')
        result=archive(root,a.output_dir)
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
