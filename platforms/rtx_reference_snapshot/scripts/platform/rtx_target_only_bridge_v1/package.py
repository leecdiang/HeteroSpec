"""Repository-supported content-addressed raw evidence parts; CPU-only restore."""
import argparse, hashlib, json, os, pathlib, tarfile
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def build(root):
    doc=root/'benchmarks/rtx_target_only_bridge_v1';out=root/'work/rtx-target-only-bridge-v1';artifact=root/'artifacts/rtx_target_only_bridge_v1';artifact.mkdir(parents=True,exist_ok=True)
    files={}
    for directory in [out,doc/'historical_raw',root/'scripts/platform/rtx_target_only_bridge_v1']:
        for p in directory.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.tmp') and 'packaging' not in p.parts:files[p.relative_to(root).as_posix()]=p
    for p in doc.iterdir():
        if p.is_file() and p.suffix in ['.md','.json','.csv']:files[p.relative_to(root).as_posix()]=p
    for p in (doc/'inputs').rglob('*'):
        if p.is_file():files[p.relative_to(root).as_posix()]=p
    for name in load(doc/'SOURCE_BINDINGS.json')['files']:files[name]=root/name
    manifest={'schema':'heterospec.cas.archive.v1','files':{name:{'sha256':sha(p),'bytes':p.stat().st_size} for name,p in sorted(files.items())},'omissions':['model weights','released/native runtime binaries'],'scope':'snapshot before packaging and final delivery receipts; later reports/receipts remain separate Git objects'}
    work=out/'packaging';work.mkdir(exist_ok=True);write(work/'MANIFEST.json',manifest);archive=work/'raw-cas-v1.tar.gz';cas={}
    for name,p in files.items():cas.setdefault(manifest['files'][name]['sha256'],p)
    with tarfile.open(archive,'w:gz',compresslevel=6) as tf:
        tf.add(work/'MANIFEST.json',arcname='MANIFEST.json',recursive=False)
        for h,p in sorted(cas.items()):tf.add(p,arcname='cas/'+h,recursive=False)
    parts=[]
    with archive.open('rb') as f:
        i=0
        for b in iter(lambda:f.read(48*1024*1024),b''):
            i+=1;p=artifact/f'raw-cas-v1.part-{i:03d}';p.write_bytes(b);parts.append({'path':p.relative_to(root).as_posix(),'bytes':len(b),'sha256':sha(p)})
    write(artifact/'MANIFEST.json',manifest);index={'schema':'heterospec.cas.parts.v1','bytes':archive.stat().st_size,'sha256':sha(archive),'parts':parts,'logical_files':len(files),'unique_blobs':len(cas)};write(artifact/'ARCHIVE.json',index)
    print(json.dumps(index),flush=True)
def restore(root,dest):
    index=load(root/'artifacts/rtx_target_only_bridge_v1/ARCHIVE.json')
    assert not dest.exists() or not any(dest.iterdir()),'destination must be empty'
    dest.mkdir(parents=True,exist_ok=True);joined=dest/'joined.tar.gz'
    with joined.open('wb') as f:
        for part in index['parts']:
            p=root/part['path'];assert sha(p)==part['sha256'] and p.stat().st_size==part['bytes']
            with p.open('rb') as g:
                for b in iter(lambda:g.read(8*1024*1024),b''):f.write(b)
    assert sha(joined)==index['sha256'] and joined.stat().st_size==index['bytes'];cas=dest/'cas';cas.mkdir()
    with tarfile.open(joined,'r:gz') as tf:
        for m in tf:
            if m.name=='MANIFEST.json':manifest=json.load(tf.extractfile(m));continue
            assert m.isfile() and m.name.startswith('cas/')
            h=m.name[4:];assert len(h)==64 and all(c in '0123456789abcdef' for c in h)
            p=cas/h
            with p.open('wb') as f:
                src=tf.extractfile(m)
                for b in iter(lambda:src.read(8*1024*1024),b''):f.write(b)
            assert sha(p)==h
    for name,b in manifest['files'].items():
        rel=pathlib.PurePosixPath(name);assert not rel.is_absolute() and '..' not in rel.parts
        p=dest/pathlib.Path(name);p.parent.mkdir(parents=True,exist_ok=True);os.link(cas/b['sha256'],p)
        assert sha(p)==b['sha256'] and p.stat().st_size==b['bytes']
    receipt={'status':'PASS','parts':len(index['parts']),'logical_files':len(manifest['files']),'archive_sha256':index['sha256']};write(dest/'RESTORE_RECEIPT.json',receipt);print(json.dumps(receipt),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','restore']);p.add_argument('--root',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[3]);p.add_argument('--dest',type=pathlib.Path);a=p.parse_args()
    build(a.root.resolve()) if a.action=='build' else restore(a.root.resolve(),a.dest.resolve())
